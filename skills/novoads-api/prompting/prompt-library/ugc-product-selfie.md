# UGC product selfie — character + product + style reference workflow

**Use when:** The user wants to generate a UGC-style selfie image of one of their AI influencers holding/using a product. Combines a character sheet, a product photo, and style reference images into a single Nano Banana generation.

## Required inputs

| Input | Source | Role in `referenceAssetIds` |
|-------|--------|---------------------------|
| **Character hero** | `references/influencers/{name}/01-hero-front.jpg` | Identity — face, hair, build, skin |
| **Product photo** | `references/products/{product}.png` | What they're holding/using |
| **Style references** (2) | `references/aesthetics/{style}/` | Visual vibe — lighting, framing, quality |

Each input is uploaded once via `POST /v1/uploads` → `PUT` the bytes to the returned
`uploadUrl`, echoing the returned `headers` byte for byte → keep the `assetId`. The ids are
**durable**: a character hero and a product photo are uploaded once and reused across every
shoot, and reusing the same id is what holds identity steady across sessions.

## Reference order — and the hard cap of 4

```
referenceAssetIds = [
  character_hero_assetId,   # position 1: identity anchor
  product_assetId,          # position 2: product context
  style_ref_1_assetId,      # positions 3-4: style/vibe
  style_ref_2_assetId,
]
```

**A generation may cite up to 14 references on `nano-banana-pro`** (spec 2.7.0). Order is
preserved and the first is the strongest signal, so the character hero always goes first — and
the discipline survives the bigger cap: hero, product, and at most **two** style references.
More style refs dilute the hero.

This is a tighter budget than this workflow used to assume — and it points the same direction
the failure table at the bottom already does: *"character face doesn't match → too many style
references diluting identity → reduce style refs to 2."* The cap enforces the fix. If a style
needs more than two images to communicate, put the rest into words in the prompt.

## Prompt formula

The prompt must fight the model's tendency toward polished, studio-quality output. UGC works because it feels raw and real.

### Structure

```
[Camera hardware] + [Framing] + [Character description] + [Action with product] + [Expression] + [Outfit] + [Setting/background] + [Imperfection block] + [Negative cues]
```

### The imperfection block (CRITICAL)

This is what separates convincing UGC from "AI influencer photo." Always include at least 4-5 of these:

- `slight motion blur on hair strands`
- `slightly overexposed highlights on forehead and nose`
- `visible image grain and noise`
- `iPhone front camera wide-angle lens distortion on the extended arm`
- `slightly off-center framing, tilted a few degrees`
- `washed out flat color grading`
- `soft focus — nothing is tack sharp`
- `uneven ambient indoor lighting with one side of face slightly in shadow`
- `caught mid-blink or mid-word, not a perfect expression`

### Skin realism block (CRITICAL — always include)

AI models default to airbrushed, flawless skin which instantly reads as fake. Always describe **subtle, natural skin** in the character description. Pick 3-4 of these cues based on the character:

- `natural skin with visible pores`
- `slight unevenness in skin tone`
- `minor undereye shadows`
- `a hint of shine on the nose and forehead from natural oils`
- `slight pinkness on cheeks and nose` (works well for fair skin)
- `minor skin texture variation`
- `faint undereye shadows`
- `the kind of skin you see on a real person's unfiltered front camera`

**Do NOT use:** acne, pimples, breakouts, blemishes, redness, or anything that sounds like a skin condition. The goal is "real person, not retouched" — not "person with skin problems."

Place these cues **inline with the character description**, not in the imperfection block. Example: `"...warm tan skin with visible pores, slight unevenness in skin tone, minor undereye shadows, a hint of shine on the nose and forehead from natural oils..."`

### Negative cues (always include)

```
No retouching, no beauty filter, no studio lighting, not a professional photo, not overly polished, not perfectly composed, not tack sharp. No airbrushed skin, no flawless complexion.
```

### Example prompt (tested and approved)

