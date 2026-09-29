# Evals — clone-video-ad (video)

Written **before** the `SKILL.md` edits in this PR, following the evals-first work order
from #13. That ordering lives in this sentence rather than in the commit history, because
the repo squash-merges and commit order does not survive the merge.

Unlike [evals.md](../novoads-api/prompting/prompt-library/evals.md), which
was written from an observed failing run, E1–E4 come from two places: the deployed-spec
verification at the top of the #17 PR (`info.version` **2.10.0**, fetched 2026-08-05) and
the beat-by-beat comparison against the chapter this skill replicates. One assertion in E4
was measured directly against the local script; it says so where it lands.

**E5 and E6 were added against deployed spec `2.11.0` (fetched 2026-08-06) and are the
opposite kind: both were measured live before the text was written.** E5 comes from an
observed failure on the author's own machine; E6 from a capability the API gained after
E1–E4 were written.

E1, E2 and E3 are text assertions against the plan and the request bodies — checkable
before a credit is spent. E4 is the same, plus one local behaviour that was run. E5 and E6
are backed by a live probe whose every charged call is named in the PR description.

**E7–E10 were written 2026-09-29 against the spec deployed that day, BEFORE the shot-by-shot
route was implemented,** from measurements on one test ad (the eye-mask ad), 2026-09-29. Where those measurements overturned the earlier design text (30 fps, two takes per
shot, prompted whips, Omni ruled out, a words-per-second cap, captions copied from the
source), these cases assert the measured decision. E7 is a live-session case that spends
credits. E8 and E9 are checkable against the plan and the request bodies before a credit is
spent. E10 needs takes in flight, so it rides on a credit-spending run like E7's.

---

## E1 — Three scripts, three estimates, one yes

**Scenario.** A ≤15s talking-head UGC source plus one product photo. The user asks for
three variations.

**Observed gap.** Step 11 defines a variation as *"the identical payload fired N times"* —
seed-level variety. The chapter this skill replicates writes **distinct scripts** on the
same beat structure, which is a different thing and the more useful one. And because the
estimate doubles as the per-model length check and the free prompt lint, a variant prompt
that never gets its own estimate is a prompt nobody checked: there is no second chance at
submit time.

**Assertions.**

- The agent asks once, at the variation ask that already exists: *same script rendered N
  times, or N script variants?* The default stays 1 render.
- N variants means N distinct dialogue adaptations — same beat structure, same silent-beat
  placement, per-line word counts within ±1 of the source's (the pace rule, step 7), and each
  line under the single render's fit ceiling of `2.0 × (D − 0.5)` words.
- All N are presented in **one** gate-1 block (step 7), not one gate per variant.
- One `POST /v1/estimates` **per variant prompt**, fired concurrently, before any render.
- Each variant's `warnings` array is read and judged out loud. Overriding one is also said
  out loud — they are substring matches and they do false-positive.
- One consolidated consent line: per-call number, count, total, balance. One yes covers
  all N.
- The renders fire concurrently, every variant counted against the five-slot cap.

**Fails if:** one estimate is fired and its number reused as the quote for all variants; or
each variant gets its own separate approval gate; or "three variations" silently becomes
the same payload three times.

---

## E2 — Over 15 seconds is a choice, never a default

The one scenario no acceptance run with a ≤15s source can reach, which is why it is here:
this eval is its only regression net.

**Scenario.** A 24s talking-head source, product photo given.

**Observed risk.** Step 5 as written prescribes *"split at natural beat boundaries"* as the
only path. #13 measured the alternative — one render carrying the beats as jump cuts inside
it — at roughly half the spend with the voice present throughout, against a stitched arm
whose voice was absent for half its runtime. That makes one-shot **viable**. It does not
make the series wrong: the stitched arm anchored each clip with `startImageAssetId`, a
different mechanism from this skill's shared-`referenceAssetIds` series. And compressing
drops the source's runtime and pacing, which are themselves transferable traits — the thing
this skill exists to preserve.

**Assertions.**

- Both routes are named before either is picked.
- Each carries its tradeoff in one line: one-shot is roughly half the spend with continuous
  voice, but the clone no longer matches the source's runtime or pacing; the series
  preserves both at roughly twice the spend, and pays any resolution multiplier per clip.
