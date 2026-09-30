# Influencer recreation from reference image

**Use when:** The user provides a photo of an influencer (or themselves) and wants to recreate that person in AI-generated content.

## Required flow (do NOT skip steps)

1. User provides a reference image
2. Agent analyzes the image (Step 1 below)
3. Agent writes a Nano Banana-style recreation prompt (Step 2)
4. **Price the still and get an explicit yes**
5. **Generate a still image** with `POST /v1/images`
6. **User approves** the still image
7. **Only after approval** → generate video with the approved still as `startImageAssetId`

**Image route:** `POST /v1/images` with `model: "nano-banana-pro"`. The original photo is
uploaded via `POST /v1/uploads` and cited in `referenceAssetIds` — there is no base64 field on
this API. The call usually returns the images: it blocks for the render (typically 60–90 seconds) and
returns the finished image. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid.

**Video route (after approval):** upload the approved still → pass its `assetId` as
`startImageAssetId` on a Seedance video. See the `novoads-api` skill's SKILL.md for the call.
Veo 3.1 and Sora 2 are **not** on this API.

## Workflow

### Step 1: Analyze the reference image

When the user shares an image, **dissect it systematically** using this checklist. Describe what you see — do not invent or assume details not visible.

**Face and features:**
- Estimated age range
- Skin tone (light / medium / olive / tan / deep / dark)
- Face shape (oval, round, square, heart, etc.)
- Distinctive features (dimples, freckles, beauty marks, jawline)

**Hair:**
- Color (natural shade — e.g. "warm chestnut brown," not just "brown")
- Length (above shoulder / shoulder-length / mid-back / long)
- Texture and style (straight, wavy, curly, coily; loose, pulled back, braided, etc.)
- Parting (center, side, none visible)

**Eyes and brows:**
- Eye color if visible
- Brow shape (arched, straight, thick, thin)
- Makeup if present (winged liner, smoky, natural, none)

**Makeup and skin:**
- Level (bare-faced, natural/minimal, glam, editorial)
- Lip color
- Skin finish (dewy, matte, natural)

**Body and pose:**
- Build (petite, slim, athletic, curvy, plus-size)
- Posture and pose (relaxed, confident, leaning, arms crossed, etc.)
- Hand position and gestures

**Clothing and accessories:**
- Garment type, color, fabric texture (e.g. "cream satin button-up blouse")
- Jewelry (earrings, necklace, rings — material and style)
- Other accessories (sunglasses, hat, bag)

**Lighting and environment:**
- Light direction and quality (golden hour side light, overhead fluorescent, ring light, window light)
- Background (blurred rooftop, bedroom, studio, street, nature)
- Color temperature (warm, neutral, cool)

**Vibe / energy:**
- Expression (warm smile, serious, candid laugh, pensive)
- Overall aesthetic (editorial, casual, glam, sporty, bohemian)

### Step 2: Write the recreation prompt

Combine the analysis into **one dense paragraph** (80-150 words) following this structure:

```
[Subject description with physical features] in [setting/environment].
[Clothing and accessories described specifically].
[Pose and expression]. [Lighting described as physical properties].
[Camera and style]. [Skin and texture realism cues].
```

**Rules:**
- Use **specific visual language**, not vague adjectives ("warm chestnut wavy hair past her shoulders" not "nice hair")
- Describe **lighting as physics** ("soft directional golden-hour light from camera-left creating gentle shadows on the right side of her face") not mood words alone
- Include **at least one texture cue** for realism ("visible skin texture," "fabric sheen," "individual hair strands catching light")
- Do NOT use celebrity names or real people's names in the prompt
- State aspect ratio and any framing (close-up, medium shot, etc.)

### Step 3: Present to user for approval of the PROMPT

Show the user:
1. Your **breakdown** of what you observed in the image (the analysis)
2. The **recreation prompt** you wrote
3. Ask if anything needs adjusting before generating the image

### Step 4: Generate the still image (Nano Banana)

Once the user approves the prompt:

