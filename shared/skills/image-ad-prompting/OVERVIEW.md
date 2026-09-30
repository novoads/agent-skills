# Image-ad ecosystem — overview for AI coding agents

**One-line summary:** three skills + one shared prompt library let you generate standalone Meta image-ad creatives on any of the Novoads image models — ChatGPT Image 2, Nano Banana Pro, Reve 2.1 — and reverse-engineer existing ads into reusable templates. Output is image files. Meta-side uploading is handled by a *separate* `meta-ad-builder` skill, not by these.

**Read this whole file** at the start of any session where the user mentions: making an ad, image creative, ad library, gpt-image-2, ChatGPT Image 2, Nano Banana, Nano Banana Pro, Reve, cloning an ad, reverse-engineering an ad, or anything in the `T1–T42` template namespace.

---

## What's in the family

```
┌─────────────────────────────────────────────────────────────────┐
│ SHARED BRAIN (no SKILL.md — referenced by all 3 skills below)   │
│ shared/skills/image-ad-prompting/                               │
│   ├ prompting/prompt-library.md   40 validated templates        │
│   ├ prompting/template-format.md  entry-format skeleton         │
│   ├ prompting/safety-suffixes.md  3 always-on prompt guards     │
│   ├ scripts/check_library.py      the evals, runnable, free     │
│   ├ evals.md                      what they check and why       │
│   └ OVERVIEW.md                   this file                     │
├─────────────────────────────────────────────────────────────────┤
│ GENERATOR SKILLS (produce image files)                          │
│ skills/chatgpt-image-ad/         → gpt-image-2                  │
│ skills/nano-banana-image-ad/     → nano-banana-pro              │
├─────────────────────────────────────────────────────────────────┤
│ TEMPLATE-CREATION SKILL (reverse-engineer an ad → library)      │
│ skills/clone-image-ad/   asks which model to validate against,  │
│                          routes to the matching generator, and  │
│                          can cross-check on a third (reve-2.1). │
└─────────────────────────────────────────────────────────────────┘
```

`reve-2.1` has no generator skill of its own. It is reachable from `clone-image-ad`'s
Phase-1 chooser and by naming it directly on a call — it exists as a second opinion when a
template renders wrong on both of the other two, not as a default route.

---

## Presenting choices to the user

**The tables and decision trees in this file are the agent's routing doctrine, not a menu
for the user.** The model comparison below, the decision tree after it, and every entry's
`Model notes:` block exist so the agent can decide. A user who is shown them is being asked
to do the job they came here to hand over. Observed 2026-08-07: a first-time user typed "I
want to create image ads" and got a two-engine capability matrix plus a four-item brief, and
the run ended there.

Every turn has the same shape: **one decision, already made, with an escape hatch.**
Recommend, say why in one line, offer exactly one alternative. The evals for this section are
E1 to E3 in [evals.md](evals.md).

### A. No product named yet

Ask one question. Do not ask for aspect ratio, variant count or reference paths yet, and do
not name a model.

```
What are we advertising?
1) Your product (recommended): paste a link, or drop a photo right here.
2) No product yet? Say "pick something trendy" and I will mock up a demo ad (a test artifact, not something to publish).
```

### B. Product known: the plan

Do not offer a template menu, and do not ask pilot-or-everything. The full library is the
default:

```
1) Run the full library (recommended): every template that fits your product, one total price shown before anything renders. I check the first few myself and keep going when they read right.
2) Want it tighter? I pick the strongest 8 to 12 for your product, spanning every ad family, and name each pick in the plan.
3) Have your own idea? Describe it and I will build 3 custom takes.
```

**The full library spans every generator skill.** Templates routed to different engines
are one plan with one total, never a deferred second pass. Observed 2026-08-08: a run
scoped "the full set" to the one engine its own skill drives, quoted 26 of 40, and parked
the photoreal remainder behind "if you want them", which is a menu wearing a delay.

Option 2 is curation, not a menu. Pick 8 to 12 with at least one from each ad family that
fits the product (conversation/UI, comparison/data, editorial/social proof, photoreal):
the point of a tighter first run is learning which family works for this brand, and a
single-family pick cannot answer that. Name each pick in the plan with a half line on why
it fits, then take ONE go for the whole set. Per-pick approval questions rebuild the menu
this section exists to remove.

