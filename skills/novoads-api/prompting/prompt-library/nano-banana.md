# Nano Banana Pro — image prompting and QA

**Vendor guide:** [Google Cloud — Ultimate prompting guide for Nano Banana](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana)

## The endpoint

**Image generation:** `POST /v1/images`. One endpoint serves every image model; you pick
with `model`.

It is **synchronous** — the call blocks for the render (typically 60–90 seconds) and comes back
with the finished images in `images[]`, along with `creditsCharged` and the `model` that ran.
There is no job to poll and no asset endpoint to wait on.

Use it for:
- Influencer recreation stills (see [influencer-recreation.md](influencer-recreation.md))
- Product showcase starting frames (see [product-showcase.md](product-showcase.md))
- Character sheets (see [character-sheet.md](character-sheet.md))
- Standalone stills (product heroes, lifestyle shots, etc.)

**There is no Nano Banana video route.** `/v1/b-roll` and `/v1/scene` do not exist on this API.
For an ambient product clip, generate a silent video with `omni-flash` or `seedance-2.0` — see
the `novoads-api` skill's SKILL.md.

## Model selection

There is **one** Nano Banana here: `nano-banana-pro`. The `nano-banana-2` / `nano-banana-edit` /
legacy `nano-banana` split is gone, so **there is no variant question to ask the user** — the
old "Nano Banana 2 or Pro?" prompt is void.

The image models, all on the same endpoint:

| API `model` value | When to use |
|---|---|
| `gpt-image-2.5-sunburst` (the API default since deployed spec 2.25.0) | Typography, dense small text, UI mimicry, and the one to name when labels and fine detail have to come back exact. Slower than Flare. |
| `gpt-image-2.5-flare` | The same grid and the same price as Sunburst, faster. The everyday choice in the GPT family. |
| `gpt-image-2` | The original GPT model, unchanged and still offered. Same six ratios, same reference cap, same prompt ceiling as the two above. |
| `nano-banana-pro` | Photoreal humans, material realism, multi-reference blending, character continuity. |
| `reve-2.1` | A deliberately different read on a concept, or a third opinion when the others miss. |

The three GPT rows differ in speed against fidelity and in nothing else a request body can see, so
moving between them is a one-word change that does not re-price the call.

**Credits:** every price comes from a live `POST /v1/estimates` in the current session. Do not
quote a figure from memory, from `logs/novoads-api.jsonl`, or from `MASTER_CONTEXT.md` — none of
them hold prices, deliberately. Report what actually happened from `creditsCharged` on the
response. **Name the model in the estimate body:** the schedules differ by more than 3× across
the five, so an estimate that omits `model` prices `gpt-image-2.5-sunburst`, the cheapest
schedule on the list.

## Request body

See [reference.md](../../reference.md) for the full schema. Key fields:

- `model` (required) — `nano-banana-pro` for the stills this file covers
- `prompt` (required) — the image prompt; follow the template and checklist below
- `aspectRatio` (optional, **defaults to `1:1`**): `nano-banana-pro` takes `1:1` `2:3` `3:2` `3:4` `4:3` `4:5` `5:4` `9:16` `16:9` `21:9`. Always set it explicitly; the default is rarely the shot you want. (the GPT models do **not** take `3:2`, `3:4`, `4:3` or `5:4`.)
- `referenceAssetIds` (optional): up to **14** `assetId` strings from `POST /v1/uploads` (spec 2.7.0; the three GPT models cap at 4, `reve-2.1` at 8). Order is preserved and may be addressed positionally from the prompt. Few well-chosen references beat many.
- `numImages` (optional, default 1) — 1–4 variants of the **same** prompt, in one call. Charged per image.
- `productId` (optional) — organizational only; it does not influence what is generated.

The request schema is **strict**: an unrecognized field, or an aspect ratio from another model's
grid, is a `400` before anything is charged.

**References are uploaded once.** `POST /v1/uploads` returns a durable `assetId` that keeps
working across calls and sessions. Re-uploading the same file produces a different id and loses
whatever identity anchor it was holding.

