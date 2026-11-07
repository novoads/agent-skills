# Premium product reveal — Seedance 2.0

**Use when:** you need a dramatic, dark-background product launch video — a hero announcement, a new model reveal, "introducing the next generation". No person on screen. The product is the star, floating in black void with dramatic lighting, animated text reveals, and premium material close-ups.

**Model guide:** read [seedance-2.md](seedance-2.md) first for the request fields, the grid, and the platform rules.

**Mode:** `referenceAssetIds` with the product photo as `@Image1`. Not `startImageAssetId` — this style opens on darkness and lets the product emerge, so a flat product photo as literal frame 1 fights the whole premise. The two fields are mutually exclusive anyway.

## What defines this style

This style strips away everything except the product and dramatic text. The entire frame is black void — no environment, no lifestyle, no person. The product emerges from darkness through lighting that catches metallic surfaces, glass edges, textured materials. Text builds phrase by phrase in clean, bold typography, creating a narrative rhythm without any spoken dialogue.

The power comes from **restraint and revelation**. Each beat reveals slightly more — a new angle, a new detail, a new text line that reframes what you are looking at. The pacing is deliberate and slow. Where UGC feels spontaneous and fast, this feels inevitable and weighty.

## Two things to know before you write a word

**1. Seedance preserves logos and destroys printed text.** A reveal whose final frame is a wordmark is asking for exactly the thing the model is worst at. Keep the reference photo sharp, paste the label-hold clause in, and check the render: the estimate's `label_without_hold` warning is a reminder at best, and nothing refuses the call.

**2. There is no person in this style, by design.** Do not invent an actor. The formula below is complete without one, and the parts of the general Seedance guidance that assume a human on camera — the actor descriptor, the spoken line — do not apply on this route. Judgement about which advice fits which route is yours; this is the standard case.

The worked example below is priced live 2026-08-03. Price your own before submitting: the estimate is the only source of a number, and what it says about the prompt in `warnings` is advice.

## The structure

```
 1. VOID STAGE        — the black backdrop and lighting setup
 2. PRODUCT HERO      — what the product looks like and how it's lit
 3. TEXT NARRATIVE     — the story told through animated typography
 4. REVEAL SEQUENCE   — the choreography of product angles and details
 5. VARIANT SHOWCASE  — size/color/model comparisons (optional)
 6. BRAND CLOSE       — final product name + series branding card
```

---

## Layer-by-layer formula

### Layer 1: Void stage

The background is pure black — not dark grey, not moody shadows, but true black void. The product appears to float in nothingness. Lighting is the only thing that gives the scene dimension.

**Pattern:**
```
{{DURATION}} premium product reveal video. Pure black background, {{LIGHTING_STYLE}}, {{LIGHTING_DIRECTION}}.
```

**Variables:**

| Variable | Options | Notes |
|---|---|---|
| `DURATION` | 15 seconds | The `seedance-2.0` maximum, and the right choice for this style. Remember `durationSeconds` defaults to **5** — set it. |
| `LIGHTING_STYLE` | dramatic studio rim lighting, soft gradient spotlight, hard directional key light, warm amber accent lighting, cool silver edge lighting | Rim lighting is the default — it outlines the product against the void |
| `LIGHTING_DIRECTION` | light coming from above and behind the product, side-lit from the left with a subtle fill on the right, backlit with a soft halo around the edges, overhead spot with sharp falloff | Specifies WHERE light hits the product |

**Key rule:** never describe a visible light source (no lamps, no windows, no softboxes in frame). The light simply exists — the source is invisible. That is what maintains the floating-in-void illusion.

---

### Layer 2: Product hero

Describe the product's physical form, material, and the specific way light interacts with its surfaces — then lock the label.

**Pattern:**
```
A {{PRODUCT_DESCRIPTION}} — {{MATERIAL_SURFACE}}, {{LIGHT_INTERACTION}}.
The product @Image1 is centered in frame, {{SCALE_CUE}}.
The product label remains perfectly sharp and identical to the reference image
with its text unchanged and fully legible.
```

