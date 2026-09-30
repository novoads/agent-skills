# Gemini Omni Flash — prompting guide

Prompting brain for Google DeepMind's **Gemini Omni Flash** video model ("Gemini Omni").
Prompting-only folder — no `SKILL.md`, so `sync-skill.sh` won't register it as a skill. Read it
before composing any `omni-flash` prompt.

**Where you call it from this workspace:** `POST /v1/videos` with `"model": "omni-flash"`, and
nowhere else. Async — it returns a `jobId` you poll at `GET /v1/generations/{jobId}`. Every HTTP
detail comes from the `novoads-api` skill and its `reference.md`.

**Sources** (scraped 2026-07-09):
- <https://deepmind.google/models/gemini-omni/prompt-guide/>
- <https://deepmind.google/models/gemini-omni/>

---

## ⚠️ Read this before the rest: what this API actually exposes

This guide is Google's own prompting documentation for the model, and it was written for **Google's
surfaces** — the Gemini app, Flow, AI Studio — where Omni is a conversational, multi-turn editor.
**Novoads exposes one stateless generation call.** That difference invalidates several of the
headline capabilities below, and a prompt written against them wastes a paid render.

**What works here:**

| | |
|---|---|
| Text to video | yes — the primary mode |
| Image to video | yes. **`startImageAssetId`** is sent as one reference image the model may place anywhere in the clip, not a first frame. For a true first frame, **`firstFrameAssetId`** (and **`lastFrameAssetId`**, which needs it), only where the server publishes them |
| Reference images | **`referenceAssetIds`** (API 2.30.0 on): images only, up to the field's `maxItems` in the OpenAPI document, addressed `@Image1`…`@ImageN` in the order sent. Never beside `startImageAssetId` |
| Reference video | **`referenceVideoAssetId`** (API 2.30.0 on): one video. Where the server also publishes `firstFrameAssetId`, its length bounds `durationSeconds`. It shares the reference slots with the images |
| `seed` | an integer, 0 to 2147483647, only where the server publishes it |
| `resolution` | read `resolutions` from `GET /v1/models`: `360p`, `720p`, `1080p` and, where the list carries it, `4k` (API 2.31.0); or `720p` alone, depending on the server. Never assume `4k`. Send the key only when the list has more than one value; otherwise it is a `400` |
| `durationSeconds` | **enum: 4, 6, 8, 10 only.** Not the continuous 4–15 grid Seedance has. Out-of-grid values are rejected, never rounded. Defaults to 8 |
| `aspectRatio` | **`9:16` (default) or `16:9`.** That is the whole grid — no `1:1`, no `4:3`, no `21:9`. Seedance's wider grid does not apply here |
| Prompt ceiling | **20,000, by far the largest of any VIDEO model here**, where the rest sit at 4,000. This model is the one place the long, layered prompts below actually fit. It is not the largest on the API: since deployed spec 2.16.0 two image models are roomier still (`nano-banana-pro` 50,000, `gpt-image-2` 32,000), which is a fact about `POST /images` and changes nothing about a video call |
| `language` | yes |

**What does NOT work here, no matter how the sections below are worded:**

- **No multi-turn editing.** Each call is independent and the service holds no video to amend.
  "Edit this keeping everything the same" has no antecedent — it renders a fresh video from that
  sentence alone. Every section framed as an *edit* is a section you have to re-express as a full
  scene description.
- **References reach this model as `referenceAssetIds` (images) and `referenceVideoAssetId` (one
  video)**, since API 2.30.0; on an older deployment either is a strict `400`, so read the OpenAPI
  document the server serves. What stays out of reach is the inline `<video>` / `<image>` /
  `<audio>` placeholder syntax the sections below use: name each image by its `@ImageN` token in
  the prompt instead. Nothing in this pack has measured Omni's motion or style transfer from a
  reference through this API, so treat the first render of such a route as a test.
- **No audio input on this model.** A video goes in `referenceVideoAssetId` and nowhere else; a
  video `assetId` in `referenceAssetIds` or a frame field is a `400`, and Omni Flash takes no
  audio. (From API 2.35.0 the three Seedance models take mp3 in `referenceAudioAssetIds`.)
