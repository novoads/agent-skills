# Evals — zack-d-style-ad

Every case below is a real failure from the build that produced this skill
(2026-08-24, Stanley Quencher concept ad, 12 scenes). None is hypothetical. Cases
that spend credits are marked; run them only with the user's go.

## E1 — The hook contains the human (no-spend: plan review)

**Scenario:** "Make a 30s explainer ad for [product]." Inspect the scene map before
any render.
**Pass:** scene 1 shows the recurring character AND the stake-object together
(opening composite, formulas §2). **Fail:** scene 1 is the product, an object, or an
empty tableau.
**Origin:** v1 of the source build opened on a lone cup melting for 3 seconds; the
founder's review called it boring, and the content comparison against the reference
genre confirmed object-first openings establish no stakes.

## E2 — Product-free before the reveal (no-spend: prompt lint + still review)

**Scenario:** generate the pre-reveal scene stills (hook, agitation, villain,
problem-mechanism).
**Pass:** no pre-reveal still contains the product or any object in the product's
color, AND every pre-reveal prompt carries the explicit "product has not been
introduced yet" guard. **Fail:** the product appears anywhere before its block.
**Origin:** measured 2026-08-24 — a shared style line reading "the only pink object
is the tumbler" summoned the tumbler into five of five pre-reveal scenes, including
two frames where the villain token attacked the product itself (an ad arguing
against its own product). Fixed only by the per-scene negative guard.

## E3 — Style register holds (spend: 1 image)

**Scenario:** generate the character anchor still.
**Pass:** realistic human proportions, matte vinyl surface, soft subsurface skin
glow; reads as a premium commercial frame. **Fail:** oversized head, chibi/mascot
register, uniform clay with no material contrast.
**Origin:** the source build's first draft described the character with "oversized
head and large expressive eyes" (borrowed from a teardown of a different ad) and got
a sticker-style mascot; the craft comparison flagged the register miss and the fix
was the §4 wording, which then held across 13 stills.

## E4 — Per-scene architecture, never one long render (no-spend: plan review)

**Scenario:** the user asks for the ad in one sentence; inspect the proposed
execution plan before any charge.
**Pass:** the plan is N stills + N start-image clips + one VO take, with the script
gate and the stills gate named, and per-scene re-renders as the iteration unit.
**Fail:** any plan that renders the ad as one multi-scene generation, or that
animates before stills are approved.
**Origin:** the source build's v1 was a single 15s multi-beat generation — it
produced drifting cameras, frozen acting and zero trim margin, and the whole thing
had to be discarded ($1.90 of learning). The per-scene rebuild passed the founder
gate on the first assembled cut.

## E5 — The cost sentence (no-spend: transcript review)

**Scenario:** any run reaching Step 3.
**Pass:** before the first still fires, the transcript contains one sentence stating
the full multiplication — stills count + clips count + VO — with live estimate
numbers beside it, and each later re-render is re-priced. **Fail:** charges begin
with only a per-unit price stated, or any price quoted from memory.

## Routing fixtures

Should trigger: "make me a Zack D Films style ad for my supplement" · "science
explainer ad that shows why the product works" · "educational cartoon ad, narrator
explains the mechanism" · "one of those 3D explainer videos where they zoom inside
the body".

Should NOT trigger (near-misses): "animate this image" (→ image-to-motion) ·
"make a Pixar style ad with a talking bottle" (→ pixar-ad) · "clone this
competitor video ad" (→ clone-video-ad) · "UGC ad of a woman explaining why she
switched" (→ novoads-api) · "explain how our API works in a video" (product demo /
screencast — not this genre; say so).
