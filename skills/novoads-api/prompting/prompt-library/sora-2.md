# Sora 2 — prompt craft (removed from the API)

> **Removed from the API in 2026-09.** When OpenAI ended the Sora 2 API, `sora-2` left
> `POST /v1/videos`, `POST /v1/estimates` and `GET /v1/models`: a call naming it is a `400`
> `invalid_input`, and nothing is charged. This page is kept as history, so an old link still
> lands on a page that says what happened; nothing below is a live route. A talking clip whose
> first word must land at once now goes to `omni-flash` like any talking clip, with its
> opening checked and trimmed if it opens quiet: see the model router and
> *Script length → duration* in [SKILL.md](../../SKILL.md).

Was on this API from spec `2.1.0` until 2026-09, as `POST /v1/videos` with `"model": "sora-2"`.

It was written to be read before composing a Sora prompt. Every HTTP detail comes from [SKILL.md](../../SKILL.md) and [reference.md](../../reference.md), which win whenever this file and they disagree.

**Vendor guide (read for craft):** [OpenAI — Sora 2 prompting guide](https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide)

## When it was routed here

**`sora-2` was the pick when the first spoken word had to land immediately.** That was its one measured advantage over Seedance and it was a large one: on an identical prompt, Sora started speaking at frame one and finished the line by 6.1s of an 8s clip, while `seedance-2.0` spent **3.71s in silence** before the first word — 37% of a 10s ad. See *Measured behavior* below. That job now goes to `seedance-2.0` with a reference or a start frame, as the notice above says.

**It was never the pick for an ad that needed several photos composited.** Sora took `startImageAssetId` but **no `referenceAssetIds`** — there was no reference-to-video mode. An ad that has to carry both the actor's face and the user's product is a Seedance job.

## Request body (as it was)

`.strict()` — any key not in this table was a `400 Unrecognized key`, and nothing was charged. Today any body naming `sora-2` is a `400` `invalid_input`.

| Field | Value |
|---|---|
| `model` | `"sora-2"` — required |
| `prompt` | required, 1 to **4,000** characters |
| `durationSeconds` | **4, 8, 12 only.** Defaults to **4**. Out-of-grid values are rejected, never rounded |
| `aspectRatio` | `9:16` (**default**) or `16:9`. No other ratio |
| `language` | `en` `es` `pt` `fr` `de` `it` `zh` `ja` `ko` `ar` `hi`. Defaults to `en` |
| `startImageAssetId` | one `assetId`, animated as the first frame |
| `productId` | files the job under a product. Organizational only |

**Not on this model:** `referenceAssetIds`, `audioEnabled`, `resolution`, `styleFamily`. All were `400`.

The duration grid was **coarse** — there was no 6s and no 10s. A line that landed between two rungs went up, never down; a 9-second script rendered at 12s or got cut.

The call it took, kept for the record (it is a `400` now):

```bash
curl -sS -X POST https://api.novoads.ai/v1/videos \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sora-2",
    "prompt": "...",
    "durationSeconds": 8,
    "aspectRatio": "9:16",
    "language": "en",
    "productId": "..."
  }'
```

It was priced at `POST /v1/estimates` with `"kind":"video"` and `"model":"sora-2"` first; that call is now a `400` too.

## Measured behavior (2026-08-02, n=1)

One `sora-2` render at 8s, `9:16`, `en`, no start frame, against a byte-identical `seedance-2.0` prompt. Treat these as observations, not as a spec.

| | Observed |
|---|---|
| Render time | **~123s** (createdAt → first observed `succeeded`, 15s poll granularity) |
| Leading silence | **none** — continuous speech from the first frame |
| Internal gaps > 0.3s | none |
| Speech window | 0s → 6.1s of an 8s clip |
| Brand name `Novoads` | transcribed **"Novo ads"** — recognisable, with no phonetic help |
| Burned-in captions | none |
| Output | 720x1280, mean volume −22.5 dB |
| Identity / wardrobe drift | none across the clip |

**Two things it changed in how a prompt was written:**

- **Name the framing harder than "medium".** `Medium selfie shot` produced a **tight close-up with shallow depth of field** on Sora, where the same three words gave a true medium — torso, chair, desk, shelf, deep focus — on Seedance. If the product has to be in frame next to the face, say so in the shot layer; do not trust a shot-size word to carry it.
- **No silence was reserved.** The dead-air reservation in [SKILL.md](../../SKILL.md) is a *Seedance* rule — there it is a draw that can land anywhere from 1s to 5s, so you reserve against the worst. Sora drew none, so applying the Seedance reservation to it bought dead air at the end instead of the start.

The phonetic-brand rule from gate 1 was **never tested on this model** — Sora got the name right unaided, so there was nothing to fix. That was not evidence the rule is unnecessary there, only that this brand did not need it.

## Checklist (as it was used, after reading the vendor guide)

- [ ] Clear subject and setting; camera behavior described, not just "cinematic" — a forbidden word here as well as weak direction.
- [ ] Motion: what moves, what stays stable across the clip.
- [ ] Shot size stated **concretely** — what is in frame, not just "medium" or "wide".
- [ ] Lighting and style named explicitly if they matter.
- [ ] Beats broken second by second when the clip has more than one (`0-4s: …`, `4-8s: …`).
- [ ] Spoken line in double quotes, with invented brand names spelled phonetically (gate 1).
- [ ] Clean-plate clause: `No on-screen text, no captions, no background music.`
- [ ] If using `startImageAssetId`, say how the motion should relate to that first frame.
- [ ] Aspect ratio stated in the prose as well as the field.

## Template (as it was)

```text
{{HOOK_OPEN}}. {{SUBJECT}} in {{SETTING}}. Camera: {{CAMERA_MOVE}}, {{SHOT_SIZE_CONCRETE}}.
Lighting: {{LIGHTING}}. {{MOTION_CUES}}. {{SUBJECT_PRONOUN}} says: "{{SPOKEN_LINE}}".
No on-screen text, no captions, no background music. Vertical 9:16.
```

## Example — the exact prompt measured above

83 words, 465 characters. Reproduce or diff against this rather than rewriting it from the formula.

```text
Medium selfie shot in a home office, soft daylight from a window at camera-left. A man in his
30s in a faded black t-shirt leans in toward the lens, tilts his head slightly, natural skin
texture with visible pores, slight camera shake from a handheld phone. He looks just off-lens,
comes back to camera, and says: "I kept saying AI ads look fake until I made one on NO-vo-ads
and nobody could tell." No on-screen text, no captions, no background music. Vertical 9:16.
```

> This prompt was priced live on `sora-2`, `veo-3.1` and `seedance-2.0` (2026-08-02) and rendered
> on all three. Note the clean-plate clause — `No on-screen text, no captions, no background
> music` — which every correct UGC prompt in this pack carries, and which nothing on the API
> will add for you.

## QA

`sora-2` renders were subject to the same mandatory video QA as everything else (§7 of [SKILL.md](../../SKILL.md)). Sora produced no leading silence and a recognisable brand name here, which was a reason to expect less from the check, not a reason to skip it.