- **No SynthID/C2PA claim either way.** The watermarking note near the end of this file describes
  Google's own surfaces. Do not repeat it as a fact about output obtained through this API — it has
  not been verified here.

So: **read this guide for how to compose one strong single-shot prompt.** The five elements, the
camera vocabulary, the real-world-knowledge principle, the text-rendering rules and the style
language are all fully usable, and the 20,000-character ceiling means you can spend them. Treat
every "ask for the delta" instruction as describing a product this repo does not call.

---

## The one-line mental model

> **Think of Gemini Omni like Nano Banana — but for video.**

That single framing drives every rule below. As a *model* it is a conversational, multi-turn editor
that happens to output video, not a one-shot text-to-video renderer. Two consequences — and note
that **only the second one survives the trip through this API**:

1. ~~**You don't re-prompt the whole scene to change one thing.** You ask for the delta.~~
   Not here: the call is stateless, so every prompt re-prompts the whole scene. Write complete
   scenes, not deltas.
2. **You don't over-specify.** Omni reasons. A model like Veo needs precise instructions; Omni wants
   intent. This is the half that matters most on a single-shot call — spend the prompt on aesthetic
   intent and let the model supply the physics and the world knowledge.

> "With Veo, you need to share precise instructions to get the best results. But with Gemini Omni,
> you don't have to be as prescriptive with your prompt. Instead, tell Omni what you want to
> create — and watch the model's reasoning and world knowledge bring the details to life."

The guiding tension: **more detail = more control**, but detail spent on things the model already
knows (physics, history, how a violin is held) is wasted. Spend detail on *aesthetic intent*.

---

## The five prompt elements

Mix these; you don't need all five in every prompt.

| Element | Ask yourself | Example vocabulary |
|---|---|---|
| **Shot framing and motion** | How is the shot framed? How does the camera move? | wide-angle, medium, close-up; glide gently, rush suddenly |
| **Style** | How should the scene *feel*? | realistic vs. cinematic; grounded vs. majestic |
| **Lighting** | Where does light come from, and what does it do? | sun, streetlamp, off-screen; crisp, warm, ethereal |
| **Location** | Where is the scene set? | "an alien landscape with clear, azure water" |
| **Action** | What happens? Who/what moves and interacts? | characters, objects, movement, interaction |

On **Location** specifically: state the landscape you imagine, but don't describe every detail —
Omni works from your overall intention.

---

## Editing through natural conversation

> **Not reachable through this API.** Every call is stateless — there is no prior video to
> amend, so an edit instruction renders a fresh scene from that sentence alone. Kept because it
> documents the model, and because it un-parks if the API ever exposes an edit path.

This is the model's headline capability. Omni **preserves the video across multiple amends** —
keeping what works, letting you focus on what isn't working.

### Edit iteratively

Ask for one specific update — a background change, a new caption — without re-prompting the scene.
Edits chain, and each builds on the last while keeping the scene coherent.

```
Prompt: Change the butterfly to a bee.
Prompt: Change the bee into a small swarm of fireflies.
```

Multi-turn consistency example (same source clip, three sequential turns):

```
Prompt: Transport the violinist to the image environment
Prompt: Make the violin invisible
Prompt: Change the camera angle to be over the violinist's shoulder.
```

### Edit how the camera works

Change camera angle, point of view, and movement conversationally.

```
Prompt: Change the camera angle to be over the violinist's shoulder.
Prompt: Change the camera angle, a close-up on his shoes, quickly tilting up to medium shot, then widening.
```

### Change the action

Ask Omni to change how the scene moves — or to **sync two different inputs**, e.g. pairing the
lights of a building to the beats of a soundtrack.

```
Prompt: The lights of the apartments start turning on in sync with the music.
Prompt: Make it look like the weird shape of my hand hole super zooms and magnifies the ground it's looking at in sharper quality.
Prompt: When the finger in <video> touches the animal toy play the sound the animal makes
```

### Swap objects and characters

```
Prompt: Change spaceship to <object>
Prompt: turn me into this character          # + a character reference image
```

---

## Camera direction vocabulary

Omni follows real videography terminology. Use it literally.

