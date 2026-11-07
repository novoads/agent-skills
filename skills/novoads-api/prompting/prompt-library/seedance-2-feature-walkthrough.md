# Feature walkthrough — Seedance 2.0

**Use when:** you need a product showcase where the person is actively wearing or using the product and walks the viewer through its features one by one, physically demonstrating each. The vibe is enthusiastic, informative and fast — an influencer who genuinely loves a product speedrunning every reason why.

**Model guide:** read [seedance-2.md](seedance-2.md) first for the request fields, the grid, and the platform rules.

**Mode:** `referenceAssetIds` — `@Image1` the product, `@Image2` the person. Up to 9, images only, resolved by array position. This style almost always ships as a 2–3 clip series, and the person reference is what keeps it the *same* person across clips. Not `startImageAssetId`; the two fields are mutually exclusive and sending both is a `400`.

## What defines this style

This is not a review. There is no skepticism arc, no "I was surprised", no before-and-after. The person loves the product from the first frame and the whole video is a high-energy feature dump — each beat isolates one feature and physically demonstrates it.

1. **Show, don't tell.** Every claim is backed by a physical action. "Hidden pockets" means she is reaching into the pocket on camera. "Stretchy waistband" means she is pulling the elastic. The person never just *talks about* a feature — they *prove it* with their hands.

2. **Density without overwhelm.** Fast talking, a lot of ground, each beat cleanly separated by a jump cut. A 15-second clip covers 1–2 distinct features. For products with more, generate multiple clips that each take a different slice.

3. **First-person embodiment.** The person IS the demo. They are wearing it, using it, living in it while they talk. The camera is close and the framing is personal.

## Three things to know before you write a word

**1. The dialogue is rendered, spoken and lip-synced in this same call.** Whatever sits inside the double quotes is what the actor says out loud in the finished file, and changing it later means paying for the render again. **`SKILL.md` gate 1 applies to every clip in the series** — numbered beats, word count against the duration, `language` stated, explicit yes. Approving the concept is not approving the sentences.

**2. A multi-clip series is where identity breaks, and `@Image2` is the fix.** Seedance re-casts on every cut, let alone between two separate generations. The fork's answer was to repeat the actor's description verbatim in clip B — which helps and does not hold a face. Passing the same person photo as `@Image2` in every clip of the series is what makes it one person. Keep the verbatim tag as well, and never write `the same guy` or `as before`: a back-reference resolves to nobody.

**3. Every clip is its own charge.** A 3-clip series is three generations at three prices. Price the whole set at `POST /v1/estimates` and show the total before submitting any of it, and remember that ten generations per organization may be in flight at once. Draft the series on `seedance-2.0-mini` at about a fifth of the price, then re-render the winners — the `assetId`s are durable, so the finals reuse the same uploads.

The Clip A example below is the fork's, restored verbatim, and priced live 2026-08-03. Note
that it states no aspect ratio in the prompt text: the `aspectRatio` field is what binds the
output, and the sentence only steers composition — so add `Vertical 9:16.` when the framing
matters, and send the field either way.

## The structure

```
 1. FORMAT HEADER         — duration, content type, device, lighting, angle
 2. PERSON + PRODUCT      — appearance AND the product they're wearing/using (inseparable)
 3. SETTING               — simple background that doesn't compete with the product
 4. FEATURE BEATS         — one feature per beat, each with dialogue + physical demo
 5. GRAPHIC OVERLAYS      — text captions, info cards, color/size callouts
 6. TONE & PACING         — energy level, speech rhythm, relationship to viewer
 7. TECHNICAL QUALITY     — camera, lighting, audio characteristics
```

---

## Layer-by-layer formula

### Layer 1: Format header

**Pattern:**
```
15 seconds UGC style {{CONTENT_TYPE}} video, filmed on smartphone,
{{LIGHTING_SOURCE}}, {{CAMERA_ANGLE}}.
```

