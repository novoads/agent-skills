# Product hero — Seedance 2.0

**Use when:** you need a dramatic, no-person product showcase where the product itself is the star. Shot like a movie poster — moody lighting, a single deep backdrop color, and elemental interaction (water splashing, ice, mist, dust, sparks, smoke). Best for beverages, supplements, cans, bottles, cosmetics, tech gadgets, or anything with strong packaging.

**Model guide:** read [seedance-2.md](seedance-2.md) first for the request fields, the grid, and the platform rules.

**Mode:** `referenceAssetIds` with the product photo as `@Image1`. Not `startImageAssetId` — the opening shot is a macro detail inside a lit set, not the flat product photo. The two fields are mutually exclusive; sending both is a `400`.

## What defines this style

There is no person in this video. The product is the only subject, and the entire visual language exists to make it look larger than life.

1. **The product is the hero.** Every shot is framed around it — extreme close-ups of the label, dramatic angles looking up at it, wide hero compositions with multiple variants. The camera treats the product the way a portrait photographer treats a face.

2. **Elemental interaction creates the action.** With no person doing things, the energy comes from the environment — water splashing against the can, rain on the surface, condensation beading, ice cracking, mist swirling. The product stays mostly static while the world around it moves.

3. **Dramatic lighting and color set the mood.** The background is a single deep color (blue, black, dark teal, amber), the product is spot-lit, contrast is high. Shadows and highlights give it weight and presence.

## Two things to know before you write a word

**1. There is no person in this style, by design.** Do not invent an actor to satisfy the general Seedance guidance — the actor descriptor and the spoken line are written for routes with a human on camera, and this is not one. Same call as the premium reveal and the Pixar routes.

**2. Paste the label-hold clause in every time.** This style lives on macro shots of packaging, and Seedance preserves logos while destroying printed text. Nothing on the API will remind you:

> the product label remains perfectly sharp and identical to the reference image with its text unchanged and fully legible

The worked example below was priced live 2026-08-02 with the clause and the ratio line in place. Price your own before submitting.

## The structure

```
 1. FORMAT HEADER        — duration, visual style, camera type
 2. PRODUCT              — what it looks like, how it's positioned
 3. ENVIRONMENT          — backdrop color, surface, elemental effects
 4. SHOT SEQUENCE        — the visual beats: angles, movements, compositions
 5. TEXT OVERLAYS        — tagline, CTA, feature callouts
 6. TECHNICAL QUALITY    — lighting, camera movement, color grade, audio
```

---

## Layer-by-layer formula

### Layer 1: Format header

**Pattern:**
```
15 seconds {{CONTENT_TYPE}} video, {{CAMERA_STYLE}}, {{MOOD_DESCRIPTOR}},
silent b-roll with no spoken dialogue.
```

| Variable | Options | Notes |
|---|---|---|
| `CONTENT_TYPE` | product hero, beverage commercial, premium product showcase, brand film | Match the product category |
| `CAMERA_STYLE` | slow-motion macro photography, dramatic product cinematography, high-speed product photography | The shooting approach |
| `MOOD_DESCRIPTOR` | dark and dramatic, moody and premium, bold and energetic, clean and minimal | The overall visual tone |

The silence clause is not decoration. Seedance renders audio from the prompt, so a product film that never says it is silent can come back with an invented voice over it — or, worse, staged as a talking shot with nobody in frame to do the talking.

**Send `"audioEnabled": false` as well.** The field is live on `seedance-2.0` and `seedance-2.0-mini` and defaults to `true`, so a call that omits it generates a speech track for a film with nobody in it. It does not change the price — `POST /v1/estimates` refuses the field for exactly that reason — so the flag is free insurance.

**Keep both.** The flag mutes the render; the prose clause stops the model staging a talking shot in the first place. Neither replaces the other, and the flag cannot un-stage a shot the prompt asked for.

**One caveat specific to this style:** `audioEnabled: false` mutes *everything*, including the foley and the impact SFX that a splash or spark shot renders. If you want Seedance's own sound design and only need the dialogue gone, leave the flag at its default, keep the prose clause, and check the result with the video QA step in `SKILL.md` §7 — the transcript tells you whether a voice crept in.

---

### Layer 2: Product

**Pattern:**
```
The @Image1 ({{PRODUCT_DESCRIPTION}}) — {{SURFACE_DETAILS}}, {{CONDITION_DETAILS}}.
The product label remains perfectly sharp and identical to the reference image
with its text unchanged and fully legible.
```

| Variable | How to fill | Key principle |
|---|---|---|
| `PRODUCT_DESCRIPTION` | Real product name + physical description: shape, size, colors, label design, material | Be very specific — this is the only thing on screen. Never an unbranded or blank-label stand-in; ask for the photo. |
| `SURFACE_DETAILS` | condensation droplets on the surface, frost forming on the edges, matte finish absorbing the light | Small details that make it feel real and tactile |
| `CONDITION_DETAILS` | ice cold, freshly opened, sealed and pristine, slightly wet from condensation | The product's "state" |

---

### Layer 3: Environment

