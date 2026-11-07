# Beat formulas — the genre library

The per-beat prompt formulas for `pixar-ad`. `SKILL.md` owns
the pipeline: the gates, the costs, the calls, the SYNC/VO track rule. This file
owns the CRAFT: what each beat is, the variables it takes, and a worked prompt
for the still and for the clip.

Read `SKILL.md` first. Nothing here overrides it. Where this file shows a prompt,
the style lock and the negative block in `SKILL.md` are pasted into it verbatim.

> **Provenance.** The genre arc, the cast-sheet shape, the variable tables and
> the six-block animation structure are adapted from the Pixar-style-ad prompting
> guide in `krusemediallc/arcads-claude-code` (MIT, Copyright (c) 2026 Caleb
> Kruse / Kruse Media LLC). Adapted, not copied: the API mechanics are ours, the
> studio names are stripped under our IP rules, the audio doctrine is our
> SYNC/VO one, and the T12 lessons are measurements his guide could not have.
> Full notice in `NOTICE.md` beside this file.

## Why the genre works

The hook is **anthropomorphism plus a tiny story**, not the product. A viewer
scrolling past an ad decides in half a second whether a face is worth looking at,
and this genre puts a face on the one thing they already have an opinion about:
their problem. The product does not appear until someone has already agreed the
problem is real.

That is the whole mechanism, and it is why a beat board that opens on the product
loses to one that opens on a sad object with eyes.

## The four genre roles

Four roles, not four beats. Our board is five to six beats (`SKILL.md`), and the
roles map onto it. A role can span two beats; a beat carries exactly one role.

| Role | Purpose | What is on screen | Fits skeleton beat |
|---|---|---|---|
| **A. Anthropomorphized problem** | Give the pain point a face and a voice. The pain point IS the character. | Close-up macro of the problem object with oversized eyes and a small mouth, speaking the complaint in first person. | 1 (Hook) and, in a montage, 2 |
| **B. Protagonist reveal** | Cut to a human in a warm interior meeting the product. | Big-eyed protagonist in soft window light, holding the product, surprised or curious. | 3 or 4 (the Turn) |
| **C. Mascot mechanism** | Show HOW it works, from inside. | Stylized cross-section of the relevant structure with small mascot characters doing the mechanism, energy lines tracing it. | 4 (the Turn), or its own beat |
| **D. CTA and end card** | Resolve the hook. Protagonist confident, then the real product. | Protagonist facing camera, then the composited hero card. | Last beat |

**Role A is the one that is missing when an ad in this genre falls flat**, and it
is the one T12 skipped. All three of its beats were setup shots with narration
over them. There was no character, so there was nothing to root for.

### Arc variations

Pick one when the straight A-B-C-D arc does not fit:

- **Cold-open intercut.** Alternate role A with quick cuts of the human looking
  defeated before settling into B. Buys urgency, costs a beat.
- **Multi-pain montage.** Three problem characters in sequence, one line each,
  before B. Best when the product solves three named complaints. Each character
  gets its own object, its own voice and its own world.
- **Testimonial overlay.** The protagonist speaks the value in first person in
  role B instead of a narrator. Turns beat B into a SYNC beat, which is a good
  way to satisfy the one-SYNC-beat rule when role A is silent.

## Cast and continuity sheet

Write this BEFORE any call. It is what makes five separately rendered beats look
like one film, and it is the input to the cast-sheet image in Gate 3.

```
PROTAGONIST (human hero)
- Age band: 20s / 30s / 40s / 70s
- Build: petite / average / curvy
- Hair: colour, length, style ("ash-brown low bun with face-framing strands")
- Eyes: colour, large irises, multiple catchlights
- Skin: warm undertone, freckles across the nose bridge
- Outfit: cream waffle-knit robe over a fitted tank, thin gold necklace
- Personality cue: gentle smile, slightly tilted head
- TERSE TAG (11 to 30 chars, wardrobe-anchored): "cream waffle robe woman"

ANTHROPOMORPHIC PROBLEM CHARACTER (role A)
- What object: <the pain point itself, never a stand-in>
- Face placement: <two big sad eyes and a small downturned mouth, embedded where>
- Voice and personality: <defeated, weary, mumbling>
- Its ONE line, in first person, under 8 words

MASCOT CHARACTERS (role C)
- Form: chibi blob, 2 to 3 inches tall, smooth matte rubbery material
- Colour: ivory white with soft pink cheeks
- Eyes: tiny black dot pupils, single highlight, oversized
- Behaviour: cooperative team, gently working the mechanism
- Count: 3 to 5. More than five and they stop reading as individuals.

WORLDS (one per beat, and they must differ)
- Role A: <macro world of the problem object>
- Role B and D: <sunlit interior, named practical light source>
- Role C: <stylized cross-section of the structure>

PRODUCT
- Real brand, real packaging, from the photo. Colours, shape, label text.
- Held at chest height, one or both hands, facing camera.
- Which beats it appears in: <B and D only, plus the composited end card>
```

