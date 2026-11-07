# Beat formulas — the clay narrative library

The per-beat prompt formulas for `claymation-ad`. `SKILL.md`
owns the pipeline, the style lock, the negative block and the material detail
block. This file owns the eight beats: what each is, the variables it takes, and
worked prompts.

Read `SKILL.md` first. Where a formula below says `{STYLE LOCK}`,
`{NEGATIVE}` or `{MATERIAL}`, paste that block from `SKILL.md` verbatim.

> **Provenance.** The eight-beat narrative arc, the cast-sheet shape, the
> subject-lock fragment technique, the material-detail block and the
> clay-specific QA checklists are adapted from the claymation-ad prompting guide
> in `krusemediallc/arcads-claude-code` (MIT, Copyright (c) 2026 Caleb Kruse /
> Kruse Media LLC). Adapted, not copied: the API mechanics are ours, the studio
> names are stripped under our IP rules, the audio doctrine is our SYNC/VO one,
> and the gates and measured rules are ours. Full notice in `NOTICE.md`.

## Why this genre works, and why it is not the Pixar one

The Pixar ad runs on a want. Someone has a problem, the problem gets a face, the
product resolves it, and the whole thing takes twenty-five seconds because a want
does not need longer.

The clay ad runs on **affection for a person**. A named protagonist, in a
miniature set built for them, noticed by a friend, alone at a window, and then
better. It is slower on purpose, and the extra thirty seconds are not padding:
they are what buys the viewer's attachment before the product is allowed on
screen.

Two consequences for every decision below:

- **The narrator is the storyteller, not a voice-over.** Third person, past or
  present tense, talking about someone the viewer is watching. "Diane had not
  slept through the night since March" is the register. "Tired of restless
  nights?" is not, and it belongs to a different ad.
- **The product arrives late.** Beat 6 of 8. Everything before it is the
  character. An ad that opens on packaging has thrown away what it paid for.

## Subject lock fragments

Write these once, paste them verbatim wherever the character appears. Our renders
re-cast on every cut, so a fragment that gets paraphrased between beats returns a
different sculpt. Do not elaborate them; an elaborated fragment re-casts as
readily as a missing one.

```
PROTAGONIST (full, used in beat 1 and any beat introducing her again):
"Diane, a woman in her late 50s with shoulder-length terracotta-brown wavy
plasticine hair sculpted in distinct ribbon-strands, matte clay skin with
visible thumbprint impressions and deep sculpted laugh lines, warm brown matte
clay eyes set into deep sockets, a sculpted brow furrow. She wears a cream
chunky knit cardigan with visible wool weave over a rust-red blouse, dark wool
trousers and brown leather slippers."

PROTAGONIST (terse tag, 11 to 30 chars, every later beat):
"cream knit cardigan Diane"

SUPPORTING (beat 3):
"Margaret, a woman in her 60s with silver curly plasticine hair with carved
strand grooves, round wire glasses, a sage-green cable-knit sweater with visible
wool weave, matte clay skin."

PRIMARY SETTING (beats 1, 6, 8):
"A sunlit miniature clay kitchen, green-painted wooden cabinets, a red gingham
tablecloth, hand-thrown ceramic cups, a copper kettle on a small stove, potted
herbs on the windowsill, warm tungsten light from a window on camera-left."

SECONDARY SETTING (beat 3):
"A neighbourhood cafe with potted plants, wooden tables and hanging brass
pendant lights."
```

## Cast and continuity sheet

```
PROTAGONIST
- Name, said aloud by the narrator: <e.g. Diane>
- Age band: 30s / 40s / 50s / 60s. This look flatters older faces; use them.
- Distinctive feature: <shoulder-length terracotta wavy hair, deep laugh lines>
- Build: average / petite / sturdy
- Eyes: colour, matte, sculpted lower lids visible
- Outfit: <cream chunky knit cardigan over rust-red blouse, wool trousers>
- Posture cue: <slight forward lean, soft rounded shoulders>
- TERSE TAG (11 to 30 chars, wardrobe-anchored): "cream knit cardigan Diane"

SUPPORTING CHARACTER (beat 3)
- Relationship: best friend / spouse / coworker
- Distinctive feature: <silver curly hair, round wire glasses, sage sweater>
- Age band: similar to or older than the protagonist

NARRATOR (voice-over, never on screen)
- Persona: warm storyteller, mid-pace / wry observer, dry
- Chosen ONCE from `GET /v1/voices`. One voiceId for every line in the ad.

SETTING, primary (beats 1, 6, 8)
- <a small sunlit kitchen with green-painted cabinets, red gingham tablecloth,
   wooden table, copper kettle, potted herbs on the windowsill>

SETTING, secondary (beat 3)
- <a neighbourhood cafe with wooden tables and brass pendant lights>

PRODUCT
- A clay-shaded prop: matte hand-painted label, slightly imperfect form, paint
  that looks applied by hand.
- The real brand and the real label text, from the photo.
- Appears in beats 6, 7 and 8 only, plus the composited end card.
```

