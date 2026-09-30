# clone-image-ad — reverse-engineer an existing ad into a reusable template

This guide is the shared brain for the **`clone-image-ad`** skill — taking an existing image ad and turning it into a parameterizable prompt template stored in the shared library.

The workflow is **model-agnostic through Phase 6**. The model choice happens in Phase 1: the skill asks the user (or auto-detects from the reference's typography-vs-photo balance) which of the three Novoads image models to validate against:

- **`gpt-image-2`** — typography / UI-mimicry templates
- **`nano-banana-pro`** — photoreal / lifestyle / multi-reference templates
- **`reve-2.1`** — the third opinion, when a template renders wrong on both of the others or the user wants a deliberately different look

Phase 8 optionally cross-validates on another model so the resulting library entry has accurate `Model notes:`.

All three are reached through this skill's own validator, `scripts/validate_image.py`. The two
generator skills are model-locked on purpose; cloning is the one workflow that needs to move
between models, so it carries its own caller.

For the shared library, see:
- [prompt-library.md](../../image-ad-prompting/prompting/prompt-library.md) — destination for new entries
- [template-format.md](../../image-ad-prompting/prompting/template-format.md) — entry format / skeleton
- [safety-suffixes.md](../../image-ad-prompting/prompting/safety-suffixes.md) — the 3 always-on suffixes
- [OVERVIEW.md](../../image-ad-prompting/OVERVIEW.md) — the ecosystem hub

## Hard rules — never relax

1. **Strip platform/screenshot chrome from analysis.** When describing what's in the reference, describe the actual ad creative, not the screenshot wrapper. Do not include iOS status bars, "Sponsored"/"Saved" badges, post text/captions surrounding the image, link-card footers, engagement rows, platform tab bars. If the reference is a screenshot of an ad-in-feed, mentally crop the wrapper. The output template must produce a standalone image that would be uploaded as a Meta creative.

2. **Always validate by generating.** A template that hasn't been round-tripped through the chosen model against the original isn't validated. Run at least one generation with `--image-ref <original>` and compare. Refine the prompt until the structure matches.

3. **Always test the generalized version.** Before saving, fill the placeholders with a *different brand* and generate. If the structure breaks, the placeholder set is wrong — fix it.

4. **Never write brand-specific text into the final template.** Wordmarks, product names, slogans, specific photographs, hex colors specific to the source brand — all become `{placeholders}`. Only structural content (layout descriptions, photography style, typography family, composition rules) remains literal.

5. **A v1 faithful clone is an internal working artifact and is never publishable.** Phase 4 deliberately reproduces the source *including* its wordmark, its registered marks and any real customer testimonial in it — that is what makes it a structural check. It is evidence, not creative: it never goes in an ad account, a deck, a social post or a case study. **Placeholderization (Phase 6) is where brand-specifics and real testimonials die**, and nothing leaves this workflow until they have. A quoted review carries a real person's name; invent the fill, never inherit it.

6. **Save to the user's library, do not silently overwrite.** Default save target is the shared library at `shared/skills/image-ad-prompting/prompting/prompt-library.md`. If the target template name (e.g., `T40 — Lifestyle hero`) collides with an existing entry, ask the user before overwriting.

7. **Document model notes for more than one model when you can.** Even if the user only cares about one right now, the library entry's value is portability — a `gpt-image-2: clean / nano-banana-pro: weak on small text` note saves future you from picking the wrong model.

8. **Price the whole run up front, once.** A clone is not one generation. Phase 4 plus the Phase 5 iteration cap plus the Phase 7 test fill plus an optional Phase 8 cross-check is **six or more charged calls**, and every one of them is billed. Show the user a total from live estimates before Phase 4 and get one explicit yes — do not ask six times, and do not discover the cost at the end.

## Cost — the one thing this workflow gets wrong if you let it

Every generation in this workflow is charged. There are no free re-rolls and no refunds for a
render you didn't like (the only automatic refund is `502 provider_failed`, when the provider
itself broke).

Before Phase 4, price the run with `POST /v1/estimates`:

```bash
curl -sS -X POST "$NOVOADS_BASE_URL/v1/estimates" \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"kind":"image","model":"<chosen model>","prompt":"<the v1 prompt>","numImages":1}'
```

Multiply by the number of calls the run may need and present that as a **range**: the floor is
Phase 4 + Phase 7 (two calls), the ceiling is Phase 4 + four iterations + Phase 7 + Phase 8.
Say which model each leg prices at — the schedules differ by more than 3× across the three, so
a cross-model Phase 8 on `reve-2.1` costs meaningfully more than the same call on `gpt-image-2`.

