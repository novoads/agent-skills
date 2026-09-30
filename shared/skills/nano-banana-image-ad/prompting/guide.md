# nano-banana-image-ad — model-specific prompting guide

This guide is the brain for the **`nano-banana-image-ad`** skill — generating standalone Meta ad creatives with **Nano Banana Pro** (`nano-banana-pro`, Google's Gemini Pro Image) on the Novoads API.

For the shared template library and entry format, see:
- [prompt-library.md](../../image-ad-prompting/prompting/prompt-library.md) — 40 validated templates
- [template-format.md](../../image-ad-prompting/prompting/template-format.md) — how to write a new entry
- [safety-suffixes.md](../../image-ad-prompting/prompting/safety-suffixes.md) — the 3 always-on prompt guards
- [OVERVIEW.md](../../image-ad-prompting/OVERVIEW.md) — the ecosystem hub

**One model, no variants.** Novoads serves exactly one Nano Banana: `nano-banana-pro`. The
`nano-banana-2` / `nano-banana-edit` / legacy `nano-banana` split the older skill carried does
not exist here. Every "use the Pro variant for this" instruction has collapsed into "you are
already on it" — the levers that remain are references and prompt craft.

## What Nano Banana Pro is good at

Pick this skill (over `chatgpt-image-ad`) when the ad's success depends on any of these:

- **Photoreal handheld objects** — held-up whiteboard signs, hand-lettered cardboard, handwritten napkin notes, sticky-note + product flatlays, letter-board signs. It renders held-paper texture, marker bleed, and hand-shadow naturalism better than gpt-image-2.
- **Aspirational lifestyle photography** — full-bleed scenic backgrounds (sunset coastline, mountain trail, kitchen at golden hour) with naturalistic lighting and shallow DOF.
- **Multi-image reference blending** — Nano Banana Pro takes up to **14** references on this API (gpt-image-2 caps at 4), and it blends logo + product + style board + character more cleanly. The headroom is real, but 2-4 well-chosen references still usually beat many: extra style refs dilute subject identity.
- **Subject continuity across multiple runs** — pass the same hero portrait `assetId` across N generations and the character stays consistent.
- **Rich material rendering** — leather, metal, fabric, foil, glass, liquid, plasticine. Anywhere the brief says "photoreal" or "tactile".
- **Stop-motion / claymation / Pixar-adjacent aesthetics** — material-based realism that gpt-image-2 flattens.
- **The four extra aspect ratios** — `3:2`, `3:4`, `4:3`, `5:4` exist here and not on gpt-image-2. That alone can decide the route for a bespoke canvas.

## What Nano Banana Pro struggles with

If any of these are core to the ad, **prefer `chatgpt-image-ad` instead**:

- **Dense small body text** — chat bubbles, ChatGPT-response panels, table rows, calendar blocks, Slack messages, comment threads, search results pages. Letters blur or rearrange at small size.
- **UI mimicry of specific platforms** — iOS Messages chrome, Slack window proportions, Google search result layout. The aesthetic is "close enough" but not pixel-faithful.
- **Brand wordmark fidelity** — text wordmarks (FORBES, an exact font weight) can drift if not passed as a reference.
- **Condensed-sans / brutalist typography hero quotes** — letter-spacing and condensed letterforms shift run-to-run.
- **Crossword grids, AirDrop dialogs, fake comment threads** — anything where small-text fidelity inside a rectangular UI element is the whole gag.

It is also the **more expensive of the two default routes**. When a template is a coin flip
between the two models, that is a real tiebreaker — but confirm the actual figures with a live
`POST /v1/estimates`, never from memory.

## Hard limits

These come from the live API contract (`GET /v1/openapi.json` is the authority):

1. **Model is `nano-banana-pro`.** The script refuses everything else, including the retired `nano-banana-2` / `nano-banana-edit` strings and `gpt-image-2`.
2. **Max 14 reference images.** `referenceAssetIds` caps at 14 on `nano-banana-pro` (spec 2.7.0 — `gpt-image-2` takes 4, `reve-2.1` 8). The script enforces it. Headroom is not a goal: 2-4 well-chosen references usually beat many.
3. **Prompts are capped**, and the three always-on suffixes count against it (roughly 1,500 together). The script checks the assembled prompt and fails locally, before spending anything.
4. **No platform/screenshot chrome in output.** `NO_CHROME_SUFFIX` is always on (unless `--allow-chrome`).
5. **Edge-safe rule always on.** Text and focal subjects must sit inside the central 84% of the canvas.
6. **Glyph-safety rule always on.** Plain words inside body-text blocks; emoji OK in headlines.
7. **No edit mode on THIS model.** `nano-banana-pro` does not publish `sourceAssetId`: no inpainting, no mask, no `--source`, no img2img. Here, "swap the background" is a fresh generation with the original passed as a reference. It is **not** true of the API as a whole — `gpt-image-2` does edit from a prompt (spec `2.10.0`), so route a genuine edit to `chatgpt-image-ad` instead of re-drawing it here.

## Aspect ratios

One model, one enum:

| Ratio | `nano-banana-pro` | `gpt-image-2` |
|---|---|---|
| `1:1` (default) | ✅ | ✅ |
| `2:3` | ✅ | ✅ |
| `4:5` | ✅ | ✅ |
| `9:16` | ✅ | ✅ |
| `16:9` | ✅ | ✅ |
| `21:9` | ✅ | ✅ |
| `3:2` | ✅ | ❌ |
| `3:4` | ✅ | ❌ |
| `4:3` | ✅ | ❌ |
| `5:4` | ✅ | ❌ |

**Default to `4:5` for Meta feed-portrait** — it renders natively. `aspectRatio` **defaults to
`1:1`**, so a Stories creative that forgot to set `9:16` is a square image and a wasted charge.
Always send it explicitly.

## Reference images — the one mechanic worth mastering

`POST /v1/uploads` returns a **durable, reusable `assetId`**. That single fact drives most of
what this model is good for:

- Upload the hero portrait once; pass the same `assetId` on every run in the campaign. That is what holds a face steady across generations — not a model flag.
- Upload the product and the brand wordmark once each; they are the two references that most often stop drift.
- Order is preserved, so positional language in the prompt works ("the product in the first reference image").
- Four is the ceiling. When a brief seems to need five, one of them is usually style guidance that belongs in the prose instead.

## Workflow phases (`nano-banana-image-ad`)

This skill produces *images* — not Meta ads. Meta-side uploading is handled by the separate
`meta-ad-builder` skill.

### Phase 1: Preflight

Verify in this exact order; bail on the first failure with a fix-it message.

1. The working directory has a `.env` with `NOVOADS_API_KEY` (`novo_` + 64 hex).
2. `./scripts/check-novoads-env.sh` prints OK. A 401 is a bad or revoked key; a 403 with `details.reason: plan_required` is a good key on an account without API access — different problems, say which.

### Phase 2: Gather inputs

| Input | Source | Notes |
|---|---|---|
| Seed prompt | User | Creative direction in their words. You will rewrite it (see Phase 3). |
| Reference image(s) (`--image-ref`) | User | Optional but strongly recommended. Up to **4**. |
| Variant count `N` | User, default 1 | Cap at 4. Sent as `numImages` in one call; every image is charged. |
| Aspect ratio | User | One of the ten above. Reject anything else. |

### Phase 3: Prompt rewrite

**First check the prompt library** ([prompt-library.md](../../image-ad-prompting/prompting/prompt-library.md)).

#### 3a — Check the prompt library

If the user's seed prompt or brief maps onto an existing template:
1. Read the matching template's `Model notes` block — **only proceed if it says nano-banana is clean, preferred, or strong**. If gpt-image-2 is strongly preferred, suggest switching skills.
2. Fill in the `{placeholder}` variables.
3. Use that as the rewritten prompt.

#### 3b — Fleshing out a fresh prompt (or filling a template)

When writing or completing a prompt, anchor on:

- Subject and pose
- **Lighting and time of day** — this model renders natural light beautifully; specify "golden hour through east-facing window," "diffuse overhead studio softbox," "harsh midday sun with crisp shadows."
- **Lens / framing** — "35mm shallow DOF," "macro extreme close-up," "wide environmental"
- Color palette / mood
- Composition
- **Negative space for text overlay** if the ad has body/headline copy
- **Reference roles** — name each reference explicitly: "the product in the first reference image," "the lighting/mood from the second," "the character from the third." Multi-ref blending improves dramatically with named roles, and order is preserved so positional language is reliable.
- **Material specifics** — "subsurface scattering on skin," "satin foil reflectivity," "knit fabric weave," "marker bleed at stroke edges." This model renders material distinctions; lean into them.
- **Standalone-creative scope** — never describe iOS chrome, Sponsored badges, engagement counts, or platform UI.
- **Avoid keyword-soup prompts** — one well-written paragraph beats a comma-separated keyword list.
- **Concrete over polished.** "Cinematic", "ultra-detailed" and "hyperrealistic" produce the plastic look this format exists to avoid. Nothing on the API will catch one — describe the light source, the surface, the flaw instead.

Show the rewritten prompt to the user as one block. Tell them which template (if any) it's
based on. Ask: "Use this, edit it, or start over?" Loop until approved.

### Phase 4: Price it

`POST /v1/estimates` with `{"kind":"image","model":"nano-banana-pro","prompt":"<final>","numImages":<N>}`.
Free. Show the user `credits` and whether it fits their `balance`, and wait for an explicit yes.

**Name the model** — the image schedules differ by more than 3×, so an estimate that forgot
`model` prices gpt-image-2 and understates this run. This is the **only** legitimate source of
a price: not memory, not the logs, not `MASTER_CONTEXT.md`.

The call says nothing about the prompt. No endpoint on this API reads one for quality, so the
rewrite rules in Phase 3 are the only check there is — apply them before you price, not after.

Price the **assembled** prompt including the safety suffixes. The estimate body is strict — it
takes only `kind`, `prompt`, `model`, `numImages`, `language`. It never sees `aspectRatio` or
references, and neither changes the price. It also does not run moderation, so a priced prompt
can still come back `422`.

### Phase 5: Generate

```bash
./skills/nano-banana-image-ad/scripts/generate_image.py \
  --prompt "<rewritten>" \
  --aspect-ratio <ratio> \
  --n <N> \
  --image-ref <product.png> \
  [--image-ref <style-board.png>] \
  [--image-ref <character.png>] \
  --out ./generated \
  --env-file .env
```

The call blocks for the render, typically 60–90 seconds. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid.

Each line on stdout is JSON for one image (`variant`, `path`, `job_id`, `width`, `height`,
`aspect_ratio`, `model`, `credits_charged`). Display the paths to the user.

### Phase 6: Confirm variants

Show all paths and ask: "Use all / use these specific ones / regenerate / cancel." Open the
output folder so the user can see them.

### Phase 7: Hand off

Selected images are ready for the **`meta-ad-builder`** skill — the handoff is a list of file
paths.

## Retry mode (when an image fails the QA visual check)

Common Nano Banana defects + their fix prompts:

- **Garbled small text** → If text is essential, switch to `chatgpt-image-ad`; that is the real fix. Otherwise scale the text block up to occupy ≥30% of the canvas and re-render.
- **Wordmark drift** → Pass the wordmark as `--image-ref` AND name it ("the brand wordmark from the first reference image"). There is no higher-fidelity variant to escalate to — references are the lever.
- **Wrong character identity across runs** → Reuse the **same `assetId`** for the portrait on every call, and name its role in the prompt. Re-uploading the same file gives a new id and loses the anchor.
- **Extra fingers / wrong limb count** → Add an explicit anatomy clause: "exactly two hands, five fingers each, anatomically correct arms, no extra limbs."

**Retry cap: 2 regeneration attempts** (3 total including the first). Every retry is a fresh
charge — there is no free re-roll — so keep the cap and report the extra credits at the end of
the run. If defects remain after the cap, stop, show the best attempt, and ask the user how to
proceed.

## Out of scope — fail clearly

- **Meta upload** — the `meta-ad-builder` skill. This skill produces images only.
- **Ad copy writing** — different skill.
- **Video, carousel, DCO ads** — image only; video lives in the `novoads-api` skill.
- **ChatGPT Image 2 / gpt-image-2 generation** — use `chatgpt-image-ad` instead.
- **Editing or retouching an existing image** — not on this model. `gpt-image-2` takes `sourceAssetId` (spec 2.10.0); send it to `chatgpt-image-ad`.
- **Editing the prompt library** — use `clone-image-ad` to add new validated templates.
