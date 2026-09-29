#!/usr/bin/env python3
"""Shot table for the shot-by-shot clone route: cuts, flashes, per-shot stats, words, frames.

  python3 skills/clone-video-ad/scripts/shot_table.py SOURCE.mp4 --job outputs/<job> [--transcript TRANSCRIPT.json] [--resegment]

Cuts come from ffmpeg scene detection read at two thresholds (every scene > 0.25 hit
is a cut; a 0.12-only hit within 0.1 s of such an anchor merges into it; the other
0.12-only hits group within 0.1 s into one cut each, marked confirm_cut for the vision
read). A segment of <= 0.15 s whose YAVG is far above its neighbours is a flash: it is
folded into the next shot as cut_in.flash_s, never counted as a shot (consecutive flashes
add up). Any other segment under 0.2 s (the frames of a whip pan) folds into the next
shot as cut_in.whip_s with cut_in.type_hint "whip"; at the very end it stays its own row
(render_hint hold_candidate). shots.json `aspect` is the nearest
of 9:16 and 16:9 to the source, for every still and take request.

Writes outputs/<job>/shots.json (the run's resumable ledger), frames/<id>_{in,mid,out}.jpg
and strips/<id>_cut.jpg (one tile per frame available around the cut; row.strip is set
only when the file was written). Re-running keeps the table's rows as they stand: ids,
in/out, cut_in, hand merges and every filled field, including the `new` ledger. It
refreshes only each row's stats, speech (with --transcript), frames and strip.
--resegment re-cuts from the detector (fields carried over by id) and is refused, exit 2,
once any row has a take in its ledger.

Stdlib Python 3.9+ plus ffmpeg/ffprobe. The other scripts in this folder import the
helpers below (probe, frame_series, stats_series, window_stats, load_words, ...).
"""

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

VERSION = 1
SCENE_HI = 0.25          # every hit above it is a cut
SCENE_LO = 0.12          # hits in (0.12, 0.25] are "0.12-only"
MERGE_S = 0.10           # a 0.12-only hit this close to a 0.25 anchor merges into it
GROUP_S = 0.10           # leftover 0.12-only hits closer than this (strictly) form one cut,
                         # placed at the group's first hit (measured on one test ad, 2026-09-29:
                         # 2.73, 31.43, 45.63)
STARTUP_S = 0.10         # a scene score before 0.1 s is a start-up artefact
FLASH_MAX_S = 0.15       # a flash lasts at most this long
FLASH_DY = 40.0          # ... and its YAVG sits this far above both neighbours
FLASH_CONTEXT_S = 0.30   # neighbour luma is read over this much of each side
STATS_FPS = 10           # per-shot stats recipe: fps=10, scale=180:320, signalstats
STATS_W, STATS_H = 180, 320
HOLD_HINT_S = 1.0
MICRO_S = 0.20           # any other segment shorter than this (the frames of a whip pan, a
                         # stutter) is not a shot: it folds into the next one as cut_in.whip_s
                         # (a trailing one stays a row: there is no next shot to fold into)
SINGLE_FRAME_S = 0.4
STRIP_S = 0.5
FRAME_H = 640            # extracted frames are scaled to this height
STRIP_TILE_W = 120
EPS = 1e-6
# The aspect values both the GPT image models and the Seedance video models accept (their
# `aspectRatio` enums in GET /v1/openapi.json, as of 2026-09-29; omni-flash takes only 9:16
# and 16:9). shots.json `aspect` is the nearest of these to the source; build refuses a take
# whose aspect is off by > 2 %.
ASPECTS = (("9:16", 9 / 16.0), ("16:9", 16 / 9.0), ("1:1", 1.0), ("21:9", 21 / 9.0))

STAT_KEYS = ("YAVG", "SATAVG", "UAVG", "VAVG", "YLOW", "YHIGH")
CLAUDE_FIELDS = ("framing", "subject_fill_pct", "subject_pos", "camera", "action", "people",
                 "speaks_on_camera", "room_id", "light_words", "product", "on_screen_text_style",
                 "render")
