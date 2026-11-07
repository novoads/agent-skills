# Studio lookbook — Seedance 2.0

**Use when:** you need a polished product showcase that feels like a short brand film. One person, one product, shown across multiple styled looks against a clean studio backdrop. The voice narrates over the visuals rather than talking to camera. Best for clothing, footwear, bags, watches, or anything that benefits from being styled several ways.

**Model guide:** read [seedance-2.md](seedance-2.md) first for the request fields, the grid, and the platform rules.

**Mode:** `referenceAssetIds`, and this is the style where two references earn their keep — `@Image1` the product, `@Image2` the person. Up to 9 are allowed, images only, addressed positionally in the order you send them. Not `startImageAssetId`: the opening shot is a composed studio setup, not the flat product photo, and the two fields are mutually exclusive.

## What defines this style

This style sits in the gap between raw UGC and a produced commercial, and borrows credibility from both:

1. **Visual-first storytelling.** Unlike UGC, where the person talks to camera, here the visuals lead and the voice follows. The narrator describes what you are seeing, or what the next cut is about to show. Each shot type serves a different purpose in building the product's story.

2. **Multi-look versatility.** The same product appears in 2–3 styling combinations to prove it is versatile. The person changes tops and footwear between cuts; the product stays constant and is the thread connecting every shot.

3. **Behind-the-scenes authenticity.** The video deliberately reveals the studio — lights, camera rig, seamless backdrop, monitor. It is a trust signal: yes, this is produced, we are not pretending it is casual.

## Three things to know before you write a word

**1. The voiceover is rendered by Seedance, in this call, from this prompt.** The line inside the double quotes is spoken out loud in the finished file, and it cannot be changed without paying for the render again. So **`SKILL.md` gate 1 applies to this style** — extract the narration, present it as numbered beats with a word count against the duration, and get an explicit yes before submitting. `The sound is voiceover recorded separately, clean and close-mic'd` stays in the prompt as a description of how the audio should *sound*; it is not an instruction to add a track afterwards.

**2. Multi-look is where identity drifts, and `@Image2` is the fix.** Seedance re-casts on every cut. The fork's answer was a repeated wardrobe tag, which still fights the outfit changes this style is built on. A person reference holds the face while the clothes change around it — that is what the reference mode is for. Keep the verbatim tag too, and **never** write `the same woman` or `as before`: a back-reference resolves to nobody.

**3. The forbidden-word list and this style disagree, and the style wins.** `studio` is on the general list in [seedance-2.md](seedance-2.md), because on a UGC route it costs you the phone-filmed look. This is the one route where a lit studio with the rig in frame is the entire premise, so `studio backdrop`, `photo studio`, `cinema camera` and `cinema-quality` are the correct vocabulary here and every worked example below uses them. Nothing on the API enforces the list either way — it is craft advice, and craft advice is route-dependent. `cinematic`, `professional`, `stunning`, `8k` and `perfect` stay out regardless.

## The structure

```
 1. FORMAT HEADER         — duration, style, lighting approach
 2. PERSON + STYLING      — the model and their base look, plus outfit changes
 3. STUDIO SETTING        — the backdrop, the BTS elements visible
 4. SHOT SEQUENCE         — the visual beats: what the camera shows, in order
 5. VOICEOVER SCRIPT      — narration that runs over the visuals (NOT synced to lip movement)
 6. TONE & PACING         — the mood, the rhythm, the energy arc
 7. TECHNICAL QUALITY     — lighting, camera movement, color grade, audio
```

---

## Layer-by-layer formula

### Layer 1: Format header

**Pattern:**
```
15 seconds {{CONTENT_TYPE}} video, {{CAMERA_SYSTEM}}, {{LIGHTING_SETUP}}, clean studio backdrop.
```

| Variable | Options | Notes |
|---|---|---|
| `CONTENT_TYPE` | brand lookbook, product showcase, studio campaign, styled editorial | Match the feel |
| `CAMERA_SYSTEM` | filmed on cinema camera with shallow depth of field, filmed on DSLR with natural motion, shot on smartphone with stabilizer | More polished than UGC |
| `LIGHTING_SETUP` | large softbox key light with white seamless backdrop, natural studio window light on white background, overhead paper lantern with soft fill | Soft, even, flattering |

---

### Layer 2: Person + styling

The person is a model or brand ambassador, not a creator talking to their phone. They move deliberately, pose naturally, and do not address the camera.

