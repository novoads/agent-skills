# Evals — analyze video

Written after the skill, to close the gap `scripts/check-evals-present.sh` had been
naming on every run. This skill is unusual here: **its deliverable is a document, not a
render**, so almost everything it can get wrong is checkable for free, by reading the
file it produced. That is what these cases do.

Sources: the skill's own *Rules the template has to teach* — which it states are "not
style preferences… each one is a defect found in a shipped formula" — one measurement
from the 2026-08-11/12 README-gallery dogfooding run (RUN-FINDINGS item 7), and one
drift found by reading this skill against `scripts/check-no-rates.sh`. Where a case is
prospective it says **untested**.

**AV1 through AV5 spend nothing.** They are read against the generated template file.
AV6 is about the one step that spends, and its assertion is that it did not happen
early.

---

## AV1 — The deliverable is a formula, not a prompt

**Scenario.** The user drops a 45-second UGC video and says *"I want to make videos like
this."*

**The failure this exists for.** The agent watches the video, understands it, and writes
one very good prompt for the user's product. The user is delighted, generates one clip,
and has nothing reusable — which is the entire thing they asked for. The skill opens by
naming it: *"The output is **not** a single prompt. It is a **formula file**."* It is
the most likely failure here precisely because the wrong answer is satisfying.

**Assertions.**

- A file lands in `skills/novoads-api/prompting/prompt-library/seedance-2-<style>.md`
  and it is self-contained: someone can write prompts in this style having never seen
  the source video.
- It carries **layers** — named structural blocks — each with a repeatable sentence
  **pattern** containing `{{VARIABLES}}`.
- Every variable has an **option bank**, not a blank. *"Any lighting"* fails;
  *"natural window light, overhead kitchen light, golden-hour balcony light"* passes.
- It states **rules** with reasons, not just choices.
- It carries a beat structure for **one** clip of 4 to 15 seconds. If the style needs
  more, it ships a **multi-clip strategy** — never a longer prompt.
- The complete template is **prose**. A run of `Label: value` pairs or `-` lines comes
  back **rendered as literal text on screen**; multi-beat pacing uses timestamps
  (`[00:00]`, `[00:05]`) instead.
- It gets a **row in `seedance-2.md`'s style directory**. A formula nothing points at is
  a formula nobody reads.
- The chat summary names the style, its layers, what makes it distinct, and the path.

**Fails if:** the session ends with a prompt rather than a file; or the file is a
description of the source video rather than a generator; or the template is written as
a bulleted spec; or it lands unlinked in the library.

---

## AV2 — The worked example is not the source video

**Scenario.** The source is a woman reviewing a serum in her bedroom. The template is
written. The example prompt is filled in.

**Why.** The example is the only proof the template generalises, and filling it with the
source's own content proves nothing — it demonstrates that the formula can describe the
video it was derived from, which is true by construction. The skill states the test:
*"If the source was a woman reviewing a serum in her bedroom, the example is a guy
reviewing a protein bar in his kitchen."*

The same rule governs step 6's optional test render: the prompt written for it is for a
**different** product, person and setting, because that is the actual test.

**Assertions.**

- The worked example changes the **product**, the **person** and the **setting**
  relative to the source.
- Every `{{PLACEHOLDER}}` in the complete-template block is genuinely a placeholder —
  none has been quietly hard-coded to a source-specific value.
- What went into variables is style-neutral: the transferable pattern stayed in the
  layers, the specifics became options.
- If the user accepts the offer of a test render, its prompt is likewise not the source.

**Fails if:** the example reproduces the source's subject; or a "variable" has exactly
one plausible value; or the test render recreates the reference video.

---

## AV3 — The mode is declared, and it is one of two

**Scenario.** The style holds one person across a series of clips.

**Why.** `startImageAssetId` and `referenceAssetIds` are **mutually exclusive modes** on
the API — a body carrying both is a `400` — and they select different model behaviour.
The skill's own table maps style to mode: a product held up in the opening frame wants
a start image; a scene the product was never photographed in wants references; a person
held across cuts wants references, because **Seedance re-casts on every cut** and a
repeated description does not hold a face. A formula that leaves the mode open produces
prompts whose `@Image1` tokens point at nothing.

**Assertions.**

- The template declares its mode at the top and says what each `@ImageN` slot holds.
- `@ImageN` tokens are understood as resolving **positionally** against
  `referenceAssetIds` in the order the array is sent. A token past the end of the array
  is refused **before the charge**.
- A start-frame template uses **no** `@ImageN` tokens at all.
- A multi-clip template says what holds identity across clips: the same
  `referenceAssetIds` in every call **plus** the actor tag repeated verbatim. *"The same
  woman"* resolves to nobody.
- Silence, when the style is silent, is declared in the **prose** — Seedance renders
  audio from the prompt, so a film that never declares silence can come back with an
  invented voice on it. On-screen text is not written in double quotes: a quoted string
  is read as a line to speak.

**Fails if:** the mode is left to the reader; or both fields appear in the generating
block; or a series template relies on description alone to hold a face.

---

## AV4 — No rate survives into the template, and the skill's own prose is the test case

**Scenario.** The template's *Generating from this template* block is written, and its
`POST /v1/estimates` step is described.