DETECTOR_ROW_KEYS = {"id", "in", "out", "dur", "cut_in", "confirm_cut", "grade", "speech",
                     "frames", "strip", "render_hint"}
DETECTOR_TOP_KEYS = {"version", "source", "duration", "fps", "size", "aspect", "aspect_off_pct",
                     "cuts_025", "cuts_012", "flashes", "shots", "source_start", "format_duration",
                     "transcript"}
PIPE_DEMUX = {"image/webp": "webp_pipe", "image/png": "png_pipe", "image/jpeg": "jpeg_pipe"}


# ------------------------------------------------------------------ process helpers
def run(cmd, check=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError("command failed (%d): %s\n%s" % (
            r.returncode, " ".join(str(c) for c in cmd)[:400], r.stderr[-1200:]))
    return r


def run_bytes(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True)
    if r.returncode:
        raise RuntimeError("command failed (%d): %s\n%s" % (
            r.returncode, " ".join(str(c) for c in cmd)[:400], r.stderr.decode(errors="replace")[-1200:]))
    return r.stdout


def sniff_mime(path):
    """The image type from its magic bytes, never from the extension."""
    with open(path, "rb") as fh:
        head = fh.read(16)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return "application/octet-stream"


def image_input(path):
    """ffmpeg input args for a still, with the demuxer forced from the sniffed type."""
    mt = sniff_mime(path)
    return (["-f", PIPE_DEMUX[mt]] if mt in PIPE_DEMUX else []) + ["-i", str(path)]


def _rate(s):
    try:
        a, b = str(s).split("/")
        a, b = float(a), float(b)
        return a / b if b else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(path):
    r = run(["ffprobe", "-v", "error", "-of", "json", "-show_entries",
             "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration"
             ":format=duration", path])
    d = json.loads(r.stdout)
    streams = d.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if v is None:
        raise RuntimeError("no video stream in %s" % path)
    fps = _rate(v.get("r_frame_rate")) or _rate(v.get("avg_frame_rate"))
    fmt_dur = float(d.get("format", {}).get("duration") or 0)
    vdur = v.get("duration")
    vdur = float(vdur) if vdur not in (None, "N/A") else None
    nb = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None
    if vdur is None and nb and fps:
        vdur = nb / fps
    return {"width": int(v["width"]), "height": int(v["height"]), "fps": fps,
            "duration": vdur or fmt_dur, "format_duration": fmt_dur, "nb_frames": nb,
            "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


def _parse_metadata(text):
    """metadata=print:file=- output -> [{'pts_time': t, key: float, ...}]"""
    frames, cur = [], None
    for line in text.splitlines():
        if line.startswith("frame:"):
            m = re.search(r"pts_time:(-?[\d.]+)", line)
            cur = {"pts_time": float(m.group(1)) if m else float("nan")}
            frames.append(cur)
        elif cur is not None and "=" in line:
            k, _, val = line.partition("=")
            k = k.strip().replace("lavfi.signalstats.", "").replace("lavfi.", "")
            try:
                cur[k] = float(val)
            except ValueError:
                pass
    return frames


def frame_series(path, signalstats=True, pre=""):
    """One pass over every native frame: t (from the first frame), scene score, and
    (optionally) full-resolution signalstats. The scene score is computed for every
    frame by select, so thresholding it here equals select='gt(scene,thr)'."""
    vf = (pre + "," if pre else "") + ("signalstats," if signalstats else "") + \
        "select='gte(scene,0)',metadata=print:file=-"
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", vf,
               "-f", "null", "-"]).stdout
    fr = _parse_metadata(out)
    t0 = fr[0]["pts_time"] if fr else 0.0
    for f in fr:
        f["t"] = f["pts_time"] - t0
        f["scene"] = f.get("scene_score", 0.0)
    return fr