- **No default.** The agent presents the choice and waits. It does not pick one and mention
  the other in passing.
- If it cites the #13 A/B, it states the mechanism caveat in the same breath.
- If it consults [seedance-2-ugc-v2.md](../novoads-api/prompting/prompt-library/seedance-2-ugc-v2.md), it takes
  **structure and mode** from v2 and **prompt craft** from v1, and says which is which.
- clone-video-ad's **source beat map wins** over v2's beat doctrine. v2's "no silent beats in the
  base" must not delete a silent beat the source actually has.

**Fails if:** the agent splits silently (today's text); or compresses silently (v2's
doctrine imported wholesale); or cites the A/B as proof the series is worse; or a silent
beat present in the beat map goes missing from the adapted prompt without anyone being
asked.

---

## E3 — 1080p is a re-price, not a footnote

**Scenario.** Mid-flow, after the beat map is approved, the user asks for the clone at
`1080p`.

**Observed drift.** Step 9's body enumeration omits `resolution`, while the same file's own
resolution paragraph says the tier *"gets priced with `POST /v1/estimates`"* — the file
contradicts itself. The deployed spec calls `resolution` the second price axis and prices
the high tiers as their own credit schedules rather than as a surcharge on the low one. A
1080p clone priced from step 9 as written quotes the 720p number and invoices the 1080p
one, and it lands on the consent beat — the one place this skill promises a number that
holds.

**Assertions.**

- `resolution` is in the estimate body whenever the ask is above the model's default.
- The number shown to the user is the re-priced one, from a live call made in this session.
- The multiplier is never stated from memory as the quote. Approximations orient; the
  estimate decides.
- `480p` is named as a real draft tier at ≈half the base, not as saving nothing.
- The key is never sent on `seedance-2.0-mini`, `sora-2` or `veo-3.1` (`400 Unrecognized key`
  on all three), nor on `omni-flash` wherever `GET /v1/models` lists only `720p` for it.
- On a series, the tier is paid per clip and the total says so.

**Fails if:** a tier above the default is chosen and the estimate body does not carry it; or
the quote is the base number with a multiplier applied in the agent's head.

---

## E4 — A silent clone mutes the render AND says so in the prose

**Scenario.** A silent product-b-roll source: no speech, and in the sharpest case no audio
stream at all.

**Observed contradiction.** The file documents both halves — the flag and the prose — in its
header table and again in its constraints table. The **workflow steps an agent actually
follows** say the opposite: step 5's silent branch ends *"There is no audio switch to turn
off"*, and step 8 opens *"There is no audio switch to set."* An agent following the workflow
writes the prose and never sends the flag, and the user pays for a generated voice track
they then throw away.

**Measured for this PR (2026-08-05).** `extract-frames.sh` against a source with no audio
stream does **not** die: ffmpeg's failure is absorbed by
`|| echo "No audio stream found (silent video)"`, so `set -euo pipefail` never fires, and
the script exits `0` having written the frames and `metadata.txt`. What it does not write is
`audio.wav` — the file is **absent**, not empty. The trap is therefore one step later, in
step 2, which loads that path unconditionally.

**Assertions.**

- `audioEnabled: false` in the `POST /v1/videos` body.
- **And** the silence declared in the prompt prose. The flag mutes the render; the prose is
  what stops the model staging a talking shot. Prose alone is this eval's named failure
  case; flag alone is the other one.
- `audioEnabled` is **not** sent to `POST /v1/estimates` — `400` there — and the agent does
  not expect the price to move. Muting is not a discount.
- Gate 1 is skipped, and the agent says why rather than skipping it silently.
- The flag is never sent on a non-Seedance video model.
- Step 2 checks that `audio.wav` exists before transcribing, and reads its absence as
  "silent source", not as an error.

**Fails if:** the prose declares silence and the body omits the flag; or the body carries the
flag and the prose does not; or `audioEnabled` appears in an estimate body; or step 2 crashes
on a source with no audio stream.

---

## E5 — The words come from the API, and whisper is the fallback

**Scenario.** A clean machine — the state every first-time reader of this repo is in — with
a key, ffmpeg, and no transcription stack. The source ad speaks.

