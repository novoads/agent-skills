# Changelog

What changed in the **pack**: the skills, the scripts, the setup path and the docs.

This is not an API changelog. When a file here and the deployed spec disagree, the spec wins:
[`GET /v1/openapi.json`](https://api.novoads.ai/v1/openapi.json) describes what the API does now,
though not how it got there.

Entries land under `## Unreleased`. `./scripts/release.sh` dates that heading into
`## vX.Y.Z — YYYY-MM-DD` and opens a fresh one; it never invents the prose. Group an entry
as Added / Changed / Fixed, or as dated `###` subsections like the ones below.

## Unreleased

### Changed

**A scene where someone talks on camera goes on `omni-flash` (API 2.60.2).** Fewer words come out wrong
(measured 2026-11-08, videos with a word wrong: in Spanish 12% against about half on Seedance; in English, on our own renders, 12% against about 20%), and at `720p` it costs less than `seedance-2.0`. The API's default stays `seedance-2.0`:
this changes what an agent picks, not what a call with no `model` renders. For an agent:

- **`novoads-api`'s decision tree and `clone-video-ad`'s step 5 route a talking scene to `omni-flash`**:
  4, 6, 8 or 10 seconds a clip, the shortest that holds the line, and a part over 10 seconds splits
  where the line splits. A square ad, a scene with `productSwap`, animated characters and a model the
  user names stay as they were, and so does every scene where nobody talks.
- **The word count on `omni-flash` is now 8, 14, 19 and 25**, from about 2.8 words a second after the
  first second, in place of the flat `2.0 × duration`; the estimate warns past it (`omni_line_too_long`).
- **A scene Google's safety check stops goes to `seedance-2.5`**, priced first and shown for a yes. It
  is the one failure that moves a scene to another model.
- **`clone-video-ad` offers the mini draft for Seedance scenes only**, because a draft on mini would
  show an `omni-flash` scene neither its look nor its voice.
- **A hook that must land at once no longer needs Seedance**: on 32 of our own Omni clips the first
  speech came at a median of 0.15s (25 under half a second, 4 past a second), by voice detection.
- **Clips from different models are stitched through `POST /v1/assemblies`**, now in `reference.md`.
  A split talking ad is often a mix, and `-c copy` across models exits 0 with the sound broken: their
  sample rates differ while their codecs match, which "re-encode if the codecs differ" never caught.
- **The first `silence_end` is the first word only when the first silence starts at 0.** On 22 of 32
  of our Omni clips it sat inside the line, 1.7 to 7s in, and read as a false alarm. `caption-video`'s
  transcribe step reads it the same way now: the old read trimmed its copy past the first speech on 16
  of those 32, by voice detection.
- **`analyze-video`'s pasted block carries the rule**, so a template where someone talks does not send
  its renders to Seedance past the router.
- **`novoads-api` no longer refuses a join of clips the user already has**: `POST /v1/assemblies` does it
  where the deployment offers it.
- **A failed job's one more try:** `vendor_error`, `vendor_timeout` or no `reasonCode` gets one under a
  new `idempotencyKey`, and a second failure stops and says so.
- **A talking part over 10 seconds needs one person's picture**: `clone-video-ad` and the router now say
  to make one with `POST /v1/images`, shown for a yes, when there is none to hand.

## v1.4.1 — 2026-11-07

### Changed

**No skill routes to `reve-2.1` or `sora-2` any more (`reve-2.1` retired in API 2.48.0, `sora-2`
removed from the API in 2026-09).** v1.4.0 marked the two models in the tables it touched; this
makes every other line true. For an agent:

- **A second opinion on a still goes to the other image family.** `clone-image-ad`'s Phase 1
  chooser, its Phase 8 cross-check and its shared guide validate on `gpt-image-2` or
  `nano-banana-pro` only, and send a second opinion to the other of the two. Its validator,
  `validate_image.py`, takes `--model gpt-image-2|nano-banana-pro`; the retired `reve-2.1` is
  refused in argument parsing, before any upload, with a line that says so and names the model
  to use instead.
- **The image-ad overview's model table drops the retired `reve-2.1` column**, because the table
  lists only what differs between models a call can still name; one line under it says what
  happened. The prompt library's model notes and its ratio and cap tables, `template-format.md`,
  the image-ad evals and the generator, thumbnail and character-sheet docs drop that model's caps
  and ratios.
- **`check_library.py` measures against `gpt-image-2` as the tightest model**, now that the
  retired `reve-2.1` is gone: the baseline of over-long templates is empty (T8, T11 and T14 were
  over only that model), and the library header says 40 of the 40 templates have room for the
  pin block.
- **A talking clip whose first word must land at once goes to `seedance-2.0`** with a reference or
  a start frame, the eye-contact-break beat dropped and the first `silence_end` trimmed, in
  `clone-video-ad`, `analyze-video` and the cross-model UGC guide, where they used to point at
  `sora-2`; `seedance-2.md` and `ugc-product-selfie.md` no longer list it as live. `sora-2.md`
  opens with a removed notice and keeps its measurements as history, so an old link still lands
  on a page that says what happened.
- **Field lists name the live video models.** The `referenceAssetIds`, `audioEnabled`,
  `resolution`, default and duration lines in `novoads-api` and the README, and the `audioEnabled`
  lines in `clone-video-ad`, drop `sora-2` (removed) and add `wan-3.0` and `kling-v3-pro` where the
  spec has them. The README's model table gets a `wan-3.0` row read off its request schema, and
  `reference.md`'s `POST /videos`, `resolution` and timings tables get `wan-3.0` rows (`kling-v3-pro`
  joins the last two), so a Wan body can be built from the reference. `novoads-api`'s router names
  Wan, and its timing and script-length sections say Kling and Wan are unmeasured.