def stats_series(path, pre=""):
    """The per-shot stats recipe (fps=10, scale=180:320, signalstats); t = i / 10."""
    vf = (pre + "," if pre else "") + "fps=%d,scale=%d:%d,signalstats,metadata=print:file=-" % (
        STATS_FPS, STATS_W, STATS_H)
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", vf,
               "-f", "null", "-"]).stdout
    fr = _parse_metadata(out)
    for i, f in enumerate(fr):
        f["t"] = i / float(STATS_FPS)
    return fr


def window_stats(series, a, b, frac=0.8):
    """Mean of each signalstats key over the middle `frac` of [a, b]; the frame nearest
    the midpoint when the window holds none."""
    pad = (b - a) * (1.0 - frac) / 2.0
    lo, hi = a + pad, b - pad
    sel = [f for f in series if lo - EPS <= f["t"] <= hi + EPS]
    if not sel and series:
        mid = (a + b) / 2.0
        sel = [min(series, key=lambda f: abs(f["t"] - mid))]
    res = {}
    for k in STAT_KEYS:
        vals = [f[k] for f in sel if k in f]
        res[k] = round(sum(vals) / len(vals), 2) if vals else None
    res["n_frames"] = len(sel)
    return res


# ------------------------------------------------------------------ words
_VOWELS = "aeiouyáéíóúàèìòùâêîôûäëïöüãõœæ"
_VGROUP = re.compile("[%s]+" % _VOWELS)
_TOKEN = re.compile(r"[\w'’\-]+", re.UNICODE)


def tokens(text):
    """Spoken words in a line: runs of letters/digits (apostrophes and hyphens kept)."""
    return [t for t in _TOKEN.findall(text or "") if any(ch.isalnum() for ch in t)]


def syllables(word, lang="en"):
    """A vowel-group count (a tie-break signal, not a dictionary). English drops a
    silent final e and a non-syllabic -ed."""
    w = "".join(ch for ch in word.lower() if ch.isalnum())
    if not w:
        return 0
    if w.isdigit():
        return len(w)
    n = len(_VGROUP.findall(w))
    if (lang or "en").lower().startswith("en") and n > 1:
        if w.endswith("e") and not w.endswith(("le", "ee", "ye")):
            n -= 1
        elif w.endswith("ed") and not w.endswith(("ted", "ded")):
            n -= 1
    return max(1, n)


