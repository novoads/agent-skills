# chatgpt-image-ad — model-specific prompting guide

This guide is the brain for the **`chatgpt-image-ad`** skill — generating standalone Meta ad creatives with **ChatGPT Image 2** (`gpt-image-2`) on the Novoads API.

For the shared template library and entry format, see:
- [prompt-library.md](../../image-ad-prompting/prompting/prompt-library.md) — 40 validated templates
- [template-format.md](../../image-ad-prompting/prompting/template-format.md) — how to write a new entry
- [safety-suffixes.md](../../image-ad-prompting/prompting/safety-suffixes.md) — the 3 always-on prompt guards
- [OVERVIEW.md](../../image-ad-prompting/OVERVIEW.md) — the ecosystem hub

## What `gpt-image-2` is good at

Pick this skill (over `nano-banana-image-ad`) when the ad's success depends on any of these:

- **Dense text fidelity** — table rows, chat bubbles, ChatGPT-response panels, comment threads, Slack messages, comparison tables, Apple Notes lists, weather/forecast UI, fake search results pages.
- **UI mimicry** — iOS dialogs, iMessage threads, AirDrop modals, Google search pages, Slack conversations, Apple Notes / Calendar / Weather, dating-app cards. ChatGPT Image 2 was trained extensively on these patterns and reproduces them faithfully.
- **Logo and wordmark legibility** — publication wordmarks (FORBES, WIRED, Vogue), brand wordmarks, small-caps subheads, monospace numbers.
- **Typography-led layouts** — brutalist big-statement hero quotes, magazine mastheads, editorial article heros, condensed-sans hero stats.
- **Diagrammatic layouts** — flowcharts, stacked-bar comparisons, calendar timelines, annotated callouts with arrows.

It is also the **cheapest tier of image model on this API**, which matters when a run asks for
four variants or a clone workflow burns six generations. The two GPT Image 2.5 models,
`gpt-image-2.5-flare` and `gpt-image-2.5-sunburst`, sit on that same tier and share this model's
whole grid: six ratios, 4 references, a 32,000-character ceiling, the edit arm. Sunburst is the
one to name when labels and fine detail have to survive; Flare is the fast one. Confirm the actual
figure with a live `POST /v1/estimates`. Never quote one from memory.

## What `gpt-image-2` struggles with

If any of these are core to the ad, **prefer `nano-banana-image-ad` instead**:

- **Photoreal handheld objects** — held-up whiteboard signs, handwritten napkin testimonials, flatlay product photography with rich material rendering (leather + metal + fabric textures next to each other).
- **Aspirational lifestyle photography** — full-bleed scenic backgrounds (sunset coastline, mountain trail, kitchen at golden hour) with naturalistic lighting.
- **Stop-motion / claymation / Pixar / clay textures** — anything that needs material-based realism.
- **Blending several references into one subject** — gpt-image-2 caps at 4 references on this API while Nano Banana Pro takes up to 14, and Nano Banana Pro also merges them more smoothly. When the composition needs more than four sources, the route is decided.

## Hard limits

These come from the live API contract (`GET /v1/openapi.json` is the authority):

1. **Model is `gpt-image-2`.** The script refuses other model strings (`dall-e-3`, `gpt-image-1`, etc.). Predictable model means predictable cost and behavior per run.
2. **Max 4 reference images.** `referenceAssetIds` caps at 4 on `gpt-image-2`. The script enforces it. When a composition genuinely needs more sources, `nano-banana-pro` takes up to 14 (spec 2.7.0) — switching skill is the escalation path.
3. **Prompts are capped**, and the three always-on suffixes count against it (they run to roughly 1,500 together). The script checks the assembled prompt and fails locally, before spending anything.
4. **No platform/screenshot chrome in output.** The `NO_CHROME_SUFFIX` is always on (unless you explicitly `--allow-chrome` for the rare UGC screen-recording aesthetic). Output is the standalone ad creative — the static image that gets uploaded.
5. **Edge-safe rule always on.** Text and focal subjects must sit inside the central 84% of the canvas. Backgrounds may bleed.
6. **Glyph-safety rule always on.** Plain words inside body-text blocks. Emoji OK in headlines.
7. **Edit mode exists in the GPT family, and only there.** `sourceAssetId` on `POST /v1/images` (spec `2.10.0`; since `2.25.0` on `gpt-image-2`, `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst`) edits an existing image from a prompt, so "change the background of this image" is an edit, not a re-draw. What does NOT exist is masking, region selection or an img2img strength dial: the change is described in words. `sourceAssetId` and `aspectRatio` are mutually exclusive, because an edit's output tracks the source's shape.