- **Guards.** `verify-image-caps.sh` no longer expects the retired `reve-2.1` caps: it skips a
  schema whose `model` description says `model_retired`, with a printed note, fails if its own
  table still names a retired id, and checks that the validator refuses `--model reve-2.1` as
  retired before the env gate. `check-skill-targets.sh` no longer exempts the removed `sora-2`, so
  a sentence that says use, see, switch to, route to or offer `sora-2` fails there, and it now
  exempts `kling-v3-pro` and the two Seedream 5 ids, so a correct line naming one passes.

**Facts the pack had stale, made true against the deployed spec (2.59.0, re-read on 2.60.0).** For
an agent:

- **`seedance-2.5` renders `1080p`** where `GET /v1/models` lists it (API 2.28.0), and still never
  `4k`. `novoads-api`, the README and `image-to-motion` no longer call `720p` its ceiling, and
  `image-to-motion`'s eval case now holds the `4k` refusal.
- **Video prompt ceilings are per model:** 20,000 on `omni-flash` and `wan-3.0`, 4,000 on the three
  Seedance variants and `veo-3.1`, 2,500 on `kling-v3-pro`. The old lines gave `omni-flash` the only
  20,000 and everything else 4,000, which over-filled a Kling prompt and cut a Wan brief for nothing.
- **Ten video generations in flight (API 2.51.0).** The video lines v1.4.0 missed now say ten:
  `analyze-video`, `novoads-api` and its reference (the error table and the caption, transcript
  and music rows), the log recipe, the feature-walkthrough formula, `clone-image-ad`'s guide and
  two evals.
- **`audioEnabled` is on `kling-v3-pro` and `wan-3.0` too**, in `novoads-api`'s decision list and
  `reference.md`, so a clip meant to be silent on either gets its `false`.
- **Image editing is on the five GPT models**, where the overview and `clone-image-ad`'s docs said
  `gpt-image-2` alone. The route is unchanged: an edit goes to `chatgpt-image-ad`, whose script
  sends `gpt-image-2`, and `clone-image-ad`'s validator edits on `gpt-image-2`.
- **Video calls take an `idempotencyKey` (API 2.52.0):** the same key within 24 hours returns the
  first job and its charge. `novoads-api`, `clone-video-ad` and `pixar-ad` no longer say there are
  no keys; `POST /v1/images` still takes none.
- **Images have their own queue of 12, `image_concurrency_limit`,** counted apart from video in
  both directions. The image lines that gave a ceiling of 5 or 10, or named `concurrency_limit`,
  now say so, in `chatgpt-image-ad`, `nano-banana-image-ad`, `generate-youtube-thumbnail`, the
  image-ad overview, the two character-sheet recipes and `novoads-api`. The cap of 4 in those runs
  is the run's own choice, and the lines now call it that: its value and every script's calls to the
  API are unchanged, and for this `generate-batch.sh` changes only in comments and the words of one
  printed line. The thumbnail eval YT5 now fills the image queue, and says its two measurements were taken
  on the render queue.
- **The relative price words are re-read off the spec's cells, at every length each schedule
  sells.** Against `720p`: on `seedance-2.0`, `480p` is about two-thirds, `1080p` about 2x and `4k`
  about 5x; on `seedance-2.5`, `480p` is under half and `1080p` about 1.7x, so the tier tables give
  each model its own words. `seedance-2.0-mini` is about a fifth of the price of `seedance-2.0`, not
  half. `seedance-2.5` is dearer than `seedance-2.0` from `720p` up and matches it at `480p`, and
  thirty seconds of it at `1080p` is the dearest cell the video schedules publish, where the lines
  called it the dearest model and the dearest call on the API. The spread across the set is the
  spec's: about 44x at four seconds, about 180x across every cell. A stitched series costs more in
  step with its total seconds, and "about half" and "roughly double" now read as a dated A/B's
  result. `POST /v1/estimates` stays the only source of a figure.