**One canvas, three subjects.** The cast-sheet image carries the protagonist in
three emotional states, the supporting character, and the product in two views,
at true relative size. Three designs settled for the price of one image.

## Forbidden words, and what to write instead

| Do not write | Write instead | Why |
|---|---|---|
| any studio or franchise name | `hand-sculpted stop-motion clay look` | IP rule, and the model reaches for their characters |
| `3D rendered`, `CGI`, `digital`, `smooth render` | `hand-sculpted plasticine` | Pulls straight out of the material |
| `subsurface scattering`, `ray-traced`, `glossy` | `matte clay`, `single soft highlight` | These are the Pixar look's vocabulary and they leak it in |
| `cinematic` | `stop-motion clay look` | Our lint flags it |
| `professional`, `stunning` | `polished`, `high fidelity` | Pulls to stock-render gloss, which is this genre's opposite |
| `perfect`, `flawless` | `slightly asymmetric`, `hand-finished` | Our lint flags it, and the genre is built on imperfection |
| `8k`, `4k`, `hyper-detailed` | `visible tool marks` | Our lint flags it |
| `anime`, `cel-shaded`, `2D`, `painted illustration` | delete | Wrong medium entirely |
| `photorealistic`, `realistic photo`, `live action` | delete | Wrong medium entirely |
| `stop-motion judder` in a prompt | the ffmpeg post step in `SKILL.md` | The render cannot control frame rate and the phrase breaks the look |
| `the same woman`, `as before` | the terse tag, verbatim | Back-references resolve to nothing |
| `then`, `and then`, `followed by` | split into two beats | Chained motion renders as a smear |

## Still formulas

Every still prompt is five blocks, in this order:

```
[STYLE LOCK]     identical in every beat, character for character
[ASPECT + FRAMING]
[SUBJECT]        the lock fragment, verbatim
[SCENE / ACTION]
[MATERIAL]       the lines that apply to what is in frame
[NEGATIVE]
```

### Beat 1 — Setup

**Goal:** the protagonist in their own world, before anything is wrong. The
narrator says her name and one defining trait.

```
{STYLE LOCK}

Aspect ratio 9:16, {{WIDE or MEDIUM}} shot of {{PROTAGONIST_FULL}} in
{{PRIMARY_SETTING}}. She is {{EVERYDAY_ACTION}}, {{EXPRESSION}}. Warm tungsten
light from {{LIGHT_SOURCE}}. {{PROPS}} in soft focus around her.

{MATERIAL: skin, hair, eyes, knitwear, wood, ceramic}
{NEGATIVE}
```

| Slot | Examples |
|---|---|
| `EVERYDAY_ACTION` | "pouring tea from a copper kettle" / "folding a wool blanket" / "watering the herbs on the windowsill" |
| `EXPRESSION` | "unbothered, mid-routine" / "quietly content" |
| `LIGHT_SOURCE` | "a window on camera-left" / "a low kitchen lamp" |

**Do not foreshadow.** Beat 1 is the life before the problem, and a protagonist
already looking sad in beat 1 costs beat 2 its entire job.

### Beat 2 — Inciting moment

**Goal:** close on the face as they notice it.

```
{STYLE LOCK}

Aspect ratio 9:16, close-up of {{TERSE_TAG}} looking at {{THE_SIGNAL}}. Her
{{FACIAL_REACTION}}. {{REFLECTION_OR_OBJECT}} occupies {{FRAME_POSITION}}. Warm
tungsten light from camera-left, shallow macro depth of field.

{MATERIAL: skin, hair, eyes}
{NEGATIVE}
```

