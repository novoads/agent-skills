# Evals — chatgpt image ad

Written after the skill, to close the gap `scripts/check-evals-present.sh` had been
naming on every run. Every case below is a failure someone already paid for: three
from the 2026-08-11/12 README-gallery dogfooding run (RUN-FINDINGS items 3, 5 and 6),
one from the 34-template measurement this skill's hard rule 5 cites, and two from
`reference.md`'s own live-verified traps. Where a case is prospective it says
**untested** in its own text.

The shared library owns template *content* — see
[`shared/skills/image-ad-prompting/evals.md`](../../shared/skills/image-ad-prompting/evals.md).
This file owns what happens when the caller is pointed at `gpt-image-2`: this model's
caps, its edit arm, and the two ways a library run loses images it has already paid for.

**GI1, GI2 and GI3 are text assertions against the prompt and the request body**,
checkable before a charge. GI4 and GI6 are run-shape assertions. GI5 needs a render.

---

## GI1 — The label is spelled out, in the base prompt

**Scenario.** A real product with printed packaging appears in frame, pinned by a
reference asset.

**Observed failure (measured over a 34-template run on one real product,
2026-08-04).** The pinned front label was faithful in **all 34**. Every mark the prompt
left unspecified was invented, three ways: a billboard rendered an **invented
back-of-can view** carrying *"OUR WATER IS SOURCED FROM THE AUSTRIAN ALPS…"* with an
icon row and a barcode; a prop thermos rendered a **Hydro Flask logo**; a publication
wordmark drifted. One retry naming the exclusion cured the fabricated claim completely.

**The upgrade, from the dogfooding run (RUN-FINDINGS item 3).** Pinning by reference
fixes the primary mark and not the secondary lines, because **the model does not OCR
the reference**. Spelling every label line verbatim in the prompt is the reliable fix —
and it belongs in the **base** prompt, because label fabrication is **seed-variable**:
a run that adds the spelling only after seeing a defect will sometimes not see one, and
ships the un-guarded prompt. The counterpart trap from the same run: added
shot-distance framing pins can blow banding artifacts (a white band across roughly the
bottom 220 rows), so spelling is safe to add unconditionally and a framing pin is not.

**Assertions.**

- Every legible line of product text is written out verbatim in the **first** prompt.
- Surfaces the ad does not show are excluded in words — *"front label only; do NOT
  render the back of the can, no invented label copy, no ingredient text, no sourcing
  statement, no barcode."*
- Every third-party mark the concept needs is passed as its own reference. Unpinned
  means invented, and the model states the invention as fact.
- The pin block is passed as `--pin-block`, so the script wraps the measured wording
  and counts it against this model's cap rather than a hand-written clause overflowing
  it.
- A framing pin, if added, earns a full-frame artifact sweep in Phase 6.

**Fails if:** the label is pinned by reference alone; or the verbatim spelling first
appears in a retry; or a clean first draw is read as proof the prompt is safe.

---

## GI2 — A clean estimate is proof of the price, not of the length

**Scenario.** A dense-text template — a chat thread, a comparison table, a long
typographic hero — whose final prompt, with the always-on suffixes appended, runs long.

**Observed trap (deployed spec `2.16.0`, verified 2026-08-08).** `POST /v1/estimates`
caps `prompt` at **50,000 characters for every image model**. `POST /v1/images` caps
**this** model at **32,000**. A prompt between those two numbers prices cleanly and is
then refused by the generation. Only `nano-banana-pro`, at 50,000, has the two numbers
agree — which is exactly why the number cannot be carried between the two image skills.

The same asymmetry has a second half: the estimate **skips moderation**, which the paid
call runs, so a prompt it priced clean can still come back `422 content_policy` with
nothing charged.

**Assertions.**

- The length that decides is measured **locally, against 32,000**, before either call —
  which is what `generate_image.py` does.
- A clean estimate is never reported to the user as "the prompt is fine". It is
  reported as the price.
- The estimate body carries only `kind`, `prompt`, `model`, `numImages`, `language`.
  `aspectRatio` or `referenceAssetIds` in it is a `400 Unrecognized key`, and neither
  moves the price.
- `model` is named in the body. Omitting it prices the API default, and the image
  schedules differ by more than 3×.
- The prompt priced is the **final** one, suffixes included.

**Fails if:** the estimate's ceiling is used as the length check; or a `422` at
generation is treated as a surprise the estimate should have caught; or the estimate is
fired on the pre-suffix prompt.

---

## GI3 — The edit arm: no `aspectRatio`, and the source spends a slot

**Scenario.** A finished image exists and the user asks for one change —
"remove the sticker on the bottle".

**Observed live (dogfooding run, RUN-FINDINGS item 6, confirmed live).**
`sourceAssetId` exists **only** on the five GPT models, and it **rejects `aspectRatio`**: an
edit's output tracks the source's shape, so the pair is a `400`. The second half is
easier to miss — **the source spends a reference slot**, so source plus
`referenceAssetIds` must total ≤ 4.

Two more edges worth asserting. *Closest*, not exact: this model's grid has nothing
between `1:1` and `16:9`, so a 4:3 landscape source renders `1:1`. And the arm is
flag-gated at the **schema** level — if `sourceAssetId` is absent from
`GET /v1/openapi.json`, this deployment cannot edit and no retry changes that.

**Assertions.**

- An edit run sends no `--aspect-ratio`. The script refuses the pair locally, before
  spending, for the same reason the API does.