**Variables:**

| Variable | Options | Notes |
|---|---|---|
| `PRODUCT_DESCRIPTION` | brushed stainless steel fire pit, matte black water bottle, polished aluminum speaker, frosted glass perfume bottle | Name the real product and its primary material. Never a blank or unbranded stand-in — ask for the photo instead. |
| `MATERIAL_SURFACE` | brushed metal with fine grain texture, polished surface with mirror reflections, matte finish absorbing light softly, textured rubber grip with subtle sheen | How the surface LOOKS under dramatic lighting |
| `LIGHT_INTERACTION` | rim light catching the edges in a thin white line, reflections sliding across the curved surface, light pooling in the engraved logo, soft highlights moving across the brushed grain | How light BEHAVES on this specific material |
| `SCALE_CUE` | filling the lower third of the frame, small enough to see its full form with black space around it, large and imposing in frame | Helps the model size the product correctly |

**Material–light pairing bank:**

| Material | Best lighting interaction | Example |
|---|---|---|
| Brushed metal | Rim light catching edges, grain visible | stainless steel fire pit, aluminum laptop |
| Polished / chrome | Sharp reflections sliding across surface | sunglasses, chrome hardware |
| Matte plastic / rubber | Soft diffused highlights, no hard reflections | phone case, matte water bottle |
| Glass / clear | Light refracting through, caustic patterns | perfume bottle, glass jar |
| Fabric / textile | Subtle texture under raking light, soft shadows | shoe upper, bag material |

---

### Layer 3: Text narrative

The text tells the story. It builds phrase by phrase — each line appearing in sequence, creating a narrative rhythm.

**Pattern:**
```
Bold white text appears: "{{LINE_1}}" — {{LINE_1_TIMING}}.
{{LINE_2_TRANSITION}}: "{{LINE_2}}" — {{LINE_2_TIMING}}.
{{LINE_3_TRANSITION}}: "{{LINE_3}}" — {{LINE_3_TIMING}}.
```

Keep it as prose with quoted strings, the way it is written above. A run of `Label: value, Label: value` pairs is the shape that comes back **rendered as literal text on screen** — which on this style, where text is already on screen by design, produces a frame with the prompt's own scaffolding baked into it.

**Text reveal timing options:**

| Timing | Description | Use when |
|---|---|---|
| `fades in over 1 second` | Smooth, premium feel | Opening line, brand name |
| `snaps on screen` | Impact, emphasis | Key claim, product name reveal |
| `types on letter by letter` | Building tension | Feature descriptions |
| `slides in from left/right/below` | Motion energy | Secondary info lines |
| `builds word by word` | Dramatic pacing | Multi-word claims, taglines |

**Text narrative structures:**

| Structure | Line 1 | Line 2 | Line 3 | Best for |
|---|---|---|---|---|
| **Introduction** | "INTRODUCING" | Product category claim | Product name | New product launches |
| **Superlative** | Bold claim ("Our most X ever") | Proof point | Product name | Upgrades, next-gen |
| **Question** | "What if X?" | Answer / feature | Product name reveal | Innovation stories |
| **Feature stack** | Feature 1 | Feature 2 | Feature 3 + product name | Feature-heavy products |

**Key rules:**
- Max 3 text lines in 15 seconds — more feels rushed
- Each line under 8 words — this is a billboard, not a paragraph
- Text appears CENTER FRAME or upper third — never at the very bottom
- Every word of on-screen text is text Seedance has to draw. Keep the strings short, and expect to check them in QA the way you check a label.

---

### Layer 4: Reveal sequence

The choreography — how the product moves and how the camera moves around it. In 15 seconds you get 2–3 distinct product views.

**Pattern:**
```
{{OPENING_REVEAL}}. {{CAMERA_MOVE_1}}.
{{TRANSITION}} — {{CAMERA_MOVE_2}}, {{DETAIL_FOCUS}}.
{{FINAL_POSITION}}.
```

**Opening reveal styles:**

