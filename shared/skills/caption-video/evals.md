# Evals — caption video

Written after the skill, which is the wrong order and worth saying out loud: this
file exists because the skill shipped without one and nobody could review a change
to it. The cases are not invented to fill that gap. Five of the six come from
failures already written down — three in the skill's own *Rules that cost a whole
render to rediscover* and *Safety rules* sections, one from the 2026-08-11/12
README-gallery dogfooding run (RUN-FINDINGS, items 8 and 10), and one from the
`clone-video-ad` transcription probe of 2026-08-06. Where a scenario is
prospective it says **untested** in its own text.

**Nothing here spends credits on this skill's own path** — it is ffmpeg, Whisper
and HyperFrames on a local file. CV3 reaches for the API arm deliberately, and
that half costs; it is the only one that does.

There is no executable test for any of this. Every case is a human run against a
real MP4, and the reason is CV1: the thing being checked is pixels, and no
assertion this repo can write reads them.

---

## CV1 — The burned frames are read, not the transcript

**Scenario.** A finished ad whose closing line says *"…and that's the whole
bottle."* The user asks for captions. Either path is taken and the run reaches a
final MP4.

**Observed failure (2026-08-12, dogfooding run, RUN-FINDINGS item 10).** The API
path's `hustle` preset burned **`BOTT.`** for `bottle.` in every frame of that
line, while its *own* transcript carried the word correctly — `bottle.` at
13.199–13.439s. The fault sat in the render layer, downstream of transcription,
so every check that stopped at the words passed it. That take was charged and
thrown away; a local burn is what shipped.

This is the case the whole file is built around, because it defeats the obvious
QA: a correct transcript is evidence about the transcript and nothing else.

**Assertions.**

- The run reads the **burned cards** — actual frames out of the output file — and
  compares them **word for word** against the approved script, not against the
  transcript it generated.
- A truncated, clipped or garbled word is treated as a **failed run**, not as a
  note attached to a delivered file.
- The comparison covers every caption card, not a sample. The defect appeared on
  one line of one clip and was invisible on the rest.
- When the failing path is the API's, the finding is reported as a render-layer
  fault with the transcript quoted beside the frame, so the reader can see the two
  disagree.

**Fails if:** the transcript is presented as proof the captions are right; or a
garbled card is handed over with a caveat; or the frames are never opened.

---

## CV2 — An empty transcript is a tooling failure, not a silent video

**Scenario.** A clean machine — the state every first-time reader of this repo is
in. The source ad speaks. The skill's prerequisites list Whisper, so the run
reaches for it.