def load_words(path):
    """words[] from a /v1/transcripts response (or a bare list): [{text,start,end}], lang."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)

    def find(o):
        if isinstance(o, list) and o and isinstance(o[0], dict) and "start" in o[0]:
            return o, {}
        if isinstance(o, dict):
            w = o.get("words")
            if isinstance(w, list):
                return w, o
            for k in ("transcript", "data", "result", "response", "output"):
                if k in o:
                    r = find(o[k])
                    if r:
                        return r
        return None

    got = find(d)
    if not got:
        raise ValueError("no words[] with start/end in %s" % path)
    raw, holder = got
    lang = (holder.get("language") or holder.get("language_code") or
            (d.get("language") if isinstance(d, dict) else None) or "en")
    words = []
    for w in raw:
        if not isinstance(w, dict) or w.get("type") not in (None, "word"):
            continue
        text = w.get("text", w.get("word", w.get("punctuated_word", "")))
        if not tokens(text) or w.get("start") is None or w.get("end") is None:
            continue
        words.append({"text": str(text).strip(), "start": float(w["start"]), "end": float(w["end"])})
    words.sort(key=lambda x: x["start"])
    return words, str(lang)


def speech_block(words, lang):
    if not words:
        return None
    text = " ".join(w["text"] for w in words)
    toks = [t for w in words for t in tokens(w["text"])]
    start, end = words[0]["start"], words[-1]["end"]
    return {"text": text, "n_words": len(toks),
            "n_syll": sum(syllables(t, lang) for t in toks),
            "start": round(start, 3), "end": round(end, 3),
            "wps": round(len(toks) / max(end - start, 0.01), 2)}


# ------------------------------------------------------------------ cuts
def detect_cuts(series):
    """Two-threshold merge. Returns (cuts, hits_025, hits_012)."""
    hits = [(f["t"], f["scene"]) for f in series if f["t"] >= STARTUP_S and f["scene"] > SCENE_LO]
    hi = [(t, s) for t, s in hits if s > SCENE_HI]
    lo_only = [(t, s) for t, s in hits if s <= SCENE_HI]
    cuts = [{"t": t, "score": s, "seen_at": "0.25", "confirm_cut": False, "merged": []} for t, s in hi]
    left = []
    for t, s in lo_only:
        near = [c for c in cuts if abs(c["t"] - t) <= MERGE_S + EPS]
        if near:
            min(near, key=lambda c: abs(c["t"] - t))["merged"].append(round(t, 3))
        else:
            left.append((t, s))
    groups = []
    for t, s in sorted(left):
        if groups and t - groups[-1][-1][0] < GROUP_S - EPS:
            groups[-1].append((t, s))
        else:
            groups.append([(t, s)])
    for g in groups:
        t0 = g[0][0]
        s = max(x[1] for x in g)
        cuts.append({"t": t0, "score": s, "seen_at": "0.12-only", "confirm_cut": True,
                     "group": [round(x[0], 3) for x in g]})
    cuts.sort(key=lambda c: c["t"])
    return cuts, hi, hits


def _mean_y(series, a, b):
    ys = [f["YAVG"] for f in series if a - EPS <= f["t"] < b - EPS and "YAVG" in f]
    return sum(ys) / len(ys) if ys else None


def segments_to_shots(cuts, series, duration, fps):
    """Cut list -> shot spans. Two kinds of segment are not shots: a flash (<= 0.15 s, far
    brighter than both neighbours) and a micro segment (any other segment under MICRO_S,
    such as the frames of a whip pan). Each folds into the next shot as flash_s or whip_s,
    and consecutive ones add up. At the very end there is no next shot: a trailing flash
    joins the last shot, and a trailing micro segment stays its own row (a real cut just
    before the end, e.g. the first frames of the next shot in a trimmed ad)."""
    bounds = [0.0] + [c["t"] for c in cuts] + [duration]
    cut_at = [None] + cuts
    segs = []
    for j in range(len(bounds) - 1):
        a, b = bounds[j], bounds[j + 1]
        if b - a < EPS:
            continue
        segs.append({"a": a, "b": b, "cut": cut_at[j]})
    half_frame = 0.5 / fps if fps else 0.0
    for j, s in enumerate(segs):
        s["flash"] = False
        if s["b"] - s["a"] > FLASH_MAX_S + half_frame:
            continue
        y = _mean_y(series, s["a"], s["b"])
        prev_y = _mean_y(series, max(0.0, s["a"] - FLASH_CONTEXT_S), s["a"]) if j > 0 else None
        next_y = _mean_y(series, s["b"], s["b"] + FLASH_CONTEXT_S) if j + 1 < len(segs) else None
        nb = [v for v in (prev_y, next_y) if v is not None]
        if y is not None and nb and y - max(nb) >= FLASH_DY:
            s.update(flash=True, y=round(y, 1), neighbours_y=[round(v, 1) for v in nb])
    shots, flashes, pending = [], [], None
    for j, s in enumerate(segs):
        span = s["b"] - s["a"]
        kind = "flash" if s["flash"] else ("whip" if span < MICRO_S - half_frame else None)
        if kind and len(segs) > 1:
            last = j + 1 == len(segs)
            if kind == "flash":
                flashes.append({"in": round(s["a"], 3), "out": round(s["b"], 3), "dur": round(span, 3),
                                "yavg": s["y"], "neighbours_yavg": s["neighbours_y"],
                                "folded_into": "previous" if last and shots else "next"})
            if not last:
                if pending is None:
                    pending = {"a": s["a"], "cut": s["cut"], "flash_s": 0.0, "whip_s": 0.0}
                pending["flash_s" if kind == "flash" else "whip_s"] += span
                continue
            if kind == "flash" and shots:  # a trailing flash joins the last shot
                shots[-1]["tail_flash_s"] = round(s["b"] - (pending["a"] if pending else s["a"]), 3)
                shots[-1]["b"] = s["b"]
                pending = None
                continue
            # a trailing micro segment falls through: it stays its own (hold candidate) row
        head = pending or {"a": s["a"], "cut": s["cut"], "flash_s": 0.0, "whip_s": 0.0}
        shots.append({"a": head["a"], "b": s["b"], "cut": head["cut"],
                      "flash_s": head["flash_s"], "whip_s": head["whip_s"]})
        pending = None
    return shots, flashes


def nearest_aspect(w, h):
    """The nearest of ASPECTS to w:h (in log ratio) and how far off it is, in percent."""
    r = w / float(h)
    name, val = min(ASPECTS, key=lambda x: abs(math.log(r / x[1])))
    return name, round(100.0 * abs(r / val - 1.0), 1)


# ------------------------------------------------------------------ frames
def grab_frame(src, t, out):
    """One frame at t; returns True when the file was written."""
    Path(out).unlink(missing_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % max(0.0, t), "-i", src, "-frames:v", "1",
         "-vf", "scale=-2:%d" % FRAME_H, "-q:v", "3", out], check=False)
    return Path(out).is_file() and Path(out).stat().st_size > 0


def grab_strip(src, t_cut, fps, out, duration=None):
    """A STRIP_S strip centred on the cut, one tile per frame actually available (a cut near
    either end has fewer); tpad clones the last frame if the decoder delivers one short, so
    the tile always fills. Returns True when the file was written."""
    a = max(0.0, t_cut - STRIP_S / 2.0)
    end = a + STRIP_S if duration is None else max(a, min(float(duration), a + STRIP_S))
    n = max(1, int((end - a) * fps + 1e-6)) if fps else 1
    Path(out).unlink(missing_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % a, "-i", src, "-t", "%.3f" % max(end - a, 0.001),
         "-vf", "scale=%d:-2,tpad=stop_mode=clone:stop=%d,tile=%dx1:padding=2:color=white" % (STRIP_TILE_W, n, n),
         "-frames:v", "1", "-q:v", "3", out], check=False)
    return Path(out).is_file() and Path(out).stat().st_size > 0


# ------------------------------------------------------------------ table
def detect(src, transcript=None):
    """The detector's reading of the source: probe, cuts, spans, stats and words."""
    src = str(Path(src).resolve())
    info = probe(src)
    fps = info["fps"]
    series = frame_series(src)
    duration = info["duration"]  # the video stream's own duration
    cuts, hi, lo_all = detect_cuts(series)
    spans, flashes = segments_to_shots(cuts, series, duration, fps)
    words, lang = ([], "en")
    if transcript:
        words, lang = load_words(transcript)
    return {"src": src, "info": info, "fps": fps, "duration": duration, "series": series, "hi": hi,
            "lo_all": lo_all, "spans": spans, "flashes": flashes, "stats": stats_series(src),
            "words": words, "lang": lang, "transcript": transcript}