- **`clone-video-ad` no longer says `seedance-2.0-mini` refuses `resolution`,** which stopped being
  true at API 2.34.0.
- **A `429` has seventeen reasons (2.60.0),** counted off the spec. `reference.md` breaks out nine
  and names the other eight, and the lines that said four or twelve causes are gone.
- **The image lines about idempotency name `POST /v1/images`,** in the thumbnail, `chatgpt-image-ad`
  and `nano-banana-image-ad` skills and `novoads-api`'s reference, where they said this API or
  "there are no keys": video calls take one.
- **The old credit figures are gone from the skills.** Each figure a skill still quoted was written
  in an older credit unit, so it read about ten times too small: `POST /v1/analyses`,
  `POST /v1/transcripts`, the sweep and caption quotes, and the image, video and voice-change calls
  of dated runs. Those lines now name the meter (one flat fee, or by the minute with a one-minute
  minimum) or the ordering a dated A/B found, and `POST /v1/estimates` stays the only source of a
  figure. `reference.md` no longer gives a ratio between credits and an internal unit, and
  `check-no-rates.sh` now exempts no skill line. The voice-change eval dates the run where a
  15-second source and a sourceless quote agreed: today a source past the minimum quotes higher, so
  name it.
- **`concurrency_limit` covers music as well as video,** where `reference.md`'s reason table said
  video only.
- **`reference.md` prices voice change and voice-overs as the API bills them:** voice change by the
  second of source above a minimum charge (API 2.32.0), so a sourceless quote is that minimum and
  anything longer has to name its source; a voice-over per 400 characters of the spoken text.
- **A caption on a talking actor bills every started minute.** The lines that said everything this
  API generates bills one minute now say that of a clip from `POST /v1/videos`.
- **No line says the API cannot edit an image.** The overview's limits list and
  `nano-banana-image-ad`'s out-of-scope list now send an edit to `chatgpt-image-ad`.
- **The image skills' estimate lines name `quality` and `resolution`,** which move the price, where
  they said five fields were the only ones accepted.
- **The README's dated estimate capture keeps its shape and drops its two figures.**
- **The last line that said five shared slots says ten,** in `pixar-ad`'s music step.
- **`novoads-api`'s two estimate examples show plainly made-up numbers,** where they read like
  quotes the schedules could produce.
- **The estimate's field lists are whole.** `novoads-api`'s table adds `productSwap`, `sourceAssetId`
  and `preset`, `reference.md`'s adds `sourceAssetId`, and `clone-video-ad` names `productSwap`. The
  lines that said an arm takes only what moves the price now say it takes only what it lists:
  `outputFormat` is accepted and moves nothing.
- **Worked `POST /v1/videos` calls send an `idempotencyKey`, a new one per render,** in
  `novoads-api`, `clone-video-ad`, `pixar-ad`, `analyze-video` and the Seedance and Veo recipes. A
  key is only for a retry of the identical call: the same key within 24 hours returns the first job
  whatever the new body says, so a corrected clip sent under an old key comes back as the old clip,
  with no error and no render. `reference.md`, the Seedance and Veo tables and the re-render lines
  in `novoads-api`, `clone-video-ad`, `pixar-ad` and `claymation-ad` now say so, and the lines about
  firing N variations or re-sampling a stutter say each take gets a new key.
- **A `429`'s other `details` keys are named:** `details.limit`, `details.remainingSeconds` and
  `details.retryAfterSeconds`, where the lines called `details.inFlight` the only one.
- **`nano-banana-pro` takes 14 references on every line.** Its guide's ceiling line and input table,
  the character-sheet and product-selfie recipes, a comment in `generate-batch.sh` and two lines of
  `shared/references/README.md` said 4. The two recipes keep four as their own budget and now call
  it that, and the product-selfie recipe loads the two style images it uploads, where it said three.
- **No line says nothing reads a prompt.** `POST /v1/estimates` lints every image and video prompt,
  and its `warnings` are advice. The Seedance guide and recipes, the image guides, the overview, the
  prompt library, the thumbnail skill and `novoads-api` now say what the estimate names and that a
  clean estimate does not clear the forbidden-word lists, which are longer than what `banned_polish`
  catches. `seedance-2.md`'s section is now called *What the estimate flags*, the name the lines
  pointing at it already used. The formulas files say the lint flags a word or a shape, where they
  said it refuses one or errors on it.
- **A row that never finishes stops counting on a clock of its own queue:** 5 minutes for an
  analysis, 30 for a caption, transcript, sweep, voice-over or voice change, and up to about two
  hours from its send for a video, an image or a talking actor the provider still reports as
  running. `reference.md` said 30 minutes for all of them.
- **The Seedance and Veo tables list `idempotencyKey`,** and `seedance-2.md` no longer says a field
  outside its table is a `400`: the table holds the fields the formulas use, and the body takes more.
