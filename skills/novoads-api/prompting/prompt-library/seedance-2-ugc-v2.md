# UGC video prompt formula v2 — one render, four talking beats

**This file does not replace [seedance-2-ugc.md](seedance-2-ugc.md).** That file's
nine-layer formula is the craft and is still the authority on *how a UGC prompt is
written* — person, setting, skin realism, technical flaws, vibe. Read it first.

v2 answers a different question: **what shape should the ad be, and how many API calls
does it take?** Everything here is about structure and mode. Where the two disagree —
and they disagree in exactly one place, silent beats — v2 wins **inside the base video**
and v1 wins everywhere else.

Written from a live A/B (2026-08-03): the same script rendered both ways. One
generation with beats cost **7.0 credits, 15s, no post-production**. Three clips
stitched cost **13.8 credits, 24s**, and left the voice absent for half the runtime.

---

## The two modes, and why the choice is not reversible

Seedance takes a start frame **or** reference images — never both. Sending both is a
`400`. So the mode is chosen the moment you decide how frames are used:

| | **One-shot (default)** | **Stitched (escape hatch)** |
|---|---|---|
| API calls | **1** | one per scene |
| Frames | scene stills as `referenceAssetIds` (`@Image1…N`) | one `startImageAssetId` per clip |
| Cuts | jump cuts **inside** the render | cuts happen at the joins |
| Post | none | trim + concat |
| Identity | earned by the actor tag + a fixed location | guaranteed by each start frame |
| Cost (measured) | 7.0cr / 15s | 13.8cr / 24s |

**Default to one-shot.** Choose stitched only when a beat genuinely needs a different
room, or the script cannot be spoken inside one clip's runtime.

⚠️ **A phrase like "generate a start frame for each scene" silently commits you to
stitched mode.** If a user says that, say so and offer the one-shot alternative before
generating anything — they usually mean "I want control over how each beat looks,"
which one-shot gives them through references.

---

## The base video: four beats, all talking, one location

The deliverable of this workflow is **one finished ad**. Not a set of parts.

**Four beats.** Hook → discovery → demo → verdict. Four is the default because it is what
fits 15s at an unhurried pace — and 15s is the `seedance-2.0` ceiling, not the family's.
`seedance-2.5` renders any integer **4 to 30**. When the ad runs longer than 15s, take
the duration and the tier from `SKILL.md` first, then come back here for the shape.

**Every beat has the person on camera and a spoken line.** No silent beats in the base.

> This is v2's one deliberate departure from v1, which asks for at least one silent
> action beat per video. That advice is right for a clip that stands alone and wrong
> here: inside a base video a silent beat is dead air with no voice under it. Silent
> material belongs in the b-roll pass, laid **over** the base while the voice continues
> (see "What happens after" below). Same footage, different layer.

**One location, held across every cut.** State the room, the light source and the
wardrobe once, and say plainly that they do not change. Only framing and camera distance
vary between beats.

> Why: Seedance re-casts the actor on every cut. Each variable you hold constant is one
> fewer thing it reinvents. In the 2026-08-03 run the multi-location attempt (bedroom →
> nightstand macro → under a duvet) was the highest-risk render of the day; the
> reference implementation this workflow is modelled on fixes the location explicitly.
> Evidence: one contrasting render plus the reference prompt. Strong default, not a law
> — worth a same-prompt A/B when someone has 14 credits to spend on the question.

**The actor tag repeats verbatim in every beat.** `grey tee woman` in beat 1 is
`grey tee woman` in beat 4. Never `the same woman`, never `as before` — a back-reference
resolves to nobody and the estimate flags it.

---

## The hook beat — one shape, every length

The opening beat is engineered, not improvised, and it is written the same way whether
the ad runs 15s or 30s. Four rules, all of them about the first beat.

**1. The opening line names the VIEWER'S situation, never the product.** The default
shape is a **reframe**, which moves the blame off the viewer and onto a mechanism they
had not noticed: *"You're not {{BAD_OUTCOME}} because you {{WHAT_THEY_BLAME_THEMSELVES_FOR}}.
You're {{BAD_OUTCOME}} because {{THE_REAL_MECHANISM}}."* Three escape hatches when the
reframe does not fit the brief: a **label** ("founders who run their own ads"), a
**yes-question**, or an **if-then**. All four name the viewer. None of them names the
product.