A **batch** (several references in one conversation) prices once, up front: the estimate
validates the prompt it is given, so run one estimate (it charges nothing) per distinct final prompt, present
one combined range covering every reference, and get ONE yes for the whole batch.

A batch also needs a **ledger, not a tally**. Summing each response's `creditsCharged` is
correct per call and silently under-reports across a batch — one response that scrolled past
instead of landing in the log is enough, and a 2026-08-05 nine-call run reported 3.00 credits
across 8 calls when the truth was 3.5 across 9. So read the `balance` that `POST /v1/estimates`
returns **before the first charged call and again after the last** (the estimate charges nothing; this
adds no cost), and report both: the summed `creditsCharged` and the balance delta.

**When they disagree, the delta wins only if you are the sole spender on the organization.** The
balance is org-wide, so anything else charging that key lands in your delta. Measured 2026-08-06:
a three-call probe summed 0.9 (correct — 0.3 × 3) while the full-window delta read 2.4, because
parallel sessions were generating against the same org; the balance moved 3.4 credits between two
runs in which this workflow spent nothing at all. The fix is not to distrust the delta, it is to
**bracket tightly**: read the balance immediately before and immediately after *each* charged
call, not once around the whole batch. Tight brackets in that same run reproduced 0.3 exactly.
So: report both numbers, prefer the delta when the brackets are tight and the org is quiet,
prefer the per-call `creditsCharged` when other work is in flight, and **say which one you chose
and why** — a number reported without that context is the failure mode this rule exists to stop.

The estimate charges nothing and it is the **only** legitimate source of a price. It says nothing about
the prompt — no endpoint here does — so re-read the clone prompt against the template rules
yourself before pricing. It is going to be run six times, which makes a flaw in it six times as
expensive as anywhere else in the ecosystem.

## Inputs the user must provide

| Input | Notes |
|---|---|
| **Reference ad image** | Path to a local file (PNG/JPG/WEBP). The thing being reverse-engineered. |
| Brand to test against (optional) | If they want the test fill to use a specific brand. Ask if unset. |
| Save target (optional) | Defaults to the shared library at `shared/skills/image-ad-prompting/prompting/prompt-library.md`. |
| Template tag (optional) | Short identifier like `T40`, `Lifestyle Hero` — propose one based on the analysis if not given. |

## Workflow

### Phase 1: Preflight

1. The reference image path resolves to an existing file. If not, stop and ask.
2. `.env` has `NOVOADS_API_KEY`; `./scripts/check-novoads-env.sh` prints OK.
3. **Pick the model.** Ask the user "validate against gpt-image-2, nano-banana-pro, or reve-2.1?" or auto-detect from the reference (typography-heavy → `gpt-image-2`; photoreal / handheld / multi-ref → `nano-banana-pro`). Default to one of those two; `reve-2.1` is a deliberate choice, not a fallback.
4. Locate this skill's validator: `skills/clone-image-ad/scripts/validate_image.py`. It takes `--model` and applies that model's own aspect-ratio grid.
5. Read the save target (the shared library). If the file exists, read its current entries to know what tags are taken. If not, plan to create it.

### Phase 2: Visual analysis

This is the most important phase. Read the reference image and describe what you see, structurally separating brand-specific content from format/structure. Document each of these:

- **Aspect ratio.** Measure or estimate (W:H). Map to the nearest ratio the chosen model accepts:
  - `gpt-image-2`: `1:1` `2:3` `4:5` `9:16` `16:9` `21:9`
  - `nano-banana-pro` and `reve-2.1`: those six plus `3:2` `3:4` `4:3` `5:4`

  If the original's ratio exists on one model and not another, say so in the template's
  `Aspect ratio:` field — it is a real routing constraint, not a footnote. A `1.91:1` ad maps
  to `16:9` and post-crops; a `4:3` ad is native on two models and needs a mapping on the third.
- **Format type.** What this ad pretends to be: editorial article, product flatlay, comparison table, fake search results, story composite, native UI mimic, etc.
- **Layout structure.** Header / hero / footer / grid — how regions are arranged.
- **Typography.** Family (geometric sans, condensed sans, serif, handwritten marker, monospace), weight, hierarchy. Do NOT name specific fonts unless they're iconic and necessary; instead describe the *feel*.
- **Color palette.** 3-6 hex codes. Identify which are brand-specific (will become `{brand.color_*}` variables) vs neutral/structural (white/black/grey backgrounds — stay literal).
- **Photography style.** Studio product flatlay, lifestyle UGC, editorial portrait, stock-photo-grid, etc. Describe lighting and lens.
- **Text content (verbatim).** Every visible string in the image. Mark which strings are *brand-specific* vs *structural* (e.g. "AS SEEN ON", "VS").
- **Decorative / non-text elements.** Icons, divider lines, badges, emojis, hand-lettering, sticky-note props.
- **Branded vs structural elements.** This is the key column. For everything you've described, mark each piece as `[BRAND]` (will become a variable) or `[STRUCTURE]` (stays literal in the template).
- **Chrome to strip.** Anything you saw that's a screenshot/platform artifact. Note it for explicit exclusion in the prompt.