| Variable | Options | Notes |
|---|---|---|
| `CONTENT_TYPE` | product showcase, feature walkthrough, try-on review, gear breakdown | Match the product category |
| `LIGHTING_SOURCE` | natural living room light, bright overhead apartment light, daylight from large windows, bedroom lamp light | Indoor residential — never a lit studio |
| `CAMERA_ANGLE` | casual handheld selfie angle, phone propped at chest height, phone in one hand slightly below eye level | Always front-facing, always personal |

**The 15-second constraint:** a natural speaker covers 2–3 short sentences in 15 seconds. This style is fast, so 3–4 short punchy lines is the ceiling — around **30 words at 2.0 words per second**, which is what 15 seconds actually holds (measured 2026-08-11: 29 words filled a 15s `seedance-2.0` render end to end; one render, treat it as the working figure). "Fast" is a delivery note, not a rate multiplier — the measured render was a punchy comic read and still came in at 2.0. The **40** that stood here was 2.5-words/sec arithmetic and would have clipped the kicker. Structure each clip as **one hook + 1–2 feature demos + a kicker**.

**Multi-clip strategy:** if the product has 4+ features, split across 2–3 prompts:

| Clip | Beat 1 (hook) | Beat 2 (demo) | Beat 3 (kicker) |
|---|---|---|---|
| **A: Hero** | "If I could only wear one thing…" | Demos the #1 standout feature | Quick reaction — "I'm obsessed" |
| **B: Features** | "Let me show you why this is different" | Demos 1–2 secondary features | Use case — "perfect for travel" |
| **C: Fit + CTA** | "The fit on this is unreal" | Turn-around, pulls at fabric, shows sizing | Urgency — "go run, sizes selling out" |

Every clip in the series carries the same `referenceAssetIds` array and the same verbatim actor tag.

---

### Layer 2: Person + product (combined)

The person and the product are inseparable — they are wearing or using it from the first frame.

**Pattern:**
```
The {{GENDER}} from @Image2 — {{AGE_RANGE}}, {{HAIR}}, {{SKIN_DETAILS}} —
wearing the @Image1 ({{PRODUCT_DESCRIPTION}}) — {{FIT_DETAILS}}.
```

Without a person reference, establish the actor in the sentence instead (`A guy in his late 20s with short dark hair and a trimmed beard…`) and repeat a terse 11–30 character tag word for word in every later beat and every later clip.

| Variable | How to fill | Key principle |
|---|---|---|
| `AGE_RANGE` | young woman, woman in her late 20s, guy in his mid-20s | Natural language, not exact ages |
| `HAIR` | long dark hair with soft waves, short curly hair, straight blonde hair in a ponytail | Casual styling |
| `SKIN_DETAILS` | natural skin with visible texture, warm complexion, light makeup with a natural finish | 1–2 reality cues, slightly more polished than raw UGC |
| `PRODUCT_DESCRIPTION` | full product name + key visual details: color, pattern, material | Real brand, visually recognizable |
| `FIT_DETAILS` | how it sits on the body — relaxed, oversized, fitted, cropped | Sizing reference if relevant |

**Skin detail bank** (pick 1–2 — a lighter touch than raw UGC):
- `natural skin with visible texture and warm undertones`
- `light makeup, natural-looking foundation`
- `natural complexion, slight shine on the forehead`
- `clean skin with a few expression lines when smiling`

The aim is unretouched, not unflattering: `natural skin texture` is the goal, `acne` and `blemishes` are not.

---

### Layer 3: Setting

Simple and residential. Says "this is her real home" without stealing attention.

**Pattern:**
```
standing in {{SPACE}} — {{DETAIL_1}}, {{DETAIL_2}}, {{ATMOSPHERE}}.
The background is slightly out of focus, keeping attention on {{PRONOUN}} and the product.
```

| Setting | Background details | Atmosphere |
|---|---|---|
| **Living room** | couch behind her, neutral walls | bright, open, modern |
| **Bedroom** | bed in background, pillows, nightstand lamp | cozy, personal |
| **Hallway / entry** | door frame, coat hooks, shoes by the door | casual, on-the-go |
| **Kitchen** | counter behind her, cabinets, morning light | warm, everyday |

