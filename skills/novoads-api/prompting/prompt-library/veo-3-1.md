# Veo 3.1 — prompt craft

**Live on this API** since spec `2.1.0`. `POST /v1/videos` with `"model": "veo-3.1"`.

Read this before composing a Veo prompt. Every HTTP detail comes from [SKILL.md](../../SKILL.md) and [reference.md](../../reference.md), which win whenever this file and they disagree.

**Vendor guide:** [Google Cloud — Ultimate prompting guide for Veo 3.1](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)

## When to route here

**Pick `veo-3.1` when the user names it, or when the shot has to evolve over its own runtime** — a camera move that changes what the frame means between the first second and the last, rather than a person talking to a fixed lens. That is what Veo's prompting model is built around and it is what the vendor guide spends its length on.

**Two reasons to think before routing here:**

- **Nobody in this repo has measured a Veo render.** No render time, no leading-silence figure, no output resolution, no transcript. Everything below the request body is vendor craft and arithmetic. Say the wait is unknown rather than borrowing Seedance's numbers, and run the video QA in §7 of [SKILL.md](../../SKILL.md) with more attention, not less.
- **8 seconds is the ceiling**, and it is also the default. Veo has the shortest maximum of any video model here. A script that does not fit in 8s is a Seedance job or a split.

**No `referenceAssetIds`.** Veo takes `startImageAssetId` only, so an ad that has to composite the actor *and* the product is a Seedance job.

## Request body

`.strict()` — any key not in this table is a `400 Unrecognized key`, and nothing is charged.

| Field | Value |
|---|---|
| `model` | `"veo-3.1"` — required |
| `prompt` | required, 1 to **4,000** characters |
| `durationSeconds` | **4, 6, 8 only.** Defaults to **8**, which is also the maximum — the one model here that does. Out-of-grid values are rejected, never rounded |
| `aspectRatio` | `9:16` (**default**) or `16:9`. No other ratio |
| `language` | `en` `es` `pt` `fr` `de` `it` `zh` `ja` `ko` `ar` `hi`. Defaults to `en` |
| `startImageAssetId` | one `assetId`, animated as the first frame |
| `productId` | files the job under a product. Organizational only |
| `resolution` | from API 2.34.0, the tiers `GET /v1/models` lists for `veo-3.1` (`720p`, `1080p`); default is its `defaultResolution` (`1080p`). One flat price at every tier, so `720p` is never a saving; quote with `POST /v1/estimates` all the same. Before 2.34.0 the key is a `400` |

**Not on this model:** `referenceAssetIds`, `audioEnabled`, `styleFamily`. All are `400` (verified live 2026-08-02). `resolution` was on this list until API 2.34.0.

```bash
curl -sS -X POST https://api.novoads.ai/v1/videos \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo-3.1",
    "prompt": "...",
    "durationSeconds": 8,
    "aspectRatio": "9:16",
    "language": "en",
    "productId": "..."
  }'
```

**Price it at `POST /v1/estimates` before you commit, and price Seedance next to it.** The video schedules differ by roughly 5x across the set. Quoting one model's number for another is the failure this repo has no rate tables in order to prevent.

## Checklist

- [ ] Scene, action, and **how the shot evolves** over time — first frame → later beats. This is the layer Veo rewards.
- [ ] **Style** named explicitly if it matters (film stock, documentary, animation).
- [ ] Camera behavior described concretely, not as "cinematic" — a forbidden word as well as weak direction.
- [ ] Shot size stated as what is in frame, not just a shot-size word.
- [ ] Spoken line in double quotes, with invented brand names spelled phonetically (gate 1).
- [ ] **ALWAYS** end with `No on-screen text, no captions, no background music.` — Veo burns subtitles into the video if they are not explicitly excluded. This is a vendor-documented default, not a superstition.
- [ ] If using `startImageAssetId`, say how the motion should treat that first frame. Do not assume this API's Seedance reference rules carry over — Veo has no reference mode at all.
- [ ] Aspect ratio stated in the prose as well as the field.

## Template

```text
{{OPENING_BEAT}}. {{ACTION_OVER_TIME}}. Setting: {{SETTING}}. Camera: {{CAMERA}}.
Style: {{STYLE}}. Lighting: {{LIGHT}}. {{SUBJECT}} says: "{{SPOKEN_LINE}}".
No on-screen text, no captions, no background music. Vertical 9:16.
```

## Example

```text
Wide shot of a city rooftop at golden hour; a runner ties their shoes, then jogs toward camera
as the camera tracks sideways. Documentary handheld feel, warm natural light, subtle film grain.
No logos on clothing. No on-screen text, no captions, no background music. Vertical 9:16.
```

## Duration from word count

The **2.0**-words-per-second arithmetic and nothing more — **unmeasured on this model.** The rate is Seedance's, measured 2026-08-11 on one render, and it is carried here only because it is the sole figure anyone has actually timed; the 2.5 that used to drive this table was never measured on anything. Budget no silence, because nobody here knows whether Veo front-loads it the way Seedance does. Find out with the QA step and write the number down.

| Script length | Duration |
|---|---|
| 1–8 words | 4s |
| 9–12 words | 6s |
| 13–16 words | 8s |
| **17+ words** | **Too long** — 8s is the ceiling. Split, or move to Seedance |

## QA

Mandatory, same as every video — §7 of [SKILL.md](../../SKILL.md). On this model it is also the cheapest way to close the measurement gap: the ffprobe and silencedetect output from the first real Veo render is worth appending to `MASTER_CONTEXT.md` as a dated learning, because it is the number this file cannot give you.
