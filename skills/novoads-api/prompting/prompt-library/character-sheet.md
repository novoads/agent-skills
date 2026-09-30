# Character sheet (Nano Banana Pro) — generate an AI influencer from a text description

**Use when:** The user wants to create a new AI influencer from scratch by describing them in plain English. Generates a 10-image character sheet (multiple angles, white background) that becomes the reference set for all future generations with that character.

**Model:** `nano-banana-pro`. It is the only Nano Banana on this API — there is no `nano-banana-2` and no Pro/standard choice to make. **This is the default character-sheet workflow** — start here for pure photoreal AI-influencer use.

**See also:** [character-sheet-gpt-image-2.md](character-sheet-gpt-image-2.md) — the same workflow on **ChatGPT Image 2** (`gpt-image-2`). Stylized-photoreal aesthetic and a narrower aspect-ratio grid; pick that one for editorial / stylized brand looks or A/B comparison runs.

## The reference budget — read this first

A generation may cite up to **14 `referenceAssetIds`** on `nano-banana-pro` (spec 2.7.0 —
`gpt-image-2` caps at 4, `reve-2.1` at 8). The budget is generous; the discipline below still
shapes this whole workflow, because more references dilute the hero.

What makes it workable: `POST /v1/uploads` returns a **durable `assetId`** that keeps working
across calls and across sessions. Uploads are free and unlimited; only generations are charged.
So the approved hero is uploaded **once**, and its `assetId` anchors all nine remaining angles —
and every future workflow that uses this character. Re-uploading the same file yields a
different id and silently loses the anchor.

Record the hero's `assetId` in the character folder (see Step 6). It is the single most valuable
artifact this workflow produces.

## Required flow (do NOT skip steps)

1. User describes the influencer in plain English (e.g., "20-year-old female redhead")
2. Agent expands the description into a detailed visual prompt (Step 1)
3. Agent presents the expanded prompt for user review (Step 2)
4. **Price the run and get an explicit yes** (Step 3)
5. **Generate 1 hero front portrait** (Step 4)
6. **User approves the hero image** — do NOT skip this step
7. **Generate 9 remaining angles** citing the hero's `assetId` (Step 5)
8. **QA all images** (Step 6)
9. **Save to `references/influencers/`** using the naming convention (Step 7)

## Step 1: Expand the user's description

Take the user's plain-English description and expand it into a detailed visual prompt. Fill in any unspecified details with natural, photorealistic defaults. The prompt should be specific enough to produce a consistent character.

**Base prompt structure:**

```
A {age}-year-old {gender} influencer with {hair color} {hair texture} {hair length} hair, {skin tone} skin with {distinguishing features}, {eye color} eyes, {build} build, {makeup level}, wearing {clothing}. Clean white studio background, photorealistic, visible skin texture, individual hair strands catching light.
```