- **The two silent recipes' worked calls send `audioEnabled: false`,** as their prose orders.
  `seedance-2-product-hero.md` also says under its call that the flag mutes the bass and foley its
  prompt describes, and to drop the flag to keep them.
- **The image skills say what their run sends:** `kind`, `prompt`, `model`, `numImages`. The scripts
  have no tier or size flag and render the default, so `quality` and `resolution` belong on the
  estimate only for a direct `POST /v1/images` at that tier.
- **`language` is described as a record.** The spoken language comes from the quoted line, where two
  lines called the field the language the ad is rendered in.
- **A UGC prompt's `@Image1` goes with `referenceAssetIds`.** `seedance-2.md` routed the UGC formula
  to `startImageAssetId`, where the token names nothing, nothing refuses it and the call is charged.
  The table and `novoads-api`'s first-run route now send the product photo first in the array,
  `seedance-2-ugc.md` says which mode its `@Image1` means and how to open on the photo instead, and
  `seedance-2.md` and `reference.md` say the check on a token past the end of the array runs only
  when references are sent.
- **No line promises how long an upload lasts.** An `assetId` can be reused across calls. The lines
  that called it durable, reusable forever or without limit, or said it does not expire, now say that
  instead, and `reference.md` says the spec makes no promise of how long an id lasts, so keep the
  source file and upload it again if a call cannot find or read the file behind an old id, or a job
  built on one fails and its `reasonCode` names no other cause. The lines that called a second
  upload a bug that loses the anchor now say what it is: the same picture under a new id.
- **A job read carries its charge and says why it stopped.** `creditsCharged` is on
  `GET /v1/generations/{jobId}` and on the list, where the lines said the `202` was the only copy:
  log it from the `202` as before, and a lost `202` is one read away. `reasonCode` is in the manual
  now: `reference.md`'s Status lifecycle says what to do for each reason, the recovery lines ask
  for it, and the image scripts print it.
- **A polled image job is read by its own fields.** A one-image job has `outputUrl` and
  `outputAssetId` and no `images[]`, whichever answer it gave, so the lines that said to read
  `images[]` after a `running` answer now name those fields, with `images[]` on a job of several.
  The lines that called the response the only copy of images 2..N now say that of a single-row
  job: a job rendered as one row per image has them on the read and on the list.
- **A `400` is a request refused before any charge.** `reference.md`'s *The shape of a 400* and
  `novoads-api` no longer call it a malformed request and nothing else: a refusal with a name of
  its own, such as `upload_incomplete` or `model_retired`, carries `details.code` or
  `details.reason` and no `details.issues`, and its `message` says what to do.
- **The image library's reference line names its one exception.** T4 with its four publication
  wordmarks pinned beside the product is five references, so that run goes to `nano-banana-pro`.
- **`check-no-rates.sh` reads three more shapes:** a figure after `creditsCharged`, a decimal after
  `quoted`, and `a fraction of a credit`. It also reads `centi-credit` with or without a number.
- **Smaller corrections.** The overview's second-opinion row no longer sends an agent back to a
  family that already failed: when both draw a template wrong, the template is the problem. The
  overview says `clone-image-ad` renders through its own validator, and the template library's
  ratio set includes `4:5`. The README's `resolution` paragraph lists `seedance-2.0-mini` and
  `veo-3.1`, and it no longer says `omni-flash` takes no reference images. `image-to-motion` says
  which cell is dearest moves with the schedules, where it blamed a provider. Fifteen seconds is
  named as `seedance-2.0`'s ceiling, where three lines said Seedance's, and `seedance-2.0-mini`'s
  default of 10 seconds is on the lines that gave 5 for it. `kling-3.md` no longer waits for a model
  that is live. `reference.md`'s `warnings` row is back inside its table, and its line about the CDN
  in front of the API, which cuts a long request at around 125 seconds, names no provider.
  `clone-image-ad`'s guide lists every automatic refund, where it called `502 provider_failed` the
  only one. `nano-banana.md`'s model table says it is the models that page routes between. The
  sample line in `logs/README.md` shows a plainly made-up charge. `safety-suffixes.md` says
  `--no-safe-zone` waives the safe-zone suffix for one run. `template-format.md` and the library's
  closing section name the one `clone-image-ad` skill and its Phase 9, the entry skeleton uses the
  id `nano-banana-pro`, and its ratio line says the two Seedream 5 ids refuse `4:5` and `21:9`.
  `seedance-2-ugc.md` says what its two worked examples leave out, and of the two lines that said
  they pass validation, `novoads-api/SKILL.md` now says what they draw and `ugc-selfie-style.md`
  drops the claim. `seedance-2-product-hero.md` says at its top that its worked example leaves out
  the clause and the ratio line, where it said they were in place, and the thumbnail skill no longer
  points at a phase it does not have. `character-sheet.md` and its GPT twin point at Step 7 for the
  folder and the ids, where they pointed at the QA step. `logs/README.md` and the two image skills'
  logging lines say a slow render is polled, where they said images have nothing to poll.