def detector_rows(ctx):
    """Fresh rows from the detector's spans (geometry and empty fields; no stats yet)."""
    rows = []
    for i, sp in enumerate(ctx["spans"]):
        c = sp["cut"]
        row = {"id": "SH%02d" % (i + 1), "in": round(sp["a"], 2), "out": round(sp["b"], 2),
               "dur": round(sp["b"] - sp["a"], 2),
               "cut_in": {"score": round(c["score"], 3) if c else None,
                          "seen_at": c["seen_at"] if c else "start",
                          "flash_s": round(sp["flash_s"], 2), "whip_s": round(sp.get("whip_s", 0.0), 2),
                          "type_hint": "whip" if sp.get("whip_s", 0.0) > EPS else None, "type": None},
               "confirm_cut": bool(c and c["confirm_cut"])}
        if c and c.get("group") and len(c["group"]) > 1:
            row["cut_in"]["group"] = c["group"]
        if c and c.get("merged"):
            row["cut_in"]["merged_012"] = c["merged"]
        if sp.get("tail_flash_s"):
            row["tail_flash_s"] = sp["tail_flash_s"]
        for k in CLAUDE_FIELDS:
            row[k] = None
        row["new"] = {"person_id": None, "room_id": None, "still_prompt": None, "motion_prompt": None,
                      "still_assetId": None, "still_path": None, "takes": []}
        rows.append(row)
    return rows


