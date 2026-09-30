# Seedance 2.0 — model guide

The platform rules for `seedance-2.0` and `seedance-2.0-mini`. Read this before any of the four style formulas, and read the formula before writing the prompt.

**Route:** `POST /v1/videos` → `202` with a `jobId` → poll `GET /v1/generations/{jobId}` until a **terminal** status → download from `GET /v1/generations/{jobId}/watch`. The call sequence, the two gates, and the polling loop live in [SKILL.md](../../SKILL.md); every field-level detail lives in [reference.md](../../reference.md). This file is craft plus the model's own grid.

## Request fields

Only `model` and `prompt` are required. The body is **strict** — any key not in this table is a `400` and nothing is charged.

| Field | Value / range | Notes |
|---|---|---|
| `model` | `seedance-2.0`, `seedance-2.0-mini` | Mini is half the price on the same grid. Ask once per workflow; see *Mini-draft tier* below. |
| `prompt` | required | The video prompt. See *Length* below. |
| `durationSeconds` | any integer **4 to 15** | Continuous range, not an enum. **Defaults to 5**, which is never what an ad wants. Set it. Out-of-grid values are rejected, never rounded. |
| `aspectRatio` | `16:9` `9:16` `1:1` `4:3` `3:4` `21:9` | **Defaults to `16:9`.** Set `9:16` for Reels, TikTok, Stories. Free — it does not move the price. |
| `resolution` | `480p` `720p` `1080p` `4k` | **Defaults to `720p`. This one changes the price** — see below. On `seedance-2.0-mini` only from API 2.34.0, and only the tiers `GET /v1/models` lists for it. |
| `language` | `en` `es` `pt` `fr` `de` `it` `zh` `ja` `ko` `ar` `hi` | The language the ad is rendered in. Write the prompt in it too. |
| `startImageAssetId` | one `assetId` | Animates that image as the **first frame**. |
| `referenceAssetIds` | up to **9** `assetId`s | **Composites** them as visual references. Addressed in the prompt as `@Image1`…`@ImageN`. |
| `productId` | UUID | Optional. What makes `GET /v1/generations?productId=…` a useful history later. |

**`startImageAssetId` and `referenceAssetIds` are two modes, not two fields.** Sending both is a `400` that says so in as many words:

> `startImageAssetId and referenceAssetIds are separate modes and cannot be combined. Pass startImageAssetId to animate one image as the first frame, or referenceAssetIds to composite several references into a new scene.`