**The terse tag is not decoration.** Our renders re-cast on every cut, so a beat
that says "the same woman" names nobody. Establish the protagonist once in full,
then repeat the tag word for word in every later beat. Do not elaborate it; an
elaborated tag re-casts as readily as a missing one.

Save the sheet next to the run. The next ad for the same brand reuses it.

**If the brand already has a hero image of its character, skip generating one.**
Pass it as the reference into the role B and role D stills directly. Roles A and
C do not need it at all, since neither has the protagonist in frame. That saves
the cast-sheet render and, more importantly, it is the only way to match a
character a brand has already published.

## Forbidden words, and what to write instead

Two lists collapse into one table. The first column pulls the render away from
the look; the second is what our own prompt lint flags.

| Do not write | Write instead | Why |
|---|---|---|
| `cinematic` | `3D animated film look` | Both: pulls to live-action grade, and our lint flags it |
| `perfect`, `flawless` | `ivory white matte`, `even` | Our lint flags it |
| `8k`, `4k`, `hyper-detailed` | `high fidelity`, `rich material detail` | Our lint flags it |
| `stunning`, `professional` | `polished` | Pulls to stock-render gloss |
| `studio`, any studio or franchise name | `stylized 3D animated feature film look` | IP rule. Non-negotiable |
| `masterpiece`, `award-winning` | delete | Our lint flags it |
| `anime`, `Ghibli`, `2D`, `cel-shaded` | delete | Pulls out of the 3D look |
| `cartoon` | `stylized 3D animated` | Pulls to flat 2D |
| `realistic photo`, `photorealistic`, `live action` | delete | Pulls out of the look entirely |
| `the same woman`, `as before` | the terse tag, verbatim | Back-references resolve to nothing |
| `then`, `and then`, `followed by` | split into two beats | Chained motion renders as a smear |

The last two are ours and they are errors, not taste. The rest are craft.

## Still formulas

Every still prompt is five blocks in this order:

```
[STYLE LOCK]        identical in every beat, character for character
[ASPECT + FRAMING]
[CHARACTER]         protagonist OR problem character OR mascots
[SCENE / ACTION]
[NEGATIVE]
```

The style lock and the negative block live in `SKILL.md` and are pasted in
verbatim. They are not reproduced here, so that there is one copy of each.

### Role A still — the anthropomorphized problem

**Formula:**

```
{STYLE LOCK}

Aspect ratio 9:16, extreme close-up macro shot of {{PAIN_OBJECT}} resting on
{{SURFACE}}. Embedded in the {{OBJECT}} are two oversized eyes with thick lower
lashes and a {{EYE_EXPRESSION}} expression, pupils oversized, {{N}} specular
catchlights, slight tears welling at the corners. A small downturned mouth sits
below the eyes. The {{OBJECT}} has a {{POSTURE}} posture that reinforces its
sadness. Background is soft-focus {{SETTING}} with warm ambient bokeh. The
character looks directly at camera.

{NEGATIVE}
```

**Variables:**

| Pain object | Surface | Eye expression | Posture |
|---|---|---|---|
| clump of dark tangled hair | stainless steel shower drain with soap bubbles | exhausted, half-lidded | drooping over the drain edge |
| cracked flaking fingernail | a pale fingertip with fine skin texture | tearful, brows pinched inward | slightly bent and chipped |
| a worn dingy pillow | rumpled white linen in morning light | grumpy, brows furrowed | sagging in the middle |
| a tired plant leaf | terracotta pot on a kitchen counter | weary, eyes half-closed | wilted, drooping downward |
| a heap of laundry | wicker basket overflowing | overwhelmed, eyes wide and frazzled | precariously stacked |
| a small blob of congestion | inside a tiny nasal passage, soft pink walls | smug, brows raised | wedged in and settled |

**Worked example, congestion blob:**

