# Character sheet (ChatGPT Image 2 / gpt-image-2) — generate an AI influencer

**Use when:** The user wants to create a new AI influencer using **gpt-image-2** instead of Nano Banana. Same 10-image character sheet workflow, tuned for gpt-image-2's quirks.

**Parallel to:** [character-sheet.md](character-sheet.md) (Nano Banana version) — same goal, different model. Pick based on the table below.

## When to pick gpt-image-2 vs Nano Banana for character sheets

| Factor | `gpt-image-2` | `nano-banana-pro` |
|---|---|---|
| **Photoreal human faces** | Good — stylized photoreal | **Stronger** — more "shot on camera" feel |
| **Character identity continuity across N images** | Moderate — drifts over many gens; needs a stronger text anchor | **Stronger** |
| **Multi-reference blending** | 4 refs, blended less smoothly | 4 refs, **blended more smoothly** |
| **Stylized / slightly illustrated look** | **Stronger** — distinct gpt-image aesthetic | Pure photoreal, less stylized |
| **Aspect ratios** | `1:1` `2:3` `4:5` `9:16` `16:9` `21:9` | those **plus** `3:2` `3:4` `4:3` `5:4` |
| **Cost** | **Cheaper** per image | More per image |
| **Best for** | Brand has a slightly stylized / editorial / poster-art aesthetic; A/B comparison runs; cost-sensitive exploration | The default for pure photoreal AI-influencer / UGC use |

Both models cap references at **4** — that is no longer a differentiator, and the old "5 vs 14"
split is gone. Confirm the cost figures with a live `POST /v1/estimates`; never quote them from
memory.

**Default recommendation:** start with Nano Banana ([character-sheet.md](character-sheet.md)). Use this gpt-image-2 version when (a) the brand aesthetic specifically wants the gpt-image-2 look, (b) you're running a side-by-side test, or (c) the user explicitly asks for ChatGPT Image 2.

## Required flow (do NOT skip steps)

1. User describes the influencer in plain English (e.g., "20-year-old female redhead").
2. Agent expands the description into a detailed visual prompt (Step 1).
3. Agent presents the expanded prompt for user review (Step 2).
4. **Generate 1 hero front portrait** with gpt-image-2 (Step 3).
5. **User approves the hero image** — do NOT skip this step.
6. **Generate 9 remaining angles** using the hero + up to 3 prior angles as `referenceAssetIds` (Step 4 — note the 4-ref cap).
7. **QA all images** (Step 5).
8. **Save to `references/influencers/`** using the naming convention (Step 6).

## Step 1: Expand the user's description

Same as the Nano Banana version — see [character-sheet.md § Step 1](character-sheet.md). The base prompt structure is identical:

```
A {age}-year-old {gender} influencer with {hair color} {hair texture} {hair length} hair, {skin tone} skin with {distinguishing features}, {eye color} eyes, {build} build, {makeup level}, wearing {clothing}. Clean white studio background, photorealistic, visible skin texture, individual hair strands catching light.
```

**gpt-image-2 tuning notes:**

- **Be more specific than you'd be with Nano Banana.** gpt-image-2 leans on the text more than on the reference image for identity, so vague descriptors like "soft features" drift more across angles. Pin specific facial-anatomy notes: "narrow nose bridge", "high cheekbones with subtle hollows", "rounded chin", etc.
- **Always include the texture cues** — "visible skin texture, fine hair flyaways catching light, subtle pores" — gpt-image-2 defaults to a slightly smoother / more illustrated rendering without them.
- **Avoid celebrity / real-person names.** Same rule as Nano Banana.

## Step 2: Present the expanded prompt for approval

Show the user:
1. The expanded visual description (be more anatomically specific than the Nano Banana flow — see Step 1 note).
2. The 5 descriptor tags for the folder name (same convention as Nano Banana — see Step 6).
3. **Flag that this is the gpt-image-2 variant** — tell them you can swap to Nano Banana if they want a more photoreal feel.
4. Ask if anything needs adjusting before generating.