```
Raw iPhone front-camera selfie video frame grab. A 25-year-old mixed race
woman with voluminous curly honey-brown hair, warm tan skin with visible
pores, slight unevenness in skin tone, minor undereye shadows, a hint of
shine on the nose and forehead from natural oils — beauty mark on right
cheek, green eyes. She is on her couch holding up a tall purple and gold
[BRAND] soda can, talking mid-sentence to camera with a candid
unposed expression — mouth slightly open, caught between words, not
smiling perfectly.

Casual oversized beige hoodie. Cozy messy apartment background —
houseplants, throw pillows, warm lamp glow — slightly out of focus.

CRITICAL STYLE: This must look like an unedited frame pulled from a real
iPhone selfie video, NOT a professional photo. Include these imperfections:
slight motion blur on hair strands, slightly overexposed highlights on
forehead and nose, visible image grain and noise, iPhone front camera
wide-angle lens distortion on the arm holding the phone, slightly
off-center framing tilted a few degrees, washed out flat color grading,
soft focus — nothing is tack sharp, uneven ambient indoor lighting with
one side of face slightly in shadow. No retouching, no beauty filter,
no studio lighting, no airbrushed skin, no flawless complexion. The image
should feel raw, unpolished, and authentically amateur.
```

## Step-by-step flow

### Step 1: Gather inputs

1. **Character:** Ask which influencer (by name). Load their `01-hero-front.jpg`.
2. **Product:** Ask which product or check `references/products/`. If multiple, ask user to pick.
3. **Style:** Default to `references/aesthetics/ugc-selfie/` for UGC. If other style folders exist, ask user which vibe. Load 3 images from the chosen style folder (pick the most varied ones if more than 3 exist).
4. **Scene:** Ask for the scene/setting (bedroom, car, kitchen, outdoors, etc.) and outfit. If the user doesn't specify, pick a natural casual setting.

### Step 2: Upload the references (once)

Upload via `POST /v1/uploads` and keep each `assetId`:
- 1 character hero
- 1 product photo
- 2 style references

Total: exactly **4** `referenceAssetIds` per call — the hard cap.

Reuse ids you already have. The character hero and product photo almost certainly have
`assetId`s from an earlier run; re-uploading them produces new ids and loses the anchor.

### Step 3: Compose the prompt

1. Start with `"Raw iPhone front-camera selfie video frame grab."`
2. Describe the character using their key visual traits from the character sheet folder name (hair, eyes, skin, build, distinguishing features).
3. **Add skin realism cues inline** with the character description — pick 3-4 from the skin realism block above (e.g., "visible pores, slight unevenness in skin tone, minor undereye shadows, hint of shine from natural oils"). This is non-negotiable.
4. Describe the action with the product — holding it up, drinking it, showing it to camera, etc.
5. Describe a candid mid-speech expression — NOT a perfect smile.
6. Specify the outfit (casual, contextual to the scene).
7. Describe the background/setting — make it lived-in and slightly messy.
8. **Add the full imperfection block** — this is non-negotiable. Without it, the output will look too polished.
9. End with negative cues.

### Step 4: Generate

**Price it first.** `POST /v1/estimates` with
`{"kind":"image","model":"nano-banana-pro","prompt":"…","numImages":3}` — free, and the only
legitimate source of a price. Show `credits` against the user's `balance` and get an explicit
yes. Every variation is charged.

Then call `POST /v1/images` with:
- `model`: `nano-banana-pro`
- `prompt`: the composed prompt
- `aspectRatio`: `9:16` (it defaults to `1:1` — always set it)
- `referenceAssetIds`: the 4 ids from Step 2
- `numImages`: `3`
- `productId` (optional — organizational only)

Default to **3 variations** so the user can compare. `numImages` does this in **one call** —
do not fire three separate requests. Same price, one third of the calls, and it leaves your
concurrency slots free.

The call usually returns the images: it blocks for the render (typically 60–90 seconds) and returns all
three images in `images[]`, with `creditsCharged` for the whole call.

### Step 5: Present and iterate

1. Download all variations.
2. **Open them for the user** using `open <path>` (macOS).
3. QA each for anatomy issues (hands holding the product are the most common problem area).
4. Present as a numbered list.
5. Ask user which they prefer, or if they want adjustments.

## Scene suggestions

When the user doesn't specify a scene, rotate through these for variety:

| Scene | Background cues | Outfit suggestion |
|-------|----------------|-------------------|
| **Living room couch** | Throw pillows, houseplants, warm lamp, slightly messy | Oversized hoodie or loungewear |
| **Bedroom** | Bed with rumpled sheets, nightstand, fairy lights | Tank top, casual tee |
| **Car** | Leather seats, sunroof visible, buildings through window | Sweater, jacket |
| **Kitchen** | Counter, coffee mug, morning light through window | Robe, casual tee |
| **Bathroom mirror** | Mirror selfie, bathroom counter, towels | Getting-ready outfit |
| **Outdoor cafe** | Table, coffee cup, street in background | Casual date outfit |
| **Desk/office** | Laptop, notebook, desk lamp | Work-from-home casual |

