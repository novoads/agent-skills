# Evals — nano-banana image ad

Written after the skill, to close the gap `scripts/check-evals-present.sh` had been
naming on every run. The cases are not invented for the occasion: five of the six
come from failures already recorded — three in the 2026-08-11/12 README-gallery
dogfooding run (RUN-FINDINGS items 2, 3 and 4), one in the 34-template measurement
this skill's hard rule 5 cites, and one in the spec change that PR #88 landed. Where
a case is prospective it says **untested** in its own text.

The shared library has its own file — [`shared/skills/image-ad-prompting/evals.md`](../../shared/skills/image-ad-prompting/evals.md)
— and it owns everything about template *content*. This file owns what happens when
this skill's caller is pointed at `nano-banana-pro`: the model's own caps, its own
failure shapes, and the two places where its sibling's numbers are wrong here.

**NB1 and NB2 are text assertions against the request body and the prompt**, checkable
before anything is charged. NB3 is a local behaviour of `generate_image.py`. NB4, NB5
and NB6 need a render.

---

## NB1 — Every label line is spelled out, in the base prompt

**Scenario.** A real product with a real label — a can, a bottle, a box — appears in
frame. The product photo is passed as a reference.

**Observed failure (dogfooding run, RUN-FINDINGS item 3, and validated repeatedly
across that run).** Pinning the product with a reference asset fixes the *primary*
mark and does not fix the rest of the label. The model invents **secondary label
lines** — a sourcing claim, an ingredient row, a back-of-pack panel — and renders them
as confidently as the real ones. The guard this skill shipped with assumes the model
can read the reference and copy what is written on it. **It cannot OCR the reference.**
The reliable fix is spelling every label line **verbatim in the prompt**.

**And it belongs in the base prompt, not the retry.** Label fabrication is
**seed-variable**: the same prompt produces a clean label on one draw and an invented
paragraph on the next, so a run that only adds the spelling after seeing a defect will
sometimes never see the defect and ship the un-guarded prompt.

**The counterpart trap, from the same run.** Added **shot-distance framing pins** can
blow banding artifacts — a white band across roughly the bottom 220 rows was observed.
Spelling is safe to add unconditionally; a framing pin is not, and earns a full-frame
artifact sweep when it is used.

**Assertions.**

- Every line of text that will be legible on the product is written out in the prompt,
  verbatim, in the **first** prompt sent — not added in a retry.
- The pin block is passed as `--pin-block "<one-line product description>"` rather than
  hand-written, so the script wraps the shared library's standard guard and counts it
  against this model's cap.
