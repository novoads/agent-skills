# Evals — novoads api

Written after the skill, to close the gap `scripts/check-evals-present.sh` had been
naming on every run. This is the router every other skill in the pack falls through to,
so its failures are the ones that reach the most runs — and most of them are quiet: a
charge that looks like nothing happened, a poll loop that spins on a finished job, a QA
command that reports success by printing nothing.

Sources, named per case: the 2026-08-11/12 README-gallery dogfooding run (RUN-FINDINGS
P1, P2 and items 9 and 12), the live-verified traps in [reference.md](reference.md), and
one contradiction found by reading this skill's *Guardrails* list against its own body.
Where a case is prospective it says **untested**.

**Two conventions carried from the sibling files.** Nothing here quotes a credit
figure — the estimate arm quotes at spend time. And the prompt-library's own eval file,
[prompting/prompt-library/evals.md](prompting/prompt-library/evals.md), owns the UGC
base-video and b-roll contract; this file owns the API surface.

---

## NA1 — A bare, envelope-less error does not mean nothing happened

**Scenario.** A generation call comes back with a status code and **no**
`{"error":{"code":…,"requestId":…}}` body. The user asks what went wrong.

**Observed failure (dogfooding run, RUN-FINDINGS P1).**
`POST /v1/videos {model: "seedance-2.5", startImageAssetId: …}` failed roughly 176ms
after row creation, **every time**, answering a bare `502` at the edge with no JSON
envelope — so the caller never learned that a row had been created **and charged**.
Credits charged and then refunded correctly, which is the part that makes this
survivable and also the part nobody could see from the response. It was isolated with
nine single-variable probes: not the asset, not the brand, not `aspectRatio`,
`audioEnabled`, `durationSeconds`, `resolution` or the prompt. The same model without a
start image succeeded; the previous model with the *same* start image succeeded. The
estimate could not have caught it — the estimate never sees `startImageAssetId`.

**The documented sibling shape, which is the reason this is a class and not an
incident.** [reference.md](reference.md) records a `403` carrying **a bare Cloudflare
edge page with `error code: 1010`** — no `code`, no `requestId` — which "reads exactly
like a revoked key or a dead subscription and is **neither**". Its fix is the client
(a default `python3-urllib` User-Agent), not the credential. Two tells are given: the
body is the wrong **shape**, and a request that succeeded moments earlier over `curl`
proves the key is live.

So the rule generalises: **the envelope is the signal.** A response without one did not
come from the application layer, and nothing about the job can be read out of it —
including whether there is a job.

**Assertions.**

- A response with no error envelope is reported as *"the request did not reach a state
  this API described"*, never as a diagnosis of the key, the plan or the prompt.
- Before anything is retried, `GET /v1/generations` is called and matched on
  `createdAt` — a row may exist, may be charged, and may already be refunded.
- Nothing is re-sent blind. There are **no idempotency keys**, so a retry can render and
  charge again.
- The user is told plainly whether a charge landed and whether it came back, from the
  ledger rather than from the failed response.
- On a bare edge page specifically, the client is examined before the credential. A
  regenerated key, a subscription check, or "your plan lapsed" are wrong answers.
- The `seedance-2.5` + `startImageAssetId` pairing is **re-probed against the current
  deployment** rather than assumed broken or assumed fixed — the door was reported
  reopened and verified live in a later change, and both a stale "it works" and a stale
  "it is broken" are wrong in expensive directions.

**Fails if:** a bare status code is translated into a cause; or a retry is fired before
the generations list is read; or the charge-then-refund is left unmentioned because the
response did not carry it.

---

## NA2 — The poll loop survives a response a strict parser rejects

**Scenario.** A multi-line video prompt was submitted. The run polls
`GET /v1/generations/{jobId}`.

**Observed failure (dogfooding run, RUN-FINDINGS P2; the same finding is recorded in
[reference.md](reference.md), observed live 2026-08-12).** The **echoed `prompt` can
carry raw newlines**: the control characters arrive unescaped inside the JSON string, so
`json.loads()` raises. A loop that reads a parse error as *"not ready yet"* then spins
until it times out **on a job that already finished** — one run's loop spun for ten
minutes. It is a server-side escaping bug: nothing about the render or the charge is
affected, and the render is sitting there succeeded the whole time.

`json.loads(body, strict=False)` works, and the equivalent lenient mode works elsewhere.

**Assertions.**

- The poll parses tolerantly. A parse failure is **not** a status.
- A parse failure is reported as a parse failure, distinguished in the run's own words
  from `queued`, `running` and `finalizing`.
