# Reference images

Drop reference images here for the agent to use when generating stills, video start frames, and other generations via this repo's API. The agent checks this folder automatically.

## How a file here reaches the API

Local paths are never sent. Every image goes through one upload first:

1. `POST /v1/uploads` with `{"contentType": "image/jpeg", "sizeBytes": <exact byte count>}` returns an `assetId` plus a presigned `uploadUrl` and the `headers` to send back byte for byte.
2. `PUT` the raw bytes to that URL. `Content-Type` and `Content-Length` are both signed into it — a mismatch is a 403 from storage that reads like an auth failure and is not one.
3. Pass the `assetId` in the request body.

**Upload each file once.** The `assetId` is durable and reusable without limit — the same id works on call one and call one hundred, across sessions and across models. Re-uploading the same bytes mints a *second* asset and silently loses the identity anchor, so it is a bug rather than a wasted step. Uploads are free; only generations are charged. The 900-second expiry on the response belongs to the upload URL, not to the asset.

Which field the `assetId` goes into depends on what you are generating:

| | Field | How many | Notes |
|---|---|---|---|
| **Video** — animate this exact image | `startImageAssetId` | 1 | The image becomes the clip's literal first frame. Not addressed in the prompt. |
| **Video** — composite these references | `referenceAssetIds` | up to **9** | Addressed positionally: `@Image1`, `@Image2`… The Seedance variants and, since API 2.30.0, `omni-flash` (up to its own limit); `veo-3.1` and `sora-2` reject it. |
| **Image** | `referenceAssetIds` | per model: **4** `gpt-image-2` / **14** `nano-banana-pro` / **8** `reve-2.1` | Addressed positionally. No `startImageAssetId` — a still has no first frame. |

The two video modes are **mutually exclusive**: sending `startImageAssetId` and `referenceAssetIds` in the same request is a 400, not a merge. References are **images only** — `POST /v1/uploads` also accepts video, but a video `assetId` used as a reference is an error.

There is no `referenceImages` field on this API, and no base64 field anywhere: upload first, pass ids. `skills/novoads-api/reference.md` is the authority for every HTTP detail.

## Folder structure

### `influencers/`
AI-generated character sheets — each influencer gets their own subfolder with 10 reference angles.

#### Folder naming convention

```
{name}-{descriptor1}-{descriptor2}-{descriptor3}-{descriptor4}-{descriptor5}
```

- **name:** A human first name (lowercase) — for easy reference in conversation
- **5 descriptors:** Visual architecture tags (lowercase, hyphenated) that identify the influencer at a glance

Descriptors should cover these categories in order:
1. **Hair color** — `redhead`, `blonde`, `brunette`, `black-hair`, `silver`
2. **Hair style** — `wavy`, `straight`, `curly`, `pixie`, `braided`
3. **Distinguishing feature** — `freckles`, `dimples`, `sharp-jaw`, `high-cheeks`, `beauty-mark`
4. **Eye color** — `green-eyes`, `blue-eyes`, `brown-eyes`, `hazel-eyes`
5. **Skin tone** — `fair`, `olive`, `tan`, `deep`, `medium`

**Examples:**
- `emma-redhead-wavy-freckles-green-eyes-fair/`
- `sofia-brunette-straight-dimples-brown-eyes-olive/`
- `kai-blonde-curly-sharp-jaw-blue-eyes-tan/`

#### File naming convention (inside each influencer folder)

```
01-hero-front.jpg      ← the approved anchor image (full body front)
02-3q-left.jpg
03-3q-right.jpg
04-profile-left.jpg
05-profile-right.jpg
06-face-closeup.jpg
07-back-shoulder.jpg
08-medium-portrait.jpg
09-full-body-3q.jpg
10-above-angle.jpg
```

Upload all 10 once and keep the `assetId`s — but **only 4 can be cited per image call** (9 per Seedance video call), so the skill is choosing which. The default allocation for a likeness generation is `01-hero-front.jpg` as the anchor plus one 3/4 angle, one close-up, and the single most important brand asset. Beyond that the text prompt carries the identity: restate the person's features verbatim rather than reaching for a fifth photo. For a series, keep a rolling window anchored on the hero — `[hero, N-1, N-2, N-3]` — and never feed a drifted output forward.

### `products/`
Product photos for showcase videos and product hero images.
- Different angles, packaging, in-use shots, flat lays
- The agent uploads these and passes the `assetId`s in `referenceAssetIds` in the product showcase workflow, addressing them in the prompt as `@Image1`, `@Image2`…
- Tip: clean backgrounds (white/neutral) produce the best results

### `aesthetics/`
Style references organized into subfolders by vibe. The agent uploads 3 images from the chosen style folder and passes their `assetId`s in `referenceAssetIds` to influence generation style — 3 of the 4 image slots, so leave room for the subject or product reference that has to share the call.

#### `aesthetics/ugc-selfie/`
iPhone selfie-style UGC — raw, unpolished, authentic-looking frame grabs. Drop 3-5 reference images showing the target aesthetic: front-camera selfies, slightly grainy, imperfect lighting, casual environments.

#### Adding new styles
Create a new subfolder (e.g., `aesthetics/cinematic/`, `aesthetics/studio/`) and populate with 3-5 reference images. The agent will ask which style to use when generating.

### `examples/ugc-stills/`
5 example UGC product selfie outputs showing the target quality — character + product + scene with skin realism and camera imperfections baked in. Use these as a visual reference for what the UGC pipeline produces.

## Supported formats

JPEG, PNG and WebP — `POST /v1/uploads` takes `image/jpeg`, `image/png` and `image/webp` for images (plus `video/mp4`, `video/quicktime` and `video/webm`, which are not usable as references). Anything else has to be converted before it can be uploaded at all. Maximum 100 MB per file, and `sizeBytes` must be the exact byte count — measure it, do not estimate it.

Shipped images are JPEG 85% for smaller repo size. Nothing here converts or upscales an input on your behalf; the 1024px floor the image scripts check is on generated *output*, and they warn rather than upscale.

## Privacy

This folder is gitignored — your images stay local and are never committed to the repo.