| Style | Description | Best for |
|---|---|---|
| **Rise from below** | Product slowly rises into frame from bottom | Height-oriented products (bottles, fire pits) |
| **Fade from dark** | Lighting gradually illuminates a product already in frame | Any product, most dramatic |
| **Rotate in** | Product spins into position from off-angle | Products with interesting 3D form |
| **Zoom out** | Starts on extreme close-up detail, pulls back to reveal full product | Products with distinctive textures |

**Camera movement bank:**

| Move | Description | Effect |
|---|---|---|
| `slow 360 rotation around the product` | Product stays center, camera orbits | Shows all sides, premium feel |
| `gentle push-in from medium to close-up` | Camera slowly approaches | Builds intimacy with product |
| `overhead top-down view descending` | Bird's eye, moving down | Products with an interesting top profile |
| `slow pan across surface detail` | Camera slides laterally across texture | Highlights material quality |

**Key rule:** every camera movement is SLOW — 3 to 5 seconds minimum. Use `slowly`, `deliberately`, `gracefully`. And keep one move per beat: a second move chained onto the first with `then` renders as a smear, which on a slow reveal is the most visible defect there is.

---

### Layer 5: Variant showcase (optional)

If the product comes in multiple sizes, colors or models, show them in comparison.

**Pattern:**
```
{{COMPARISON_LAYOUT}} — {{ITEM_1_APPEARS}}, {{ITEM_2_APPEARS}}, {{ITEM_3_APPEARS}}.
{{SIZE_LABELS}} appear below each variant.
```

**Comparison layouts:**

| Layout | Description | Best for |
|---|---|---|
| **Top-down lineup** | Products viewed from above, left to right | Size variants |
| **Side-by-side** | Products standing next to each other, camera at eye level | Height / form comparison |
| **Single swap** | One product transitions into another | Color variants, generations |

A lineup is also the case for a second reference: pass the second colorway's photo as `@Image2` and name it in the sentence, rather than describing a color the model has to invent.

---

### Layer 6: Brand close

The final 2–3 seconds. Product name, series name, brand lockup on screen.

**Pattern:**
```
Final frame: {{BRAND_LOCKUP_POSITION}}. Text reads "{{PRODUCT_FULL_NAME}}" in {{TYPOGRAPHY_STYLE}}.
The product is {{FINAL_HERO_ANGLE}}.
```

---

## Beat structure (15-second format)

| Beat | Timing | What happens | Text |
|---|---|---|---|
| **1: Tease** | 0–4s | Product partially visible or emerging from darkness. First text line. Slow, dramatic. | "INTRODUCING" or bold claim |
| **2: Reveal** | 4–10s | Full product visible, camera moves around it. Key feature or claim. The hero moment. | Product category + key differentiator |
| **3: Lineup + close** | 10–15s | Variant comparison (if applicable) or final hero angle. Product name and brand lockup. | Full product name + series branding |

**Pacing rules:**
- No spoken dialogue. Say so in the prompt — `a silent product film with no spoken dialogue` — and the music and SFX carry the energy.
- Camera movements are slow and deliberate, never jerky.
- Text transitions drive the rhythm. Each new line is a new beat of energy.
- At least 1 second of pure black between the last text and the end.

---

## Multi-clip strategy

This style maps naturally to a **3-clip product launch series**:

| Clip | Focus | Text narrative | Product view |
|---|---|---|---|
| **A: The announcement** | "Something new is here" | INTRODUCING → bold claim → product name | Emerging from void, hero angle, brand close |
| **B: The features** | "Here's what makes it special" | Feature 1 → Feature 2 → Feature 3 | Close-ups on each feature detail, texture shots |
| **C: The lineup** | "Available in X sizes/colors" | "In all-new sizes" or "X colors" | Side-by-side comparison, variant reveal |

Each clip stands alone as a 15-second ad; together they tell a launch story. Three clips is three separate generations at three separate charges — price the set at `POST /v1/estimates` and show the total before submitting any of them. **Upload the product photo once**: the same `assetId` carries all three, and re-uploading it would hand the model a different reference for what is meant to be one product.

---

## Technical specs