def refresh_row(row, i, n_rows, ctx, job, frames, warnings):
    """Recompute a row's [S] stats (dur, grade, speech when a transcript is given, the
    render hint), its frames and its strip from its own in/out. Nothing else is touched."""
    src, fps = ctx["src"], ctx["fps"]
    a, b = float(row["in"]), float(row["out"])
    ci = row.get("cut_in") or {}
    body_a = min(b, a + float(ci.get("flash_s") or 0) + float(ci.get("whip_s") or 0))
    row["dur"] = round(b - a, 2)
    row["grade"] = window_stats(ctx["stats"], body_a, b)
    if ctx["transcript"]:
        mine = [w for w in ctx["words"] if a - EPS <= (w["start"] + w["end"]) / 2.0 < b - EPS
                or (i == n_rows - 1 and (w["start"] + w["end"]) / 2.0 >= b - EPS)]
        row["speech"] = speech_block(mine, ctx["lang"])
    else:
        row.setdefault("speech", None)
    if frames:
        fl = []
        if b - body_a < SINGLE_FRAME_S:
            picks = [("mid", (body_a + b) / 2.0)]
        else:
            picks = [("in", body_a + 0.05), ("mid", (body_a + b) / 2.0), ("out", b - 0.05)]
        for tag, t in picks:
            rel = "frames/%s_%s.jpg" % (row["id"], tag)
            if grab_frame(src, t, job / rel):
                fl.append(rel)
            else:
                warnings.append("%s: no frame written at %.2f s" % (row["id"], t))
        row["frames"] = fl
        row.pop("strip", None)
        if i > 0:
            rel = "strips/%s_cut.jpg" % row["id"]
            if grab_strip(src, a, fps, job / rel, ctx["duration"]):
                row["strip"] = rel
            else:
                warnings.append("%s: no strip written for the cut at %.2f s" % (row["id"], a))
    else:
        # --no-frames refreshes nothing on disk: keep only the entries whose files exist
        row["frames"] = [f for f in row.get("frames") or [] if (job / f).is_file()]
        if row.get("strip") and not (job / row["strip"]).is_file():
            row.pop("strip")
    row["render_hint"] = "hold_candidate" if (b - a) < HOLD_HINT_S else "take"


def top_doc(ctx, rows):
    info, series = ctx["info"], ctx["series"]
    aspect, off = nearest_aspect(info["width"], info["height"])
    doc = {"version": VERSION, "source": ctx["src"], "duration": round(ctx["duration"], 3),
           "format_duration": round(info["format_duration"], 3), "fps": round(ctx["fps"], 3),
           "size": [info["width"], info["height"]], "aspect": aspect, "aspect_off_pct": off,
           "source_start": round(series[0]["pts_time"], 3) if series else 0.0,
           "cuts_025": [round(t, 3) for t, _ in ctx["hi"]],
           "cuts_012": [round(t, 3) for t, _ in ctx["lo_all"]],
           "flashes": ctx["flashes"], "shots": rows}
    if ctx["transcript"]:
        doc["transcript"] = str(Path(ctx["transcript"]).resolve())
        doc["transcript_language"] = ctx["lang"]
    return doc


def build_table(src, job, transcript=None, frames=True, warnings=None):
    """A fresh table from the detector (no earlier shots.json read)."""
    ctx = detect(src, transcript)
    job = Path(job)
    return _finish(ctx, detector_rows(ctx), job, frames, warnings if warnings is not None else [])