| Product kind | The signal | Facial reaction |
|---|---|---|
| Skincare | fine lines in a bathroom mirror | brow lifting, a fingertip at the corner of the eye |
| Sleep / stress | a bedside clock reading 3:12 | eyes open in the dark, jaw set |
| Joints | a jar lid that will not turn | a wince held a beat too long |
| Hair | a clay hairbrush with strands caught in it | eyes dropping, mouth going flat |
| Digestion | a plate pushed half an inch away | a hand flat on the stomach, eyes distant |

### Beat 3 — Social validation (the SYNC beat)

**Goal:** someone else says the thing out loud. This is the beat that hurts, and
it is the beat where a mouth moves.

```
{STYLE LOCK}

Aspect ratio 9:16, medium two-shot of {{TERSE_TAG}} and {{SUPPORTING_FULL}}
across {{TABLE_OR_SETTING}} in {{SECONDARY_SETTING}}. {{PROTAGONIST_POSTURE}}.
{{SUPPORTING_POSTURE}}. Warm tungsten light from camera-left.

{MATERIAL: skin, hair, eyes, knitwear, ceramic}
{NEGATIVE}
```

The line belongs to the SUPPORTING character, not the protagonist. A friend
naming the problem is observation; the protagonist naming it is complaint, and
complaint is what the genre spends eight beats avoiding.

**Write it as something a person would actually say.** Casual, unfinished, a
little sideways. "You have not been sleeping, have you" is a friend. "Are you
still struggling with restless nights?" is a brochure with a face on it. The
same rule governs every spoken line in this genre: the narrator may be
composed, the characters never are.

### Beat 4 — Quiet despair

**Goal:** alone. No dialogue at all. The narrator carries it.

```
{STYLE LOCK}

Aspect ratio 9:16, {{MEDIUM or CLOSE}} shot of {{TERSE_TAG}} alone at
{{MIRROR_WINDOW_OR_SINK}}, {{POSTURE}}, looking at {{WHAT}}. The room is
{{DIMMER_LIGHT}}. Nothing else moves in frame.

{MATERIAL: skin, hair, eyes, knitwear}
{NEGATIVE}
```

**Light this beat down.** One stop below beats 1 and 3 is the whole
cinematography of despair in this genre, and it costs nothing.

### Beat 5 — Clay infographic

**Goal:** the mechanism, sculpted. No characters.

```
{STYLE LOCK}

Aspect ratio 9:16, a hand-sculpted clay infographic {{ON_WHAT}} showing
{{THE_MECHANISM}}. {{SCULPTED_LETTERS}} spell "{{SHORT_LABEL}}" in clay above a
{{CHART_FORM}} in plasticine. {{INDICATOR}}. Warm tungsten light, shallow macro
depth of field, the wall texture visible behind it.

{MATERIAL: wood, ceramic}
{NEGATIVE, minus the no-on-screen-text clause}
```

**This is the ONE beat that may carry on-screen text**, and it is short words and
numbers only, sculpted from clay, never a sentence. Drop the `no on-screen text`
line from the negative block for this beat and only this beat. Everywhere else it
stays.

Expect the sculpted letters to come back misspelled and treat it as normal: our
renders carry a MARK and destroy TYPE. Keep the label to one or two short words,
check it at full crop, and if it will not come out clean, composite it.

### Beat 6 — Discovery

**Goal:** the product, found. First time it is on screen.

```
{STYLE LOCK}

Aspect ratio 9:16, close-up of {{PRODUCT}} rendered as a clay-shaded prop with a
hand-painted matte label, sitting on {{SURFACE}} in {{PRIMARY_SETTING}}.
{{TERSE_TAG}}'s hand reaches into frame toward it. Warm tungsten light from
camera-left, shallow macro depth of field. The product label is identical to the
reference image, its text unchanged and fully legible.

{MATERIAL: product packaging, wood, skin}
{NEGATIVE}
```

The label-hold sentence is mandatory whenever packaging is in frame.

### Beat 7 — Transformation

**Goal:** weeks pass and something is visibly better. **One thing.**

```
{STYLE LOCK}

Aspect ratio 9:16, {{MEDIUM}} shot of {{TERSE_TAG}} in {{SETTING}},
{{USING_OR_AFTER}}. {{THE_ONE_CHANGE}}. Everything else about her is unchanged:
same face proportions, same hair, same cardigan, same clay texture. Warm tungsten
light, brighter than the earlier beats.

{MATERIAL: skin, hair, eyes, knitwear}
{NEGATIVE}
```