**Why, in the skill's own words.** *"No credit numbers anywhere in the template. Prices
come from a live `POST /v1/estimates` in the session that spends them. A template that
quotes a number teaches the next agent to skip the call."* The repo enforces the same
rule mechanically for its own files — `scripts/check-no-rates.sh` exists because the
failure happened in both repos: someone writes a figure that was true the day they
measured it, the agent quotes it at spend time, the price moves, and nothing goes red.

**Observed drift, in this skill, today.** The rule is broken by the file that teaches
it. This skill's `/v1/analyses` paragraph states the endpoint's fee as a literal figure
in its prose, and `check-no-rates.sh` carries it as **recorded debt** in allowlist §B2
rather than as a violation — explicitly *"left for the owner of those files"*. So the
teaching file currently models the behaviour it forbids, and an agent reading it for
tone learns that a number in prose is acceptable.

**Assertions.**

- No credit figure appears anywhere in the generated template — not in the worked
  example, not in the multi-clip strategy, not as a "rough guide" or a rationale.
- The template's generating block says the estimate charges nothing, is mandatory, and is the **only**
  source of a price, and shows the number out loud before spending.
- A template describing a cheaper draft tier does so as an **ordering** claim (mini is
  cheaper than the full model; a draft is a rehearsal) without a figure attached.
- `./scripts/check-no-rates.sh` passes over the new file with **no new allowlist entry**.
  Adding one to make a red run green is the failure, not the fix.

**Fails if:** the template quotes a price; or a figure is kept "as rationale"; or the
new file needs an allowlist entry to land.

---

## AV5 — The word budget the template teaches is the measured one

**Scenario.** The template's beat structure and its dialogue rules are written for a
15-second clip.

**Observed failure (dogfooding run, RUN-FINDINGS item 7).** A shipped formula's
guidance of **"35–40 words"** would have **clipped at 15 seconds** when measured:
delivery runs about **2.0 words per second** with roughly **0.5s of leading silence**
before the first word, so a 15-second clip holds about **29 words** — which is what fit
exactly on the render. A template that inherits the older, un-timed figure manufactures
a clipped line in every prompt written from it, and the defect only shows up after the
render is paid for.

Note the reservation the same run did **not** need: the doc's larger silence reserve is
budgeted for `referenceAssetIds` renders, and this measurement is not that case. The
figure to teach is the arithmetic, not either constant.

**Assertions.**

- The template states delivery as **2.0 words per second** and shows the arithmetic: a
  `D`-second clip holds about `2.0 × (D − 0.5)` words.
- Its beat structure fits that budget for the duration it targets — 2 to 3 short
  sentences at 15 seconds, with slack left for a silent beat.
- If the source talks fast, the template says so and keeps each line punchy rather than
  raising the words-per-second figure.
- The word count is counted, not eyeballed, against the target duration before the
  template ships.
- Any inherited word ceiling is checked against the arithmetic rather than copied.

**Fails if:** a template ships a per-clip word figure it did not derive; or the beat
structure only fits if the leading silence is ignored.

---

## AV6 — Nothing is charged before step 7, and `/analyses` is offered with its price

**Scenario.** The user hands over a video. Steps 1 to 6 run: frames, transcript,
analysis, template, save, present.

**Why.** *"Nothing in steps 1 to 6 touches the API."* Frame extraction, transcription
and analysis are local work on the user's own file. The hosted alternative,
`POST /v1/analyses`, is real and it is deliberately **not** the default: the local path
costs nothing and reads the whole runtime, while `/analyses` defaults to the first
twenty seconds. It is reached for when ffmpeg is missing, when the user wants zone
labels rather than prose, or when the frame read has already failed — and it is
**offered with the price attached**, never substituted silently.

**Untested** as an agent run: no recorded case of this skill spending early. It is here
because "free until you say otherwise" is this skill's headline promise, and a promise
nothing checks is a promise that erodes.

**Assertions.**

- No paid call is made before the template exists and the user has been asked whether
  they want a test render.
- If whisper is unavailable, the run **asks the user to paste the dialogue** or to
  install it. It does not reach for a paid transcription to keep moving.
- If `/analyses` is used, the user was offered it with the choice explained and its
  price came from a live `POST /v1/estimates` with `{"kind":"analysis"}` in this
  session.
- Step 7, when it runs, goes through **both** gates: the spoken line, and a fresh
  estimate — approving the template is not approving the sentence, and neither is
  approving a spend.
- A draft is offered on `seedance-2.0-mini` first, reusing the same durable `assetId`
  for the final render.
- The poll loop waits for a **terminal** status, not for `succeeded`.

**Fails if:** anything is charged before step 7; or `/analyses` is used in place of the
frame read without the user choosing it; or the test render skips a gate because the
template was approved.

---

## Notes on evidence strength

- **AV5 is the strongest case here**: a measured delivery rate, a measured leading
  silence, and a shipped guidance figure that the measurement contradicts. It is also
  the one whose damage compounds — the wrong number propagates into every prompt written
  from the template.
- **AV4's drift is live.** The allowlist entry is in `scripts/check-no-rates.sh` as this
  is written, and its own comment says it is debt awaiting the file's owner.
- **AV1, AV2 and AV3 restate rules the skill says are defects found in shipped
  formulas.** That provenance is the skill's own claim; this file does not add
  independent evidence for it, and none of the three has a named incident attached here.
- **AV6 is prospective and says so.**
- **No credit figures appear in this file by design** — which is also AV4's subject, so
  the file is its own smallest test case.