### Fixed

- **A picture that outlasted the POST's wait is downloaded, not reported missing.** The two
  `generate_image.py` scripts, `validate_image.py` and `generate-batch.sh` read only `images[]`
  after a poll, and the read of a one-picture job has its picture in `outputUrl` and no
  `images[]`, so a paid, finished render that answered `running` ended in "no images" and exit 1.
  They now take `outputUrl` when the read lists no `images[]`. The new `scripts/test-image-poll.sh`
  checks the three Python scripts with every call stubbed, how they print why a job stopped
  included, the batch's own function with a stand-in `curl`, and its run total on planted job
  files; the doctor and CI run it.
- **The thumbnail batch says why a polled job stopped, and its total counts only what stayed
  charged.** When a job that answered `running` stops, `generate-batch.sh`'s FAILED line now names
  its `reasonCode` and `error`, as the Python scripts' line does. Its run total counted a failed or
  blocked job, whose credits come back on their own: it now leaves those out, and it parses each
  job file as the rest of the script does, so a file with a raw newline in its prompt is counted.

## v1.4.0 — 2026-11-07

### Changed

**GPT Image 2.6 Sunburst and Flare, and the default that moved with them (API 2.57.0, 2.58.0).**
`POST /v1/images` takes `gpt-image-2.6-sunburst` and `gpt-image-2.6-flare`, on the 2.5 pair's grid:
the same six ratios, 4 references, 32,000 prompt characters, `quality`, `outputFormat` and the
`sourceAssetId` edit arm. A call that names no model and no preset now renders on 2.6 Sunburst,
where it rendered on 2.5 Sunburst, and an estimate that names no model prices it. The 2.5 pair and
`gpt-image-2` keep working, and the 2.5 and 2.6 ids charge the same as each other. What an
unqualified call sees change is the model in the response and the size: 2.6 comes back at
1088 x 1920 at `9:16` at every quality, where 2.5 could come back larger (up to 2160 x 3840 at
`high`). `novoads-api`'s model tables and its Nano Banana prompt file, the image-ad overview and
its prompt library, the README, `chatgpt-image-ad` (which still locks `gpt-image-2` and now points
label-exact work at 2.6 Sunburst) and the thumbnail and Nano Banana skills' estimate lines say so,
and `verify-image-caps.sh` audits the two new ids. The lines that said every GPT model charges the
same per image now say `gpt-image-2` has its own price at `high`, and the lines that called
`gpt-image-2` the cheaper or the cheapest model now say at which `quality`.

**`reve-2.1` is retired (API 2.48.0), and `sora-2` left the API (2026-09).** The API refuses
`reve-2.1` before any charge with `400` `invalid_input`, `details.reason: "model_retired"`, on
`POST /v1/images` and `POST /v1/estimates`, and a call naming `sora-2` is a `400` `invalid_input`;
`GET /v1/models` lists neither. The README's model tables, `novoads-api`'s model row, image grid
and Nano Banana prompt file, and the image-ad overview say so. `novoads-api`'s router and the
overview send a second opinion on a still to the other image family, and `novoads-api` sends a
clip whose first word must land at once to `seedance-2.0` with a reference or a start frame, then
a trim. `wan-3.0` (API 2.53.0) joins `novoads-api`'s list of video ids. The lines that still said
five generations in flight now say ten (API 2.51.0), and the GPT character sheet says
`nano-banana-pro` takes 14 references, not 4.

**Ten video generations in flight (API 2.51.0).** An organization may now have ten video
generations running at once through the API, up from five, on every plan; the eleventh is the
same `429` with `details.reason: concurrency_limit`. `novoads-api`'s limits table says 10, and
the Pixar, clay, clone-video and image-to-motion skills now submit in waves of up to ten, so a
Pixar board and an eight-beat clay board each go out in one wave.

**Image presets (API 2.40.0).** `novoads-api` documents `preset: "image-to-ad" | "product-to-ad" |
"upscale"` on `POST /v1/images`: the dashboard's three one-photo tools, run on the photo in
`imageAssetId` with no `model` or `prompt`. Quoted by `POST /v1/estimates` with the same `preset`,
charged what it quoted, and polled like any image when it answers `running`. The image-ad overview
says when to reach for one.

**Kling end frame and motion-control sound (API 2.44.0).** `kling-v3-pro` takes
`lastFrameAssetId` beside `startImageAssetId`; `POST /v1/videos/animate-actor` takes
`keepOriginalSound: false`. Neither changes how the job is priced. The driving clip is MP4 or MOV
only: a WebM clip does not render (the provider refuses the container), so convert it to MP4
first, and `POST /v1/uploads` takes no M4V. API 2.45.0 refuses a WebM driving clip with a `400`
before the charge. The `novoads-api` routing row for Kling keeps its original trigger,
and the row for editing an existing MP4 is back to its original wording, with background removal
on a row of its own.

