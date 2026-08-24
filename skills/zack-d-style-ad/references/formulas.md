# 3D explainer formulas — the genre rules

Read §1 before writing the script, §2–§5 before writing scene briefs, §6 at assembly.

## Contents
- [§1 The eight-block script](#1-the-eight-block-script)
- [§2 Scene density and the sandwich](#2-scene-density-and-the-sandwich)
- [§3 The no-text rule](#3-the-no-text-rule)
- [§4 Accent discipline and the two-token color system](#4-accent-discipline-and-the-two-token-color-system)
- [§5 Scene-brief patterns](#5-scene-brief-patterns)
- [§6 Cut-map assembly recipe](#6-cut-map-assembly-recipe)

## §1 The eight-block script

Write the voiceover as one block of spoken words, built from these blocks in order.
Each block is one to three lines; each line must fit a single 2–3s scene.

1. **HOOK** — a scroll-stopping claim or question that names the audience's world.
   Lead with the mechanism or a specific claim, never a generic benefit. ("Did you
   know most cups kill your ice in under an hour?")
2. **PROBLEM AGITATION** — the pain made specific to daily life, escalating across
   two or three concrete moments. Not "it's annoying"; a 10 a.m. meeting, a lunch
   given up.
3. **VILLAIN** — name the real root cause, delivered as a **calm realization**, not a
   rant: "The problem isn't the ice. It's the single wall." This kills self-blame and
   makes the mechanism the obvious next thought. If the product has no honest root
   cause to name, drop this block and say why — never invent one.
4. **MECHANISM** — problem-mechanism first (how the cause does its damage), then
   solution-mechanism (how the fix physically works). Keep it visual: walls, streams,
   barriers, engines. This is the part the viewer feels smart for understanding.
5. **PROOF** — a number, a study, a crowd. Only claims that survive checking.
6. **PRODUCT** — name it once, positioned as the thing that delivers the mechanism.
   The name is spoken; it is never written on screen.
7. **DREAM OUTCOME** — two or three moments of life with the cause gone. Active verbs.
8. **CTA** — a direct recommendation plus the link. Short. ("Get yours. Link below.")

The emotional path must land in this order: frustration with old solutions → relief
that the cause is now clear → ready to buy. Contractions, spoken rhythm, nothing a
human would not say aloud.

**Revision line, reusable verbatim:** "Revise the script — sharper hook / stronger
villain / simpler words / more agitation / stronger CTA. Keep everything else."

## §2 Scene density and the sandwich

**One spoken line = one scene = one new image.** The genre's pace comes from something
new happening on screen at every line — more scenes rather than fewer. At ~3.2 spoken
words/second and ~8 words a line, a 30s ad is ~12 scenes; a 60s ad is ~22–24.

**The sandwich:** human scenes open the ad (hook + agitation) and close it (dream
outcome + CTA); the mechanism middle belongs to objects and cutaways. The human
carries the emotion, the objects carry the argument. Aim for the character on screen
around **half of total runtime**, doing things — sipping, wincing, striding, carrying —
never posing until the final CTA hold.

**The opening composite:** the first frame shows the human AND the stake-object
together — the explainer object (the failing engine, the melting cube) floats at the
character's chest or beside their head while they act. A human inside the first
second is what separates this genre's hooks from product slideshows.

**The reveal is late.** The product enters at its block (§1.6) and not one scene
earlier. Every pre-reveal still prompt carries: *"The product has not been introduced
yet; no [product color] objects of any kind."* A shared style line that names the
product's color will summon the product into pre-reveal scenes — measured; the guard
is per-scene.

## §3 The no-text rule

No captions, no headlines, no logos, no wordmarks, no UI, no end card. Two reasons:
the narrator carries every word (that is what makes the format feel like a lesson
rather than an ad), and rendered text is the most fragile thing in any generated
frame. Recognition of an unnamed brand comes from silhouette and palette; if the
silhouette cannot carry it, this genre is the wrong tool for that product.

## §4 Accent discipline and the two-token color system

The world is neutral — greys, off-whites, one pale ambient hue for the void. Against
that, exactly three saturated things may exist:

- **The villain token:** one warm accent (e.g. glowing red heat particles) that
  embodies the cause. It is the only warm saturated color in the film.
- **The hero token:** one cool accent (e.g. ice-blue glitter) that embodies the fix.
- **The product**, in its own color, appearing only from the reveal onward — and the
  product's color appears on nothing else in any frame (wardrobe, props, background).

The tokens must **interact with the same geometry twice with opposite outcomes** —
the villain token passes through the old solution's wall but dies against the
product's barrier. That inversion, same asset + opposite outcome, is the visual
argument of the whole ad. Give the product scene one **dark-contrast frame** (deeper
vignette, rim light) so the reveal is the most contrast-rich moment of the film.

Style register, stated in every still prompt: premium 3D animated commercial frame,
matte vinyl surfaces, soft subsurface skin glow, **realistic human proportions with
gentle stylization**. Never "cute", "chibi", "kawaii", "big head", "large expressive
eyes" — any of these drifts the register to mascot in one generation.

## §5 Scene-brief patterns

Per-block composition patterns. Each still prompt = shared style block + one of
these + what is absent.

- **Hook composite:** medium shot, character mid-action with the stake-object
  floating at chest height, its state already decaying (dimming, dripping, cracking).
  Camera slightly low; strong rim light.
- **Agitation:** the character failing at something ordinary. Blurred witnesses as
  negative space read as social pressure without a second character to keep
  consistent.
- **Villain macro:** a clean clinical cross-section — one wall, one pane, one
  membrane — with the villain token streaming through it unopposed. Shallow depth of
  field, calm framing: this is a realization, not an action scene.
- **Mechanism impact:** the same villain token slamming into the product's barrier
  and dying — bursts, ricochets, sparks fading — while the hero token glitters
  untouched beyond the gap. Highest-energy frame in the film.
- **Proof crowd:** a scale-jump wide — many small identical figures, each holding the
  product; glowing rating stars arced above. The product's color, repeated small, is
  the only color in the crowd.
- **Product hero:** the product alone, slow-rotation pose, the film's one
  dark-vignette frame, hero-token rim light.
- **Active payoff:** the character mid-verb with the product — grabbing it from a car
  cupholder, striding with it, using it — motion-forward composition.
- **Point-down CTA:** the character holds the product beside their head and points
  the other index finger straight down at the feed; direct eye contact; held to the
  final frame.

Motion prompts (one per clip, start-image mode): name one action fitted to that exact
still, at most one slow camera move, an explicit end hold, and always the closing
guard — *"Keep every material, color and shape exactly as in the image — no morphing,
no style drift, no new objects appearing. No text."*

## §6 Cut-map assembly recipe

1. **Timings from the VO, not from taste.** Transcribe the finished voiceover take
   (Whisper via the caption-video shared step) and use each line's start/end as its
   scene's slot. Slots of 1.9–4.1s are normal; every slot must fit inside its
   rendered clip (which is why clips render at 4–5s).
2. **Trim + normalize each clip** to its slot, then concatenate:

```bash
# per scene: slot length from the cut map
ffmpeg -y -i clips/c01.mp4 -t 2.74 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1" \
  -an -c:v libx264 -crf 18 -preset fast seg/seg01.mp4
# list.txt: one "file 'segNN.mp4'" line per scene, in order
ffmpeg -y -f concat -safe 0 -i seg/list.txt -c copy video.mp4
```

3. **Lay the audio:** VO at full level from 0.0s; the music bed 18–22 dB under it,
   faded out over the CTA hold (the music-mix shared step owns the loudness
   mechanics). Let the final clip run 2–3s past the last spoken word as the CTA hold.
4. **QA at full attention:** watch the cut once for structure (blocks land in order,
   product invisible until reveal, opening is human) and once for likeness (void,
   register, accent discipline, gapless narration). Fix per scene — one still + one
   clip — and re-assemble; the concat is free.