- The loop exits on any **terminal** status — `succeeded`, `failed`, `blocked`,
  `canceled` — never on `succeeded` alone. A loop waiting only for success never returns
  on a job that died, and the user watches a spinner over a dead render.
- Polling is every 15 seconds, not 5: five concurrent jobs at 5s is exactly the per-key
  ceiling with no headroom for the calls doing real work.
- A `409` from `/watch` is read as *"not finished yet"* and the poll continues.
- `queued` is reported as charged-and-submitted, which is normal, not as a stall.

**Fails if:** a parse error is folded into "still running"; or the loop's exit condition
is `succeeded`; or the poll interval is tightened to make a job feel faster.

---

## NA3 — Every warning is read, judged out loud, and neither obeyed nor dropped by reflex

**Scenario.** Gate 2. The prompt is priced and `warnings` comes back non-empty.

**Both failure directions are on the record.**

*They false-positive*, and two were reproduced live 2026-08-04:
`label_without_hold` fired on the word **"screen"** in a prompt for a SaaS dashboard
demo — there was no printed label in the shot, and pasting in the labelHold clause would
have told the model to preserve a package that is not there. `chained_motion` fired on
the word **"Then"** *inside a quoted spoken line* — dialogue, not a second motion
instruction; splitting it would have split the sentence the actor says. Both rules are
substring matches and neither can tell a physical package from a UI, or narration from
stage direction.

*And one was right.* On the dogfooding run (RUN-FINDINGS item 12) a **paraphrased**
`labelHold` clause tripped the rule, because the lint string-matches the canonical
sentence — pasting that sentence verbatim cleared the warning and the clause was one the
prompt genuinely wanted. That is the counterweight to the false-positive tally, and it
is why "ignore the lint" is as wrong as "obey the lint".

**Assertions.**

- Every entry is read. None is dropped silently, including the ones being overridden.
- Each is judged against what the prompt **actually says**, including *where* the matched
  substring sits, and the reasoning is stated in one line to the user — *"the
  `label_without_hold` warning matched the word 'screen', but this is a SaaS dashboard
  with no printed label, so I am not adding the clause"*.
- A suggested fix is never pasted into a prompt it does not fit.
- The warnings are understood as **advisory**: none refuses a call, none changes the
  price, and a prompt that trips all of them renders exactly like one that trips none.
- `POST /v1/estimates` is understood as the **only** endpoint that runs them.
  `POST /v1/videos` and `POST /v1/images` carry no `warnings` field, so there is no
  second chance to collect them.
- Image prompts are linted too, by rules of their own. A run that reports image
  estimates as unlinted is repeating a retired claim.
- The prompt libraries remain the real quality gate. A clean warnings array is not a
  review.

**Fails if:** a fix is applied without reasoning; or an override happens silently; or
the array is treated as a verdict in either direction.

---

## NA4 — The Guardrails list contradicts the body, and the body is right

**Scenario.** An agent reads this skill top to bottom and reaches *Guardrails* last.

**Observed drift — found, and corrected.** The `POST /v1/images` section states the
reference cap is per model — `nano-banana-pro` **14**, `reve-2.1` 8, `gpt-image-2` 4 —
and [reference.md](reference.md) agrees, with the probe log attached: verified live
2026-08-04 against spec `2.7.0`, *which raised `nano-banana-pro` from 4 to 14*, each
probe pinned with an out-of-range `numImages` so no body could be valid (15 refused, 14
accepted; 9 on `reve-2.1` refused, 8 accepted; 5 on `gpt-image-2` refused).

The *Guardrails* bullet read **"4 on `gpt-image-2` and `nano-banana-pro`"** — the
pre-`2.7.0` value — for as long as it took someone to read the file top to bottom rather
than in the order it was edited. It was the last statement in the file on the subject, it
was stated as a rule rather than as a reference, and it was wrong. An agent that trusted
it capped a fourteen-reference model at four, **silently**: nothing refuses a short array,
the render succeeds, and the missing references show up as a likeness that drifted or a
brand mark that got invented. The bullet now names each model's own cap, in the body's order; the
assertions below are what a future edit must not undo.

This is the failure the guardrail list is *designed* to cause when it goes stale, which
is the general lesson: a summary that restates a number owns that number forever.

**Assertions.**

- Reference caps are read from `reference.md`'s per-model table, or re-measured with
  `./scripts/verify-image-caps.sh`. Never from a guardrail sentence.
- No single cap number is carried across models. The bodies are strict, so an over-cap
  array is a `400` — *"Too big: expected array to have <=N items"* — with nothing
  charged, which is the good outcome: a silently dropped reference would be a paid render
  missing the product.
- Video references are understood as a **different** number and a narrower set: up to 9,
  on the three Seedance variants only.