def _finish(ctx, rows, job, frames, warnings):
    job.mkdir(parents=True, exist_ok=True)
    if frames:
        (job / "frames").mkdir(exist_ok=True)
        (job / "strips").mkdir(exist_ok=True)
    for i, row in enumerate(rows):
        refresh_row(row, i, len(rows), ctx, job, frames, warnings)
    return top_doc(ctx, rows)


def rows_with_takes(old):
    rows = list(old.get("shots") or []) + list(old.get("orphaned_rows") or [])
    return [r.get("id") for r in rows if isinstance(r, dict) and ((r.get("new") or {}).get("takes"))]


def kept_rows_problem(old, ctx):
    """Why the earlier table's segmentation cannot be kept on this source, or None."""
    rows = old.get("shots")
    fps = ctx["fps"] or 30.0
    try:
        d_old = float(old.get("duration"))
        ins = [float(r["in"]) for r in rows]
        outs = [float(r["out"]) for r in rows]
    except (TypeError, ValueError, KeyError):
        return "the existing shots.json has rows without a numeric in/out or no duration"
    if abs(d_old - ctx["duration"]) > 1.0 / fps + 2e-3:
        return ("the existing shots.json was cut from a %.3f s source and this one is %.3f s; "
                "use a new --job for a different source" % (d_old, ctx["duration"]))
    if any(o <= i for i, o in zip(ins, outs)) or any(b <= a for a, b in zip(ins, ins[1:])):
        return "the existing shots.json has a row whose out is not after its in, or rows out of order"
    return None


def keep_segmentation(old, ctx, transcript_given):
    """The earlier rows as they stand (ids, in/out, cut_in, every filled field, hand
    merges); the detector's top-level facts refreshed; notes where the detector disagrees."""
    warnings = []
    rows = old["shots"]
    doc_top = top_doc(ctx, rows)
    for k, v in old.items():
        if k not in DETECTOR_TOP_KEYS and k not in doc_top:
            doc_top[k] = v
    if not transcript_given:
        for k in ("transcript", "transcript_language"):
            if k in old:
                doc_top[k] = old[k]
    frame = 1.0 / (ctx["fps"] or 30.0)
    det = [round(sp["a"], 2) for sp in ctx["spans"][1:]]
    kept = [float(r["in"]) for r in rows[1:]]
    extra = [t for t in det if all(abs(t - k) > frame + 0.01 for k in kept)]
    gone = [k for k in kept if all(abs(t - k) > frame + 0.01 for t in det)]
    if extra or gone:
        warnings.append("kept the table's %d row(s) and their edits; the detector alone would cut at %s "
                        "(not in the table: %s; table cuts it does not read: %s); --resegment re-cuts"
                        % (len(rows), det, extra, gone))
    for i, (a, b) in enumerate(zip(rows, rows[1:])):
        if abs(float(a["out"]) - float(b["in"])) > 0.011:
            warnings.append("%s ends at %s but %s starts at %s" % (a.get("id"), a["out"], b.get("id"), b["in"]))
    return doc_top, warnings


def merge_existing(doc, old, transcript_given):
    """--resegment: fresh detector rows; keep the `new` ledger, cut_in.type and every
    non-null field Claude or a later step wrote, matched by id."""
    warnings = []
    old_rows = {r.get("id"): r for r in old.get("shots", []) if isinstance(r, dict)}
    for r in doc["shots"]:
        o = old_rows.pop(r["id"], None)
        if not o:
            continue
        for k, v in o.items():
            if k == "new" and isinstance(v, dict):
                r["new"] = v
            elif k not in DETECTOR_ROW_KEYS and v is not None:
                r[k] = v
        if isinstance(o.get("cut_in"), dict) and o["cut_in"].get("type") is not None:
            r["cut_in"]["type"] = o["cut_in"]["type"]
        if not transcript_given and o.get("speech") is not None:
            r["speech"] = o["speech"]
        if (abs(float(o.get("in", r["in"])) - r["in"]) > 0.02 or abs(float(o.get("out", r["out"])) - r["out"]) > 0.02) \
                and (r.get("new") or {}).get("takes"):
            warnings.append("%s moved from %s-%s to %s-%s; its takes may no longer fit" % (
                r["id"], o.get("in"), o.get("out"), r["in"], r["out"]))
    orphans = list(old.get("orphaned_rows", [])) + list(old_rows.values())
    if orphans:
        doc["orphaned_rows"] = orphans
        warnings.append("%d earlier row(s) no longer match a shot id; kept under orphaned_rows" % len(old_rows))
    for k, v in old.items():
        if k not in DETECTOR_TOP_KEYS and k != "orphaned_rows" and k not in doc:
            doc[k] = v
    if not transcript_given:
        for k in ("transcript", "transcript_language"):
            if k in old:
                doc[k] = old[k]
    return warnings