**Pattern:**
```
The {{GENDER}} from @Image2 — {{AGE_RANGE}}, {{HAIR}}, {{FACIAL_DETAILS}}, {{BUILD}} —
wearing {{LOOK_1_DESCRIPTION}} with the @Image1 ({{PRODUCT_DESCRIPTION}}).
```

Without a person reference, establish the actor in the sentence instead (`A woman in her late 20s with shoulder-length dark hair…`) and repeat a terse 11–30 character tag verbatim in every later shot.

| Variable | How to fill | Key principle |
|---|---|---|
| `AGE_RANGE` | man in his early 30s, woman in her late 20s | Slightly more editorial than typical UGC |
| `HAIR` | longer hair pulled back, short textured crop, natural curls | Styled but not overdone |
| `BUILD` | lean build, athletic build, medium build | Helps with fit description |
| `LOOK_1_DESCRIPTION` | plain white crew-neck tee, suede chelsea boots, silver watch | The base outfit |
| `PRODUCT_DESCRIPTION` | full product name, color, key construction details | Stays constant across looks |

**Multi-look styling bank** (the product stays; the surrounding pieces change):

| Look | Top | Footwear | Vibe |
|---|---|---|---|
| **Casual workwear** | plain white tee, trucker hat backwards | suede boots, work boots | rugged, everyday |
| **Smart casual** | chambray button-down, sleeves rolled | leather boots, white sneakers | polished, weekend |
| **Cold weather** | chunky knit sweater, beanie | rain boots, hiking boots | outdoor, layered |
| **Minimal** | fitted black tee, no hat | clean white sneakers | modern, urban |

---

### Layer 3: Studio setting

**Pattern:**
```
Shot in a {{STUDIO_TYPE}} — {{BACKDROP}}, {{BTS_ELEMENT}}.
```

| Variable | Options | Notes |
|---|---|---|
| `STUDIO_TYPE` | small photo studio, converted loft studio, bright garage studio | A real space, not a corporate set |
| `BACKDROP` | white seamless paper backdrop, off-white muslin, light grey backdrop | Clean, lets the product pop |
| `BTS_ELEMENT` | large softbox visible at the edge of frame, camera rig on a tripod in the foreground, hardwood floor peeking past the seamless edge, a monitor showing the live feed | Include 1–2. They are the authenticity anchor |

---

### Layer 4: Shot sequence

Each 15-second clip uses 3–4 shot types. The shots do **not** sync to the narration — the voiceover runs continuously while the visuals cut between angles.

**Shot type bank:**

| Shot type | What it shows | Purpose |
|---|---|---|
| **Seated inspect** | Sitting on a stool, holding the product, examining it | Shows relationship to the product |
| **Full-body standing** | Wearing the product, hands in pockets or at sides | Overall fit and silhouette |
| **Turn / walk** | Turns to show side or back, or walks a few steps | How the product moves on a body |
| **Waist-down fit** | Cropped at the waist, product on legs or lower body | Fit, break line, hem |
| **Extreme close-up** | Tight on fabric, stitching, rivets, construction | Proves quality |
| **Rack display** | Product on a rack or hanger, multiple colorways | Shows the range |
| **BTS reveal** | Wide shot of the full studio — lights, camera, backdrop | Authenticity signal |
| **Outfit change** | Same person, different styling around the same product | Proves versatility |

**15-second frameworks:**

| Clip type | Shot 1 (~4s) | Shot 2 (~4s) | Shot 3 (~4s) | Shot 4 (~3s) |
|---|---|---|---|---|
| **Hero intro** | Seated inspect | Full-body standing | Extreme close-up | BTS reveal |
| **Versatility** | Full-body Look A | Turn / walk | Full-body Look B | Waist-down fit |
| **Detail focus** | Rack display | Extreme close-up | Waist-down fit | Full-body standing |

Separate shots with `Cut to`. Never `then` or `followed by` — those read as one action chained onto another and come back as a smear.

---

### Layer 5: Voiceover script

The voiceover is not lip-synced. The person poses, turns and inspects while a voice narrates over the top. Seedance still renders it from this prompt.

**Pattern for 15 seconds (2–3 sentences max):**
```
Voiceover: "{{OPENING_LINE}}. {{FEATURE_LINE}}. {{CLOSER_LINE}}."
```