`referenceAssetIds` is **images only** (`image/jpeg`, `image/png`, `image/webp`); since API 2.35.0 mp4 and mp3 references go in `referenceVideoAssetIds` and `referenceAudioAssetIds`, with caps from the OpenAPI document (`GET /v1/openapi.json`: each field's `maxItems` and description, which also state the summed-seconds and total-file caps), and cannot be combined with `startImageAssetId`; an audio reference needs an image or video reference beside it. Ten references is `referenceAssetIds: Too big: expected array to have <=9 items`. `omni-flash` takes `referenceAssetIds` too since API 2.30.0 (images only as well, with one separate `referenceVideoAssetId`); read its guide before carrying a Seedance reference prompt across.

**`resolution` exists on this model and it multiplies the bill** (verified live 2026-08-04, spec 2.6.0 — the older note here saying the field did not exist described a previous deployment). It takes `480p`, `720p`, `1080p`, `4k` and defaults to `720p`. Relative to that base: `480p` costs **≈half**, `1080p` is **≈2.5x**, `4k` is **≈5x**. The `480p` arm was repriced on 2026-08-07 — it used to cost the same as `720p`, which is why the older note here called it no draft tier at all. It is one now: measured live 2026-08-12, exactly half the `720p` quote on `seedance-2.0` and on `seedance-2.5`, so a rehearsal render has an honest cheap tier to go to.

Those are ratios for warning the user, **not a rate card — never quote a credit number from them.** Price the exact cell with `POST /v1/estimates`, which takes `resolution` on its video arm, and get the usual approval before rendering.

Stay at `720p` unless someone asks for more: it is what Reels, TikTok and Stories re-encode to anyway. Reach for `1080p` or `4k` only for a client deliverable, a placement with a quality floor, or a render you plan to crop into.

**Before API 2.34.0, never send `resolution` on `seedance-2.0-mini`** (from 2.34.0 read its `resolutions` in `GET /v1/models`; it lists `480p` and `720p`). `POST /v1/estimates` will accept `720p` for mini and price it, which reads like permission and is not: mini's `POST /v1/videos` variant has no such property and answers `400 Unrecognized key: "resolution"` (observed 2026-08-04, not re-verified — confirming it costs a paid render). Mini renders 720p, fixed.

Default output measured at `9:16`: 720x1280 (2026-08-02, at the `720p` default); do not carry that number to other models.

### Fields this model does not have

Every one of these comes back `400 (root): Unrecognized keys: …` — verified live, 2026-08-02, in one request each:

`duration` (it is `durationSeconds`) · `referenceImages` (it is `referenceAssetIds`) · `referenceVideos` · `referenceAudios` (since API 2.35.0 they are `referenceVideoAssetIds` and `referenceAudioAssetIds`) · `startFrame` / `endFrame` (it is `startImageAssetId`) · `nbGenerations` · `projectId` (the API has products, not projects).

**`resolution` was on this list and no longer belongs on it** — it is a real field on `seedance-2.0` as of spec 2.6.0 (verified live 2026-08-04). It is still rejected on `sora-2` (and on `seedance-2.0-mini` and `veo-3.1` before API 2.34.0), and on `omni-flash` wherever `GET /v1/models` lists only `720p` for it.

**`audioEnabled` is the one exception, and it is a mute switch, not an audio track.** It arrived in spec `2.2.0` on `seedance-2.0` and `seedance-2.0-mini` only — the other three video models still `400` on it, and so does `POST /v1/estimates` for every model, because it does not move the price. It defaults to `true`. Send `false` for a clip that is meant to be silent (a pipeline laying its own VO in post, a cutaway built to run muted); otherwise leave it alone.

What it does **not** give you is control over the audio. Seedance still renders the dialogue and the lip-sync from the prompt itself, in the same call, at no extra cost — which is why the spoken line has its own approval gate in `SKILL.md` before anything is submitted. The flag decides whether that track exists, not what is in it.

### `@Image1` reference mapping

The four style formulas write `@Image1`, `@Image2`, `@Image3` inline in the prompt text. Those tokens resolve **positionally** against `referenceAssetIds`: `@Image1` is the first `assetId` in the array, `@Image2` the second, in the order you send them. Order is the contract — the array is what binds, the token is how the prompt points at it.

A token pointing past the end of the array is refused **before the charge**, so `@Image2` in a prompt that ships one reference fails free rather than billing a render the provider cannot resolve.

Upload once and reuse: the `assetId` is durable across calls, across models, and across sessions. Re-uploading the same bytes mints a **second** asset and throws away the identity anchor a multi-clip series exists to hold.

Which mode a formula wants:

| Formula | Mode | Why |
|---|---|---|
| UGC selfie review | `startImageAssetId` | The product photo is literally the opening frame. |
| Premium reveal, product hero | `referenceAssetIds` | The product emerges from a void it was never photographed in — the model has to composite it, not animate the flat photo. |
| Studio lookbook, feature walkthrough | `referenceAssetIds` | Two references earn their keep: `@Image1` the product, `@Image2` the actor. |

## Prompt craft

These rules are about how Seedance reads a prompt. None of them is enforced anywhere: the API renders and bills whatever you send. `POST /v1/estimates` flags a subset at no charge (see *What the estimate flags*), and the rest only you can check.

### Length

Keep prompts between **100 and 260 words**. Shorter prompts produce vague results. Longer ones
overwhelm the model and cause it to lose focus on key details.

A prompt that is too short leaves the model filling gaps you cared about; one that keeps piling on
adjectives past the point where every shot is specified starts losing the details rather than adding
them. Write every beat properly and stop.

### Structure

Seedance responds best to this order:

```
Subject + Action + Camera + Style + Constraints
```

- **Subject** — who or what is in the scene. Age, wardrobe, expression, posture.
- **Action** — what happens. Present tense, **one** primary movement per shot.
- **Camera** — framing (wide, medium, close-up) and movement (dolly-in, pan, handheld).
- **Style** — the light source, the surface, the grade. Name real things, not moods.
- **Constraints** — "the label stays legible", "steady motion", "no on-screen text".

Write it as flowing prose. A bulleted list or a run of `Label: value` pairs comes back **rendered as literal text on screen** — that is a real failure mode, not a style preference.

### Be explicit about motion

The model cannot infer intensity. Instead of `she picks up the bottle`, write `she slowly picks up the bottle with her right hand, turning it toward the camera`. Degree adverbs — **slowly, gently, quickly, casually, deliberately** — visibly change the render.

Two or three comma-joined cues on **one** action are good. A *second action* strung onto the first with `then` / `and then` / `followed by` renders as a smear, or not at all. Split it into two shots.

### Timestamps for pacing

For multi-beat sequences, timestamps control the rhythm:

```
[00:00] A guy in his 20s sits in his car holding an electrolyte packet. Medium shot, dashboard light.
[00:05] He pours the packet into his water bottle, shakes it. Close-up on hands.
[00:09] He takes a sip, pauses, nods with raised eyebrows. Back to medium shot.
[00:13] He holds the packet up to the camera, half-smile, and says: "Yeah, these are legit."
```

Useful for multi-shot choreography, for stopping the model rushing, and for style or camera changes inside one clip. Keep each block on one main action.

### Consistency anchors

When references are in play, say out loud that they must not drift:

- `The product from @Image1 remains visually unchanged in every shot.`
- `Keep the outfit unchanged across all cuts.`
- `The product label remains perfectly sharp and identical to the reference image with its text unchanged and fully legible.`

Repeat the actor tag **verbatim** rather than back-referencing it. `the same woman` resolves to nobody — no identity carries across a cut — and an elaborated tag re-casts as readily as a missing one.

### When the label garbles in motion

The anchor above is necessary and not sufficient, and the gap between them is a stage difference: **stills render label lines that clips destroy.** Measured 2026-08-12 on one product across both stages — the still rendered all five printed lines on the can correctly, and the clip built from that same still came back with `STILL ARTESIAN WATER` as `CTILLNETERAN WATER` in every frame. A legible invented word is worse than a blurred one: it reads as the brand's own copy.

**The lever is type size in frame, not prompt wording.** That is the opposite of where retries usually go. The fix that worked: pin the product close to the lens so it renders about **1.5× larger** — the smallest line went from roughly 14px to roughly 28px — and spell every printed line **verbatim** in the prompt. All five lines came back correct and sharp. Rewording the label-hold clause alone does not do it, because the model cannot resolve type it has not been given the pixels for.

Two counterweights, both worth the minute they cost:

- **Cut in past the bad frames first — it is free.** On the next beat the same defect ran only to frame 12 at 24fps, so trimming 0.5s off the head fixed the deliverable for zero credits. Sweep the frames before paying for a re-render; the wrong word is often legible only at the head.
- **A framing pin can blow a banding artefact.** A parallel claymation render in the same run picked up a white band across the bottom rows after a shot-distance pin was added. This render did not (worst bottom-260-row mean 47/255 against its own mid-frame 40) — but that was checked, not assumed. After any framing change, sweep the **full** frame, not just the label.

### Style anchors

Include at least one: `documentary` (natural, observational), `photorealistic` (grounded, no stylization), `handheld` (reinforces the phone-filmed look), `commercial` (polished — sparingly, and never on UGC).

**Avoid:** `cinematic`, `anime`, `studio` — these pull away from UGC authenticity. For premium/product-hero styles, use `dramatic` or `premium` instead of `cinematic`.

### Forbidden words

Never use in Seedance 2.0 prompts: `cinematic`, `professional`, `stunning`, `8k`, `studio`, `perfect`.

These are craft advice, not a gate. **Nothing on the API rejects them, and nothing reports them** — the estimate prices the render and says nothing about how the prompt is written. Delete the word anyway and describe the real thing in its place: the light source, the surface, the flaw. "Cinematic kitchen" is a wish; "sunlit kitchen, soft window light from camera-left, natural skin texture with visible pores" is a shot.

One route overrides this list: `studio` is correct on the [studio lookbook](seedance-2-studio-lookbook.md), whose whole premise is a lit studio with the rig in frame. The list is written for UGC, which is where most of this library lives — see note 3 in that file.

### Iteration

Change **one** element at a time:

1. Action right, framing wrong → adjust the camera description.
2. Pacing rushed → add timestamps or cut dialogue.
3. Product drifts between shots → add a consistency anchor.
4. Motion stiff → add degree adverbs and a second comma-joined cue.

## What the estimate is for

`POST /v1/estimates` is the price, and that is the whole of it. It is mandatory before every render because it is the **only** source of a number — never quote a cost from memory, from this file, or from a previous session. It spends nothing, so there is no reason to skip it.

It has no opinion about your prompt. Nothing in the API reads a prompt for craft, on this endpoint or any other: a prompt that breaks every rule in this file is priced, charged and rendered exactly as written. Everything above is the quality gate. There is no second one.

## Duration and dialogue

Any integer 4 to 15 seconds. Pick it from the spoken word count.

**A rendered line runs about 2.0 words per second, and the render opens with about 0.5s of silence before the first word.** So the word budget is `2.0 × (durationSeconds − 0.5)` — 29 words for a 15s clip. (Measured 2026-08-11 on one `seedance-2.0` render: a 29-word script, speech occupying 0.48s to 14.72s of 15.07s, Whisper word timings. One render, so treat it as the working figure and re-measure when you have another.)

That 2.0 already absorbs ordinary pausing — the measured take spent a 3s performed sip beat inside that span and still fit. It is deliberately **not** the articulation rate: words divided by voiced time alone came to ~2.5, and planning at 2.5 is what overruns, because it quietly assumes the actor never stops. Script to 2.0 and the silence takes care of itself.

| Script word count | Duration |
|---|---|
| 1–8 words | 4–5s |
| 9–15 words | 6–8s |
| 16–23 words | 9–12s |
| 24–29 words | 13–15s |
| **30+ words** | **Too long** — offer to split into multiple clips |

For no-dialogue styles (product hero, premium reveal), default to **15s**.

Embed the line in the prompt with natural attribution: `she says: "…"` or `he speaks: "…"`. It is rendered as audio with lip-sync in the same call, which is why it cannot be changed afterwards without paying for the render again — and why `SKILL.md` gate 1 exists.

## Mini-draft tier

`seedance-2.0-mini` is the same grid, the same fields, and the same formulas at **half the price**, and it returns in 2–3 minutes instead of 3–8. Use it as a draft tier:

1. Ask once per workflow which tier to use (`SKILL.md` makes this an explicit question; no preference means `seedance-2.0`).
2. Upload the reference **once**. The `assetId` is durable, so the final render reuses it with no second upload.
3. Draft on `seedance-2.0-mini` until the prompt is right — wrong framing, a garbled label, or a rushed line costs half as much to discover.
4. Re-price at `POST /v1/estimates` with `model` set to the final tier and re-confirm before the finishing render. **Show both numbers side by side** when the user is choosing; never quote either from memory.

The prompt does not change between tiers. If it renders well on mini, the only thing the full model changes is fidelity.

## Style template directory

Pick the formula that matches the goal, then read its file before composing:

| User goal | Formula | Key trait |
|---|---|---|
| UGC selfie-style product review / testimonial | [seedance-2-ugc.md](seedance-2-ugc.md) | 9-layer formula: person + setting + realism markers + one spoken line |
| Dark-background premium product reveal (no person) | [seedance-2-premium-reveal.md](seedance-2-premium-reveal.md) | Void stage + text narrative + dramatic lighting |
| Elemental product hero — splash, mist, effects (no person) | [seedance-2-product-hero.md](seedance-2-product-hero.md) | Product-only with environmental interaction |
| Studio lookbook with voiceover (polished, multi-look) | [seedance-2-studio-lookbook.md](seedance-2-studio-lookbook.md) | Voiceover narration over styled product shots |
| Fast-paced feature walkthrough / demo | [seedance-2-feature-walkthrough.md](seedance-2-feature-walkthrough.md) | Feature-per-beat physical demos with dialogue |
| **Reverse-engineer a reference video** into a new formula for this library | [../analyze-video/SKILL.md](../../../analyze-video/SKILL.md) | Frames + transcript locally → a template file that lands in this folder and gets a row in this table |
| **Clone one specific ad** for a different product | [../clone-video-ad/SKILL.md](../../../clone-video-ad/SKILL.md) | The same analysis, but the output is a rendered clip rather than a file |

If none fits, compose a custom prompt directly from the platform rules above, following Subject + Action + Camera + Style + Constraints.

Neighbours worth knowing about: [ugc-selfie-style.md](ugc-selfie-style.md) in this folder is a **cross-model** UGC guide whose formulas target Veo 3.1, Sora 2 and Kling 3.0. Two of those are now live — see [veo-3-1.md](veo-3-1.md) and [sora-2.md](sora-2.md) — but Kling is not, and neither Veo nor Sora takes `referenceAssetIds`, so for Seedance UGC use [seedance-2-ugc.md](seedance-2-ugc.md) rather than porting a cross-model formula across. The other video model here is `omni-flash`: narrower grids, references since API 2.30.0, and a 20,000-character prompt ceiling, guide at `shared/skills/gemini-omni-flash/prompting/guide.md`.

## Adaptation checklist (all styles)

- [ ] **Word count** — prompt is between 100–260 words
- [ ] **`durationSeconds` set explicitly** — from the dialogue word count, or 15 for no-dialogue. The default is 5.
- [ ] **`aspectRatio` set explicitly** — `9:16` for social. The default is `16:9`.
- [ ] **Motion specificity** — degree and direction, two or three cues on one action, no `then`
- [ ] **Consistency anchors** — product and wardrobe stated as unchanged across cuts
- [ ] **Label hold** — present whenever a label, package or screen is visible
- [ ] **No forbidden words** — no `cinematic`, `professional`, `stunning`, `8k`, `studio`, `perfect`
- [ ] **`@Image1` tokens match the array** — every token points at a reference you actually send
- [ ] **One mode only** — `startImageAssetId` **or** `referenceAssetIds`, never both
- [ ] **Style anchor** — at least one (documentary, photorealistic, handheld)
- [ ] **Timestamps** — for multi-beat sequences
- [ ] **Priced live** — `POST /v1/estimates` this session, the number shown to the user, user said yes
