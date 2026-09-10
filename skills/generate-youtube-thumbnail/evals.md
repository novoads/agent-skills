# Evals — generate youtube thumbnail

Written after the skill, to close the gap `scripts/check-evals-present.sh` had been
naming on every run. Two of the six cases are drift **present in this skill's own text
as this file is written** — found by reading it against `reference.md` — and one comes
from the 2026-08-11/12 README-gallery dogfooding run (RUN-FINDINGS item 9). The rest
are the skill's own recorded rules. Where a case is prospective it says **untested**.

This skill runs `nano-banana-pro` at a different job from `nano-banana-image-ad`:
likeness first, batch second, CTR third. So the cases that matter here are the ones
about **references** — how many, which, and whether the same ones survive a series.

**YT1 and YT2 are text assertions against the skill file and the request body**,
checkable before a charge. YT3 and YT4 are run-shape assertions. YT5 and YT6 need a
batch.

---

## YT1 — The reference cap in this file contradicts itself, and the rule loses

**Scenario.** A likeness run. The user wants themselves in the thumbnail and has a
folder of face photos: headshot, two three-quarter angles, a smiling one, a neutral one.
Five, because the skill says five.

**Observed drift — found, and reconciled.** Three numbers disagreed inside one document.
Recorded here because the shape recurs whenever a vendor raises a limit: the section that
announces the new number gets rewritten, and the sentences that merely *use* the old one do
not. The four survivors were:

- *References — how many, and why it changed back* said **14**, and said the 4-on-every-
  model advice "has been corrected".
- The same section then said **"Always use 5+ face references for character work."**
- Workflow step 2 ended **"Then pick the 4 that will be cited (see the cap section
  above)"** — pointing at the section that had just said fourteen.
- *Quirks and pitfalls* → `referenceAssetIds` is an array of plain strings ended
  **"Maximum 4."**
- And *Compose prompts* told the reader to lean on the likeness block harder "since it is
  now carrying work the 5th reference used to do" — a sentence that only parses under the
  retired cap.

An agent reading the workflow in order obeys the last instruction it hit, so it cited four
references on a model that takes fourteen, **while the same file told it five was the
minimum for the job it was doing**. Nothing refuses a short array, so the run completes, the
likeness generalises, and the cause is invisible. All five sentences now name 14 or defer to
`reference.md`; the assertions below are what a future edit must not break.

`reference.md` settles it: `nano-banana-pro` takes **14**, verified live 2026-08-04
against spec `2.7.0` with pinned out-of-range probes — 15 refused, 14 accepted. It also
retires this file's other stale line: `gpt-image-2` **has** been probed (5 refused), so
its 4 is measured rather than unknown.

**Assertions.**

- A likeness run on this model cites **at least five** face references and may cite up
  to fourteen.
- No step of the run caps at four, and no sentence quotes four as this model's limit.
- The authority for a cap is `reference.md`'s per-model table, re-checkable with
  `./scripts/verify-image-caps.sh` — never a number restated in a workflow step.
- If the run is routed to `gpt-image-2` or `reve-2.1` instead, the 5+ advice is stated
  as **not surviving the trip**, with that model's real cap named.

**Fails if:** four references are cited on a likeness run; or the run reports four as
this model's cap; or the contradiction is resolved by lowering the 5+ rule instead of
raising the step.

---

## YT2 — The anchor is an `assetId`, and it is the same one every time

**Scenario.** A series: one approved hero thumbnail, then five variations of it.

**Why.** `POST /v1/uploads` returns an `assetId` that is durable across calls and
across sessions. Re-uploading the same face photo produces a **different** id and
quietly loses the anchor that was holding the likeness steady — the run still succeeds,
the face still appears, and it is subtly a different person. This is the **opposite** of
the backend this workflow was ported from, where a reused reference caused
`HTTP 500 UNKNOWN_ERROR` and every generation needed a fresh upload, so the wrong habit
is the one a reader arrives with.

**Assertions.**

- Every shared reference is uploaded **once** per batch, or once per campaign, and the
  ids are reused.
- For variation N the rolling window is `[hero, N-1, N-2, N-3, N-4]` — the approved hero
  as anchor plus the four most recent good outputs.
- A variation that **drifted** is dropped from the window rather than fed forward. A bad
  reference propagates.
- The presigned `uploadUrl` expiring is understood as bounding the PUT window only, not
  the asset.
- The signed headers are echoed byte for byte on the PUT. `Content-Type` and
  `Content-Length` are both in the signature, so an added `; charset=…` is a `403` that
  reads like an auth failure and is not one.

**Fails if:** the same photo is re-uploaded per call; or a drifted output is carried
into the next window; or an id is discarded when its upload URL expires.

---

## YT3 — Chat-pasted is not on disk, and a described brand is not a brand

**Scenario.** The user pastes their logo and a photo of themselves into the
conversation and asks for a thumbnail.

**Why.** Neither is a file the API can be given. And the fallback — describing the brand
in words — produces a generic approximation that renders confidently and charges
normally. The distinction the skill draws is the useful one: generic descriptions are
fine for backgrounds, expressions and clothing; **brand-specific items need actual
files.**