**What to specify (fill in defaults if the user doesn't mention):**
- **Age:** Exact number, not a range
- **Hair:** Color, texture (straight/wavy/curly), length (shoulder-length/long/short)
- **Skin:** Tone + one distinguishing feature (freckles, clear, beauty mark, etc.)
- **Eyes:** Color
- **Build:** Slim, athletic, curvy, etc.
- **Makeup:** Soft natural / minimal / none
- **Clothing:** Default to a fitted white t-shirt (neutral, doesn't distract from the character)

**Rules:**
- Use specific visual language, not vague adjectives
- Do NOT use celebrity names or real people's names
- Keep clothing simple and neutral — the character sheet is about the person, not the outfit
- Always include texture cues: "visible skin texture," "individual hair strands catching light"
- Avoid polish words like "cinematic", "ultra-detailed", "hyperrealistic". They produce the plastic look this workflow exists to avoid. Nothing on the API will catch one — describe the light source, the surface, the flaw instead.

## Step 2: Present the expanded prompt for approval

Show the user:
1. The expanded visual description you wrote
2. The 5 descriptor tags you'll use for the folder name (see naming convention below)
3. Ask if anything needs adjusting before generating

## Step 3: Price the run (MANDATORY)

This workflow is **10 generations minimum**, plus any QA retries. Price it before spending:

```bash
curl -sS -X POST "$NOVOADS_BASE_URL/v1/estimates" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"kind":"image","model":"nano-banana-pro","prompt":"<the hero prompt>","numImages":1}'
```

Multiply by 10 and present the total against the user's `balance`. Get one explicit yes covering
the run. The estimate charges nothing and is the **only** legitimate source of a price — never quote
credits from memory, from `logs/novoads-api.jsonl`, or from `MASTER_CONTEXT.md`.

The call says nothing about the prompt itself — no endpoint here does. Re-read the base prompt
against the rules above before approving: it gets reused ten times, so a flaw in it is paid for
ten times over.

## Step 4: Generate the hero image (full body front)

This is the anchor image that defines the character. All other angles will reference it. **Use a full-body shot as the hero** — this gives the model complete visual context (face, hair, build, clothing, shoes, proportions) so every subsequent angle stays consistent. A medium portrait forces the model to invent the lower half for full-body angles.

1. Compose the hero prompt: prepend `"Full body front view, head to toe."` to the base prompt, add `"She/He looks directly at camera with a warm, confident expression. Relaxed stance, weight on one hip. Camera at eye level, soft even studio lighting from both sides."` Include the full outfit (e.g., jeans + white sneakers) in the hero prompt since this is the full-body reference.
2. Call `POST /v1/images` with:
   - `model`: `nano-banana-pro`
   - `prompt`: the hero prompt
   - `aspectRatio`: `9:16`
   - `productId` (optional — organizational only; omit to use the default product)
3. **The call usually returns the image.** It blocks for the render (typically 60–90 seconds) and returns the finished image in `images[]`. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid.
4. **Post-generation QA:** Inspect for anatomy defects per [nano-banana.md](nano-banana.md). Regenerate with a refined prompt if needed (up to 2 retries — each is charged).
5. Download the image to the character's `references/influencers/` folder and **open it for the user** (`open <path>` on macOS, `xdg-open` on Linux) so they can review it at full resolution.
6. **Wait for explicit user approval.** This is the character — if they don't like it, iterate before generating 9 more images. Do NOT proceed without approval.

## Step 5: Generate 9 remaining angles

Once the hero is approved:

1. Upload the approved hero **once** via `POST /v1/uploads` → `PUT` the bytes to the returned `uploadUrl`, echoing the returned `headers` byte for byte → keep the `assetId`.
2. For each of the 9 remaining angles, compose a prompt that:
   - Starts with the angle description
   - References the hero: `"The exact same person from the reference image — same face, same {hair description}, same {distinguishing features}, same {eye color} eyes, same {build} build, same {clothing}."`
   - Specifies white studio background, photorealistic
   - Includes angle-specific lighting and pose
3. Call `POST /v1/images` for each with:
   - Same `model` and `aspectRatio` as the hero
   - `referenceAssetIds`: `[hero_assetId]` — the **same id every time**, no re-upload
   - The angle-specific prompt
4. **Rolling window for drift.** If an angle starts drifting from the hero, add the last one or two *good* angles alongside the hero: `[hero, angle_N-1, angle_N-2]`, well inside the 14-reference cap (spec 2.7.0). Keep the window small even so — never feed a drifted angle forward; a bad reference propagates.
5. **Concurrency is 5.** Fire at most 4 at a time to keep headroom. A 6th in flight returns `429` with `details.reason: concurrency_limit`, and unlike the other 429 causes, slowing down doesn't help — only a finishing job frees a slot.
6. QA each image per [nano-banana.md](nano-banana.md).

### The 10 angles

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

## Step 6: QA all images

Follow [nano-banana.md](nano-banana.md) QA checklist for each image. Additionally check for **cross-image consistency:**
- Same hair color, texture, and length across all 10
- Same face shape and features
- Same skin tone and distinguishing features
- Same clothing

If any image drifts significantly from the hero, note it when presenting results.

## Step 7: Save to references folder

### Folder naming convention

```
references/influencers/{name}-{hair_color}-{hair_style}-{feature}-{eye_color}-{skin_tone}/
```

**Format:** All lowercase, hyphens between words within a descriptor, hyphens between descriptors.

| Position | Category | Examples |
|----------|----------|----------|
| 1 | **Name** (human first name) | `emma`, `sofia`, `kai`, `marcus`, `luna` |
| 2 | **Hair color** | `redhead`, `blonde`, `brunette`, `black-hair`, `silver`, `auburn` |
| 3 | **Hair style** | `wavy`, `straight`, `curly`, `pixie`, `braided`, `bob`, `long-straight` |
| 4 | **Distinguishing feature** | `freckles`, `dimples`, `sharp-jaw`, `high-cheeks`, `beauty-mark`, `clear-skin` |
| 5 | **Eye color** | `green-eyes`, `blue-eyes`, `brown-eyes`, `hazel-eyes`, `gray-eyes` |
| 6 | **Skin tone** | `fair`, `olive`, `tan`, `deep`, `medium`, `porcelain` |

**Examples:**
- `emma-redhead-wavy-freckles-green-eyes-fair/`
- `sofia-brunette-straight-dimples-brown-eyes-olive/`
- `kai-blonde-curly-sharp-jaw-blue-eyes-tan/`
- `marcus-black-hair-fade-strong-brow-brown-eyes-deep/`

### File naming convention

Files are zero-padded and named by angle:

```
01-hero-front.jpg
02-3q-left.jpg
03-3q-right.jpg
04-profile-left.jpg
05-profile-right.jpg
06-face-closeup.jpg
07-back-shoulder.jpg
08-medium-portrait.jpg
09-full-body-3q.jpg
10-above-angle.jpg
```

`01-hero-front.jpg` is always the approved anchor image.

### Also save the hero's assetId

Write the hero's `assetId` into the character folder — an `assets.json` alongside the images is
enough:

```json
{ "hero_asset_id": "<assetId from POST /v1/uploads>", "model": "nano-banana-pro" }
```

Because the id is durable, every later workflow can cite it directly instead of re-uploading —
which is also what keeps the character's identity stable across sessions.

### After saving

- **Open the full character folder** for the user (`open <folder_path>` on macOS, `xdg-open` on Linux) so they can review all 10 images at full resolution
- Present results as a numbered list showing all 10 angles
- Report the **total credits actually charged**, summed from each response's `creditsCharged` — not the estimate

## Using a character sheet for subsequent workflows

Once a character sheet exists in `references/influencers/`, it can be used as input for:

- **Product showcase** ([product-showcase.md](product-showcase.md)) — the hero `assetId` + a product photo to generate the influencer holding the product
- **Influencer recreation** ([influencer-recreation.md](influencer-recreation.md)) — skip the "analyze reference" step since the character already exists
- **Video generation** — pass the hero (or any angle) as `startImageAssetId` on a Seedance video. See the `novoads-api` skill's SKILL.md for the video call. Note the character may shift slightly in a video model's rendering style; say so before the user spends on video.

When referencing an existing character, cite `01-hero-front.jpg`'s `assetId` first — order is
preserved and the first reference is the strongest identity signal. Add up to **three** more
angles if a pose needs extra grounding; four is the hard ceiling.

## Example

**User says:** "Create a 20-year-old female influencer redhead"

**Agent expands to:**
> A 20-year-old female influencer with natural red hair, fair skin with light freckles across her nose and cheeks, green eyes, slim build, soft natural makeup, wearing a fitted white t-shirt. Clean white studio background, photorealistic, visible skin texture, individual hair strands catching light.

**Folder name:** `emma-redhead-wavy-freckles-green-eyes-fair`

**Descriptor tags:** redhead, wavy, freckles, green-eyes, fair

**Flow:** Price the run → generate hero → user approves → upload hero once → generate 9 angles citing that one `assetId` → QA → save folder + `assets.json` → report actual credits → done.
