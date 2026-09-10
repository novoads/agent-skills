# Novoads REST API reference

Companion to `SKILL.md`. Read that first for the call sequence. This file is the field-level detail and the lab notebook.

**The authority is <https://api.novoads.ai/v1/openapi.json>.** Where this file and the spec disagree, the spec wins, except in *Known discrepancies* below, where the spec is wrong and this file says so.

## Contents

**Before your first call**

- [Base URL and auth](#base-url-and-auth)
  - [Use `curl`. A `403` with `error code: 1010` is Cloudflare, not your key](#use-curl-a-403-with-error-code-1010-is-cloudflare-not-your-key) · [Ad analysis is on this API now](#ad-analysis-is-on-this-api-now)
- [Endpoints](#endpoints)

**Endpoint reference**

- [POST /uploads](#post-uploads)
- [POST /estimates](#post-estimates)
- [POST /videos](#post-videos)
  - [`audioEnabled`](#audioenabled) · [`startImageAssetId` and `referenceAssetIds` are two modes, not two fields](#startimageassetid-and-referenceassetids-are-two-modes-not-two-fields) · [`resolution` — on `seedance-2.0` and `seedance-2.5`, and it is a price field](#resolution--on-seedance-20-and-seedance-25-and-it-is-a-price-field)
- [POST /images](#post-images)
  - [Chain from `images[].assetId`, never from `images[].url`](#chain-from-imagesassetid-never-from-imagesurl) · [`sourceAssetId` — editing an image (spec 2.10.0, the GPT models only)](#sourceassetid--editing-an-image-spec-2100-the-gpt-models-only) · [The response is the only copy of images 2..N](#the-response-is-the-only-copy-of-images-2n)
- [POST /captions, POST /videos/{jobId}/captions](#post-captions-post-videosjobidcaptions)
  - [Presets and pricing](#presets-and-pricing) · [Failure modes](#failure-modes)
- [POST /transcripts](#post-transcripts)
  - [Pricing](#pricing) · [Failure modes](#failure-modes-1) · [What it does not do](#what-it-does-not-do) · [One thing it does that you cannot see](#one-thing-it-does-that-you-cannot-see)
- [POST /music](#post-music)
  - [Failure modes](#failure-modes-2)
- [GET /voices](#get-voices)
  - [Pricing](#pricing-1) · [Failure modes](#failure-modes-3) · [What it does not do](#what-it-does-not-do-1)
- [POST /voiceovers](#post-voiceovers)
  - [Pricing](#pricing-2) · [Failure modes](#failure-modes-4) · [What it does not do](#what-it-does-not-do-2)
- [POST /voice-changes](#post-voice-changes)
  - [Pricing](#pricing-3) · [Failure modes](#failure-modes-5) · [What it does not do](#what-it-does-not-do-3)
- [GET /generations](#get-generations)
- [GET /generations/{jobId}](#get-generationsjobid)
- [GET /generations/{jobId}/watch](#get-generationsjobidwatch)
- [GET /products, POST /products](#get-products-post-products)
- [GET /models](#get-models)

**Operating and troubleshooting**

- [Status lifecycle](#status-lifecycle)
- [Limits](#limits)
- [Errors](#errors)
  - [A 400 has one shape](#a-400-has-one-shape) · [The causes of a 429](#the-causes-of-a-429) · [The 500 rule](#the-500-rule)
- [Known discrepancies](#known-discrepancies)
- [Prompt rules](#prompt-rules)

*Hand-maintained: update it when you add, rename or reorder a heading, until CI generates this list.*

---

## Base URL and auth

```
https://api.novoads.ai/v1
Authorization: Bearer novo_<64 hex>
```

The key is shown once, at creation, and cannot be retrieved afterward. Create and revoke at <https://novoads.ai/dashboard/settings?tab=api>. Maximum 10 live keys per organization.

API generations draw from the organization's plan credits at the same rate as the dashboard. There is no separate API wallet, no free API tier, and no separate API plan: any live subscription, the $1 trial included, can generate here.

### Use `curl`. A `403` with `error code: 1010` is Cloudflare, not your key

**The API sits behind Cloudflare, and Cloudflare's bot rule refuses `python3-urllib` outright.** A request sent with Python's stdlib `urllib` default `User-Agent` comes back `403` carrying a bare edge page with **`error code: 1010`** — not a Novoads `{"error":{...}}` envelope, no `code`, no `requestId`. The same key, on the same endpoint, over `curl`, succeeds a second later.

It reads exactly like a revoked key or a dead subscription and is **neither**. Two tells:

- **The body is the wrong shape.** Every real Novoads failure is the `{"error":{"code",...,"requestId"}}` envelope in *Errors* below. An HTML-ish page with a numeric Cloudflare code never came from this API's application layer.
- **It hits everything at once.** On 2026-08-02 it took all three estimate calls simultaneously while a `GET /v1/products` issued moments earlier over `curl` had already succeeded. A genuine auth or plan failure would have refused that one too.

**The fix is the client, not the credential.** Use `curl`, as every example in this repo does. If you must call from Python, send a browser-like `User-Agent` — the default is the whole problem. Do not "fix" this by regenerating a key, checking the subscription, or telling the user their plan lapsed.

### Ad analysis is on this API now

Reading an existing ad into a structured hook, beats, casting and layout breakdown is **`POST /v1/analyses`** (spec `2.19.0`, verified live 2026-08-08). It is synchronous, the breakdown comes back in the response body, and there is no `jobId` to poll. The fee is **flat per call** whatever comes back — price it through `POST /v1/estimates` with `{"kind":"analysis"}` like every other spend, and quote the number that comes back rather than one from this file.

That fee is why it is never the default. Frames plus a transcript on the user's own machine cost nothing and read the whole runtime; the hosted call is what you reach for when there is no ffmpeg, when the read has to be structured rather than prose, or when the frame-by-frame pass has already failed. Offer it as the paid alternative, priced first, and let the user choose.

Older copies of this file said analysis was deliberately absent here. That stopped being true when `/analyses` shipped.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `POST` | `/uploads` | Mint a presigned PUT for a reference image or video. |
| `POST` | `/estimates` | Price a generation. Spends nothing. The only source of a credit number. |
| `POST` | `/videos` | Submit a video. `202`, charged, asynchronous. |
| `POST` | `/images` | Generate images. Synchronous, images in the response. |
| `POST` | `/music` | Generate a music bed from a prompt. `202`, charged, asynchronous. Returns **two** tracks. |
| `POST` | `/captions` | Burn subtitles into a generated or uploaded video. `202`, charged, asynchronous. |
| `POST` | `/transcripts` | The words of a video with their timings. **`200`, charged, SYNCHRONOUS — the transcript is in the response.** |
| `POST` | `/analyses` | Read an uploaded ad (video or still) into a structured breakdown. **`200`, charged, SYNCHRONOUS.** Flat per-call fee. |
| `POST` | `/competitor-ads` | Sweep a brand's live ads out of Meta's Ad Library. **`200`, charged, SYNCHRONOUS.** Behind a per-deployment flag. |
| `GET` | `/voices` | The voices you may speak in. Filterable, reads only, spends nothing. |
| `POST` | `/voiceovers` | Render a line of text as speech. **`200`, charged, SYNCHRONOUS — the mp3 is in the response.** Behind a per-deployment flag. |
| `POST` | `/voice-changes` | Re-perform the speech in a source in another voice. **`200`, charged, SYNCHRONOUS — the mp3 is in the response.** Behind a per-deployment flag. |
| `POST` | `/videos/{jobId}/captions` | Same operation, source in the path. Generated videos only. |
| `GET` | `/caption-presets` | The 30 caption styles, with tier and per-minute rate. |
| `GET` | `/generations` | List jobs, filterable and paginated. |
| `GET` | `/generations/{jobId}` | One job, with `outputUrl` once it has succeeded. |
| `GET` | `/generations/{jobId}/watch` | `302` to a freshly signed download URL. |
| `GET` | `/models` | The model catalog, with each model's grid and price. |
| `GET` `POST` | `/products` | List and create products. |
| `GET` `PATCH` `DELETE` | `/products/{productId}` | One product. |
| `GET` | `/products/{productId}/folders` | Folders under a product. Read-only. |

`GET /v1/openapi.json` is public and needs no key. There are **no** folder-creation, project, or add-to-project endpoints on v1.

---

## POST /uploads

Request:

```json
{ "contentType": "image/jpeg", "sizeBytes": 248193 }
```

`contentType` is one of `image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `video/quicktime`, `video/webm`, `audio/mpeg`, `audio/wav`. `sizeBytes` is the exact byte count, maximum 104,857,600 (100 MB).

**The two audio types are newer than the rest and only one endpoint consumes them** (verified live 2026-08-12, deployed spec `2.21.0`): `POST /voice-changes`, whose whole subject is speech that may not have a picture attached. Everywhere else an audio `assetId` is refused by kind — `POST /transcripts` names it and says so. Minting one is free either way, so an audio id sitting unused costs nothing; sending it to the wrong endpoint is a `400`, not a conversion.

Response `201`:

| Field | Meaning |
|---|---|
| `assetId` | Use in `startImageAssetId` and `referenceAssetIds`. Scoped to your organization. |
| `uploadUrl` | Presigned. PUT the raw bytes here. |
| `method` | The verb the URL was signed for. |
| `headers` | Send these on the PUT, byte for byte. |
| `expiresInSeconds` | 900. Request a new URL rather than retrying an expired PUT. |
| `maxBytes` | Ceiling this endpoint accepts. |

**`Content-Type` and `Content-Length` are both signed into the URL.** If either differs from what was returned, storage rejects the PUT with a 403 that looks like an auth failure and is not one. `image/jpeg; charset=utf-8` is the classic way to lose an hour here. Measure the file, do not estimate it.

**The `assetId` is durable and reusable, without limit.** It is the storage key itself, resolution is a stateless check plus a fresh presign on every call, and nothing consumes it: the same id works on call one and call one hundred, from `startImageAssetId` and from `referenceAssetIds`. Upload the product photo once and reuse it across every iteration and every model. The **900 second expiry belongs to the upload URL, not to the asset** — that is the distinction most likely to be conflated.

---

## POST /estimates

Discriminated on `kind`, and strict. Any field not listed is a 400.

**There are more than two arms.** `kind: "caption"` prices `POST /captions`, `kind: "transcript"` prices `POST /transcripts`, `kind: "voiceover"` prices `POST /voiceovers` and `kind: "voice-change"` prices `POST /voice-changes` — see those sections for their fields and for the reason a sourceless quote is the one-minute minimum on the three that are billed per minute. Which arms a deployment publishes is flag-dependent (`music`, `transcript`, `voiceover` and `voice-change` each have their own); read the live `openapi.json` `discriminator.mapping` rather than counting them here.

**An arm's `kind` names the OPERATION, and the job it prices names its OUTPUT.** You estimate `voiceover` and `voice-change`; you poll a job whose `kind` is `"audio"`, exactly as with `music`. Neither is a typo to be fixed.

| Field | `kind: "video"` | `kind: "image"` |
|---|---|---|
| `kind` | required, `"video"` | required, `"image"` |
| `prompt` | required | required |
| `model` | `seedance-2.0` (default), `seedance-2.5`, `seedance-2.0-mini`, `omni-flash`, `veo-3.1`, `sora-2` | `gpt-image-2.5-sunburst` (default), `gpt-image-2.5-flare`, `gpt-image-2`, `nano-banana-pro`, `reve-2.1` |
| `durationSeconds` | 4 to 30 | n/a |
| `resolution` | `480p` `720p` `1080p` `4k` — **range-checked per model** | n/a |
| `numImages` | n/a | 1 to 4 |
| `language` | `en` `es` `pt` `fr` `de` `it` `zh` `ja` `ko` `ar` `hi` | same |

All eleven models price here, `veo-3.1` and `sora-2` included (verified live, 2026-08-02; `seedance-2.5` added to the enum in deployed spec `2.13.0`, 2026-08-07).

**The `4 to 30` span is the OUTER bound across the whole set, and no model renders all of it.** Only `seedance-2.5` goes past 15 seconds; asking `seedance-2.0` for 20 is a `400` here rather than a quote for something it cannot render. The spec says so in the field's own description — read `GET /v1/models` for the per-model grid.

**`resolution` is accepted here because it moves the price** — on `seedance-2.0`, `480p` is ≈half the `720p` base, `1080p` is ≈2.5x it and `4k` ≈5x (the 480p arm re-priced 2026-08-07; the rest verified live 2026-08-04). Like `durationSeconds`, the enum in the table is the schema's union and **not** what any one model accepts: the service range-checks it against the named model, so `{"model":"seedance-2.0-mini","resolution":"1080p"}` comes back `400 resolution must be one of 720p for seedance-2.0-mini` while `720p` prices cleanly (verified live 2026-08-04). Full per-model table and the mini caveat under *POST /videos → `resolution`*.

There is **no `styleFamily`** on either arm. The field was deleted from the whole API in spec `2.0.0`, and both arms are strict, so a body carrying it comes back `400 (root): Unrecognized key: "styleFamily"` (verified live, 2026-08-02).

There is **no `audioEnabled`** on either arm, and that is deliberate rather than an omission: the field does not move the price, and this endpoint takes only fields that do. Sending it is `400 Unrecognized key: "audioEnabled"` even on `seedance-2.0`, where the *generation* call accepts it (verified live, 2026-08-02). Price the render without it; send it on `POST /videos`.

**`durationSeconds` is validated against the *named model's* grid here, not against the 4–30 span in the table.** Same behavior as the prompt ceiling: `{"model":"sora-2","durationSeconds":11}` comes back `400 durationSeconds must be one of 4, 8, 12 for sora-2.` while `8` prices cleanly (verified live, 2026-08-02). So the free call catches an out-of-grid duration before the paid one does — one more reason to run it every time.

Response:

| Field | Meaning |
|---|---|
| `credits` | What the generation would cost. |
| `balance` | Organization balance at read time. A snapshot, not a reservation. |
| `sufficient` | `balance >= credits` at that moment. |
| `shortBy` | Present when short. |
| `topUpUrl` | Present when short. |

| `warnings` | Advisory craft advice: `[{ rule, message }]`. Omitted when nothing fires. **This endpoint is the only one that returns it** (verified live 2026-08-04). |

**`warnings` never refuses the call and never changes `credits`** — and it false-positives. See *Prompt rules* below before you act on one.

Pass `model` explicitly. **At the same length the video schedules span more than 10x across the set, and more than 28x across every cell the deployment publishes** once length and resolution are counted too (both figures are derived by the API itself and printed in the `model` field's description — they moved when `seedance-2.5`'s thirty-second grid landed). Image schedules differ by more than 3x. Pricing the wrong model is a quote that disagrees with the invoice.

**The schema's 20,000-character `prompt` ceiling is not the one that binds.** The service applies the *named model's* limit here too, so a 5,000-character prompt priced as `seedance-2.0` is rejected at the estimate, for free, exactly as the paid call would reject it. Omit `model` and it is judged as `seedance-2.0`. Only `omni-flash` genuinely accepts 20,000.

This endpoint refuses a churned organization with a 403, on purpose. `sufficient` is a claim that the generation would go through, so answering `true` to an account whose generation would then be refused is a quote that disagrees with the invoice.

**Two things the estimate cannot see.** It never receives `aspectRatio`, `startImageAssetId`, `referenceAssetIds` or `productId`, because none of them moves the price. And it **skips moderation**, deliberately — running it would pay for a moderation call on every estimate for a verdict that almost never differs. So the one gap left is a prompt that prices clean here and fails moderation: `422` at generation. Nothing is charged in that case either.

**What this endpoint does with the prompt, exactly.** The price does not depend on it at all — that comes from the model and the duration, resolution or image count. The prompt is checked for two things: the named model's character ceiling, which is a hard `400`; and the craft rules, which are **advisory** and come back in `warnings` without affecting the price or the outcome. See *Prompt rules* below — they false-positive, so they are read and judged, not applied.

---

## POST /videos

Per-model request bodies, all `.strict()`.

**Shared by all six video models:** `model`, `prompt`, `durationSeconds`, `aspectRatio`, `language`, `startImageAssetId`, `productId`. Only `model` and `prompt` are required. Beyond that the variants differ, and every difference is a `400` rather than a dropped field:

- **`referenceAssetIds`** — the three Seedance variants only. `omni-flash`, `veo-3.1` and `sora-2` have no such field.
- **`audioEnabled`** — the three Seedance variants only. See below.

There is **no `styleFamily`** on any variant. It was deleted from the API in spec `2.0.0` along with the blocking prompt rules it scoped, and the variants are strict, so sending it is a `400`.

| `model` | `durationSeconds` (default) | `aspectRatio` | `refs` | `audio` | Prompt max |
|---|---|---|---|---|---|
| `seedance-2.0` | 4–15, any integer (**5**) | `16:9` (default) `9:16` `1:1` `4:3` `3:4` `21:9` | ≤9 | yes | 4,000 |
| `seedance-2.5` | **4–30, any integer** (**5**) | same | ≤9 | yes | 4,000 |
| `seedance-2.0-mini` | 4–15, any integer (**10**) | same | ≤9 | yes | 4,000 |
| `omni-flash` | 4, 6, 8, 10 (**8**) | `9:16` (default) `16:9` | — | — | 20,000 |
| `veo-3.1` | 4, 6, 8 (**8**) | `9:16` (default) `16:9` | — | — | 4,000 |
| `sora-2` | 4, 8, 12 (**4**) | `9:16` (default) `16:9` | — | — | 4,000 |

Defaults that bite: **the three Seedance variants default to `16:9`**, alone among the six — every other model already defaults to `9:16`. On duration, `seedance-2.0` and `seedance-2.5` default to 5 and mini to 10, `omni-flash` to 8, `sora-2` to 4, and **`veo-3.1` to 8, which is also its maximum** — the only model here that defaults to its ceiling. An out-of-grid `durationSeconds` is rejected, never rounded. Set both fields explicitly on any ad.

**`seedance-2.5` is the only model here that renders past 15 seconds**, and its grid is the same continuous integer range Seedance has always had — 4, 5, 6 … 29, 30, with no gaps. It is otherwise shaped exactly like `seedance-2.0`: same six aspect ratios, same `16:9` default, same 9 reference images, same `audioEnabled` toggle, same 4,000-character prompt ceiling. **The one place it is narrower is `resolution`** — see that section.

### `audioEnabled`

A boolean on **the three Seedance variants only** — `seedance-2.0`, `seedance-2.5` and `seedance-2.0-mini` — default `true`, so omitting it renders exactly what the endpoint rendered before the field existed. It controls the synchronized sound effects, ambient sound and lip-synced speech the model generates from the prompt.

Send `false` for a clip that is meant to be silent: a pipeline laying its own voice-over in post otherwise pays for a voice track it throws away, and a product cutaway built to run muted comes back with sound effects nobody hears.

**It does not change the price**, the length, or anything else about the grid — both Seedance providers charge the same either way, which is why `POST /estimates` refuses the field.

Verified live 2026-08-02, each probe pinned with an out-of-grid `durationSeconds` so no body could be valid and none could charge:

| Sent to | Result |
|---|---|
| `seedance-2.0`, `seedance-2.0-mini` (and `seedance-2.5`, from its published variant) | accepted — the only complaint was the pinned duration |
| `omni-flash`, `veo-3.1`, `sora-2` | `400 Unrecognized key: "audioEnabled"` |
| `POST /estimates`, any model | `400 Unrecognized key: "audioEnabled"` |

**Keep the prose silence clause in the prompt as well.** The flag mutes the render; the clause (`a silent product film with no spoken dialogue`) stops the model staging a talking shot in the first place — an actor mouthing nothing, billed in full. They do different jobs and the belt-and-suspenders pair is deliberate.

Response `202`: `jobId`, `status`, `creditsCharged`, `model`. **No `warnings`** — this endpoint does not run the prompt rules. They run on `POST /estimates` only (see *Prompt rules*), so the advice was already on the quote you took before submitting.

`creditsCharged` is in the unit the billing page shows. Internally 1 credit is 10 centi-credits; the API has already converted, so echo the number as given.

### `startImageAssetId` and `referenceAssetIds` are two modes, not two fields

Confirmed against the deployed spec `2.0.0` on 2026-08-02 (the `1.2.0`-era note that video took no references is superseded).

| | `startImageAssetId` | `referenceAssetIds` |
|---|---|---|
| What the model does with it | Animates the image as the **first frame** | **Composites** the images as visual references — a character, a product, a wardrobe, a setting |
| How many | 1 | Up to **9** |
| Which models | all six | the three Seedance variants only — `seedance-2.0`, `seedance-2.5`, `seedance-2.0-mini`. The `omni-flash`, `veo-3.1` and `sora-2` variants omit the field, and all three are strict (`400 Unrecognized key`, verified live 2026-08-02) |
| Addressed in the prompt | no | yes: `@Image1`, `@Image2` … in the order you send them |

**Sending both is a 400**, not a merge: they select different modes on the provider.

**Images only** — `image/jpeg`, `image/png`, `image/webp`. `POST /uploads` also accepts video, and a video `assetId` here is an error rather than a reference: the providers price video-input renders differently while the credit cost here is a function of duration alone, so accepting one would make the quote disagree with the invoice.

An `@ImageN` token pointing past the end of the array is refused **before the charge** — an unresolvable reference is a content failure at the provider, and a 400 is a better answer than a refunded render.

### `resolution` — on `seedance-2.0` and `seedance-2.5`, and it is a price field

Verified live 2026-08-04 against deployed spec **2.6.0**; `seedance-2.5`'s row read off deployed spec **2.13.0**, 2026-08-07. The earlier note here — that no variant had the field and `GET /models` published no output size — described an older deployment and is superseded.

| `model` | `resolution` accepted | Default |
|---|---|---|
| `seedance-2.0` | `480p`, `720p`, `1080p`, `4k` | `720p` |
| `seedance-2.5` | **`480p`, `720p` — and nothing above** | `720p` |
| `seedance-2.0-mini` | **none — the variant has no such property** | 720p, fixed |
| `omni-flash`, `sora-2` | **none** | 720p, fixed |
| `veo-3.1` | **none** | 1080p, fixed |

**`seedance-2.5` does not inherit 2.0's high tiers, and that is a provider fact rather than a rollout gap.** Neither provider serves the model above 720p at all, so `1080p` and `4k` are a `400` on it and always will be. Do not carry a resolution across a model switch: a workflow that renders `seedance-2.0` at `1080p` and then swaps the model id to `seedance-2.5` is a rejected request, not a downgrade.

**`GET /v1/models` now publishes this**: each entry carries `resolutions[]` and `defaultResolution`. That is the authority — read it rather than trusting this table, which is a snapshot.

**It changes the price**, which makes it unlike every other output-shape field here. Relative to the `720p` base, each tier is its own credit schedule rather than a surcharge on the one below it:

| `resolution` | `seedance-2.0` | `seedance-2.5` |
|---|---|---|
| `480p` | **≈half** the base | **≈half** the base |
| `720p` | base (default) | base (default) |
| `1080p` | ≈2.5x | **not accepted** |
| `4k` | ≈5x | **not accepted** |

**`480p` changed on 2026-08-07.** It used to cost the same as `720p`, so there was no reason to ask for it. The family-wide reprice that shipped alongside `seedance-2.5` put it at roughly half — a price *decrease* on live models, so nothing that rendered yesterday costs more today, but a workflow that skipped `480p` on the old advice should reconsider it. **It is only reachable on the two models that take the field**: `seedance-2.0-mini` still publishes no `resolution` property and still range-checks the estimate arm to `720p`, whatever the dashboard charges for a mini draft.

Those are ratios, not a rate card — they exist so you can warn a user that `4k` is a five-fold decision before they ask for it. **The number they approve still comes from `POST /estimates`**, and this repo holds no rate table (see SKILL.md gate 2).

**`POST /estimates` takes `resolution`** on the video arm and prices it, so the quote can track the tier you actually intend to render.

**The `seedance-2.0-mini` split-brain, verified live 2026-08-04.** The estimate arm's `resolution` enum is shared across all six models, but the server range-checks it per model:

| Call | Result |
|---|---|
| `POST /estimates`, mini, `resolution: "720p"` | `200` — priced, identical to omitting the field |
| `POST /estimates`, mini, `480p` / `1080p` / `4k` | `400 invalid_input` — *"resolution must be one of 720p for seedance-2.0-mini"* |
| `POST /videos`, mini, any `resolution` | `400 Unrecognized key: "resolution"` — the variant has no such property (**observed 2026-08-04, not re-verified**: confirming it again means a paid render) |

**So an estimate that accepted `resolution` is not a licence to send it to `POST /videos`.** On mini, never send the key at all.

Output size actually measured, at `9:16`: `seedance-2.0` at its `720p` default and `sora-2` both returned **720x1280** (2026-08-02, ffprobe). `omni-flash` and `veo-3.1` are unmeasured — do not quote a number for them, and do not generalise 720p across the set now that Veo is on it.

There are **no idempotency keys.** See the 500 note below.

---

## POST /images

| `model` | `aspectRatio` | `referenceAssetIds` | `numImages` | Prompt max |
|---|---|---|---|---|
| `gpt-image-2.5-sunburst` (default) | `1:1` (default) `4:5` `2:3` `9:16` `16:9` `21:9` | up to **4** | 1 to 4 | **32,000** |
| `gpt-image-2.5-flare` | same six | up to **4** | 1 to 4 | **32,000** |
| `gpt-image-2` | same six | up to **4** | 1 to 4 | **32,000** |
| `nano-banana-pro` | `1:1` `2:3` `3:2` `3:4` `4:3` `4:5` `5:4` `9:16` `16:9` `21:9` | up to **14** | 1 to 4 | **50,000** |
| `reve-2.1` | same as Nano Banana Pro | up to **8** | 1 to 4 | **4,000** |

**The default moved to `gpt-image-2.5-sunburst` in deployed spec 2.25.0** (2026-09-10), from `gpt-image-2`. A call that omits `model` renders on Sunburst and the response's `model` field says so, and reading it rather than assuming is the habit that survives the next move. `gpt-image-2` is untouched: still live, still offered, still the same grid and the same price. Nothing about an existing call changed except what an unqualified one lands on.

**The three GPT models are one grid with two dials.** `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare` and `gpt-image-2` publish the same six aspect ratios, the same cap of 4 reference images, the same 32,000-character prompt ceiling, the same `sourceAssetId` edit arm and the same price per image. So switching between them changes the `model` value and nothing else in the body, and it does not re-price the call. What differs is speed against fidelity: Flare is fast and is the one to reach for on most images; Sunburst is slower and keeps fine detail and labels exact. On our own ten-prompt comparison the two were judged even on label text, logo geometry and product shape, so treat the difference as a latency-versus-detail preference rather than a quality ranking, and do not promise a customer a better render from either one.

**The prompt ceiling is per model too, since deployed spec 2.16.0.** It was 4,000 on all three of the models that existed then; now only `reve-2.1` carries that number, the three GPT models take 32,000 and `nano-banana-pro` 50,000. The two 2.5 ids arrived after the split and have never carried 4,000. Read off the live per-model request schemas and verified on 2026-08-08. The consequence worth knowing is the reverse of the reference cap's: a prompt written for one model is not automatically sendable to another, and a run that switches `model` to `reve-2.1` for a second opinion can be refused on length alone with nothing else changed. The refusal is a `400` and charges nothing.

**One thing this does not cover: `POST /estimates` does not share these numbers.** Its own request schema caps `prompt` at 50,000 for every image model, so a 20,000-character `reve-2.1` prompt prices cleanly and is then refused by `POST /images`. A clean estimate is proof of the price, not of the length.

**The reference cap is per model and is not uniform.** Each of the three GPT models takes 4, `nano-banana-pro` 14, `reve-2.1` 8. Do not carry one number across the set: the bodies are strict, so a fifth reference to `gpt-image-2` is `400 Too big: expected array to have <=4 items` rather than a silently dropped image, which is the good outcome: a dropped reference is a paid render missing the product. Verified live 2026-08-04 against spec 2.7.0 (which raised `nano-banana-pro` from 4 to 14), each probe pinned with an out-of-range `numImages` so no body could be valid: 15 refs on `nano-banana-pro` → too big, 14 → accepted; 9 on `reve-2.1` → too big, 8 → accepted; 5 on `gpt-image-2` → too big. The two 2.5 models arrived at 4 as well, read off their published schemas in deployed spec 2.25.0. Their vendor accepts more, and 4 is where this API holds them. Standing re-check: `./scripts/verify-image-caps.sh`.

Synchronous. The response carries `images[]` (`url`, `expiresInSeconds` 3600, `assetId`, `width`, `height`), `jobId`, `status`, `creditsCharged`, and `model`. **No `warnings`**, for the same reason as video: the prompt rules run on `POST /estimates` only — where an image prompt *does* get read. `banned_polish` and `blank_label` observed on a `kind: "image"` estimate against deployed spec 2.19.0 (verified live 2026-08-12); the older note here, that images returned no `warnings` key at all, described the 2026-08-04 deployment. Nothing to poll. `numImages` multiplies the price.

Reference order is preserved and can be addressed positionally by the prompt. There is no base64 field: upload first, pass ids.

Images accept **no `startImageAssetId`** — there is no first-frame concept on a still — and **no `styleFamily`**, which no longer exists anywhere on this API.

### Chain from `images[].assetId`, never from `images[].url`

**A generated image URL is not an asset id.** `url` is a one-hour presign for fetching the
bytes and nothing downstream accepts it; the id sits beside it as `images[].assetId`, and that
is what `referenceAssetIds` / `startImageAssetId` on `POST /videos` and `referenceAssetIds` /
`sourceAssetId` on `POST /images` take — no download and no re-upload hop. Read off deployed
spec 2.19.0 on 2026-08-12, after a run that did the download-and-re-upload dance because this
page had never named the field. It is **optional** in the schema, so read it rather than assume
it: if a response ever omits it, the fallback is downloading the bytes and minting an id with
`POST /v1/uploads`.

### `sourceAssetId` — editing an image (spec 2.10.0, the GPT models only)

Pass an `assetId` as `sourceAssetId` and the prompt describes the CHANGE rather than the
whole picture. Same endpoint, same `ImageJob` response, same price as a generation of the
same size — an edit is one image, charged once.

| | |
|---|---|
| Models | The three GPT models only: `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare` and `gpt-image-2`. The field is ABSENT from the `nano-banana-pro` and `reve-2.1` variants, and `.strict()` refuses it there. |
| `aspectRatio` | **Cannot be combined.** Sending both is `400`, not a silently-ignored field. |
| Output shape | Tracks the source: the service measures it and renders the closest cell of the model's grid. Portrait never becomes landscape, or the reverse — but the grid has nothing between `1:1` and `16:9`, so a 4:3 source renders `1:1`. |
| `referenceAssetIds` | Still allowed. The source **counts against the same cap** and is always first. |
| Source type | Images only. A video assetId is refused by extension before anything is fetched. |

**It is flag-gated, and the flag gates the SCHEMA.** Where the deployment has it off,
`sourceAssetId` does not appear in `CreateImageRequestGptImage2` at all and the request is
refused like a typo. So `GET /v1/openapi.json` is the honest capability check: if the
property is absent, this deployment cannot edit, and no retry will change that.

### The response is the only copy of images 2..N

A `numImages > 1` call charges for every image, but only the **first** is recoverable
afterwards. `GET /generations/{jobId}` returns a single `outputUrl` — image 1 — and images
2..N exist nowhere but the body of the response that returned them. Lose that response and
the credits stay spent.

That is not a hypothetical: the render blocks inside the POST for 60–90 seconds, so a
proxy or CDN idle-timeout on a long call drops a response for work the API already did and
charged for. Two consequences worth building around:

- **Write each image to disk as you read it**, before doing anything else with the response.
  Do not hold a batch in memory and save at the end.
- **Prefer one image per call in a long batch.** `numImages: 4` is one concurrency slot and
  the same price as four calls, which is the right trade when four variants of one prompt
  are wanted. It is the wrong trade when the four are independent deliverables, because it
  puts three unrecoverable images behind a single response.

  Since spec `2.12.0` this costs you nothing in throughput: images have their **own** budget
  of **12** concurrent jobs, so twelve single-image calls run at once and each response is
  independently recoverable. Fire the batch twelve wide rather than serialising it — 36
  images is three waves, not thirty-six calls in a row.

If a call does time out, do **not** re-send it — there are no idempotency keys, so a retry
renders and charges again. Check `GET /generations` first and match on `createdAt`; a job
that landed is already there, and image 1 is retrievable even though its siblings are not.

---

## POST /captions, POST /videos/{jobId}/captions

Documented from the live spec `2.6.0` on 2026-08-04. This endpoint family was **missing from this pack entirely** until then; the decision tree routed every caption request to the local ffmpeg skill as though no first-party endpoint existed.

Burns styled subtitles into a video and returns a `jobId`. **Asynchronous and charged**, exactly like `POST /videos`: poll `GET /generations/{jobId}` to a terminal status, then `…/watch`.

| Field | `POST /captions` | `POST /videos/{jobId}/captions` |
|---|---|---|
| `preset` | **required**, one of 30 | **required**, one of 30 |
| `jobId` | in the body — a video this API generated | **in the path** |
| `assetId` | in the body — a video you uploaded | not expressible |

Both bodies are strict (`additionalProperties: false`). **Exactly one of `jobId` and `assetId`** on `POST /captions`; sending both is a `400` rather than a guess, because captioning the wrong one of two sources still bills for it. The path form exists because an `assetId` contains slashes and cannot be a path segment.

**The subtitle text is transcribed from the video's own audio. There is nothing to write, and there is nothing to read back FROM THIS ENDPOINT:** no response and no field on a caption job carries the caption text or its timings. `GET /generations/{jobId}` on a caption job returns `outputUrl` and no transcript. **The output is a new MP4 with the subtitles burned in — there is no SRT on the captions endpoint** (verified 2026-08-04, still true).

**A workflow that needs the WORDS uses `POST /transcripts`, not this.** That endpoint returns text, word-level timings and an SRT in one synchronous call, and it runs on the BASE video — which is where you want it anyway, because b-roll placement is read from the transcript before the captions step. Captioning and transcribing are two operations, priced separately.

Response `202`: `jobId`, `status`, `creditsCharged`, `model`. `model` is always **`captions-v1`** — a fixed identifier, identical on every caption job, deliberately not in `GET /models`, because that endpoint answers what this API can *generate* with and a caption is applied to a video that already exists.

### Presets and pricing

`GET /caption-presets` → `{ "presets": [{ "id", "tier", "credits" }] }`. **30 presets in two tiers** — `basic`, and the costlier `dynamic`. The `credits` field on each entry is that preset's per-billed-minute rate and is the only place to read it; this file deliberately does not restate the numbers, because a rate copied into a skill file goes stale without anything going red. The `dynamic` nine are `glass`, `whisper`, `glide`, `glide2`, `fusion`, `terminal`, `handwritten`, `backdrop`, `backdrop2`.

The meter is `rate x whole minutes, rounded up, minimum one`, **doubled again above the 1080p tier, measured on the SHORT edge** — a portrait `1080x1920` is 1080p held sideways and is *not* doubled; a true 4K source is. Duration and resolution are read from the file at request time, not declared. Everything this API generates is ≤30s (`seedance-2.5`'s ceiling; every other model stops at 15), so it still bills exactly one minute.

**`POST /estimates` has a third arm for this:** `{ "kind": "caption", "preset", jobId | assetId }`. `preset` is required; the source is optional but **name it for anything over a minute**, because a sourceless quote is the one-minute minimum. A sourceless quote therefore returns exactly that preset's tier rate for one minute — verified live 2026-08-04 against `basic` (`casper`) and `dynamic` (`glass`), each matching its own entry in `GET /caption-presets`. No prompt, so no `warnings`.

### Failure modes

| Code | Cause |
|---|---|
| `400` | Both source fields, a still passed as `assetId`, or a file that cannot be measured. **A source we cannot measure charges nothing** — unpriceable is unbillable. |
| `402` | Not enough credits; `details` carries `required` and `available`. |
| `404` | No such job or asset **for this organization**, or an upload that never completed. A `jobId` from the dashboard answers 404 identically to one that does not exist — a distinguishable response would be a way to probe what else the account holds. |
| `409` | The source job has not succeeded yet, **or it was rendered with `audioEnabled: false`**. No speech to transcribe, and an empty result you were charged for is worse than a refusal. |
| `429` | `details.reason: caption_concurrency_limit` — **10** concurrent caption jobs, counted **separately** from the 5-generation `concurrency_limit`, so a batch of captions can never block the next render. |

**Re-captioning the same video in the same preset is idempotent and free**: the second call returns the *first* job's id and charges nothing, enforced by a database constraint, so two identical requests racing cannot double-charge. **A different preset on the same video is a new job and a new charge** — style iteration is not free.

---

## POST /transcripts

Documented from the live spec `2.8.0` on 2026-08-04. Gated on `TRANSCRIPT_API`; where the flag
is off the path 400s with a message naming what the deployment does render.

The words of a video, with their timings. **Synchronous** — `200`, and the transcript is in the
response body. There is no `jobId` to poll. It is the **second** charged endpoint here that answers with its
result rather than a job to wait on — `POST /images` is the precedent and states the rule — and it
is deliberate: the provider is one round-trip with no job id of its own, so there is nothing to
poll and nothing to strand.

Measured 2026-08-04: a 15-second ad comes back in about a second, a 5-minute source in ~25s, a
10-minute one in ~46s.

| Field | Type | Notes |
|---|---|---|
| `jobId` | string, optional | A video this API generated. **Exactly one of `jobId` / `assetId`.** |
| `assetId` | string, optional | A video you uploaded with `POST /uploads`. **Video only, and that is now a refusal rather than an impossibility**: since `2.21.0` uploads mint `audio/mpeg` and `audio/wav` ids too, and this endpoint names them and refuses them. Exactly one. |
| `languageCode` | string, optional | `en` `es` `pt` `fr` `de` `it` `zh` `ja` `ko` `ar` `hi`. **Omit it.** Auto-detect is the right default; forcing the wrong language does not fail, it returns a confidently wrong transcript. Note the local `caption-video` path has the OPPOSITE default (it forces English), so do not assume parity. |

Body is strict. There is **no granularity knob** — every response carries all three renderings,
because they are three views of one call and cost nothing extra.

Response `200`:

| Field | Meaning |
|---|---|
| `jobId` | Addressable afterwards at `GET /generations/{jobId}`, whose `outputUrl` presigns the same JSON. |
| `status` | Always `"succeeded"` — the transcript is right here. |
| `creditsCharged` | What this call **was billed**. `0` most often means the transcript was already stored (see below); it also covers a rare race where the job's charge had already been reversed. Treat `0` as "not billed", not as "served from cache". |
| `model` | Always `transcript-v1` — a fixed identifier, identical on every transcript. Do not branch on it. |
| `language` | What the transcriber detected, **verbatim, as ISO-639-3** — `"spa"`, `"eng"`. Not the two-letter code. |
| `durationSeconds` | Length of the source. |
| `text` | The whole transcript as one string. |
| `words[]` | `{ text, start, end }` per word. **Real words only** — the vendor's whitespace tokens are filtered out, so `words.length` is a word count. |
| `segments[]` | `{ start, end, text }` per sentence. |
| `srt` | The same transcript as a SubRip file. |

> **ALL TIMINGS ARE SECONDS**, as decimals — `0.42`, not `420`. The local `caption-video` path
> reports the same concept in **milliseconds**. Mixing them up is a 1000x error that still looks
> plausible, and it is the single most likely way to get this wrong.

### Pricing

Billed **per BILLED MINUTE**, `ceil(seconds / 60)` with a one-minute floor, so a 15-second ad
and a 55-second one cost exactly the same and a 10-minute source costs ten times that. There
is **no resolution term** — unlike captions — because the transcriber is billed on duration
and never sees the picture. The rate itself comes from the estimate arm below, not from here.

**`POST /estimates` has its own arm:** `{ "kind": "transcript", jobId | assetId }`. Source is
optional; name it for anything over a minute, because a sourceless quote is the one-minute
minimum. The arm is **strict and narrower than the generate body** — sending `languageCode` to
the estimate is a `400`, because it does not move the price.

**Transcribing the same source twice is free.** The second call returns the stored transcript
with `creditsCharged: 0`. So a client that times out and retries is not billed twice, and two
skills that each want the same words pay once between them. Verified live 2026-08-05: second call
`creditsCharged: 0`, same `jobId`, every field byte-identical, and **one** charge in the ledger
across both.

What counts as "the same source" is finer than the id, deliberately: the cache identity is
(organization, R2 key, **byte length**, model, language, vocabulary). So a different
`languageCode` is a different transcript rather than a cache hit; **re-uploading different bytes
under the same `assetId` normally MISSES** rather than serving the old words for new media; and a
vocabulary upgrade on our side misses once so the next call gets the better transcript.

The byte-length half is a cheap content check, not a checksum: it catches every ordinary
re-upload, but **a replacement of exactly the same size is still a HIT** and returns the previous
file's words for free. If you replace media in place and need it re-read, upload it under a new
`assetId`.

### Failure modes

| Code | Cause |
|---|---|
| `400` | Both source fields or neither; an unknown key; a source **over the 10-minute cap** (named in the message); or the flag being off on this deployment. **Nothing is charged** for any of those — they are all decided before the debit. One 400 is the exception and arrives *after* it: a container whose declared duration disagrees with its real contents is caught during audio extraction, so it is charged and then refunded. |
| `402` | Not enough credits; `details` carries `required` and `available`. |
| `404` | No such job or asset **for this organization**, or an upload that never completed. **Also a video generated outside this API** — a dashboard `jobId` answers 404 identically to one that does not exist, because a distinguishable response would be a way to probe what else the account holds. **Also a CAPTION job's id**: a caption's output is not a transcript source, and the message says so — pass the jobId of the ORIGINAL video. (An `assetId` that names a still rather than a video is a `400`, not a 404 — nothing is missing, it is the wrong kind.) |
| `409` | Several causes, and **whether you are charged depends on which** — the message always says so. *Before the debit, nothing is charged:* the source job has not succeeded, it has no stored file yet, its stored file could not be read just now (retryable), it has **no audio stream at all** (every b-roll clip is this shape), or a transcript of this source is **already in flight** (the message names the job to poll). *After the debit, charged and then refunded:* the track exists but carries **only room tone**, so no speech was detected — the pre-charge check reads streams, and a stream of silence is still a stream — or the audio could not be extracted. |
| `429` | `details.reason: transcript_concurrency_limit` — **10** concurrent transcripts, counted separately from both the 5-generation `concurrency_limit` and the caption ceiling. |
| `502` | The transcriber failed. **Read the message for the money**, which is not always the same sentence: `Credits were refunded.` means the reversal already landed, while `The refund did not go through on this attempt and has been queued; your credits will be returned automatically.` means it has **not** come back yet and a backstop will return it. |

### What it does not do

No diarization, no speaker labels, no translation. The transcript is faithful to what was said,
in the language it was said in.

### One thing it does that you cannot see

Every call is sent a **server-side biasing vocabulary** — product and model names, so the words
that recur in these scripts are spelled the way we spell them. It is not a request field and you
cannot set it. It can change the words you get back, and changing it invalidates the cache (that is
the "vocabulary" term in the identity above). It biases toward known words; it **cannot** recover a
word the speaker did not say — a script that spells a brand phonetically will transcribe as the
phonetic spelling.

---

## POST /music

Documented from the live spec `2.7.0` on 2026-08-04, against a deployment with the endpoint enabled.

Renders a music bed from a prompt and returns a `jobId`. **Asynchronous and charged**, exactly like `POST /videos`: poll `GET /generations/{jobId}` to a terminal status. Typical renders finish in about **75 seconds** — much faster than a video.

| Field | Required | Notes |
|---|---|---|
| `prompt` | **yes** | 1–500 chars. What the track should sound like, as prose: instrumentation, mood, tempo, what it sits under. |
| `style` | no | ≤200 chars. Folded **into** the prompt on our side, not sent as a provider field. |
| `instrumental` | no | Defaults to **`true`**. Leave it — lyrics compete with the voice-over. |
| `durationHintSeconds` | no | 5–180. **Advisory only.** |
| `productId` | no | Files the job under a product. Organizational only. |

The body is strict: an unknown key is a `400`, not a shrug.

**The 500-character ceiling applies to the COMPOSED prompt, not to your field alone.** `style`, the instrumental sentence and the duration hint are all concatenated into one string before submission, and *that* is what is measured — before the charge, so an over-long compose is a free `400` rather than a billed `502`. Leave headroom: a 500-character `prompt` plus any `style` at all is over the line.

**`durationHintSeconds` is a preference, not a setting.** The provider takes no duration parameter in the mode this endpoint uses, so the hint is prose in the prompt. Expect roughly **one to two minutes** of audio whatever you ask for, and trim it yourself. It does not move the price.

**One request returns TWO tracks, for one charge.** The model renders two takes of the same prompt. Both arrive in `audio[]` on the polled job and both are yours; they differ in length and arrangement, not in price. That is why the mixing step can offer named variants without a second render — see the `music-mix` skill.

Response `202`: `jobId`, `status`, `creditsCharged`, `model`. `model` is a **fixed internal identifier** for the music renderer, identical on every music job, and deliberately absent from `GET /models`, which answers what this API renders *video* with. Do not branch on its value.

**`POST /estimates` has a fourth arm for this, and it takes nothing but the kind:**

```json
{ "kind": "music" }
```

Sending `prompt` alongside it is a `400` (`Unrecognized key: "prompt"`) — the price is **flat per request**, so there is nothing to price on. Verified live 2026-08-04: the arm returns a `credits` number and **no `warnings` key**, because there is no visual prompt to advise about. Take the fee from that call.

**Mind the kind asymmetry, it is deliberate:** you *estimate* `kind: "music"` and you *poll* a job whose `kind` is `"audio"`. The estimate names the operation; the job names its output. Neither is a typo to be fixed.

**This endpoint is behind a deployment flag.** Where music is off, `POST /v1/music` answers `400 invalid_input` — not a `404` — and the `music` estimate arm and the `/music` path are absent from `GET /v1/openapi.json`. Check the spec before assuming an outage.

### Failure modes

| Code | Cause |
|---|---|
| `400` | Missing/over-long `prompt`, an over-long **composed** prompt, an unknown key, or music disabled on this deployment. Nothing is charged. |
| `402` | Not enough credits; `details` carries `required` and `available`. |
| `429` | Concurrency ceiling — a music job consumes one of the **5** shared generation slots, the same pool as video. |
| `502` | The provider refused or failed. Terminal, and refunded. |

A prompt the provider's own classifier refuses comes back as terminal status **`blocked`**, not `failed` — rephrase it rather than retrying it, because a retry buys the same refusal.

---

## GET /voices

Documented from the live spec `2.21.0` on 2026-08-12, and **missing from this file entirely
until then** — every skill that cast a voice was reading the one-line summary in
`SKILL.md`'s call list.

The voices `POST /voiceovers` will speak in and `POST /voice-changes` will convert to: the
platform voices plus **your own** organization's cloned and designed ones. Another
organization's clones are never listed, and asking for one by id is a `404`.

Reads only. Spends nothing, and unpaginated — a list to pick from, not a feed.

| Param | Matching | Notes |
|---|---|---|
| `gender` | whole value, case-insensitive | `male`, `female` are what the catalog records |
| `age` | whole value, case-insensitive | `young`, `middle_aged`, `old`. Matched whole, so `old` does not also mean `middle_aged` |
| `accent` | **substring**, case-insensitive | open-ended prose that drifts with the provider. `american` finds `african american` **and** `latin american`, roughly one result in eight |
| `language` | base subtag | `es` finds a voice recorded as `es` or `es-CL`; `et` stays Estonian. The same rule `POST /voiceovers` applies to its own `language` |
| `limit` | applied **after** the filters | **1–200**, and a cap rather than a page — no cursor, no continuation. Outside that range is a `400` |

**Filter, always.** Unfiltered this is thousands of voices and megabytes of JSON, which an
agent pays for in context. Measured live 2026-08-12: `gender=male&language=en` returned
**5,362 voices and 3.8 MB**; adding `age=young` cut it to 1,762 and 1.2 MB; adding
`accent=american` to 875 and 598 KB. Filters AND together.

**`limit` is not a sample.** The list comes back ordered by name, so `limit=12` on a
filtered read hands you twelve voices whose names begin with A — verified live on the same
day. Use it to bound a response you are about to page through in code, not to pick
candidates: for that, read the filtered list and sample it yourself.

**A filter hides an unlabelled voice, except your own.** `gender`, `age` and `accent` read
labels the provider records, and a voice carrying none of them drops out of a filtered list.
Your organization's own cloned and designed voices come back under **every** filter
regardless — a clone is recorded with no labels at all, and a demographic filter would
otherwise erase the voices you made. In a filtered list they sort **after** the matches, so
`limit` trims them before it trims the brief.

Per voice: `id`, `name`, `source` (`platform` | `organization`), and where recorded
`previewUrl`, `languages`, `primaryLanguage`, `category`, `labels`.

**`previewUrl` is a few seconds of the voice speaking, served from the provider's CDN
without an API key.** Audition before you spend. It is absent where there is no sample,
which is the normal case for a voice your organization cloned. `languages` is absent for the
same voices, and a voice with no recorded languages accepts **any** `language` on
`POST /voiceovers` while dropping out of a `language`-filtered list here.

### Pricing

Free. It is a read.

### Failure modes

`401` on a bad key, `403` on an organization that may not use the API. A filter value that
matches nothing is an empty `voices` array and a `200`, not an error.

**There is also a `400`, and it is easy to trip:** a `limit` outside 1–200, a `language`
that is not a language tag — and **voice-over generation being off on this deployment**.
That last one matters to a caller reading a catalog before a conversion: this read is
gated by the same flag the generation is, so on a deployment without it the *audition*
fails first, at the same `400`, and it is not a bad key.

### What it does not do

No free-text search, no pagination, no ordering control, and no acoustic information: the
labels describe a voice in words, and words are not a register. Two voices labelled
identically can sit an octave apart. If the job is to match an existing performance, measure
the candidates — `change-voice` ships a script that does exactly that.

---

## POST /voiceovers

Documented from the live spec `2.21.0` on 2026-08-12. Gated on a per-deployment flag; where
it is off the path answers `400` with a message naming what the deployment does render.

Renders a line of text as speech and returns **the finished mp3** — `200`, not `202`. The
provider answers in seconds and returns bytes rather than a job id, so there is nothing to
poll. The `jobId` in the response exists to reconcile spend and to find the call again in
`GET /generations` when **the response itself** is what times out. If that happens, do not
call again: the audio was probably rendered and charged.

| Field | Required | Notes |
|---|---|---|
| `script` | **yes** | 1–1,000 characters, about 40 seconds. Read **VERBATIM**, including anything in square brackets — the model reads those as performance tags rather than skipping them, so keep stage directions out |
| `voiceId` | **yes** | no default, ever. From `GET /voices` |
| `language` | no | ISO 639-1. Validated against the voice's own recorded languages |
| `productId` | no | files the job under a product. Organizational only |

Body is strict. Response `200`: `jobId`, `assetId`, `url`, `expiresInSeconds`,
`creditsCharged`, `characters`, `voiceId`. **Download `url` immediately** — it is minted per
response and time-limited; `assetId` is the durable handle.

**`voiceId` is required and has no default.** A default voice is a performance you would be
charged for without hearing it, and it would move under you whenever the catalog is
re-synced.

**A script over the cap is refused before anything is charged**, rather than rendered as one
long take. That is the right shape anyway: one call per line is what a pipeline laying
narration into gaps wants.

**`language` is checked against the chosen voice**, so a mismatch is a named `400` rather
than a charged take in the wrong accent. Voices with no recorded languages — typically your
own clones — accept any value. Omit it and the model infers the language from the script.

### Pricing

**Per 100 characters of the TRIMMED script, rounded up**, with a floor of one centi-credit.
The same schedule the dashboard bills for the same render. `POST /estimates` has its own arm:
`{ "kind": "voiceover", "script": … }` — `script` is **required** there, because it is what
the price is made of, and it is checked against the same cap, so a script this endpoint
quotes is a script that endpoint accepts.

### Failure modes

| Code | Cause |
|---|---|
| `400` | Validation, a script over the cap, a language the voice does not speak, or voice-over being off on this deployment. Nothing charged. |
| `402` | Not enough credits; `details` carries `required` and `available`. |
| `404` | No such voice, **or one this organization may not use** — deliberately indistinguishable, because telling them apart would let a caller enumerate other organizations' clones. |
| `422` | Moderation refused the script. Nothing charged. |
| `429` | `details.reason: voiceover_concurrency_limit` — **10** in flight, its own queue. |
| `502` | The provider failed. Credits refunded automatically. |

Credits are charged before the provider call and refunded automatically if it fails.

### What it does not do

It does not clone a voice, and it does not take audio. It reads text in a voice that already
exists in your catalog. Replacing the voice in something already recorded is
`POST /voice-changes`, below.

---

## POST /voice-changes

Documented from the live spec `2.21.0` on 2026-08-12, **and exercised end to end the same
day** — every number in this section is from that run. Gated on a per-deployment flag; where
it is off the path and the `voice-change` estimate arm are both absent from
`GET /openapi.json` and the path answers `400`, not `404`.

Takes a video this API rendered, or a video **or audio file** you uploaded, and returns
**the finished audio** with the speech re-performed by a voice you choose. `200`, not `202`:
the provider returns bytes rather than a job id.

| Field | Required | Notes |
|---|---|---|
| `jobId` | one of the two | a video this API generated |
| `assetId` | one of the two | a file you uploaded. **Video or audio** (`audio/mpeg`, `audio/wav`) — the only endpoint here that takes audio-only uploads |
| `voiceId` | **yes** | no default, and **no substitution, ever**. From `GET /voices` |
| `productId` | no | organizational only |

Body is strict; exactly one source. Response `200`: `jobId`, `assetId`, `url`,
`expiresInSeconds`, `creditsCharged`, `billedMinutes`, `voiceId`.

**What it preserves: timing, pacing and delivery, frame-accurately.** The take drops back
onto the original picture and stays in sync, which is the whole reason this exists rather
than a text-to-speech call. Measured on a 15s ad: the largest per-word start drift between
the source's transcript and the finished output's, across 33 words, was **0.021s**.

**The level is matched for you.** The provider returns converted audio roughly 15 dB under
the source; the endpoint measures the source and gains the take to within **1.5 dB** of it
before storing. Measured on the same run: source `mean_volume −22.6 dB`, take **−23.2 dB**.
Anything that arrives further off than that is a defect in your own mux, not in the take —
the classic one being ffmpeg's default mono-to-stereo rematrix, which costs exactly 3 dB.

**`voiceId` never substitutes.** Some internal paths swap in a replacement when a voice goes
inactive; this one fails and refunds instead, because you chose a specific performance. A
made-up id came back `404 not_found` naming the id, with nothing charged (verified live).

**Converting the same source in the same voice twice is free.** The second call returns the
**same `jobId` and `assetId`** with `creditsCharged: 0` and a freshly minted `url`. Verified
live: two calls, one charge in the balance. A **different voice is a different conversion**
and a new charge — so auditioning by conversion is the expensive way to cast. The identity
covers the stored object's size, not just its name, so re-uploading different bytes under
the same `assetId` is not a hit either.

**Sources are capped at 5 minutes**, because the audio comes back inline rather than polled.
A longer one answers `400` naming the limit and charges nothing. Split it and convert the
parts. A 15-second source converted in **7.1 seconds**.

### Pricing

**Per minute of source audio: whole minutes, rounded UP, one-minute minimum**, with no
resolution term — the converter reads an audio track and never sees the picture.
`billedMinutes` on the response says what was counted. `POST /estimates` has its own arm:
`{ "kind": "voice-change", jobId | assetId }`, at most one source. **Name the source for
anything over a minute**; a sourceless quote is the one-minute minimum, which is why a 15s
ad and an empty body quoted the same number on the acceptance run.

### Failure modes

| Code | Cause |
|---|---|
| `400` | Validation, a source **past the 5-minute cap** (named), or voice changes being off on this deployment. Nothing charged. |
| `402` | Not enough credits; `details` carries `required` and `available`. |
| `404` | No such job or asset for this organization, **or no such voice** — the voice cases are deliberately indistinguishable from "not yours". A voice that went inactive *after* the request started lands here too, with the credits refunded. |
| `409` | The source job has not succeeded yet, it has **no audio to convert**, or **a conversion of this source in this voice is already in flight** — the message names that job id, so poll it or retry in a moment and the stored audio comes back without a second charge. Anything charged before a `409` is refunded. |
| `429` | `details.reason: voice_change_concurrency_limit` — **10** in flight, its own queue, counted apart from renders, captions, transcripts and narration. |
| `500` | **Do not blindly retry**: this endpoint charges, and a failure can land after the debit. Call `GET /generations` first. |
| `502` | The provider failed. Credits refunded automatically. |

### What it does not do

Four assumptions callers arrive with, none of them true here:

- **It does not translate.** The words that come back are the words that went in.
- **It does not read a script.** There is no text field; the input is audio.
- **It does not fix pronunciation** — and by extension it does not change an accent. The
  model reproduces the source's phonemes, mistakes included, so a mispronounced brand name
  comes back mispronounced in a nicer voice. The fix is to re-render the source with the
  word spelled phonetically and convert that.
- **It does not detect speech.** The gate is "does this have an audio track", not "is
  anyone talking": a music bed sent here converts into vocal noise, is **charged in full**,
  and answers `200`. That is a charged success, not an error, and there is nothing to refund.
  Check for speech locally before you call — the `change-voice` skill ships a free check that
  does it in about a second.

And it does not return **video**. Muxing the take back over the picture, and deciding which
spans to swap so a sound effect or a music bed survives untouched, is yours to do locally,
deliberately: those are creative decisions a server should not make on your behalf.

---

## GET /generations

| Param | Values |
|---|---|
| `limit` | 1 to 50, default 10 |
| `offset` | default 0 |
| `kind` | `video`, `image`, `audio`, `text` — `audio` is a music job and `text` is a transcript, both spelled for the row's own kind rather than for their estimate arms' `music` / `transcript` |
| `productId` | filter to one product |
| `updatedSince` | ISO 8601. The incremental-sync path: store the highest `updatedAt` you have seen and pass it back. |
| `sortBy` | `createdAt` (default), `updatedAt` |
| `sortOrder` | `desc` (default), `asc` |

Returns `items`, `total`, `limit`, `offset`, `hasMore`. `total` ignores pagination.

This is also the recovery path when a call times out: the work may have run and been charged, and the lost thing is the response carrying the `jobId`.

## GET /generations/{jobId}

`jobId`, `status`, `kind`, `model`, `prompt`, `createdAt`, and once succeeded, `outputUrl` plus `outputUrlExpiresInSeconds` (3600). On failure, `error` carries our own wording, never a provider's raw text, and the credits are already refunded.

**The echoed `prompt` can carry raw newlines, and a strict JSON parser will reject the whole response.** Observed live 2026-08-12 on a multi-line video prompt: the control characters arrive unescaped inside the string, so `json.loads()` raises and a poll loop that treats a parse error as "not ready yet" spins until it times out on a job that finished. Parse the poll response tolerantly — `json.loads(body, strict=False)` in Python, or the equivalent lenient mode elsewhere. It is a server-side escaping bug, not a signal about the job; nothing about the render or the charge is affected.

**On a `kind: "audio"` job that has succeeded, there is also `audio[]`** — the two tracks a music request delivered, each `{ url, expiresInSeconds, durationSeconds, title }`. `audio[0]` is the canonical one and is what `outputUrl` points at; `audio[1]` is a second take of the same prompt, and **`audio[]` is the only place it is published** — it is not a separate library asset and it will not turn up in a listing. Both URLs are presigned and minted **when you read the job**, so re-poll for fresh ones instead of storing them.

## GET /generations/{jobId}/watch

`302` to a URL signed at request time. `curl -L` friendly, and the right thing to hand a video player or an `<img>` tag, because the signature is minted on request rather than read from something that may have expired in your database.

While the job is unfinished this is a `409` naming the current status.

## GET /products, POST /products

`GET` lists the organization's products. `POST` creates one and returns it with its `id` — that id is what goes in `productId` on every generation call.

**`GET /products` returns the array under `items`, not `products`** (verified live 2026-08-04). This is the same paginated envelope `GET /generations` uses, and the pack previously did not say so anywhere — which left `.products` as the obvious wrong guess:

```json
{ "items": [ { "id": "...", "name": "...", "folders": [], "createdAt": "...", "updatedAt": "..." } ],
  "total": 12, "limit": 10, "offset": 0, "hasMore": true }
```

Every list endpoint on this API answers with the same five keys — `items`, `total`, `limit`, `offset`, `hasMore` — so `.items` is the one accessor to learn. `total` ignores pagination. Query params: `limit`, `offset`, `updatedSince`, `sortBy`, `sortOrder`.

Each item carries `id`, `name`, `description`, `targetAudience`, `mainFeatures`, `painPoint`, `perceived`, `folders`, `createdAt`, `updatedAt`. Every descriptive field except `name` can be `null`.

Request body for `POST`, `.strict()` — `name` is the only required field:

| Field | Type | Limit |
|---|---|---|
| `name` | string | **required**, 1 to 200 chars |
| `description` | string | ≤ 2,000 chars |
| `targetAudience` | string | ≤ 500 chars |
| `mainFeatures` | string[] | ≤ 20 items, each ≤ 200 chars |
| `painPoint` | string | ≤ 500 chars |
| `perceived` | string | perceived value — what a buyer feels it is worth. ≤ 500 chars |

```bash
curl -sS -X POST https://api.novoads.ai/v1/products \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aurora Sleep Tea",
    "description": "A caffeine-free herbal tea blended for people who fall asleep late.",
    "targetAudience": "Adults 25-45 who work late and struggle to wind down.",
    "mainFeatures": ["Caffeine free", "Valerian and chamomile", "Brews in 3 minutes"],
    "painPoint": "Lying awake for an hour after getting into bed.",
    "perceived": "A nightly ritual worth more than the price of a coffee."
  }'
```

**Every descriptive field is stored verbatim and none of them influence what is generated.** Not one reaches the prompt. Filling them in buys you a readable history — `GET /v1/generations?productId=…` becomes a useful filter — and nothing else. Do not treat a product record as a brief the model will read, and do not paste brand voice in here expecting it to change a render; that belongs in `MASTER_CONTEXT.md`, which the agent actually reads.

`PATCH /products/{productId}` takes the same fields, all optional. `GET /products/{productId}/folders` is read-only, and there is no folder-creation endpoint.

## GET /models

The catalog: per model `id`, `displayName`, `kind`, `endpoint`, `credits`, `representativeOutput`, `aspectRatios`, `durationsSeconds`, `maxPromptCharacters`, and — on video models — **`resolutions[]` and `defaultResolution`** (verified live 2026-08-04; the earlier note that this endpoint published no output size is superseded).

**`resolutions[]` is the authority on which tiers a model takes.** Live on 2026-08-04, plus `seedance-2.5` from deployed spec `2.13.0` on 2026-08-07: `seedance-2.0` returns `["480p","720p","1080p","4k"]`; **`seedance-2.5` returns `["480p","720p"]`**; `seedance-2.0-mini`, `omni-flash` and `sora-2` return `["720p"]`; `veo-3.1` returns `["1080p"]`. Read it instead of hardcoding a set — a value outside a model's list is a `400`, not a downscale. Note that only `seedance-2.0` and `seedance-2.5` expose `resolution` as a *request* field: for the fixed-tier models, `resolutions[]` reports what they render, not something you may send.

**`durationsSeconds` is the same kind of authority for length**, and since 2.13.0 the entries no longer agree with each other: `seedance-2.5` publishes 4 … 30, every other model stops at or below 15. Read the model's own array rather than assuming a family shares a grid.

**`credits` prices `representativeOutput`, and that unit is not the same across models** — one model's representative output is 5 seconds of video, another's is 10. Comparing the two `credits` numbers directly compares different things. For a real comparison, price both at `POST /v1/estimates` with the same `durationSeconds`.

## Status lifecycle

```
queued -> running -> finalizing -> succeeded
                                -> failed
                                -> blocked
                                -> canceled
```

`succeeded`, `failed`, `blocked`, `canceled` are terminal. Nothing else will change.

**Poll for terminal, not for `succeeded`.** A loop waiting only on `succeeded` never exits on a failed job.

`queued` means charged and submitted but not yet rendering. It is normal, not a stall.

Measured on production renders (all providers, succeeded only, p10 to p90):

| model | typical wait | median | observed in this repo |
|---|---|---|---|
| `seedance-2.0` | 3 to 8 minutes | ~5 minutes | **~171s, ~171s, ~154s** (2026-08-02/03, n=3) |
| `seedance-2.5` | not published | — | — |
| `seedance-2.0-mini` | 2 to 3 minutes | ~2.3 minutes | — |
| `omni-flash` | not published | — | — |
| `veo-3.1` | not published | — | — |
| `sora-2` | not published | — | **~123s** (2026-08-02, n=1) |

The right-hand column is `createdAt` → first observed `succeeded` at 15-second poll granularity, so it is an upper bound on a handful of renders — not a distribution, and not a contradiction of the fleet range next to it. **Quote the fleet range where there is one and say the number is a range.** Both renders anyone here has actually timed came back under three minutes, so "about five minutes" is a promise the API did not make: a user told five who waits nine has been misled, and the p90 says nine happens.

For `seedance-2.5`, `omni-flash`, `veo-3.1` and `sora-2` there is no published range at all. Say the wait is unknown rather than borrowing another model's — and for `seedance-2.5` specifically, do not borrow `seedance-2.0`'s on the strength of the shared family name: a thirty-second render is six times the output of the five-second clips those numbers were measured on.

About 4% of `seedance-2.0` renders run past 10 minutes. Failures are usually reported faster than successes, but their tail is much worse, so a wait that is far past p90 is more likely a slow success than a silent failure.

---

## Limits

| Limit | Value |
|---|---|
| Requests per key | 60 per minute |
| Requests per organization | 180 per minute, across every key it holds |
| Requests per client address, pre-authentication | 1,200 per minute |
| Concurrent **video** generations per organization | 5 (`429`, `error.code` `rate_limited`, `details.reason` `concurrency_limit`, `Retry-After` 15s) |
| Concurrent **image** generations per organization | **12** (`429`, `details.reason` `image_concurrency_limit`) — its own budget since spec `2.12.0`, not carved out of the 5 above |
| Concurrent **caption** jobs per organization | 10 (`429`, `details.reason` `caption_concurrency_limit`) — a separate budget from the 5 above |
| Concurrent **transcript** jobs per organization | 10 (`429`, `details.reason` `transcript_concurrency_limit`), where `POST /transcripts` is offered — again its own budget |
| Concurrent **voice-over** jobs per organization | 10 (`429`, `details.reason` `voiceover_concurrency_limit`), where `POST /voiceovers` is offered — again its own budget |
| Concurrent **voice-change** jobs per organization | 10 (`429`, `details.reason` `voice_change_concurrency_limit`), where `POST /voice-changes` is offered — again its own budget |
| Source duration, `POST /voice-changes` | 5 minutes (`400`, named, nothing charged) |
| JSON request body | 64 KB |
| Upload size | 100 MB |
| Upload URL lifetime | 900 seconds |
| Output URL lifetime | 3,600 seconds, minted at read time |
| Live API keys per organization | 10 |

Every response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`, and a `429` also carries `Retry-After`. Two caveats an agent that paces itself off those headers needs:

- The headers always describe **your per-key budget**. A `429` from the organization ceiling or from the pre-auth ceiling can arrive while they still show room.
- The pre-auth ceiling reports `Retry-After` and **no** `X-RateLimit-*` headers at all.

Concurrency detail worth knowing: the count covers the organization's **API surface only**, so dashboard renders do not consume an integration's slots, and a row stops counting after 30 minutes unfinished, so a stuck job cannot jam an organization permanently. Reads, estimates and uploads are not affected by it.

The video and image budgets are counted by two queries that cannot see each other's rows, and that separation runs **both ways**: a batch of images in flight never refuses a `POST /videos`, and five videos rendering never refuse a `POST /images`. Before `2.12.0` images spent video slots and both halves of that were false. So do not treat a `429` on one as a reason to stop calling the other — branch on `details.reason`, which is exactly what it is for.

Cloudflare's edge timeout of roughly 100 seconds is the real ceiling on any single request, which is why video generation is asynchronous and image generation is not (it fits).

---

## Errors

Envelope, on every failure:

```json
{ "error": { "code": "...", "message": "...", "requestId": "...", "details": { } } }
```

**Branch on `code`.** The wording of `message` can change. `requestId` matches the `x-request-id` response header; quoting it makes the whole server-side trace one lookup.

| `code` | Status | Notes |
|---|---|---|
| `invalid_input` | 400 | **Malformed request only.** `details.issues` names each bad field. Nothing charged. See below. |
| `unauthorized` | 401 | Missing, malformed or revoked key. Carries `WWW-Authenticate: Bearer`. |
| `insufficient_credits` | 402 | `details` has `required` and `available`, in credits. |
| `forbidden` | 403 | `details.reason` is `plan_required` or `subscription_inactive`, or the API is not enabled for that organization. |
| `not_found` | 404 | No such object **for this organization**. Deliberately indistinguishable from someone else's object. |
| `method_not_allowed` | 405 | Real path, wrong verb. Carries an `Allow` header. |
| `conflict` | 409 | Includes `/watch` on an unfinished job. |
| `content_policy` | 422 | Moderation, and the **only** refusal of a prompt for what it says. Nothing charged. |
| `rate_limited` | 429 | **Twelve causes**, nine of them broken out. See below. |
| `internal_error` | 500 | **Do not blindly retry.** See below. |
| `provider_failed` | 502 | Credits refunded automatically. |

### A 400 has one shape

It is a schema rejection, and it names the fields:

```json
{ "error": { "code": "invalid_input", "message": "(root): Unrecognized key: \"styleFamily\"",
  "details": { "issues": [ { "field": "(root)", "message": "Unrecognized key: \"styleFamily\"" } ] } } }
```

An out-of-grid `durationSeconds` and a prompt past the model's ceiling land the same way — the
response names the field and the limit.

**There is no second shape.** Until spec `2.0.0` a prompt-rule failure was also a 400, carrying `details.rule` and `details.violations[]`. Those keys no longer appear on any response — the rules that replaced them are **advisory only** and arrive as the `warnings` array on a `200` from `/estimates`, never as an error. Code that branches on `details.rule` is reading for something that will never arrive; code that wants the craft advice reads `warnings` off the estimate. (The earlier claim here that `warnings` was itself removed in spec `3.0.0` was wrong — deployed spec is `2.6.0` and it returns the field; verified live 2026-08-04.)

### The causes of a 429

Every one carries `details.reason` and a `Retry-After` header. Those two are the documented
contract: sleep on the header, branch on the reason. `error.details` is a free-form object, so a
response may carry more than the spec names — `details.inFlight` on a concurrency refusal is the
only extra it does name. Do not branch on an undocumented `details` key.

**The deployed spec names twelve reasons** (read off `2.21.0`, 2026-08-12). Nine are broken
out below; the three this pack has never hit are `competitor_ads_concurrency_limit`,
`analysis_concurrency_limit` and `analysis_hourly_limit`. Read the live spec's `429`
description if you meet one that is not here — this table is a working set, not the contract.

| `details.reason` | Cause | What to do |
|---|---|---|
| `concurrency_limit` | 5 **video** generations already in flight for the organization; `details.inFlight` says how many | Wait for one to reach a terminal state, then submit. A longer backoff does not help; a finished job does. Video generation only — images have their own queue below. |
| `image_concurrency_limit` | **12 image generations already in flight** for the organization (verified against the deployed spec `2.12.0`, 2026-08-06) | Same shape: wait, do not slow down. Counted **separately** from `concurrency_limit` in both directions — images never block a render, renders never block an image. |
| `caption_concurrency_limit` | **10 caption jobs already in flight** for the organization (verified in spec 2.6.0, 2026-08-04) | Same shape as above: wait, do not slow down. Counted **separately** from `concurrency_limit`, deliberately — a batch of captions can never block your next render, and vice versa. |
| `transcript_concurrency_limit` | **10 transcripts already in flight** for the organization, where `POST /transcripts` is offered (verified against the deployed spec `2.12.0`, 2026-08-06) | Wait. A transcript is synchronous, so this bounds how many you can hold open at once and is often the first ceiling a batch meets. |
| `voiceover_concurrency_limit` | **10 voice-overs already in flight** for the organization, where `POST /voiceovers` is offered (verified against the deployed spec `2.12.0`, 2026-08-06) | Wait — but on a two-second TTS call, not on your renders. Easy to misread as "stop generating video" when renders are legitimately in flight; they are unrelated queues. |
| `voice_change_concurrency_limit` | **10 voice changes already in flight** for the organization, where `POST /voice-changes` is offered (verified against the deployed spec `2.21.0`, 2026-08-12) | Wait. Synchronous like transcripts, so this bounds how many conversions you can hold open at once rather than how fast you may ask. Its own queue: a batch of conversions never blocks a render, a caption or a narration line. |
| `key_limit` | 60 requests per minute on this key | Honor `Retry-After`. The `X-RateLimit-*` trio tracks this ceiling and only this one. |
| `organization_limit` | 180 requests per minute across every key the organization holds | Honor `Retry-After`. `X-RateLimit-*` will still show room on your key — correct, not a broken limiter. Minting another key does not raise it. |
| `client_limit` | 1,200 requests per minute from one address, **pre-authentication** | Honor `Retry-After`. Carries no `X-RateLimit-*` trio. |

An agent that reads only "429 means slow down" backs off on the wrong axis when the real problem is jobs in flight — and, with five separate concurrency queues, it may be backing off the wrong queue entirely. Branch on `details.reason`.

**The in-flight count is per organization, not per key or per session**, so `concurrency_limit` is the ordinary outcome of running several workflows at once — two agents each holding three renders open is a sixth submission refused, with neither of them individually misbehaving (observed live 2026-08-12 across parallel callers on one org). **Nothing is charged on the refusal**: the row is never created, so there is no job to find and no credit to reclaim. A render clears in roughly two minutes at the short durations, so resubmit the same body after one — the fix is a finished job, and minting a second key does not buy a slot.

### The 500 rule

The generation endpoints charge credits, and a failure can land **after** the debit committed. A blind retry can pay twice, and there are no idempotency keys yet.

On a 500: call `GET /v1/generations` first. If the job is there, poll it. Only resubmit if it is genuinely absent.

---

## Known discrepancies

Dated. Struck through when fixed, never deleted, because a retraction is more useful than a gap.

- ~~**2026-08-01, the published 422 description is wrong.**~~ **Fixed in the spec; re-read 2026-08-02.** The 422 description was corrected once to name 400 as the prompt-rule status, and corrected again when the rules stopped blocking. It now reads: moderation is the ONLY way a prompt is refused for what it says, and a 400 means malformed, "never that we disliked the writing". The underlying behavior never changed: 422 is moderation only.
- ~~**2026-08-01, the per-operation `429` description names only one of its three causes.**~~ **Fixed in the spec, verified 2026-08-02.** Every operation's `429` now names all four ceilings — `key_limit`, `organization_limit`, `concurrency_limit`, `client_limit` — and says how each is paced, including that waiting is the only fix for concurrency. Live probe: a per-key 429 returns `details: {reason: "key_limit", limit: 60, retryAfterSeconds: 51}`.
- ~~**2026-08-01, `styleFamily` on an image estimate has no counterpart on the paid image call.**~~ **Resolved 2026-08-02 by deleting the field.** `styleFamily` is gone from both estimate arms and from every video variant, so the quote and the invoice now accept exactly the same prompt fields. Both arms are strict: sending it is `400 (root): Unrecognized key: "styleFamily"` (verified live on `kind: "video"` and `kind: "image"`). The rules it used to scope no longer refuse anything, so the divergence it caused — price clean, then 400 — is structurally impossible now.

## Prompt rules

**They exist, on `POST /estimates` only, and they are advisory.** The previous text here said there were none and that the `warnings` field had been deleted in spec `3.0.0` (2026-08-03). **That was wrong on both counts: the deployed spec is `2.6.0`, there is no `3.0.0`, and `/estimates` returns `warnings` today** (verified live 2026-08-04).

| | |
|---|---|
| Where | `POST /estimates` **only**. `POST /videos` and `POST /images` do not run them and return no `warnings` field. |
| Shape | `warnings: [{ "rule": string, "message": string }]`. Omitted entirely when nothing fires. |
| Force | **None.** Advisory. They never refuse a call, never change `credits`, and never reach the provider. |
| Scope | Video **and image** craft. Video rules seen live: `no_spoken_line`, `missing_actor_descriptor`, `label_without_hold`, `chained_motion`, `no_aspect_ratio`. Image rules seen live: `banned_polish`, `blank_label` (deployed spec 2.19.0, verified live 2026-08-12 — an earlier probe on 2026-08-04 returned no `warnings` key for images at all, which described that deployment). A caption estimate has no prompt and returns none. |

**They match substrings, so they false-positive.** Two reproduced live on 2026-08-04:

- `label_without_hold` fired on the word **"screen"** in a prompt for a SaaS dashboard demo. The rule protects *printed* text on physical packaging; there was no label in the shot, and applying the suggested labelHold clause would have asked the model to preserve a package that does not exist.
- `chained_motion` fired on the word **"Then"** — inside a **quoted spoken line**. The rule looks for a second staged action; this was dialogue. Splitting the shot would have split the actor's sentence.

Neither rule can distinguish a physical package from a UI, or narration from stage direction.

**How to use them:** read every one, judge it against what your prompt actually says and where the matched substring sits, and state your reasoning if you override it. Never paste a suggested fix into a prompt it does not fit, and never drop a warning silently — an unexplained override is indistinguishable from not having read it.

**The skill layer is still the real quality gate.** The prompt libraries carry a practitioner's craft notes and cover everything these four rules do not — which is nearly all of it. Read the formula file for the route before composing; a clean estimate is not a reviewed prompt. Moderation remains the only thing that can *refuse* a prompt for what it says, and it refuses content, not craft — see the `422` row in the error table.

What that leaves the estimate doing is the one thing it was always for: **the price.** It is still mandatory before every render, and it is still the only legitimate source of a number.