**Assertions.**

- The run stops and asks for real files in a project folder. It does not proceed from
  a chat-pasted image.
- Brand-specific items — logos, branded apparel, custom merchandise, the product — are
  refused as text descriptions and requested as files.
- The `references/` folder is listed before the user is asked for anything, in case the
  files are already there.
- Nothing is charged before the references question is settled.

**Fails if:** a run generates from a text description of a logo; or a chat-pasted image
is treated as available; or the user is asked for files that are already on disk.

---

## YT4 — The estimate names the model, and the batch is multiplied before the yes

**Scenario.** Ten thumbnail concepts, one composed prompt each.

**Why.** `POST /v1/estimates` defaults to `gpt-image-2.5-sunburst` when `model` is omitted
(it was `gpt-image-2` until deployed spec 2.25.0; both sit on the same cheapest schedule, so
the arithmetic below is unchanged), and the image schedules differ by more than 3×. An estimate without `model` therefore quotes the
cheap model for a `nano-banana-pro` batch, and the gap is multiplied by ten before
anyone sees an invoice.

**Assertions.**

- `model: "nano-banana-pro"` is in the estimate body.
- The per-image number, the count, the total and the `balance` are all shown, and the
  run waits for an explicit yes.
- If `sufficient` is false the run says so and stops, quoting `shortBy` and `topUpUrl`.
- No number is quoted from memory, from `logs/novoads-api.jsonl` or from
  `MASTER_CONTEXT.md`.
- The prompt is re-read against the formula **before** pricing: a batch runs the same
  shape N times, so a flaw in it is paid for N times.
- The closing report sums `creditsCharged` from the responses, never the estimate.

**Fails if:** the estimate omits `model`; or a total is shown without the per-image
number; or the final report quotes the quote.

---

## YT5 — A concurrency refusal is a wait, not a backoff, and it costs nothing

**Scenario.** The batch script runs while another session on the same organization is
also generating.

**Observed live (dogfooding run, RUN-FINDINGS item 9, and again 2026-08-12 across
parallel callers on one org).** The in-flight count is **per organization**, not per key
or per session, so two agents each holding three renders open produce a refused sixth
submission with neither of them individually misbehaving. It cleared in about two
minutes. **Nothing is charged on the refusal** — the row is never created, so there is
no job to find and no credit to reclaim.

**Assertions.**

- The run branches on `details.reason`. `concurrency_limit` is waited out; only a
  finishing job frees a slot, and a longer backoff does nothing.
- `Retry-After` is honoured rather than a backoff being invented.
- The refusal is reported as costing nothing, and no lookup is made for a phantom
  charged job.
- The batch caps itself at 4 in flight against an org ceiling of 5, and the run states
  that the ceiling is shared with anything else the account is doing.
- `key_limit`, `organization_limit` and `client_limit` are recognised as the paced ones
  — and minting another key is not offered as a fix for the organization ceiling.

**Fails if:** a `concurrency_limit` refusal is treated as a rate limit and backed off;
or the user is told a refused submission cost them something; or the run reports "the
API is down".

---

## YT6 — The unverified claims are labelled as unverified

**Scenario.** A reference image is smaller than the batch script's upscale target, and
the user asks why it is being resized.

**Why.** The skill's own text is careful here and the care is the thing being tested:
*"images smaller than 1080px longest side return `422 — image too small`"* was a rule of
the **previous backend** and **has not been verified against Novoads**. The script still
upscales, because small references genuinely produce worse likeness — but that is a
craft reason, not an API rule, and reporting it as an API rule teaches the user a
constraint that may not exist.

**Untested** as an agent run: nobody has observed a session misreporting it. It is here
because this file's whole value is telling a reviewer what "working" means, and a skill
that launders practice into policy fails quietly forever.

**Assertions.**

- The upscale is explained as improving likeness, not as satisfying an API minimum.
- No unverified inherited claim is presented to the user as this API's behaviour.
- The same discipline holds for wait times and caps: a number this pack has not measured
  is quoted as unknown rather than borrowed from a sibling model or a previous backend.

**Fails if:** the `422` claim is stated as a Novoads rule; or an inherited number is
quoted without its provenance.

---

## Notes on evidence strength

- **YT1 is the strongest case here and the only one that is red today.** Every quoted
  sentence is in the skill file as this is written, and the adjudicating number is
  live-verified in `reference.md` with the probe log attached.
- **YT5 is measured twice** — once in the dogfooding run and once across parallel
  callers on one organization — and the "nothing is charged" half is what makes it worth
  an assertion rather than a note.
- **YT2's mechanism is documented and its inversion is the interesting part**: the
  behaviour to unlearn came from a different backend, so the failure arrives as a habit
  rather than as a mistake.
- **YT3 and YT4 are recorded rules of this skill**, restated as checks. Neither has a
  named incident in this pack.
- **YT6 is prospective and says so**, and it is deliberately about the skill's honesty
  rather than about its output.
- **No credit figures appear in this file by design.** The estimate arm quotes at spend
  time.