---

### Layer 4: Feature beats (the engine)

Each beat is one feature = **one physical demonstration + one dialogue line**.

**Beat pattern:**
```
{{TRANSITION}} — {{FRAMING_CHANGE}}, {{PRONOUN}} {{PHYSICAL_DEMO}}: "{{DIALOGUE}}"
```

Use `Jump cut —` as the transition. Never `then`, `and then` or `followed by`: those read as a second action chained onto the first, and the second one comes back a smear. A jump cut is a new shot, which is exactly what this style wants anyway.

**15-second beat structure (3 beats):**

| Beat | Purpose | What happens | Dialogue | Time |
|---|---|---|---|---|
| 1 | **Hook** | Bold claim or excited statement, gestures to the product | 1 punchy sentence | ~4s |
| 2 | **Feature demo** | Physically demonstrates 1–2 features with the hands | 1–2 short sentences | ~7s |
| 3 | **Kicker** | Quick reaction, verdict, or CTA | 1 short line | ~4s |

**The silent beat option:** one of the three can be a silent physical demo — no dialogue, just action — which creates a breath in dense dialogue. If used, put it at beat 2, and mark it `(silent beat — no dialogue)` when you present the script at gate 1.

**Physical demonstration bank:**

| Feature type | Physical demo |
|---|---|
| Hidden pockets | reaches into the pocket, pulls the hand out showing depth |
| Stretch / comfort | pulls at the waistband, shows the elastic snap back |
| Hood / built-in feature | pulls the hood up, shows how it works |
| Softness / material | runs a hand across the fabric, bunches it to show texture |
| Fit | turns around, shows the back, pulls at the sides |
| Zipper / closure | zips up and down, shows how it fastens |
| Weight / structure | lifts the product slightly, lets it drop to show weight |

**Dialogue rules:**
- Confident, not questioning. She KNOWS this product is good.
- Descriptive and specific — names materials, features, design choices
- Short and punchy; the pace is fast
- Uses "this" and "these" a lot, pointing at what she is wearing
- The last beat carries urgency ("go run to", "selling out", "link in bio")
- No em dashes inside the spoken line — they read as written, not spoken

---

### Layer 5: Graphic overlays

| Overlay type | When | Example |
|---|---|---|
| **Keyword caption** | Bottom of frame, during each beat | "HIDDEN POCKETS", "STRETCHY AND COMFORTABLE" |
| **Size reference** | During the fit / turn-around beat | "5'4" / Size: M" |
| **Color swatches** | During the CTA beat | Product color options as swatches |

Not every beat needs one, but the hook and CTA beats almost always do. Write them as a sentence — `a keyword caption reads HIDDEN POCKETS across the lower third` — rather than as a bracketed `Caption: …` label, which invites the model to draw the label itself into the frame.

**These overlays are burned into the render.** If you want captions you can restyle or correct afterwards, leave them out of the prompt and burn them on later: that is what `shared/skills/caption-video/prompting/guide.md` is for, and it costs no credits.

---

### Layer 6: Tone & pacing

**Pattern:**
```
Throughout the video, the tone is {{EMOTION_1}}, {{EMOTION_2}}, {{EMOTION_3}} —
{{BEHAVIOR_DESCRIPTION}}. {{PACING_CUE}}.
```

**Tone bank:**

| Vibe | Emotion words | Behavior |
|---|---|---|
| **Enthusiastic expert** | confident, excited, knowledgeable | talks fast but clearly, moves with purpose |
| **Hype girl** | bubbly, high-energy, contagious | smiles constantly, gestures big |
| **Cool recommender** | assured, casual-expert, effortless | knows the product inside out |

**Pacing:** this style moves FAST. The rhythm is `speak (1–2 sentences) → demonstrate (1–2 seconds of action) → cut → repeat`.

