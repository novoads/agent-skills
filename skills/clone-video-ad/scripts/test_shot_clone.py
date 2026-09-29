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
its shot, and pace check/align on canned words[].
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


def make_photo(d, color, name):
    p = d / name
    src = "color=c=white:s=480x360,format=yuv420p,drawbox=x=140:y=80:w=200:h=200:color=%s:t=fill" % color
    # JPEG bytes under a .png name: the band must sniff the type, never trust the name
    # (ffmpeg's image2 demuxer would pick the png decoder from the extension and fail).
    ffmpeg("-f", "lavfi", "-i", src, "-frames:v", "1", "-c:v", "mjpeg", "-q:v", "2", "-f", "image2", p)
    return p


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


if __name__ == "__main__":
    sys.exit(main())