<!-- eval:still-role-a:start -->
```
Stylized 3D animated feature film look. Soft volumetric golden-hour lighting from
a large window, warm cosy palette of cream, butter yellow, dusty pink and soft
sage. Subsurface scattering on skin, painterly background, shallow depth of field
with creamy bokeh. Characters have large expressive eyes with multiple specular
catchlights, stylized but believable proportions, smooth simplified hands, soft
hair strands with subsurface glow. Rich material detail: waffle-knit fabric
weave, ceramic glaze, glass refraction. Slightly desaturated colour grade.
Vertical 9:16 composition.

Aspect ratio 9:16, extreme close-up macro shot of a small pale green blob of
congestion wedged inside a tiny nasal passage with soft pink walls. Embedded in
the blob are two oversized eyes with thick lower lashes and a smug, settled
expression, pupils oversized, three specular catchlights. A small satisfied mouth
sits below the eyes. The blob has slumped comfortably into the passage like an
armchair. Background is soft-focus pink tissue with warm ambient bokeh. The
character looks directly at camera.

no live-action footage, no photorealistic humans, no uncanny faces, no dead eyes,
no anime style, no 2D cel-shaded look, no flat illustration, no named or
copyrighted animated film characters, no harsh fluorescent lighting, no extra
fingers, no melted features, no warped product labels, no on-screen text, no
subtitles, no captions
```
<!-- eval:still-role-a:end -->

### Role B still — the protagonist reveal

**Formula:**

```
{STYLE LOCK}

Aspect ratio 9:16, medium head-and-shoulders shot of {{PROTAGONIST}} standing in
{{INTERIOR}}. Soft window light from camera-left wraps across the face, backlight
rim through {{LIGHT_SOURCE}}. The {{TERSE_TAG}} holds {{PRODUCT}} at chest height
with {{HAND_POSITION}}, looking down at it with {{EXPRESSION}}, lips slightly
parted. Hair is {{HAIR}}, eyes are {{EYE_COLOUR}} with oversized irises and
multiple highlights. Wearing {{OUTFIT}}. Background includes {{PROPS}} in soft
focus. The product label is identical to the reference image, its text unchanged
and fully legible.

{NEGATIVE}
```

**Variables:**

| Slot | Examples |
|---|---|
| `PROTAGONIST` | "a woman in her late 20s, warm undertone skin, light freckles across the nose bridge" |
| `INTERIOR` | "a sunlit bedroom with sheer linen curtains and an exposed beam ceiling" / "a bright kitchen with pale oak cabinets" |
| `LIGHT_SOURCE` | "sheer curtains" / "a south-facing window" / "a morning kitchen window" |
| `PRODUCT` | the real packaging, from the photo: colour, shape, label text |
| `HAND_POSITION` | "both hands cradling it" / "one hand around the body, the other thumb on the label" |
| `EXPRESSION` | "delighted curiosity, eyes wide" / "gentle surprise, eyebrows raised" |
| `HAIR` | "ash-brown low bun with face-framing strands" |
| `OUTFIT` | "a cream waffle-knit robe over a fitted tank, thin gold necklace" |
| `PROPS` | "a leafy potted monstera, an unmade linen bed, soft morning light" |

The label-hold sentence at the end is not optional whenever packaging is in
frame. Our renders preserve a MARK and destroy TYPE, so a label with no hold
clause comes back as a plausible-looking misspelling of the brand.

### Role C still — the mascot mechanism

**Formula:**

```
{STYLE LOCK}

Aspect ratio 9:16, stylized cross-section view of {{STRUCTURE}}, rendered as a
soft painterly landscape of {{TEXTURES}}. {{N}} small chibi mascot characters
populate the scene, each a 2 to 3 inch tall ivory-white matte blob with a smooth
rounded body, tiny black-dot eyes with one highlight each, soft pink cheeks and
small simple limbs. They are {{MASCOT_ACTION}}. {{ENERGY_VISUAL}} connects the
mascots and traces through the structure, showing the mechanism working. Soft
warm interior lighting with a golden ambient glow.

{NEGATIVE}
```

**Variables, by what the product claims:**

