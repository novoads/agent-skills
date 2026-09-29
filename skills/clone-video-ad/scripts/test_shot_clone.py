#!/usr/bin/env python3
"""Executable test for the clone-video-ad shot route: shot_table.py, pace.py, assemble.py.

  python3 skills/clone-video-ad/scripts/test_shot_clone.py [--keep]

Builds its own fixtures with ffmpeg lavfi sources in a temp dir (no network, nothing
read from outside the repo), prints one line per case and "N cases, M failed", and
exits non-zero on any failure. Covers: cuts at both thresholds within one frame, the
anchor merge, a flash folded (not a shot), confirm_cut on a 0.12-only cut, words per
shot, frames and strips, re-running shot_table keeps the `new` ledger, the hue gate
(PASS on a hue-protected grade, FAIL on eq=saturation=0.4 and on a +10 deg rotation,
NO_PRODUCT on a grey product), the opening lock (>= 0.90 on a 2 % centre zoom, < 0.90 on
another image), the frozen and invented-cut checks, build at 24 and 30 fps (duration
within one frame, twin written), verify, a --talker window replacing the voiceover in
its shot, and pace check/align on canned words[]. The review-fix cases: LIGHT without a
photo refused and NO_PRODUCT never a pass, a coloured-backdrop photo refused, an aspect
mismatch refused unless --allow-crop, a re-run keeping a hand merge and --resegment
refusing once a take exists, a whip pan folded as whip_s, two flashes summed, strips near
the end, the windowed motion floor, pace's JSON errors and silent shots, and verify's
one-hit-per-cut rule. The re-review cases: a pastel photo refused under LIGHT (--allow-grey
for a neutral product), takes at the requested aspect from a 4:5 source cropped with a
NOTICE while takes off it are refused, and the packshot gate (a tight crop and a product
with a second-colour label pass, a coloured backdrop and three equal colours are refused).
Requires ffmpeg/ffprobe on PATH. Python stdlib only, no pytest.
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # importing the sibling scripts leaves no __pycache__
sys.path.insert(0, str(HERE))
import assemble as asm  # noqa: E402
import pace  # noqa: E402
import shot_table as st  # noqa: E402

RESULTS = []
W, H = 360, 640
PINK = "0xE0508C"


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *[str(a) for a in args]], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("fixture ffmpeg failed: %s\n%s" % (" ".join(map(str, args))[:300], r.stderr[-600:]))


def script(name, *args):
    r = subprocess.run([sys.executable, str(HERE / name), *[str(a) for a in args]], capture_output=True, text=True)
    try:
        out = json.loads(r.stdout) if r.stdout.strip() else None
    except ValueError:
        out = None
    return r.returncode, out, r.stderr


def case(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # a crash is a failed case, never a crashed suite
        ok, detail = False, "%s: %s" % (type(e).__name__, str(e)[-300:])
    RESULTS.append(ok)
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def circ(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def enc(out, *pre, fps=30):
    ffmpeg(*pre, "-c:v", "libx264", "-preset", "veryfast", "-crf", "10", "-pix_fmt", "yuv420p", "-r", fps, "-an", out)


# ------------------------------------------------------------------ fixtures
def make_cut_source(d):
    """30 fps, 4.0 s: A | B (0.25 cut at 1.0) | C (0.12-only at 2.0) | white flash 3.0-3.1 |
    D1 (0.25 at 3.1) | D2 (0.12-only at 3.167, merges into the 3.1 anchor)."""
    # select's scene score is about |dY|/100 on a static cut: a 20-level RGB step reads
    # ~0.17 (0.12-only), 40+ clears 0.25.
    segs = [("0x303030", 30), ("0xC0C0C0", 30), ("0xACACAC", 30), ("0xFFFFFF", 3), ("0x202020", 2), ("0x343434", 25)]
    fc = ";".join("color=c=%s:s=%dx%d:r=30,trim=end_frame=%d,setpts=PTS-STARTPTS[s%d]" % (c, W, H, n, i)
                  for i, (c, n) in enumerate(segs))
    fc += ";" + "".join("[s%d]" % i for i in range(len(segs))) + "concat=n=%d:v=1:a=0[v]" % len(segs)
    out = d / "cut_source.mp4"
    enc(out, "-filter_complex", fc, "-map", "[v]")
    words = [("Wait", 0.20, 0.40), ("you", 0.45, 0.60), ("bought", 0.62, 0.90),
             ("it", 1.10, 1.20), ("on", 1.25, 1.35), ("Amazon?", 1.40, 1.90),
             ("Those", 3.30, 3.50), ("aren't", 3.55, 3.75), ("real", 3.80, 3.95)]
    tr = d / "transcript.json"
    tr.write_text(json.dumps({"language": "en", "words": [{"text": w, "start": a, "end": b, "type": "word"}
                                                          for w, a, b in words]}))
    return out, tr, words


def make_photo(d, color, name, bg="white"):
    p = d / name
    src = "color=c=%s:s=480x360,format=yuv420p,drawbox=x=140:y=80:w=200:h=200:color=%s:t=fill" % (bg, color)
    # JPEG bytes under a .png name: the band must sniff the type, never trust the name
    # (ffmpeg's image2 demuxer would pick the png decoder from the extension and fail).
    ffmpeg("-f", "lavfi", "-i", src, "-frames:v", "1", "-c:v", "mjpeg", "-q:v", "2", "-f", "image2", p)
    return p


def colors(d, name, segs, w=W, h=H, fps=30):
    """Flat colour segments [(colour, frames), ...] concatenated at fps."""
    fc = ";".join("color=c=%s:s=%dx%d:r=%s,trim=end_frame=%d,setpts=PTS-STARTPTS[s%d]" % (c, w, h, fps, n, i)
                  for i, (c, n) in enumerate(segs))
    fc += ";" + "".join("[s%d]" % i for i in range(len(segs))) + "concat=n=%d:v=1:a=0[v]" % len(segs)
    out = d / name
    enc(out, "-filter_complex", fc, "-map", "[v]", fps=fps)
    return out


def product_clip(d, name, bg="0x2050B0", dur=3, fps=24, base=None):
    src = base or "color=c=%s:s=%dx%d:r=%d:d=%s" % (bg, W, H, fps, dur)
    vf = ("format=yuv420p,drawbox=x=40:y=60:w=120:h=120:color=0x30B040:t=fill,"
          "drawbox=x=60:y=300:w=150:h=200:color=%s:t=fill" % PINK)  # in drawbox, t is thickness, not time
    out = d / name
    enc(out, "-f", "lavfi", "-i", src, "-vf", vf, fps=fps)
    return out


# ------------------------------------------------------------------ cases
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    d = Path(tempfile.mkdtemp(prefix="shot_clone_test_"))
    try:
        run_cases(d)
    finally:
        if a.keep:
            print("fixtures kept in %s" % d)
        else:
            shutil.rmtree(str(d), ignore_errors=True)
    failed = RESULTS.count(False)
    print("%d cases, %d failed" % (len(RESULTS), failed))
    return 1 if failed else 0


def run_cases(d):
    src, tr, words = make_cut_source(d)
    frame = 1 / 30.0
    job = d / "job"
    code, _, err = script("shot_table.py", src, "--job", job, "--transcript", tr, "--no-frames")
    doc = json.loads((job / "shots.json").read_text()) if (job / "shots.json").exists() else {"shots": [], "cuts_025": [], "cuts_012": []}
    shots = doc["shots"]

    def near(lst, t):
        return any(abs(x - t) <= frame + 1e-6 for x in lst)

    case("cuts at scene>0.25 within one frame (1.0, 3.0, 3.1)",
         lambda: (code == 0 and all(near(doc["cuts_025"], t) for t in (1.0, 3.0, 3.1)),
                  "cuts_025=%s exit=%d %s" % (doc["cuts_025"], code, err[-200:])))
    case("cut at scene>0.12 only within one frame (2.0) with confirm_cut",
         lambda: (near(doc["cuts_012"], 2.0) and any(abs(r["in"] - 2.0) <= frame and r["confirm_cut"]
                                                     and r["cut_in"]["seen_at"] == "0.12-only" for r in shots),
                  "cuts_012=%s" % doc["cuts_012"]))
    case("0.12-only hit within 0.1 s of an anchor merges (no cut at 3.167)",
         lambda: (near(doc["cuts_012"], 3.167) and not any(abs(r["in"] - 3.17) < 0.02 for r in shots),
                  "shots in=%s" % [r["in"] for r in shots]))
    case("flash folded into the next shot, not counted as a shot",
         lambda: (len(shots) == 4 and abs(shots[3]["in"] - 3.0) < 0.02 and abs(shots[3]["cut_in"]["flash_s"] - 0.1) < 0.02
                  and not any(r["dur"] <= 0.15 for r in shots) and len(doc.get("flashes", [])) == 1,
                  "shots=%s flashes=%s" % ([(r["id"], r["in"], r["out"], r["cut_in"]["flash_s"]) for r in shots],
                                           doc.get("flashes"))))
    case("words assigned per shot from words[] (3/3/0/3)",
         lambda: ([(r["speech"] or {}).get("n_words", 0) for r in shots] == [3, 3, 0, 3],
                  "n_words=%s" % [(r["speech"] or {}).get("n_words", 0) for r in shots]))

    def frames_case():
        j2 = d / "job_frames"
        c2, _, e2 = script("shot_table.py", src, "--job", j2)
        need = ["frames/SH01_in.jpg", "frames/SH01_mid.jpg", "frames/SH01_out.jpg", "strips/SH02_cut.jpg", "strips/SH04_cut.jpg"]
        missing = [p for p in need if not (j2 / p).exists()]
        return c2 == 0 and not missing, "missing=%s %s" % (missing, e2[-200:])
    case("frames/<id>_{in,mid,out}.jpg and strips/<id>_cut.jpg written", frames_case)

    # ---- hue gate
    photo = make_photo(d, PINK, "photo_pink.png")
    grey = make_photo(d, "0x808080", "photo_grey.png")
    ung = product_clip(d, "ungraded.mp4")
    band = asm.product_band(photo)
    prot = d / "graded_protected.mp4"
    enc(prot, "-i", ung, "-vf", asm.hue_protected_grade_filter(band, 0.3), fps=24)
    sat = d / "graded_sat04.mp4"
    enc(sat, "-i", ung, "-vf", "eq=saturation=0.4", fps=24)
    rot = d / "graded_hue10.mp4"
    enc(rot, "-i", ung, "-vf", "hue=h=10", fps=24)

    def gate(clip, ph, want_code, want_verdict):
        c, out, e = script("assemble.py", "hue-gate", clip, "--ungraded", ung, "--photo", ph, "--windows", "0-1.5,1.5-3")
        out = out or {}
        return (c == want_code and out.get("verdict") == want_verdict,
                "exit=%d verdict=%s kept=%s drift=%s cov=%s %s" % (c, out.get("verdict"), out.get("chroma_retained"),
                                                                    out.get("hue_drift"), out.get("coverage"), e[-150:]))
    case("photo type sniffed from bytes (%s under a .png name)" % st.sniff_mime(photo),
         lambda: (band.get("band") is True and st.sniff_mime(photo) == "image/jpeg",
                  "band=%s" % {k: band.get(k) for k in ("mime", "center", "half_width", "chroma_floor")}))
    case("hue gate PASSes a hue-protected grade (k=0.3)", lambda: gate(prot, photo, 0, "PASS"))
    case("hue gate FAILs eq=saturation=0.4", lambda: gate(sat, photo, 1, "FAIL"))
    case("hue gate FAILs a +10 deg hue rotation", lambda: gate(rot, photo, 1, "FAIL"))
    case("hue gate reports NO_PRODUCT on a grey product photo (exit 2)", lambda: gate(prot, grey, 2, "NO_PRODUCT"))

    # ---- opening lock and the other free checks
    still = d / "still.png"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=%dx%d" % (W, H), "-frames:v", "1", still)
    other = d / "other.png"
    ffmpeg("-f", "lavfi", "-i", "mandelbrot=s=%dx%d" % (W, H), "-frames:v", "1", other)
    take = d / "take_zoom2.mp4"
    enc(take, "-f", "lavfi", "-i", "testsrc2=s=%dx%d:r=24:d=2" % (W, H),
        "-vf", "crop=iw/1.02:ih/1.02,scale=%d:%d" % (W, H), fps=24)
    frozen = d / "take_frozen.mp4"
    enc(frozen, "-loop", "1", "-i", still, "-t", "2", fps=24)
    cutty = d / "take_cut.mp4"
    enc(cutty, "-f", "lavfi", "-i", "testsrc2=s=%dx%d:r=24:d=1" % (W, H), "-f", "lavfi", "-i",
        "smptebars=s=%dx%d:r=24:d=1" % (W, H), "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]", fps=24)

    def chk(tk, st_, dur, want_code, pred):
        c, out, e = script("assemble.py", "check", tk, "--still", st_, "--dur", dur)
        out = out or {}
        return c == want_code and pred(out), "exit=%d lock=%s motion=%s cuts=%s %s" % (
            c, out.get("opening_lock"), (out.get("motion") or {}).get("mean_absdiff"), out.get("invented_cuts"), e[-150:])
    case("opening lock >= 0.90 on a 2% centre-zoomed take (check passes)",
         lambda: chk(take, still, 1.5, 0, lambda o: o["opening_lock"]["ssim"] >= 0.90 and 1.01 <= o["opening_lock"]["scale"] <= 1.03))
    case("opening lock < 0.90 against a different image (check fails)",
         lambda: chk(take, other, 1.5, 1, lambda o: o["opening_lock"]["ssim"] < 0.90))
    case("check fails a frozen take on motion", lambda: chk(frozen, still, 1.5, 1, lambda o: not o["motion"]["pass"]))
    case("check fails an invented cut inside [0, D]", lambda: chk(cutty, still, 1.5, 1, lambda o: len(o["invented_cuts"]) >= 1))

    # ---- ledger + build + verify
    t1 = product_clip(d, "t1.mp4", bg="0x2050B0", dur=3)
    t2 = product_clip(d, "t2.mp4", base="testsrc2=s=%dx%d:r=24:d=3" % (W, H))
    t3 = product_clip(d, "t3.mp4", bg="0x205020", dur=3)
    hold = d / "hold.png"
    ffmpeg("-f", "lavfi", "-i", "smptebars=s=%dx%d" % (W, H), "-vf",
           "drawbox=x=100:y=250:w=160:h=160:color=%s:t=fill" % PINK, "-frames:v", "1", hold)
    sj = job / "shots.json"
    doc = json.loads(sj.read_text())
    doc["product_photo"] = str(photo)
    rows = {r["id"]: r for r in doc["shots"]}
    for sid, path in (("SH01", t1), ("SH02", t2), ("SH04", t3)):
        rows[sid]["render"] = "take"
        rows[sid]["new"]["takes"] = [{"jobId": "job-" + sid, "status": "done", "path": str(path), "pick": True}]
    rows["SH01"]["framing"] = "CU"
    rows["SH03"]["render"] = "hold"
    rows["SH03"]["new"]["still_path"] = str(hold)
    rows["SH03"]["cut_in"]["type"] = "whip-right"
    rows["SH02"]["cut_in"]["type"] = "hard"
    sj.write_text(json.dumps(doc, indent=1))

    def rerun():
        c, _, e = script("shot_table.py", src, "--job", job, "--transcript", tr, "--no-frames")
        d2 = json.loads(sj.read_text())
        r2 = {r["id"]: r for r in d2["shots"]}
        ok = (c == 0 and r2["SH01"]["new"]["takes"][0]["jobId"] == "job-SH01" and r2["SH01"]["framing"] == "CU"
              and r2["SH03"]["new"]["still_path"] == str(hold) and r2["SH03"]["cut_in"]["type"] == "whip-right"
              and r2["SH03"]["render"] == "hold" and d2.get("product_photo") == str(photo)
              and (r2["SH01"]["speech"] or {}).get("n_words") == 3)
        return ok, "exit=%d %s" % (c, e[-200:])
    case("re-running shot_table.py keeps the new ledger and Claude's fields", rerun)

    builds = {}
    for fps in (24, 30):
        jb = d / ("build%d" % fps)
        jb.mkdir()
        shutil.copyfile(str(sj), str(jb / "shots.json"))

        def bcase(fps=fps, jb=jb):
            c, out, e = script("assemble.py", "build", jb / "shots.json", "--grade", "light", "--fps", fps)
            m, t = jb / "master.mp4", jb / "master_ungraded.mp4"
            if not (m.exists() and t.exists()):
                return False, "exit=%d no master/twin %s" % (c, e[-300:])
            pm, pt = st.probe(str(m)), st.probe(str(t))
            dur = pm["nb_frames"] / pm["fps"]
            builds[fps] = jb
            ok = (c == 0 and abs(dur - 4.0) <= 1.0 / fps + 1e-3 and pm["nb_frames"] == pt["nb_frames"]
                  and round(pm["fps"]) == fps and (pm["width"], pm["height"]) == (W, H)
                  and json.loads((jb / "assembly.json").read_text())["hue_gate"]["verdict"] == "PASS")
            return ok, "exit=%d frames=%s/%s dur=%.4f fps=%s hue=%s" % (
                c, pm["nb_frames"], pt["nb_frames"], dur, pm["fps"], (out or {}).get("hue_gate"))
        case("build --fps %d: duration within one frame, graded twin written, hue gate PASS" % fps, bcase)

    def vcase():
        jb = builds.get(24)
        if not jb:
            return False, "no 24 fps build"
        c, out, e = script("assemble.py", "verify", jb / "master.mp4", jb / "shots.json")
        out = out or {}
        return c == 0 and out.get("pass") and out.get("duration_ok"), "exit=%d cuts=%s %s" % (
            c, [(x["id"], x.get("measured"), x.get("err"), x["ok"]) for x in out.get("cuts", [])], e[-150:])
    case("verify: duration within a frame and every table cut matched (24 fps)", vcase)

    def tones(path, a, b):
        """Goertzel magnitude of the 440 Hz (voiceover) and 1000 Hz (talker) tones in the
        master's audio over [a, b], mono 48 kHz: which voice is audible there."""
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % a, "-t", "%.3f" % (b - a), "-i", str(path),
                            "-vn", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True)
        pcm = [int.from_bytes(r.stdout[i:i + 2], "little", signed=True) for i in range(0, len(r.stdout) - 1, 2)]
        mags = {}
        for f in (440, 1000):
            w = 2 * math.cos(2 * math.pi * f / 48000.0)
            s1 = s2 = 0.0
            for x in pcm:
                s1, s2 = x + w * s1 - s2, s1
            mags[f] = math.sqrt(max(0.0, s1 * s1 + s2 * s2 - w * s1 * s2)) / max(1, len(pcm))
        return mags

    def talker_case():
        jt = d / "build_talker"
        jt.mkdir()
        shutil.copyfile(str(sj), str(jt / "shots.json"))
        vo_wav, talk_wav = d / "vo_440.wav", d / "talker_1000.wav"
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=4", vo_wav)
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000:duration=3", talk_wav)
        c, out, e = script("assemble.py", "build", jt / "shots.json", "--grade", "none",
                           "--vo", vo_wav, "--vo-start", 0, "--talker", "SH02=%s" % talk_wav)
        m = jt / "master.mp4"
        if not m.exists():
            return False, "exit=%d no master %s" % (c, e[-300:])
        # SH02 is the 1.0-2.0 s window (hard cuts both sides): talker inside, voiceover outside.
        win = {"before": tones(m, 0.2, 0.8), "inside": tones(m, 1.15, 1.85), "after": tones(m, 2.2, 2.8)}
        ratio = {k: round(v[1000] / max(v[440], 1e-9), 2) for k, v in win.items()}  # talker / voiceover
        rec = json.loads((jt / "assembly.json").read_text())
        tk = (rec.get("audio") or {}).get("talkers") or []
        ok = (c == 0 and ratio["inside"] > 20 and ratio["before"] < 0.05 and ratio["after"] < 0.05
              and len(tk) == 1 and tk[0]["id"] == "SH02"
              and abs(tk[0]["a"] - 1.0) < 1e-6 and abs(tk[0]["b"] - 2.0) < 1e-6)
        return ok, "exit=%d talker/vo=%s window=%s %s" % (c, ratio, [(t["a"], t["b"], t["gain_db"]) for t in tk], e[-150:])
    case("build --talker SH02=...: the shot's window carries the talker audio, the rest the voiceover",
         talker_case)

    # ---- pace
    good = d / "script_good.json"
    good.write_text(json.dumps({"lines": [{"shot": "SH01", "text": "You bought it"},
                                          {"shot": "SH02", "text": "on the marketplace?"},
                                          {"shot": "SH04", "text": "Those aren't real"}]}))
    bad = d / "script_bad.json"
    bad.write_text(json.dumps({"lines": [{"shot": "SH01", "text": "one two three four five"},
                                         {"shot": "SH02", "text": "on the marketplace?"}]}))

    def pcheck(scr, want_code, pred):
        c, out, e = script("pace.py", "check", sj, scr)
        out = out or {}
        return c == want_code and pred(out), "exit=%d total=%s reasons=%s %s" % (c, out.get("total"), out.get("reasons"), e[-150:])
    case("pace check passes words within +/-1 per shot and total within 5%",
         lambda: pcheck(good, 0, lambda o: o["pass"] and o["total"]["words"] == 9))
    case("pace check fails +2 words on a shot and a silent spoken shot",
         lambda: pcheck(bad, 1, lambda o: any("SH01" in r for r in o["reasons"]) and any("SH04" in r for r in o["reasons"])))
    vo_ok = d / "vo_ok.json"
    vo_ok.write_text(json.dumps({"words": [{"text": w, "start": a_ - 0.2, "end": b_ - 0.2} for w, a_, b_ in words]}))
    vo_late = d / "vo_late.json"
    vo_late.write_text(json.dumps({"words": [{"text": w, "start": a_ + 0.2, "end": b_ + 0.2} for w, a_, b_ in words]}))

    def palign(tr_, vs, want_code, pred):
        c, out, e = script("pace.py", "align", sj, tr_, "--vo-start", vs)
        out = out or {}
        return c == want_code and pred(out), "exit=%d start_err=%s end_err=%s suggest=%s off=%s %s" % (
            c, out.get("start_err"), out.get("end_err"), out.get("suggest"), out.get("phrases_off"), e[-150:])
    case("pace align passes a VO placed on the source's speech (vo-start 0.2)",
         lambda: palign(vo_ok, 0.2, 0, lambda o: abs(o["start_err"]) < 1e-6 and o["phrases_off"] == []
                        and abs(o["suggest"]["atempo"] - 1.0) < 1e-6))
    case("pace align fails a VO 0.4 s late and suggests vo-start -0.2",
         lambda: palign(vo_late, 0.2, 1, lambda o: abs(o["start_err"] - 0.4) < 1e-6 and abs(o["suggest"]["vo_start"] + 0.2) < 1e-6))
    code_p, out_p, _ = script("pace.py", "plan", sj)
    case("pace plan gives per-shot word targets",
         lambda: (code_p == 0 and [(s["words_min"], s["words_max"]) for s in out_p["shots"]] == [(2, 4), (2, 4), (0, 0), (2, 4)],
                  "targets=%s" % [(s["id"], s["words_min"], s["words_max"]) for s in (out_p or {}).get("shots", [])]))
    review_fix_cases(d, sj, src, still, frozen, grey, prot, ung, vo_ok, out_p)
    rereview_fix_cases(d, sj, grey)


