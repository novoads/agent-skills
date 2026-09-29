#!/usr/bin/env python3
"""Pace rule for the shot route: per-shot word targets, a script check, VO alignment.

  python3 skills/clone-video-ad/scripts/pace.py plan  outputs/<job>/shots.json                 # per-shot word targets
  python3 skills/clone-video-ad/scripts/pace.py check outputs/<job>/shots.json SCRIPT.json     # the new lines per shot
  python3 skills/clone-video-ad/scripts/pace.py align outputs/<job>/shots.json VO_TRANSCRIPT.json [--vo-start S] [--script SCRIPT.json]

SCRIPT.json = {"lines": [{"shot": "SH01", "text": "..."}, ...]}.
plan   per-shot word targets: a spoken shot takes its source count +/-1 (at least 1), a
       silent shot takes 0. A source with no speech says so (no_speech): skip the pace step.
check  passes when every shot is inside plan's targets (syllables reported), the total is
       within +/-5 %, and every shot the source speaks in is spoken in. Exit 0/1.
align  reads the new voiceover's transcript words[] (times in the VO file, placed at
       --vo-start in the master) and reports speech start/end against the source (+/-0.15 s),
       per-shot phrase offsets, a suggested atempo (clamped 0.85-1.15) with the vo-start that
       goes with it, and the phrases still more than 0.2 s off after that (split at the pause
       before and shift). Phrases are cut from the words by the script's per-shot counts
       (--script) or else by the source's counts scaled to the new total. Exit 0 when start
       and end are within tolerance at the given --vo-start.
Any error (a missing or unreadable file, a source with no speech for align) prints
{"pass": false, "error": "..."} and exits 2. Stdlib only.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # importing the sibling scripts leaves no __pycache__
sys.path.insert(0, str(HERE))
import shot_table as st  # noqa: E402

WORD_TOL = 1
TOTAL_TOL = 0.05
EDGE_TOL_S = 0.15
PHRASE_TOL_S = 0.20
ATEMPO_MIN, ATEMPO_MAX = 0.85, 1.15


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _src(doc):
    lang = doc.get("transcript_language") or "en"
    rows = []
    for r in doc["shots"]:
        sp = r.get("speech") or None
        rows.append({"id": r["id"], "in": r["in"], "out": r["out"],
                     "n_words": sp["n_words"] if sp else 0, "n_syll": sp["n_syll"] if sp else 0,
                     "start": sp["start"] if sp else None, "end": sp["end"] if sp else None})
    return rows, lang


def _bounds(n_words):
    """(min, max) words for a shot the source speaks n_words in; a silent shot stays silent."""
    if n_words <= 0:
        return 0, 0
    return max(1, n_words - WORD_TOL), n_words + WORD_TOL


def _no_speech_note(doc):
    if not doc.get("transcript"):
        return ("shots.json has no transcript: a source that speaks needs shot_table.py --transcript "
                "before the pace step; a source with no speech skips the pace step")
    return "the source has no speech: skip the pace step (a clone without a voiceover script)"


def plan(doc):
    rows, lang = _src(doc)
    total = sum(r["n_words"] for r in rows)
    shots = [{"id": r["id"], "in": r["in"], "out": r["out"], "source_words": r["n_words"],
              "source_syll": r["n_syll"], "must_speak": r["n_words"] > 0,
              "words_min": _bounds(r["n_words"])[0], "words_max": _bounds(r["n_words"])[1],
              "phrase_start": r["start"], "phrase_end": r["end"]} for r in rows]
    spoken = [r for r in rows if r["start"] is not None]
    extra = {} if total else {"no_speech": True, "note": _no_speech_note(doc)}
    return {"language": lang, **extra, "shots": shots,
            "total": {"source": total, "min": round(total * (1 - TOTAL_TOL), 2), "max": round(total * (1 + TOTAL_TOL), 2)},
            "speech_start": min(r["start"] for r in spoken) if spoken else None,
            "speech_end": max(r["end"] for r in spoken) if spoken else None,
            "rules": "words per shot within +/-%d, total within +/-%d%%, phrase breaks on the same cuts, "
                     "speech start and end within %.2f s" % (WORD_TOL, int(TOTAL_TOL * 100), EDGE_TOL_S)}


def _script_lines(script, ids):
    per, unknown = {}, []
    for ln in script.get("lines", []):
        sid = ln.get("shot")
        if sid not in ids:
            unknown.append(sid)
            continue
        per[sid] = (per.get(sid, "") + " " + (ln.get("text") or "")).strip()
    return per, unknown


def check(doc, script):
    rows, lang = _src(doc)
    per, unknown = _script_lines(script, {r["id"] for r in rows})
    reasons = ["line for unknown shot %s" % u for u in unknown]
    out, tn, ts = [], 0, 0
    for r in rows:
        text = per.get(r["id"], "")
        toks = st.tokens(text)
        n, syl = len(toks), sum(st.syllables(t, lang) for t in toks)
        lo, hi = _bounds(r["n_words"])
        ok = lo <= n <= hi
        row = {"id": r["id"], "text": text, "words": n, "source_words": r["n_words"], "delta": n - r["n_words"],
               "syll": syl, "source_syll": r["n_syll"], "syll_delta": syl - r["n_syll"], "ok": ok}
        if r["n_words"] > 0 and n == 0:
            reasons.append("%s: the source speaks here (%d words) and the script is silent" % (r["id"], r["n_words"]))
        elif r["n_words"] == 0 and n > 0:
            reasons.append("%s: the source is silent here and the script speaks (%d words)" % (r["id"], n))
        elif not ok:
            reasons.append("%s: %d words vs source %d (+/-%d)" % (r["id"], n, r["n_words"], WORD_TOL))
        out.append(row)
        tn += n
        ts += r["n_words"]
    tot_ok = abs(tn - ts) <= TOTAL_TOL * ts + 1e-9 if ts else tn == 0
    if not tot_ok:
        reasons.append("total %d words vs source %d (+/-%d%%)" % (tn, ts, int(TOTAL_TOL * 100)))
    res = {"pass": not reasons, "shots": out,
           "total": {"words": tn, "source": ts, "delta_pct": round(100.0 * (tn - ts) / ts, 1) if ts else None, "ok": tot_ok},
           "reasons": reasons}
    if not ts:
        res.update(no_speech=True, note=_no_speech_note(doc))
    return res


def _split_counts(counts, n):
    """Scale counts to sum n (largest remainder)."""
    s = float(sum(counts))
    if not s:
        return [0] * len(counts)
    raw = [c * n / s for c in counts]
    fl = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - fl[i], reverse=True)[:n - sum(fl)]:
        fl[i] += 1
    return fl


def align(doc, words, vo_start=0.0, script=None):
    rows, lang = _src(doc)
    spoken = [r for r in rows if r["start"] is not None]
    if not spoken:
        raise ValueError("align needs speech in the source: " + _no_speech_note(doc))
    if not words:
        raise ValueError("the voiceover transcript has no words")
    if script:
        per, _ = _script_lines(script, {r["id"] for r in rows})
        counts = [len(st.tokens(per.get(r["id"], ""))) for r in spoken]
        if sum(counts) != len(words):
            counts = _split_counts(counts, len(words))
    else:
        counts = _split_counts([r["n_words"] for r in spoken], len(words))
    src_start, src_end = spoken[0]["start"], max(r["end"] for r in spoken)
    new_start, new_end = words[0]["start"], words[-1]["end"]
    raw_tempo = (new_end - new_start) / max(src_end - src_start, 1e-3)
    tempo = min(ATEMPO_MAX, max(ATEMPO_MIN, raw_tempo))
    sug_start = src_start - new_start / tempo
    phrases, i = [], 0
    for r, c in zip(spoken, counts):
        ws = words[i:i + c]
        i += c
        if not ws:
            phrases.append({"id": r["id"], "words": 0, "offset": None, "offset_after": None})
            continue
        a, b = ws[0]["start"], ws[-1]["end"]
        off = a + vo_start - r["start"]
        off_after = a / tempo + sug_start - r["start"]
        phrases.append({"id": r["id"], "words": c, "text": " ".join(w["text"] for w in ws),
                        "vo_start": round(a, 3), "vo_end": round(b, 3), "source_start": r["start"],
                        "offset": round(off, 3), "offset_after": round(off_after, 3)})
    s_err, e_err = new_start + vo_start - src_start, new_end + vo_start - src_end
    ok = abs(s_err) <= EDGE_TOL_S and abs(e_err) <= EDGE_TOL_S
    return {"pass": ok, "vo_start": vo_start,
            "source": {"start": src_start, "end": src_end, "span": round(src_end - src_start, 3)},
            "vo": {"start": round(new_start, 3), "end": round(new_end, 3), "span": round(new_end - new_start, 3),
                   "words": len(words)},
            "start_err": round(s_err, 3), "end_err": round(e_err, 3), "tolerance_s": EDGE_TOL_S,
            "suggest": {"atempo": round(tempo, 4), "atempo_raw": round(raw_tempo, 4), "clamped": tempo != raw_tempo,
                        "vo_start": round(sug_start, 3),
                        "end_err_after": round(new_end / tempo + sug_start - src_end, 3)},
            "phrases": phrases,
            "phrases_off": [{"id": p["id"], "offset_after": p["offset_after"],
                             "action": "split at the pause before this phrase and shift it by %+.2f s" % -p["offset_after"]}
                            for p in phrases if p["offset_after"] is not None and abs(p["offset_after"]) > PHRASE_TOL_S]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("shots")
    c = sub.add_parser("check")
    c.add_argument("shots")
    c.add_argument("script")
    a_ = sub.add_parser("align")
    a_.add_argument("shots")
    a_.add_argument("transcript")
    a_.add_argument("--vo-start", type=float, default=0.0)
    a_.add_argument("--script")
    a = ap.parse_args(argv)
    try:
        return _run(a)
    except Exception as e:  # every error is a JSON line and exit 2, never a traceback
        msg = "%s: %s" % (type(e).__name__, e) if not isinstance(e, ValueError) else str(e)
        print(json.dumps({"pass": False, "error": msg}, indent=1, ensure_ascii=False))
        return 2


def _run(a):
    doc = _load(a.shots)
    if not isinstance(doc, dict) or not isinstance(doc.get("shots"), list):
        raise ValueError("%s is not a shots.json (no shots[])" % a.shots)
    if a.cmd == "plan":
        print(json.dumps(plan(doc), indent=1, ensure_ascii=False))
        return 0
    if a.cmd == "check":
        res = check(doc, _load(a.script))
        print(json.dumps(res, indent=1, ensure_ascii=False))
        return 0 if res["pass"] else 1
    words, _ = st.load_words(a.transcript)
    res = align(doc, words, a.vo_start, _load(a.script) if a.script else None)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