**Images can answer `running` (API 2.39.0).** `POST /v1/images` still usually returns the
finished images, but a render still going after about 105 seconds now answers `200` with
`status: "running"`, the same `jobId` and no images. The three image scripts (`chatgpt-image-ad`,
`nano-banana-image-ad`, `clone-image-ad`) and the YouTube thumbnail batch now poll
`GET /v1/generations/{jobId}` to a terminal status and read `images[]` there, instead of reporting
a paid render as an empty result, and never resubmit it. Every skill, prompt library, guide and
README line that said images are synchronous now says this. Seedream 5 (`seedream-5-lite`,
`seedream-5-pro`) is documented beside the other image models.

**Kling 3.0 on the API (2.38.0).** `kling-v3-pro` is on `POST /v1/videos` where `GET /v1/models`
lists it: 3 to 15 seconds, `16:9`, `9:16` or `1:1`, one resolution, audio on or off, text or a
start frame. The Kling prompt library is no longer parked, and the lines saying Kling is not on the
API are gone. The shortest `durationSeconds` the API publishes is now 3; each model still refuses
what its own grid does not list.

**Background removal, product swap and motion control (API 2.41.0 to 2.43.0).** `novoads-api`
documents `POST /v1/background-removals` (a job or an uploaded video up to 30 seconds),
`productSwap: { actorId, productAssetId }` on the Seedance family (an actor from `GET /v1/actors`,
never an uploaded face), and `POST /v1/videos/animate-actor` (an actor moved by a driving clip you
upload, priced by the clip's measured length). Each is quoted by `POST /v1/estimates`
(`kind: "background-removal"`, `productSwap: true`, `kind: "motion-control"`) and charged what it
quoted.

**`omni-flash` `4k` on API 2.31.0.** `novoads-api`, the Omni Flash prompting guide and the README
add `4k` to Omni's possible resolutions, only where `GET /v1/models` lists it: the server
publishes that tier in some configurations and not others, so read the live list and never assume
it. An Omni render at `4k` is a true 4K source, so its captions bill doubled; price it with the
caption arm of `POST /v1/estimates`. Lines that still said only Seedance takes `resolution` (the
README, `clone-video-ad` and its evals, `image-to-motion`, the Seedance library) now leave room
for Omni.

**`omni-flash` on API 2.29.0 and 2.30.0.** `novoads-api` and the Omni Flash prompting guide read
Omni's resolutions from `GET /v1/models` (send `resolution` only when that list has more than one
value) and document its reference images, reference video, first and last frames and seed. On
`omni-flash`, `startImageAssetId` is a reference image, not a first frame.

**`change-voice` bills by the second (API 2.32.0).** Voice changes are priced from the seconds of
source above a minimum charge, no longer from whole started minutes, the same on every door; the
response adds `billedSeconds` and keeps `billedMinutes` as deprecated. The skill stops saying "per
minute" for voice change and never types a price: quote with `POST /v1/estimates`. A workspace
also has a daily allowance of voice-change source audio (`429 voice_change_daily_cap`) and a busy
state (`503 voice_change_capacity`), both refused before anything is charged.

**`change-voice` can hand back the finished video (API 2.33.0).** `POST /v1/voice-changes` takes an optional
`output`: `"audio"` stays the default and unchanged (a synchronous `200` with the mp3), and
`"video"` answers `202` with a job to poll at `GET /v1/generations/{jobId}`, whose `outputUrl` is
the new mp4; the `202`'s `status` is the job's lifecycle (`queued`, `running`, or `succeeded` with nothing
charged for a change already made). Same price as audio out, quoted by the same `voice-change`
estimate, but charged only once the job finds speech and refunded if it fails after that. It needs a video
source and is enabled per workspace; both refusals are a `400` with nothing charged. The skill
gains a Video out section, `novoads-api/reference.md` stops calling the endpoint synchronous
only, and new evals cover the job, the audio-source refusal and the unchanged default.

### Fixed

**Entry price (2026-10-08).** The README, `AGENTS.md`, `scripts/setup.sh`, `scripts/check-novoads-env.sh`,
`.env.example` and a `clone-image-ad` example still gave the entry price from before the 2026-09-20
ladder. They now say plans start at $15/month (Starter, 200 credits) and link the pricing page with
the date the figure was read. The README opens with one line saying what Novoads is and what the
pack drives.

## v1.3.0 — 2026-09-11

### Changed

**The repo is `novoads/agent-skills`.** It was `novoads/claude-code-ads`; the name described the
one host it started on, and the pack now installs into Claude Code, Cursor and Codex alike.

- Install is `npx skills add novoads/agent-skills`, and the clone is
  `git clone https://github.com/novoads/agent-skills.git`. GitHub serves a permanent redirect from
  the old slug, so existing links, clones and pinned tags keep working — the sweep is about
  pointing at the name that will still be here, not about repairing something broken.
