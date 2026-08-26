---
name: zack-d-style-ad
description: >-
  Build a Zack-D-Films-style animated science-explainer ad through the Novoads API: a
  narrated 3D explainer that shows WHY a physical product works — script first, one
  still per scene, each still animated as its own clip, cut to a single voiceover. Use
  when the user asks for a "Zack D Films style" ad, a "science explainer ad", a
  "mechanism ad", a "narrated cartoon / 3D ad where the narrator explains the mechanism",
  an "educational product ad", or wants to show what happens inside the body or inside
  the device when a physical product is used. Not for software, apps, APIs or services:
  "explain how our product / API works in a video" is a demo or screencast, not this
  genre — say so and stop. Not for animating ONE existing still (image-to-motion),
  character-comedy storyboard ads (pixar-ad, claymation-ad), cloning a reference video
  (clone-video-ad), or talking-head UGC (novoads-api).
---

# 3D Explainer Ad (Zack-D-style)

An explainer ad earns attention by teaching. The narrator names a problem, reveals its
root cause, shows the mechanism that fixes it, and only then shows the product. The
render style is matte 3D in an empty pale void; the persuasion is the structure, not the
polish. A viewer should finish it feeling they learned something — the sale rides along.

The pipeline is deterministic at both ends and latent in the middle: **script → scene
map → stills → clips → voiceover → assembly**. The craft lives in the script and the
scene briefs; everything after them is mechanics this pack already documents.

The genre rules that make the format recognizable — the eight script blocks, the
human→mechanism→human sandwich, scene density, accent discipline, the no-text rule —
live in [references/formulas.md](references/formulas.md). Read it before writing the
script, not after a flat draft.

## Before anything: this runs on a Novoads account

- **Base URL:** `https://api.novoads.ai/v1`. **Auth:** `Authorization: Bearer
  $NOVOADS_API_KEY` from `.env`. Check with `./scripts/check-novoads-env.sh`; missing
  key → `./scripts/setup.sh`.
> **REST key required. A Novoads MCP connector is not a substitute.** If
> `NOVOADS_API_KEY` is missing or still the placeholder, stop before any
> generation work and tell the user: "Before continuing, create an API key at
> <https://novoads.ai/dashboard/settings?tab=api> and paste it into `.env`."
> That holds even when `mcp__novoads__*` tools are connected and authenticated in
> the session. Never call `mcp__novoads__*` tools from this repo's workflows: they
> are a different surface with different behavior, including the units they quote
> costs in. Repo installs verify with `./scripts/check-novoads-env.sh`; a solo
> install checks `NOVOADS_API_KEY` in the environment.
- No account yet? **<https://novoads.ai/?utm_source=claude-code&utm_medium=github&utm_campaign=skill-pack>**
  The entry offer is a **$1 trial**. Never call it free.

Every HTTP mechanic — auth, strict bodies, status codes, the poll loop, uploads,
concurrency, error envelopes — is written once in
[`novoads-api/SKILL.md`](../novoads-api/SKILL.md) and its `reference.md`. This file
carries the genre and the ordering; the sibling skills carry the per-model mechanics.

**The cost gate, stated for this genre.** One ad is many charges: N scene stills + N
clips + 1 voiceover. Price every class with `POST /v1/estimates` in this session
(`kind:"image"`, `kind:"video"` with the prompt, `kind:"voiceover"` with the script) and
say the multiplication out loud before anything fires — "12 stills + 12 clips + 1 VO"
is a sentence the user must see with live numbers next to it. No rate lives in this
file, on purpose. A re-run of one scene is one still + one clip, and is priced again.

## Step 1 — Script first. The script decides how many scenes exist.

Write the full ad as a **spoken voiceover only** — no scene directions, no labels.
Build it from the eight blocks in
[formulas.md §1](references/formulas.md): hook, problem agitation, villain (root
cause), mechanism (problem-mechanism then solution-mechanism), proof, product, dream
outcome, CTA. Rules that are not style preferences:

- **5th-grade language.** Short words, short sentences. If a 10-year-old would not say
  the sentence out loud, rewrite it.
- **Under-write.** Every line must fit a 2–3 second scene slot; a lean read is what
  makes the cut feel fast. Target ~3.2 words/second of final runtime.
- **Every factual claim is verified before it is voiced.** Product specs from the
  product page, numbers from a source the user can name. No invented statistics, no
  invented review counts.
- The VO body ceiling on `POST /v1/voiceovers` is **1,000 characters** — a 30–35s
  script sits near 550 and fits; a 60s script may not. Check before promising length.

**Gate: the script is approved on its own, before any charge.** The user reads the
exact words. Iterate here — a script revision is free; a scene revision is two charges.

## Step 2 — Scene map: one still per line, density over economy

Split the approved script into scenes of **one spoken line (~2–3s) each**. More scenes
rather than fewer — something new must be happening on screen at every line. A 30s ad
is ~12 scenes; do not compress it to 6 "so it's cheaper" without saying that tradeoff
out loud (that decision belongs to the user, priced).

Map each scene to its block and check the shape against
[formulas.md §2–§4](references/formulas.md):

- **The opening scene contains the human.** Object-only hooks are the measured failure
  mode of this genre (eval E1). The stakes live on a person within the first second.
- **The sandwich holds:** human scenes open (problem) and close (payoff + CTA); the
  object/mechanism scenes sit in the middle where the narrator teaches.
- **The product appears in NO scene before its reveal block** (eval E2). The scenes
  before it show only the problem world.
- **The payoff is active.** The character does things (commute, carry, stride) — never
  a static happy pose until the final CTA hold.

## Step 3 — Stills: anchor first, then every scene, references pinned

Render all stills with `nano-banana-pro` via `POST /v1/images` — mechanics, reference
rules and the upload contract are
[`nano-banana-image-ad`](../nano-banana-image-ad/SKILL.md)'s; this file adds only the
genre's ordering and guards.

1. **Character anchor first.** One full-body still of the recurring character on the
   void. Its `assetId` is durable — pass it in `referenceAssetIds` on **every scene
   that shows the character**, which is what keeps the face consistent across scenes.
2. **Product reference pinned in every scene that shows the product.** Unpinned means
   invented — the sibling skill's rule, measured there and re-confirmed in this
   genre's build. If the user has a product photo, upload it once and reuse the id.
3. **Scene stills, one per scene**, each prompt from the scene-brief patterns in
   [formulas.md §5](references/formulas.md), each carrying the shared style block plus
   that scene's composition, lighting and — critically — what is **absent**.

Genre guards for every still prompt:

- **Style register:** realistic proportions, matte vinyl surfaces, soft subsurface skin
  glow. Never "cute", "chibi", "big head", "kawaii" — the register drifts to mascot
  instantly (eval E3).
- **Accent discipline:** the world is neutral; the product's color appears ONLY on the
  product; one villain accent color, one hero accent color
  ([formulas.md §4](references/formulas.md)).
- **Scenes before the reveal say so:** "the product has not been introduced yet; no
  [product color] objects of any kind." A style line naming the product's color is
  enough to summon it — measured; that is why the guard is per-scene, not global.
- **No text anywhere.** No captions, no logos, no wordmarks, no UI. The narrator
  carries every word (formulas.md §3).

**Gate: the user reviews the stills as a contact sheet before any clip is priced.**
Style is won or lost here at image prices. A wrong still is regenerated for one image
charge; a wrong clip discovered later is an image charge plus a video charge.

## Step 4 — Clips: one scene, one clip, one action

Animate each approved still as its own clip in **start-image mode** — the mechanics,
the upload flow, the `startImageAssetId`-vs-`referenceAssetIds` exclusivity, and the
**dated known issue that currently routes start-image renders to `seedance-2.0`** are
all in [`image-to-motion`](../image-to-motion/SKILL.md). Follow its
Step 4 verbatim, with this genre's motion constraints:

- **One action and at most one camera move per clip.** The clip only has to carry a
  2–3s slot; a second idea is drift.
- Write motion that fits **that exact still**: name the object that moves, the
  direction, the easing. End on a hold.
- Close every motion prompt with the no-drift guard: *"Keep every material, color and
  shape exactly as in the image — no morphing, no style drift, no new objects
  appearing. No text."*
- `durationSeconds`: render **4–5s** per clip and trim to the slot at assembly. The
  trim margin is the edit's freedom; a clip rendered at exactly slot length leaves
  none.
- `audioEnabled: false` on every clip. The voiceover and music are laid at assembly;
  clip-invented audio fights the mix, and narration must never live in the render
  (one voice per ad — the [`pixar-ad`](../pixar-ad/SKILL.md) VO
  doctrine applies unchanged).

Render the **riskiest scene first** — usually the mechanism impact shot — look at it,
and only then batch the rest. One clip is the style check; eleven clips are not a
place to discover a systematic miss.

## Step 5 — Voiceover and music

- **One VO take of the whole script**, `POST /v1/voiceovers`, voice picked ONCE from
  `GET /v1/voices` and named to the user before the charge. Per-line takes cast a
  different-sounding read per line; one take is the format's gapless narration.
- Time the read: transcribe the finished take with the Whisper step from
  [`caption-video`](../../shared/skills/caption-video/SKILL.md) to get per-line
  timestamps. Those timestamps ARE the cut map — each scene's slot is its line's
  start/end (recipe in [formulas.md §6](references/formulas.md)).
- If the take runs long, a **pitch-preserved tempo stretch up to ~1.15×** is
  inaudible and cheaper than re-recording; past that, cut words, not quality.
- Music: an instrumental bed, laid under the VO with
  [`music-mix`](../../shared/skills/music-mix/SKILL.md) — duck it **18–22 dB under
  the narration**, gentle build toward the product reveal, fade on the CTA hold.

## Step 6 — Assemble, then judge two things separately

Trim each clip to its cut-map slot, concatenate, lay VO and bed
([formulas.md §6](references/formulas.md) has the exact ffmpeg recipe). Working files
go in `outputs/<name>/`, long prompts in `prompts/` — never a new top-level directory.

QA the cut on two independent axes:

- **Structure:** does every block land, in order, on its line? Does the product stay
  invisible until its reveal? Is the opening human?
- **Likeness:** does it read as the genre — void, matte 3D, accent discipline, gapless
  narration, point-down CTA hold?

A cut can pass one and fail the other. Iterate per scene: the unit of revision is one
still + one clip. **Never re-render the whole ad to fix one scene** — per-scene
architecture is the reason this genre is affordable to iterate.

## Hard rules

1. **Script approved before any charge; stills approved before any clip.** Two gates,
   both cheap, both mandatory.
2. **Price every charge class live** from `POST /v1/estimates` in this session, and say
   the full multiplication (stills + clips + VO) before the first render. No rate
   lives in this file.
3. **The opening scene contains the human.** An object-only hook fails eval E1.
4. **The product appears in no still before its reveal block**, and every pre-reveal
   prompt says so explicitly. Fails eval E2 otherwise.
5. **No text in any frame.** The narrator carries every word.
6. **One action per clip, rendered 4–5s, trimmed to its slot.** One long multi-scene
   render is not this skill (eval E4) — it is the failure this architecture replaces.
7. **One voiceover take, one voice, named before the charge.**
8. **Never put narration in a clip's own audio.** `audioEnabled: false`; the mix owns
   all sound.
9. **Every factual claim in the script is verified or attributed** before it is voiced.
10. If the ad is for a brand the user does not own, publishing it is their decision —
    deliver it as a **concept ad** and say so; never present it as client work.
