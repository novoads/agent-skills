# Changelog

What changed in the **pack**: the skills, the scripts, the setup path and the docs.

This is not an API changelog. When a file here and the deployed spec disagree, the spec wins,
and [`GET /v1/openapi.json`](https://api.novoads.ai/v1/openapi.json) is where its own history
lives.

Entries land under `## Unreleased`. `./scripts/release.sh` dates that heading into
`## vX.Y.Z — YYYY-MM-DD` and opens a fresh one; it never invents the prose. Group an entry
as Added / Changed / Fixed, or as dated `###` subsections like the ones below.

## Unreleased

### Added

**`image-to-motion` ships seven finished examples**, each with the still we sent beside the last
frame that came back, the ask, three timed frames, the clip and the prompt —
[skills/image-to-motion/README.md](skills/image-to-motion/README.md), media under
`assets/gallery/image-to-motion/`. Rendered 2026-08-15 on `seedance-2.5` at 720p through the
skill as a customer runs it. Nobody in the field shows the input beside the output; this skill's
claim is *that exact image, moving, every word intact*, and a pair is the only thing that shows it.

- **Eval E6 has been run** (thirteen renders): text that is in the still survives our render
  path at 720p; text that exists only in the prompt does not. Hard rule 8 now says so, with the
  date, instead of forbidding the claim.
- **New craft, measured, now in SKILL.md and eval E10**: on this API the still is frame one, so an
  element that is in the still cannot be literally absent at 0.0s — written that way the model
  cut to the opening state (four of six) or duplicated the element (two of six). Name the vanish
  and stage the return instead (three of three clean); keep anything that carries words in the
  still; use an opening-state still only for text-free reveals.
- The `seedance-2.5` wait is measured (154–385s per 8–10s clip) instead of "unknown".
- The root README's image-to-motion row is re-rendered on `seedance-2.5` and its stale note —
  that 2.5 refused every start image — is retired; #85 fixed that on 2026-08-12.

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