**Pattern:**
```
Set against a {{BACKDROP}} on a {{SURFACE}}. {{ELEMENTAL_EFFECT_1}}, {{ELEMENTAL_EFFECT_2}}.
```

| Variable | Options | Notes |
|---|---|---|
| `BACKDROP` | deep blue gradient background, matte black void, dark teal-to-black gradient, warm amber glow, ice-white backdrop | One dominant color, often a gradient |
| `SURFACE` | dark reflective surface, wet black marble, sheet of ice, matte black platform, mirror-like wet surface | Reflective surfaces double the product's presence |
| `ELEMENTAL_EFFECT_1` | water splashing dramatically around the product, rain falling onto the can, mist swirling at the base, ice cracking and shifting | The PRIMARY motion |
| `ELEMENTAL_EFFECT_2` | water droplets suspended in mid-air, light refracting through droplets, surface ripples spreading outward, frost crystals forming | The SECONDARY detail |

**Element bank by product type:**

| Product type | Primary element | Secondary element |
|---|---|---|
| **Beverage / can / bottle** | water splash, rain, pour into glass | condensation, ice, droplets frozen in air |
| **Supplement / powder** | powder explosion, dust cloud | particles catching the light, settling |
| **Skincare / cosmetic** | cream swirl, liquid drip, mist | dewy droplets, light refraction |
| **Tech / gadget** | sparks, light trails, electricity | reflections, lens flare, smoke |
| **Food** | steam, sizzle, drip | condensation, crumbs, splatter |

---

### Layer 4: Shot sequence

3–4 shots that escalate in drama, typically moving from tight and tactile to wide and heroic.

**Shot type bank:**

| Shot type | What it shows | Purpose |
|---|---|---|
| **Extreme close-up / macro** | Label detail, surface texture, condensation | Opens the video — texture sells quality |
| **Grab / interaction** | A hand reaching in to grab the product, water displaced | The only human element — just a hand, and it creates scale |
| **Dramatic angle** | Product from below or tilted, rain / effects falling | Makes it feel larger than life |
| **Hero composition** | Product centered, full label visible | The money shot |
| **Slow-motion splash** | Water or element hitting the surface | Pure spectacle |
| **CTA frame** | Hero composition with text | Closing frame — holds 3–4 seconds |

**15-second shot sequence frameworks:**

| Sequence type | Shot 1 (~3s) | Shot 2 (~3s) | Shot 3 (~4s) | Shot 4 (~5s) |
|---|---|---|---|---|
| **Escalating drama** | Macro close-up | Hand grab + splash | Dramatic low angle with rain | Hero comp + tagline |
| **Reveal build** | Blurred product in ice | Focus pulls to sharp label | Splash / pour moment | Multi-variant hero + CTA |
| **Pure spectacle** | Slow-mo splash | Dramatic angle, rain pouring | Cut to second variant | Hero lineup + tagline |

Separate the shots with `Cut to` — never with `then`, `and then` or `followed by`, which read as one continuous action being chained and come back as a smear.

---

### Layer 5: Text overlays

| When | What | Style |
|---|---|---|
| **Mid-video (~8–10s)** | Brand tagline or product claim | Large, bold, centered |
| **End card (~12–15s)** | Where to buy + feature callouts | "Available at [retailer]" + feature badges |

**Write the overlay as a bracketed label**, on its own line, as the template and the worked example
below do:

> `[Text overlay: "MAXIMUM VOLTAGE. ZERO COMPROMISE."]`
> `[End card: "Available everywhere — Zero Sugar | 200mg Caffeine"]`

**Tagline rules:**
- Short, punchy, memorable — 4 to 8 words
- Often a contrast or juxtaposition
- Bold sans-serif or gothic, white or gold on the dark background
- Every word is text the model has to draw, so keep it short and check it in QA the way you check a label

---

### Layer 6: Technical quality

**Pattern:**
```
The lighting is {{LIGHT_SETUP}} — {{LIGHT_QUALITY}}. The image is {{CAMERA_QUALITY}} —
{{CAMERA_DETAILS}}. The color grade is {{COLOR_GRADE}}. The sound is {{AUDIO_TYPE}} —
{{AUDIO_DETAILS}}.
```

**Lighting:** high contrast, dramatic shadows. The product is the brightest thing in frame.

**Camera:** high-end product photography quality. Tack-sharp focus on the label. Slow-motion capture on splash and water. Very smooth movement, no shake.

**Color grade:** deep saturated backdrop with neutral product tones — the product pops against the environment.

**Audio:** a music bed with foley (ice cracking, water splashing, a can tab). No voice, no dialogue — and say so in the header, per layer 1.

---

## Complete template

