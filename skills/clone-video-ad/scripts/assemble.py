#!/usr/bin/env python3
"""Free local checks, the product-hue gate, the shot-route build and its verifier.

  python3 skills/clone-video-ad/scripts/assemble.py check    TAKE.mp4 --still STILL.png --dur D
  python3 skills/clone-video-ad/scripts/assemble.py hue-gate GRADED.mp4 --ungraded TWIN.mp4 --photo PRODUCT [--windows a-b,c-d]
  python3 skills/clone-video-ad/scripts/assemble.py build    outputs/<job>/shots.json [--grade light|none] [--fps 24|30] [--vo VO.mp3 --vo-start S] [--bed BED.audio]
                                                      [--photo PRODUCT] [--allow-crop] [--talker SH07=voice_changed.mp3 ...]
  python3 skills/clone-video-ad/scripts/assemble.py verify   outputs/<job>/master.mp4 outputs/<job>/shots.json

check     opening lock (max SSIM of take frame 0 vs the still centre-cropped at 1.00-1.05,
          both 180x320 grey, PASS >= 0.90), no scene > 0.25 cut inside [0, D], motion present
          (the largest mean frame difference over any 0.5 s window inside [0, D] above the
          floor, so a take that moves and then holds passes). Exit 0 when all pass.
hue-gate  product mask from the photo's hue band, built on the ungraded twin (4 fps, 180x320);
          PASS when chroma kept >= 0.80 overall and per window and hue drift <= 6 deg.
          Exit 0 PASS, 1 FAIL, 2 NO_PRODUCT (also when the photo is not a packshot on a
          white or neutral background: product share > 0.5 or band half-width > 30 deg).
build     per shot: the picked take trimmed to its slot, or a held still with a slight zoompan;
          transitions from cut_in.type (whip-left|whip-right -> xfade slide + horizontal blur
          centred on the cut, zoom-in -> xfade zoomin, flash_s -> a white blend, else hard);
          LIGHT grade = eq brightness to the source shot's YAVG (contrast 1.0, iterated to
          +/-2) then the hue-protected chroma scale toward its SATAVG; NONE = no grade.
          Writes master_ungraded.mp4 (twin), master.mp4, assembly.json (with every command).
          Refuses (exit 2, nothing rendered): LIGHT without a product photo, a photo that is
          not a packshot, and a take or still whose aspect is off the source's by > 2 %
          unless --allow-crop (then the crop is recorded). A NO_PRODUCT or SKIPPED hue gate
          exits 0 with a WARNING line on stderr and is never reported as PASS.
          --talker ID=AUDIO (repeatable) puts that audio (a voice-changed talker take, timed
          from the take's frame 0) in shot ID's window instead of the voiceover, with short
          crossfades, level-matched to the voiceover before the shared loudnorm. Needs --vo.
verify    duration within one frame, measured cuts (both thresholds) within 0.05 s of the
          table's (a whip or zoom cut: inside its transition window), each measured hit
          claimed by one table cut at most, per-shot Y and SAT against the source. Exit 0 on
          a pass.

Colour units are ffmpeg YUV: chroma = hypot(U-128, V-128), hue = atan2(V-128, U-128) deg.
Stdlib Python 3.9+ plus ffmpeg/ffprobe; no network.
"""

import argparse
import itertools
import json
import math
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # importing the sibling scripts leaves no __pycache__
sys.path.insert(0, str(HERE))
import shot_table as st  # noqa: E402

# ---- product-hue gate (measured on one test ad, 2026-09-29) ----
PHOTO_FLOOR = 8.0            # photo chroma above which a pixel is product (white bg ~1.4)
PHOTO_MIN_SHARE = 0.002      # fewer product pixels than this share -> band = none
PACKSHOT_MAX_SHARE = 0.50    # more "product" than this share of the photo -> the backdrop is coloured
PACKSHOT_MAX_HALF = 30.0     # a band wider than +/- this many degrees is not one product colour
PACKSHOT_MSG = ("the product photo is not a packshot on a white or neutral background (or a cut-out); "
                "use one, or --grade none")
LIGHT_NO_PHOTO_MSG = "LIGHT grade needs the product photo (--photo); use --grade none to skip the grade"
FLOOR_FRAC = 0.35            # clip chroma floor = 0.35 x the photo product's median chroma
BAND_MARGIN = 6.0            # degrees added to the photo's 2-98 % hue spread
GATE_FPS = 4
GATE_W, GATE_H = 180, 320
MIN_COVERAGE = 0.06
MIN_BUCKET_COVERAGE = 0.01
CHROMA_RETAINED_MIN = 0.80
HUE_DRIFT_MAX = 6.0
PHOTO_CHROMA_MIN = 0.50
GRADE_FEATHER = 10.0
# ---- opening lock / check ----
LOCK_MIN = 0.90
LOCK_SCALES = [round(1.0 + 0.005 * i, 3) for i in range(11)]
LOCK_WARN_SCALE = 1.04
LOCK_W, LOCK_H = 180, 320
# Motion = the largest mean |frame diff| (180x320 luma) over any MOTION_WINDOW_S window
# inside [0, D]: a take that moves, then holds still, still reads as moving. A frozen clip
# reads 0.0, a slow push-in on a static detailed frame 0.8-1.0, real takes 4.6-6.9
# (measured on one test ad, 2026-09-29). A frozen frame under heavy grain can read ~0.8,
# so the floor catches a stuck take, not a grainy one.
MOTION_WINDOW_S = 0.5
MOTION_FLOOR = 0.5
# ---- build ----
TRANS_S = 0.25
HOLD_ZOOM_PER_S = 0.0135
HOLD_ZOOM_MAX = 1.05
LUMA_TOL = 2.0
LUMA_AIM = 1.28              # half of one eq brightness step
EQ_LEVELS_PER_STEP = 2.555   # vf_eq: brightness enters as int(100*b + 100) * 511/200 levels
LUMA_ITERS = 4
FLASH_ALPHA = 0.85
TALKER_FADE_S = 0.04        # crossfade between the voiceover and a talker window
TALKER_GAIN_MAX_DB = 12.0   # level-match clamp for a talker window against the voiceover
CUT_TOL_S = 0.05
ASPECT_TOL = 0.02            # a take or still whose aspect is off the source's by more is refused
XFADE = {"whip-right": "slideleft", "whip-left": "slideright", "zoom-in": "zoomin"}
SEG_ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p"]
FINAL_ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"]
EPS = 1e-6

_LUT = {}


class Refusal(Exception):
    """A request build will not run as given (exit 2, nothing rendered)."""