- `novoads-update`'s "is this the pack clone?" probe matches **both** slugs. A clone made before
  the rename keeps the old URL in its git config forever (the redirect moves fetches, not
  `origin`), and matching only the new name would have told exactly those users they were not in
  the pack — the population that skill exists to update.
- Not swept: the 2026-08-07 entry below, which records adopting the `claude-code-ads` identity.
  That happened, and history is not a link.

- **The pack installs as a plugin.** `.claude-plugin/plugin.json` (#101, no entry at the time)
  gives the pack an identity and a skill namespace alongside the marketplace entry: it installs
  as `skills@novoads`, carries no `version` field on purpose (`scripts/release.sh` is the one
  writer of a release; the installed version falls through to the commit SHA instead), and reads
  correctly from a standalone `~/.claude/skills/` drop, not only through the marketplace.
- `plugin.json`'s own `skills` array now reads `["./skills", "./shared/skills"]`, matching
  `marketplace.json`'s copy of the same field. `guard.yml` gained a non-strict `claude plugin
  validate .` step so the two manifests disagreeing again would be red instead of silent.
- **Every mention of the retired $1 trial is gone.** The pack now says there is no free tier
  and no trial, and the entry price lives only in README, AGENTS.md and the setup scripts —
  a skill file an agent reads at spend time carries the fact, never the figure.

## v1.2.0 — 2026-08-13

### Changed

**The naming standard is complete: a product surface carries the brand, a job does not.**

- `novoads-pixar-ad` → `pixar-ad`, `novoads-claymation-ad` → `claymation-ad`,
  `novoads-image-to-motion` → `image-to-motion`. A skill directory name is the slash command
  the user types, and these three name a JOB — the ad they want made — not a Novoads surface.
  `novoads-api` and `novoads-update` keep the prefix, because those two genuinely are the
  surface: one is our REST API, the other updates this pack. Existing installs are repaired
  by `prune_orphans` in `shared/scripts/sync-skill.sh`, which removes a synced skill whose
  source is gone, so nobody ends up with the old name and the new one both answering the
  router.

## v1.1.0 — 2026-08-13

### 2026-08-13

**Added — the pack can now update itself, and knows how old it is.**

- `VERSION` at the repo root, and `metadata.packVersion` stamped into all sixteen
  `SKILL.md` files. Both hold the **last published tag** — `release.sh` is what moves them,
  at cut time — so a main-tracking clone's stamp matches what the world can actually
  download. Every `/v1` response carries `X-Novoads-Pack-Version`, and a skill mentions a
  newer pack **only when that header is ahead of its stamp**: someone tracking main sits
  ahead of the tag by design and must not be told they are behind. That is the whole
  self-check — it does not nag, and it never blocks a run.
- `migrations/` — the one-time repairs a fast-forward cannot perform. A clone made months
  ago is not a fresh clone plus some commits: renamed skills, renamed config keys and
  orphaned generated output all survive a `git pull` that thinks it succeeded.
  `migrations/run.sh` replays them in `sort -V` order above
  `.update-state/last-setup-version`, gates each one on its own touchfile, and is called
  from both `setup.sh` and `update.sh` so either path repairs the same tree. Fresh installs
  adopt the current version and replay nothing. A migration that fails is reported, retried
  next run, and never stops the ones after it.
- `scripts/release.sh` — the one writer of a release. It bumps `VERSION`, re-stamps every
  skill, dates the changelog, commits, and tags **that same commit**. Dry-run by default,
  and it never pushes.
  - The invariant it exists to hold: **the tag commit is the VERSION-bump commit.** gstack
    shipped the other arrangement and got two clocks — a hand-maintained `VERSION` on one
    schedule, installs delivered from branch HEAD on another. Across a measured 29-day
    window, clones sat silently behind while reporting themselves current, and two clones
    holding different trees reported the same version. The assertion interrogates the
    **tag**, not the working copy: it reads `vX.Y.Z:VERSION` back out of the tagged tree and
    requires the stamps in the same commit, because asking whether a tag just created on
    HEAD points at HEAD is a question that answers itself.
  - On `--apply` it prints the post-release checklist, because two of the three steps are
    in another repository and nothing fails when they are skipped: the well-known skill
    index keeps serving the previous tag, and the `/v1` version header keeps advertising
    the previous release, both of them quietly and indefinitely.
  - It warns when any skill description passes 1000 characters. The platform truncates at
    1024, and the tail is where the "NOT for X, use Y instead" disambiguation lives, so a
    description that goes over does not fail — it quietly starts stealing sentences that
    belong to its neighbour. Three descriptions are inside 25 characters of that cliff
    today.

### 2026-08-12

- `change-voice`, the twelfth skill: replace the voice in a finished ad with one from the
  catalog and keep the timing, so the lips still match. `POST /v1/voice-changes` returns audio
  and nothing else, so the three decisions it cannot make are the skill — which voice, which
  spans to replace, and whether the result is any good (#84).
  - Casting is by **measurement**, not by label. `match-voice.py` measures the source's pitch,
    auditions candidate previews and ranks by semitone distance; it shortlists and a human
    picks. No `voiceId` is ever defaulted.
  - `check-speech.py` is a free local refusal that runs **before the upload**. The endpoint
    gates on "does this have an audio track", not "is anyone talking", so a music bed converts
    into vocal noise, bills in full and answers `200`.
  - `assemble-voice-change.py` fences the spans nobody is talking in, so the sound effects
    survive from the original track, copies the picture bit for bit, and measures the file it
    wrote rather than the one it meant to write.
- `novoads-api/reference.md` gains `GET /voices` and `POST /voiceovers`, which had **no
  sections at all** — every skill that cast a voice was working off a one-line summary — plus
  `POST /voice-changes` and its rows in the Limits table and the 429 catalog. Three corrections
  fall out of the same read against deployed spec `2.21.0`: `POST /uploads` mints `audio/mpeg`
  and `audio/wav` ids, the estimates arm list gains `voiceover` and `voice-change`, and the 429
  section stops claiming eight causes when the spec names twelve (#84).
- Review rounds on the above, each one a defect that reported itself as success (#84):
  - The speech check's span walk followed a quiet hum out of the loud region to `0.00`, and
    SKILL.md hands that number to the fence — so an ad with a hum under its head had its whole
    original track overwritten. The walk now stops at the edge of the loud region.
  - The assembly's closing check read the container's duration, which the copied video stream
    drives, so a take that ended early printed PASS over an ad ending in silence. It measures
    the audio stream now, and refuses a take that cannot cover the span it was fenced to.
  - A voice id from the catalog was used as a filename, so an absolute one wrote outside the
    preview cache. Previews are keyed on a hash of their URL, and curl is held to https.
  - A path that could not be read was reported as a file with no speech in it, which is a
    different problem with a different fix.
  - The cost gate announced the conversion and then spent on two transcripts nobody had
    priced. It announces every charged call in the run, each quoted by its own free estimate.

## v1.0.0 — 2026-08-12

First tagged release. Eleven skills on one executable path (REST plus `NOVOADS_API_KEY`), nine
models, and a live estimate in front of anything that spends. Everything below landed before the
tag, in the order it shipped.

### 2026-08-12

- The README opens on proof and one action: a gallery of real output with the asks that produced
  it, and the install prompt above the fold (#76, #77).
- Corrected two claims that had gone false: the draft tier is real, and the image estimate does
  read the prompt (#75).

### 2026-08-10

- `novoads-image-to-motion`, a transport-only port (#71).
- Competitor sweeps run in parallel, because the reason not to had died (#61 through #65).
- A claim in a render now needs a true one of ours behind it, and a testimonial needs a person
  (#66, #67, #68).
- The placeholder lint refuses a prompt carrying scaffolding before it charges, and reads the
  prompt it is actually about to send (#70, #72).

### 2026-08-09

- "Clone this ad" returns the ad, and stops re-asking who you are: brand context is read once and
  reused (#52).
- The video cloner was unreachable through its own description, and the pair was misnamed. Both
  fixed (#54, #55).
- Competitor candidates land as a contact sheet you can click and toggle, rather than a list you
  scroll (#58, #59, #60).

### 2026-08-08

- `spy-competitor-ads`: find a competitor's live ads through the Novoads API (#48).
- The pack runs **one** executable path, REST plus `NOVOADS_API_KEY`, with a CI ratchet that keeps
  the docs from drifting off it (#50).
- One Pixar skill and one clay skill, both REST (#49).
- Setup stops asking the agent to keep things from you, opens `.env`, and names everything the
  pack does (#51).
- Per-model prompt caps match the deployed spec, checked by script (#44).
- The setup close rides the script's stdout, where the clone flow can see it (#46).

### 2026-08-07

- Adopted the `claude-code-ads` identity (#32).
- Skills survive a solo install from skills.sh, not just a full clone (#33).

### 2026-08-05 to 2026-08-06

- The video clone chapter, evals first (#17), then the image clone chapter to match (#25, #26).
- The two Pixar ad skills, and the clay storyboard skill (#20, #23, #27).
- `craft.md`: one home for the three rules that kept getting recopied into every skill (#30).

### 2026-08-04 to 2026-08-05

- `broll-overlay` and `music-mix`, both evals-first and live-validated.
- Transcripts come from the API, which retired the local whisper prerequisite (#16).
- Per-model reference caps, a sanctioned batch clone, and a standing drift alarm (#15), plus the
  three cap claims that one missed (#14).

### 2026-08-02 to 2026-08-03

- First public commit. Veo 3.1 and Sora 2 un-parked (#1), and the fixes a genuinely fresh clone
  turns up (#2).