- A guardrail bullet that restates a limit is checked against the section it summarises
  before it is quoted to a user.

**Fails if:** four references are sent to `nano-banana-pro`; or the guardrail line is
quoted as the cap; or a video cap and an image cap are conflated.

---

## NA5 — The charge is on the `202`, and it is the only copy

**Scenario.** A render is submitted, polled to `succeeded`, downloaded and handed over.
Later someone asks what the run cost.

**Why.** `creditsCharged` comes back on the submit's `202` and **is not on the poll
payload** — the poll returns `jobId`, `status`, `kind`, `model`, `prompt`, `createdAt`,
and once succeeded `outputUrl` plus its expiry, verified live 2026-08-03. So a log line
written without the charge can never be completed. The failure mode is not a missing
number: it is that the number then gets **reconstructed from a rate**, which is exactly
what `scripts/check-no-rates.sh` exists to prevent, and the reconstruction is
indistinguishable from a measurement.

**Assertions.**

- The submission is logged **immediately**, one line, carrying `creditsCharged` from the
  `202`. The charge goes on the line now.
- The line is updated by `jobId`, not by position — up to five jobs are in flight and the
  one being updated is often not the last written.
- The log is never a pricing source. Prices come from `POST /v1/estimates`, always.
- No prompt text, key or `Authorization` header is ever logged.
- A cost reported to the user is summed from `creditsCharged` values, never from the
  estimate and never from a per-unit figure.
- If the charge is missing from a line, that is reported as unknown rather than
  reconstructed.

**Fails if:** the poll is searched for `creditsCharged`; or a total is derived
arithmetically from a rate; or a run reports the estimate as what was spent.

---

## NA6 — QA hears the ad, and the QA command is not silently muted

**Scenario.** A render comes back `succeeded`. Every frame looks right.

**The failure this catches (2026-08-02).** A `seedance-2.0` render spoke the approved
17-word line verbatim and pronounced **"Novoads"** as **"Nuvenov's"** — unrecognisable
as the brand. Every frame was perfect. Only the transcript caught it. In `es` the same
brand came back **"NoBots"**, and the *identical* payload was **1-for-2**: on the bad
take the model stuttered — one clause spoken twice — and `Novo` collapsed into the
preposition, leaving the ordinary phrase **"no ads"**, which is worse than a mangled
brand because the listener hears no brand at all.

**And the check itself has a trap, verified 2026-08-02.** Adding `-v error` to the
`volumedetect` and `silencedetect` calls **suppresses the entire result**: both filters
print at ffmpeg's `info` level, so the command exits `0` having told you nothing, and it
looks exactly like a clean pass. On a clip carrying 3.7s of leading silence, the
silencedetect call printed no output at all. `ffprobe` in step 1 is the opposite case,
where `-v error` is correct because `-show_entries` writes to stdout.

**Assertions.**

- Every video is transcribed before hand-off, and the transcript is read **against the
  line approved at gate 1** — the brand name, the words, the language.
- `-v error` never appears on `volumedetect` or `silencedetect`. A check that printed
  nothing is treated as **not run**, not as passed.
- The first `silence_end` is read on every render and compared against the budget. The
  silence is drawn fresh each time, so the reservation holding is confirmed, never
  assumed.
- An audio stream is confirmed to exist at all. No audio stream on a talking clip is a
  re-render, not a note.
- A mispronounced invented brand name is fixed with the **phonetic spelling for that
  language** — and gate 1 is re-run, because the words changed.
- Every `es` render is transcribed. A clean take is not evidence the next one is clean,
  and the recorded stutter is the reason.
- The phonetic fix is reported with its limits: validated on one model, in `en`, n=1;
  the `es` form is a different spelling and is provisional; `pt` is untested. It is not
  presented as a general fix.
- Every re-render goes back through gate 2 with a fresh estimate. There is no free
  retry allowance on video.

**Fails if:** a video is handed over untranscribed; or `-v error` rides on either
loudness call; or a stutter is fixed by editing the prompt (it is nondeterministic
delivery — re-sampling the identical body is the right move, and it still costs).

---

## NA7 — A 429 names which ceiling, and a concurrency refusal costs nothing

**Scenario.** A batch runs while another session on the same organization is also
generating.

**Why, and it is measured.** The in-flight count is **per organization**, not per key or
per session: two agents each holding three renders open produce a refused sixth
submission with neither individually misbehaving — observed live 2026-08-12 across
parallel callers on one org, and again in the dogfooding run (RUN-FINDINGS item 9),
where it cleared in about two minutes. **Nothing is charged on the refusal**: the row is
never created, so there is no job to find and no credit to reclaim.