| Product kind | The one change | What must NOT change |
|---|---|---|
| Skincare | the sculpted crease at one eye corner is shallower | face shape, hair, age |
| Sleep | the under-eye shadow is lighter | everything else |
| Joints | the jar lid turns, the wince is gone | posture, wardrobe |
| Hair | the strand grooves are denser at the crown | face, colour |

**Naming what must not change is half the prompt.** A transformation described on
the whole face returns a younger stranger, and a younger stranger reads as a lie.

### Beat 8 — Resolution

**Goal:** confident, product in hand, lower third clean for the caption, and then
the composited end card.

```
{STYLE LOCK}

Aspect ratio 9:16, medium shot of {{TERSE_TAG}} in {{PRIMARY_SETTING}}, facing
camera with {{WARM_EXPRESSION}}, holding {{PRODUCT}} at chest height with the
label toward camera. Warm tungsten light from camera-left. The lower third of the
frame is empty negative space. The product label is identical to the reference
image, its text unchanged and fully legible.

{MATERIAL: skin, hair, eyes, knitwear, product packaging}
{NEGATIVE}
```

**This frame is not the end card.** The end card is the real product photograph
composited over the tail of this beat in Gate 7. See `SKILL.md`.

## Animation formulas

Six things every beat prompt says, in this order:

```
[BEAT INTRO]      what this clip is, and the style anchor
[SUBJECT LOCK]    the fragment, verbatim
[ACTION]          ONE primary motion, with timing in seconds
[CAMERA]          framing and movement
[MATERIAL]        the lines that apply, because the clip is where clay is lost
[AUDIO]           the SYNC line, OR the words "voiceover shot with no speech"
[CONSTRAINTS]     continuity, clay-held-to-last-frame, and the negative block
```

**Write them as flowing prose, not as labelled fields.** The six labels are
headings for the author. Our renders read prose, and a prompt shaped as
`Subject: ... Action: ...` risks the labels arriving as literal on-screen text;
our own prompt lint flags the shape for that reason.

**The material block belongs in the CLIP prompt, not only the still.** This is
the difference from the Pixar sibling, and it is the single most important clay
rule: the still holds texture and the clip loses it. Repeat the material lines in
every clip prompt and end the constraints with "clay texture held to the last
frame".

### The AUDIO block: SYNC and VO

Same doctrine as the Pixar skill. A SYNC beat carries its line in the prompt in
double quotes and gets NO `POST /v1/voiceovers` take. A VO beat carries no speech
at all and says so. Never both in one beat, or every line plays twice.

In this genre most beats are VO, because the narrator is the form. **Beat 3 is
the SYNC beat**, and if beat 3 was dropped for the 5-beat short, beat 6 is: one
short line to herself when she finds it.

### Worked clip — beat 2, the inciting moment (VO)

<!-- eval:clip-beat-2:start -->
```
Hand-sculpted stop-motion clay look, vertical 9:16, animating the character in
the reference image. Cream knit cardigan Diane, a woman in her late 50s with
shoulder-length terracotta-brown wavy plasticine hair in carved ribbon-strands,
matte clay skin with visible thumbprint impressions and deep sculpted laugh
lines, sits on the edge of a bed in the dark.

From zero to three seconds her eyes are open and fixed on a small clay bedside
clock reading 3:12. From three to six seconds her jaw sets and she looks away
from it toward the window.

Camera: locked close-up at bed height, very subtle handheld micro-drift, no zoom,
no pan. Shallow macro depth of field with the clock softly out of focus.

Skin: matte plasticine, visible thumbprint impressions on the cheeks and
forehead, small sculpting-knife creases at the corners of the eyes. Hair:
sculpted in distinct ribbon-strands of plasticine with individual strand grooves,
slightly stiff and not flowing. Eyes: small matte clay orbs set into sculpted
sockets, a single soft highlight, no wet shine.

Audio: this beat is a voiceover shot with no speech in frame. Faint room tone and
a distant street outside.

Diane stays visually unchanged from the reference image: same face proportions,
same hair, same cardigan, clay texture held to the last frame. no live-action
footage, no photorealistic humans, no uncanny faces, no dead eyes, no smooth 3D
digital render, no glossy surfaces, no ray-traced reflections, no subsurface
scattering, no wet-eye highlights, no anime style, no 2D illustration, no named
or copyrighted animated film characters, no extra fingers, no melted features, no
on-screen text, no subtitles, no captions
```
<!-- eval:clip-beat-2:end -->

