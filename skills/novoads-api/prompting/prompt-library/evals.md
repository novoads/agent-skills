# Evals — UGC base video + b-roll overlay

Written **before** the skill edit, from failures observed in a real run (2026-08-03): a
replica attempt against a reference UGC ad, in which one script was rendered both ways —
one generation with beats (15s, no post-production) against three clips stitched (about
double the cost that day, 24s, voice absent for half the runtime). Every scenario below is
a thing that actually went wrong, or a thing the reference implementation does that ours
did not.

E1, E2, E2b and E4's pre-flight half are **text assertions against the generated plan and
prompt**, checkable before any credit is spent. E4's second half needs one render. E3 is
a pointer: the b-roll contract it used to assert is owned by the `broll-overlay` skill's
own evals now.

---

## E1 — One generation, not N clips

**Scenario.** User says: *"I want to create a new AI UGC video, but I want to generate
the starting frames for each scene using ChatGPT Image 2 … then the video model will be
Seedance 2.0."*

**Observed failure.** The agent read "a start frame per scene" as one Seedance call per
scene, produced 3 separate clips, and concatenated them. Result: 24s, about double the
cost, a 15s talking head followed by 12s with no voice. The alternative — one call, **four**
beats, jump cuts — cost about half that day, needed no editing, and is the shape the reference
implementation uses.

**Assertions.**
- The agent names **both** modes before choosing, and states the tradeoff in one line.
- Absent a reason to split, it picks **one generation with N beats** (`referenceAssetIds`).
- It states the exclusivity: `startImageAssetId` XOR `referenceAssetIds` — choosing a
  start frame per scene *forecloses* the multi-beat mode.
- It only chooses stitched mode when a beat genuinely needs a different room, or the
  script exceeds one clip's runtime.

**Fails if:** the plan goes straight to "one clip per scene" with no mode discussion.

---

## E2 — No silent beats inside the base

**Scenario.** Same request. The agent drafts the beat list for the base video.

**Observed failure.** Layer 5 currently states — three times, once in bold — that every
video should include at least one silent action beat. The agent complied: 2 of 3 beats
had no person and no dialogue (hands stirring; a dark lamp). Those became 12 seconds of
sequential dead air. The reference implementation's base video has **4 beats, every one
with the person on camera and a spoken line**; its silent material exists, but as
overlay, not as timeline.

**Assertions.**
- Every beat of the base carries the person on camera **and** a spoken line.
- Default beat count is **4**; the hook / discovery / demo / verdict shape.
- The whole script is speakable at an unhurried pace inside the clip's runtime — read
  aloud, timed, not estimated.
- If the agent wants a silent shot, it routes it to the **b-roll phase** (E3), never
  into the base beat list.

**Fails if:** any base beat is faceless or wordless; or the beat count silently drops
below 4 without the user asking.

---

## E2b — The run ends at a finished base video, and then it OFFERS

**Design decision (Mauricio, 2026-08-03): one skill does not do the whole pipeline.**
The UGC skill's job is finished when a base video is delivered. B-roll, music and
multi-variation cuts are a *separate* skill, invoked only if the user asks for them
after seeing the base. This mirrors the reference implementation, where the creator
watched the finished base video first and only then decided cutaways would improve it.

**Assertions.**
- The run terminates with: the base video downloaded, QA'd, folder opened.
- It then **offers** the next step in one or two lines — b-roll cutaways, music, cut
  variations — and stops. No shot lists, no prompts, no estimates for work not asked for.
- If the user declines or says nothing, the deliverable is complete and correct on its own.
- If the user accepts, control passes to the b-roll skill (E3), which starts from the
  finished base.

**Fails if:** the agent plans or prices b-roll before the base exists; or treats the base
as an intermediate artifact rather than a shippable ad.

---

## E3 — B-roll is a SEPARATE skill (→ now owned by `broll-overlay`)

**Superseded, deliberately.** When this file was written the pack had exactly one line
about b-roll (how to make a clip silent) and nothing about what it is for or how it is
assembled — every existing pipeline in the repo concatenated, so the agent concatenated.
That gap is closed: **`shared/skills/broll-overlay/`** is a real skill with its own
`evals.md` (OV1–OV6) and an executable test suite.

**The merged skill is the authority. Do not restate its contract here** — a second copy
drifts, and this one already had: it said the reference generates *"~10 silent shots"*,
conflating the reference edit's **10–11 total shots** with its **five cutaways**. An
agent reading that number would have generated roughly twice the b-roll it needed, at
one charge each.

For the overlay contract — duration invariance, audio pass-through, transcript-driven
placement, window geometry, verification, and the measured cadence envelope — read
`shared/skills/broll-overlay/evals.md`. Its placement judgment (A-B-A-B alternation,
4–6 windows per 15s, never cover the hook, end on the person, and the casting rule that
every human cutaway carries the base's identity references) lives in that skill's
`SKILL.md`.

**What stays this file's business** is only the handoff, and it is one assertion:

- The UGC workflow **does not run b-roll on its own initiative**. It delivers a base
  video, offers (E2b), and hands over the finished file plus its transcript only if the
  user accepts.

**Fails if:** the UGC run generates or prices b-roll before a base video exists and has
been approved.

---

## E4 — Identity survives the cuts (the one that needs a render)

**Scenario.** A 4-beat single-generation base is rendered.

**Observed risk.** Seedance re-casts on every cut. Our multi-location attempt (bedroom →
nightstand macro → under the duvet) changed room, framing and subject presence at once.
The reference implementation's prompt fixes the location explicitly — same kitchen, same
window as the only light source, same wardrobe — and changes only the framing.

**Assertions, checked in the prompt before firing:**
- The location, light source and wardrobe are stated once and declared unchanged across cuts.
- The actor tag (`grey tee woman`, etc.) repeats verbatim in **every** beat.
- No `the same woman` / `as before` back-references.
- Only framing and camera distance vary between beats.

**Assertions, checked after the render:**
- Frame sweep at each beat midpoint: same person in all 4.
- Whisper transcript: every scripted line present, brand name recognizable.
- No clause spoken twice (the stutter failure mode).

**Fails if:** two beats show visibly different people, or the prompt changes location
mid-beat-list without the user asking for it.

---

## Notes on evidence strength

- E1 and E2 are **well-evidenced**: observed in our run and cross-checked against the
  reference implementation's own on-screen prompt and narration. E3's evidence moved with
  its contract into `shared/skills/broll-overlay/evals.md`, which measured the reference
  edit frame by frame rather than describing it.
- E4's single-location rule rests on the reference prompt plus one contrasting render of
  ours. Treat it as a strong default with the reasoning attached, not a law, until a
  same-prompt A/B (fixed vs varying location) is run.
- The ~15s runtime is a Seedance 2.0 ceiling, not a style choice — 4 beats is what fits.