| Claim | Structure | Mascot action | Energy visual |
|---|---|---|---|
| Builds collagen | cross-section of skin layers, epidermis over dermis, a hair follicle descending | pulling glowing collagen strands taut and weaving them into a lattice | golden energy lines linking strand nodes |
| Strengthens nails | inside a nail bed with keratin layers, capillaries below | stacking and stitching keratin scales into a smooth shield | crystalline keratin layers forming |
| Supports gut | cross-section of intestinal villi with a friendly microbiome | tending tiny gardens between the villi | soft pink-green waves rolling through |
| Soothes joints | inside a knee joint with cartilage and synovial fluid | smoothing cartilage with tiny tools, applying a glowing gel | a swirling teal halo around the joint |
| Hydrates hair | cross-section of a single hair shaft with cuticle scales | smoothing lifted cuticle scales down like roof shingles | iridescent droplets soaking in |
| Clears a blocked nose | cross-section of a nasal passage, soft pink walls, a pale green blockage | guiding the blockage out along a gentle channel | a soft blue airflow ribbon opening up |

**Worked example, collagen:**

```
{STYLE LOCK}

Aspect ratio 9:16, stylized cross-section view of human skin layers, pale peachy
epidermis on top, dermis below filled with woven golden collagen fibres, a hair
follicle descending on the right. Rendered as a soft painterly landscape of warm
ivory and gold tones. Four small chibi mascot characters populate the scene, each
a 2 to 3 inch tall ivory-white matte blob with a smooth rounded body, tiny
black-dot eyes with one highlight each, soft pink cheeks and small simple limbs.
They are pulling glowing golden collagen strands taut and weaving them into a
tight lattice, one mascot at each anchor point. Glowing golden energy lines
connect the mascots along the collagen network and pulse softly. Soft warm
interior lighting with a golden ambient glow.

{NEGATIVE}
```

### Role D still — the CTA frame

**Formula:**

```
{STYLE LOCK}

Aspect ratio 9:16, medium shot of {{TERSE_TAG}} standing in {{SAME_INTERIOR}},
facing camera directly with a warm confident smile, eyes bright. Holding
{{ONE OR TWO packages}} at chest height, one in each hand, labels turned cleanly
toward camera. Soft window light from camera-left, gentle backlight rim.
Background includes {{PROPS}} in soft focus. The lower third of the frame is
empty negative space. The product label is identical to the reference image, its
text unchanged and fully legible.

{NEGATIVE}
```

The empty lower third is what the caption sits in. Ask for it here rather than
discovering in Gate 8 that every caption lands on the protagonist's chin.

**This frame is not the end card.** The end card is the real product photograph,
composited over the last beat in Gate 7. See `SKILL.md`.

## Animation formulas

Six things every beat prompt says, in this order:

```
[BEAT INTRO]      what this clip is, and the style anchor
[SUBJECT LOCK]    the character, described to match the still exactly
[ACTION]          ONE primary motion, with timing in seconds
[CAMERA]          framing and movement
[STYLE]           the style lock, verbatim
[AUDIO]           SYNC line and ambience, OR the word "voiceover"
[CONSTRAINTS]     continuity plus the negative block
```

**Write them as flowing prose, not as labelled fields.** The six labels are
headings for the author. Our renders read prose, and a prompt shaped as
`Subject: ... Action: ...` risks the labels arriving as literal on-screen text;
our own prompt lint flags the shape for that reason. Cover all six blocks in
that order, in sentences.

**Aim for 100 to 260 words.** Under a hundred and the render fills the gaps with
its own ideas; over about 260 and the later clauses stop landing, which is how a
beat comes back with the camera move and none of the action. The worked examples
below sit in that band and are the length to copy.

### The AUDIO block is where SYNC and VO are decided

This is the one place our doctrine and the source genre part company, and it is
worth stating plainly:

- **A SYNC beat** carries its spoken line in the prompt, in double quotes, and
  gets NO `POST /v1/voiceovers` take. The render generates the voice and the lip
  sync in the same call.
- **A VO beat** carries no speech in the prompt at all. It says the shot is a
  voiceover shot, and the line is laid in afterwards from `POST /v1/voiceovers`.
- **Never both in one beat.** A narrator line in the prompt plus a VO take of the
  same words plays every line twice.

**At least one beat must be SYNC.** T12 made every beat a VO beat and the result
was three setup shots with a voice talking over them. Role A is the natural SYNC
beat: the problem character speaking its own complaint in first person is the
genre's signature move, and it only works if the voice comes out of the face.

### Role A clip — the problem character speaks

**Target: 4 to 6 seconds.** One short line and a reaction.

**Formula:**