## Step 3: Generate the hero image (full body front)

Anchor image. All 9 other angles will reference it. **Use a full-body shot as the hero** — gives the model complete visual context (face, hair, build, clothing, shoes, proportions).

1. Compose the hero prompt: prepend `"Full body front view, head to toe."` to the base prompt, add the standard hero pose/lighting clauses:
   > "She/He looks directly at camera with a warm, confident expression. Relaxed stance, weight on one hip. Camera at eye level, soft even studio lighting from both sides."

   Include the full outfit (e.g., jeans + white sneakers) in the hero prompt since this is the full-body reference.

2. Call `POST /v1/images` with:
   - `model`: **`gpt-image-2`** ← key difference from the Nano Banana version
   - `prompt`: the hero prompt
   - `aspectRatio`: **`9:16`** (on gpt-image-2's grid; note it does **not** take `3:2`, `3:4`, `4:3` or `5:4`)
   - `productId` (optional — organizational only; omit to use the default product)

3. **The call usually returns the image**: it blocks for the render (typically 60–90 seconds) and returns the finished image in `images[]`. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid.

4. **Post-generation QA:** Inspect for anatomy defects per [nano-banana.md](nano-banana.md) (the QA checklist applies to any image model). gpt-image-2-specific watch-outs:
   - **Hands and fingers** — gpt-image-2 still occasionally renders extra fingers or warped hands; check both visible hands carefully on the full-body shot.
   - **Skin texture flatness** — if the output looks too smooth / illustrated, regen with explicit texture clauses ("visible pores, fine flyaways, light grain").
   - **Identity vs the prompt** — does the rendered character match every facial-anatomy clue you specified? If not, the angles will drift even more.
   - Regenerate with refined prompt if needed (up to 2 retries).

5. Download the image to the character's `references/influencers/{folder}/` and **open it for the user** so they can review at full resolution:
   - macOS: `open <path>`
   - Linux: `xdg-open <path>`
   - Windows: `explorer <path>`

6. **Wait for explicit user approval.** This is the character — if they don't like it, iterate before generating 9 more images. Do NOT proceed without approval.

## Step 4: Generate 9 remaining angles (4-ref cap)

Once the hero is approved:

1. Upload the hero image **once** via `POST /v1/uploads` → `PUT` the bytes to the returned `uploadUrl`, echoing the returned `headers` byte for byte → keep the `assetId`. It is durable and reusable across every later call and session, so this upload never repeats.
2. **Reference strategy (the rolling window):**
   - `gpt-image-2` accepts **max 4 `referenceAssetIds` per request** — the tightest of the three (`reve-2.1` 8, `nano-banana-pro` 14), which is what makes the rolling window below necessary here and optional on the Nano Banana sibling.
   - Always include the **hero** as the first ref (the anchor). Order is preserved.
   - For angles 2–4: pass `[hero]` only — you have no prior angles yet anyway.
   - For angles 5+: pass `[hero, angle_N-1, angle_N-2, angle_N-3]` — the three most recent angles plus the hero. This keeps continuity from the most recent successful generation while still anchoring on the hero.
   - **Don't include angles that drifted.** If angle N looked off, exclude it from the reference set for angle N+1 — a bad reference propagates.
   - The window is one slot narrower than it used to be, which puts more weight on step 3's text anchor. Write it in full every time.
3. Strengthen the textual prompt for each angle (gpt-image-2 leans on text more than Nano Banana does):
   - Start with the angle description (see the table below).
   - **Re-state the full character description verbatim** — don't shortcut with "the same person from the reference." Include hair / skin / eye / build / outfit. Yes it's verbose; this is what holds identity on gpt-image-2.
   - Add: `"The exact same person — same face, hair, body, and clothing as the reference images. Photorealistic, visible skin texture."`
   - Specify white studio background.
   - Include angle-specific lighting and pose.
4. Call `POST /v1/images` for each with:
   - Same `aspectRatio: 9:16` as the hero
   - `model`: `gpt-image-2`
   - `referenceAssetIds`: the array per step 2 above (max 4)
   - The angle-specific prompt
5. **Concurrency is 5.** Fire at most 4 at a time. A 6th in flight returns `429` with `details.reason: concurrency_limit` — and unlike the other 429 causes, slowing down doesn't help; only a finishing job frees a slot.
6. QA each per the Step 3 checklist.

### The 10 angles (same as Nano Banana version)

| # | File name | Angle | Prompt prefix | Pose/lighting notes |
|---|-----------|-------|---------------|---------------------|
| 1 | `01-hero-front.jpg` | Full body front (hero) | `Full body front view, head to toe.` | Direct eye contact, relaxed stance, weight on one hip, full outfit visible, soft even lighting from both sides |
| 2 | `02-3q-left.jpg` | 3/4 left | `Three-quarter view from the left.` | Angled 45° to camera-left, looking toward lens, soft directional light from camera-right |
| 3 | `03-3q-right.jpg` | 3/4 right | `Three-quarter view from the right.` | Angled 45° to camera-right, looking toward lens, soft directional light from camera-left |
| 4 | `04-profile-left.jpg` | Profile left | `Left profile view.` | Full side profile facing camera-left, hair falls naturally, soft rim light from behind |
| 5 | `05-profile-right.jpg` | Profile right | `Right profile view.` | Full side profile facing camera-right, hair falls naturally, soft rim light from behind |
| 6 | `06-face-closeup.jpg` | Face close-up | `Face close-up, tight crop.` | Forehead to chin, hair down and loose, every detail visible, soft beauty lighting, catchlights in both eyes |
| 7 | `07-back-shoulder.jpg` | Back/over shoulder | `Back view, looking over her/his shoulder.` | Faces away, looking back over right shoulder, playful glance, hair visible from behind |
| 8 | `08-medium-portrait.jpg` | Medium portrait | `Front-facing medium portrait, waist up.` | Waist-up framing, direct eye contact, warm expression, soft even lighting |
| 9 | `09-full-body-3q.jpg` | Full body 3/4 | `Full body three-quarter view.` | Full length, angled 45° to camera-left, walking toward camera, same full outfit |
| 10 | `10-above-angle.jpg` | Above angle | `Slightly above angle, looking up at camera.` | Camera positioned slightly above, chin tilted up, bright smile, soft overhead lighting |

### gpt-image-2 angle-specific tips

- **Profile shots (4, 5)** drift the most on gpt-image-2 — facial features can shift between profile and 3/4. Pass `[hero, 02-3q-left]` as refs for `04-profile-left` (the 3/4 anchors the facial features in a related angle).
- **Face close-up (6)** is where identity really shows. If drift appears here, regenerate with the hero PLUS angle 8 (medium portrait, same front-facing pose) as refs.
- **Back shoulder (7)** — the face is partial. Less drift risk. Just hero as ref is fine.

## Step 5: QA all images

Follow [nano-banana.md](nano-banana.md) QA checklist for each image. Additionally check for **cross-image consistency:**
- Same hair color, texture, and length across all 10
- Same face shape and features (gpt-image-2 is more prone to subtle drift here — be strict)
- Same skin tone and distinguishing features (freckles in same positions, etc.)
- Same clothing

If any image drifts significantly, note it when presenting results. **Offer the user a "regenerate with stronger anchor" option:** rerun that angle with `[hero, 01-hero-front, 06-face-closeup]` (or whatever angles render most cleanly) as refs, plus an even more verbose textual character description.

## Step 6: Save to references folder

Same folder naming + file naming convention as the Nano Banana version — see [character-sheet.md § Step 6](character-sheet.md). The folder structure does NOT change; this version's outputs live alongside any Nano Banana outputs.

**Tip — distinguishing gpt-image-2 vs Nano Banana outputs:**

If you generate a character with BOTH models for A/B testing, save them in sibling folders with a `-gpt` suffix:

```
references/influencers/emma-redhead-wavy-freckles-green-eyes-fair/         # Nano Banana version
references/influencers/emma-redhead-wavy-freckles-green-eyes-fair-gpt/     # gpt-image-2 version
```

The agent should treat each folder as a fully independent character sheet — don't cross-reference angles from the Nano Banana folder when generating gpt-image-2 angles (or vice versa); the rendering styles differ enough that mixing breaks consistency.

## Cost — price it before Step 3

This workflow is **10 generations minimum**, plus QA retries (~2 per sheet is typical here vs
~1 on Nano Banana, because identity drift needs more correction). Price it first:

```bash
curl -sS -X POST "$NOVOADS_BASE_URL/v1/estimates" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"kind":"image","model":"gpt-image-2","prompt":"<the hero prompt>","numImages":1}'
```

Multiply by 10, present the total against the user's `balance`, and get one explicit yes for the
run. The estimate charges nothing and is the **only** legitimate source of a price — **not**
`logs/novoads-api.jsonl` and **not** `MASTER_CONTEXT.md`. Neither holds credit numbers; the log
is observability only.

Report the **actual** total afterwards, summed from each response's `creditsCharged`.

`gpt-image-2` is the cheaper of the two character-sheet models, which cuts the other way from
how this file used to read — the extra retries it needs are the real cost, not the per-image
rate. If the choice is close, price both models: two estimates, and neither charges anything.

## Using a gpt-image-2 character sheet for subsequent workflows

Once the character sheet exists, it can be used as input for:

- **Product showcase** ([product-showcase.md](product-showcase.md)) — use the hero image + product photo to generate the influencer holding the product. Use `gpt-image-2` again for the showcase still if you want the rendering style to match the sheet.
- **Influencer recreation** ([influencer-recreation.md](influencer-recreation.md)) — skip the "analyze reference" step since the character already exists.
- **Video generation** — pass the hero (or any angle) as `startImageAssetId` on a Seedance video; see the `novoads-api` skill's SKILL.md for the call. The same `assetId` you already uploaded works directly. Note Seedance may render the character with a slight rendering-style shift since it is not gpt-image-2-native; mention this before the user spends on video. (Veo 3.1 and Sora 2 are live on this API but take a start frame only — no `referenceAssetIds` — so a character sheet drives them through `startImageAssetId`, one angle per clip.)
- **UGC selfie-style** ([ugc-selfie-style.md](ugc-selfie-style.md)) — gpt-image-2 has a slightly stylized aesthetic that can fight against "iPhone selfie" realism cues. Consider using the Nano Banana sheet for UGC use cases even if the gpt-image-2 sheet exists for the same character.

**Cross-model rendering style:** if you mix references from the gpt-image-2 sheet with a Nano Banana generation request, the model will average between styles. Pick one model per derived workflow for cleanest output.

## Example

**User says:** "Create a 20-year-old female influencer redhead — use ChatGPT Image not Nano Banana"

**Agent expands to:**
> A 20-year-old female influencer with natural deep-auburn red hair, mid-length and softly wavy, fair skin with light freckles scattered across the bridge of her nose and high cheekbones, almond-shaped emerald-green eyes, slim athletic build with narrow shoulders, soft natural makeup, wearing a fitted white t-shirt and dark fitted jeans with white sneakers. Clean white studio background, photorealistic, visible skin texture with subtle pores, fine flyaway hairs catching light, individual eyelashes visible.

(Note the extra anatomy specificity vs the Nano Banana example — gpt-image-2 needs the verbose anchor.)

**Folder name:** `emma-redhead-wavy-freckles-green-eyes-fair-gpt`

**Descriptor tags:** redhead, wavy, freckles, green-eyes, fair

**Flow:** Price the run → generate hero (gpt-image-2) → user approves → upload hero once → generate 9 angles with `[hero]` + recent angles as refs (max 4 total) → QA strictly for identity drift → save to `-gpt` folder → report actual credits → done.