### Per-beat animation notes

| Beat | Motion | The trap |
|---|---|---|
| 1 Setup | one everyday gesture, completed | two gestures glitch the physics |
| 2 Inciting | the reaction only, no reaching | a reach plus a reaction is two actions |
| 3 Social | the supporting character speaks, the protagonist reacts | both speaking is two actions and unusable audio |
| 4 Despair | almost nothing: a breath, an eye drop | motion here breaks the beat |
| 5 Infographic | a single indicator moving, or a slow push in | animating clay letters garbles them further |
| 6 Discovery | the hand reaches and stops on contact | picking it up and turning it is two actions |
| 7 Transformation | one continuous action in the after-state | do not animate the transition itself |
| 8 Resolution | the smile arrives, the product lifts | keep the lower third clear |

## Cross-beat continuity rules

1. **Chain each still on the previous one**, not only on the cast sheet.
2. **The style lock is byte-identical in every prompt.**
3. **Subject-lock fragments are pasted, never paraphrased.**
4. **The primary setting is the same set in beats 1, 6 and 8.** Reusing it is
   what makes the miniature world feel real rather than assembled.
5. **Generate the protagonist stills sequentially**, each approved before it
   anchors the next. **Beat 5 is the exception**: the clay infographic has no
   character in it, so it needs no continuity anchor and can be rendered at any
   point, including alongside the others. If the brand already has a hero image
   of its protagonist, skip the cast sheet entirely and pass that image as the
   reference into every character beat: it saves a render and it is the only way
   to match a character the brand has already published.
6. **Animate from the STILL, never from a frame of another clip.**
7. **The light warms across the arc.** Beats 1 to 4 cooler and lower, beats 6 to
   8 warmer and brighter. It is the cheapest storytelling in the file.

## Image QA, per still

- [ ] Clay texture is there: thumbprint and tool marks visible on faces and hands
- [ ] No smooth digital render leaking in
- [ ] Knit fabric reads as real wool weave, not painted-on stripes
- [ ] Eyes are matte, one soft highlight at most, no wet-eye multi-catchlight
- [ ] Hair shows individual carved strand grooves
- [ ] Wooden and ceramic props are hand-finished and slightly irregular
- [ ] Same face proportions, hair and outfit as the previous protagonist beat
- [ ] The product label paint looks hand-applied, matte and slightly uneven
- [ ] No burned-in text, except beat 5's sculpted letters
- [ ] 9:16
- [ ] Clean negative space in the lower third on beat 8
- [ ] Five fingers on every visible hand

Two retries per beat. If the third still loses clay texture, change the beat, not
the retry count: a tighter material block and a simpler frame recover it more
often than another roll does.

## Clip QA, per beat

Watch the whole clip. **Watch the last second especially.**

- [ ] **Clay texture survives to the final frame.** The smoothing tendency is the
      number one risk in this genre and it arrives late in the clip, not early
- [ ] Knit fabric stays woven wool
- [ ] Eyes stay matte, no wet sheen developing mid-clip
- [ ] Identity holds from the input still to the last frame
- [ ] The product label paint stays hand-applied, no digital crispness
- [ ] Beat 7's improvement is localised to the one named thing
- [ ] Mirror and reflection surfaces move correctly on beats 2, 4 and 7
- [ ] No burned-in text or subtitles appeared
- [ ] Lip sync is plausible on the SYNC beat, and no mouth moves on VO beats
- [ ] One action, and it is the one in the prompt

**The repair depends on the failure.** A beat that did two things or smeared its
action gets a SHORTER prompt: fewer clauses, one action, the character named in
it. A beat that grew a sixth finger, melted a feature or drifted a label gets ONE
added negative naming that artefact exactly. Getting it backwards is why a beat
gets re-rolled three times.

Clay adds a third case, and it is the common one here: **texture lost by the end
of the clip** is neither. Re-render with the material block restated in full and
"clay texture held to the last frame" in the constraints. That is an addition,
not a subtraction, because the render was never told to hold it.
