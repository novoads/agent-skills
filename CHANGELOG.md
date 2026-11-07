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

**Facts the pack had stale, made true against the deployed spec (2.59.0).** For an agent:

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
- **Smaller corrections.** The overview's second-opinion row no longer sends an agent back to a
  family that already failed: when both draw a template wrong, the template is the problem. The
  overview says `clone-image-ad` renders through its own validator, and the template library's
  ratio set includes `4:5`. The README's `resolution` paragraph lists `seedance-2.0-mini` and
  `veo-3.1`, and it no longer says `omni-flash` takes no reference images.

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