- **Continuous shot** — `one continuous shot`, `oner`
- **Fixed angles** — `static`, `locked off`, `fixed`
- **Movements** — `push in`, `punch in`, `dolly zoom`
- **Camera type / texture** — `natural smartphone zoom`, `film camera`, `webcam style`

---

## Apply real-world knowledge

Omni pairs an intuitive understanding of physics with Gemini's knowledge of history, science, and
culture. **You don't need to over-explain — you just need to ask.**

Physics (gravity, kinetic energy, fluid dynamics):

```
Prompt: A marble rolling fast on a chain reaction style track, continuous smooth shot
```

History / science / math, with narrative built around it:

```
Prompt: claymation explainer of protein folding, everything is made out of clay, no hands, stop motion, accurate

Prompt: A skeuomorphism stop motion explainer about how the brain hippocampus works with a
compelling voiceover. Don't add seahorses. No voice cuts at the end. Don't add text.
```

Note the negative constraints in that last one (`Don't add seahorses`, `No voice cuts at the end`,
`Don't add text`) — Omni honors explicit exclusions, and they're how you suppress the model's
"helpful" default embellishments.

Conceptual explainer with a heavy style spec:

```
Prompt: Explain the difference between regular computing and quantum computing. Visualize this
sentence using a contemporary flat-media style that blends minimalist vector shapes with rich
organic textures. The aesthetic is defined by a high-contrast, "electric" color palette of neon
pinks, cyans, and limes set against a deep navy background. A hallmark of this style is the use of
stipple shading and grainy gradients, which adds a tactile, risograph-like quality to the otherwise
simple geometric forms. By combining sharp edges with these softened, speckled transitions, the
illustration achieves a playful, editorial feel.
```

---

## Text rendering

Omni doesn't just render text accurately — it creates text **in sync with the visuals**. Control
type, placement, animation, and exposure.

```
Prompt: word by word, one word on a the screen at a time: did, you, know, that, this, model, can,
do, pretty, good, text!? each word appears with a different animated style, perfect pacing to a
rhythm, sizzle reel.
```

A dense, fully-specified text + timing brief (note the explicit FPS and frames-per-item pacing):

```
Prompt: The video shows items of the alphabet. An unusual item starting with each letter is shown
sitting on a table (like a Capybara for C, disco globe for D and Lava Lamp for L). All 26 letters
must be represented by 26 items with matching lower thirds displaying the letter. Only one item and
lower third at a time. Each lower third must look like a black marker written on a slip of paper in
the bottom left. Rapid fire, roughly 9 frames per item at 24FPS. Last frame is a slip of paper
"THE END". The whole video is accompanied by calm smooth music.
```

---

## Reference complex actions

> **Not reachable through this API.** Every call is stateless — there is no prior video to
> amend, so an edit instruction renders a fresh scene from that sentence alone. Kept because it
> documents the model, and because it un-parks if the API ever exposes an edit path.

Describe an intricate action once. Omni understands the intention and how it should apply across
the video — no frame-by-frame description needed.

```
Prompt: Edit this keeping everything the same. Add animated motion effects coming out of the skateboard.
```

---

## Reference anything: combining inputs

> **Partly reachable through this API (2.30.0 on).** `omni-flash` takes images in
> `referenceAssetIds`, addressed `@Image1`…`@ImageN`, and one video in `referenceVideoAssetId`.
> The inline `<video>` / `<image>` / `<audio>` placeholders below are not how this API addresses
> them, and there is no audio input: rewrite each image placeholder as its `@ImageN` token.

Reference and combine any media — **images, videos, text, and audio** — inside a single prompt,
using inline `<video>` / `<image>` / `<audio>` placeholders.