The queues are separate, and that is the part an agent gets wrong. Video, images,
captions, transcripts, voice-overs and voice-changes each have their own ceiling and
their own `details.reason`. The deployed spec names twelve reasons. An agent that reads
only *"429 means slow down"* backs off on the wrong axis when the problem is jobs in
flight — and may be backing off the wrong **queue** entirely.

**Assertions.**

- The run branches on `details.reason` and sleeps on `Retry-After`.
- `concurrency_limit` is waited out. A longer backoff does nothing; a finished job does.
- A `429` on one queue is never read as a reason to stop calling another.
- The refusal is reported as costing nothing, and no lookup is made for a phantom job.
- `organization_limit` is not answered by minting another key, and the `X-RateLimit-*`
  headers still showing room on the key is understood as correct rather than as a broken
  limiter.
- No branch is written on a `details` key the spec does not name. `details.inFlight` on
  a concurrency refusal is the only extra there is.
- At most five generations are in flight, and the ceiling is stated as shared with
  whatever else the account is running.

**Fails if:** a concurrency refusal is backed off; or the user is told a refused
submission cost them something; or one queue's refusal stops the others.

---

## NA8 — An estimate that accepted a field is not a licence to send it

**Scenario.** A draft on `seedance-2.0-mini`. The estimate is priced with
`resolution: "720p"` and it comes back clean.

**Observed split-brain (verified live 2026-08-04).** `POST /v1/estimates` **accepts**
`resolution: "720p"` for mini and prices it — identically to omitting it — while
answering `400 invalid_input` for `480p`, `1080p` or `4k`. `POST /v1/videos` does not
accept the key for mini **at all**: mini's request variant has no `resolution` property,
and a body carrying one returned `400 Unrecognized key: "resolution"`. So a field that
priced cleanly is a rejected generation. (That last observation is flagged in the docs
as **not re-verified**, because confirming it again means a paid render — which is
itself worth asserting: the run does not go and check.)

**The neighbouring shape, same lesson.** Never carry a `resolution` across a model
switch. `seedance-2.5` renders `480p` and `720p` and nothing above — a workflow that
renders `seedance-2.0` at `1080p` and swaps the model id is a **rejected request**, not
a downgrade. And the estimate body more generally is strict and narrow: it takes only
the fields that move the price, so `aspectRatio`, `startImageAssetId`,
`referenceAssetIds`, `productId`, `audioEnabled` and `styleFamily` are each a `400`
there — while some of them are perfectly valid on the generation call.

**Assertions.**

- `resolution` is never sent on a mini call, to either endpoint.
- A field's acceptance by the estimate is never used as evidence the generation accepts
  it. The two schemas are different and the differences are documented per field.
- `resolution` is re-priced whenever the tier changes, and never carried across a model
  change.
- `model` is named explicitly in every estimate body — the schedules span more than 10×
  across the set at one length, and the prompt ceiling is enforced against whichever
  model is named. Naming none is judged as `seedance-2.0`.
- `durationSeconds` is validated against the **named model's** grid, and an out-of-grid
  value is **rejected, never rounded**.
- The estimate is understood to skip moderation, so a clean quote can still meet a `422`
  at generation with nothing charged.
- The mini `Unrecognized key` observation is left as documented rather than re-probed —
  re-verifying it costs a render, and the rule it supports does not depend on the
  re-verification.

**Fails if:** `resolution` reaches a mini generation; or an estimate's acceptance is
quoted as proof; or a resolution survives a model switch.

---

## Notes on evidence strength

- **NA1 and NA2 are the strongest cases here.** Both were isolated on a paid run with
  single-variable probes, and both are failures whose *response* actively misleads: one
  hides a charge, one hides a finished render. NA1's generalisation to "the envelope is
  the signal" is supported by a second, independently documented bare-page failure.
- **NA3 has evidence on both sides**, which is unusual and is the point: two reproduced
  false positives and one reproduced true positive. An eval that only carried one side
  would train the wrong reflex.
- **NA4 is red today.** The stale guardrail bullet is in this skill as this file is
  written; the adjudicating number carries a live probe log in `reference.md`.
- **NA6's flagship failure is measured** and so is its harness trap — which is the
  sharper half, because a QA step that reports nothing while exiting `0` is
  indistinguishable from a pass.
- **NA5, NA7 and NA8 are read off live-verified documentation** rather than re-probed
  here. NA7's per-organization half was observed live twice; NA8's mini half carries the
  docs' own "not re-verified" flag, deliberately preserved.
- **No credit figures appear in this file by design.** Ratios, ordering and meter shape
  survive; the number comes from `POST /v1/estimates` in the session that spends it.