## Aspect ratios

One model, one enum — no per-broker matrix any more:

| Ratio | `gpt-image-2` | `nano-banana-pro` / `reve-2.1` |
|---|---|---|
| `1:1` (default) | ✅ | ✅ |
| `2:3` | ✅ | ✅ |
| `4:5` | ✅ | ✅ |
| `9:16` | ✅ | ✅ |
| `16:9` | ✅ | ✅ |
| `21:9` | ✅ | ✅ |
| `3:2` `3:4` `4:3` `5:4` | ❌ | ✅ |

**Every ratio the shared template library uses (`1:1`, `2:3`, `9:16`) renders natively here**,
so no template needs a fallback-and-crop. Only a bespoke prompt asking for `3:2`, `3:4`, `4:3`
or `5:4` hits the gap — for those, switch to `nano-banana-image-ad`.

`aspectRatio` **defaults to `1:1`**. A Stories or Reels creative that forgot to set `9:16` is a
square image and a wasted charge. Always send it explicitly.

The script does not auto-crop — it returns what the API produced and warns via stderr if
dimensions come back below 1024 on either side.

## Workflow phases (`chatgpt-image-ad`)

This skill produces *images* — not Meta ads. Meta-side uploading is handled by the separate
`meta-ad-builder` skill. The phases here cover input → prompt → price → generate → confirm.

### Phase 1: Preflight

Verify in this exact order; bail on the first failure with a fix-it message.

1. The working directory has a `.env` with `NOVOADS_API_KEY` (`novo_` + 64 hex).
2. `./scripts/check-novoads-env.sh` prints OK. A 401 is a bad or revoked key; a 403 with `details.reason: plan_required` is a good key on an account without API access — different problems, say which.

### Phase 2: Gather inputs

| Input | Source | Notes |
|---|---|---|
| Seed prompt | User | The creative direction in their words. You will rewrite it (see Phase 3). |
| Reference image(s) (`--image-ref`) | User | Optional but **strongly recommended** when the ad features a specific product. Up to **4**. |
| Variant count `N` | User, default 1 | Cap at 4. Sent as `numImages` in one call; every image is charged. |
| Aspect ratio | User | One of `1:1`, `2:3`, `4:5`, `9:16`, `16:9`, `21:9`. Reject anything else. |

### Phase 3: Prompt rewrite

**First check the prompt library** ([prompt-library.md](../../image-ad-prompting/prompting/prompt-library.md)). It has 40 validated parameterizable templates with per-model notes.

#### 3a — Check the prompt library

If the user's seed prompt or brief maps onto an existing template, use it:
1. Read the matching template's `Model notes` block — **only proceed if it says `gpt-image-2: clean` or "preferred"**. If it says nano-banana-pro is preferred, suggest switching skills.
2. Fill in the `{placeholder}` variables for the user's brand.
3. Use that as the rewritten prompt.

Tell the user which template you matched and why.

#### 3b — Fleshing out a fresh prompt (or filling a template)

When writing or completing a prompt, anchor on:

- Subject and pose
- Lighting and time of day
- Lens / framing
- Color palette / mood (pull from the brand's identity)
- Composition (rule of thirds, leading lines)
- **Negative space for text overlay** if the ad has body/headline copy
- **Reference roles** — if `--image-ref` is being used, name each reference's role explicitly in the prompt (e.g. "the product in the first reference image", "the lighting from the second"). Order is preserved, so positional language works. Multi-reference quality improves when each reference is labeled.
- **Standalone-creative scope** — never describe iOS chrome, Sponsored badges, engagement counts, or platform UI. The script's no-chrome guard catches violations, but write the prompt as if the rule is on you.
- **gpt-image-2 strengths to lean on** — explicit typography (font weight + size feel), UI proportions ("iOS dialog with rounded corners ~24px"), small-text body content (treat lines as exact strings).
- **Concrete over polished.** Words like "cinematic", "ultra-detailed" and "hyperrealistic" produce the plastic look this format exists to avoid. Nothing on the API will catch one — describe the real thing instead: the light source, the surface, the flaw.

Show the rewritten prompt to the user as one block. Tell them which template (if any) it's
based on. Ask: "Use this, edit it, or start over?" Loop until approved.

### Phase 4: Price it

`POST /v1/estimates` with `{"kind":"image","model":"gpt-image-2","prompt":"<final>","numImages":<N>}`.
Free. Show the user `credits` and whether it fits their `balance`, and wait for an explicit yes.

This is the **only** legitimate source of a price — not memory, not the logs, not
`MASTER_CONTEXT.md`. It says nothing about the prompt: no endpoint on this API reads one for
quality, so the rewrite rules in Phase 3 are the only check there is. Apply them before you
price, not after.

Price the **assembled** prompt including the safety suffixes, and remember the estimate body is
strict — it takes only `kind`, `prompt`, `model`, `numImages`, `language`. It never sees
`aspectRatio` or references, and neither changes the price.

### Phase 5: Generate

```bash
./skills/chatgpt-image-ad/scripts/generate_image.py \
  --prompt "<rewritten>" \
  --aspect-ratio <ratio> \
  --n <N> \
  --image-ref <product.png> \
  [--image-ref <style-board.png>] \
  --out ./generated \
  --env-file .env
```

The call is synchronous and blocks for the render, typically 60–90 seconds. Nothing to poll.

Each line on stdout is JSON for one image (`variant`, `path`, `job_id`, `width`, `height`,
`aspect_ratio`, `model`, `credits_charged`). Display the paths to the user.

If any image comes back below 1024 on either side, regenerate it (the script logs a warning to
stderr but still emits the JSON line). If the call failed, stop and report the error from stderr.

### Phase 6: Confirm variants

Show all paths and ask: "Use all / use these specific ones / regenerate / cancel." One
confirmation covers all selected images. Open the output folder so the user can see them.

### Phase 7: Hand off

The selected images are ready for the **`meta-ad-builder`** skill. The handoff is a list of
file paths; that skill does the cloning + copy-writing + upload.

If the ad-builder expects a specific shape, write the paths to a known location
(e.g. `./generated/run-<ts>.jsonl`) and tell the user where.

## Retry mode (when an image fails the QA visual check)

If an image has obvious defects (extra fingers, garbled text, wrong UI proportions, blurred
wordmark), regenerate with a **revised prompt** that explicitly corrects the issue. Do NOT
resend the same payload and expect a different outcome.

Common gpt-image-2 defects + their fix prompts:
- **Garbled small text** → "Render <specific text block> at LARGE size, occupying at least 25% of the canvas height. Plain English words only, no glyph artifacts."
- **Wrong text count** (e.g. asked for 3 Slack messages, got 4) → Explicit count, e.g. "EXACTLY THREE message rows, no fourth row, no scroll cutoff at the bottom."
- **Wordmark drift** → Pass the actual wordmark file as `--image-ref` AND name it in the prompt ("the brand wordmark from the first reference image").
- **UI proportion drift** (e.g. iOS dialog too small) → "The iOS dialog occupies the central 70% of the canvas width."

**Retry cap: 2 regeneration attempts** (3 total including the first). Every retry is a fresh
charge — there is no free re-roll — so keep the cap and report the extra credits at the end of
the run. If defects remain after the cap, stop, show the best attempt, and ask the user how to
proceed.

## Out of scope — fail clearly

- **Meta upload** — the `meta-ad-builder` skill. This skill produces images only.
- **Ad copy writing** — different skill.
- **Video, carousel, DCO ads** — image only; video lives in the `novoads-api` skill.
- **Nano Banana image generation** — use `nano-banana-image-ad` instead.
- **Masked or region-selected retouching** — this model edits from a prompt (`sourceAssetId`, spec 2.10.0), but there is no mask and no img2img strength dial.
- **Editing the prompt library** — use `clone-image-ad` to add new validated templates.