**Voiceover rules:**
- First person, but not to camera — a narration, not a conversation
- Conversational, slightly more polished than raw UGC dialogue
- Names the product by its full name at least once
- Hits 1–2 specific features
- Closes with the brand name or where to buy
- Relaxed and measured, not rushed
- **Count the words.** A calm lifestyle narration is **deliberately slower** than the library's 2.0 words/sec baseline — about **1.5 words/sec** — so 15 seconds is roughly **22–29 words**, not 50. The two ends of that range mean different things: 22 is the *style* (1.5 words/sec, the unhurried read this format is for), and 29 is *physics* (2.0 words/sec, measured 2026-08-11 — a 29-word script filled a 15s render end to end with no tail room). Write toward 22. Past 29 the narration is not merely rushed, it is cut off. Over-writing is the most common way this style comes back rushed.

Set `language` to the language you wrote it in, and write the prompt in that language too. Nothing on the API pushes back on a Spanish or Portuguese narration, and the estimate's advice arrives in the prompt's own language.

---

### Layer 6: Tone & pacing

**Pattern:**
```
Throughout the video, the tone is {{EMOTION_1}}, {{EMOTION_2}}, {{EMOTION_3}} —
{{VISUAL_BEHAVIOR}}. {{PACING_CUE}}. The voiceover is {{VOICE_QUALITY}}.
```

**Tone bank:**

| Vibe | Emotion words | Visual behavior | Voice quality |
|---|---|---|---|
| **Considered appreciation** | confident, thoughtful, measured | moves slowly, inspects details, handles the product with care | warm, steady, unhurried |
| **Quiet pride** | understated, assured, grounded | stands tall, tucks a shirt, adjusts cuffs | low-key, conversational, no hard sell |
| **Aspirational everyday** | elevated, real, capable | styled but not stiff, moves naturally | articulate but relaxed |

**Pacing rules:**
- Shots linger 3–4 seconds each — longer than UGC jump cuts
- Cuts are clean (hard cut, no dissolves) but unhurried
- The person moves slowly and deliberately between poses
- The narration pace matches the visual pace

---

### Layer 7: Technical quality

**Pattern:**
```
The lighting is {{LIGHT_SETUP}} — {{LIGHT_QUALITY}}. The image is {{CAMERA_QUALITY}} —
{{CAMERA_DETAILS}}. The sound is {{AUDIO_TYPE}} — {{AUDIO_DETAILS}}.
```

**Lighting:** `large softbox creating soft even illumination, slightly warm tone`

**Camera:** `cinema-quality, shallow depth of field on close-ups, earth-tone color palette`

**Audio:** `voiceover recorded separately, clean and close-mic'd, subtle ambient music underneath` — a description of the sound you want, rendered in this same call.

---

## Complete template

```
15 seconds {{CONTENT_TYPE}} video, {{CAMERA_SYSTEM}},
{{LIGHTING_SETUP}}, clean studio backdrop. A {{AGE_RANGE}}
{{GENDER}} with {{HAIR}}, {{FACIAL_DETAILS}}, {{BUILD}}, wearing
{{LOOK_DESCRIPTION}} with the @Image1 ({{PRODUCT_DESCRIPTION}}).
Shot in a {{STUDIO_TYPE}} — {{BACKDROP}}, {{BTS_ELEMENT}}.

{{SHOT_1_TYPE}} — {{SHOT_1_DESCRIPTION}}.

Cut to {{SHOT_2_TYPE}} — {{SHOT_2_DESCRIPTION}}.

Cut to {{SHOT_3_TYPE}} — {{SHOT_3_DESCRIPTION}}.

Voiceover: "{{VO_LINE_1}}. {{VO_LINE_2}}. {{VO_LINE_3}}."

Throughout the video, the tone is {{TONE_EMOTIONS}} —
{{VISUAL_BEHAVIOR}}. {{PACING_CUE}}.
The voiceover is {{VOICE_QUALITY}}.

The lighting is {{LIGHT_SETUP}} — {{LIGHT_QUALITY}}. The image is
{{CAMERA_QUALITY}} — {{CAMERA_DETAILS}}. The sound is
{{AUDIO_TYPE}} — {{AUDIO_DETAILS}}.
```

---

## Worked example: waxed canvas weekender bag

The fork's example, restored verbatim, and priced live 2026-08-03. It states no aspect ratio in
the prompt text — the `aspectRatio` field is what binds the output, so send it, and add the
sentence too when the framing matters.