**2. One engineered physical action, dramatizing the exact claim of that line.** Not a
gesture and not "looking into camera" — one specific, readable thing a hand does that
makes the claim visible. Give it a **salience command** ("the {{HOOK_PROP}} stays the
brightest, most readable object in the lower third"), let it run for **most of the
beat**, and give the beat an explicit **END STATE**: the frame it has to arrive at.
Models steer toward end states; a beat without one drifts into an invented camera move.

**3. The product is not shown, named or hinted at inside roughly the first quarter of
the runtime** — about **25–30% of the canvas**, expressed as a fraction so it moves with
the duration instead of sitting at a fixed second. At 15s that is ~4s; at 30s, ~8s. The
hook beat itself is the one beat that must not be squeezed: **6s is its floor**, because
an action needs that long to reach a declared end state and still be read at feed speed.
So a 15s ad spends its first 6s on the viewer and has ~9s left for the other three beats.
That is what the hook costs, and it is why a five-beat script does not fit 15s.

**4. Prop discipline.** Every object a beat introduces is **owned by a named hand**, its
count is written as a **digit** ("3 index cards", never "three" and never "some"), and
that count is **re-pinned in every beat the prop appears in** — a prop named once and
carried implicitly multiplies across cuts. Nothing moves unless a hand moves it, and the
ban list ends with the sentence **"nothing appears out of thin air."**

**What this is, and what it is not.** Product-withheld is doctrine validated for
**craft**: it renders clean, and of the opening shapes tried here it was judged the best
of them. There is **no conversion claim** behind it — nothing in this repo has measured
a hook rate, a watch curve or a sale for any opening shape. A product-in-hand opening
stays available and correct when the brief asks for one (a reveal, a drop, an unboxing).
What changed is the default, not the option.

---

## Template — one render, four beats

Fill the `{{VARIABLES}}` using v1's layer guidance for wording, skin realism and flaws.

```
{{DURATION}} UGC style {{CONTENT_TYPE}} video, filmed on smartphone,
{{LIGHTING_SOURCE}}, {{CAMERA_ANGLE}}. {{ACTOR_TAG}}: {{AGE_RANGE}},
{{HAIR}}, {{SKIN_TEXTURE}}, wearing {{CLOTHING}}. {{THEIR_SPACE}} —
{{CLUTTER_DETAIL_1}}, {{CLUTTER_DETAIL_2}}, {{CLUTTER_DETAIL_3}}.
The setting stays the same throughout: {{ROOM}}, {{LIGHT_SOURCE}} as the
only light, {{FIXED_DETAILS}}. Only the framing changes between cuts.

The video opens on the @Image1 framing — {{ACTOR_TAG}} {{HOOK_ACTION}}:
{{ACTOR_TAG}}'s {{NAMED_HAND}} {{HOOK_ACTION_DETAIL}}, and {{HOOK_PROP}} stays
the brightest, most readable object in the lower third. No product in frame.
{{ACTOR_TAG}} says: "{{HOOK_LINE}}"
By the end of this beat, {{HOOK_END_STATE}}.

Quick jump cut — {{ACTOR_TAG}} {{BEAT_2_FRAMING}}, {{BEAT_2_ACTION}}. This is
where {{PRODUCT_DESCRIPTION}} first enters the frame, {{PRODUCT_HANDLING}}:
"{{BEAT_2_DIALOGUE}}"

Quick jump cut to the @Image2 framing — {{ACTOR_TAG}} {{BEAT_3_FRAMING}},
{{BEAT_3_ACTION}}: "{{BEAT_3_DIALOGUE}}"

Quick jump cut — {{ACTOR_TAG}} {{BEAT_4_FRAMING}}, {{BEAT_4_ACTION}}:
"{{BEAT_4_LINE}}"

One continuous voice across every beat, {{TONE_EMOTIONS}}, speaking
steadily from the first frame to the last with no long pauses. Each jump cut
is slightly closer or at a different angle, as if {{PRONOUN}} filmed a few
takes and kept the honest bits.

The product label remains sharp and identical to the reference images,
its text unchanged and fully legible.

The lighting is {{LIGHT_TYPE}} — {{LIGHT_FLAW}}. The image is slightly
imperfect — {{CAMERA_FLAWS}}. Sound is {{AUDIO_SOURCE}} — {{AUDIO_DETAILS}}.
No subtitles, no captions, no text overlays. Every object is placed by a hand
and stays where the hand left it; nothing appears out of thin air.

The overall feel is {{VIBE_ADJECTIVES}} — {{RELATABLE_METAPHOR}}.
Vertical 9:16.
```

**Notes on the tokens.** `@ImageN` refers to the reference array positionally — the
order you send them. Not every beat needs a reference; two or three carry the look and
the rest inherit it. A token pointing past the end of the array is refused before the
charge.

**At least one reference must show the person.** Identity inside this render is earned by
the actor tag, but the reference set has a second job downstream: `broll-overlay` casts
the base actor into every human cutaway by re-sending **the same `referenceAssetIds` this
base used**. A reference set of product-only stills leaves that pass with no identity to
reuse, and Seedance re-casts on every render — which is how one live run put five
white-cast cutaways over a Black base actor (2026-08-04). Keep the references you send
here; they are an input to the next step, not scratch.

---

## Checklist before you price it

- [ ] **Four beats**, each with the person on camera and a spoken line
- [ ] **Hook line names the viewer's situation**, not the product — reframe (default),
      label, yes-question or if-then
- [ ] **One engineered physical action** on the hook beat, carrying a salience command
      and an explicit **END STATE**, running most of the beat
- [ ] **Hook beat ≥6s**, and the product neither shown nor named inside the first
      **~25–30%** of the runtime
- [ ] **Prop counts written as digits** and re-pinned in every beat the prop appears in;
      every object owned by a named hand; the ban list ends "nothing appears out of thin air"
- [ ] **Actor tag verbatim** in all four; no `the same woman` / `as before`
- [ ] **Setting declared unchanged**; only framing varies
- [ ] Script read aloud at an unhurried pace **fits the runtime** — timed, not estimated
- [ ] …and **fills** it: **~2.0 words/sec** of delivered speech, so a 15s ad wants
      **27–30 spoken words**. Measured 2026-08-11: a 29-word script filled a 15s
      `seedance-2.0` render exactly — speech from 0.48s to 14.72s of 15.07s, with no
      tail room left. One render, so treat it as the working figure. The **35–40**
      that stood here was 2.5-words/sec arithmetic, and at that rate the last line
      runs past the end: 35 words needs about 18s, so the verdict beat gets clipped
- [ ] **Dead air is a delivery problem, not a word-count one.** An under-written script
      does render its slack as silence (measured 2026-08-03: 5.9s across 5 gaps in a 15s
      render built from ~27 words) — but 29 words filled the same runtime on 2026-08-11,
      so two words are plainly not what separated them. The variable is pausing, and the
      item below is the fix. Never pad a script to reach a word count: the padding is
      what gets clipped
- [ ] **No "pause after each sentence" instruction.** Correct for a single-shot testimonial,
      harmful across four beats where every pause compounds. Ask for a steady delivery from
      first frame to last instead
- [ ] `@ImageN` tokens ≤ the number of references actually sent
- [ ] Label-hold clause present if the product carries printed text
- [ ] Ratio restated in the prompt (`Vertical 9:16.`)
- [ ] Invented or coined brand name spelled phonetically inside the quotes
- [ ] Priced with a live `POST /v1/estimates`; warnings read and cleared

---

## What happens after: stop, then offer

**The base video is the deliverable.** When it is downloaded and QA'd, the job is done.
Do not plan, price or generate anything further on your own initiative.

Then offer, in a line or two: **b-roll cutaways** laid over the base, **burned captions**,
**background music**, or **variations of the cut**. If the user declines, the ad is
complete and correct as it stands.

If they accept, each is separate work owned by its own skill, and each takes the finished
base as input rather than replacing it:

| Offer | Skill | Contract |
|---|---|---|
| B-roll cutaways | `broll-overlay` | Needs the base **and its transcript** (`POST /v1/transcripts` — one call, no local install; the *captions* endpoint still returns no text). **Overlays**, never extends: final duration equals the base's. A longer output means someone concatenated. |
| Burned captions | novoads API `POST /v1/captions` | A new MP4 with subtitles burned in. |
| Music bed | `music-mix` | Track from `POST /v1/music` on the same key, or the user's own file. Mixed last, over the captioned cut. |

Order matters: b-roll → captions → music. Music is genuinely last, because its script
stream-copies the picture and would otherwise have nothing final to sit under.

---

## Old patterns

- *"The video opens … holding {{PRODUCT_DESCRIPTION}}"* — the old hook beat, with the
  product welded into the opening frame. It left the opening line nothing to do but
  announce a thing the viewer could already see. Superseded by the hook beat above; a
  product-in-hand opening is now something the brief has to ask for.
- *"Every video should have at least one silent action beat"* — v1's rule, correct for
  standalone clips, wrong inside a base video. Silent material moves to the b-roll pass.
- *"One clip per scene, then stitch"* — still valid as the escape hatch, no longer the
  default. It costs roughly double and requires post-production.
- *"Reserve +4s for leading silence"* — measured at 0.44s and 0.0s on start-frame and
  reference renders respectively (n=2), then at 0.515s, 0.529s and 0.482s across three
  more reference renders on 2026-08-11 (n=5). The +4s reserve does not draw in this
  workflow; budget about **0.5s** of leading silence, spend the rest on words, and
  check the render.