## Checklist

- [ ] Follow the vendor guide for framing **subject**, **style**, and **constraints**.
- [ ] State whether the output should be **photoreal**, **illustration**, **product hero**, etc.
- [ ] Set `aspectRatio` explicitly — never rely on the `1:1` default.
- [ ] Avoid polish words (`cinematic`, `ultra-detailed`, `hyperrealistic`). They produce the plastic "looks AI" render; describe the light source, the surface, the flaw instead. Nothing on the API checks this — the checklist is the check.
- [ ] Price the run with `POST /v1/estimates` and get an explicit yes before generating.
- [ ] Run **post-generation QA** (below) before treating the image as final.

### Post-generation QA (mandatory)

The response already contains the finished image, so QA happens immediately — there is no
polling gap. Check for:

- Extra or missing **hands** or **fingers**; wrong finger count; fused or blurred digits
- Wrong number of **limbs**; duplicated or missing arms/legs; impossible **joints** or poses
- **Face:** duplicate or merged features, asymmetry beyond natural range, distorted eyes or teeth
- **Objects:** merged geometry, floating items, melted product edges (product shots)
- **Artifacts:** obvious seams, texture soup, stray body parts at frame edges
- **Small text:** this is Nano Banana's weak spot. If legible dense text is the point of the image, the job belongs on `gpt-image-2`.

If anything looks off, follow the **Regeneration loop** — do not hand a defective still to the
user as the only option without at least one retry (unless they explicitly waive QA).

### Regeneration loop

1. **Inspect** the image from the `images[].url` in the response (the URL is presigned and expires — `expiresInSeconds` says when; re-read the job with `GET /v1/generations/{jobId}` for a fresh one).
2. If **defective:** compose a **new prompt** that names the fix (e.g. "exactly two hands visible, five fingers each," "single coherent face," "product label sharp and readable"). Keep the creative intent; add corrective constraints rather than resending the identical body.
3. Call `POST /v1/images` again with the same `model`, `aspectRatio`, `referenceAssetIds` and `productId` as before unless you are intentionally changing them.
4. **Cap:** at most **2** regeneration attempts after the first image (**3** total per deliverable). After that, describe the remaining issues, show the best attempt, and ask the user how to proceed.
5. **Credits:** each generation bills separately and there are no free re-rolls. QA retries use the QA-fix exception (no second pre-confirmation inside the cap) but are still billed — report the cumulative `creditsCharged` when you present results.
6. **Do not blindly retry a `500`.** There are no idempotency keys, so a resubmit can render and charge twice. Check `GET /v1/generations` for a job that already landed first. (A `502 provider_failed` is different — the provider broke and credits are refunded automatically.)

Full agent steps: [SKILL.md — Generated image QA](../../SKILL.md).

## Template

```text
{{SUBJECT}}. Style: {{STYLE}}. Composition: {{COMPOSITION}}. Lighting: {{LIGHT}}. Background: {{BG}}. Avoid: {{AVOID}}.
```

## Example

```text
Minimal product hero: matte black earbuds on concrete, soft studio three-point lighting, subtle reflection, no people, no extra props.
```

## curl example

```bash
source .env && curl -sS -X POST \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-pro",
    "prompt": "Minimal product hero: matte black earbuds on concrete, soft studio three-point lighting, subtle reflection, no people, no extra props.",
    "aspectRatio": "1:1"
  }' \
  "https://api.novoads.ai/v1/images"
```

The response is the finished job — `images[]` with presigned URLs, plus `creditsCharged` and the
`model` that ran. Price it first:

```bash
source .env && curl -sS -X POST \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "image",
    "model": "nano-banana-pro",
    "prompt": "Minimal product hero: matte black earbuds on concrete, soft studio three-point lighting, subtle reflection, no people, no extra props.",
    "numImages": 1
  }' \
  "https://api.novoads.ai/v1/estimates"
```