```
15 seconds {{CONTENT_TYPE}} video, {{CAMERA_STYLE}},
{{MOOD_DESCRIPTOR}}. The @Image1 ({{PRODUCT_DESCRIPTION}}) —
{{SURFACE_DETAILS}}, {{CONDITION_DETAILS}}. Set against a
{{BACKDROP}} on a {{SURFACE}}. {{ELEMENTAL_EFFECT_1}},
{{ELEMENTAL_EFFECT_2}}.

{{SHOT_1_TYPE}} — {{SHOT_1_DESCRIPTION}}.

Cut to {{SHOT_2_TYPE}} — {{SHOT_2_DESCRIPTION}}.

Cut to {{SHOT_3_TYPE}} — {{SHOT_3_DESCRIPTION}}.

{{SHOT_4_TYPE}} — {{SHOT_4_DESCRIPTION}}.
[Text overlay: "{{TAGLINE}}"]
[End card: "{{CTA}}"]

The lighting is {{LIGHT_SETUP}} — {{LIGHT_QUALITY}}.
The image is {{CAMERA_QUALITY}} — {{CAMERA_DETAILS}}.
The color grade is {{COLOR_GRADE}}.
The sound is {{AUDIO_TYPE}} — {{AUDIO_DETAILS}}.
```

---

## Worked example: energy drink can

The fork's example, restored verbatim, and priced live 2026-08-03. Note what it leaves out and add both before you send it: a label-hold clause, and the ratio line.

```
15 seconds product hero video, slow-motion macro photography,
dark and dramatic. The @Image1 (VOLT Energy — tall 16oz matte
black can with neon green lightning bolt logo, silver pull tab,
"ZERO SUGAR / MAX CHARGE" in electric green text on the lower
third) — condensation droplets forming on the matte surface,
ice cold and freshly cracked. Set against a deep black void on
a dark reflective surface. Water splashing dramatically as the
can is set down, neon green light refracting through the
suspended water droplets.

Extreme close-up — the neon green logo fills the frame, water
droplets cling to the matte black surface, one droplet slowly
rolling down past the lightning bolt.

Cut to a hand reaching in from the left, gripping the can and
lifting it — water cascades off the surface in slow motion,
droplets hanging in the air, green light catching each one.

Cut to dramatic low angle — the can tilted slightly toward
camera, rain pouring down onto it from above, water sheeting
off the edges, the pull tab gleaming.

Hero composition — the can centered on the wet reflective
surface, a second variant (white can, red logo) placed behind
it at an angle. Water settling. The reflection doubles them.
[Text overlay: "MAXIMUM VOLTAGE. ZERO COMPROMISE."]
[End card: "Available everywhere — Zero Sugar | 200mg Caffeine"]

The lighting is single spotlight from above with rim light on
edges, deep shadows pooling around the base. The image is
high-end product photography, tack-sharp label, slow-motion
water capture. The color grade is deep black shadows with
electric green highlights bleeding from the logo into the
water. The sound is deep bass building to a drop at the splash
moment, foley crackle of the can tab, water impact, resolving
to a low hum under the end card.
```

The call:

```json
{
  "model": "seedance-2.0",
  "idempotencyKey": "<one per clip>",
  "prompt": "<the prompt above>",
  "durationSeconds": 15,
  "aspectRatio": "9:16",
  "language": "en",
  "referenceAssetIds": ["<assetId from POST /v1/uploads>"]
}
```

The second colorway in the closing shot is a good second reference: pass its photo as `@Image2` rather than describing a variant the model has to invent. Two references, one call, same price — references do not move the cost, duration does.

Price it first. The estimate takes the pricing fields only:

```json
{
  "kind": "video",
  "model": "seedance-2.0",
  "durationSeconds": 15,
  "language": "en",
  "prompt": "<the prompt above>"
}
```

Nothing is spoken here, so gate 1 does not apply. Gate 2 always does.

---

## Adaptation checklist

- [ ] **15 seconds** — `durationSeconds: 15` set explicitly (the default is 5)
- [ ] **`aspectRatio` set** — `9:16` for social (the default is `16:9`), and restated as `Vertical 9:16.` at the end of the prompt
- [ ] **No person in frame** — hands only, and only for a grab shot
- [ ] **Product is the only subject** — real brand, named, described in full
- [ ] **Label hold clause present**
- [ ] **Silence stated** — `silent b-roll with no spoken dialogue` in the header
- [ ] **Elemental interaction specified** — water, ice, mist, smoke, sparks: something MOVES
- [ ] **Backdrop is a single deep color** — not white, not busy
- [ ] **Surface is reflective**
- [ ] **3–4 shots that escalate** — macro → interaction → dramatic angle → hero, separated by `Cut to`, never chained with `then`
- [ ] **Camera movement slow and deliberate**
- [ ] **Tagline written as a bracketed `[Text overlay: "…"]` label**, with `[End card: "…"]` under it
- [ ] **Audio is music + foley, no dialogue** — and decide the flag: `audioEnabled: false` for a fully silent master, or leave it default to keep Seedance's foley (see Layer 1)
- [ ] **Length** — around 330 words for this 4-shot shape; every shot specified, nothing padded
- [ ] **`@Image1`** — product photo uploaded once, passed in `referenceAssetIds`, never alongside `startImageAssetId`
- [ ] **No forbidden words** — no `cinematic`, `professional`, `stunning`, `8k`, `studio`, `perfect`
- [ ] **Priced live** — `POST /v1/estimates` this session, the number shown to the user, user said yes