1. Read **[nano-banana.md](nano-banana.md)** and follow the vendor guide's formula.
2. **Price it** with `POST /v1/estimates` (`{"kind":"image","model":"nano-banana-pro","prompt":"…","numImages":1}`), show the user `credits` against their `balance`, and get an explicit yes. It charges nothing, and it is the only legitimate source of a price. Budget for up to 2 QA retries, each charged.
3. Upload the original photo via `POST /v1/uploads` → `PUT` the bytes to the returned `uploadUrl`, echoing the returned `headers` byte for byte → keep the `assetId`. It is durable: reuse it for every later generation of this person instead of re-uploading.
4. Optionally upscale a small reference first (good practice for likeness; the "too small → 422" rule was specific to the previous backend and is **unverified** here).
5. Call `POST /v1/images` with:
   - `model` — **`nano-banana-pro`** (the only Nano Banana on this API; there is no variant to choose)
   - `prompt` — the recreation prompt
   - `aspectRatio` — match the reference image or user preference. **It defaults to `1:1`**, so set it explicitly.
   - `referenceAssetIds` — `[original_assetId]`, up to **14** total on `nano-banana-pro` (spec 2.7.0)
   - `productId` (optional — organizational only)
6. **Post-generation QA:** the response carries the image only when the render finishes in time; one still going after about 105 s answers `status: "running"` with no images, so poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there, and never resubmit it (that job is already paid). Inspect the image as soon as you have it (see [nano-banana.md](nano-banana.md) — Post-generation QA and Regeneration loop). If you see defects (extra fingers, bad hands, etc.), regenerate with a refined prompt — up to **2** retries after the first attempt, each billed. **Do not show the user a still as "the result" until QA passes or retries are exhausted** (if still bad after retries, explain and show attempts).
7. **Show the QA-passed (or best-effort) still next to the original reference**, and report the cumulative `creditsCharged`.

### Step 5: User approves the still image

- Show the recreation result alongside the original reference — **after** internal QA and any auto-retries above.
- **Wait for explicit user approval** before proceeding to video.
- If the user is not satisfied, iterate on the prompt and regenerate (this is separate from automatic QA retries; follow credit confirmation rules in SKILL.md for new user-directed generations).

### Step 6: Generate video from approved image

Only after the user says the still looks good:

1. Upload the approved still via `POST /v1/uploads` → keep the `assetId`.
2. Pass it as `startImageAssetId` on a Seedance video (`POST /v1/videos`). Note `startImageAssetId` and `referenceAssetIds` are **separate modes** — sending both is a `400`, not a merge.
3. Video is **asynchronous**, unlike an image call (which usually answers in its response): the call returns `202` with a `jobId`; poll `GET /v1/generations/{jobId}` for a **terminal** status, then `…/watch` for the download. The `novoads-api` skill's SKILL.md owns that sequence, including its own cost gate.

## Example

**Reference analysis:**
> Woman in her mid-20s, medium olive skin tone, oval face with subtle dimples. Warm chestnut brown wavy hair, shoulder-length, center-parted, individual strands catching light. Hazel-green eyes, natural arched brows. Minimal makeup — light coverage, nude lip, dewy skin finish. Slim build, relaxed upright posture. Wearing a cream satin button-up blouse, small gold hoop earrings. Soft golden-hour light from camera-left, shallow depth of field, blurred urban rooftop background. Warm confident smile with direct eye contact. Casual editorial vibe.

**Recreation prompt:**
```text
A woman in her mid-20s with medium olive skin, oval face, and subtle
dimples. Warm chestnut brown wavy hair, shoulder-length, center-parted,
individual strands catching golden light. Hazel-green eyes, natural
arched brows, minimal makeup with nude lip and dewy skin. She wears a
cream satin button-up blouse and small gold hoop earrings. Relaxed
upright posture, warm confident smile with direct eye contact. Soft
directional golden-hour light from camera-left creates gentle shadows.
Shallow depth of field, blurred urban rooftop background. Medium
close-up, editorial portrait style. Visible skin texture, fabric
sheen on blouse. Photorealistic.
```

## Tips for consistency across multiple generations

- Save the approved prompt text in `MASTER_CONTEXT.md` under a heading like **"Influencer: [name/alias]"** so future sessions can reuse it without re-analyzing.
- When generating video from the recreation, pass the approved still's `assetId` as `startImageAssetId` on a Seedance video (see [reference.md](../../reference.md) for the upload → assetId pipeline).
- **Reuse the same `assetId`** rather than re-uploading the same photo. A fresh upload gives a different id and quietly loses the identity anchor that was holding the face steady.
- Small wording changes between generations will drift the face. Keep the core description **frozen** and only vary pose, clothing, or setting in subsequent prompts.