- Surfaces the ad does **not** show are excluded in words (*"front label only; no
  invented label copy, no barcode"*).
- Every third-party mark the concept needs — a logo, a publication wordmark, a prop
  brand — is passed as its own reference. Unpinned means invented.
- If a shot-distance framing pin is added, the QA pass in Phase 6 sweeps the **whole
  frame** for banding, not just the product.

**Fails if:** the label is pinned by reference alone; or the verbatim spelling appears
first in a retry prompt; or a clean first draw is read as evidence the prompt is safe;
or a framing pin is added and only the product region is inspected.

---

## NB2 — Fourteen here, four on the sibling, and the pack still says four in one place

**Scenario.** A likeness or multi-reference run that wants more than four references:
the product, the logo, a character shot, a style board, several face angles.

**Observed drift.** `nano-banana-pro` takes up to **14** `referenceAssetIds` — raised
from 4 in spec `2.7.0`, verified live 2026-08-04 with pinned out-of-range probes (15
refused, 14 accepted), and re-landed in this pack by PR #88. `gpt-image-2` takes 4 and
each Seedream 5 model 10. The number is per model and there is no single one.

**The stale copy was still on disk when this eval was written.** The `novoads-api` skill's
*Guardrails* list then read
*"Image `referenceAssetIds` caps are per model: 8 on `reve-2.1`, 4 on `gpt-image-2` and
`nano-banana-pro`"* — the pre-`2.7.0` value — while the same file's own `POST /v1/images`
section and `reference.md` both said 14. An agent that read the guardrail list last
capped itself at four on a model that takes fourteen, and it did so **silently**: nothing
refuses a short array. That line has since been corrected to 14, and closing it was not
this file's job — naming it was.

**Assertions.**

- A run on this model may pass up to 14 references and does not stop at 4.
- The number is never carried from `chatgpt-image-ad`, and never from a guardrail
  sentence in another skill. The authority is `reference.md`'s per-model table, and
  `./scripts/verify-image-caps.sh` is the standing re-check.
- A refusal reads `Too big: expected array to have <=14 items` and **nothing was
  charged** — it is a `400`, not a dropped image.
- Fourteen slots available is not fourteen slots spent: the skill still says that two
  to four well-chosen references usually beat many.

**Fails if:** the run caps at 4 on this model; or quotes 4 to the user as this model's
limit; or treats a `400` on the array as a charge.

---

## NB3 — Upload once; `--ref-asset-id` is the reachable path

**Scenario.** A batch — several prompts, or several variants of one concept — sharing
one product photo or one character shot.

**Observed failure (dogfooding run, RUN-FINDINGS item 4).** This skill's caller
**lacked `--ref-asset-id`** while its `gpt-image-2` sibling had it, so upload-once /
reuse was unreachable through the pack's own script: `--image-ref` uploads the file on
every invocation. Uploads carry no charge, so the cost was not credits: it was a repeat upload
and a **new** `assetId` on every invocation, for the same picture. PR #88 added the flag.

**Assertions.**

- A batch uploads each shared reference **once** and passes `--ref-asset-id <assetId>`
  on every subsequent call.
- The same `assetId` is used for the character reference across every variant in a
  series: one upload, one id, one picture.
- `--image-ref` and `--ref-asset-id` are understood as interchangeable and sharing the
  same 14-reference cap.
- The `assetId` is treated as reusable across calls and models; the presigned
  `uploadUrl` is not, and its expiry is not read as the asset expiring.

**Fails if:** a batch re-uploads the same file per prompt; or a run cites a different
picture for one character across its variants.

---

## NB4 — The image estimate returns warnings, and they are read

**Scenario.** Phase 4. The final prompt — the one carrying the always-on suffixes — is
priced.

**Observed drift, both directions (dogfooding run, RUN-FINDINGS item 2).** This skill
carried a stale note, stamped *"verified live 2026-08-04"*, saying an image estimate
came back with no `warnings` key at all. On deployed spec `2.19.0` it **does** return
them, with rules of its own — `banned_polish` and `blank_label` both observed live
2026-08-12. A file that says a signal does not exist is worse than one that says
nothing: the agent never looks.

**And they false-positive.** They match substrings and cannot tell a physical package
from a UI. The counterweight is on the record too: on the same run the estimate lint
was **right once** — a paraphrased `labelHold` clause tripped it, and pasting the
canonical sentence verbatim cleared it. So neither "always obey" nor "always ignore" is
the rule.

**Assertions.**

- The estimate is fired on the **final** prompt, with `model` named in the body — the
  image schedules differ by more than 3×, so pricing the wrong model quotes a number
  the invoice disagrees with.
- Every returned warning is read, and each one is judged **out loud** against what the
  prompt actually says, including where the matched substring sits.
- Overriding one is stated in a sentence to the user. Dropping one silently is a fail
  even when the override is correct.
- A suggested fix is never pasted into a prompt it does not fit.
- The estimate is understood as **not** proof the prompt is sendable: it skips
  moderation, so a cleanly-priced prompt can still come back `422 content_policy` with
  nothing charged.

**Fails if:** the run reports that image estimates carry no warnings; or acts on one
without reasoning; or drops one without saying so; or treats a clean estimate as a
guarantee.

---

## NB5 — N variants is one call

**Scenario.** The user asks for four variations of one concept.

**Why.** `numImages: 1`–`4` returns N images from **one** request, charged per image.
Four parallel requests produce the same images at the same price while burning four of
the organization's twelve image slots — and those slots are shared with every other image
call the organization runs through the API, so the cost lands on somebody's next image
rather than on this one, which is what makes it easy to keep doing.

**Untested as an agent run** — no recorded case of this skill fanning out. It is here
because the failure is invisible from inside the run that causes it.

**Assertions.**

- One `POST /v1/images` with `numImages: N`. No fan-out.
- `aspectRatio` is set explicitly on every call; the field defaults to `1:1` and a
  default-shaped ad is a wasted render.
- The quote shown to the user is the per-image number times N, with the total and the
  balance named before the yes.
- Every image is written to disk as it is read from the response.

**Fails if:** N parallel calls are fired for N variants; or `aspectRatio` is left to
default; or a total is shown without the per-image number behind it.

---

## NB6 — An edit request leaves this skill

**Scenario.** A finished image exists and the user asks to change something in it —
"remove the sticker", "make the background a kitchen counter".

**Why.** There is **no edit mode on this model**. `nano-banana-pro` does not publish
`sourceAssetId`; there is no mask, no inpainting, no img2img. Editing is a GPT-model
capability, which makes it a reason to switch skills rather than a reason to
approximate. The approximation is the failure: a reference-led regeneration reads like
an edit, costs like a render, and silently reinvents everything the user did not
mention.

**Assertions.**

- The run names the limitation and routes to `chatgpt-image-ad`. It does not
  reconstruct the image from references and present the result as an edit.
- Nothing is charged before the routing decision is made.
- The reverse also holds: a request that only this model's ratio set can serve —
  `3:2`, `3:4`, `4:3`, `5:4`, none of which exist on `gpt-image-2` — stays here, and
  the reason is stated.

**Fails if:** an edit is approximated with a fresh generation; or the user is told this
model can edit; or a ratio outside this model's ten is sent (a `400` before any charge).

---

## Notes on evidence strength

- **NB1 is the strongest case in this file.** Its defect was observed repeatedly across
  a paid run, its fix was validated in the same run, and its counterpart trap (banding
  behind a framing pin) was measured on a real frame. It is also the only case here
  whose correct behaviour changed *where* a rule goes — base prompt, not retry —
  which is a claim a reader would not guess.
- **NB2 is a live contradiction, not a historical one.** The stale guardrail line is on
  disk today and an agent reads it.
- **NB3 and NB4 are recorded run findings** whose remedies have already landed (#88 and
  the retired 2026-08-04 note). They are kept because a regression here is silent: a
  re-uploaded reference and a dropped warning both look exactly like a clean run.
- **NB5 and NB6 are design assertions,** marked untested where they are. NB6's
  capability half is read off the deployed spec rather than probed here.
- **No credit figures appear in this file by design.** The estimate arm quotes at spend
  time; ratios and ordering claims are what survive.