## Style folder system

Style references live in `references/aesthetics/{style}/`. Each folder should contain 3-5 images that define the visual language.

### Available styles (add more by creating new folders with reference images)

| Folder | Vibe | When to use |
|--------|------|-------------|
| `ugc-selfie/` | iPhone selfie, casual, authentic, imperfect | Product reviews, "OMG you guys" moments, talking to camera |
| `cinematic/` | Moody lighting, shallow DOF, film grain | Brand storytelling, premium product launches |
| `lifestyle/` | Outdoor, natural light, aspirational but real | Wellness, fitness, food & drink brands |
| `editorial/` | High contrast, fashion magazine, posed | Fashion, beauty, luxury brands |

To add a new style: create the folder, drop in 3-5 reference images, and the agent will automatically use them when you ask for that style.

## Cost

There is no cost table here, deliberately. Every price comes from a live `POST /v1/estimates`
in the current session (see Step 4), shown to the user and approved before anything generates.
`numImages` multiplies it, and QA retries are charged on top — there are no free re-rolls.
Report the real total from `creditsCharged` when you present results.

## Common issues and fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Image looks too polished/professional | Missing imperfection block | Add ALL imperfection cues — don't skip any |
| Character face doesn't match | Too many style references diluting identity | Reduce style refs to 2, keep character hero first |
| Product is unrecognizable | Text on product garbled (common AI limitation) | Describe the product visually in the prompt (color, shape, size) rather than relying on text |
| Hands look wrong | AI hand generation is imperfect | Add "naturally gripping the can/bottle, anatomically correct hand with five fingers" to prompt; regenerate if needed |
| Background too clean | Default AI behavior | Explicitly describe mess: "cluttered coffee table, stacked books, charging cable visible" |

## Combining with video

Once the user approves a UGC still, it can start a video.

### Seedance + `startImageAssetId`

**The video literally starts from the approved image** — face, pose, scene and product placement
are preserved from frame one. This is the correct path for animating UGC stills.

1. Upload the approved still via `POST /v1/uploads` → keep the `assetId`.
2. `POST /v1/videos` with a Seedance model, `startImageAssetId: <assetId>`, and the dialogue in `prompt`. Note `startImageAssetId` and `referenceAssetIds` are **separate modes** — sending both is a `400`, not a merge.
3. **Take the `720p` default and move on.** `seedance-2.0` *does* have a `resolution` field (`480p`, `720p`, `1080p`, `4k`, default `720p` — verified live 2026-08-04; this step used to say the field did not exist, which was true of an older deployment), but there is still nothing to ask the user about on a UGC selfie: it ships to Reels and TikTok, which re-encode anyway, and `1080p`/`4k` cost ≈2.5x/≈5x the base for a difference the feed discards. `seedance-2.0-mini` takes `resolution` only where `GET /v1/models` lists more than one tier for it (API 2.34.0 on); leave it at the default here.
4. Video is **asynchronous**, unlike images: `202` + `jobId` → poll `GET /v1/generations/{jobId}` for a **terminal** status → `…/watch` for the download. The `novoads-api` skill's SKILL.md owns that sequence, the spoken-line approval gate, and its own cost gate.
5. **Human motion cues (CRITICAL):** Always include at least 3-4 natural movement cues in the prompt. Without these, the video will look like a frozen mannequin staring at camera. Pick from:
   - Eye behavior: "briefly breaks eye contact, glances down at the product, then looks back at camera"
   - Head/face: "slight head tilts while talking, nods along with own words, raises eyebrows for emphasis"
   - Body: "shifts weight, leans toward camera for emphasis, adjusts grip on the product"
   - Scene motion: "takes a small step, turns the product to show another angle"
6. **ALWAYS end prompt with:** `"No subtitles, no captions, no text overlays."`
7. See [seedance-2-ugc.md](seedance-2-ugc.md) for the full UGC video prompting formula and cue library.

### Veo 3.1 and Sora 2

Not on this API. Their prompt libraries sit in this folder for if and when they land. Say so
plainly rather than routing a user toward an endpoint that does not exist.