---

### Layer 7: Technical quality

**Pattern:**
```
The lighting is {{LIGHT_TYPE}} — {{LIGHT_QUALITY}}. The image is {{CAMERA_QUALITY}} —
{{CAMERA_DETAILS}}. The sound is {{AUDIO_SOURCE}} — {{AUDIO_DETAILS}}.
```

**Lighting:** bright, even, residential. Natural daylight from windows is ideal.

**Camera:** phone quality, but steady and well framed. Slightly more polished than raw UGC.

**Audio:** direct phone mic, clear voice, quiet room.

---

## Complete template

```
15 seconds UGC style {{CONTENT_TYPE}} video, filmed on smartphone,
{{LIGHTING_SOURCE}}, {{CAMERA_ANGLE}}. A {{AGE_RANGE}} {{GENDER}} with
{{HAIR}}, {{SKIN_DETAILS}}, wearing the @Image1 ({{PRODUCT_DESCRIPTION}})
— {{FIT_DETAILS}}. Standing in {{SPACE}} — {{BG_DETAIL_1}},
{{BG_DETAIL_2}}, {{ATMOSPHERE}}.

The video opens with {{PRONOUN}} {{HOOK_ACTION}}: "{{HOOK_LINE}}"

Jump cut — {{BEAT_2_FRAMING}}, {{BEAT_2_DEMO}}: "{{BEAT_2_DIALOGUE}}"

Jump cut — {{BEAT_3_FRAMING}}, {{BEAT_3_ACTION}}: "{{KICKER_LINE}}"
{{CLOSING_ACTION}}.

Throughout the video, the tone is {{TONE_EMOTIONS}} —
{{TONE_BEHAVIOR}}. {{PACING_CUE}}.

The lighting is {{LIGHT_TYPE}} — {{LIGHT_QUALITY}}. The image is
{{CAMERA_QUALITY}} — {{CAMERA_DETAILS}}. The sound is
{{AUDIO_SOURCE}} — {{AUDIO_DETAILS}}.
```

---

## Worked example: backpack (2-clip series)

Clip A priced live 2026-08-03. Price your own before submitting — the number depends on the
model and the duration, never on the words.

### Clip A — hook + hero feature

```
15 seconds UGC style product showcase video, filmed on smartphone,
bright natural daylight from large windows, casual handheld selfie
angle. A guy in his late 20s with short dark hair and a trimmed
beard, natural skin with visible texture and slight tan, wearing the
@Image1 (Nomad Tech Backpack — matte black, 30L, roll-top closure
with magnetic buckles) — the bag is on his back, straps adjusted.
Standing in his apartment entryway — shoes by the door, keys on a
hook, bright and minimal.

The video opens with him gesturing to the backpack over his shoulder,
smiling at camera: "If I could only use one bag for everything —
work, gym, travel — this is the one."

Jump cut — he swings the bag around to his front, unrolls the top,
shows the magnetic buckle snapping shut: "Roll-top expands when you
need space, locks down with these magnets."

Jump cut — he holds the bag at chest height, taps the side, nods:
"Absolute game changer." He laughs, video cuts.

Throughout the video, the tone is confident, knowledgeable, genuinely
impressed — he presents each feature like an obvious advantage,
speaks quickly but clearly, demonstrates without fumbling. Each beat
is quick but not rushed.

The lighting is bright natural daylight from the windows, filling the
entryway evenly. The image is natural phone quality, not color graded
but well-exposed, steady handheld with slight movement when he turns.
The sound is direct from phone mic — his voice is clear and close,
minimal room echo, no music underneath.
```

30 spoken words across three beats at 15 seconds — about 2 words per second, which fits a fast delivery with the demo actions given room. That is the measured rate, not a rounding: a 29-word script filled a 15s render end to end on 2026-08-11. This example was right all along; the 2.5-words/sec rule that used to sit above it was not.

### Clip B — secondary features + CTA

Same person, same bag, same array. The actor description is repeated word for word, and `@Image2` is what actually holds the face across the two renders.