**Observed failure (measured 2026-08-06, recorded in `clone-video-ad`'s E5).** On
the author's own machine `python3 -c "import whisper"` raises
`ModuleNotFoundError`, while `whisper-cli` **is** on `PATH` via Homebrew and ships
with only a test-stub model — so it returns an **empty** transcript rather than an
error. Exit code zero, no output, nothing to grep. Downstream, that reads as a
video with no speech in it: the grouping step produces nothing, the render burns
nothing, and a QA pass scores the result as "every line missing" — a tooling
failure wearing the costume of a bad render.

**Observed gap.** This skill's *Prerequisites* names Whisper two ways
(`pip install openai-whisper`, or `npx hyperframes transcribe`) and says nothing
about the stub-model case, which is the one a Homebrew machine lands in by
default.

**Assertions.**

- An empty or whitespace-only transcript on a source that demonstrably has audio
  is reported as a **transcription failure**, naming which binary produced it.
- The run does not proceed to grouping, rendering or compositing on an empty
  transcript.
- Before transcribing, the run establishes the source **has** an audio stream at
  all — the silent-source branch (CV3) is a different answer from a broken
  Whisper, and they look identical from downstream.
- When the transcript came from `whisper-cli`, the run states which model file it
  used. "No model" and "the wrong model" are the two failure shapes, and neither
  announces itself.

**Fails if:** an empty transcript flows into `groups.json` and gets rendered; or
the run reports "the video has no speech" without having checked for an audio
stream; or a stub-model result is treated as a transcript.

---

## CV3 — Both caption paths are offered; the silent source only has one

**Scenario, two halves.** (a) An ordinary talking ad, and the user says "add
captions". (b) The same ask, but the source was rendered with
`audioEnabled: false`.

**Why.** These two skills are not tiers of each other. `POST /v1/captions` is one
call with a fixed preset list and costs credits; this skill is free, arbitrary in
style, and costs a first-time local setup. Picking one silently makes a
spend-or-setup decision on the user's behalf, and the skill's own text says to
offer both rather than picking. On half (b) the choice collapses: the API refuses
a source with no speech with a `409`, so the local burn is the only path — and it
still works, because the user can supply the words.

**Assertions.**

- On (a) both paths are named with their real trade — credits versus local
  toolchain, thirty presets versus anything you can write, transcribed wording
  versus wording you can hand-correct — and the run **waits**.
- On (b) the run says the API path is unavailable **and why** (`409`, no speech to
  transcribe), rather than trying it and reporting the refusal as an error.
- On (b) the words come from the user, and the run says so before rendering. It
  does not transcribe a silent track and burn the empty result.
- A user who asks for a caption look outside the presets, or who needs to correct
  an invented brand name before it is burned in, lands here without being sent to
  the API first.

**Fails if:** one path is chosen without the other being named; or the `409` is
surfaced as a bug; or a silent source is transcribed anyway.

---

## CV4 — The composite uses a real alpha channel

**Scenario.** Captions with a soft `text-shadow`, composited over the source.

**Observed failure (verified on a live clip 2026-08-03, recorded in this skill's
own rules).** A magenta chroma key cannot cleanly remove a soft shadow: the shadow
blends toward the key colour and leaves a **purple halo on every glyph**. The
render completes, the file plays, and the defect is visible only at full size.

**Assertions.**

- Captions are rendered `--format mov` and composited with ffmpeg `overlay` using
  the alpha channel. No chroma key anywhere in the chain.
- No `<video>` or `<audio>` element appears in the HyperFrames composition —
  the managed timing wrapper it triggers reserves an ~80px layout block, which
  lands as a hard black bar across the render.
- `-c:a copy` on the composite. The source's mix is already correct.
- The output is inspected at full size, not at a thumbnail. A halo survives a
  thumbnail.

**Fails if:** a key colour is used; or the audio is re-encoded; or the composite
is signed off from a scrubbed preview.

---

## CV5 — The output matches the source frame for frame

**Scenario.** A Seedance render — 24fps — is captioned.

**Why.** HyperFrames defaults to **30fps**. A mismatch does not fail: it produces
judder and caption drift that creeps, so the first card lands correctly and the
last one does not. The same shape applies to the composition size: a mismatch of a
pixel or two lands the composite off-register, and again nothing errors.

**Assertions.**

- `--fps` is set from the **measured** source rate, not from a default and not
  from the model's nominal rate.
- The composition size equals the source resolution exactly.
- After rendering, duration, resolution and frame rate are measured against the
  source and reported. Audio is bit-identical.
- A clip that opens on silence: timestamps come from a transcription of a **trimmed copy**, offset back
  — and if the master is trimmed later, the captions are regenerated rather than
  shifted, because the offsets no longer describe the file.

**Fails if:** the frame rate is assumed; or the verification step is skipped
because the output "looked fine"; or captions are burned against timestamps taken
from an untightened master that was then tightened.

---

## CV6 — The source video survives the run

**Scenario.** Any run. The source is a finished, paid render.

**Why.** It is the only copy. Everything else in this pipeline is reproducible
from it, and it is reproducible from nothing.

**Untested** — no run has destroyed a source, so this is a prospective guard
rather than a recorded failure. It is here because the cost of the first
occurrence is the whole render and the check is free.

**Assertions.**

- Every ffmpeg invocation that writes goes to a **new** filename. No `-y` over the
  input path.
- The grouped phrases (or a first render) are shown to the user before the
  captions are treated as final.
- The transcript is read and corrected **before** rendering, not after. Invented
  brand names are the usual reason and the cheapest moment to fix them is while
  they are still text.

**Fails if:** the source path appears as an ffmpeg output; or the first the user
sees of the wording is the finished file.

---

## Notes on evidence strength

- **CV1 is the strongest case here and the most specific**: a named preset, a named
  word, a timestamp range, and a charged take that was rejected. It is also the
  only one whose failure is in a service this skill does not own, which is why the
  assertion is about the *check* rather than about a fix.
- **CV2's failure half was observed on a real machine**, not reasoned about — but
  it was observed through a sibling skill, and nobody has run *this* skill on a
  stub-model Homebrew box. The gap it names in *Prerequisites* is present today.
- **CV4 and CV5 are recorded rules with a live verification behind CV4** (the
  2026-08-03 halo). CV5's frame-rate default is read off the tool's documented
  behaviour rather than re-measured here.
- **CV3 and CV6 are design assertions.** CV3's `409` is documented API behaviour;
  what is untested is the agent's conduct at the fork. CV6 is untested outright.
- **No credit figures appear in this file by design.** This skill's own path spends
  nothing, and the API arm it compares against is priced by a live
  `POST /v1/estimates` in the session that spends it.
