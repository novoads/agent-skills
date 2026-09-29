# clone-video-ad — the shot-by-shot route

Read this only when step 5 of [SKILL.md](../SKILL.md) picked the shot route. The route rebuilds the
source one shot at a time: a new still per shot, a short silent take animated from that still, one
voiceover for the whole ad, then a local assembly that lands every cut on the source's cut times.
SKILL.md still owns the key gate, the dialogue gate (step 7), the source boundary (step 10) and the
transcript diff (step 12). This file adds what the route needs on top of them.

The scripts are stdlib Python plus `ffmpeg`/`ffprobe`, called from the pack root:
[scripts/shot_table.py](../scripts/shot_table.py), [scripts/pace.py](../scripts/pace.py) and
[scripts/assemble.py](../scripts/assemble.py), tested by
[scripts/test_shot_clone.py](../scripts/test_shot_clone.py). Everything a run writes goes under
`outputs/<job>/`. No `scripts/` beside `SKILL.md` means a solo install: [solo-install.md](solo-install.md).

## Contents

- [The flow and its gates](#the-flow-and-its-gates)
- [The shot table is the ledger](#the-shot-table-is-the-ledger)
- [Pricing, and the one yes at gate D](#pricing-and-the-one-yes-at-gate-d)
- [Casting stills and room plates](#casting-stills-and-room-plates)
- [Shot stills](#shot-stills)
- [Motion prompts](#motion-prompts)
- [Takes](#takes)
- [QC: free checks, then one analysis](#qc-free-checks-then-one-analysis)
- [On-camera talkers](#on-camera-talkers)
- [Voice and pace](#voice-and-pace)
- [Captions](#captions)
- [Grade](#grade)
- [Assembly and verify](#assembly-and-verify)
- [Hand-over](#hand-over)
- [Cost shape](#cost-shape)

## The flow and its gates

| # | Step | Where | Gate |
|---|---|---|---|
| S0 | SKILL steps 0 and 2: inputs, the key gate, the source uploaded and transcribed. Save the `POST /v1/transcripts` response as `outputs/<job>/source_transcript.json` | `/v1` | none |
| S1 | `shot_table.py` writes the cuts, per-shot grade stats, words per shot, frames and strips | local | none |
| S2 | Read every frame and strip, fill the table's read fields, present the table as SKILL step 4's contract | your read | **A**: table ok? |
| S3 | The route, both routes priced live (SKILL step 5) | `/v1/estimates` | **B**: route and tier |
| S4 | The new script, one line per shot, checked by `pace.py check` | local | **C**: dialogue (SKILL step 7) |
| S5 | Voice picked from `GET /v1/voices`; every still, take, the voiceover, talker conversions and the QC call priced | `/v1/estimates` | **D**: one yes, priced |
| S6 | Casting stills and room plates, then one still per shot, then take 1 per rendered shot, 5 in flight | `/v1/images`, `/v1/videos` | none |
| S7 | The free checks, the QC call, adaptive take 2, the picks | local, `/v1/analyses` | **E**: picks shown, free to flip |
| S8 | Voiceover, fit and align; talkers; `assemble.py build`; captions; `verify`; transcript diff | local, `/v1` | none |

- Gates A, B and C may be shown together, but each answer is its own approval (SKILL step 7).
- **Gate D is one yes covering the whole set**: the stills, take 1 for every rendered shot plus the
  take-2 ceiling, the voiceover, the talker conversions and the QC call. Nothing is spent before it,
  and a third take on any shot is a new ask.
- Gate E spends nothing. Show each shot's pick, its checks and the sensor that picked it, and let
  the user flip any pick before assembly.

## The shot table is the ledger

```bash
python3 skills/clone-video-ad/scripts/shot_table.py SOURCE.mp4 --job outputs/<job> \
  --transcript outputs/<job>/source_transcript.json
```

It finds cuts at two scene thresholds (0.25 and 0.12) and merges them, folds a white flash of up to
0.15 s into the next shot as `cut_in.flash_s` (a flash is not a shot), assigns the transcript's
`words[]` to shots, and writes `frames/<id>_in.jpg`, `_mid.jpg`, `_out.jpg` plus
`strips/<id>_cut.jpg` (0.5 s around each incoming transition). Then `outputs/<job>/shots.json`:

- Top level: `version`, `source`, `duration`, `fps`, `size`, `cuts_025`, `cuts_012`, `shots[]`.
- Each row, measured: `id` (`SH01`), `in`, `out`, `dur` (to 0.01 s; show it at 0.1),
  `cut_in {score, seen_at, flash_s, type}`, `confirm_cut`, `grade {...}` (the shot's
  `YAVG SATAVG UAVG VAVG YLOW YHIGH`), `speech {text, n_words, n_syll, start, end, wps}` or null,
  `frames[]`, `render_hint` (`hold_candidate` under 1.0 s, else `take`).
- Each row, **yours to fill at S2**: `framing`, `subject_fill_pct`, `subject_pos`, `camera`,
  `action`, `people`, `speaks_on_camera`, `room_id`, `light_words`, `product`,
  `on_screen_text_style`, `render` (`take` or `hold`), and `cut_in.type` (`hard`, `whip-left`,
  `whip-right` or `zoom-in`).
- Each row's `new` block, **filled as the run goes**: `person_id`, `room_id`, `still_prompt`,
  `motion_prompt`, `still_assetId`, `still_path`, `takes[]` of
  `{jobId, status, path, checks, qc, pick, sensor}`.

**A row with `confirm_cut: true` was seen at the low threshold only.** Confirm it on its strip. If
no cut is visible, merge it into the row before (that row's `out` becomes this row's `out`) and say
so at gate A. **`render: hold`** is for a static shot under about 1 s: it is its own still (or the
next shot's) held with a slight zoompan at assembly, never a take.

**`shots.json` is the run's resumable ledger.** Write each field the moment it exists: the still's
`assetId` when `POST /v1/images` answers, each take's `jobId` **before the first poll**. A resumed
session reads the file, polls every `jobId` that is not terminal, and submits only rows that have no
take. It never resubmits a row that already has a `jobId`. Re-running `shot_table.py` on the same
job merges into the file and keeps `new` and every field you filled.

## Pricing, and the one yes at gate D

Every number comes from `POST /v1/estimates` in this session (SKILL step 9). The calls are free and
fire concurrently:

```bash
curl -sS -X POST "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/estimates" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H "Content-Type: application/json" \
  -d '{"kind":"image","model":"gpt-image-2.5-sunburst","prompt":"<still prompt>","numImages":1}'
```

The other bodies on the same endpoint:

- `{"kind":"video","model":"seedance-2.0","durationSeconds":<N>,"language":"en","prompt":"<motion prompt>"}`,
  one per rendered shot (`seedance-2.0-mini` on the draft tier; `omni-flash` where you use it).
- `{"kind":"voiceover","script":"<the approved script>"}` for the one voiceover.
- `{"kind":"voice-change"}` per talker shot, only where `GET /v1/openapi.json` publishes that arm.
  Sourceless, it quotes the one-minute minimum, which is what a take shorter than a minute bills.
- `{"kind":"analysis"}` once, for the QC call.
- `{"kind":"transcript"}` for the voiceover check and the final diff.

**At gate B** the prompts do not exist yet, so price by class: one video estimate per distinct
`durationSeconds` in the table (a placeholder prompt is enough; the number moves with model,
duration and resolution) times the shots at that duration, one image estimate times the stills
(shots plus casting stills plus room plates), and the voiceover, analysis and transcript arms. Put
the single-render quote beside it. **At gate D** re-price with the real prompts and script, and read
the `warnings` each video and image estimate returns.

Show each kind's count and per-call number, the take-1 total, the take-2 ceiling (every rendered
shot re-taken once), the grand total and the balance. Warn when the total exceeds `balance`. Then
ask for one yes.

## Casting stills and room plates

**One casting still per original person, or per pair of hands**, generated before any shot still
and reused as a reference in every still of that person (`person_id` `P1`, `P2`, `H1`…). Cast new
people: a different face, age band or styling the user approved, never a lookalike of the source's
creator. Frame it plainly: head and shoulders (or the hands on a plain surface), even light, a plain
wall, no product.

**One empty room plate per `room_id`**: the room type, layout and the row's `light_words`, framed
as the widest shot in that room, no people, no product, no text. A new room in the source's spirit,
not a copy of the source's room.

Both go through `POST /v1/images` with no references. Record each `assetId`: it is durable across
calls and sessions, so one plate anchors every shot in that room (SKILL step 10).

## Shot stills

One still per shot on `POST /v1/images`, references in this order, which is the order the prompt
calls them by:

```bash
curl -sS -X POST "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/images" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-sunburst","aspectRatio":"9:16","numImages":1,"prompt":"<still prompt>",
       "referenceAssetIds":["<product photo>","<casting still>","<room plate>"]}'
```

The GPT image models take at most 4 references. Drop the casting still for a shot with nobody in
it, and the product for a shot without it, and renumber the prompt's images to match.

The still prompt, one flowing paragraph:

> Vertical phone photo. A `<framing>` of the person in image 2 `<pose at the shot's first frame>`,
> filling about `<subject_fill_pct>`% of the frame height at `<subject_pos>`, in the room from
> image 3, `<light_words>`, `<camera height and angle>`. The `<product>` must be exactly the
> `<product>` in image 1: `<features read off the photo: shape, colours, materials, the label text
> as printed>`. No text overlays.

**The preservation clause is the last sentence**, and it is the one place a product's appearance
is written out: the still is what the take inherits. Read the features off the product photo,
never from memory, and sniff the photo's type with `file --mime-type` before uploading it, because
the extension can lie.

**No source pixels ever enter a generation.** Not the source video, not a frame, a crop or a
trace of one: the frames and strips are for reading. If a still's framing comes back off,
regenerating wider and cropping locally to the row's framing is allowed, since the crop uses no
source pixels:

```bash
ffmpeg -y -i SH04.png -vf "crop=iw*0.8:ih*0.8:(iw-ow)/2:(ih-oh)/2,scale=1080:1920" SH04_crop.png
```

Upload the crop once (SKILL step 10) and record its `assetId` as the row's `still_assetId`.

## Motion prompts

Camera plus **one** hand or body action, timed to finish before the shot's `dur` and then hold:

> Handheld phone, eye level, a slow push in. In the first 1.5 seconds the hand lifts the jar toward
> the lens, then holds still. Silent: no speech, no music. No cuts, no text on screen.

- **One action.** Two actions renders as a smear (SKILL step 6), and an action still moving at the
  trim point cuts mid-gesture.
- **Silent.** `audioEnabled: false` on Seedance, and the silence in the prose too (SKILL step 8).
- **No product words.** The start still carries the product; naming or describing it again in the
  motion prompt invites the model to redraw it.
- **No whips.** A prompted whip lands late and breaks the opening. Every transition is made locally
  at assembly from `cut_in.type`.

## Takes

```bash
curl -sS -X POST "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/videos" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"seedance-2.0","prompt":"<motion prompt>","durationSeconds":4,"aspectRatio":"9:16",
       "audioEnabled":false,"language":"en","startImageAssetId":"<the row still_assetId>"}'
```

- **`durationSeconds = max(4, ceil(dur + 0.2))`**, an integer. The take is trimmed locally to `dur`.
- **Models.** `seedance-2.0` by default; `seedance-2.0-mini` is the draft tier (no `resolution` key).
  `omni-flash` with `firstFrameAssetId` (the still as a true first frame, plus `seed` for a
  reproducible re-take) only where `GET /v1/openapi.json` publishes the field; its durations are
  4, 6, 8 and 10, so round up to the next of those, and `audioEnabled` is a Seedance-only key.
  ```bash
  curl -sS "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/openapi.json" | grep -c firstFrameAssetId
  ```
  `0` means this deployment does not publish it: stay on Seedance.
- **`startImageAssetId` never rides with `referenceAssetIds`**, and on `omni-flash` a first frame
  rides with neither.
- **At most 5 in flight** across the organization. Fire five, start the next as each turns terminal.
- **Write each `jobId` into the row's `new.takes[]` before polling.** Poll
  `GET /v1/generations/<jobId>` every 15 seconds until terminal, then download through `/watch` to
  `outputs/<job>/takes/<id>_t1.mp4` (SKILL step 12).
- **Adaptive take 2.** A second take only when take 1 fails the free checks or the QC. Change one
  thing in the motion prompt (usually the action's timing) and name it in the ledger.

## QC: free checks, then one analysis

**The free checks first**, on every take:

```bash
python3 skills/clone-video-ad/scripts/assemble.py check outputs/<job>/takes/SH01_t1.mp4 \
  --still outputs/<job>/stills/SH01.png --dur 2.4
```

It prints JSON and exits 0 when all three pass: the **opening lock** (the best SSIM of frame 0
against the still, centre-cropped at scale 1.00 to 1.05, passes at 0.90 or more; it reports the
scale), **no invented cut** inside `[0, dur]`, and **motion present** (not frozen).

**Then one paid read for the whole set.** Cut each passing take's `[0, dur]` window, slow it 2-4x so
the default sampling sees every moment, and join the windows into one reel. Keep the reel's index
(reel seconds to shot and take) in `outputs/<job>/qc/reel.json`:

```bash
ffmpeg -y -i outputs/<job>/takes/SH01_t1.mp4 -t 2.4 -vf "setpts=3*PTS" -an outputs/<job>/qc/SH01_t1.mp4
```

Upload the joined reel (SKILL step 2) and send **one** `POST /v1/analyses`, priced at gate D. Set
`maxSeconds` to the reel's length. Ask a forensic `question` where the analysis request schema in
`GET /v1/openapi.json` publishes that field (the body is strict; an unknown key is a free `400`):

> Second by second, list every defect with its timestamp: a hand or finger that appears, vanishes
> or doubles; an object that moves on its own; a face or product that morphs; a label or colour
> that changes; text that appears; a cut; motion that freezes. Say "clean" for a clean stretch.

Map each timestamp back through the reel index. If the slowed reel runs past the longest
`maxSeconds` the schema allows, slow it 2x rather than splitting it; a second call is a second fee.

**The fallback sensor is contact sheets**, a frame every 0.25 s over the used window, read by you:

```bash
ffmpeg -y -i outputs/<job>/takes/SH01_t1.mp4 -t 2.4 -vf "fps=4,scale=270:-1,tile=4x4" \
  outputs/<job>/sheets/SH01_t1_%02d.jpg
```

Record which sensor made each pick in the take's `sensor` (`analysis` or `sheets`) and its verdict
in `qc`. Gate E shows both.

## On-camera talkers

A shot whose `speaks_on_camera` is true is the one exception to the silent rule. Render it with
audio on and that shot's new words quoted in the motion prompt, so the lips move to them. Then,
where `GET /v1/openapi.json` publishes `POST /v1/voice-changes`, convert its speech to the
voiceover's voice:

```bash
curl -sS -X POST "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/voice-changes" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H "Content-Type: application/json" \
  -d '{"jobId":"<the picked take jobId>","voiceId":"<the voiceover voiceId>"}'
```

It keeps the take's timing and returns the audio. Splice it over that shot's window in the
voiceover track (the take trimmed to `dur`, placed at the row's `in`) before `build`, so the lips
and the voice agree. **Where that endpoint is not published, or the splice drifts audibly**, fall
back to a silent reaction: re-take the shot silent with a listening or reacting action, and let the
voiceover carry the words over it.

## Voice and pace

**Pace, before the voiceover exists.** `plan` gives the per-shot word targets; `check` is the gate C
test of the new script, one line per shot in `SCRIPT.json` (`{"lines":[{"shot":"SH01","text":"…"}]}`):

```bash
python3 skills/clone-video-ad/scripts/pace.py plan  outputs/<job>/shots.json
python3 skills/clone-video-ad/scripts/pace.py check outputs/<job>/shots.json outputs/<job>/SCRIPT.json
```

`check` passes, exit 0, when words per shot are within ±1 of the source's, the total within ±5%,
and every shot the source speaks in is spoken in. Syllables break the tie when a brand name splits.

**One voiceover track for the whole ad.** Pick the voice from `GET /v1/voices` at gate D, matched to
the source's age, accent and energy, and say it is a different voice. Then:

```bash
curl -sS -X POST "${NOVOADS_BASE_URL:-https://api.novoads.ai}/v1/voiceovers" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H "Content-Type: application/json" \
  -d '{"script":"<the approved script, one string>","voiceId":"<voiceId>","language":"en"}'
```

Download its `url` at once. A script over the endpoint's character cap splits at a phrase break into
consecutive calls in the same voice, joined into one track.

**Transcribe the voiceover, muxed into an mp4.** `POST /v1/transcripts` refuses an audio asset, and
on a silent video it answers `409` "No speech was detected", so never transcribe a silent take:

```bash
ffmpeg -y -f lavfi -i color=black:s=320x568:r=24 -i outputs/<job>/vo.mp3 -shortest \
  -c:v libx264 -c:a aac outputs/<job>/vo_probe.mp4
```

Upload it, transcribe it, save the response as `outputs/<job>/vo_transcript.json`, then align:

```bash
python3 skills/clone-video-ad/scripts/pace.py align outputs/<job>/shots.json outputs/<job>/vo_transcript.json
```

It reports speech start and end against the source (within 0.15 s passes), the per-shot phrase
offsets, a suggested `atempo` (0.85 to 1.15) and the phrases more than 0.2 s off. Fit the speed with
`ffmpeg -i vo.mp3 -filter:a atempo=<a> vo_fit.mp3`, split each late or early phrase at the pause
before it and shift it, then transcribe and align again until start and end pass.

## Captions

Only when the source carries burned-in captions. **The text comes from the new voiceover's
transcript**, hand-checked against the approved script; only the **style** comes from the source:
size, weight, case, position and words per card. The source's captions repeat its own voiceover word
for word, brand included, so copying them leaks a competitor's name into your ad. **No token from
the source's brand or product may appear in any caption card**: check the card text against the
source transcript before burning.

Burn them with the shared [caption-video](../../../shared/skills/caption-video/SKILL.md) skill, with
its `--fps` set to the master's (24 by default) and its composition at the master's size. It is
local, and it deliberately avoids ffmpeg's `drawtext` and `subtitles` filters.

## Grade

Two modes, per shot against that shot's source stats. `build` always writes an ungraded twin with
identical timing, size and fps, because the hue gate compares the two.

- **LIGHT (the default).** A brightness-only luma match to the source shot, then a hue-protected
  saturation pull toward it that keeps the product's hue band. Why: the cuts read like the
  original's, and a contrast stretch judged worse than no stretch at all.
- **NONE (an option).** The takes' own colour. Why: on openings it judged at least as well as
  LIGHT, so offer it whenever the user prefers the render's own look.

**The hue gate must PASS** before a graded master is handed over. `build` runs it and records it in
`outputs/<job>/assembly.json`; to re-run it by hand:

```bash
python3 skills/clone-video-ad/scripts/assemble.py hue-gate outputs/<job>/master.mp4 \
  --ungraded outputs/<job>/master_ungraded.mp4 --photo <the product photo>
```

Exit 0 is PASS (the product keeps at least 0.80 of its chroma overall and in every window, and its
hue drifts 6° or less), 1 is FAIL, 2 is NO_PRODUCT (too little of the photo's product hue in frame
to measure: neither a pass nor a fail, and reported as such). On a FAIL, rebuild with
`--grade none`. Hand over **both masters** either way.

## Assembly and verify

```bash
python3 skills/clone-video-ad/scripts/assemble.py build outputs/<job>/shots.json --grade light --fps 24 \
  --vo outputs/<job>/vo_fit.mp3 --vo-start <S>
python3 skills/clone-video-ad/scripts/assemble.py verify outputs/<job>/master.mp4 outputs/<job>/shots.json
```

`build` takes each row's picked take trimmed to `[0, dur]` (or its still held with a slight zoompan
for a `hold` row), scales it to the source's size, makes each transition locally from `cut_in.type`
(a whip is a slide with a horizontal blur, `zoom-in` a zoom, a flash a white blend of `flash_s`,
`hard` a cut), grades, and muxes the voiceover at `--vo-start` (the source's first spoken word less
the voiceover's own lead-in, both in `align`'s report) with loudness normalized and an optional
`--bed`. It writes `master.mp4`, `master_ungraded.mp4` and `assembly.json` with the exact ffmpeg
commands. The output runs the source's length within one frame.

- **fps.** 24 keeps the takes' native rate and is the default. `--fps 30` duplicates frames, which
  judders measurably; offer it only when the user asks for 30.
- **`verify`** exits 0 when the duration is within one frame and every measured cut sits within
  0.05 s of the table's, and it reports per-shot saturation and brightness against the source.
  A failing cut names the shot to look at.

Then burn captions, and run SKILL step 12's transcript diff on the finished master.

## Hand-over

Into `outputs/<job>/`, then open the folder (SKILL step 12):

- **Both masters**, graded and ungraded (captioned, when the source was), and which grade each is.
- `shots.json`, the ledger: every still prompt, motion prompt, `jobId`, check and pick.
- The contact sheets, and the QC reel's verdicts with the sensor that made each pick.
- **The source copy** beside them (`source-<what-it-is>.mp4`, SKILL step 12).
- The transcript diff of the master against the approved script, per shot.
- **A rights note**, said plainly: the composition (shot order, framing, timing, structure) belongs
  to the original creator. The clone recasts it with new people, rooms, words and product; whether
  it may run as an ad is the user's call to clear.
- The total spend, summed from the `creditsCharged` values the API returned.

## Cost shape

Ratios only; every number comes from the live estimates at gates B and D.

- The shot route runs **about 4x a single-render series** of the same length. The takes are most
  of it; the stills, the voiceover and the one QC call are a small share.
- A `hold` shot costs its still only. The adaptive take 2 runs about a third cheaper than two takes
  on every shot. Mini takes cost about half the takes' share, as a draft.
- The QC call is one flat fee for the whole reel, never one per take.