### Lighting
- **Primary:** rim / edge lighting from behind — a thin white outline around the product
- **Secondary:** soft fill from one side to show surface detail without flattening
- **No visible light source** — light appears to come from nowhere
- **Highlight behavior:** highlights slide slowly across surfaces as the camera or product moves

### Color palette
- **Background:** pure black
- **Product:** true-to-life colors with slightly boosted contrast
- **Text:** white, or a single brand accent color
- **No color grading** beyond high contrast

### Camera
- Ultra-clean, sharp focus — the opposite of UGC
- No grain, no noise, no imperfections — everything deliberate
- Shallow depth of field on close-ups
- Smooth motion — dolly and track feel, no handheld shake

### Frame
- **`aspectRatio: "9:16"`** for social — product centered with generous black space above and below. The API default is `16:9`, so set it, and restate it at the end of the prompt text as `Vertical 9:16.`
- Text must be readable on mobile — large, bold, high-contrast
- **`resolution` does exist on `seedance-2.0`** — `480p`, `720p`, `1080p`, `4k`, default `720p` (verified live 2026-08-04; the older line here denying it described a previous deployment). Default output measured 720x1280 at `9:16`.
- **A premium reveal is the one style with a real reason to go above `720p`** — it is a glossy hero film, often the client-facing deliverable, and the tier is visible on a large screen in a way a talking-head UGC clip is not. It is still a **spend** decision: `1080p` is ≈2x the `720p` base and `4k` ≈5x. Raise it only with the user's say-so, on a fresh `POST /v1/estimates` for that exact cell, and never quote a credit number from those ratios. Downward, `480p` is **≈two-thirds** of the `720p` base (the older line here said it cost the same and bought nothing, which stopped being true with the 2026-08-07 reprice) — not a tier to ship a premium reveal on, but the honest one for a rehearsal pass that only has to prove the prompt works.

---

### Audio: send `audioEnabled: false`, and keep saying it in the prose

This style has no dialogue, so **send `"audioEnabled": false` on the generation call.** The field is live on `seedance-2.0` and `seedance-2.0-mini` (default `true`) and renders the clip silent. Without it you are paying for a speech track on a film that has nobody in it — and worse, Seedance can invent a narrator over a product reveal that was never meant to have one.

**It does not change the price**, which is why `POST /v1/estimates` refuses the field. Price the render without it, generate with it.

**Do not drop the prose silence clause when you set the flag — keep both.** They do different jobs:

| | What it does |
|---|---|
| `audioEnabled: false` | Mutes the render. A guarantee, at the field level |
| `a silent product film with no spoken dialogue` in the prompt | Stops the model *staging* a talking shot in the first place — an actor mouthing nothing, billed in full |

The flag cannot un-stage a shot the prompt asked for. If the render carries music or SFX you *want*, leave `audioEnabled` at its default and mute in post instead.

---

## Complete template

```
15 seconds premium product reveal video. Pure black background,
{{LIGHTING_STYLE}}, {{LIGHTING_DIRECTION}}.

A {{PRODUCT_DESCRIPTION}} — {{MATERIAL_SURFACE}},
{{LIGHT_INTERACTION}}. The product @Image1 is centered in frame,
{{SCALE_CUE}}.

[00:00] {{OPENING_REVEAL}}. Bold white text fades in: "{{TEXT_LINE_1}}"
— centered above the product.

[00:04] {{CAMERA_MOVE_1}}, revealing {{DETAIL_1}}.
Text transitions to: "{{TEXT_LINE_2}}" — {{LINE_2_TIMING}}.

[00:09] {{CAMERA_MOVE_2}}. {{VARIANT_OR_HERO_ACTION}}.
Text: "{{TEXT_LINE_3}}" — {{LINE_3_TIMING}}.

[00:13] Final frame: {{BRAND_LOCKUP_POSITION}}.
Text reads "{{PRODUCT_FULL_NAME}}" in {{TYPOGRAPHY_STYLE}}.
The product is {{FINAL_HERO_ANGLE}}.

The camera moves slowly and deliberately throughout — every movement
is smooth, no quick cuts or handheld shake. The lighting is dramatic,
with rim light catching the product edges against the pure black void.
The feel is premium, authoritative, restrained — a product announcement
that commands attention through simplicity.
```

