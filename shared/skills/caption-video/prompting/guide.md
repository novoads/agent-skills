# Captioning a finished video — HyperFrames + Whisper + alpha compositing

**Use this skill when:** the user has a finished MP4 (claymation ad, Pixar ad, UGC selfie, B-roll, anything) with a narrator / dialogue / voiceover, and wants timed burned-in captions added without re-rendering the source.

> **First, check whether the API is the better answer.** Novoads has a first-party captioning endpoint — `POST /v1/captions`, 30 preset styles, one call, no local toolchain (verified live 2026-08-04; see the `novoads-api` skill's SKILL.md → *Burned-in captions*). **It costs credits and this skill is free**, but this skill needs Whisper, HyperFrames, a Node project and an ffmpeg alpha composite, which is a real setup cost the first time.
>
> **Come here instead of the API when** the user wants a style outside the 30 presets, needs to hand-correct the wording (invented brand names are the usual reason — Whisper mishears them and the API gives you no way to fix it), wants to **hand-edit the wording before rendering** (the API transcribes, it does not let you author — and note that as of 2026-08-04 `POST /v1/transcripts` DOES return text, word timings and an SRT, so "I want the timings" on its own is no longer a reason to come here), is captioning enough footage that per-minute credits add up, or the source was rendered with `audioEnabled: false` — which the API refuses with a `409` and this skill can still caption if you supply the words.

> ⚠️ **Trim before captioning.** (Doctrine: [craft.md](../../../references/craft.md) § 3.) If the source video has any beats with VO followed by silent visual ("dead space"), trim those beats *before* captioning — re-encode each beat to `vo_dur + 0.5s`, re-concat, and only then transcribe. Whisper timestamps applied to a tightened master line up; timestamps from a dead-space master will drift when the source is later trimmed. See [pixar-ad § Trim to the narration](../../../../skills/pixar-ad/SKILL.md) for the canonical rule and ffmpeg recipe — it applies to every video-ad style.

Anchors on **HyperFrames** (HTML-based composition framework) + **Whisper** (word-level transcription) + **ffmpeg alpha compositing**. This pattern was tuned across multiple production runs — follow it exactly or expect the bugs listed below.

> **Changed 2026-08-03, after a live run:** this workflow used to render captions over
> chroma-key magenta and key it out. **It does not work with the skeleton below.** The
> caption style carries a soft `text-shadow`, and a shadow that fades toward the magenta
> background cannot be separated from it by any similarity/blend pair — the result is a
> purple halo on every glyph. Widening the key to swallow the halo eats the white stroke.
> HyperFrames can render a real alpha channel, so it now does: transparent background,
> `--format mov`, and ffmpeg `overlay` reading the alpha directly. Chroma-key is gone from
> this guide; do not reintroduce it.

## Why not just use ffmpeg `subtitles` / `drawtext` directly?

You can, but only if your local ffmpeg was built with `libass` + `libfreetype`. **Homebrew's `ffmpeg` formula ships without them** — the filters are silently missing and `ffmpeg -vf subtitles=...` returns `No such filter`. The HyperFrames workflow below sidesteps that entirely by rendering captions in a real Chrome and compositing the result in.

It's also dramatically nicer for typography: real web fonts, real `text-stroke`, real GSAP animations per phrase, per-emphasis styling. PIL + drawtext can't match.

## The pipeline

### 1. Initialize a captioning project

Sit it alongside the source video, not inside it — keeps reruns clean.

```bash
cd path/to/<run-id>/                     # the folder that already holds the finished mp4
npx --yes hyperframes@0.6.26 init <run-id>-captions
cp <source-video>.mp4 <run-id>-captions/source.mp4
```

> **On paths:** earlier versions of this guide assumed the source sat in a `final/`
> subdirectory. Nothing in this repo creates one — `novoads-api` downloads land under
> `outputs/<run>/`, and other pipelines differ again. **Locate the source video, then use
> its real path.** `final/` appears nowhere below; if you see it in an older doc, treat it
> as a placeholder, not a directory that exists.

Record the three properties every later step has to match:

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration -of default=nw=1 source.mp4
```

### 2. Transcribe with Whisper at the right model size

**The model choice matters.** Wrong model → drifty captions. Decision tree:

| Source audio | Model | Why |
|---|---|---|
| Pure speech, no music | `small.en` | Fast, accurate |
| **Speech mixed with background music (typical ad)** | **`medium.en`** | `small.en` biases word boundaries when music interferes — symptoms are per-word drift of 100-300ms |
| Multilingual | `medium` or `large-v3` (no `.en` suffix) | `.en` models *translate* non-English audio into English silently |
| Produced track with vocals + full instrumentation | `large-v3` or OpenAI/Groq API | Even `medium.en` may misalign |

```bash
npx --yes hyperframes@0.6.26 transcribe source.mp4 --model medium.en
```

Output is `transcript.json` — a flat array of `{text, start, end}` per word.

**Run the quality check** (mandatory per the hyperframes-media skill): grep for `♪`/`�` tokens. If >20% of entries are music notes or obvious nonsense words, retry with a larger model.

#### Leading silence: transcribe a trimmed copy, then offset the timestamps back

**Whisper smears the first words across leading silence.** Measured on a live clip
2026-08-03: the source opened with **3.16s of verified silence**, and Whisper placed
`"I kept saying"` at **0.03–2.73s** — entirely inside the silence, so the first caption
appeared nearly three seconds before anyone spoke. This is not a model-size problem;
`medium.en` does it too. It is Whisper anchoring its first segment at t=0.

The fix does **not** touch the source video. Transcribe a trimmed *copy*, then add the
trim offset back to every timestamp, so the numbers describe the original timeline again:

```bash
# 1. Measure the leading silence.
ffmpeg -hide_banner -i source.mp4 -af silencedetect=noise=-40dB:d=0.3 -f null - 2>&1 \
  | grep silence_

# Read the first silence. If its silence_start is at 0, its silence_end is where speech starts.
# If it starts later, or there is none, the clip opens on speech: LEAD=0, skip this section.
# Verify by ear before trusting it; music under the VO can move the threshold.
LEAD=3.16

# 2. Trim a COPY. Re-encode (not -c copy) so the cut is frame-accurate.
ffmpeg -y -ss "$LEAD" -i source.mp4 -c:v libx264 -crf 18 -c:a aac trimmed.mp4

# 3. Transcribe the copy.
npx --yes hyperframes@0.6.26 transcribe trimmed.mp4 --model medium.en
mv transcript.json transcript.trimmed.json
```

```bash
# 4. Offset every timestamp back onto the source timeline.
python3 - "$LEAD" <<'EOF'
import json, sys
lead = float(sys.argv[1])
words = json.load(open("transcript.trimmed.json"))
for w in words:
    w["start"] = round(w["start"] + lead, 3)
    w["end"]   = round(w["end"] + lead, 3)
json.dump(words, open("transcript.json", "w"), indent=2)
print(f"offset {len(words)} words by +{lead}s → transcript.json")
EOF
```

Everything downstream reads `transcript.json` and needs no further change. Keep
`trimmed.mp4` and `transcript.trimmed.json` around until you have verified the render —
they are the evidence if the sync looks wrong.

**Sanity gate:** the first word's `start` must now be ≥ your measured `LEAD`. If it is
still near zero, the offset did not apply and the captions will fire early.

**The source video is never trimmed.** Captions composite onto the original file, so its
duration, its dead-space beats and its audio all stay exactly as approved.

### 3. Group words into reading phrases

Word-by-word captions are exhausting to read. Group into 3-5 word phrases that break on punctuation. Use this helper (commit it as `build_groups.py` in the project):

```python
#!/usr/bin/env python3
"""transcript.json (word-level) → groups.json (reading phrases)."""
import json, re, pathlib

WORDS = json.load(open("transcript.json"))
MAX_CHARS = 22
MAX_WORDS = 5
MAX_GAP = 0.55   # force a new group if pause exceeds this

def is_sentence_end(t): return bool(re.search(r'[.!?](?:["\'\)\]])?$', t))
def is_clause_break(t): return bool(re.search(r'[,—:;](?:["\'\)\]])?$|\.\.\.$', t))

groups, cur, cur_chars, last_end = [], [], 0, 0.0
for w in WORDS:
    text = w["text"]
    if not text.strip(): continue
    gap = w["start"] - last_end if cur else 0
    candidate = cur_chars + (1 if cur else 0) + len(text)
    if cur and (candidate > MAX_CHARS and len(cur) >= 2 or len(cur) >= MAX_WORDS or gap >= MAX_GAP):
        groups.append(cur); cur, cur_chars = [], 0
    cur.append(w); cur_chars += len(text) + (1 if cur_chars else 0); last_end = w["end"]
    if is_sentence_end(text) or (is_clause_break(text) and len(cur) >= 2):
        groups.append(cur); cur, cur_chars = [], 0
if cur: groups.append(cur)

out = []
for g in groups:
    text = re.sub(r"\s+([,.;:!?])", r"\1", " ".join(w["text"] for w in g).strip())
    out.append({
        "text": text,
        "start": round(g[0]["start"], 2),
        "end": round(g[-1]["end"], 2),
        "emphasis": "normal",   # set per-group manually below if you want comedic/brand/product styling
    })
pathlib.Path("groups.json").write_text(json.dumps(out, indent=2))
print(f"{len(out)} groups → groups.json")
```

**This helper is a first pass, not an oracle. Read `groups.json` before rendering.** Two
failure modes showed up on the live 2026-08-03 run, both from the same greedy loop:

- **One-word orphan groups.** A sentence-end flush (`is_sentence_end`) immediately after a
  `MAX_WORDS`/`MAX_CHARS` flush leaves a single trailing word as its own group. On screen
  it reads as a flicker. **Fix by hand:** merge a 1-word group into its neighbour — the
  previous one if they share a sentence, otherwise the next.
- **A clause split across a pause.** `gap >= MAX_GAP` flushes on timing alone, with no
  regard for grammar, so a breath mid-phrase can cut `"and then it just"` / `"stopped
  working"` into two groups. **Fix by hand:** rejoin, or raise `MAX_GAP` for that clip if
  the speaker breathes a lot.

Neither is worth automating away — the loop is deliberately simple, and eyeballing 20-odd
groups takes under a minute. What is *not* optional is doing it: these land in the burned
pixels of a finished creative.

A quick pass to surface the orphans:

```bash
python3 -c "
import json
for i,g in enumerate(json.load(open('groups.json'))):
    n=len(g['text'].split())
    if n==1: print(f'{i}: 1-word group -> {g[\"text\"]!r} @ {g[\"start\"]}s')
"
```

Then optionally hand-tag emphasis. Common emphasis classes:
- `normal` — default white text
- `comedic` — slightly larger, warm color, snappier ease
- `brand` — purple/pink, larger, used for brand name mentions
- `product` — pink/magenta, largest, used for pricing/quantity callouts
- `helen` (or other character name) — italic, alternate color, for dialogue spoken by characters in the video (vs. the narrator)

### 4. Write the composition

**CRITICAL: do NOT put `<video>` or `<audio>` elements in the composition.** HyperFrames wraps any `class="clip"` element in a managed timing wrapper that injects its own positioning/sizing styles, which **overrides any CSS you declare**. The wrapper for `<audio>` reserves an ~80 px layout block at the bottom of the stage, producing a hard black bar in the render. This bit us hard once — don't repeat it.

Instead: render captions over a **transparent** background and composite the source video underneath in ffmpeg post, using the real alpha channel.

Skeleton `index.html` (drop into the captioning project root):

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=720, height=1280" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&display=swap" rel="stylesheet">
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        margin: 0; width: 720px; height: 1280px; overflow: hidden;
        /* Transparent — the render carries a real alpha channel and ffmpeg
           composites on it. Do NOT set a chroma-key colour here: the soft
           text-shadow below blends into it and leaves a halo no key can remove. */
        background: transparent;
        font-family: "Outfit", system-ui, sans-serif;
      }
      #stage { position: relative; width: 720px; height: 1280px; }
      #captions { position: absolute; inset: 0; z-index: 10; pointer-events: none; }
      .caption-group {
        position: absolute; left: 50%; transform: translateX(-50%);
        max-width: 660px; width: max-content; text-align: center;
        opacity: 0; visibility: hidden; will-change: transform, opacity;
      }
      .caption-group .line {
        display: inline-block; font-family: "Outfit", sans-serif;
        font-weight: 900; font-size: 54px; line-height: 1.1;
        color: #fff; text-transform: uppercase;
        -webkit-text-stroke: 6px #0e0a06; paint-order: stroke fill;
        text-shadow: 0 5px 14px rgba(0,0,0,.7), 0 2px 4px rgba(0,0,0,.9);
        white-space: pre-wrap;
      }
      .caption-group.emp-comedic .line { font-size: 60px; color: #ffe6a8; }
      .caption-group.emp-brand   .line { font-size: 56px; color: #f7d9ff; -webkit-text-stroke: 6px #3d1648; }
      .caption-group.emp-product .line { font-size: 62px; color: #ffd9f6; -webkit-text-stroke: 6px #3d1648; }
      .caption-group.emp-helen   .line { font-style: italic; font-size: 50px; color: #ffd6a8; -webkit-text-stroke: 5px #2a1808; }
    </style>
  </head>
  <body>
    <div id="stage" data-composition-id="main" data-start="0" data-duration="73.36" data-width="720" data-height="1280">
      <div id="captions"></div>
    </div>

    <script>
      /* GROUPS data — built from groups.json. Inline it here or load via fetch. */
      window.__GROUPS__ = __GROUPS_JSON_INLINE__;
    </script>

    <script>
      window.__timelines = window.__timelines || {};

      // Adjust Y positions per project — e.g. lift captions higher during a CTA window
      // to clear a burned-in overlay in the source video.
      const Y_DEFAULT = 940;   // ~73% from top, lower third
      const layer = document.getElementById("captions");
      window.__GROUPS__.forEach((g, gi) => {
        const wrap = document.createElement("div");
        wrap.className = "caption-group emp-" + (g.emphasis || "normal");
        wrap.id = "cg-" + gi;
        wrap.style.top = Y_DEFAULT + "px";
        const line = document.createElement("span");
        line.className = "line";
        line.textContent = g.text;
        wrap.appendChild(line);
        layer.appendChild(wrap);
      });

      const tl = gsap.timeline({ paused: true });
      // SNAPPY SYNC: caption appears AT whisper-reported start (no lead-in), animates
      // in over 60ms. Lead-in offsets cause perceptible drift — don't add them.
      window.__GROUPS__.forEach((g, gi) => {
        const el = document.getElementById("cg-" + gi);
        const inDur = 0.06, outDur = 0.08;
        const prevEnd = gi > 0 ? window.__GROUPS__[gi - 1].end : 0;
        const inStart = Math.max(prevEnd + 0.003, g.start);
        const outStart = Math.max(inStart + inDur + 0.02, g.end - outDur - 0.005);
        const ease = (g.emphasis === "comedic" || g.emphasis === "product" || g.emphasis === "brand") ? "back.out(1.3)" : "power2.out";
        tl.set(el, { visibility: "visible" }, inStart);
        tl.fromTo(el, { opacity: 0, scale: 0.97, y: 4 }, { opacity: 1, scale: 1, y: 0, duration: inDur, ease }, inStart);
        tl.to(el, { opacity: 0, scale: 0.96, y: -6, duration: outDur, ease: "power2.in" }, outStart);
        tl.set(el, { opacity: 0, visibility: "hidden" }, g.end);
      });
      tl.seek(0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
```

Replace `__GROUPS_JSON_INLINE__` with the contents of `groups.json` before rendering (read groups.json + string-substitute, or `fetch("groups.json")` at runtime).

Set `data-duration` on `#stage` to the actual source-video duration (use `ffprobe -v error -show_entries format=duration -of csv=p=0 source.mp4`).

### 5. Render with alpha + composite

Render to a format that carries an alpha channel. MP4/H.264 does not; **`--format mov`**
does (QuickTime RLE / ProRes 4444), and HyperFrames supports it.

```bash
cd <run-id>-captions
npm run check                       # 0 errors / 0 warnings expected
npx --yes hyperframes@0.6.26 render --format mov --fps 24
# outputs renders/<project>_<timestamp>.mov — captions + transparency, nothing else
```

**`--fps` must match the source.** HyperFrames defaults to **30fps**; Seedance renders at
**24**. Compositing a 30fps caption track over a 24fps source makes ffmpeg resample one of
them — visible as judder, and as caption edges landing a frame or two off where
`groups.json` says they should. Read the real rate from the `ffprobe` in step 1
(`r_frame_rate` comes back as a fraction, e.g. `24/1`) and pass it.

Then composite. The overlay filter uses the alpha channel directly — no keying:

```bash
ffmpeg -y \
  -i <source-video>.mp4 \
  -i renders/<latest-render>.mov \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto[vout]" \
  -map "[vout]" -map "0:a" \
  -c:v libx264 -preset medium -crf 18 -c:a copy -pix_fmt yuv420p \
  <source-video>-with-captions.mp4
```

`-c:a copy` carries the source audio through untouched, so your narration + BGM + ducking
mix from the source video is preserved. Write to a **new filename** — never overwrite the
source.

**Why not chroma-key.** The previous version of this step rendered over `#ff00ff` and used
`chromakey=0xff00ff:0.10:0.05`. Against this skeleton it fails: `.line` carries
`text-shadow: 0 5px 14px rgba(0,0,0,.7)`, and a soft shadow fading into magenta produces a
continuum of part-magenta pixels. A similarity value tight enough to preserve the white
stroke leaves those pixels behind as a **purple halo around every glyph**; loosening it
until the halo goes takes the stroke with it. There is no working pair of values, because
the information needed to separate shadow from background was destroyed at render time.
Alpha keeps it. (Verified on a live clip, 2026-08-03.)

### 6. Verify before calling it done

```bash
for f in <source-video>.mp4 <source-video>-with-captions.mp4; do
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,nb_frames \
    -show_entries format=duration -of default=nw=1 "$f"
done
```

Width, height, frame rate and duration must match the source. Then spot-check two frames —
one mid-caption, one in a gap:

```bash
ffmpeg -y -ss <a-caption-timestamp> -i <source-video>-with-captions.mp4 -frames:v 1 check.png
```

Look for: no halo around the glyphs, no black bar at the bottom, captions clear of any
burned-in overlay already in the source.

## Common pitfalls (and the fixes)

| Symptom | Cause | Fix |
|---|---|---|
| **Purple/coloured halo around every glyph** | Chroma-key compositing against a soft `text-shadow` — the shadow blends into the key colour and cannot be separated from it | Don't chroma-key. Render `--format mov` over `background: transparent` and `overlay` on the alpha (step 5) |
| **~80 px black bar at the bottom of the render** | `<audio>` or `<video>` with `class="clip"` in the composition — HyperFrames' wrapper reserves layout space | Remove those elements entirely; use the composite-in-post pattern above |
| **First caption appears seconds before anyone speaks** | Whisper smeared the opening words across leading silence (3.16s of silence → first words placed at 0.03s, observed 2026-08-03) | Transcribe a silence-trimmed copy and offset the timestamps back (step 2). Never trim the source itself |
| **Captions drift 100-300 ms per word** | Used `small.en` on audio with background music | Re-transcribe with `medium.en` |
| **Judder, or caption edges a frame or two off** | Render fps ≠ source fps — HyperFrames defaults to 30, Seedance renders 24 | Pass `--fps` matching the source's `r_frame_rate` |
| **A single word flashes as its own caption** | `build_groups.py` flushed on `MAX_WORDS`/`MAX_CHARS` and then again on sentence-end, orphaning the last word | Merge it into a neighbour by hand in `groups.json` (step 3) |
| **A phrase is cut in half mid-clause** | `gap >= MAX_GAP` flushed on a breath, ignoring grammar | Rejoin by hand, or raise `MAX_GAP` for that clip |
| **Captions fire ~50-150 ms early** | GSAP `inStart` formula has a lead-in like `g.start - 0.05` | Use `g.start` directly. No lead-in. The animation duration (60 ms) is the only "anticipation" you need |
| **Captions feel laggy on the eye** | In-animation duration too long (140+ ms with `back.out`) | Drop to 60 ms with `power2.out` for normal text, `back.out(1.3)` only for emphasis |
| **`ffmpeg -vf subtitles=...` fails with "No such filter"** | Homebrew ffmpeg lacks libass | Don't use that filter — this whole skill is the alternative |
| **Pixel positions off by 1-2 px after compositing** | Source video resolution doesn't match composition `data-width`/`data-height` | They must match. Verify with `ffprobe -select_streams v:0 -show_entries stream=width,height` |
| **Captions visible during a burned-in CTA overlay window** | Caption Y position collides with overlay | Lift captions during that time range — e.g. `wrap.style.top = (g.start >= CTA_START ? Y_LIFTED : Y_DEFAULT) + "px"` |
| **A file named `final/…` doesn't exist** | An older revision of this guide assumed a `final/` subdir | No pipeline here creates one. Use the source video's real path |

## File layout convention

The captioning project sits **beside** the source video, wherever that video happens to
live. There is no required parent layout and **no `final/` directory** — put the project
next to the file you were given:

```
<wherever the source video is>/
├── <source-video>.mp4                           ← input, never modified
├── <source-video>-with-captions.mp4             ← output of step 5
└── <run-id>-captions/                           ← the hyperframes project
    ├── index.html
    ├── source.mp4                               ← working copy
    ├── trimmed.mp4                              ← silence-trimmed copy, transcription only
    ├── transcript.trimmed.json                  ← whisper output, trimmed timeline
    ├── transcript.json                          ← offset back onto the source timeline
    ├── groups.json                              ← reading phrases (hand-checked)
    ├── build_groups.py
    └── renders/                                 ← timestamped captions-with-alpha .mov files
```

## When NOT to use this skill

- **Captions need to drive video timing** (e.g. caption-reactive transitions, words synced to scene cuts) — use a more integrated HyperFrames composition that includes the video, accepting the layout caveat by carefully managing element wrappers.
- **Caller wants per-word ("kinetic") captions** — adapt step 3 to emit per-word groups instead of phrase groups; everything else stays the same.
- **Source has burned-in subtitles already** — don't double-caption; tell the user.

## Related skills

- The `novoads-api` skill — the upstream pipeline that produces the source videos, and the
  home of `POST /v1/captions`, the default captioning path this skill is the fallback to
- [`pixar-ad`](../../../../skills/pixar-ad/SKILL.md) and
  [`claymation-ad`](../../../../skills/claymation-ad/SKILL.md)
  — produce the kind of source video this skill captions, and carry the "no dead space"
  trimming rule referenced at the top
- The `meta-ad-builder` skill — publishes the captioned result as a Meta ad. It opts out of
  Meta's frame-modifying Advantage+ enhancements by default *because* these captions are
  burned into the pixels; if you deploy by hand instead, opt them out yourself

**This skill makes no Novoads API calls.** It is entirely out of band — ffmpeg, Whisper and
HyperFrames on a finished MP4 — so it costs no credits and needs no API key. It runs on any video
file, whoever generated it.
