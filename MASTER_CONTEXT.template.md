# Master context (project + agents)

**Purpose:** One place for humans and AI agents to capture **decisions**, **brand voice**, **API quirks**, and **what we learned** while using this repo.

## How agents should use this file

- **At the start of substantive work:** Read this file for project-specific context that is not in the skill.
- **After meaningful changes:** Append a new **dated entry** under [Changelog](#changelog) (Decision / What changed / Why).
- **If fields are empty:** Fill them lazily. The first time the user asks to generate something that needs a field (default product, brand voice), ask for it then — once — and write the value back so no future session asks again. A setup session asks for nothing beyond the API key.

## Brand context

**Nobody fills this in up front.** Each field is asked for the first time a skill
genuinely needs it, once, and written back so no later session asks again. A blank
file is the normal starting state.

Read and write it with `scripts/brand-context.py` rather than by hand — it is the
one file every skill reads, and hand edits drift the format. `check <skill>` says
what is missing and nothing more:

```bash
./scripts/brand-context.py check clone-static   # exit 2 = blocked, and names why
./scripts/brand-context.py set product.photo references/products/hero.png
./scripts/brand-context.py list                 # everything, set or not
```

Editing by hand is fine too — keep one `- **Label:** value` per line.

**Fastest way to fill most of it:** `./scripts/brand-context.py from-url https://yourbrand.com`
drafts the brand block from your own site. It costs no credits, and every field it
drafts is shown for correction before anything is generated from it.

### Who you are

- **Brand name:**
- **One-liner:**
- **Logo file:**
- **Colors:**
- **Fonts:**

### How you sound

Used when a clone rewrites the source's copy at the same length and rhythm. **Sample
phrasings earn their keep here** — "direct, warm" is not something a model can act on,
and a real line of your own copy is.

- **Tone:**
- **Audience:**
- **Words to use:**
- **Words to avoid:**
- **Sample phrasings:**

### What you sell

The two blocking fields. No clone renders without them, because a competitor's ad says
nothing about what your product looks like and a fabricated one is the failure a viewer
catches instantly.

- **Product photo:**
- **Product description:**

### Your market

Filled by `spy-competitor-ads`. `Last swept` is what decides whether the next run reuses
the stored swipe file or pays for a fresh sweep.

- **Competitors:**
- **Last swept:**
- **Winning ads:**

## Reference images

Drop reference images into the `references/` folder at the repo root:
- `references/influencers/` — face/body photos to recreate as AI people
- `references/products/` — product photos for showcase workflows
- `references/aesthetics/` — mood boards, lighting references, style inspiration

The agent checks this folder when composing prompts. (If the API in this repo requires hosted URLs rather than local file uploads, also fill in your hosting strategy in the API-specific section below.)

## Universal prompting principles

These apply across all generative-image and generative-video APIs.

### UGC realism

- **Imperfection block (camera):** Every UGC image/video prompt must include camera imperfections: motion blur, overexposure, grain, lens distortion, off-center framing, soft focus. Without this, output looks too polished.
- **Skin realism block (mandatory):** Include 3–4 subtle skin cues inline with character description: "visible pores, slight unevenness in skin tone, minor undereye shadows, hint of shine from natural oils." Do NOT use: acne, pimples, breakouts, blemishes, redness. Goal is "real person, not retouched" — not "person with skin problems."
- **Reference image order:** character hero first (strongest identity signal), then product, then style refs.

### Influencer / character recreation

- Two-step flow: (1) generate a still image with the reference image as input, (2) show user for approval, (3) only then generate video using the approved still as the start frame / reference.
- Never skip the approval step — video is expensive, stills are cheap to iterate.

### Image QA

- Visually review still images after generation (hands, fingers, limbs, face, merged objects, artifacts).
- If defective, regenerate with refined prompt — up to **2 retries** (3 attempts total).
- QA retries skip a second credit confirmation but still bill credits.

### Video prompting

- **No subtitles, no captions, no text overlays** — append this clause to every prompt; many video models burn captions in by default.
- **Human motion cues are mandatory** for person-on-screen videos: 3–4 cues per prompt (breaking eye contact, head tilts, weight shifts, grip adjustments). Without these, subjects look like frozen mannequins.

## Meta ad deployment

Used by the **`meta-ad-builder`** shared skill (`shared/skills/meta-ad-builder/`) — publishes
finished creatives as Meta (Facebook/Instagram) ads. Fill in your account IDs once; the skill
reads them so you don't paste them every run. These are account identifiers, not secrets, but
the file is gitignored either way.

- **Default ad account** (`META_AD_ACCOUNT_ID`):
- **Facebook Page ID** (`META_PAGE_ID`):
- **Instagram user ID** (`META_IG_USER_ID`):
- **Meta Pixel ID** (`META_PIXEL_ID`):
- **Default destination URL / offer link:**
- **Default ad set(s) to deploy into** (name → ID):
- **Default CTA type** (e.g. `SIGN_UP`, `LEARN_MORE`):

The access token itself (`META_ACCESS_TOKEN`) lives in `.env`, never here. Every ad the skill
creates is **PAUSED** — review and un-pause in Meta Ads Manager.



## Project snapshot — Novoads

- **API base:** `https://api.novoads.ai/v1` (see `.env.example`). `NOVOADS_BASE_URL` overrides the host only — callers append `/v1/…`.
- **Auth:** `Authorization: Bearer $NOVOADS_API_KEY`. The key is `novo_` plus 64 hex, created at <https://novoads.ai/dashboard/settings?tab=api>; no quoting needed in `.env`. Check it with `./scripts/check-novoads-env.sh`.
- **Skill:** `.claude/skills/novoads-api/` and `.cursor/skills/novoads-api/` (sync from `skills/novoads-api/` via `scripts/sync-skill.sh`).
- **Spec:** <https://api.novoads.ai/v1/openapi.json> is the authority whenever a file in this repo disagrees with it.

## My workspace

- **Default product ID:** _(auto-populated after first `GET /v1/products` call)_
- **Default product name:** _(auto-populated)_

### Products

One block per brand, written the first time a product image arrives, so a later session
finds what the first one uploaded instead of asking for it again. If a call or a job built on a
cached `assetId` fails, upload the local reference again and replace the id.

- **Product slug:** _(auto-populated)_
  - **Local reference:** _(auto-populated: the file under `references/products/`)_
  - **Upload `assetId`:** _(auto-populated after the first `POST /v1/uploads`)_
  - **`productId`:** _(auto-populated after `POST /v1/products`)_

## Credit costs

**This file holds no prices, deliberately.** Every credit number comes from a live
`POST /v1/estimates` call in the session that is about to spend, shown to you and approved
before anything is generated — that call is free and also validates the prompt. Do not add a
rate table here: a stored number goes stale silently and a quote that disagrees with the
invoice is worse than no quote. `GET /v1/models` carries the live schedules if you want to
compare models.

## API learnings — Novoads

**Empty on purpose. Your sessions fill it in.**

Endpoints, fields, limits, status codes, timings, and error branching are already documented in
the skill — `skills/novoads-api/SKILL.md` and its `reference.md`, with
<https://api.novoads.ai/v1/openapi.json> as the authority above both. Do not copy any of that
here: a second copy drifts, and then two files disagree about what the API does.

What belongs here is what the skill cannot know — things learned while generating *your* ads:
a prompt phrasing that keeps failing for your product category, a duration that reads better for
your audience than the table suggests, a reference image that consistently produces a good start
frame. Add them as dated bullets, and if a note contradicts the skill, say so explicitly and
verify against the live spec before trusting it.

Never record a price here. See "Credit costs" above.

## Changelog

Dated entries, newest last — Decision / What changed / Why.