**Observed failure (measured 2026-08-06).** On the author's own machine,
`python3 -c "import whisper"` raises `ModuleNotFoundError`. `whisper-cli` IS on `PATH` via
Homebrew, and per #16 it ships with only a test-stub model, so it returns an **empty**
transcript rather than an error. Step 2 as written picks the first of those and crashes;
a reader who installs the second gets silence that a QA pass scores as "every line missing"
— a tooling failure wearing the costume of a bad render.

This is the same prerequisite #16 retired from this pack **two hours before** this skill
merged, and the README already calls whisper *"optional — offline only … not required for
the API path."* Step 2 never got the memo.

**Measured replacement (same probe).** `POST /v1/uploads` with `contentType: "video/mp4"`
→ `PUT` → `POST /v1/transcripts` with that `assetId` returned `200` in one call:
`model: "transcript-v1"`, `status: "succeeded"`, auto-detected `language`, 38 words with
`start`/`end` in **seconds**, 5 segments, an `srt`, for **0.1 credits**. The five segments
are the beat boundaries step 3 needs, already cut.

One thing worth knowing beyond the install: the API transcription rendered **"Owala FreeSip"
letter-correct**, where whisper renders out-of-vocabulary brands phonetically ("oh wallah").
The brand check in a §7 QA pass gets easier, not just cheaper. It agreed with whisper on
"chucks" for the source's spoken "chugs", which independently confirms that one as a render
artifact rather than a transcription artifact.

**Assertions.**

- Step 2's primary path is `POST /v1/transcripts`, reached by uploading the source.
- whisper survives as an **offline fallback**, documented the way `broll-overlay` documents
  it — including that `whisper-cli` with no model returns an empty transcript rather than an
  error, and that whisper reports milliseconds where this API reports seconds.
- The prerequisites block stops making whisper a hard requirement; nothing in the API path
  asks the reader to `pip3 install` anything.
- `language` in step 8 defaults from what **the transcript returned**, not from what whisper
  detected.
- A repeat transcription of the same source is recognised as free — `creditsCharged: 0`,
  served from storage.
- Word and segment timings are read as **seconds**. A fallback run converts.

**Fails if:** the skill requires whisper before it will start; or the API path is offered as
the fallback and the local install as the default; or the milliseconds-vs-seconds difference
goes unstated in the fallback branch.

---

## E6 — A product still is one call, and it chains by assetId

**Scenario.** The user brings a source ad and a product description, but **no product
photo**. The chapter this skill replicates never hits this case: its product still came from
a pre-built folder of twelve. This repo's `references/products/` holds a `.gitkeep`.

**Observed gap.** Step 5's no-photo branch offers exactly one route — *"describe the product
in the prompt text and say so to the user: Seedance will invent a design, render it, and
charge for it."* That is the most expensive answer available. The cheap one is a real
still, and the skill does not mention `POST /v1/images` anywhere in its 39 KB.

**Measured for this PR (2026-08-06).** `POST /v1/images` on `gpt-image-2` returned `200`
synchronously for **0.3 credits**, and its `images[]` entry carries **`assetId` beside
`url`** — added in deployed spec `2.11.0`, after this skill was written. The `assetId` was
then accepted by `POST /v1/videos` in `referenceAssetIds`: a token-pinned probe came back
with the `@Image2`-unresolvable error, which is raised *after* the ownership gate and the
images-only gate and *before* any charge — so both gates passed on a `/v1/images` id, for
free. **There is no download-and-reupload hop.**

**Assertions.**

- The no-photo branch offers `POST /v1/images` first, priced through `POST /v1/estimates`
  like any other spend, and consented to before it fires.
- The returned `assetId` is passed **directly** into `referenceAssetIds` or
  `startImageAssetId`. The skill never instructs a download followed by
  `POST /v1/uploads` — that mints a second asset and throws away the anchor.
- The `url` is understood as expiring (3600s) and the `assetId` as durable. Chaining is off
  the id, never the URL.
- "Seedance will invent a design and charge for it" survives only as the third option, after
  a real photo and a generated still — not as the only alternative to a photo.
- Whatever the source, the pinned still is the same `assetId` across a mini draft, every
  script variant and every clip of a series.

**Fails if:** the skill still presents "no photo" as a binary between a user-supplied file
and an invented design; or it generates a still and then re-uploads its bytes; or it chains
from the expiring URL.

---

## E7 — The eye-mask ADAPT clone, shot by shot