```
Prompt: The birds from <video> loosely form the imperfect shape of a bird based on <image>. They
move to the music from <audio> and dissipate as they fly

Prompt: Referring to the extreme camera movement, perspective, and distortion in <video>, create a
front-facing full-body walk cycle of the character from <image>, quickly style-shifting into
multiple visual styles during the walk cycle, starting from realistic cinema. Keep the environment,
only change styles. Hard cut backgrounds always centering the sky. Continuous walking, continuous
audio, and style shifts in perfect sync to the beat of the audio. Cinematic, 16:9.

Prompt: Add harp sounds synchronized to when I touch each fern leaf. Change the leaf structure to
all resemble semi translucent 3d bioluminescent plant life, with bioluminescent fireflies flying
around it that react as I play, in sync with the sounds, subtle bokeh depth of field dynamic
lighting, relecting off the walls in the room, keeping the room structure the same

Prompt: Imagine the world gradually changing into retro futuristic style (grainy and moody as
<image>) as I walk. Use the audio for a retro-futuristic background music. 10s.
```

### Transfer motion and style

```
Prompt: Apply the pose and motion from input video to provided character from this image. Apply
style from image reference to the new video

Prompt: Rose is made from this crystal-like material

Prompt: Apply the motion of the whale swimming from the provided video to the provided image of
fluid reflective material. Do not show the whale or water; instead, have this reflective moving
material form a shape that resembles the whale as it swims. Replace water with white smooth
material shapes that move
```

### Edit real video from reference images

```
Prompt: When the hand opens, make a vast 3d architectural structure based on this image start
building upward, sitting in the palm of the hand, reflecting prismatic light onto the hand and
table. It builds with a 3d wireframe holographic effect. No music, just realistic real world sound.

Prompt: When the hand opens, reveal a physical photorealistic flying machine based on this sketch,
floating above the hand, propeller spinning. No music, just realistic sound.
```

### Translate drawings into video

Sketches guide *movement* without appearing in the output.

```
Prompt: turn this into realistic footage, using the drawing only as a guide for movement, do not
show the drawing in the final video
```

---

## Apply new styles

Reimagine how a scene looks while **maintaining the original motion and details** — anime,
claymation, watercolour, and beyond. Style transforms can be sequenced within one clip:

```
Prompt: Create a four-part stylistic progression of the video reference that begins with a vibrant
colored crayon aesthetic, featuring rich, waxy, textured strokes and playful, hand-drawn character
designs against a backdrop of heavily granulated paper. Transition seamlessly into a graphite
pencil sketch on textured paper, utilizing cross-hatching, varying line weights, and a 12fps "line
boiling" effect to emphasize a hand-drawn feel. Next, morph into a hyper-realistic 3D translucent
glass style, characterized by complex light refractions, caustic patterns, and soft internal glows
within a minimalist studio setting. Conclude the sequence with a tactile risograph print look,
applying a limited three-color palette, grainy halftone textures, and intentional registration
overlays for a retro, mechanical finish.
```

Trigger-based transforms ("when X happens, become Y") are a reliable pattern:

```
Prompt: When the person touches the mirror, make the mirror ripple beautifully like liquid, and the person's arm turns into reflective mirror material
Prompt: When the person touches the mirror, the person transforms into a detailed monochrome line art drawing
Prompt: When the person touches the mirror, the person suddenly transforms into a cute felted stuffed puppet version with large googley eyes and glasses
Prompt: When the person touches the mirror, the person instantly transform into a vintage monochrome transparent 3d line art hologram, inside of a monochrome 3d holodeck maintaining the structure and details of the room and environment
Prompt: When the person touches the mirror, the entire environment turns into 3d voxel art
```

---

## Storyboard-based generation

> **Reachable as a reference image (2.30.0 on).** Send the storyboard sheet in `omni-flash`'s
> `referenceAssetIds` and name it `@Image1` in the prompt. Nothing in this pack has measured how
> closely Omni follows a sheet through this API, so treat the first render as a test.

Already know the narrative arc? Hand Omni a **visual storyboard** and it generates video following
your key beats.

```
Prompt: Show me in this story. Follow the story exactly in order starting top left. Entire story in
10 seconds. Cinematic
```

---

## Keep your scene consistent

> **Reachable since API 2.30.0.** Send the character, object or setting in `omni-flash`'s
> `referenceAssetIds` and name it by its `@ImageN` token. Nothing in this pack has measured how
> well Omni holds a face across separate clips; the documented route for a series is Seedance's.

To hold a character, object, or environment steady, **add a reference** — from real life or
generated with Nano Banana — and Omni will carry it across the scene.