def review_fix_cases(d, sj, src, still, frozen, grey, prot, ung, vo_ok, out_p):
    fx = {}

    def load(p):
        return json.loads(Path(p).read_text())

    # ---- F-a: LIGHT needs a photo; NO_PRODUCT is a warning, never a pass
    def fa_refuse():
        jf = d / "fa_nophoto"
        jf.mkdir()
        dd = load(sj)
        dd.pop("product_photo", None)
        (jf / "shots.json").write_text(json.dumps(dd))
        c, out, e = script("assemble.py", "build", jf / "shots.json", "--grade", "light")
        err = (out or {}).get("error") or ""
        ok = (c == 2 and (out or {}).get("pass") is False and err == asm.LIGHT_NO_PHOTO_MSG
              and not (jf / "master.mp4").exists() and "Traceback" not in e)
        return ok, "exit=%d error=%s" % (c, err)
    case("F-a: build --grade light without a product photo exits 2 and renders nothing", fa_refuse)

    def fa_noproduct():
        jf = d / "fa_grey"
        jf.mkdir()
        shutil.copyfile(str(sj), str(jf / "shots.json"))
        c, out, e = script("assemble.py", "build", jf / "shots.json", "--grade", "light", "--photo", grey, "--allow-grey")
        rec = load(jf / "assembly.json") if (jf / "assembly.json").exists() else {}
        v = (rec.get("hue_gate") or {}).get("verdict")
        ok = (c == 0 and v == "NO_PRODUCT" and ((out or {}).get("hue_gate") or {}).get("verdict") == "NO_PRODUCT"
              and rec.get("allow_grey") is True and any("--allow-grey" in w for w in rec.get("warnings", []))
              and any(ln.startswith("WARNING: hue gate NO_PRODUCT") for ln in e.splitlines())
              and any("NO_PRODUCT" in w for w in rec.get("warnings", [])))
        return ok, "exit=%d verdict=%s stderr=%s" % (c, v, e.strip()[-160:])
    case("F-a: a NO_PRODUCT hue gate (grey product, --allow-grey) exits 0 with a WARNING line, never a PASS", fa_noproduct)

    # ---- F-b: a packshot on a coloured backdrop is not a product band
    bad = make_photo(d, PINK, "photo_pink_on_blue.png", bg="0x2050B0")

    def fb_build():
        jf = d / "fb"
        jf.mkdir()
        shutil.copyfile(str(sj), str(jf / "shots.json"))
        c, out, e = script("assemble.py", "build", jf / "shots.json", "--grade", "light", "--photo", bad)
        err = (out or {}).get("error") or ""
        b = asm.product_band(bad)
        ok = c == 2 and err.startswith(asm.PACKSHOT_MSG) and not (jf / "master.mp4").exists() and b.get("not_packshot")
        return ok, "exit=%d share=%s error=%s" % (c, b.get("photo_product_share"), err[-160:])
    case("F-b: build --grade light refuses a coloured-backdrop photo (exit 2)", fb_build)

    def fb_gate():
        c, out, e = script("assemble.py", "hue-gate", prot, "--ungraded", ung, "--photo", bad)
        out = out or {}
        ok = c == 2 and out.get("verdict") == "NO_PRODUCT" and any(asm.PACKSHOT_MSG in r for r in out.get("reasons", []))
        return ok, "exit=%d verdict=%s reasons=%s" % (c, out.get("verdict"), out.get("reasons"))
    case("F-b: hue-gate returns NO_PRODUCT with the packshot reason", fb_gate)

    # ---- F-c: aspect
    def fc_refuse():
        land = colors(d, "land.mp4", [("0x303030", 30), ("0xC0C0C0", 30)], w=640, h=360)
        jl = d / "fc_land"
        script("shot_table.py", land, "--job", jl, "--no-frames")
        dl = load(jl / "shots.json")
        tk = d / "take_portrait.mp4"
        enc(tk, "-f", "lavfi", "-i", "testsrc2=s=%dx%d:r=24:d=2" % (W, H), fps=24)
        for r in dl["shots"]:
            r["render"] = "take"
            r["new"]["takes"] = [{"path": str(tk), "pick": True}]
        (jl / "shots.json").write_text(json.dumps(dl))
        fx["fc"] = jl
        c, out, e = script("assemble.py", "build", jl / "shots.json", "--grade", "none")
        err = (out or {}).get("error") or ""
        ok = dl.get("aspect") == "16:9" and c == 2 and "--allow-crop" in err and not (jl / "master.mp4").exists()
        return ok, "aspect=%s exit=%d error=%s" % (dl.get("aspect"), c, err[-160:])
    case("F-c: shots.json aspect is 16:9 for a 16:9 source, and build refuses 9:16 takes (exit 2)", fc_refuse)

    def fc_allow():
        jl = fx.get("fc")
        if not jl:
            return False, "no fixture"
        c, out, e = script("assemble.py", "build", jl / "shots.json", "--grade", "none", "--allow-crop")
        rec = load(jl / "assembly.json") if (jl / "assembly.json").exists() else {}
        crops = rec.get("crops") or []
        ok = (c == 0 and rec.get("allow_crop") is True and len(crops) == 2
              and all(abs(x["kept_pct"] - 31.6) < 0.5 for x in crops) and "centre-cropped" in e)
        return ok, "exit=%d crops=%s" % (c, [(x["id"], x["size"], x["kept_pct"]) for x in crops])
    case("F-c: --allow-crop builds and records each crop in assembly.json", fc_allow)

    # ---- F-d: a re-run keeps the segmentation; --resegment refuses once a take exists
    def fd_keep():
        cc = colors(d, "cc.mp4", [("0x303030", 30), ("0xC0C0C0", 30), ("0xACACAC", 30)])
        jd = d / "fd"
        script("shot_table.py", cc, "--job", jd, "--no-frames")
        doc = load(jd / "shots.json")
        before = [(r["id"], r["in"], r["out"]) for r in doc["shots"]]
        sh = doc["shots"]
        sh[1]["out"] = sh[2]["out"]  # the reference's hand merge of a rejected confirm_cut row
        sh[1]["dur"] = round(sh[1]["out"] - sh[1]["in"], 2)
        del sh[2]
        for r in sh:
            r["render"] = "take"
            r["new"]["takes"] = [{"jobId": "job-" + r["id"], "path": "takes/%s_t1.mp4" % r["id"], "pick": True}]
        (jd / "shots.json").write_text(json.dumps(doc))
        fx["fd"] = (cc, jd)
        c, out, e = script("shot_table.py", cc, "--job", jd, "--no-frames")
        after = load(jd / "shots.json")["shots"]
        got = [(r["id"], r["in"], r["out"], [t["jobId"] for t in r["new"]["takes"]]) for r in after]
        ok = (len(before) == 3 and c == 0 and (out or {}).get("segmentation") == "kept"
              and got == [("SH01", 0.0, 1.0, ["job-SH01"]), ("SH02", 1.0, 3.0, ["job-SH02"])]
              and after[1]["dur"] == 2.0 and after[1]["grade"]["n_frames"] > 0)
        return ok, "exit=%d before=%s after=%s warnings=%s" % (c, before, got, (out or {}).get("warnings"))
    case("F-d: a re-run after a hand merge keeps the merged rows and their takes", fd_keep)

    def fd_reseg():
        if "fd" not in fx:
            return False, "no fixture"
        cc, jd = fx["fd"]
        c, out, e = script("shot_table.py", cc, "--job", jd, "--no-frames", "--resegment")
        refused = (c == 2 and "--resegment refused" in ((out or {}).get("error") or "")
                   and len(load(jd / "shots.json")["shots"]) == 2)
        doc = load(jd / "shots.json")
        for r in doc["shots"]:
            r["new"]["takes"] = []
        (jd / "shots.json").write_text(json.dumps(doc))
        c2, out2, e2 = script("shot_table.py", cc, "--job", jd, "--no-frames", "--resegment")
        n = len(load(jd / "shots.json")["shots"])
        ok = refused and c2 == 0 and n == 3 and (out2 or {}).get("segmentation") == "resegmented"
        return ok, "refuse exit=%d, no-take resegment exit=%d rows=%d" % (c, c2, n)
    case("F-d: --resegment refuses (exit 2) while a row has a take, and re-cuts once none has", fd_reseg)

    # ---- F-e: a whip pan's frames fold into the next row
    def fe_whip():
        whip = d / "whip.mp4"
        fc = ("mandelbrot=s=1440x640:r=30,trim=end_frame=1,loop=loop=200:size=1,setpts=N/30/TB[m];"
              "[m]split=2[m1][m2];"
              "[m1]crop=%d:%d:0:0,trim=end_frame=30,setpts=PTS-STARTPTS[a];"
              "[m2]crop=%d:%d:'min(n*260,1080)':0,trim=end_frame=5,setpts=PTS-STARTPTS[w];"
              "color=c=0x406080:s=%dx%d:r=30,trim=end_frame=30,setpts=PTS-STARTPTS[b];"
              "[a][w][b]concat=n=3:v=1:a=0[v]" % (W, H, W, H, W, H))
        enc(whip, "-filter_complex", fc, "-map", "[v]")
        je = d / "fe"
        c, out, e = script("shot_table.py", whip, "--job", je, "--no-frames")
        rows = load(je / "shots.json")["shots"]
        ci = (rows[1].get("cut_in") or {}) if len(rows) > 1 else {}
        ok = (c == 0 and len(rows) == 2 and 0.1 <= (ci.get("whip_s") or 0) < 0.2 and ci.get("type_hint") == "whip"
              and all(r["dur"] >= 0.2 for r in rows))
        return ok, "rows=%s" % [(r["id"], r["in"], r["out"], (r.get("cut_in") or {}).get("whip_s")) for r in rows]
    case("F-e: a 5-frame whip pan folds into the next row as cut_in.whip_s, not a row", fe_whip)

    def fe_tail():
        tail = colors(d, "tail013.mp4", [("0x707070", 56), ("0x202020", 4)])  # a darker 0.13 s last shot
        jt = d / "fe_tail"
        c, out, e = script("shot_table.py", tail, "--job", jt, "--no-frames")
        rows = load(jt / "shots.json")["shots"]
        last = rows[-1] if rows else {}
        ok = (c == 0 and len(rows) == 2 and abs(last.get("in", 0) - 1.87) < 0.02 and last.get("render_hint") == "hold_candidate"
              and not (last.get("cut_in") or {}).get("whip_s") and not rows[0].get("tail_flash_s"))
        return ok, "rows=%s" % [(r["id"], r["in"], r["out"], r["render_hint"]) for r in rows]
    case("F-e: a cut 0.13 s before EOF stays its own row (nothing to fold into)", fe_tail)

    # ---- F-f: consecutive flashes add up
    def ff_flashes():
        series = [{"t": i / 30.0, "YAVG": 30.0 if i / 30.0 < 1.0 else (235.0 if i / 30.0 < 1.2 else 40.0)} for i in range(66)]
        cuts = [{"t": 1.0, "score": 0.9, "seen_at": "0.25", "confirm_cut": False},
                {"t": 1.1, "score": 0.2, "seen_at": "0.25", "confirm_cut": False},
                {"t": 1.2, "score": 0.9, "seen_at": "0.25", "confirm_cut": False}]
        sh, fl = st.segments_to_shots(cuts, series, 2.2, 30.0)
        cov = sum(x["b"] - x["a"] for x in sh)
        ok = (len(sh) == 2 and abs(sh[1]["a"] - 1.0) < 1e-6 and abs(sh[1]["flash_s"] - 0.2) < 1e-6
              and len(fl) == 2 and abs(cov - 2.2) < 1e-6)
        return ok, "shots=%s flashes=%d covered=%.3f" % ([(x["a"], x["b"], round(x["flash_s"], 3)) for x in sh], len(fl), cov)
    case("F-f: two consecutive flash segments sum into one flash_s and the shots cover the source", ff_flashes)

    # ---- F-g: strips near the end
    def fg_row():
        late = colors(d, "late2.mp4", [("0x303030", 54), ("0xC0C0C0", 6)])  # a 0.2 s last shot
        jg = d / "fg"
        c, out, e = script("shot_table.py", late, "--job", jg)
        rows = load(jg / "shots.json")["shots"]
        last = rows[-1] if rows else {}
        # 1.55-2.0 s holds 13 frames at 30 fps: 13 tiles, not 15 with two left blank
        want = 13 * st.STRIP_TILE_W + 12 * 2
        size = asm._image_size(jg / last["strip"]) if last.get("strip") and (jg / last["strip"]).is_file() else None
        ok = c == 0 and len(rows) == 2 and size is not None and size[0] == want
        return ok, "rows=%s strip=%s size=%s want width %d" % ([(r["id"], r["in"], r["out"]) for r in rows],
                                                               last.get("strip"), size, want)
    case("F-g: a cut 0.2 s before the end gets a strip with one tile per frame left", fg_row)

    def fg_eof():
        late = colors(d, "late1.mp4", [("0x303030", 57), ("0xC0C0C0", 3)])  # a cut 0.1 s before the end
        jg = d / "fg1"
        c, out, e = script("shot_table.py", late, "--job", jg)
        rows = load(jg / "shots.json")["shots"]
        named = [r["strip"] for r in rows if r.get("strip")]
        direct = d / "strip_eof.jpg"
        wrote = st.grab_strip(str(late), 1.9, 30.0, direct, 2.0)
        # a strip that cannot be written (the source is gone) leaves row.strip unset
        row = {"id": "SH02", "in": 1.0, "out": 2.0, "cut_in": {}}
        ctx = {"src": str(d / "gone.mp4"), "fps": 30.0, "duration": 2.0, "stats": [], "transcript": None}
        (d / "fg_gone" / "frames").mkdir(parents=True)
        (d / "fg_gone" / "strips").mkdir()
        warn = []
        st.refresh_row(row, 1, 2, ctx, d / "fg_gone", True, warn)
        ok = (c == 0 and all((jg / x).is_file() for x in named) and wrote and direct.is_file()
              and "strip" not in row and any("no strip" in w for w in warn))
        return ok, "rows=%s strips=%s direct=%s unwritable-row strip=%s" % (
            [(r["id"], r["in"], r["out"]) for r in rows], named, wrote, row.get("strip"))
    case("F-g: a cut 0.1 s before EOF: a strip is written, and row.strip is set only when its file exists", fg_eof)

    # ---- F-h: motion floor over sliding windows
    def fh_motion():
        still23 = d / "still23.png"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=720x1080", "-frames:v", "1", still23)
        push = d / "take_pushin.mp4"
        enc(push, "-loop", "1", "-i", still23, "-t", "2", "-vf",
            "crop=ih*9/16:ih,crop=iw/1.02:ih/1.02,scale=%d:%d,zoompan=z='1+0.002*on':d=1:s=%dx%d:fps=24" % (W, H, W, H), fps=24)
        c, out, e = script("assemble.py", "check", push, "--still", still23, "--dur", 1.5)
        mo = (out or {}).get("motion") or {}
        c2, out2, _ = script("assemble.py", "check", frozen, "--still", still, "--dur", 1.5)
        mo2 = (out2 or {}).get("motion") or {}
        ok = c == 0 and mo.get("pass") is True and c2 == 1 and mo2.get("pass") is False
        return ok, "push-in exit=%d window_max=%s; frozen exit=%d window_max=%s (floor %s)" % (
            c, mo.get("window_max"), c2, mo2.get("window_max"), asm.MOTION_FLOOR)
    case("F-h: a smooth push-in on a static detailed frame passes check; a frozen take fails", fh_motion)

    # ---- F-i: pace errors are JSON; silent shots agree
    def fi_silent():
        scr = d / "script_silent_shot.json"
        scr.write_text(json.dumps({"lines": [{"shot": "SH01", "text": "You bought it"},
                                             {"shot": "SH02", "text": "on the marketplace?"},
                                             {"shot": "SH03", "text": "Hmm"},
                                             {"shot": "SH04", "text": "Those aren't real"}]}))
        c, out, e = script("pace.py", "check", sj, scr)
        reasons = (out or {}).get("reasons") or []
        plan_sh03 = [x for x in (out_p or {}).get("shots", []) if x["id"] == "SH03"]
        ok = (c == 1 and any(r.startswith("SH03") and "silent" in r for r in reasons)
              and plan_sh03 and plan_sh03[0]["words_max"] == 0)
        return ok, "exit=%d reasons=%s" % (c, reasons)
    case("F-i: pace check refuses 1 word on a silent shot, as plan's words_max 0 says", fi_silent)

    def fi_errors():
        jn = d / "fi_speechless"
        jn.mkdir()
        dd = load(sj)
        dd.pop("transcript", None)
        for r in dd["shots"]:
            r["speech"] = None
        (jn / "shots.json").write_text(json.dumps(dd))
        c1, o1, e1 = script("pace.py", "align", jn / "shots.json", vo_ok)
        c2, o2, e2 = script("pace.py", "check", sj, d / "no_such_script.json")
        c3, o3, e3 = script("pace.py", "plan", jn / "shots.json")
        ok = (c1 == 2 and (o1 or {}).get("pass") is False and "speech" in ((o1 or {}).get("error") or "")
              and c2 == 2 and (o2 or {}).get("pass") is False and bool((o2 or {}).get("error"))
              and "Traceback" not in e1 + e2 and c3 == 0 and (o3 or {}).get("no_speech") is True)
        return ok, "align exit=%d %s | check exit=%d %s | plan no_speech=%s" % (
            c1, (o1 or {}).get("error"), c2, (o2 or {}).get("error"), (o3 or {}).get("no_speech"))
    case("F-i: pace errors print JSON with exit 2 (no traceback); plan names a source with no speech", fi_errors)

    # ---- F-j: one measured hit per table cut
    def fj_claims():
        m = colors(d, "fj_master.mp4", [("0x303030", 30), ("0xC0C0C0", 30)])  # one real cut, at 1.0
        jj = d / "fj"
        jj.mkdir()
        rows = [{"id": "SH01", "in": 0.0, "out": 1.0}, {"id": "SH02", "in": 1.0, "out": 1.04, "cut_in": {}},
                {"id": "SH03", "in": 1.04, "out": 2.0, "cut_in": {}}]
        (jj / "shots.json").write_text(json.dumps({"duration": 2.0, "shots": rows}))
        c, out, e = script("assemble.py", "verify", m, jj / "shots.json")
        cuts = (out or {}).get("cuts") or []
        hit = [x.get("measured") for x in cuts if x.get("ok")]
        ok = (c == 1 and len(cuts) == 2 and len(hit) == 1 and any("claimed by SH02" in (x.get("note") or "") for x in cuts))
        return ok, "exit=%d cuts=%s" % (c, [(x["id"], x.get("measured"), x["ok"], x.get("note")) for x in cuts])
    case("F-j: verify never lets two table cuts claim the same measured hit", fj_claims)