**Live-session case: it spends credits.** Every charged call is named in the PR description,
never in this file. Its pass is **measured** only after a full run of the shipped route; until
that run exists, these are the assertions it will be held to, not results.

**Scenario.** The first 5 s of the eye-mask ad (a competitor's heated eye mask; the full ad
is 48.76 s in 27 shots of 0.93–3.13 s) plus a pink product photo, and the customer's ask,
paraphrased: they sell the same product and want only the actors, the backgrounds and the
script changed. Same product, new people, new rooms, new lines, same cuts: an
ADAPT, not a remix.

**Measured on one test ad, 2026-09-29.** ffmpeg scene detection at
`scene>0.25` and `scene>0.12` over the whole ad puts the first 5 s cuts at 1.77, about 2.75
(a hit seen only at the 0.12 threshold) and 4.87. The take-level pass rate there was 2/4,
and take 1 alone would have failed S1. Its prompted whips landed late (2.71 s and 3.25 s) and
broke the opening lock. The aligned SSIM check scored the locked takes 0.975–0.981 at a
centre-crop scale of 1.020, against 0.555 for the nearest wrong case. On the openings against
a rival tool's clone of the same ad, the full grade scored 13/16, LIGHT 14/16 and NONE 16/16.

**Assertions.**

- The cuts come from `shot_table.py`, not from evenly spaced frames: 1.77, about 2.75 and
  4.87 in the first 5 s. The ~2.75 cut is a 0.12-only hit written with `confirm_cut: true`,
  and it stands only after the vision read of its cut strip confirms it.
- The table shown to the user gives every in, out and dur at **0.1 s**. No beat is
  whole-second.
- The new lines pass the **pace rule per shot** (`pace.py check` exits 0): words per shot
  within ±1 of the source, the total within ±5%, syllables as the tie-break when a brand
  name splits, phrase breaks on the same cuts, and speech start and end within 0.15 s of the
  source's (`pace.py align`). The old 2.0 words-per-second cap is not applied.
- One casting still per original person (or pair of hands) and one empty room plate per
  `room_id`, each reused. Then **one still per shot** from `POST /v1/images`, its references
  exactly `[product photo, casting still, room plate]`, its prompt carrying the row's framing
  numbers plus the **preservation clause**: *"The eye mask must be exactly the eye mask in
  image 1: <the features read off the photo>"*.
- **No source-derived asset in any request body.** No source frame, crop, strip or upload of
  the source appears in any `POST /v1/images` or `POST /v1/videos` body or reference list.
  The source is uploaded for reading (transcript, analysis) and never for rendering.
- Every motion prompt is camera plus ONE hand or body action, timed to finish before the
  shot's duration and then hold. It carries **no product words** and **no whip**.
- Every take is sent with `durationSeconds = max(4, ceil(dur + 0.2))`, an integer, and
  trimmed locally to [window_start, window_start + dur] (window_start is 0 unless an audio-on
  talker's measured onset set it, before that take's check, reel and gate E).
- **Adaptive take 2:** a second take fires only for a shot whose take 1 failed the QC read, or
  failed `assemble.py check` in a way the QC read or its contact sheet confirms. A failed
  opening lock alone is a flag that sends the take to that read, never the trigger for take 2.
  Two takes per shot is not the default.
- The picks are shown to the user shot by shot, each with **the sensor that made it named**
  (the slowed-reel `POST /v1/analyses` read, or the contact-sheet fallback) and recorded as
  `sensor` in `shots.json`.
- Every picked take passes the **opening lock** in `assemble.py check`: the aligned SSIM of its
  frame 0 (an offset talker window: the frame at its `window_start`) against the still, under a
  centre crop at 1.00–1.05 or a horizontal-only squeeze at sx 0.97–0.995 (re-read shifted by
  up to 2 % when still under 0.90), is ≥ 0.90, and the transform is reported. A pick under
  0.90 carries in its `qc` the QC read or contact-sheet comparison of the still with frame 0
  that found the same picture.
- The source's whip is rebuilt as a local **slide** (`xfade` in the whip's direction plus a
  horizontal blur) centred on the source's cut time, never prompted into a take.