def _luts():
    if not _LUT:
        ch, hue = [0.0] * 65536, [0.0] * 65536
        for u in range(256):
            du = u - 128
            for v in range(256):
                dv = v - 128
                i = (u << 8) | v
                ch[i] = math.hypot(du, dv)
                hue[i] = math.degrees(math.atan2(dv, du)) % 360.0
        _LUT["ch"], _LUT["hue"] = ch, hue
        _LUT["yok"] = bytes(1 if 20 < y < 240 else 0 for y in range(256))
    return _LUT["ch"], _LUT["hue"]


def circ_diff(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def _percentile(sorted_vals, p):
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    x = p / 100.0 * (n - 1)
    lo = int(math.floor(x))
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (x - lo)


def _median(vals):
    s = sorted(vals)
    n = len(s)
    return (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0) if n else 0.0


def raw_yuv444(inp_args, vf, w, h):
    data = st.run_bytes(["ffmpeg", "-v", "error", *inp_args, "-an", "-vf", vf, "-f", "rawvideo", "-"])
    fs = 3 * w * h
    return [data[i * fs:(i + 1) * fs] for i in range(len(data) // fs)]


# ------------------------------------------------------------------ product band
def product_band(photo):
    """The product's hue band from the photo (type sniffed, decoded to 8-bit YUV 480x360):
    pixels with chroma > PHOTO_FLOOR are product; band = chroma-weighted circular mean hue
    +/- (the larger 2nd/98th percentile deviation + BAND_MARGIN). band None = grey product."""
    ch, hue = _luts()
    w, h = 480, 360
    n = w * h
    f = raw_yuv444(st.image_input(photo), "scale=%d:%d:flags=area,format=yuv444p" % (w, h), w, h)[0]
    Y, U, V = f[:n], f[n:2 * n], f[2 * n:]
    idx = [(u << 8) | v for u, v in zip(U, V)]
    prod = [i for i, k in enumerate(idx) if ch[k] > PHOTO_FLOOR]
    res = {"photo": str(photo), "mime": st.sniff_mime(photo), "photo_product_share": round(len(prod) / float(n), 3)}
    if len(prod) < max(1, PHOTO_MIN_SHARE * n):
        res.update(band=None, reason="no product pixel above chroma %.1f in the photo" % PHOTO_FLOOR)
        return res
    su = sum(U[i] - 128 for i in prod)
    sv = sum(V[i] - 128 for i in prod)
    center = math.degrees(math.atan2(sv, su)) % 360.0
    diffs = sorted(circ_diff(hue[idx[i]], center) for i in prod)
    half = max(abs(_percentile(diffs, 2)), abs(_percentile(diffs, 98))) + BAND_MARGIN
    chroma = _median([ch[idx[i]] for i in prod])
    res.update(band=True, center=round(center, 2), half_width=round(half, 2),
               lo=round((center - half) % 360, 2), hi=round((center + half) % 360, 2),
               photo_chroma=round(chroma, 2), photo_luma=round(_median([Y[i] for i in prod]), 1),
               photo_rel=round(_median([ch[idx[i]] / max(Y[i], 1) for i in prod]), 4),
               chroma_floor=round(FLOOR_FRAC * chroma, 2))
    if res["photo_product_share"] > PACKSHOT_MAX_SHARE or half > PACKSHOT_MAX_HALF:
        # a coloured backdrop reads as "product": the band would protect (and the gate
        # would measure) the backdrop, so there is no product band to trust
        res.update(band=None, not_packshot=True,
                   reason="%s (product share %.2f > %.2f or band half-width %.1f deg > %.0f)" % (
                       PACKSHOT_MSG, res["photo_product_share"], PACKSHOT_MAX_SHARE, half, PACKSHOT_MAX_HALF))
    return res


def _inband_lut(band):
    ch, hue = _luts()
    c, half, floor = band["center"], band["half_width"], band["chroma_floor"]
    return bytes(1 if ch[i] > floor and abs(circ_diff(hue[i], c)) <= half else 0 for i in range(65536))


_T01 = bytes.maketrans(b"\x00\x01", b"01")
_T10 = bytes.maketrans(b"01", b"\x00\x01")


def _mask_indices(frame, inb, w=GATE_W, h=GATE_H):
    """Masked pixel indices after a 3x3 morphological opening (cv2 MORPH_OPEN semantics:
    the border never erodes and never dilates). Rows are bitsets."""
    n = w * h
    yok = _LUT["yok"]
    Y, U, V = frame[:n], frame[n:2 * n], frame[2 * n:]
    m = bytes(inb[(u << 8) | v] & yok[y] for y, u, v in zip(Y, U, V))
    full = (1 << w) - 1
    top = 1 << (w - 1)
    rows = [int(m[o:o + w][::-1].translate(_T01), 2) for o in range(0, n, w)]
    hr = [r & ((r << 1) | 1) & ((r >> 1) | top) & full for r in rows]
    er = [hr[y] & (hr[y - 1] if y else full) & (hr[y + 1] if y < h - 1 else full) for y in range(h)]
    hd = [(r | (r << 1) | (r >> 1)) & full for r in er]
    dl = [hd[y] | (hd[y - 1] if y else 0) | (hd[y + 1] if y < h - 1 else 0) for y in range(h)]
    bits = "".join(format(r, "0%db" % w)[::-1] for r in dl).encode().translate(_T10)
    return list(itertools.compress(range(n), bits))


def _sums(frame, idx, n=GATE_W * GATE_H):
    ch, _ = _luts()
    U, V = frame[n:2 * n], frame[2 * n:]
    c = su = sv = 0.0
    vals = []
    for i in idx:
        u, v = U[i], V[i]
        x = ch[(u << 8) | v]
        c += x
        su += u - 128
        sv += v - 128
        vals.append(x)
    return c, su, sv, vals


def parse_windows(s):
    if not s:
        return None
    if isinstance(s, (list, tuple)):
        return [(float(a), float(b)) for a, b in s]
    return [tuple(float(x) for x in w.split("-", 1)) for w in s.split(",") if w.strip()]


def gate_frames(path, fps=GATE_FPS):
    return raw_yuv444(["-i", str(path)], "fps=%d,scale=%d:%d:flags=area,format=yuv444p" % (fps, GATE_W, GATE_H),
                      GATE_W, GATE_H)


def hue_gate(clip, photo=None, ungraded=None, windows=None, band=None, fps=GATE_FPS):
    """Twin form (ungraded given): the mask is built on the ungraded frames, the SAME pixels
    are measured in `clip`; chroma_retained = sum graded chroma / sum ungraded chroma,
    hue_drift = chroma-weighted circular mean hue, graded minus ungraded. Photo form: the
    product's median chroma against the photo's (a coarse backstop)."""
    band = band or product_band(photo)
    windows = parse_windows(windows)
    res = {"clip": str(clip), "ungraded": str(ungraded) if ungraded else None,
           "mode": "twin" if ungraded else "photo", "fps": fps, "windows": windows}
    if not band.get("band"):
        res.update(band=None, verdict="NO_PRODUCT", reasons=[band.get("reason", "no product band")])
        return res
    res["band"] = {k: band[k] for k in ("center", "half_width", "lo", "hi", "chroma_floor")}
    npx = GATE_W * GATE_H
    inb = _inband_lut(band)
    fr = gate_frames(ungraded or clip, fps)
    fg = gate_frames(clip, fps) if ungraded else fr
    if ungraded and abs(len(fg) - len(fr)) > 1:
        res["warning"] = "frame count differs: graded %d vs ungraded %d (timing must match)" % (len(fg), len(fr))
    nf = min(len(fg), len(fr))
    t = [i / float(fps) for i in range(nf)]
    sel = [True] * nf if not windows else [any(a <= ti < b for a, b in windows) for ti in t]
    per = []
    for i in range(nf):
        if not sel[i]:
            per.append(None)
            continue
        idx = _mask_indices(fr[i], inb)
        cu, uu, vu, _ = _sums(fr[i], idx)
        cg, ug, vg, vals = _sums(fg[i], idx)
        per.append({"n": len(idx), "cu": cu, "uu": uu, "vu": vu, "cg": cg, "ug": ug, "vg": vg,
                    "vals": vals if not ungraded else None})
    nsel = sum(sel)
    tot = sum(p["n"] for p in per if p)
    res["frames"] = nsel
    res["coverage"] = round(tot / float(nsel * npx), 4) if nsel else 0.0
    res["frames_with_product"] = sum(1 for p in per if p and p["n"] / float(npx) >= MIN_BUCKET_COVERAGE)
    if res["coverage"] < MIN_COVERAGE:
        res.update(verdict="NO_PRODUCT", reasons=["mask covers %.1f%% < %d%%" % (100 * res["coverage"], 100 * MIN_COVERAGE)])
        return res
    P = [p for p in per if p]
    CG, UG, VG = sum(p["cg"] for p in P), sum(p["ug"] for p in P), sum(p["vg"] for p in P)
    hue_g = math.degrees(math.atan2(VG, UG)) % 360.0
    res["hue_clip"] = round(hue_g, 1)
    res["hue_vs_photo"] = round(circ_diff(hue_g, band["center"]), 1)
    reasons = []
    if ungraded:
        CU, UU, VU = sum(p["cu"] for p in P), sum(p["uu"] for p in P), sum(p["vu"] for p in P)
        res["chroma_retained"] = round(CG / max(CU, 1e-6), 3)
        res["hue_drift"] = round(circ_diff(hue_g, math.degrees(math.atan2(VU, UU)) % 360.0), 2)
        buckets = windows or [(s, s + 1.0) for s in range(int(math.ceil(t[-1] + 1e-9)) + 1)] if t else []
        rows = []
        for a, b in buckets:
            bi = [i for i in range(nf) if a <= t[i] < b]
            if len(bi) < 2:
                continue
            bp = [per[i] for i in bi if per[i]]
            cov = sum(p["n"] for p in bp) / float(len(bi) * npx)
            if cov >= MIN_BUCKET_COVERAGE:
                rows.append({"t0": a, "t1": b, "coverage": round(cov, 3),
                             "ratio": round(sum(p["cg"] for p in bp) / max(sum(p["cu"] for p in bp), 1e-6), 3)})
        res["buckets"] = rows
        res["chroma_retained_min_bucket"] = min((r["ratio"] for r in rows), default=None)
        if res["chroma_retained"] < CHROMA_RETAINED_MIN:
            reasons.append("chroma retained %.2f < %.2f" % (res["chroma_retained"], CHROMA_RETAINED_MIN))
        if rows and res["chroma_retained_min_bucket"] < CHROMA_RETAINED_MIN:
            reasons.append("a window retains %.2f < %.2f" % (res["chroma_retained_min_bucket"], CHROMA_RETAINED_MIN))
        if abs(res["hue_drift"]) > HUE_DRIFT_MAX:
            reasons.append("hue drift %+.1f deg > %.0f" % (res["hue_drift"], HUE_DRIFT_MAX))
    else:
        med = _median([x for p in P for x in p["vals"]])
        res["chroma_clip"] = round(med, 2)
        res["chroma_vs_photo"] = round(med / band["photo_chroma"], 3)
        if res["chroma_vs_photo"] < PHOTO_CHROMA_MIN:
            reasons.append("product chroma %.2f x photo < %.2f" % (res["chroma_vs_photo"], PHOTO_CHROMA_MIN))
    res["verdict"] = "FAIL" if reasons else "PASS"
    res["reasons"] = reasons
    return res


# ------------------------------------------------------------------ hue-protected grade
def solve_other_scale(clip, target_sat, band, window=None):
    """k for the NON-product hues so the window's SATAVG lands on target_sat while the band
    keeps 100 % of its chroma (fading over GRADE_FEATHER deg). Clamped to [0, 1]."""
    ch, hue = _luts()
    stats = st.stats_series(str(clip))
    a, b = window or (0.0, len(stats) / float(st.STATS_FPS))
    measured = st.window_stats(stats, a, b)["SATAVG"]
    info = {"measured_sat": measured}
    if not measured:
        return 1.0, info
    if not band or not band.get("band"):
        k = target_sat / measured
        info.update(k_raw=round(k, 3), protected=False)
        return float(min(1.0, max(0.0, k))), info
    c0, half, fe = band["center"], band["half_width"], GRADE_FEATHER
    keep = [min(1.0, max(0.0, (half + fe - abs(circ_diff(hue[i], c0))) / fe)) for i in range(65536)]
    cw = [ch[i] * keep[i] for i in range(65536)]
    co = [ch[i] - cw[i] for i in range(65536)]
    fr = raw_yuv444(["-i", str(clip)], "fps=%d,scale=%d:%d:flags=area,format=yuv444p" % (st.STATS_FPS, GATE_W, GATE_H),
                    GATE_W, GATE_H)
    pad = (b - a) * 0.1
    pick = [f for i, f in enumerate(fr) if a + pad - EPS <= i / float(st.STATS_FPS) <= b - pad + EPS]
    if not pick and fr:
        mid = (a + b) / 2.0
        pick = [fr[min(range(len(fr)), key=lambda i: abs(i / float(st.STATS_FPS) - mid))]]
    n = GATE_W * GATE_H
    sk = so = 0.0
    for f in pick:
        uv = [(u << 8) | v for u, v in zip(f[n:2 * n], f[2 * n:])]
        sk += sum(map(cw.__getitem__, uv))
        so += sum(map(co.__getitem__, uv))
    cnt = float(max(1, len(pick) * n))
    s_keep, s_other = sk / cnt, so / cnt
    r = measured / max(s_keep + s_other, 1e-6)          # our 4:4:4 units -> signalstats units
    k = (target_sat / r - s_keep) / max(s_other, 1e-6)
    info.update(protected=True, protected_share_of_chroma=round(s_keep / max(s_keep + s_other, 1e-6), 3),
                k_raw=round(k, 3), floor_sat_at_k0=round(s_keep * r, 2))
    return float(min(1.0, max(0.0, k))), info


def hue_protected_grade_filter(band, k, feather=GRADE_FEATHER):
    """Chroma-only filter: U,V scaled by k + (1-k)*keep, keep = clip((half+feather-d)/feather,0,1),
    d = circular distance of the pixel's hue from the band centre. Hue angles never move."""
    k = round(float(k), 4)
    c, half, fe = round(band["center"], 2), round(band["half_width"], 2), float(feather)
    keep = ("st(0,cb(X,Y)-128);st(1,cr(X,Y)-128);"
            "st(2,abs(mod(atan2(ld(1),ld(0))*180/PI-%s+540,360)-180));"
            "st(3,%s+(1-%s)*clip((%s+%s-ld(2))/%s,0,1));" % (c, k, k, half, fe, fe))
    return "format=yuv420p,geq=lum='lum(X,Y)':cb='%s128+ld(0)*ld(3)':cr='%s128+ld(1)*ld(3)'" % (keep, keep)


# ------------------------------------------------------------------ check
def _image_size(path):
    inp = st.image_input(path)
    r = st.run(["ffprobe", "-v", "error", "-of", "json", "-show_entries", "stream=width,height"] + inp[:-2] + [inp[-1]])
    s = json.loads(r.stdout)["streams"][0]
    return int(s["width"]), int(s["height"])


def opening_lock(take, still):
    tinfo = st.probe(take)
    sw, sh = _image_size(still)
    ta = tinfo["width"] / float(tinfo["height"])
    cw, chh = (sh * ta, float(sh)) if sw / float(sh) > ta else (float(sw), sw / ta)
    scores = []
    for s in LOCK_SCALES:
        w, h = max(2, int(round(cw / s))), max(2, int(round(chh / s)))
        fc = ("[0:v]crop=%d:%d,scale=%d:%d:flags=area,format=gray,setsar=1[a];"
              "[1:v]trim=end_frame=1,setpts=PTS-STARTPTS,scale=%d:%d:flags=area,format=gray,setsar=1[b];"
              "[a][b]ssim=stats_file=-" % (w, h, LOCK_W, LOCK_H, LOCK_W, LOCK_H))
        out = st.run(["ffmpeg", "-hide_banner", "-nostats", "-v", "error"] + st.image_input(still) +
                     ["-i", str(take), "-filter_complex", fc, "-f", "null", "-"]).stdout
        m = re.search(r"All:([\d.]+)", out)
        scores.append((float(m.group(1)) if m else 0.0, s))
    best, scale = max(scores)
    res = {"ssim": round(best, 3), "scale": scale, "pass": best >= LOCK_MIN, "bar": LOCK_MIN,
           "raw_ssim": round(scores[0][0], 3), "size": [LOCK_W, LOCK_H]}
    if scale > LOCK_WARN_SCALE:
        res["warning"] = "best scale %.3f > %.2f: the take reframes more than usual" % (scale, LOCK_WARN_SCALE)
    return res


def motion(path, dur, fps=None):
    """|frame diff| over [0, dur]: the mean, the single largest diff, and the largest mean
    over any MOTION_WINDOW_S window (the whole span when it is shorter)."""
    out = st.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-t", "%.3f" % dur, "-an", "-vf",
                  "scale=%d:%d:flags=area,format=yuv420p,tblend=all_mode=difference,signalstats,"
                  "metadata=print:file=-" % (LOCK_W, LOCK_H), "-f", "null", "-"]).stdout
    fr = [f for f in st._parse_metadata(out) if "YAVG" in f]
    ys = [f["YAVG"] for f in fr]
    if not ys:
        return {"mean_absdiff": 0.0, "max_absdiff": 0.0, "window_max": 0.0, "window_start": None, "diffs": 0}
    k = max(1, int(round(MOTION_WINDOW_S * (fps or 24.0))))
    k = min(k, len(ys))
    run_sum = sum(ys[:k])
    best, at = run_sum, 0
    for j in range(k, len(ys)):
        run_sum += ys[j] - ys[j - k]
        if run_sum > best:
            best, at = run_sum, j - k + 1
    t0 = fr[0]["pts_time"]
    return {"mean_absdiff": sum(ys) / len(ys), "max_absdiff": max(ys), "window_max": best / k,
            "window_start": round(fr[at]["pts_time"] - t0, 3), "window_diffs": k, "diffs": len(ys)}


def check(take, still, dur):
    info = st.probe(take)
    res = {"take": str(take), "still": str(still), "dur": dur, "take_duration": round(info["duration"], 3)}
    reasons = []
    if info["duration"] + 0.5 / max(info["fps"], 1.0) < dur:
        reasons.append("take is %.2f s, shorter than the shot's %.2f s" % (info["duration"], dur))
    lock = opening_lock(take, still)
    res["opening_lock"] = lock
    if not lock["pass"]:
        reasons.append("opening lock %.3f < %.2f" % (lock["ssim"], LOCK_MIN))
    series = st.frame_series(str(take), signalstats=False)
    inv = [{"t": round(f["t"], 3), "score": round(f["scene"], 3)} for f in series
           if st.STARTUP_S <= f["t"] <= dur + EPS and f["scene"] > st.SCENE_HI]
    res["invented_cuts"] = inv
    if inv:
        reasons.append("scene > %.2f inside [0, %.2f] at %s" % (st.SCENE_HI, dur, [c["t"] for c in inv]))
    mo = motion(take, dur, info["fps"])
    res["motion"] = {"window_max": round(mo["window_max"], 3), "window_start": mo["window_start"],
                     "window_s": MOTION_WINDOW_S, "mean_absdiff": round(mo["mean_absdiff"], 3),
                     "max_absdiff": round(mo["max_absdiff"], 3), "diffs": mo["diffs"],
                     "floor": MOTION_FLOOR, "pass": mo["window_max"] > MOTION_FLOOR}
    if not res["motion"]["pass"]:
        reasons.append("motion %.2f (largest %.1f s window) <= floor %.2f (frozen)" % (
            mo["window_max"], MOTION_WINDOW_S, MOTION_FLOOR))
    res["pass"] = not reasons
    res["reasons"] = reasons
    return res


# ------------------------------------------------------------------ build
def _resolve(p, base):
    p = Path(p)
    if p.is_absolute():
        return p
    for root in (base, Path.cwd()):
        if (root / p).exists():
            return (root / p).resolve()
    return (base / p).resolve()


def _shot_source(r, base):
    new = r.get("new") or {}
    picked = [t for t in new.get("takes") or [] if isinstance(t, dict) and t.get("pick")]
    mode = r.get("render") or ("take" if picked else ("hold" if new.get("still_path") else None))
    if mode == "take":
        if not picked or not picked[-1].get("path"):
            raise ValueError("%s: render=take but no picked take with a path in new.takes" % r["id"])
        return "take", _resolve(picked[-1]["path"], base)
    if mode == "hold":
        if not new.get("still_path"):
            raise ValueError("%s: render=hold but new.still_path is empty" % r["id"])
        return "hold", _resolve(new["still_path"], base)
    raise ValueError("%s: no picked take and no still to hold" % r["id"])


def plan_timeline(shots, F, N):
    n = len(shots)
    K = [0] + [int(round(float(r["in"]) * F)) for r in shots[1:]] + [N]
    for i in range(1, n):
        K[i] = max(K[i], K[i - 1] + 1)
    if K[n - 1] >= N:
        raise ValueError("shots do not fit %d frames at %s fps" % (N, F))
    nom = [K[i + 1] - K[i] for i in range(n)]
    cuts = [None]
    dn0 = max(2, int(round(TRANS_S * F)))
    prev_after = 0
    for i in range(1, n):
        ci = shots[i].get("cut_in") or {}
        typ = (ci.get("type") or "hard").lower()
        flash_n = int(round(float(ci.get("flash_s") or 0) * F))
        c = {"i": i, "K": K[i], "t": round(K[i] / float(F), 4), "type": typ, "kind": "hard",
             "before": 0, "after": 0, "dn": 0, "flash_frames": min(flash_n, nom[i]) if flash_n else 0}
        if typ in XFADE:
            before = min(dn0 // 2, max(0, nom[i - 1] - prev_after))
            after = min(dn0 - dn0 // 2, nom[i] // 2)
            if before + after >= 2:
                c.update(kind="xfade", xfade=XFADE[typ], before=before, after=after, dn=before + after)
            else:
                c["note"] = "slot too short for a %s; cut hard" % typ
        prev_after = c["after"]
        cuts.append(c)
    segs = []
    for i in range(n):
        head = cuts[i]["before"] if i else 0
        tail = cuts[i + 1]["after"] if i + 1 < n else 0
        segs.append({"i": i, "K": K[i], "nominal": nom[i], "head": head, "tail": tail,
                     "frames": head + nom[i] + tail})
    return K, cuts, segs


def assembly_graph(nseg, cuts, F, N, W):
    parts = ["[%d:v]fps=%s,settb=AVTB,setpts=PTS-STARTPTS[v%d]" % (i, F, i) for i in range(nseg)]
    acc = "v0"
    for i in range(1, nseg):
        c = cuts[i]
        if c["kind"] == "xfade":
            parts.append("[%s][v%d]xfade=transition=%s:duration=%.6f:offset=%.6f,fps=%s,settb=AVTB[x%d]" % (
                acc, i, c["xfade"], c["dn"] / float(F), (c["K"] - c["before"]) / float(F), F, i))
        else:
            parts.append("[%s][v%d]concat=n=2:v=1:a=0,fps=%s,settb=AVTB[x%d]" % (acc, i, F, i))
        acc = "x%d" % i
    post = []
    for c in cuts[1:]:
        if c["kind"] == "xfade" and c["type"].startswith("whip"):
            a0 = c["K"] - c["before"]
            a1 = a0 + c["dn"] - 1
            m0, m1 = a0 + c["dn"] // 3, a1 - c["dn"] // 3
            post.append("avgblur=sizeX=%d:sizeY=1:enable='between(n,%d,%d)'" % (max(1, round(14 * W / 720.0)), a0, a1))
            if m1 >= m0:
                post.append("avgblur=sizeX=%d:sizeY=1:enable='between(n,%d,%d)'" % (max(1, round(22 * W / 720.0)), m0, m1))
        if c["flash_frames"]:
            post.append("drawbox=x=0:y=0:w=iw:h=ih:color=white@%s:t=fill:enable='between(n,%d,%d)'" % (
                FLASH_ALPHA, c["K"], c["K"] + c["flash_frames"] - 1))
    post.append("trim=end_frame=%d,setpts=PTS-STARTPTS" % N)
    parts.append("[%s]%s[out]" % (acc, ",".join(post)))
    return ";".join(parts)


def mean_db(path, start=None, dur=None):
    """volumedetect's mean_volume in dB over [start, start+dur], or None for silence."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", "%.3f" % start]
    if dur is not None:
        cmd += ["-t", "%.3f" % dur]
    cmd += ["-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"]
    m = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", st.run(cmd).stderr)
    return float(m.group(1)) if m else None


def talker_plan(shots, K, segs, F, talkers, job):
    """Where each --talker audio goes: shot window [a, b] in the master, and the matching
    span of the talker file, which is timed from the take's frame 0 (the segment starts
    `head` frames before the cut when an xfade pulls it early)."""
    ids = {r["id"]: i for i, r in enumerate(shots)}
    plan = []
    for sid, p in talkers.items():
        if sid not in ids:
            raise ValueError("--talker %s: no such shot in shots.json" % sid)
        i = ids[sid]
        s = segs[i]
        plan.append({"id": sid, "path": str(_resolve(p, job)), "a": K[i] / float(F), "b": K[i + 1] / float(F),
                     "src_a": s["head"] / float(F), "src_b": (s["head"] + s["nominal"]) / float(F)})
    return sorted(plan, key=lambda t: t["a"])


def _media_size(mode, path):
    if mode == "take":
        info = st.probe(str(path))
        return info["width"], info["height"]
    return _image_size(path)


def preflight(doc, job, grade, photo, allow_crop):
    """Every refusal before a frame is rendered: LIGHT without a photo, a photo that is not
    a packshot, a take or still whose aspect is off the source's. Returns (band, sources,
    crops)."""
    photo = photo or doc.get("product_photo")
    if grade == "light" and not photo:
        raise Refusal(LIGHT_NO_PHOTO_MSG)
    if photo and not _resolve(photo, job).is_file():
        raise Refusal("the product photo was not found: %s" % photo)
    band = product_band(_resolve(photo, job)) if photo else None
    if grade == "light" and band.get("not_packshot"):
        raise Refusal(band["reason"])
    sources = [_shot_source(r, job) for r in doc["shots"]]
    W, H = [int(x) for x in doc["size"]]
    R = W / float(H)
    off = []
    for r, (mode, src) in zip(doc["shots"], sources):
        w, h = _media_size(mode, src)
        a = w / float(h)
        if abs(a / R - 1.0) > ASPECT_TOL:
            off.append({"id": r["id"], "mode": mode, "src": str(src), "size": [w, h], "aspect": round(a, 4),
                        "source_aspect": round(R, 4), "off_pct": round(100.0 * abs(a / R - 1.0), 1),
                        "kept_pct": round(100.0 * min(a / R, R / a), 1)})
    if off and not allow_crop:
        raise Refusal("%s: the %s aspect differs from the source's %dx%d (%.4f) by more than %d%%, and build "
                      "would centre-crop it to fit (keeping %s%% of the frame); make the stills and takes at "
                      "shots.json aspect (%s), or pass --allow-crop to crop on purpose" % (
                          ", ".join("%s %dx%d" % (o["id"], o["size"][0], o["size"][1]) for o in off),
                          "/".join(sorted({o["mode"] for o in off})), W, H, R, int(ASPECT_TOL * 100),
                          "/".join(str(o["kept_pct"]) for o in off), doc.get("aspect", "the nearest to the source")))
    return photo, band, sources, off


def build(shots_path, grade="light", fps=24, vo=None, vo_start=0.0, bed=None, photo=None, talkers=None,
          allow_crop=False):
    shots_path = Path(shots_path).resolve()
    job = shots_path.parent
    with open(shots_path, encoding="utf-8") as fh:
        doc = json.load(fh)
    W, H = [int(x) for x in doc["size"]]
    F = int(fps)
    D = float(doc["duration"])
    N = int(round(D * F))
    shots = doc["shots"]
    photo, band, sources, crops = preflight(doc, job, grade, photo, allow_crop)
    bdir = job / "build"
    bdir.mkdir(exist_ok=True)
    cmds = []

    def run(tag, cmd):
        cmds.append({"tag": tag, "cmd": [str(c) for c in cmd]})
        return st.run(cmd)

    K, cuts, segs = plan_timeline(shots, F, N)
    rec = {"version": 1, "shots_json": str(shots_path), "grade": grade, "fps": F, "size": [W, H],
           "frames": N, "duration_target": D, "photo": str(photo) if photo else None,
           "band": {k: band.get(k) for k in ("center", "half_width", "chroma_floor", "reason") if k in band} if band else None,
           "allow_crop": bool(allow_crop), "crops": crops, "cuts": cuts[1:], "shots": []}
    warnings = ["%s (%s) centre-cropped from %dx%d: keeps %s%% of its frame (--allow-crop)" % (
        c["id"], c["mode"], c["size"][0], c["size"][1], c["kept_pct"]) for c in crops]
    ung, grd = [], []
    for s, r, (mode, src) in zip(segs, shots, sources):
        T = s["frames"]
        out_u = bdir / ("%s_ungraded.mp4" % r["id"])
        if mode == "take":
            vf = ("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d,setsar=1,fps=%d,"
                  "tpad=stop_mode=clone:stop_duration=10,trim=start_frame=0:end_frame=%d,setpts=PTS-STARTPTS"
                  % (W, H, W, H, F, T))
            run("seg_%s_take" % r["id"], ["ffmpeg", "-y", "-v", "error", "-i", src, "-an", "-vf", vf,
                                          "-frames:v", T, "-r", F] + SEG_ENC + [out_u])
        else:
            z = "min(1+%s*on/%d,%s)" % (HOLD_ZOOM_PER_S, F, HOLD_ZOOM_MAX)
            vf = ("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d,"
                  "zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d,setsar=1"
                  % (3 * W, 3 * H, 3 * W, 3 * H, z, T, W, H, F))
            run("seg_%s_hold" % r["id"], ["ffmpeg", "-y", "-v", "error"] + st.image_input(src) +
                ["-an", "-vf", vf, "-frames:v", T, "-r", F] + SEG_ENC + [out_u])
        ung.append(out_u)
        srow = {"id": r["id"], "mode": mode, "src": str(src), "K": s["K"], "nominal_frames": s["nominal"],
                "head": s["head"], "tail": s["tail"], "frames": T}
        flash_frames = cuts[s["i"]]["flash_frames"] if s["i"] else 0
        wa, wb = (s["head"] + flash_frames) / float(F), (s["head"] + s["nominal"]) / float(F)
        tgt = r.get("grade") or {}
        if grade == "light" and tgt.get("YAVG") is not None:
            T_y, T_s = float(tgt["YAVG"]), tgt.get("SATAVG")
            y0 = st.window_stats(st.stats_series(str(out_u)), wa, wb)["YAVG"]
            # vf_eq quantises brightness to integer bins m = int(100*b + 100) (about 2.56 luma
            # levels each); a round value such as -0.07 can truncate into the bin below, so the
            # search walks the bins and sends each bin's centre, b = (m - 99.5) / 100.
            m, it, seen = 100 + int(round((T_y - y0) / EQ_LEVELS_PER_STEP)), [], set()
            for _ in range(LUMA_ITERS):
                m = max(1, min(199, m))
                if m in seen:
                    break
                seen.add(m)
                b = (m - 99.5) / 100.0
                y = st.window_stats(st.stats_series(str(out_u), pre="eq=brightness=%.4f:contrast=1.0" % b), wa, wb)["YAVG"]
                it.append({"brightness": round(b, 4), "y": y})
                err = T_y - y
                if abs(err) <= LUMA_AIM:
                    break
                m += (1 if err > 0 else -1) * max(1, int(round(abs(err) / EQ_LEVELS_PER_STEP)))
            b = min(it, key=lambda x: abs(T_y - x["y"]))["brightness"]
            k, kinfo = (1.0, {"skipped": "no SATAVG target"}) if T_s is None else \
                solve_other_scale(out_u, float(T_s), band, (wa, wb))
            vf = "eq=brightness=%.4f:contrast=1.0" % b
            if band and band.get("band"):
                if k < 0.9995:
                    vf += "," + hue_protected_grade_filter(band, k)
            elif k < 0.9995:
                vf += ":saturation=%.4f" % k
            out_g = bdir / ("%s_graded.mp4" % r["id"])
            run("grade_%s" % r["id"], ["ffmpeg", "-y", "-v", "error", "-i", out_u, "-an", "-vf", vf,
                                       "-frames:v", T, "-r", F] + SEG_ENC + [out_g])
            after = st.window_stats(st.stats_series(str(out_g)), wa, wb)
            srow["grade"] = {"y_target": T_y, "y_before": y0, "brightness": round(b, 4), "iterations": it,
                             "y_after": after["YAVG"], "luma_ok": abs(after["YAVG"] - T_y) <= LUMA_TOL,
                             "sat_target": T_s, "k": round(k, 4), "k_info": kinfo, "sat_after": after["SATAVG"],
                             "filter": vf}
            grd.append(out_g)
        else:
            if grade == "light":
                srow["grade"] = {"skipped": "the row has no source grade stats"}
            grd.append(out_u)
        rec["shots"].append(srow)
    graph = assembly_graph(len(segs), cuts, F, N, W)
    twin = job / "master_ungraded.mp4"
    graded_video = bdir / "master_video.mp4"

    def assemble(inputs, out, tag):
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for p in inputs:
            cmd += ["-i", p]
        cmd += ["-filter_complex", graph, "-map", "[out]", "-an", "-frames:v", N, "-r", F] + FINAL_ENC + \
            ["-movflags", "+faststart", out]
        run(tag, cmd)

    assemble(ung, twin, "assemble_ungraded")
    if grade == "light":
        assemble(grd, graded_video, "assemble_graded")
    else:
        shutil.copyfile(str(twin), str(graded_video))
        cmds.append({"tag": "assemble_graded", "cmd": ["copy", str(twin), str(graded_video)]})
    master = job / "master.mp4"
    Dout = N / float(F)
    if talkers and not vo:
        raise ValueError("--talker needs --vo: the talker audio replaces the voiceover inside its shot's window")
    if vo:
        vo = _resolve(vo, job)
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", graded_video, "-i", vo]
        if vo_start >= 0:
            a = "[1:a]adelay=%d:all=1," % int(round(vo_start * 1000))
        else:
            a = "[1:a]atrim=start=%.3f,asetpts=PTS-STARTPTS," % (-vo_start)
        tk = talker_plan(shots, K, segs, F, talkers, job) if talkers else []
        if tk:
            # Cut the voiceover to silence inside each talker window (crossfading over
            # TALKER_FADE_S at both edges), lay each talker span in its window, then one
            # loudnorm over the mix so both voices leave at the same loudness target.
            f = TALKER_FADE_S
            duck = "*".join("(1-clip(min((t-%.6f)/%.3f,(%.6f-t)/%.3f),0,1))" % (t["a"], f, t["b"], f) for t in tk)
            a += "aresample=48000,asetnsamples=n=240,volume='%s':eval=frame[vod]" % duck
            vo_db = mean_db(vo)
            for j, t in enumerate(tk):
                cmd += ["-i", t["path"]]
                t_db = mean_db(t["path"], t["src_a"], t["src_b"] - t["src_a"])
                gain = 0.0 if vo_db is None or t_db is None else \
                    max(-TALKER_GAIN_MAX_DB, min(TALKER_GAIN_MAX_DB, vo_db - t_db))
                t["gain_db"] = round(gain, 2)
                span = t["src_b"] - t["src_a"]
                a += (";[%d:a]atrim=start=%.6f:end=%.6f,asetpts=PTS-STARTPTS,aresample=48000,volume=%.2fdB,"
                      "afade=t=in:st=0:d=%.3f,afade=t=out:st=%.6f:d=%.3f,adelay=%d:all=1[tk%d]"
                      % (2 + j, t["src_a"], t["src_b"], gain, f, max(0.0, span - f), f,
                         int(round(t["a"] * 1000)), j))
            a += ";[vod]%samix=inputs=%d:duration=longest:normalize=0," % (
                "".join("[tk%d]" % j for j in range(len(tk))), 1 + len(tk))
        a += "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad[vo]"
        if bed:
            cmd += ["-i", _resolve(bed, job)]
            a += (";[%d:a]aresample=48000,volume=-20dB,apad[bd];[vo][bd]amix=inputs=2:duration=first:normalize=0,"
                  % (2 + len(tk)))
        else:
            a += ";[vo]"
        a += "atrim=0:%.6f,asetpts=PTS-STARTPTS[a]" % Dout
        cmd += ["-filter_complex", a, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", master]
        run("mux_audio", cmd)
        rec["audio"] = {"vo": str(vo), "vo_start": vo_start, "bed": str(bed) if bed else None,
                        "loudnorm": "I=-14:TP=-1.5:LRA=11", "bed_gain_db": -20 if bed else None,
                        "talkers": [{k: t[k] for k in ("id", "path", "a", "b", "src_a", "src_b", "gain_db")}
                                    for t in tk]}
    else:
        shutil.copyfile(str(graded_video), str(master))
        rec["audio"] = None
    windows = [(K[i] / float(F), K[i + 1] / float(F)) for i in range(len(segs))]
    if band:
        rec["hue_gate"] = hue_gate(graded_video, ungraded=twin, windows=windows, band=band)
    else:
        rec["hue_gate"] = {"verdict": "SKIPPED", "reasons": ["--grade none and no product photo"]}
    if rec["hue_gate"]["verdict"] in ("NO_PRODUCT", "SKIPPED"):
        warnings.append("hue gate %s (%s): nothing checked the product's colour, so this build is not a "
                        "hue-gate PASS" % (rec["hue_gate"]["verdict"], "; ".join(rec["hue_gate"].get("reasons") or [])))
    rec["warnings"] = warnings
    mi, ti = st.probe(str(master)), st.probe(str(twin))
    rec["master"] = {"path": str(master), "frames": mi["nb_frames"], "duration": round(mi["duration"], 4)}
    rec["twin"] = {"path": str(twin), "frames": ti["nb_frames"], "duration": round(ti["duration"], 4)}
    rec["duration_ok"] = abs((mi["nb_frames"] or 0) / float(F) - D) <= 1.0 / F + 1e-3
    rec["commands"] = cmds
    with open(job / "assembly.json", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    return rec


# ------------------------------------------------------------------ verify
def verify(master, shots_path):
    shots_path = Path(shots_path).resolve()
    with open(shots_path, encoding="utf-8") as fh:
        doc = json.load(fh)
    asm = {}
    ap = shots_path.parent / "assembly.json"
    if ap.exists():
        with open(ap, encoding="utf-8") as fh:
            asm = json.load(fh)
    info = st.probe(str(master))
    F = info["fps"]
    frames = info["nb_frames"]
    vdur = frames / F if frames and F else info["duration"]
    D = float(doc["duration"])
    res = {"master": str(master), "fps": round(F, 3), "frames": frames, "duration": round(vdur, 4),
           "source_duration": D, "duration_delta": round(vdur - D, 4)}
    reasons = []
    res["duration_ok"] = abs(vdur - D) <= 1.0 / F + 1e-3
    if not res["duration_ok"]:
        reasons.append("duration %.3f vs source %.3f (> one frame)" % (vdur, D))
    series = st.frame_series(str(master), signalstats=False)
    hits = [(f["t"], f["scene"]) for f in series if f["t"] >= st.STARTUP_S and f["scene"] > st.SCENE_LO]
    plan = {c["i"]: c for c in asm.get("cuts", []) if isinstance(c, dict)} if asm.get("fps") == round(F) else {}
    # Each measured hit is claimed by at most one table cut: pairs are taken best first
    # (an acceptable hit before any other, then the smaller error), so two table cuts can
    # never both pass on the same hit.
    tab = []
    for i, r in enumerate(doc["shots"][1:], 1):
        p = plan.get(i)
        win = None
        if p and p.get("kind") == "xfade":
            win = ((p["K"] - p["before"]) / F - 0.5 / F, (p["K"] + p["after"]) / F + 0.5 / F)
        tab.append((i, r, float(r["in"]), win))

    def acceptable(c, win, t):
        return abs(t - c) <= CUT_TOL_S or bool(win and win[0] <= t <= win[1])
    pairs = sorted((0 if acceptable(c, win, t) else 1, abs(t - c), i, h)
                   for i, _, c, win in tab for h, (t, _) in enumerate(hits))
    claim, owner = {}, {}
    for _, _, i, h in pairs:
        if i not in claim and h not in owner:
            claim[i], owner[h] = h, i
    ids = {i: r["id"] for i, r, _, _ in tab}
    rows = []
    for i, r, c, win in tab:
        typ = ((r.get("cut_in") or {}).get("type") or "hard").lower()
        row = {"id": r["id"], "table": c, "type": typ}
        h = claim.get(i)
        if h is None:
            row.update(measured=None, ok=False)
            if hits:
                nh = min(range(len(hits)), key=lambda j: abs(hits[j][0] - c))
                row["note"] = "the nearest measured hit (%.3f) is claimed by %s" % (hits[nh][0], ids.get(owner.get(nh)))
        else:
            t, sc = hits[h]
            err = t - c
            row.update(measured=round(t, 3), score=round(sc, 3), err=round(err, 3),
                       seen_at="0.25" if sc > st.SCENE_HI else "0.12", ok=acceptable(c, win, t))
            if row["ok"] and abs(err) > CUT_TOL_S:
                row.update(in_transition=[round(win[0], 3), round(win[1], 3)],
                           note="detector fires at the slide's onset; a hit inside the transition window counts")
        rows.append(row)
        if not row["ok"]:
            reasons.append("%s cut %.2f: %s" % (r["id"], c, row.get("note") or "nearest free measured hit %s" % row.get("measured")))
    res["cuts"] = rows
    res["cuts_ok"] = all(x["ok"] for x in rows)
    tcuts = [float(r["in"]) for r in doc["shots"][1:]]
    res["extra_025"] = [round(t, 3) for t, s in hits
                        if s > st.SCENE_HI and all(abs(t - c) > 0.1 + EPS for c in tcuts)
                        and not any((p["K"] - p["before"]) / F - EPS <= t <= (p["K"] + max(p["after"], p.get("flash_frames", 0))) / F + EPS
                                    for p in plan.values())]
    stats = st.stats_series(str(master))
    per = []
    for r in doc["shots"]:
        ci = r.get("cut_in") or {}
        a = min(float(r["out"]), float(r["in"]) + float(ci.get("flash_s") or 0) + float(ci.get("whip_s") or 0))
        m = st.window_stats(stats, a, float(r["out"]))
        g = r.get("grade") or {}
        per.append({"id": r["id"], "y": m["YAVG"], "y_source": g.get("YAVG"), "sat": m["SATAVG"],
                    "sat_source": g.get("SATAVG"),
                    "y_delta": round(m["YAVG"] - g["YAVG"], 2) if g.get("YAVG") is not None else None,
                    "sat_delta": round(m["SATAVG"] - g["SATAVG"], 2) if g.get("SATAVG") is not None else None})
    res["shots"] = per
    res["grade"] = asm.get("grade")
    if asm.get("hue_gate"):
        res["hue_gate"] = {k: asm["hue_gate"].get(k) for k in ("verdict", "chroma_retained", "chroma_retained_min_bucket",
                                                               "hue_drift", "coverage", "reasons")}
    res["pass"] = not reasons
    res["reasons"] = reasons
    return res


# ------------------------------------------------------------------ cli
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("take")
    c.add_argument("--still", required=True)
    c.add_argument("--dur", type=float, required=True)
    g = sub.add_parser("hue-gate")
    g.add_argument("graded")
    g.add_argument("--ungraded")
    g.add_argument("--photo", required=True)
    g.add_argument("--windows")
    b = sub.add_parser("build")
    b.add_argument("shots")
    b.add_argument("--grade", choices=("light", "none"), default="light")
    b.add_argument("--fps", type=int, choices=(24, 30), default=24)
    b.add_argument("--vo")
    b.add_argument("--vo-start", type=float, default=0.0)
    b.add_argument("--bed")
    b.add_argument("--photo", help="product photo (default: shots.json product_photo)")
    b.add_argument("--allow-crop", action="store_true",
                   help="centre-crop takes or stills whose aspect is off the source's by more than 2%% "
                        "(recorded in assembly.json) instead of refusing")
    b.add_argument("--talker", action="append", default=[], metavar="ID=AUDIO",
                   help="repeatable: a voice-changed talker take's audio for shot ID, replacing the voiceover "
                        "inside that shot's window (needs --vo)")
    v = sub.add_parser("verify")
    v.add_argument("master")
    v.add_argument("shots")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        res = check(a.take, a.still, a.dur)
        print(json.dumps(res, indent=1))
        return 0 if res["pass"] else 1
    if a.cmd == "hue-gate":
        res = hue_gate(a.graded, photo=a.photo, ungraded=a.ungraded, windows=a.windows)
        print(json.dumps(res, indent=1))
        return {"PASS": 0, "FAIL": 1}.get(res["verdict"], 2)
    if a.cmd == "build":
        talkers = {}
        for spec in a.talker:
            sid, sep, path = spec.partition("=")
            if not sep or not sid or not path:
                ap.error("--talker takes ID=AUDIO, e.g. --talker SH07=outputs/job/talk/SH07_vc.mp3")
            talkers[sid.strip()] = path.strip()
        try:
            rec = build(a.shots, a.grade, a.fps, a.vo, a.vo_start, a.bed, a.photo, talkers, a.allow_crop)
        except (Refusal, ValueError, OSError) as e:
            print(json.dumps({"pass": False, "error": str(e)}, indent=1))
            print("ERROR: %s" % e, file=sys.stderr)
            return 2
        out = {k: rec[k] for k in ("grade", "fps", "frames", "master", "twin", "duration_ok", "warnings")}
        out["hue_gate"] = {k: rec["hue_gate"].get(k) for k in ("verdict", "chroma_retained", "hue_drift", "reasons")}
        for w in rec["warnings"]:
            print("WARNING: %s" % w, file=sys.stderr)
        out["shots"] = [{"id": s["id"], "mode": s["mode"], "frames": s["frames"],
                         "y_after": (s.get("grade") or {}).get("y_after"), "y_target": (s.get("grade") or {}).get("y_target"),
                         "k": (s.get("grade") or {}).get("k")} for s in rec["shots"]]
        out["assembly_json"] = str(Path(a.shots).resolve().parent / "assembly.json")
        print(json.dumps(out, indent=1))
        ok = rec["duration_ok"] and rec["hue_gate"]["verdict"] in ("PASS", "SKIPPED", "NO_PRODUCT")
        return 0 if ok else 1
    res = verify(a.master, a.shots)
    print(json.dumps(res, indent=1))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