```
3D animated film look, 9:16, animating the character in the reference image.

{{PAIN_CHARACTER}}, described exactly as in the still.

(0 to 2s) The character {{IDLE_MOTION}}, eyes blink once slowly, the mouth
trembles, the body sags a touch more. (2s to end) The character looks up at
camera and says: "{{LINE}}". Small mouth shapes match the syllables, eyebrows
raise mid-line, a single tear slides down at the end.

Camera: locked extreme close-up macro, slight handheld micro-drift, no zoom, no
pan. Shallow depth of field.

{STYLE LOCK}

Audio: a small soft voice with {{TONE}}, intimate close-mic. Faint
{{AMBIENT_SOUND}} in the background.

The character stays visually unchanged from the reference image: same shape, same
eye placement, same surface. {NEGATIVE}
```

**Worked example, congestion blob, 5s, SYNC:**

<!-- eval:clip-role-a:start -->
```
3D animated film look, vertical 9:16, animating the character in the reference
image. A small pale green blob of congestion wedged inside a tiny nasal passage,
two oversized eyes embedded in it, a smug settled expression, a small satisfied
mouth, soft pink walls around it.

From zero to two seconds the blob settles deeper into the passage and its eyes
blink once, slowly. From two to five seconds the eyes lift to camera and the blob
says: "I live here now." Small mouth shapes match the syllables and the eyebrows
raise on the last word.

Camera: locked extreme close-up macro, very subtle handheld micro-drift, no zoom,
no pan. Shallow depth of field with the passage walls softly out of focus.

Stylized 3D animated feature film look, soft warm ambient lighting, subsurface
scattering on the tissue, painterly soft-focus background, slightly desaturated
warm colour grade.

Audio: a small smug voice, nasal and close-mic, with faint breathing ambience
behind it.

The blob stays visually unchanged from the reference image: same shape, same eye
placement, same colour. no live-action footage, no photorealistic humans, no
uncanny faces, no dead eyes, no anime style, no 2D cel-shaded look, no named or
copyrighted animated film characters, no extra eyes, no morphing limbs, no
on-screen text, no subtitles, no captions
```
<!-- eval:clip-role-a:end -->

### Role B clip — the protagonist reveal

**Target: 5 to 8 seconds.**

```
3D animated film look, 9:16, animating the protagonist in the reference image.

{{TERSE_TAG}}, {{full descriptor, verbatim from the cast sheet}}, holding
{{PRODUCT verbatim from the still}}.

(0 to 2s) She looks down at the product with delighted curiosity, lips parting.
(2s to end) She raises her eyes to camera, the smile arriving as the eyebrows
lift.

Camera: locked medium head-and-shoulders, vertical 9:16, subtle handheld
breathing motion. No dolly, no pan.

{STYLE LOCK}

Audio: this beat is a voiceover shot with no speech in frame. Soft room tone,
faint birdsong outside.

The protagonist stays visually unchanged from the reference image: same hair,
same eye colour, same outfit, same freckles. The product label remains perfectly
sharp and identical to the reference image with its text unchanged and fully
legible. {NEGATIVE}
```

Note what the AUDIO block does when the beat is VO: it says so, in words. That is
what stops the render staging a talking shot and paying for a mouth moving with
nothing behind it.

### Role C clip — the mascot mechanism

**Target: 6 to 10 seconds.** The longest beat, because the mechanism needs time
to read.

```
3D animated film look, 9:16, animating the scene in the reference image.

A stylized cross-section of {{STRUCTURE}} with {{N}} small chibi ivory-white
mascot characters, tiny black-dot eyes, soft pink cheeks, simple rounded limbs.
{{ENERGY_VISUAL}} traces through the structure.

(0 to 3s) The mascots work in coordinated rhythm, each one {{MECHANISM}} in the
same beat as the others. (3s to end) The {{ENERGY_VISUAL}} brightens and pulses
outward from their work and the whole structure settles into an even glow.

(final 2s) The mascots pause, look around at the section they finished, and give
each other tiny celebratory glances while the whole structure settles into an
even glow.

Camera: slow gentle dolly-in toward the centre of the action, 9:16 vertical,
focus held on the mascots throughout.

{STYLE LOCK}

Audio: this beat is a voiceover shot with no speech in frame. Soft sparkle sounds
match each mascot motion over a warm ambient hum.

The mascots stay visually consistent: same ivory colour, same proportions, same
eye style. The cross-section geometry does not change. {NEGATIVE}, no
photorealistic anatomy, no horror-style organs, no extra mascot limbs
```

**No photorealistic anatomy is load-bearing.** A cross-section of a body
structure is one bad adjective away from a medical illustration, and a medical
illustration is not an ad.