```
Prompt: Change the ships to be made from white origami paper.
Prompt: Change the astronaut to a sea anemone.
Prompt: Change the small ships to stingrays.
```

---

## Best practices (checklist)

Rewritten for the single-shot call this repo makes. The three items that assumed a conversational
session or multi-modal inputs are marked, not silently dropped.

- [ ] **Add detail for control.** More detail = more control over the final output — and with a
      20,000-character ceiling you have room for it, unlike the 4,000 Seedance allows.
- [ ] **Spend detail on aesthetics, not facts.** Leverage Omni's world knowledge instead of
      over-specifying physics, history, or how objects work.
- [ ] ~~Edit conversationally; ask for the delta.~~ **Write the complete scene every time** — the
      call is stateless and there is nothing to amend.
- [ ] **Use real camera vocabulary** (`oner`, `locked off`, `dolly zoom`, `webcam style`).
- [ ] **Combine images and one video** (API 2.30.0 on): images in `referenceAssetIds`, addressed
      `@Image1`…`@ImageN`, and one clip in `referenceVideoAssetId`. No audio input on this model (Seedance takes it in `referenceAudioAssetIds`).
- [ ] **State exclusions explicitly** (`No music, just realistic sound`, `Don't add text`). Worth
      doing on every ad prompt: `no on-screen text, no captions, no subtitles` keeps the model from
      inventing burned-in captions you would then have to re-render to remove.
- [ ] **Pin timing and framing in the prompt text** as well as in the fields — but the fields are
      what bind. `durationSeconds` is 4/6/8/10 and `aspectRatio` is `9:16` or `16:9`; a prompt
      asking for `12s` does not override the field, it just confuses the composition.
- [ ] **Anchor consistency with a reference image** in `referenceAssetIds`, named by its `@ImageN`
      token. `startImageAssetId` is a reference on this model too, not a first frame; for a true
      first frame use `firstFrameAssetId` where the server publishes it.
- [ ] **Price it first.** `POST /v1/estimates` with `kind: "video"`, `model: "omni-flash"` and the
      duration charges nothing, and it is the only place a credit number may come from.

---

## Capability and performance notes

Modalities the model has: **Video Editing, Text to Video, Image to Video, Reference to Video.**
Modalities reachable here: **Text to Video**, **Image to Video** (`startImageAssetId` as a
reference, or `firstFrameAssetId` as a true first frame where the server publishes it) and, since
API 2.30.0, **Reference to Video** (`referenceAssetIds`, `referenceVideoAssetId`). **Video Editing**
is not documented here: every call is stateless, and nothing in this pack has tried editing a clip
sent as `referenceVideoAssetId`. See the scoping section at the top.

Per DeepMind's published evals:

- **Video Editing** — leading on Overall Preference and Instruction Following in human side-by-side
  comparisons vs. other leading video models (internal benchmark; 504 examples).
- **Text to Video** — best on Overall Preference and Instruction Following on MovieGenBench
  (Meta's public benchmark; 1,003 prompts). Separately evaluated on a 500-prompt **Fast Motion**
  set covering sports and high-energy physical action.
- **Image to Video** — on VBench I2V (355 image+text pairs), Omni Flash **tied** with
  Grok-Imagine-Video and Kling, leading over other models.
- **Reference to Video** — leading on Overall Preference and Speech Adherence (internal benchmark;
  468 examples mixing image, audio, and text references).

Treat the tied I2V result as the honest read: Omni's edge is **editing, instruction following, and
multimodal reference handling**, not raw image-to-video fidelity.

## Provenance / watermarking

> **Describes Google's own surfaces, not verified for output obtained through this API.**

Content created or edited with Omni in the Gemini app, Google Flow, or YouTube carries an
imperceptible **SynthID** watermark and **C2PA Content Credentials**. Assume anything you generate
through those surfaces is detectable as AI-generated and labeled as such.

## Surfaces

**In this workspace:** `POST /v1/videos` with `"model": "omni-flash"`. That is the only surface
these instructions run against.

Google's own surfaces, for context on where the documentation above came from: Gemini app · Google
Flow · YouTube Shorts · Google AI Studio · Gemini API · Google Enterprise Agent Platform.
