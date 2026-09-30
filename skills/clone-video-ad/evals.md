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

---

## E1 — Three scripts, three estimates, one yes

**Scenario.** A ≤15s talking-head UGC source plus one product photo. The user asks for
three variations.

**Observed gap.** Step 11 defines a variation as *"the identical payload fired N times"* —
seed-level variety. The chapter this skill replicates writes **distinct scripts** on the
same beat structure, which is a different thing and the more useful one. And because the
estimate doubles as the per-model length check and the prompt lint, a variant prompt
that never gets its own estimate is a prompt nobody checked: there is no second chance at
submit time.

**Assertions.**

- The agent asks once, at the variation ask that already exists: *same script rendered N
  times, or N script variants?* The default stays 1 render.
- N variants means N distinct dialogue adaptations — same beat structure, same silent-beat
  placement, per-line word counts within about ±3 of the source.
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