### Role D clip — the CTA

**Target: 4 to 6 seconds.**

```
3D animated film look, 9:16, animating the protagonist in the reference image.

{{TERSE_TAG}}, {{full descriptor, verbatim}}, facing camera directly, holding
{{ONE OR TWO packages}} at chest height with the labels toward camera.

(0 to 2s) A warm confident smile arrives, the eyes brighten, a small happy head
tilt. (2s to end) She lifts the packages a touch closer to camera and the smile
widens.

Camera: locked medium shot, vertical 9:16, gentle handheld breathing motion. No
dolly, no zoom.

{STYLE LOCK}

Audio: {{either the closing SYNC line in double quotes, OR: this beat is a
voiceover shot with no speech in frame}}. Soft room tone.

The protagonist stays visually unchanged from the reference image: same hair,
same eye colour, same outfit, same freckles, same skin tone. The product label
remains perfectly sharp and identical to the reference image with its text
unchanged and fully legible. The lower third of the frame stays visually clean
for a caption overlay. {NEGATIVE}
```

**The brand name does not go in this beat's spoken line.** It goes on the
composited end card, where you own every character of it. Captions are
transcribed from the audio, and a brand name in the audio is a brand name the
transcript can rename. Measured: a voice-over saying "Owala FreeSip" was
captioned "Olaf. Free sip water", and a run whose transcript read "NoseFrida"
shipped captions reading "Nos Frida".

## Cross-beat continuity rules

1. **Chain each still on the previous one**, not only on the cast sheet. The cast
   sheet carries the character; the previous still carries the location, the
   light and the wardrobe.
2. **The style lock is byte-identical in every prompt.** Do not paraphrase it. It
   is a style anchor, and a reworded anchor is a different anchor.
3. **Reuse exact phrasing** for hair, outfit, eye colour, freckles and skin tone
   in every beat with the protagonist in it. "Ash-brown low bun" in beat 2 and
   "brown hair tied back" in beat 4 are two different people.
4. **Lock the product description once**, in the cast sheet, and paste it into
   every beat that shows the product.
5. **Generate the stills sequentially.** Each one needs the one before it
   approved and passed as a reference.
6. **Animate from the STILL, never from a frame of another clip.** An animated
   frame has already drifted; using it as the next anchor compounds the drift.
7. **Each beat gets its own world.** Five beats in one location at one shot size
   reads as boring however clean the arc is. Change location at least once and
   vary shot size across medium, close and wide.

## Image QA, per still

Before a still is animated:

- [ ] Five fingers on every visible hand, thumb included
- [ ] Both pupils aligned, no drift
- [ ] The label reads correctly and matches the real packaging
- [ ] Same protagonist as the previous beats: hair, eye colour, freckles, outfit
- [ ] No burned-in text
- [ ] 9:16
- [ ] Clean negative space in the lower third, if this frame gets a caption
- [ ] The world is not the previous beat's world

Two retries per beat. If the third attempt still fails, stop and ask.

## Clip QA, per beat

Watch the whole clip, not the thumbnail:

- [ ] Character identity holds from the first frame to the last
- [ ] No finger or limb morphing; count fingers through the clip, not once
- [ ] No label drift; the printed text stays legible and identical
- [ ] Lip sync is plausible on SYNC beats, and no mouth is moving on VO beats
- [ ] No burned-in text or subtitles appeared
- [ ] The primary action in the prompt is the action on screen, and it is ONE
- [ ] The clip's own audio is usable: ambience and in-scene voice, not a music
      bed that will fight the narration

**Which repair depends on which failure, and the two are opposites:**

| The clip failed by | Fix | Why |
|---|---|---|
| Doing two things, smearing the action, glitched physics, a prop that teleported | **Subtract.** A shorter prompt with fewer clauses, one action, the actor named in it. | The render was given more than one thing to resolve and resolved neither. Adding instructions adds candidates. |
| Six fingers, a melted feature, a drifting label, a mascot growing a limb | **Add ONE targeted negative**, naming the artefact exactly: "her hands have exactly five fingers each, no morphing". | An artefact is a thing the render was never told not to do. Shortening the prompt does not tell it. |

Getting this backwards is why a beat gets re-rolled three times. A glitched
action answered with more constraints glitches harder; an extra finger answered
with a shorter prompt comes back with an extra finger.

Two retries per beat either way. If the third attempt still fails, stop and ask.