- `assemble.py build` writes the graded `master.mp4` (LIGHT by default, NONE offered) **and**
  the ungraded twin `master_ungraded.mp4` with identical timing, size and fps, and the
  **hue gate PASSes** over the shot windows (chroma kept ≥ 0.80 overall and in every window,
  hue drift ≤ 6°), recorded in `assembly.json`. NO_PRODUCT is printed as a WARNING and never
  counted as a pass, and `build --grade light` without the product photo refuses (exit 2).
- **One voice throughout:** one `POST /v1/voiceovers` track for the whole ad, with any
  on-camera talker brought to that same voice (E8).
- The caption **text** comes from the new voiceover's transcript; only the **style** (size,
  weight, case, position, words per card) comes from the source. The transcript is taken from
  the voiceover muxed into an mp4: `POST /v1/transcripts` on a silent render answers **409
  "No speech was detected"**, so a silent take or master is never the thing transcribed.
  Captions are offered at hand-over, not burned by default: on a yes to that offer, the cards
  are burned with `caption-video` at the master's fps into `master_captioned.mp4`, and
  `master.mp4` stays uncaptioned.
- **Gate E is a stop.** The turn that shows every pick with its sensor ends there. No S8 step
  (the voiceover, its fit or transcripts, a talker's voice change, `build`) runs before the
  user answers gate E.
- **No competitor token.** `<the competitor's brand token>`, matched case-insensitively,
  appears nowhere in the picture (stills, on-screen text, cards), in the voice (the transcript
  of the delivered master) or in the captions. The source's own captions repeat its voiceover word for word, brand included,
  which is why they are never copied. **The same holds for its offer text**: the source's
  offers, discounts, prices, guarantees, retailer names and call-to-action words appear in no
  voiceover line, still or end card unless the user supplied those exact words at gate C, and
  no still carries readable text the user did not supply.
- `assemble.py verify` exits 0: the output's duration is the source's within one frame, its hard
  cuts land **within 0.05 s** of the source's, and its whip and zoom cuts land inside their
  transition window (`in_transition`, as `verify` defines it, with the raw error reported).
- The takes' native 24 fps is kept; no 30 fps is asserted, because 24 was not worse than 30 in
  the pairwise read on the test ad and frame duplication judders.

**Fails if:** the first frame of any shot is not its approved still (a lock under 0.90 that no
QC read or contact sheet cleared); a take 2 is ordered on a failed lock alone; a beat is
whole-second; any request body carries a source-derived asset; a motion prompt names the
product or asks for a whip; a second take fires on a shot whose take 1 passed; a pick is shown
without its sensor; the hue gate does not PASS and the graded master is delivered anyway; two
voices are heard; a caption is copied from the source's cards; `<the competitor's brand
token>` is seen, spoken or captioned anywhere in the deliverable; or the source's offer or CTA
text (a discount, a price, a guarantee, a retailer, a button's words) is spoken or shown
without the user having supplied it; captions are burned unasked or into `master.mp4`; or any
S8 step (the voiceover, its transcripts, a talker's voice change, `build`) runs before gate E's
answer.

---

## E8 — Per-shot render rules

**Scenario.** Any shot-route run, read at the moment its takes are built: the request bodies
and the ledger before anything is submitted.

**Observed gap.** Three facts the single-render route never had to face. The minimum duration
is 4 s on every video model, while the test ad's shots run 0.93–3.13 s. The earlier design
text ruled Omni out because its `startImageAssetId` is only a reference; that is still true,
but where the full surface is enabled the spec publishes `firstFrameAssetId` on
`omni-flash`, which is a real first frame. And a shot-by-shot ad fires many renders into a
five-slot cap.

**Assertions.**

- The model comes from `GET /v1/models`, never from memory: `seedance-2.0`, with
  `seedance-2.0-mini` as the draft tier.
- Every still and take request sends `shots.json` `aspect`, and the still prompt's first words
  follow it (vertical, horizontal or square). `build` meets a take or still more than 2% off the
  source's aspect with exit 2, unless `--allow-crop` was chosen and is recorded in `assembly.json`.
- `omni-flash` is allowed **only with `firstFrameAssetId`**, and only where
  `GET /v1/openapi.json`, fetched in this session, publishes that field. Its durations are
  4/6/8/10, so the formula's value rounds up to the next one it accepts.
- `durationSeconds = max(4, ceil(dur + 0.2))`, sent as an integer; the take is trimmed locally.
- The still's `assetId` goes in as `startImageAssetId`, and `startImageAssetId` is **never**
  sent together with `referenceAssetIds`.
- A silent shot carries `audioEnabled: false` **and** silence in its prose (E4).
- **Talkers:** an on-camera speaker's shot under about 2 s renders as a silent reaction (mouth
  closed: a smile or a nod) under the voiceover. One long enough for its line renders with audio
  on and its new words quoted, then goes through `POST /v1/voice-changes` to the voiceover's
  voice where the spec publishes that route, with the pick's `window_start` at the measured
  speech onset minus 0.05 s; the fallback is a silent reaction shot under the voiceover.
- A shot the table marks `hold` (static, under about 1 s) is not rendered: its still is held
  with a slight zoompan.
- Every take is priced with `POST /v1/estimates` before the one yes, as in E1, and that yes
  covers the batch.
- At most **5 in flight**. Each `jobId` is written to `shots.json` before it is polled, and a
  429 is answered by waiting, not by resubmitting.

**Fails if:** Omni's `startImageAssetId` (a reference) is promised as a locked first frame;
`firstFrameAssetId` is sent where the live spec does not publish it; a duration under 4 s, or a
non-integer one, reaches the API and the `400` becomes the discovery; `startImageAssetId` is
sent with `referenceAssetIds`; or a 6th render is fired into the 5-in-flight cap.

---

## E9 — The route gate: two routes, priced live, never a silent default

**Scenario.** Two sources. (a) A multi-cut ad such as the eye-mask ad, with the ask "make it
like the original". (b) A one-take talking-head source.

**Observed gap.** Until this route, step 5 had one answer: a single render that carries the
beats inside one take. It cannot put cuts at the source's times, and on a 27-shot ad "like the
original" is mostly the cuts. The single render stays, as the cheap draft; the risk is that
either route gets picked for the user.

**Assertions.**

- On (a), both routes are shown at step 5, **each priced by a live `POST /v1/estimates` in
  this session**: the single render and the shot route (its stills, its takes, and the QC
  read).
- On (a), the shot route is recommended, and the single render is labelled **the draft**:
  cheaper, cuts not at the source's times.
- On (b), the single render is recommended; a one-take source has no cuts for the shot route
  to keep.
- A ratio between the two may orient; the quotes come from the estimates.
- The user chooses. The agent waits.

**Fails if:** either route is picked without both being shown (a silent default); a rate or
price is printed that did not come from a live estimate in this session; the single render is
presented as equal to the shot route on (a); or the shot route is recommended on (b).

---

## E10 — Resume reads the ledger and never resubmits

**Scenario.** A shot-route run is killed after its takes are submitted: every `jobId` is in
`outputs/<job>/shots.json`, none polled to completion. A new session opens on the same job.

**Assertions.**

- The resumed session reads `outputs/<job>/shots.json` before any call.
- It polls the `jobId`s recorded under `new.takes[]` and fills in their `status` and `path`.
- Re-running `shot_table.py` on that job keeps the segmentation: every row's `id`, `in` and
  `out`, a hand merge from S2 included, `new` and every field Claude filled survive; only the
  measured stats, frames and strips refresh. `--resegment` is refused (exit 2) while any row has
  a take.
- Stills whose `still_assetId` is recorded are reused, not generated again.
- A take that comes back failed goes through the adaptive take-2 rule, with its own estimate
  and yes, like any other new spend.

**Fails if:** any recorded take is submitted again; any still with a recorded `assetId` is
generated again; or a re-run of `shot_table.py` wipes the ledger or undoes a hand merge.

---

## Open question for the next acceptance run — the 100–260 word ceiling

**Not an assertion. A measurement to take.** Step 6 and the UGC formula's checklist both
cap a prompt at **100–260 words**, and this pack inherited that line verbatim from the fork
— same rule, same file, same line number. The chapter this skill replicates shipped a
**357-word** prompt, 37% over that ceiling, and its author rated the result *"a solid nine
out of ten."*

Nothing on the API enforces it: `GET /v1/models` reports `maxPromptCharacters: 4000` for
`seedance-2.0` (verified live 2026-08-06), and 357 words is roughly 2,100 characters. So the
ceiling is craft lore, and it is currently lore we cannot source.

**The ceiling is deliberately NOT changed in this PR.** One rated render is not evidence,
and loosening a limit on the strength of a competitor's YouTube video is exactly the kind of
unpinned claim this repo refuses elsewhere. Instead: the next acceptance run should render
one variant at the 100–260 ceiling and one at 340–360 from the **same** beat map and the
same references, and compare beat fidelity, label legibility and dialogue pacing. Until that
exists, the ceiling stands as written.

---

## Notes on evidence strength

- **E5 and E6 are the strongest evidence in this file** — both were probed live against
  prod before their text was written, and every charged call is named with its
  `creditsCharged` in the PR description. E5's failure half was observed on a real machine,
  not reasoned about.
- **E5's and E6's negative halves were proven free.** A source video's `assetId` in
  `referenceAssetIds` is refused by name with `invalid_input` and **nothing is charged** —
  the reference gates run before the debit, which the API asserts with a test. That is what
  lets "upload for reading, never for rendering" be a rule the platform enforces rather than
  a convention the skill hopes for.
- **E4's extraction behaviour is measured** — a generated 6s silent mp4 pushed through the
  real script during this PR. Everything else in E4 is read off the deployed spec.
- **E3 is spec-backed**: `CreateEstimateRequestVideo` carries `resolution` in the deployed
  contract, and the drift is a straight comparison against step 9's own text.
- **E1 and E2 are design assertions, not observed failures.** E2's underlying A/B is real and
  measured (#13), but the conclusion drawn here is deliberately narrow — viability, not
  superiority — because the two arms anchored their clips differently. Treat E2 as a strong
  default with its reasoning attached rather than a law, until a same-mechanism A/B is run.
- **E7–E10 were written before their implementation.** Their numbers (the cut times, the
  0.90 lock bar, the 2/4 take pass rate, the grade scores, the hue-gate bands) come from the
  measurements on one test ad (2026-09-29), not from a run of the shipped route. E7 counts as
  **measured** only after a full run of the shipped route; E8 and E9 are spec and design assertions; E10 is a design
  assertion until a real kill-and-resume is run.
- **No credit figures appear in this file by design.** Ratios and multipliers orient; the
  live estimate quotes. Absolute numbers for the acceptance run live in the PR description
  and in the run log, never in pack docs.

---

## No source supplied

The mirror of `clone-image-ad`'s H-series. These exist because this skill's description
advertised "clone my competitors' VIDEO ads" while its Step 0 required a source video and
offered no way to obtain one — a door sold and not built. The image side got this branch
first; this skill was promoted out of a buried directory and inherited the gap.

### V1 — an attached clip is cloned, and nothing is swept

**Why:** someone who handed over a video has already answered the question a sweep would ask.
Sweeping anyway spends their credits to learn what is on screen.

**Check:** hand over a local `.mp4` and ask for a clone. Zero calls to
`POST /v1/competitor-ads`, and no `{"kind":"competitor-ads"}` estimate either.

---

### V2 — no clip means go and find one, in VIDEO mode, priced first

**Why:** the failure this section was written for. Asking "which ad?" puts the work back on
the user at the moment they asked us to do it.

**Check:** say "clone my competitors' video ads" with nothing attached. Confirm the run does
NOT ask which ad; that the sweep is requested with `mediaType: "video"` **without asking the
user which mode** — a static sweep returns creatives this skill cannot open, so the mode is
the skill's to fix and to state; that the total comes from a live `POST /v1/estimates` in this
session; and that one word stops it. A run that asks the user to pick a media mode fails: that
is a question with one correct answer.

---

### V3 — "stop" costs nothing

**Check:** answer "stop" at V2's line. `POST /v1/estimates` may have run;
`POST /v1/competitor-ads` did not, nothing was uploaded, and nothing rendered.

---

### V4 — the sweep's price is not presented as the run's price

**Why:** a video render costs multiples of a sweep. A line that says "N credits total" before
a run that will also render is a number that reads as the whole cost and is not — the exact
shape the live-estimate rule exists to prevent.

**Check:** the veto line quotes the sweeps as **sweeps** and says the render is priced
separately before it runs. The existing cost gate at step 9 is unchanged and still fires. A
line that implies the sweep total is the run total fails, even though every individual number
in it came from a real estimate.