- Source + references ≤ 4, counted with the source included.
- The prompt names the **change** and pins everything else — *"Change nothing else.
  Keep the label, the wordmark, the lighting and the framing exactly as they are."*
  Unspecified is what this model reinvents.
- `--source-asset-id` is used when the image is already uploaded. Re-uploading the same
  bytes mints a second asset.
- Phase 6 QA covers the **whole frame**, not the edited region: an edit is a fresh
  render, so nothing carries over pixel-for-pixel.
- A deployment without the field is reported as a capability the account does not have,
  not retried.

**Fails if:** `aspectRatio` rides along with `sourceAssetId`; or the reference budget is
counted without the source; or the QA compares only the region the user mentioned.

---

## GI4 — A generated image chains by `assetId`, never by `url`

**Scenario.** An image produced here becomes the input to something else — an edit, a
start frame, a reference on a later call.

**Observed failure (dogfooding run, RUN-FINDINGS item 5).** The
download-and-re-upload dance was performed again, because the field that makes it
unnecessary had never been named where anyone would read it. `POST /v1/images` returns
**`assetId` beside `url`** in each `images[]` entry. The `url` is a one-hour presign and
nothing downstream accepts it. The `assetId` is durable and is accepted directly.

`assetId` is **optional** in the schema, so it is read rather than assumed.

**Assertions.**

- Downstream calls take the `assetId` straight from the response. No download, no
  `POST /v1/uploads`, no second asset minted for bytes the API already holds.
- The `url` is treated as expiring and used only to save the file.
- If `assetId` is absent from a response, that is stated and the upload path is used
  deliberately — not assumed away in either direction.

**Fails if:** the chain runs off the `url`; or the image is downloaded and re-uploaded
to get an id it was already given.

---

## GI5 — A library run cannot lose an image it paid for

**Scenario.** The full-library run: one product photo, every template whose Model notes
mark this model clean or preferred, one flat output folder.

**Why, and it is measured.** A `numImages > 1` call charges for every image and only
the **first** is recoverable afterwards — `GET /v1/generations/{jobId}` returns a single
`outputUrl`, and images 2..N exist nowhere but the body of the response that returned
them. The render blocks inside the POST for 60–90 seconds, so a proxy or CDN idle
timeout drops a response for work the API already did and charged for. That is the
run's own text: **one image per call**, and **write every image to disk the moment it
arrives**.

**Assertions.**

- `numImages` is omitted or `1` for a library run. A multi-image call is used only when
  losing images 2..N would be acceptable.
- Each image is written to disk as it is read, before the next template starts. No
  batch held in memory and saved at the end.
- A timed-out call is **not** re-sent: `POST /v1/images` takes no idempotency key, so a
  retry renders and charges again. `GET /v1/generations` is checked first, matched on `createdAt`.
- At most 4 requests in flight: the run's own cap, under an org image queue of 12 that
  every other image call the org runs through the API shares.
- A `429` is branched on `details.reason`: `image_concurrency_limit` clears only by waiting,
  and `Retry-After` is honoured rather than the backoff being tightened.

**Fails if:** a batch is held in memory; or a timeout is retried without a lookup; or
the concurrency refusal is treated as a rate limit.

---

## GI6 — The run has a ceiling, and retries count against it

**Scenario.** The full-library run again, this time going badly: several templates
render defective and each takes its two allowed retries.

**Why.** The quoted total is the happy path. Every template retried twice is **three
times** that number, and QA retries deliberately do not re-ask for consent — which is
the right call inside a cap and a runaway outside one. So the cap is the only thing
standing between an approved quote and an unapproved spend.

**Untested as an agent run.** No recorded case of a library run exceeding its quote in
this pack; the reasoning is the skill's own and the arithmetic is not in dispute. It is
here because the first occurrence is expensive and the check is free.

**Assertions.**

- A hard ceiling is decided **with** the user at the same moment the run is approved,
  not inferred later from the estimate.
- The ceiling is checked before **every** request, retries included. If the next call
  would cross it, the run stops and reports what is left rather than finishing the set.
- A script driving this reads prior spend back off its own ledger, so a second process
  inherits the budget instead of restarting at zero.
- Retries are capped at 2 per originally requested image, and the extra spend is
  reported at the end from each response's `creditsCharged` — never from the estimate.
- Templates whose Model notes lead with a caveat are named as **skipped** in the report,
  not silently dropped.
- The template count comes from `prompt-library.md` at run time, never from a previous
  run's number.

**Fails if:** the run finishes the set past its ceiling; or the ceiling is checked only
against first attempts; or the final report sums estimates instead of charges.

---

## Notes on evidence strength

- **GI1's failure half is the best-measured thing in this file** — 34 templates, one
  product, three named fabrications, and a retry that cured one of them. The seed
  variability that moves the fix into the base prompt is from the later dogfooding run.
- **GI2 and GI3 are read off deployed spec with live verification stamps** (`2.16.0`
  2026-08-08; the edit arm confirmed live during the dogfooding run). GI3's flag-gating
  half is spec-read, not probed here.
- **GI4 is a repeat offence**, which is the argument for it existing: the field was
  available and the run still did the dance, because nothing an operator reads said so.
- **GI5's premise is measured** (the response is the only copy; the POST blocks long
  enough for an idle timeout to land). What is untested is an agent losing images to it
  in this pack.
- **GI6 is prospective and says so.** It is the one case here with no incident behind it.
- **No credit figures appear in this file by design.** Multiples and ordering survive;
  the number comes from `POST /v1/estimates` in the session that spends it.