```
15 seconds brand lookbook video, filmed on cinema camera with
shallow depth of field, large softbox key light with white seamless
backdrop, clean studio backdrop. A woman in her late 20s with
shoulder-length dark hair tucked behind her ears, clean skin with
natural complexion, lean build, wearing a white linen button-down
tucked into high-waisted olive trousers with the @Image1 (Waxed
Canvas Weekender — tobacco brown, leather handles and brass
hardware, side zip pocket, monogrammed luggage tag). Shot in a
small photo studio — white seamless paper, camera rig on tripod
visible in foreground.

She sits on a wooden stool holding the bag on her lap, running
her hand across the waxed canvas, inspecting the brass zipper.

Cut to full-body standing — she has the bag over her shoulder,
one hand on the strap, looking slightly off-camera with a
relaxed expression.

Cut to extreme close-up — the waxed canvas texture filling the
frame, leather handle stitching visible, a brass buckle catching
the light.

Voiceover: "I've been looking for a bag that can handle a
weekend trip without looking like luggage. The Waxed Canvas
Weekender is it — the canvas gets better with every trip."

Throughout the video, the tone is confident, thoughtful,
measured — she handles the bag with care, moves slowly, each
shot lingers. The voiceover is warm and unhurried, like someone
describing a favorite possession.

The lighting is large softbox creating soft even illumination,
slightly warm tone. The image is cinema-quality, shallow depth
of field on close-ups, earth-tone color palette. The sound is
voiceover recorded separately, clean and close-mic'd, subtle
acoustic guitar underneath.
```

The call — `@Image1` first, `@Image2` second, because the tokens resolve by array position:

```json
{
  "model": "seedance-2.0",
  "idempotencyKey": "<one per clip>",
  "prompt": "<the prompt above>",
  "durationSeconds": 15,
  "aspectRatio": "9:16",
  "language": "en",
  "referenceAssetIds": ["<product assetId>", "<person assetId>"]
}
```

If you only have the product photo, drop `@Image2`, describe the person in the sentence, and send one reference. A token pointing past the end of the array is refused before anything is charged — which is the cheap failure, but it is still a failure, so keep the prompt and the array in step.

Price it first. The estimate takes the pricing fields only; `referenceAssetIds` and `aspectRatio` are a `400` there:

```json
{
  "kind": "video",
  "model": "seedance-2.0",
  "durationSeconds": 15,
  "language": "en",
  "prompt": "<the prompt above>"
}
```

Then run gate 1 on the narration before submitting — 29 words against 15 seconds is **2.0 words per second** of delivered speech, which is not "close to the ceiling", it *is* the ceiling: a 29-word script filled a 15s render end to end on 2026-08-11, leaving no tail room. So this example sits at the fast end of a style whose whole point is an unhurried read, and another sentence would not rush it — it would clip it. (That measurement is a lip-synced talking head; whether a Seedance voiceover front-loads its silence the same way is unmeasured, so check the render.)

---

## Adaptation checklist

- [ ] **15 seconds** — `durationSeconds: 15` set explicitly (the default is 5)
- [ ] **`aspectRatio` set** — `9:16` for social (the default is `16:9`), and restated as `Vertical 9:16.` at the end of the prompt
- [ ] **3–4 shots per clip** — each lingering ~3–4 seconds, separated by `Cut to`
- [ ] **Voiceover, not talking to camera** — narration over the visuals, no lip-sync
- [ ] **Max 2–3 narration sentences**, roughly **22–29 words** for 15 seconds — aim at 22, because this style is the deliberate 1.5-words/sec read; 29 is the measured hard ceiling
- [ ] **Gate 1 run on the narration** — numbered beats, word count, explicit yes
- [ ] **At least one BTS element** — studio light, camera rig, or the seamless edge
- [ ] **Product constant across looks** — only the surrounding styling changes
- [ ] **At least one extreme close-up** — fabric, stitching, hardware
- [ ] **Person does not talk to camera** — they pose, turn, inspect, move
- [ ] **No back-reference** — repeat the actor tag verbatim, never `the same woman`
- [ ] **Length** — around 270 words for this 3-shot-plus-narration shape; every shot specified, nothing padded
- [ ] **`@Image1` / `@Image2`** — every token matches an id you actually send, in order; `referenceAssetIds` never alongside `startImageAssetId`
- [ ] **No forbidden words** — no `cinematic`, `professional`, `stunning`, `8k`, `perfect`. `studio`, `cinema camera` and `cinema-quality` are the exception on this route and are the point of it — see note 3 above.
- [ ] **Priced live** — `POST /v1/estimates` this session, the number shown to the user, user said yes