```
15 seconds UGC style feature walkthrough video, filmed on smartphone,
bright natural daylight from large windows, casual handheld selfie
angle. A guy in his late 20s with short dark hair and a trimmed
beard, natural skin with visible texture and slight tan, wearing the
@Image1 (Nomad Tech Backpack — matte black, 30L) — the bag is on
his back. Standing in his apartment entryway — shoes by the door,
keys on a hook, bright and minimal.

The video opens with him turning the bag to show the back panel,
unzipping it to reveal a padded laptop sleeve: "Separate laptop
compartment — fits a 16-inch, padded on all sides."

Jump cut — he runs his hand across the outside fabric, then flicks
water droplets off with his fingers: "Waterproof nylon. Got rained
on last week, everything inside was bone dry."

Jump cut — he puts the bag back on, adjusts the chest strap, looks
at camera: "Link's in bio — they sold out twice already, don't
sleep on it." He taps the strap and walks off frame.

Throughout the video, the tone is assured, casual-expert, effortless
— he knows the product inside out, presents features like obvious
facts, no hype, just confidence. Speaks at an upbeat pace with no
hesitation.

The lighting is bright natural daylight from the windows, filling the
entryway evenly. The image is natural phone quality, not color graded
but well-exposed, steady handheld with slight movement when he turns.
The sound is direct from phone mic — his voice is clear and close,
minimal room echo, no music underneath.
```

The call, for each clip:

```json
{
  "model": "seedance-2.0",
  "idempotencyKey": "<a new one per render>",
  "prompt": "<the clip's prompt>",
  "durationSeconds": 15,
  "aspectRatio": "9:16",
  "language": "en",
  "referenceAssetIds": ["<product assetId>", "<person assetId>"]
}
```

Clip A above uses only `@Image1`, so it can ship with a one-element array; clip B names `@Image2` and needs both. Keep the prompt and the array in step — a token past the end of the array is refused before the charge.

Price the **series**, not the clip:

```json
{
  "kind": "video",
  "model": "seedance-2.0",
  "durationSeconds": 15,
  "language": "en",
  "prompt": "<clip A's prompt>"
}
```

then multiply by the clip count, show the per-clip number, the count, the total and the balance, and get one yes for the set.

---

## Adaptation checklist

- [ ] **15 seconds** — `durationSeconds: 15` set explicitly (the default is 5)
- [ ] **`aspectRatio` set** — `9:16` (the default is `16:9`), and restated as `Vertical 9:16.` at the end of the prompt
- [ ] **Max 3 beats per clip** — hook, feature demo, kicker
- [ ] **Max 3–4 short lines**, around **27–30 words** for 15 seconds (2.0 words/sec, measured 2026-08-11) — more dialogue means another clip, not a faster read
- [ ] **Gate 1 run per clip** — numbered beats, word count, `language`, explicit yes
- [ ] **Every feature beat has a physical demonstration** — no talking-only beats
- [ ] **Hook is a bold claim** — superlative, confident, no hedging
- [ ] **Person is wearing or using the product from frame 1** — no unboxing, no reveal
- [ ] **Framing changes every beat**, separated by `Jump cut —`, never by `then`
- [ ] **Setting is simple** — 2 background details max
- [ ] **Pacing cue included** — this style moves fast; say so
- [ ] **Series planned** — 4+ features means 2–3 clips, each its own charge, priced as a set
- [ ] **Same `referenceAssetIds` array across the series**, and the actor tag repeated verbatim
- [ ] **Length** — around 260 words for this 3-beat shape; every beat specified, nothing padded
- [ ] **`@Image1` / `@Image2`** — every token matches an id you actually send, in order; never alongside `startImageAssetId`
- [ ] **No forbidden words** — no `cinematic`, `professional`, `stunning`, `8k`, `studio`, `perfect`
- [ ] **Priced live** — `POST /v1/estimates` this session, the number shown to the user, user said yes