---

## Worked example: premium water bottle launch

The fork's example, restored verbatim, and priced live 2026-08-03. Note what it leaves out and add both before you send it: a label-hold clause, and the ratio line.

```
15 seconds premium product reveal video. Pure black background,
dramatic studio rim lighting, light coming from above and behind
the product.

A double-walled insulated water bottle in matte midnight blue —
smooth matte finish absorbing light softly, rim light catching the
brushed metal lid in a thin white line. The product @Image1 is
centered in frame, filling the lower third of the frame.

[00:00] The bottle slowly rises into frame from below, rim light
illuminating its edges against the void. Bold white text fades in:
"ENGINEERED TO KEEP UP" — centered above the bottle.

[00:04] Slow 360 rotation around the bottle, revealing the textured
grip band and laser-etched logo. Text snaps on screen: "48-Hour
Ice Retention." — bold, centered.

[00:09] Camera pushes in to a close-up of the lid mechanism, showing
the one-hand flip action in slow motion. Text slides in from below:
"The All-New Summit Series" — mixed weight typography.

[00:13] Final frame: brand logo top-center with product name below it.
Text reads "SUMMIT HYDRATION SERIES" in bold sans-serif white text.
The bottle is shown at a slight 3/4 angle with rim lighting,
slowly rotating to a stop.

The camera moves slowly and deliberately throughout — every movement
is smooth, no quick cuts or handheld shake. The lighting is dramatic,
with rim light catching the metal lid and bottle edges against the
pure black void. The feel is premium, authoritative, restrained — a
product announcement that commands attention through simplicity.
```

The call:

```json
{
  "model": "seedance-2.0",
  "idempotencyKey": "<a new one per render>",
  "prompt": "<the prompt above>",
  "durationSeconds": 15,
  "aspectRatio": "9:16",
  "language": "en",
  "audioEnabled": false,
  "referenceAssetIds": ["<assetId from POST /v1/uploads>"]
}
```

Price it first. The estimate takes only what its arm lists, and `aspectRatio` or `referenceAssetIds` there is a `400`:

```json
{
  "kind": "video",
  "model": "seedance-2.0",
  "durationSeconds": 15,
  "language": "en",
  "prompt": "<the prompt above>"
}
```

No dialogue gate applies to this style — there is nothing spoken to approve. The cost gate still does.

---

## Adaptation checklist

- [ ] **15 seconds** — `durationSeconds: 15` set explicitly (the default is 5)
- [ ] **`aspectRatio` set** — `9:16` for social (the default is `16:9`), and restated as `Vertical 9:16.` at the end of the prompt
- [ ] **Pure black background** — void stage, no environment
- [ ] **Product is the only subject** — real brand, named, described in full (label, colors, material, shape)
- [ ] **Label hold clause present** — this is the style where printed text matters most
- [ ] **Silence stated** — `a silent product film with no spoken dialogue`
- [ ] **`audioEnabled: false` sent** — the flag as well as the sentence; the default is `true`
- [ ] **Max 3 text lines** — each under 8 words, reveal timing specified
- [ ] **Reveal sequence** — one opening style, 2–3 camera moves, all SLOW, none chained with `then`
- [ ] **Brand close** — full product name, typography style, final hero angle
- [ ] **Lighting** — rim / edge dominant, no visible light source
- [ ] **Timestamps** — 4 blocks covering the full 15 seconds
- [ ] **Length** — around 270 words for this 4-timestamp shape; every beat specified, nothing padded
- [ ] **`@Image1`** — product photo uploaded once, passed in `referenceAssetIds`, never alongside `startImageAssetId`
- [ ] **No forbidden words** — `dramatic` or `premium` instead of `cinematic`; no `professional`, `stunning`, `8k`, `studio`, `perfect`
- [ ] **Priced live** — `POST /v1/estimates` this session, the number shown to the user, user said yes