State this analysis to the user as a compact summary. Don't move on until it's complete.

### Phase 3: Draft v1 prompt (faithful, brand-specifics intact)

Write a prompt that, paired with the reference image, would reproduce the ad faithfully. At this stage, leave brand-specific content **literal** — do not placeholder-ize yet.

Structure the prompt with these sections (omit any that don't apply):
- Aspect ratio + canvas (e.g. "1:1 static ad creative, edge-to-edge")
- Background description
- Header section (top X% of the image)
- Main content / hero section
- Decorative elements (badges, dividers)
- Bottom section / footer band
- Typography note (weight, family-feel, hierarchy)
- Composition / spacing rules
- **Explicit chrome exclusion** — name what NOT to render (the validator's no-chrome suffix is a safety net; the prompt should also explicitly exclude)

**Your budget depends on the model you chose in Phase 1.** The prompt ceiling is per model, and
the three always-on safety suffixes consume 1,575 characters of it before your first word:

| `--model` | prompt ceiling | your v1 budget on default flags |
|---|---|---|
| `gpt-image-2` | 32,000 | 30,425 |
| `nano-banana-pro` | 50,000 | 48,425 |
| `reve-2.1` | 4,000 | **2,425** |

Deployed spec 2.16.0, verified 2026-08-08. On the first two, be as exhaustive as Phase 2 asks
and do not budget at all: a faithful six-panel clone wants roughly 3,000 characters, which is a
tenth of the room. On `reve-2.1` that same clone overflows on the first attempt, and that is the
expected outcome rather than user error. The validator checks the assembled prompt locally,
fails before spending anything, prints the exact budget for the flags you passed
(`--allow-chrome` and `--no-safe-zone` each buy some of it back), and names the roomier models.
On `reve-2.1`, aim under 2,425 anyway: a v1 that only just fits leaves no room for Phase 5's
refinements. Switching models is the other repair, and usually the better one, since trimming
costs the clone fidelity the run exists to measure.

Show the v1 prompt to the user, then price the run (see **Cost** above) and get the go-ahead.

### Phase 4: Generate with reference

Fire one generation with the original as a reference and the matched aspect ratio.

```bash
./skills/clone-image-ad/scripts/validate_image.py \
  --model <gpt-image-2|nano-banana-pro|reve-2.1> \
  --prompt "$(cat prompts/<tag>-v1.txt)" \
  --aspect-ratio <matched_ratio> \
  --image-ref <reference_path> \
  --out iterations/clone-tmp \
  --env-file .env
```

(Write the prompt to a file — **`prompts/<tag>-v1.txt`** — and pass it with `$(cat …)`, to avoid
shell-quoting hell. Name the directory: `prompts/` is gitignored and is where composed prompts
belong, so the six or so drafts Phase 5 goes through stay out of the user's `git status`. This
line used to say "a temp file" and nothing more, and a session that took it at its word invented
a top-level `prompts/` of its own — correct instinct, untracked directory, a diff the user had to
explain.) The call blocks for the render, typically 60–90 seconds. A render still going after about 105 seconds answers `status: "running"` with no images instead (API 2.39.0): poll `GET /v1/generations/{jobId}` to a terminal status and read `images[]` there. Never resubmit it; that job is already paid. Read the generated
image when it returns.

The reference cap is per model — 4 on `gpt-image-2`, 14 on `nano-banana-pro`, 8 on `reve-2.1`
(verified against spec 2.7.0, 2026-08-04). For Phase 4 you normally pass exactly one: the
original ad.

### Phase 5: Compare and iterate

Show the user the original side-by-side with the generated. Identify deltas:
- Layout regions misplaced or missing
- Typography weight wrong
- Wrong aspect ratio interpretation
- Brand color drifted
- Decorative elements (icons, badges) wrong or missing

Refine the prompt based on the deltas. Regenerate. Repeat until the structure is faithful
enough to call it "good." **Cap at 4 iterations** — beyond that, the prompt has a structural
problem and needs more dramatic editing rather than tweaking. Every iteration is charged; track
the running total and report it at the end.

**Upload the original once — and every render is addressable after that.** The `assetId` from
`POST /v1/uploads` is durable and reusable without limit, so the source ad is uploaded one time
and passed to Phase 4, all four Phase 5 iterations, Phase 7 and Phase 8 off that one id. Since
deployed spec `2.11.0` the *generated* images are addressable the same way: every entry in an
`images[]` response carries its own `assetId`, and `referenceAssetIds` and `sourceAssetId` both
accept it directly. So an iteration can be anchored to the previous render — `referenceAssetIds:
[original, v1]` to say "keep what v1 got right, fix the header" — with no download and no
re-upload. Re-uploading a file you already have an id for is the bug, not the safe move.

### Phase 6: Generalize into placeholders

This is where the template becomes reusable. Walk back through the v1 prompt and replace every `[BRAND]`-marked element from Phase 2 with a `{placeholder}` variable. Use the standard placeholder vocabulary:

**Standard variables** (use these names where they fit):
- `{brand.name}` — wordmark text
- `{brand.color_primary}` — primary brand color hex (e.g. `#1A4731`)
- `{brand.color_accent}` — secondary accent color hex (if used)
- `{brand.product_image_description}` — one-line description of the product visible in the ad
- `{brand.tagline}` — short brand promise
- `{brand.competitor_category}` — for comparison templates: what's being compared against
- `{ad.headline}` — top-line headline copy
- `{ad.subcopy}` — sub-headline / supporting copy
- `{ad.body}` — primary text block
- `{ad.cta_phrase}` — CTA button text

**Template-specific variables** — name them clearly when needed:
- `{checklist_items[]}` (Notes-style)
- `{tweet_body}` (story templates)
- `{rows[]}` (comparison templates)
- `{publication}` (editorial templates)
- `{ugc_subject}` (UGC photo composite templates)

For each variable: write a 1-line description of what it represents and what kind of value goes in it.

### Phase 7: Test the generalized template

Pick a different brand and substitute test values into every placeholder. Generate again with `--image-ref` set to the test brand's product photo (NOT the original ad). The output should:
1. Have the same layout/composition as the original
2. Show the test brand instead of the source brand
3. Read as a coherent ad, not a frankenstein

If the test fails, the structure breaks under different brand assumptions — return to Phase 6 and refine the placeholder set. Often the fix is a placeholder that was missed (e.g. you hardcoded a font feel that's specific to one brand).

**The second way to run this phase: edit the source instead of re-describing it.** `POST /v1/images`
takes `sourceAssetId` (`gpt-image-2` only) — pass the ORIGINAL ad and a prompt that names only what
changes, and the model repaints those zones while leaving the rest of the frame alone. That is
exactly what Phase 7 is trying to prove, so it is the better instrument here:

```bash
./skills/clone-image-ad/scripts/validate_image.py --model gpt-image-2 \
  --prompt "$(cat prompts/<tag>-swap.txt)" --source-image original-ad.jpg \
  --out iterations/clone-<date>/T40/test-fill --env-file .env
```

Measured on a 2026-08-06 A/B (one source, three renders, `gpt-image-2`, 0.3 credits each):

- **Phase 4 is NOT the place for it.** Given the same full faithful-reproduction prompt, the edit
  arm came back *worse* than the reference arm at identical cost — it recoloured a headline block
  that the reference arm got right. A full redraw is not an edit; describing the whole frame to an
  edit endpoint wastes what makes it an edit.
- **Phase 7 is.** Given a short prompt naming only the brand zones, the edit arm transplanted
  wordmark, footer URL and a tiled monogram while holding foil texture, torn scratch edges, panel
  grid, barcode, fine print, camera angle and lighting exactly — in one call, with no placeholder
  prompt to engineer.
- **It drifts typography.** In that same run the headline came back restyled from condensed sans to
  a brush italic although nothing asked for it. **Pin the type explicitly** in a swap prompt
  ("headline stays bold condensed uppercase sans"), and check it first when you compare.

An edit is a check on the STRUCTURE, not a substitute for the template. The deliverable of Phase 7
is still a placeholder set that survives a different brand — if the edit passes and the
placeholderized prompt does not, the template is what is broken.

**Do not confuse the aspect-ratio rules.** An edit's output tracks the source's shape, so a
`sourceAssetId` and an `aspectRatio` together are a 400. The validator refuses the pair locally,
before spending.

### Phase 8: Cross-model validation (optional but recommended)

Run the same template through another model and note the deltas in the `Model notes` block:

```markdown
**Model notes:**
- **gpt-image-2:** {what works, what struggles, e.g. "clean — strong on the table text"}
- **nano-banana-pro:** {e.g. "table text blurs at small row height — keep rows to 4 max, or use gpt-image-2"}
- **reve-2.1:** {untested, or what it did differently}
```

Only the model you actually ran gets a claim. For the rest, say so:

```markdown
**Model notes:**
- **gpt-image-2:** validated clean (see iteration path)
- **nano-banana-pro:** untested — validate before using on that model
- **reve-2.1:** untested
```

Never write a note for a model you didn't run. An invented model note is worse than an absent
one — it is the whole reason the block exists.

### Phase 9: Document the template

Compose the library entry. Use the format in [template-format.md](../../image-ad-prompting/prompting/template-format.md).

The entry must include:
- **Tag and one-line title** (e.g. `T40 — Lifestyle hero with overlay text`)
- **When to use** — 1-2 sentences on positioning fit
- **Aspect ratio** recommendation, and whether it is native on all three models
- **Reference image guidance** — what kind of reference to pass when reusing this template
- **Variable schema** — every `{placeholder}` with a 1-line description
- **Template prompt** in a fenced code block, ready to copy-paste-fill
- **Example fill** — the test fill from Phase 7, showing the variables substituted
- **Model notes** — per-model behavior, marking untested models as untested
- **Validated example path** — pointer to the iteration dir

### Phase 10: Save and confirm

1. Append the entry to the configured library file. If overwriting an existing tag, ask first.
2. Print the entry's path so the user can review.
3. Move the validated PNGs from `iterations/clone-tmp/` to a permanent dir keyed by the template tag.
4. Report the **total credits charged** across every call the run made.
5. Tell the user the template is now available to `chatgpt-image-ad` and `nano-banana-image-ad` (subject to the model notes' recommendation).

## Naming convention for new templates

If the save target already has T1–T42, continue with T43, T44, … Use semantic suffixes if helpful: `T43 — Lifestyle hero`, `T44 — Carousel cover`. Keep the `T<n>` part for cross-skill referencing.

## Out of scope

- **Generating real ads / uploading to Meta.** The `meta-ad-builder` skill. This skill produces templates only.
- **Reverse-engineering video ads.** Image only. Refuse with: *"This skill is for static image ads. Video reverse-engineering isn't supported in this version."*
- **Multi-template extraction in one run.** One reference → one template per skill invocation. A folder of N references is N independent runs — and they may run in parallel: since deployed spec `2.12.0` images have their **own** concurrency budget of **12** in flight per organization (`429`, `details.reason` `image_concurrency_limit`), counted separately from the 5-video budget in both directions, so a clone batch may run twelve wide and never blocks a render. Stagger only beyond 12. (Before `2.12.0` images spent video slots and the number here was 5 — if a `429` says `concurrency_limit` rather than `image_concurrency_limit`, you are reading the video queue.) Price the whole batch up front per the Cost section — one estimate per distinct final prompt (it charges nothing), one combined range, ONE consent before the first charged call.
- **Modifying existing templates in the library.** If the user wants to revise T3, treat it as a new run pointed at the same library entry — show the diff and ask before overwriting.
- **Editing the source image *as the way to build the template*.** There IS an image-edit path — `sourceAssetId` on `POST /v1/images`, `gpt-image-2` only — but a template is a *prompt*, and an edit produces a picture without producing the prompt that made it. Use it where it belongs (Phase 7) and never as a shortcut past Phases 3-6. An earlier version of this file said flatly that no edit path existed; that stopped being true at deployed spec `2.10.0`.

## Files this skill writes to (in user space)

- The configured prompt library (default: `shared/skills/image-ad-prompting/prompting/prompt-library.md`) — appended, never silently overwritten
- `<cwd>/prompts/<tag>-*.txt` — each draft as you compose it, so `--prompt "$(cat …)"` never fights the shell
- `<cwd>/iterations/clone-<date>/<tag>/prompt.txt` — the final validated prompt
- `<cwd>/iterations/clone-<date>/<tag>/v1.png`, `v2.png`, … — each iteration's output

Both directories are gitignored — they are the run's work-product, not repo content. Write into
them freely and do not invent a third one; see `AGENTS.md` ("Every session").

## Dependencies

- `skills/clone-image-ad/scripts/validate_image.py` — this skill's own model-aware caller.
- `.env` with `NOVOADS_API_KEY`.
- Python 3.12+.

The two generator skills are **not** required for a clone run. They are where the finished
template gets used afterwards.