The self-check inside option 1 is an **internal checkpoint, not a user decision.** Generate
the first three to five, read them against the brief for product identity, brand voice and
text legibility, then continue the remaining templates in the same run. Stop and show
evidence only when the miss is *systematic*: the product rendered from the wrong angle, a
wordmark drifting across every output, dense text garbled on every template that carries it.
One bad frame in an otherwise clean set is a retry, not a checkpoint.

### C. Custom path: the engine, pre-picked

On the template path the engine is never mentioned. The entry's `Model notes:` block decides
it, silently. Option 2 above is the only path where no template decides, so it is the only
place the engine reaches the user, and it arrives already chosen:

```
1) GPT Image 2 (recommended): your concept is text-forward and this engine nails typography.
2) Nano Banana Pro: pick this instead for photoreal (product in hand, lifestyle, multi-reference scenes).
```

The one-line reason is **derived from the actual concept**, not pasted. Swap which one is
recommended when the concept is photoreal, keeping the same shape. When the concept carries
no format signal either way, recommend GPT Image 2.

### D. A file arriving in chat

When a product image lands in the conversation, file it yourself: read the image's source
path from the message and copy it to `references/products/<product-slug>.<ext>`, then say
where it landed. Only when no readable path exists, ask the user to drag the file into
`references/products/` in Finder and say the filename. **Never ask a user to type an
absolute path.**

The same doctrine covers fetching. When the user points at their brand's site and the
product image is on it, a read-only download of a public asset is free and reversible:
perform it, file it under `references/products/`, show the image in the chat, and say in
one line what was fetched and why. Do not propose it first, and do not describe an image
with filenames and byte sizes when you can show it. Questions are reserved for the two
acts that cannot be taken back: spending credits and publishing. Observed 2026-08-08: a
run stalled on "okay to grab it?" for a small read of the brand's own public CDN, one
turn before the real question (the price), and the extra gate read as noise.

### E. What the workspace remembers

