# Product showcase — AI person with product

**Use when:** The user wants to generate a video of an AI person holding, using, or demonstrating a physical product.

## Workflow

```
User provides product image(s)
        |
        v
Agent writes Nano Banana prompt
(AI person + product interaction)
        |
        v
POST /v1/uploads  ->  durable assetId
(product photo, uploaded once)
        |
        v
POST /v1/images  (poll it if it answers `running`)
model nano-banana-pro
referenceAssetIds [product assetId]
        |
        v
Finished still returns in the response
(person holding/using product)
        |
        v
User approves still image
        |
        v
Upload still -> assetId
        |
        v
startImageAssetId on POST /v1/videos
(Seedance — async, poll to terminal)
        |
        v
Final product showcase video
```

## Step-by-step

### 1. Collect product info

Ask the user for:
- **Product image(s)** — photos of the item from different angles
- **Product context** — what it is, key features, target audience (check `MASTER_CONTEXT.md` or the product's fields via `GET /v1/products` for existing context)
- **Video intent** — UGC selfie-style? Polished ad? Unboxing?
- **Person description** — what should the AI person look like? (Or reuse an existing influencer prompt from `MASTER_CONTEXT.md`, or an existing character sheet's hero `assetId` — see [character-sheet.md](character-sheet.md))

There is no engine question to ask: `nano-banana-pro` is the only Nano Banana on this API.

### 2. Compose the Nano Banana image prompt

Follow the template below. The prompt should describe:

1. **The person** — age, gender, appearance, wardrobe, expression, pose
2. **The product interaction** — how they hold it, where it sits in frame, what angle, how prominent
3. **Match the video intent** — if the final video is UGC selfie-style, the still should already look like a selfie. If it's a polished product ad, frame accordingly
4. **Cite the product image** in `referenceAssetIds` so the model can composite it. Up to **14** references on `nano-banana-pro` (spec 2.7.0), though the product plus the character's hero shot is usually all this format needs. Name each one's role in the prompt ("the product in the first reference image"); order is preserved.

### 3. Generate the still image

1. **Price it** with `POST /v1/estimates` (`{"kind":"image","model":"nano-banana-pro","prompt":"…","numImages":1}`), show `credits` against the user's `balance`, and get an explicit yes. It charges nothing, and it is the only legitimate source of a price. Budget for up to 2 QA retries, each charged.
2. Upload the product photo via `POST /v1/uploads` → `PUT` the bytes to the returned `uploadUrl`, echoing the returned `headers` byte for byte → keep the `assetId`. It is durable, so the same product photo is uploaded once and reused across every shoot.
3. Optionally upscale a small product image first (good practice for fidelity; the "too small → 422" rule was specific to the previous backend and is **unverified** here).
4. Call `POST /v1/images` with:
   - `model` — **`nano-banana-pro`**
   - `prompt` — the product showcase prompt
   - `aspectRatio` — match the video intent (`9:16` for reels, `16:9` for landscape, `1:1` for square). **It defaults to `1:1`**, so set it explicitly.
   - `referenceAssetIds` — `[product_assetId]` (+ the character hero if you have one), max **14** on `nano-banana-pro`
   - `productId` (optional — organizational only; it does not influence what is generated)
5. **The call usually returns the image**: it blocks for the render (typically 60–90 seconds) and returns the finished still in `images[]`. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid.
6. **Post-generation QA:** Inspect the still per [nano-banana.md](nano-banana.md) (hands, product edges, merged geometry). **Regenerate** with a refined prompt if needed — up to **2** retries after the first attempt, each billed. **Only then** treat the still as ready to show.
7. Show the **QA-passed** (or best-effort after max retries) image to the user, and report the cumulative `creditsCharged`.

### 4. Get user approval

- Show the generated still to the user — **after** internal QA and auto-retries in step 3–4.
- **Wait for explicit approval** before proceeding to video.
- If the user wants a different creative direction (not just defect fixes), iterate on the prompt and regenerate per SKILL.md credit rules.

### 5. Generate video from approved still

1. Upload the approved still via `POST /v1/uploads` → keep the `assetId`.
2. Pass it as `startImageAssetId` on `POST /v1/videos` with a Seedance model. `startImageAssetId` and `referenceAssetIds` are **separate modes** — sending both is a `400`, not a merge.
3. Include dialogue/script in the video prompt. The spoken line gets its **own** approval gate before the cost gate — see the `novoads-api` skill's SKILL.md.
4. Video is **asynchronous**, unlike an image call (which usually answers in its response): `202` + `jobId` → poll `GET /v1/generations/{jobId}` for a **terminal** status → `…/watch` for the download. That skill owns the sequence and its own cost gate.

## Prompt template

```text
{{PERSON_DESCRIPTION}}. They are {{INTERACTION}} a {{PRODUCT_DESCRIPTION}}.
Setting: {{SETTING}}. Camera: {{CAMERA}}. Lighting: {{LIGHTING}}.
The product is {{PRODUCT_PLACEMENT}} — clearly visible, in-focus, natural grip.
Style: {{STYLE}}. Avoid: studio lighting, floating product, unnatural hand pose.
```

## Example

```text
A 25-year-old woman with shoulder-length brown hair in a casual white t-shirt,
smiling warmly at camera. She is holding a small amber glass skincare bottle in
her right hand at chin height, label facing camera. Setting: bright modern
bathroom, morning light through frosted window. Camera: front-facing selfie
angle, slightly above eye level. The product is centered in the lower third of
frame — clearly visible, natural grip with fingertips around the bottle.
Style: authentic, unfiltered, soft natural tones. Avoid: studio lighting,
floating product, perfect skin retouching.
```

## Script prompting for video stage

Once the starting frame is approved and video generation begins, the video model prompt should:

- Reference the starting frame ("continues from the still image")
- Add **motion and dialogue** — what the person says about the product
- Follow the Seedance prompt library ([seedance-2.md](seedance-2.md) and the format-specific files alongside it). **Veo 3.1 and Sora 2 are live** — see [veo-3-1.md](veo-3-1.md) and [sora-2.md](sora-2.md) — but neither takes `referenceAssetIds`, so a showcase built on reference images stays on Seedance. Kling 3.0 is on this API as `kling-v3-pro` (API 2.38.0), but it takes no `referenceAssetIds` either, so a showcase built on reference images stays on Seedance.
- Pull product context from `MASTER_CONTEXT.md` or the product's fields (`description`, `mainFeatures`, `painPoint`)

### Video prompt template

```text
{{PERSON}} holds {{PRODUCT}} and speaks directly to camera. {{ACTION_BEATS}}.
Product details: {{KEY_FEATURES}}. Tone: {{TONE}}. Setting: {{SETTING}}.
Camera: {{CAMERA}}. Dialogue: "{{SCRIPT}}". {{STYLE_AND_IMPERFECTIONS}}.
```

## Product context via API

Products carry marketing context (not images):

```
POST /v1/products
{
  "name": "Product Name",
  "description": "What the product is",
  "targetAudience": "Who it's for",
  "mainFeatures": ["feature 1", "feature 2", "feature 3"],
  "painPoint": "Problem it solves",
  "perceived": "How customers see it"
}
```

Product images are not part of the product object on this API. For product showcase workflows,
the product photo is uploaded via `POST /v1/uploads` and cited by `assetId` in
`referenceAssetIds` on the generation call.

A `productId` on a generation is **organizational only** — it files the job under that product
and none of its fields reach the prompt. Product context helps because *you* put it in the
prompt, not because the API forwards it.

## Tips

- **Product fidelity:** If the generated still distorts the product (wrong label, color shift), try a cleaner product photo with white/neutral background.
- **Hand pose:** "natural grip with fingertips" in the prompt helps avoid the common AI issue of unnatural hand poses around objects.
- **Consistency:** Save the approved person prompt in `MASTER_CONTEXT.md` for reuse across multiple product shoots with the same AI influencer.