def rereview_fix_cases(d, sj, grey):
    """N1 (a low-chroma photo under LIGHT), N2 (a source no API aspect matches), N3 (the
    packshot gate: an edge-ring backdrop test plus a dominant-hue cluster)."""
    def load(p):
        return json.loads(Path(p).read_text())

    def photo(name, fc):
        p = d / name
        ffmpeg("-f", "lavfi", "-i", "color=c=white:s=480x360,format=yuv420p," + fc if not fc.startswith("color=") else fc,
               "-frames:v", "1", p)
        return p

    # ---- N1: a pastel product is refused under LIGHT; --allow-grey is recorded
    pastel = photo("photo_pastel.png", "drawbox=x=140:y=80:w=200:h=200:color=0xF0E4E8:t=fill")

    def n1_refuse():
        jf = d / "n1_pastel"
        jf.mkdir()
        shutil.copyfile(str(sj), str(jf / "shots.json"))
        c, out, e = script("assemble.py", "build", jf / "shots.json", "--grade", "light", "--photo", pastel)
        err = (out or {}).get("error") or ""
        c2, out2, _ = script("assemble.py", "build", jf / "shots.json", "--grade", "none", "--photo", pastel)
        b = asm.product_band(pastel)
        ok = (c == 2 and err == asm.LOW_CHROMA_MSG and b.get("low_chroma") is True and c2 == 0)
        return ok, "light exit=%d error=%s | none exit=%d" % (c, err[-90:], c2)
    case("N1: build --grade light refuses a pastel product photo (exit 2); --grade none builds", n1_refuse)

    # ---- N2: a 4:5 source; shots.json aspect is 1:1
    def n2_setup(tag, tw, th):
        src = colors(d, "n2_src_%s.mp4" % tag, [("0x303030", 30), ("0xC0C0C0", 30)], w=288, h=360)
        jn = d / ("n2_" + tag)
        script("shot_table.py", src, "--job", jn, "--no-frames")
        dn = load(jn / "shots.json")
        tk = d / ("n2_take_%s.mp4" % tag)
        enc(tk, "-f", "lavfi", "-i", "testsrc2=s=%dx%d:r=24:d=2" % (tw, th), fps=24)
        for r in dn["shots"]:
            r["render"] = "take"
            r["new"]["takes"] = [{"path": str(tk), "pick": True}]
        (jn / "shots.json").write_text(json.dumps(dn))
        return jn, dn

    def n2_at_requested():
        jn, dn = n2_setup("sq", 288, 288)
        c, out, e = script("assemble.py", "build", jn / "shots.json", "--grade", "none")
        rec = load(jn / "assembly.json") if (jn / "assembly.json").exists() else {}
        crops = rec.get("crops") or []
        notes = [ln for ln in e.splitlines() if ln.startswith("NOTICE:")]
        ok = (dn.get("aspect") == "1:1" and dn.get("aspect_off_pct") == 20.0 and c == 0 and len(notes) == 1
              and len(crops) == 2 and all(x["why"] == "source aspect not offered" and abs(x["kept_pct"] - 80.0) < 0.5
                                          for x in crops)
              and not any("centre-cropped" in w for w in rec.get("warnings", [])))
        return ok, "aspect=%s off=%s exit=%d notices=%s crops=%s" % (
            dn.get("aspect"), dn.get("aspect_off_pct"), c, notes, [(x["id"], x["why"], x["kept_pct"]) for x in crops])
    case("N2: 1:1 takes for a 4:5 source (aspect 1:1) build without --allow-crop, one NOTICE, crops recorded",
         n2_at_requested)

    def n2_off_requested():
        jn, dn = n2_setup("tall", W, H)
        c, out, e = script("assemble.py", "build", jn / "shots.json", "--grade", "none")
        err = (out or {}).get("error") or ""
        c2, _, e2 = script("assemble.py", "build", jn / "shots.json", "--grade", "none", "--allow-crop")
        ok = (c == 2 and "not at the requested aspect (shots.json aspect 1:1)" in err and "--allow-crop" in err
              and c2 == 0 and "centre-cropped" in e2)
        return ok, "exit=%d error=%s | --allow-crop exit=%d" % (c, err[-120:], c2)
    case("N2: 9:16 takes for a 4:5 source (aspect 1:1) are refused as off the requested aspect; --allow-crop builds",
         n2_off_requested)

    # ---- N3: the packshot gate
    def n3_band(p):
        b = asm.product_band(p)
        return b, {k: b.get(k) for k in ("band", "center", "half_width", "photo_product_share",
                                          "edge_coloured_share", "dominant_share", "not_packshot")}

    base = asm.product_band(photo("n3_base.png", "drawbox=x=140:y=80:w=200:h=200:color=%s:t=fill" % PINK))

    def n3_tight():
        b, info = n3_band(photo("n3_tight.png", "drawbox=x=20:y=15:w=440:h=330:color=%s:t=fill" % PINK))
        ok = (b.get("band") is True and b["photo_product_share"] > 0.8
              and abs(circ(b["center"], base["center"])) < 2 and abs(b["half_width"] - base["half_width"]) < 2)
        return ok, "%s base centre=%s" % (info, base.get("center"))
    case("N3: a tight crop (product 84% of the frame, white margin) keeps its band", n3_tight)

    def n3_label():
        b, info = n3_band(photo("n3_label.png", "drawbox=x=140:y=80:w=200:h=200:color=%s:t=fill,"
                                "drawbox=x=190:y=150:w=100:h=40:color=0x2050B0:t=fill" % PINK))
        ok = b.get("band") is True and abs(circ(b["center"], base["center"])) < 2 and b["half_width"] < 15
        return ok, "%s" % info
    case("N3: a pink product with a small saturated blue label passes, band = the pink", n3_label)

    def n3_backdrop():
        b, info = n3_band(make_photo(d, PINK, "n3_on_blue.png", bg="0x2050B0"))
        ok = b.get("not_packshot") is True and "coloured backdrop" in b.get("reason", "")
        return ok, "%s" % info
    case("N3: pink on a saturated blue backdrop is refused (edge ring coloured)", n3_backdrop)

    def n3_two():
        # with two colours the peak always holds >= half the mass, so no dominant colour takes three
        b, info = n3_band(photo("n3_three.png", "drawbox=x=90:y=80:w=100:h=200:color=%s:t=fill,"
                                "drawbox=x=190:y=80:w=100:h=200:color=0x30B040:t=fill,"
                                "drawbox=x=290:y=80:w=100:h=200:color=0x2050B0:t=fill" % PINK))
        ok = b.get("not_packshot") is True and "no dominant product colour" in b.get("reason", "")
        return ok, "%s" % info
    case("N3: three colours of similar weight on white are refused (no dominant product colour)", n3_two)


if __name__ == "__main__":
    sys.exit(main())