After the first upload, record it in `MASTER_CONTEXT.md` under **My workspace**: the local
reference path, the `assetId` that `POST /v1/uploads` returned, and the `productId`. On the
first creative request for a brand, offer to create the product record with
`POST /v1/products`, which writes a record rather than a render (contract in the
`novoads-api` skill's `reference.md`). Later sessions read the cached `assetId` and
`productId` back instead of re-uploading the same bytes or asking the same question twice.

### F. Money

One total, from one live `POST /v1/estimates`, before anything generates. That response
already carries `balance` and `sufficient`, so the quote and the "can you afford it" answer
are the same call, and there is no second question to ask. When the full set does not fit the
balance, do not fail and do not hand the arithmetic back: recommend the subset that does fit,
say which formats it covers, and keep it one decision. **A credit figure may never come from
a markdown file**, including this one, which carries none.

---

## One endpoint, three models

Every image in this ecosystem comes from the same call: **`POST /v1/images`**, which usually answers with the finished images already in the response. One still going after about 105 seconds answers `status: "running"` with no images (API 2.39.0): the scripts poll it; a hand-rolled call polls
`GET /v1/generations/{jobId}` to a terminal status, reads `images[]` there and never resubmits, because a resubmit is a second charge. `Authorization: Bearer $NOVOADS_API_KEY`. The full contract lives in
the `novoads-api` skill's `reference.md`; this table is only what differs *between the models*.

| | `gpt-image-2` | `nano-banana-pro` | `reve-2.1` |
|---|---|---|---|
| **Default?** | yes — omit `model` and this renders | no | no |
| **Prompt cap** | model cap | model cap | model cap |
| **Reference images** | up to 4 `referenceAssetIds` | up to 14 | up to 8 |
| **Aspect ratios** | `1:1` `4:5` `2:3` `9:16` `16:9` `21:9` | those plus `3:2` `3:4` `4:3` `5:4` | same 10 as Nano Banana Pro |
| **Images per call** | `numImages` 1–4 | 1–4 | 1–4 |

Notes that bite:

- **`aspectRatio` defaults to `1:1`** on every model. For a Stories/Reels creative you must
  say `9:16` — the default is not the ad you wanted.
- **The three ratios the template library actually uses (`1:1`, `2:3`, `9:16`) are supported
  on all three models**, so no template needs a fallback-and-crop. Only bespoke prompts can
  hit the gap: `3:2`, `3:4`, `4:3` and `5:4` exist on Nano Banana Pro and Reve but **not** on
  gpt-image-2.
- **`numImages` is one call, not N calls.** Ask for 4 variants by sending `numImages: 4` and
  the response comes back with four images in `images[]`. Do not fan out four parallel
  requests — that burns four of your five concurrency slots for no benefit.
- **Every image is charged**, so `numImages` multiplies the price. It is the single biggest
  lever on what a run costs.
- **Reference images are uploaded once and reused.** `POST /v1/uploads` returns a durable
  `assetId`; pass those in `referenceAssetIds`. The id keeps working across later calls — you
  do not re-upload per variant.

**Editing exists on `gpt-image-2` alone, from spec 2.10.0.** `sourceAssetId` on
`POST /v1/images` edits an existing image from a prompt — "change the background of this
one", "remove the text". `nano-banana-pro` and `reve-2.1` do not publish the field, so an
edit request routes to `chatgpt-image-ad` regardless of which model the aesthetic would
otherwise favour.

Still no mask, no region select, no img2img strength dial: the change is described in words.
And the edit's output tracks the source's shape, so `aspectRatio` cannot be sent with it —
the API answers `400`, deliberately, rather than reframing what you asked to preserve. If
`GET /v1/openapi.json` does not show the field, this deployment has the arm off.

**The dashboard's three one-photo tools are on the API too (API 2.40.0).** `POST /v1/images`
with `preset: "image-to-ad"` (an ad built around the photo), `"product-to-ad"` (the photo in
one of the dashboard's ad templates) or `"upscale"` (the photo at 4K), the photo in
`imageAssetId`, and no `model` or `prompt`: the server writes the prompt. Reach for one when
the user names that tool or wants a still upscaled; the 40-template library and the skills here
stay the path for a prompt you control. Fields and refusals: the `novoads-api` skill's
`reference.md`, section *`preset`*. Price it with `POST /v1/estimates` and the same `preset`;
it can answer `running` like any image.

---

## Decision tree — which skill to use

The user's first sentence usually tells you which way to branch.

**Step 1: Are they generating from scratch, or cloning an existing ad image?**

- **Generating** → one of the two generator skills.
- **Cloning** (they shared an ad image and want it as a reusable prompt) → the single
  `clone-image-ad` skill (it asks which model to validate against at Phase 1).

**Step 2: Pick the model. This step is internal.**

On the template path it is already decided: the entry's `Model notes:` block names one, and
the question never reaches the user. Decide from this table when no template applies, then
present the result as a pre-made recommendation with one line of reason, in the shape rule C
gives above. The table itself is never shown.

| The user wants... | Pick |
|---|---|
| Apple Notes lists, fake search results, chat threads, ChatGPT-style conversations, iOS dialogs, Slack snapshots, comparison tables, Hinge cards, iMessage, calendar UI, weather forecast UI, magazine cover, anything **typography-heavy or UI-mimicry** | **`chatgpt-image-ad`** |
| Handheld whiteboard signs, napkin handwritten testimonials, sticky-note + product flatlays, letter-board signs, lifestyle scenes, OOH/transit photography, scratch-off tickets, **photoreal / material-rich / multi-reference** ads | **`nano-banana-image-ad`** |
| A second opinion after both of the above rendered the same template wrong, or a deliberately different look on a concept that already works | **`reve-2.1`**, via `clone-image-ad`'s chooser or by naming the model on the call |
| Ambiguous? | Look up the matching template in `prompting/prompt-library.md` and read its `Model notes:` block — every entry recommends one. |
| No template applies **and** the concept carries no format signal either way | **`chatgpt-image-ad`** is the tiebreak. `gpt-image-2` is also the API default, so an unqualified call already lands there. |

**Step 3: For cloning, the `clone-image-ad` skill handles all three models.** At Phase 1 it
asks the user (or auto-detects from the reference's typography-vs-photo balance) which model
to validate against. It then routes through the matching generator's
`scripts/generate_image.py`. Phase 8 optionally cross-validates on a second model so the
resulting library entry has `Model notes:` for more than one.

---

## The shared prompt library

`prompting/prompt-library.md` ships with **40 validated full prompts** (tags T1 through T42,
with intentional gaps at T16/T22 from the source Uni1 lineage). Every entry has:

- **When to use** — positioning fit
- **Aspect ratio** — recommended canvas
- **Reference image** — what to upload and pass in `referenceAssetIds`
- **Variables** — the placeholder schema
- **Template prompt** — the full validated prompt in a fenced code block (drop-in usable; swap brand-specifics per the Variables block)
- **Model notes** — per-model behavior on this template (which model is preferred, where each struggles)

The library is **the first place to look** when the user describes an ad concept. Match their
brief to a template, fill the variables, and ship — that's the fast path. The bespoke-prompt
path (writing from scratch) is the fallback when nothing matches.

---

## Always-on safety suffixes

Every generator script auto-appends three guards to the prompt:

1. **`NO_CHROME_SUFFIX`** — strips iOS chrome, Sponsored badges, engagement rows, link-card footers, story chrome, tab bars. The output is the *standalone* image creative, not a screenshot of how it displays in-feed. Override with `--allow-chrome` only when the ad concept genuinely needs simulated platform chrome (rare).
2. **`SAFE_ZONE_SUFFIX`** — keeps text + focal subjects inside the central 84% of the canvas. Eliminates clipped headlines.
3. **`GLYPH_SAFETY_SUFFIX`** — forbids emoji and unicode glyphs inside body-text blocks (chat bubbles, comment threads, ChatGPT responses); enforces the exact count of conversation elements.

Full text in [safety-suffixes.md](prompting/safety-suffixes.md). **Do not silently disable these** — they fix
recurring rendering failures across every modern image model. If you need to disable one for a
specific run, use `--allow-chrome` or `--no-safe-zone` flags and document why.

The suffixes count against the prompt cap of whichever model you send to, and together they
run to exactly **1,575**. **That cap is per model**, not one number: 32,000 on `gpt-image-2`,
50,000 on `nano-banana-pro`, 4,000 on `reve-2.1` (deployed spec 2.16.0, verified 2026-08-08).
The script measures the final prompt against the model it is locked to, or the one you named,
and refuses pre-network with the exact overage, so an overflow costs a round trip rather than
credits.

**Where the budget still bites: `reve-2.1`, and nowhere else.** Its 4,000 leaves 2,425 for a
template body, or 2,025 once the mandatory 400-character pin block is in, and **23 of the 40
templates** have that much room while three (T8, T11, T14) exceed even 2,425. The other two
models leave more than 30,000, which every template in this library clears with room to spare,
so on the production path the length arithmetic is no longer a constraint on what you write.
Pass the pin block as `--pin-block "<product description>"` rather than hand-writing it: the
standard guard is the wording that was measured to stop invented label copy. Per-template
headroom, per model:

```bash
python3 shared/skills/image-ad-prompting/scripts/check_library.py --verbose
```

## Evals

The library ships evals, and they need no key and no credits:

```bash
python3 shared/skills/image-ad-prompting/scripts/check_library.py            # run them
python3 shared/skills/image-ad-prompting/scripts/check_library.py --selftest # prove they can fail
```

They cover the prompt budget, conflicting element counts, documented model limits, the
transcribe-verify rule, and the entry format. Run them before landing a library change.
[evals.md](evals.md) says what each one caught.

---

## Standard workflow — generate an ad from a brief

This is the workflow inside any chat session where the user wants to make an ad:

1. **Match to a library template.** Read `prompting/prompt-library.md`. If their brief maps
   onto an existing template, use it. If not, plan a fresh prompt.

2. **Pick the model.** Read the template's `Model notes:`. If more than one works, default to
   `chatgpt-image-ad` for typography-heavy templates and `nano-banana-image-ad` for
   photoreal/lifestyle templates.

3. **Fill placeholders.** Swap `{brand.name}`, `{brand.color_primary}`, `{ad.headline}`, etc.
   with the user's brand. Show the rewritten prompt and ask for approval.

4. **Price it with a live estimate, and show the user.** `POST /v1/estimates` with
   `{"kind":"image","model":"<model>","prompt":"<final prompt>","numImages":<N>}`. It charges nothing,
   it returns `credits`, `balance` and `sufficient`, and **it is the only place a price may
   come from** — never quote a credit cost from memory, from a log file, or from
   `MASTER_CONTEXT.md`. Wait for explicit confirmation before generating. If `sufficient` is
   false, say so and stop; the response carries `shortBy` and `topUpUrl`.

   The call says nothing about the prompt itself. **No endpoint on this API reads a prompt
   for quality**, so a weak prompt prices, charges and renders exactly like a strong one —
   the template library is the whole quality gate, and it is why a prompt here says "sunlit
   kitchen, soft window light from camera-left" rather than "cinematic kitchen".

   Two things the estimate will not catch: it prices `numImages` but never sees
   `aspectRatio` or `referenceAssetIds` (sending either is a `400 Unrecognized key`), and it
   does not run moderation — so a prompt the estimate blessed can still come back `422`.

5. **Generate.** Run the matching `scripts/generate_image.py` with `--prompt`,
   `--aspect-ratio`, `--n`, and reference images. The script polls a render that answers `running`, then hands back finished images,
   with `creditsCharged` telling you what it actually cost.

6. **Visual QA.** Read each output image. Check for: garbled small text (most common
   gpt-image-2 failure), extra fingers / wrong limb count (Nano Banana failure), wordmark
   drift, wrong text count, UI proportion drift. Regenerate with a revised prompt if defective
   (cap 2 retries). **Each retry is a fresh charge** — there is no free re-roll — so report the
   extra credits at the end of the run.

7. **Hand off the image paths** to the user's separate `meta-ad-builder` skill — that's the
   skill that uploads to Meta, writes ad copy, clones page/ad-set/CTA, etc. The image-ad skills
   produce *images*, not *ads*.

---

## Standard workflow — clone an existing ad into a reusable template

Use the `clone-image-ad` skill (single model-agnostic skill — Phase 1 asks which generator to
validate against, Phase 8 optionally cross-validates on another).

The 10-phase workflow lives in `shared/skills/clone-image-ad/prompting/guide.md`. Key checkpoints:

- **Phase 2 (visual analysis)** — describe the reference structurally, separating brand-specific content from format/structure.
- **Phase 4-5 (generate + iterate)** — round-trip the prompt through the matching generator until structure is faithful. Cap at 4 iterations.
- **Phase 6 (generalize)** — replace `[BRAND]`-marked elements with `{placeholder}` variables.
- **Phase 7 (test with different brand)** — fill placeholders for a different brand and regenerate. If structure breaks, refine the placeholder set.
- **Phase 8 (cross-model validation, optional)** — round-trip the same template through another model and document deltas in the `Model notes:` block.
- **Phase 9-10 (document + save)** — append a new T<n> entry to `prompting/prompt-library.md` with the required structure.

A clone run is many generations — the iteration cap alone allows four, plus the
different-brand test and any cross-model check. **Estimate the whole run up front, not each
call**, so the user approves a total rather than being asked six times.

The library is append-only. New templates start at T43 — the next free number after the
seeded T1-T39 and the T40-T42 added since.

---

## What this ecosystem does NOT do

Surface these limits clearly when the user asks for anything outside scope:

- **Meta upload.** Different skill — `meta-ad-builder` (in `shared/skills/meta-ad-builder/`). The image-ad skills produce image files; the ad-builder skill handles cloning page/ad-set/CTA, writing copy, and uploading as paused ads.
- **Ad copy writing.** Different skill (the user's `meta-ad-builder` or equivalent handles body/headline).
- **Video, carousel, DCO ads.** Image only. For video, the `novoads-api` skill owns the video models.
- **Editing or retouching an existing image.** No model on this API has an edit or inpainting path. The nearest honest answer is a fresh generation with the original uploaded as a reference — say that, don't imply an edit.
- **Cross-model in one run.** If the user wants gpt-image-2 AND nano-banana-pro variants of the same prompt, run the generators sequentially. Each generator skill is locked to one model.

---

## Files this ecosystem owns

```
skills/
  chatgpt-image-ad/
    SKILL.md
    scripts/generate_image.py
  nano-banana-image-ad/
    SKILL.md
    scripts/generate_image.py
  clone-image-ad/
    SKILL.md

shared/skills/
  image-ad-prompting/      ← shared brain (this folder)
    OVERVIEW.md            ← this file
    prompting/
      prompt-library.md
      template-format.md
      safety-suffixes.md
  chatgpt-image-ad/
    prompting/guide.md
  nano-banana-image-ad/
    prompting/guide.md
  clone-image-ad/
    prompting/guide.md
```

---

## For human onboarding

If you're a human reading this for the first time:
- See [prompt-library.md](prompting/prompt-library.md) for the 40 validated ad templates.
- See [chatgpt-image-ad/SKILL.md](../../../skills/chatgpt-image-ad/SKILL.md) and [nano-banana-image-ad/SKILL.md](../../../skills/nano-banana-image-ad/SKILL.md) for hands-on usage.
- The `clone-image-ad` skill is for *making new templates*, not generating ads — only invoke it when you want to add to the library.