def _fail(msg):
    print(json.dumps({"pass": False, "error": msg}, indent=1))
    print("ERROR: " + msg, file=sys.stderr)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--job", required=True, help="outputs/<job> directory")
    ap.add_argument("--transcript", help="a /v1/transcripts response with words[]")
    ap.add_argument("--no-frames", action="store_true", help="skip frames/ and strips/ (fast re-runs, tests)")
    ap.add_argument("--resegment", action="store_true",
                    help="re-cut from the detector instead of keeping the existing rows (refused once a row has a take)")
    a = ap.parse_args(argv)
    job = Path(a.job)
    out = job / "shots.json"
    warnings, old = [], None
    if out.exists():
        try:
            with open(out, encoding="utf-8") as fh:
                old = json.load(fh)
        except (ValueError, OSError) as e:
            warnings.append("existing shots.json unreadable (%s); written fresh" % e)
        if not (isinstance(old, dict) and isinstance(old.get("shots"), list) and old["shots"]
                and all(isinstance(r, dict) for r in old["shots"])):
            old = None
    if old is not None and a.resegment:
        taken = rows_with_takes(old)
        if taken:
            return _fail("--resegment refused: %s already have takes in their ledger, and re-cutting would "
                         "orphan paid work; keep the table (run without --resegment) or start a new --job"
                         % ", ".join(str(t) for t in taken))
    ctx = detect(a.source, a.transcript)
    if old is not None and not a.resegment:
        problem = kept_rows_problem(old, ctx)
        if problem:
            return _fail(problem)
        doc, w = keep_segmentation(old, ctx, bool(a.transcript))
        warnings += w
        mode = "kept"
        job.mkdir(parents=True, exist_ok=True)
        if not a.no_frames:
            (job / "frames").mkdir(exist_ok=True)
            (job / "strips").mkdir(exist_ok=True)
        for i, row in enumerate(doc["shots"]):
            refresh_row(row, i, len(doc["shots"]), ctx, job, not a.no_frames, warnings)
    else:
        doc = _finish(ctx, detector_rows(ctx), job, not a.no_frames, warnings)
        mode = "detector"
        if old is not None:
            warnings += merge_existing(doc, old, bool(a.transcript))
            mode = "resegmented"
    tmp = out.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    tmp.replace(out)
    summary = {"shots_json": str(out), "segmentation": mode, "duration": doc["duration"], "fps": doc["fps"],
               "aspect": doc["aspect"], "aspect_off_pct": doc["aspect_off_pct"],
               "shots": len(doc["shots"]),
               "cuts": [{"id": r["id"], "in": r["in"], "seen_at": (r.get("cut_in") or {}).get("seen_at"),
                         "score": (r.get("cut_in") or {}).get("score"),
                         "flash_s": (r.get("cut_in") or {}).get("flash_s"),
                         "whip_s": (r.get("cut_in") or {}).get("whip_s"),
                         "confirm_cut": r.get("confirm_cut")} for r in doc["shots"][1:]],
               "confirm_cut": [r["id"] for r in doc["shots"] if r.get("confirm_cut")],
               "flashes": doc["flashes"], "warnings": warnings}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
