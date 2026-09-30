# Image-ad prompt library

Validated, parameterizable prompt templates for generating standalone Meta ad creatives. Pair each with a brand product reference image via `--image-ref` for brand fidelity.

**Hard rule:** every prompt in this library produces a *standalone* image upload — no iOS chrome, no platform UI, no brand-row, no link card, no engagement counts. Those are added by Meta when displaying the ad.

**The script auto-appends three always-on safety suffixes** to every prompt (you don't need to repeat these constraints in your library entry). See [safety-suffixes.md](safety-suffixes.md):
1. **`NO_CHROME_SUFFIX`** — strips iOS chrome, platform brand-rows, post text, link-card footers, engagement rows, action buttons, comment input, tab bars, Story chrome.
2. **`SAFE_ZONE_SUFFIX`** — forces all text/headlines/CTAs/focal subjects to fit within the central 84% of the canvas (8% padding from every edge). Backgrounds may bleed; text and focal elements may not. Eliminates clipped headlines.
3. **`GLYPH_SAFETY_SUFFIX`** — forbids emoji and unicode glyphs inside body-text blocks (chat bubbles, comments, ChatGPT responses, Slack messages); enforces the exact count of conversation elements the prompt specifies.

Together: ~1,575 chars of always-on guard, leaving headroom under each model's prompt cap for your actual prompt body.

**Reference image:** unless noted otherwise, pass a clean product hero shot (white-background product photo of the brand's packaging, including pouch / bottle / canister / sachets). The reference is the brand-fidelity anchor; the prompt is the format.

**Model portability:** every entry includes a `Model notes` block explaining how each template renders on the models the image-ad skills target:

- **`gpt-image-2`** (ChatGPT Image 2) — strong text fidelity, dense small-text rendering, faithful UI mimicry (iOS, Slack, Google search, comparison tables). Best for typography-heavy templates. The API default, and the cheapest of the three.
- **`nano-banana-pro`** (Nano Banana Pro) — strong photorealism, multi-image reference blending, character continuity across runs. Weaker on dense small text.
- **`reve-2.1`** — the third opinion, reachable through the `clone-image-ad` validator. Most entries list it as `untested`; that is honest, and better than a guess.

**The reference cap is per model, not one number** — `gpt-image-2` takes 4, `reve-2.1` 8,
`nano-banana-pro` 14 (spec 2.7.0; `./scripts/verify-image-caps.sh` is the standing check).
Every template here fits inside the smallest of those, so a template's reference guidance
never needs to name a model for capacity reasons; the gap only matters when you carry a
reference set to a model with less room than the one it was written for. Uploads are free
and each returns a durable `assetId`, so build a library and cite from it.

When a template renders cleanly on more than one, the entry says `both: clean`. When one
struggles, the note tells the consuming skill which model to prefer.

---

## Contents

**Before you pick a template**

- [Aspect-ratio compatibility (read before picking a template)](#aspect-ratio-compatibility-read-before-picking-a-template)
- [How to use this file](#how-to-use-this-file)
  - [The standard pin block](#the-standard-pin-block) · [What actually fits](#what-actually-fits)

**Templates** (40, numbered T1 to T42; there is no T16 or T22). Each entry carries its number and its plain name, so either finds it.

*Screen and chat UI mimicry*

- [T1 — Apple Notes listicle aesthetic](#t1--apple-notes-listicle-aesthetic)
- [T3 — Story tweet+UGC composite](#t3--story-tweetugc-composite)
- [T4 — "Fake Google search" mosaic](#t4--fake-google-search-mosaic)
- [T11 — Fake comment thread (user → brand)](#t11--fake-comment-thread-user--brand)
- [T12 — Fake ChatGPT conversation](#t12--fake-chatgpt-conversation)
- [T14 — Fake Slack team conversation](#t14--fake-slack-team-conversation)
- [T19 — Fake AirDrop dialog (with before/after)](#t19--fake-airdrop-dialog-with-beforeafter)
- [T20 — IG Story Q&A sticker over lifestyle photo](#t20--ig-story-qa-sticker-over-lifestyle-photo)
- [T23 — POV calendar timeline of pain points](#t23--pov-calendar-timeline-of-pain-points)
- [T24 — Phone-in-phone Reel composite](#t24--phone-in-phone-reel-composite)
- [T28 — Dating app swipe card (Hinge-style)](#t28--dating-app-swipe-card-hinge-style)
- [T29 — TikTok creator video screenshot](#t29--tiktok-creator-video-screenshot)
- [T34 — iMessage conversation (with rich link card)](#t34--imessage-conversation-with-rich-link-card)
- [T37 — Weather-app forecast UI](#t37--weather-app-forecast-ui)
- [T41 — Brutalist headline over a social-post embed](#t41--brutalist-headline-over-a-social-post-embed)

*Comparison, data and proof*

- [T5 — Comparison table (light)](#t5--comparison-table-light)
- [T6 — Comparison table (dark, hooky)](#t6--comparison-table-dark-hooky)
- [T8 — Handwritten whiteboard / posterboard comparison](#t8--handwritten-whiteboard--posterboard-comparison)
- [T13 — Before/After two-panel split](#t13--beforeafter-two-panel-split)
- [T17 — Stacked-bar with vs without comparison](#t17--stacked-bar-with-vs-without-comparison)
- [T18 — Flowchart "old way" vs "new way"](#t18--flowchart-old-way-vs-new-way)
- [T38 — Big stat hero with chart](#t38--big-stat-hero-with-chart)
- [T40 — Scratch-off ticket stat grid](#t40--scratch-off-ticket-stat-grid)

*Handwritten and physical props*

- [T7 — Sticky-note + product flatlay](#t7--sticky-note--product-flatlay)
- [T10 — Letter board sign + product](#t10--letter-board-sign--product)
- [T21 — Handwritten testimonial on napkin / paper](#t21--handwritten-testimonial-on-napkin--paper)
- [T25 — Newspaper crossword puzzle](#t25--newspaper-crossword-puzzle)
- [T26 — Cash register receipt](#t26--cash-register-receipt)
- [T27 — Handwritten founder letter](#t27--handwritten-founder-letter)
- [T31 — Scratch-off lottery ticket](#t31--scratch-off-lottery-ticket)

*Editorial, print and out-of-home*

- [T2 — Editorial article hero](#t2--editorial-article-hero)
- [T30 — Billboard / OOH placement mockup](#t30--billboard--ooh-placement-mockup)
- [T33 — Bold typography hero quote](#t33--bold-typography-hero-quote)
- [T35 — Magazine cover](#t35--magazine-cover)
- [T39 — Museum exhibit display](#t39--museum-exhibit-display)
- [T42 — Editorial testimonial card](#t42--editorial-testimonial-card)

*Product-forward and lifestyle*

- [T9 — Annotated product features (arrow callouts)](#t9--annotated-product-features-arrow-callouts)
- [T15 — Ingredient list + collage (left/right split)](#t15--ingredient-list--collage-leftright-split)
- [T32 — Pain-point checklist + product](#t32--pain-point-checklist--product)
- [T36 — Lifestyle "operator's daily kit" flatlay](#t36--lifestyle-operators-daily-kit-flatlay)

**Maintaining the library**

- [Adding new templates](#adding-new-templates)
- [Known rendering limits (mitigated by always-on suffixes)](#known-rendering-limits-mitigated-by-always-on-suffixes)

*Hand-maintained: update it when you add, rename or reorder a heading, until CI generates this list.*

---

## Aspect-ratio compatibility (read before picking a template)

Each template recommends an aspect ratio in its **Aspect ratio:** field. Two grids, sourced
from the live request schemas (`GET /v1/openapi.json` is the authority):

| Ratio | `gpt-image-2` | `nano-banana-pro` / `reve-2.1` |
|---|---|---|
| `1:1` (API default) | ✅ | ✅ |
| `2:3` | ✅ | ✅ |
| `4:5` (Meta feed-portrait) | ✅ | ✅ |
| `9:16` | ✅ | ✅ |
| `16:9` | ✅ | ✅ |
| `21:9` | ✅ | ✅ |
| `3:2` | ❌ | ✅ |
| `3:4` | ❌ | ✅ |
| `4:3` | ❌ | ✅ |
| `5:4` | ❌ | ✅ |

**Every ratio used by the 40 templates in this file (`1:1`, `2:3`, `9:16`) renders natively on
all three models.** No template in this library needs a fallback-and-crop — that whole class of
workaround is gone. The gap only bites a bespoke prompt asking for `3:2`, `3:4`, `4:3` or `5:4`,
and the fix there is to route it to `nano-banana-pro` or `reve-2.1`.

**`aspectRatio` defaults to `1:1`.** A template whose field says `9:16` must send it explicitly;
forgetting produces a square image and a wasted charge. The request schemas are strict, so a
ratio from the wrong grid is a `400` before anything is charged.

## How to use this file

When the user asks for an image ad with a known format, find the matching template below, **check the aspect-ratio table above against the model you're using**, then replace the `{placeholder}` variables and invoke the matching `chatgpt-image-ad` or `nano-banana-image-ad` skill with the filled prompt + the brand's reference image.

**Pass every brand mark in the frame as a reference asset. Unpinned means invented.**
The `Reference image:` line on each template is a requirement, not a suggestion, and it
extends to any mark the template adds — a publication wordmark, a logo on a prop, a
competitor's packaging. A 34-template run on one real product (2026-08-04) is the evidence:
the product label was faithful in **all 34** because a reference pinned it, and every
brand element that was *not* pinned either drifted or was fabricated — including a
back-of-pack view invented whole, carrying a sourcing claim about a real brand that
appeared in no prompt. The model fills unspecified surfaces with plausible brand-shaped
content; silence reads as an invitation.

### The standard pin block

Do not hand-write that constraint per run — the hand-written ones came out at ~700
characters and were the single largest cause of a refused prompt. Paste this block, fill the
one placeholder, and change nothing else:

```
[BRAND PIN] {brand.product_description}, reproduced exactly as it appears in the reference image — same wordmark, same colours, same proportions, front face only. Do NOT render the back of the pack, invented label copy, ingredient lists, sourcing or health claims, or a barcode. Every word in this image is one this prompt specifies or one already printed on the reference.
```

The generator scripts carry it as `--pin-block "<product description>"`, which appends the
guard for you and counts it against the cap before anything is sent.

**Its budget is 400 characters** — 346 of fixed guard plus about 54 for the description.
Keep the description terse (`forest-green pouch with white AG1 wordmark`), because every
character it gains comes off the template body.

### What actually fits

**The prompt cap is per model.** It used to be a single 4,000 shared by every image model,
and deployed spec 2.16.0 (verified 2026-08-08) split it in three. It is measured on the *final*
prompt, meaning your body plus the three always-on suffixes, which are **1,575** characters
together, so each model's room for a template body is its own cap minus that.

| model | prompt cap | − suffixes = body room | − pin block = pinned room |
|---|---|---|---|
| `gpt-image-2` | 32,000 | **30,425** | 30,025 |
| `nano-banana-pro` | 50,000 | **48,425** | 48,025 |
| `reve-2.1` | 4,000 | **2,425** | 2,025 |

On `gpt-image-2` and `nano-banana-pro` the budget is no longer a real constraint on this
library: the longest template here is 2,909 characters, which leaves over 27,000 spare on the
tighter of the two. Write the fill the concept needs.

`reve-2.1` keeps the old 4,000 and is the only place the old arithmetic still bites.
**23 of the 40 templates** have room for the standard pin block on `reve-2.1`; the rest need a
trim first, and T8, T11 and T14 are over 2,425 and so are refused there before any brand fill.
That model is reachable only from the `clone-image-ad` validator, so this is a cross-check
constraint rather than a production one. The refusal costs nothing either way: the scripts measure
the final prompt against the model you named and die pre-network, naming the exact overage.
Run `python3 ../scripts/check_library.py --verbose` for every template's current headroom per
model, and read [evals.md](../evals.md) L1 for why the
long ones have not simply been shortened.

Every generation is charged, re-rolls included, so price the run with a live
`POST /v1/estimates` and get the user's OK first. That call charges nothing and it is the only
legitimate source of a price. It will not check your prompt — nothing on the API does.

**Variable conventions:**
- `{brand.name}` — wordmark text on the product label (e.g. `AG1`)
- `{brand.color_primary}` — primary brand color hex (e.g. `#1A4731` deep forest green)
- `{brand.product_description}` — one-line how-the-product-looks (e.g. `forest-green pouch with white AG1 wordmark, clear shaker bottle with green liquid, coral travel sachets`)
- `{brand.competitor_category}` — what the brand is replacing/winning against (e.g. `Generic Multivitamin`)
- `{brand.tagline}` — the brand's short value prop (e.g. `Greens, simplified.`)
- Template-specific variables defined per section.

---

## T1 — Apple Notes listicle aesthetic

**When to use:** emotional / sentimental product positioning, "things I love about X" voice, brands targeting older or wellness-conscious audiences. Reads like a real customer's private list.

**Aspect ratio:** `2:3` (Meta feed-portrait friendly without iOS device frame)

**Reference image:** clean product hero (helps brand-color drift in the rare emoji that gets a brand cue)

**Variables:**
- `{notes_title}` — bold black title (≤40 chars, may end with brand-relevant emoji)
- `{date_string}` — small grey timestamp under the header (e.g. "March 14, 2026 at 6:42 AM")
- `{checklist_items[]}` — 8-12 items, each conversational + 1-2 emoji decorations, optional date suffix

**Template prompt:**
```
2:3 portrait static ad creative — a clean Apple Notes app aesthetic mock-up rendered as a standalone image, edge-to-edge, on a pure white #FFFFFF background. The aesthetic mimics the look of a personal note in Apple Notes, but this is the upload-ready ad creative itself, not a phone screenshot.

Top of the image (taking ~10% height): an Apple Notes navigation header. Left: orange "< Notes" back-chevron + label in SF Pro semibold. Center: two orange icons — a forward-arrow circle (redo) and a circular refresh arrow. Right: a share-square icon and an ellipsis-in-circle icon, both grey. Hairline grey divider beneath.

Centered just below the header, in small grey SF Pro: "{date_string}"

Then bold black SF Pro title (large, ~32pt feel): "{notes_title}"

Then a vertical list of {N} unchecked checklist items. Each row: a hollow grey circle bullet on the left, then the item text in regular black SF Pro with emoji decorations interleaved. Items (verbatim):
{checklist_items_numbered}

Generous vertical spacing, items left-aligned with consistent left padding from the bullet.

Bottom of the image (~6% height): an Apple Notes toolbar with four icons evenly spaced — orange checklist/list icon (active), camera icon, "A" inside a circle (text style), and a pencil-edit-square icon.

The composition reads as a calm, honest personal note — like a real customer's private journal entry — but rendered as a standalone ad creative ready to upload. No keyboard, no selection state, no device chrome.
```

**Example fill** (AG1):
- `{notes_title}` = `Why I Switched To AG1 🌿`
- `{date_string}` = `March 14, 2026 at 6:42 AM`
- `{checklist_items}` = 10 items: `Less time meal-prepping ⏱️🥗`, `No more 12-pill morning stack 💊→🌱`, `Travel-friendly sachets ✈️🍃`, `Easier to actually drink 💚`, `Backed by clinical research 🔬`, `Endorsed by people I trust 👥`, `One scoop, one minute ⏲️`, `Berry flavor I don't gag on 🫐`, `Fewer "did I take my vitamins?" thoughts 🧠`, `More energy by 10am ⚡`

**Model notes:**
- **gpt-image-2:** clean. Renders SF Pro feel + emoji in checklist items reliably. Preferred backend for this template.
- **nano-banana-pro:** mixed. Header chrome (orange "Notes" chevron, toolbar icons) sometimes drifts; emoji rendering inside list items is less faithful. Use only if gpt-image-2 unavailable.

---

## T2 — Editorial article hero

**When to use:** credibility-led ads — "[respected publication] covers brand X." High-trust audiences, science-backed products. The publication logo functions as a third-party endorsement.

**Aspect ratio:** `1:1` (Meta feed standard)

**Reference image:** clean product hero (for the inset product shot in the photo block)

**Variables:**
- `{publication}` — publication wordmark (`FORBES`, `WIRED`, `Vogue`, `The Wall Street Journal`)
- `{headline}` — bold editorial headline, 8-15 words, declarative
- `{subcopy}` — 1-2 sentence editorial sub-copy expanding the headline
- `{photo_subject_description}` — what's shown in the bottom 55% (e.g. `fit person in athletic wear holding clear AG1 shaker, AG1 pouch + canister + sachets in foreground`)
- `{tagline}` — short brand promise on the bottom green band (≤4 words, e.g. `Greens, simplified.`)
- `{band_color}` — brand-color hex for the bottom band (e.g. `#1A4731`)

**Template prompt:**
```
1:1 static ad creative, 1080x1080, edge-to-edge — an editorial / publication-style ad image. Standalone, ready to upload as a Meta ad creative. White inner background.

Top-left: "{publication}" wordmark in chunky bold black serif on a small white box (the publication's logo, treated as a credibility stamp).

Headline below the logo, large bold black sans-serif tight tracking: "{headline}"

Sub-copy below the headline, regular weight black sans-serif: "{subcopy}"

Hero photograph occupies the bottom ~55% of the image: {photo_subject_description}. Premium-wellness product photography, soft natural light.

Across the very bottom of the image, an inset {band_color} band about 12% tall, containing white sans-serif headline "{tagline}" left-aligned, with a small white "Learn more >" pill on the right edge.

The composition is the standalone ad creative — editorial layout that reads as a publication-co-signed brand piece. No social platform UI of any kind.
```

**Example fill** (AG1):
- `{publication}` = `FORBES`
- `{headline}` = `How AG1 Became the Greens Powder Doctors Actually Recommend`
- `{subcopy}` = `Most multivitamins fail bioavailability tests. The brand fronted by Dr. Andrew Huberman built theirs around what your body can actually absorb.`
- `{tagline}` = `Greens, simplified.`
- `{band_color}` = `~#1A4731`

**Model notes:**
- **gpt-image-2:** clean. Publication wordmark legibility is strong; subhead reads at small size.
- **nano-banana-pro:** clean for the photograph block; weaker on the subhead text legibility at 1:1 — consider scaling subhead text up or shipping at 2:3.

---

## T3 — Story tweet+UGC composite

**When to use:** influencer / authority endorsements paired with UGC-style customer footage. Story-format placements (Reels/Stories), high social-proof angle.

**Aspect ratio:** `9:16` (Stories / Reels)

**Reference image:** product hero (for the shaker/product visible in the UGC photo)

**Variables:**
- `{authority_name}` — full name of the quoted authority (a doctor, scientist, athlete, founder — someone with category credibility)
- `{authority_handle}` — Twitter/X handle of the authority
- `{authority_face_description}` — 1-line face description for the small profile photo
- `{tweet_body}` — multi-line tweet text including the value-prop bullets with emojis
- `{ugc_subject}` — what the UGC photo shows (e.g. `fit woman in workout clothes mid-laugh holding an AG1 shaker bottle`)
- `{ugc_overlay_text}` — the black-rectangle text label across the UGC photo (e.g. `Watch this BEFORE / you skip your greens 🌿`)
- `{cursive_line}` — italic teaser line above the LEARN MORE (e.g. `75+ ingredients in one daily scoop...`)

**Template prompt:**
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge. Standalone — this image gets uploaded directly as the Story ad asset.

Background: soft cream / warm grey gradient ~#F2EEE6, full bleed.

Upper-mid composition: a screenshot-style Twitter/X post card, white rounded-corner card with thin shadow, occupying roughly 55-60% of the width on the left side, vertically positioned in the upper third:
- Top of card: small round profile photo of {authority_face_description}, "{authority_name}" in bold black + a small blue-check verified mark, "{authority_handle}" in grey beneath.
- Tweet text in black sans-serif:
"{tweet_body}"

To the right of the tweet card, slightly overlapping its right edge: a vertical 9:16-cropped photo of {ugc_subject}, soft window-light morning kitchen background. Across the lower-mid of the photo, a black rounded-rectangle overlay text label: "{ugc_overlay_text}" in white sans-serif.

Below the tweet+photo composite, in the lower third of the image:
- A faint cursive italic line in black: "{cursive_line}" then "more" in grey-blue underline.
- Below that, centered, in cursive blue script: "🔗 LEARN MORE" — a link-chain icon then "LEARN MORE" in caps.

The composition is the static Story ad creative ONLY. No iOS device chrome, no Story progress bars, no story header, no swipe-up arrows.
```

**Model notes:**
- **gpt-image-2:** clean for the tweet card text + handle. Strong here.
- **nano-banana-pro:** mixed — the UGC photo block looks great, but tweet text legibility drops. Consider hybrid: nano-banana to generate UGC photo asset separately, then composite via gpt-image-2 for final assembly.

---

## T4 — "Fake Google search" mosaic

**When to use:** "as the internet says..." angle. Implicit social proof from search results aesthetic + media logos. Wellness, nutrition, beauty, supplement categories where consumers actively Google solutions.

**Aspect ratio:** `9:16`

**Reference image:** clean product hero with multiple SKUs visible (the 2×2 grid uses 4 product variations)

**Variables:**
- `{search_query}` — the query in the search bar (e.g. `The BEST greens powder for energy and gut health`)
- `{grid_tile_descriptions[]}` — 4 product-photo descriptions, one per tile, all sharing a soft tonal background (e.g. cream/sage)
- `{publication_logos[]}` — 4 publication wordmarks for the bottom row (e.g. `FORBES`, `Vogue`, `Men's Health`, `The Wall Street Journal`)
- `{accent_color_family}` — the soft tonal background for the grid (e.g. `cream-to-sage`, `pink-to-lavender`, `cream-to-amber`)

**Template prompt:**
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge. A "fake Google search results" aesthetic rendered as a standalone upload-ready image. White inner background fading to soft {accent_color_family} at the bottom 30%.

Top of the image (~6% height): a thin top app row — a small grey hamburger-menu icon on the left; centered, the multicolor "Google" wordmark (capital G blue, o red, o yellow, g blue, l green, e red) in the standard Google Sans typeface; on the right, a small color microphone icon.

Below that: a rounded-pill grey search bar with a magnifier icon on the left and the text "{search_query}" in standard sans-serif. On the right inside the pill, a small Google Lens icon (multicolor camera/diamond shape).

Below the search bar: a horizontal tab row "All  Videos  Images  News  Maps  Books" with "All" underlined in faint blue, others in muted grey. Hairline divider beneath.

Main area: a 2x2 grid of square image search results with subtle rounded corners and small gaps between them. All four tiles share a soft {accent_color_family} background:
- Top-left: {grid_tile_descriptions[0]}
- Top-right: {grid_tile_descriptions[1]}
- Bottom-left: {grid_tile_descriptions[2]}
- Bottom-right: {grid_tile_descriptions[3]}

Below the grid, soft {accent_color_family} area at the bottom: in small spaced caps "AS SEEN ON" in muted grey, then below a horizontal row of four publication wordmarks in classic typefaces: {publication_logos joined with comma}.

The composition reads as a believable "Google search results page" rendered as a standalone static ad creative. No iOS device chrome.
```

**Model notes:**
- **gpt-image-2:** clean. Google wordmark colors stay faithful; publication wordmarks crisp.
- **nano-banana-pro:** publication wordmarks drift — letters get re-spaced. Pass each publication as a `--image-ref` if pixel-perfect logo accuracy matters.

---

## T5 — Comparison table (light)

**When to use:** clinical/feature-led brand differentiation against a generic category competitor. Best for products with clear feature-superiority claims (clinical research, certifications, ingredient counts, sugar content, etc.).

**Aspect ratio:** `2:3` (Meta tall feed)

**Reference image:** product hero showing the brand's primary SKU(s)

**Variables:**
- `{brand.name}` — the wordmark text in the header
- `{brand.product_image_description}` — what the brand's product looks like (1-line)
- `{competitor_category}` — what the brand is being compared against (e.g. `Your Daily Multivitamin`, `Generic Pre-Workout`)
- `{competitor_image_description}` — generic stand-in product (1-line, deliberately dull/unbranded)
- `{brand.color_primary}` — header text color hex (deep brand color)
- `{row_accent_color}` — soft tint of the alternating row color (e.g. `~#E8F0E5` sage for green brands, `~#E5F0F8` for blue)
- `{rows[]}` — 6 rows of `{label, sublabel?, brand_value, competitor_value}` where values are `green ✓`, `red ✗`, or text (numbers, ranges)

**Template prompt:**
```
2:3 portrait static ad creative, 1080x1620 — a clean, edge-to-edge comparison-table ad image. Standalone, ready to upload as a Meta ad creative. White background.

Header section (top ~22% of the image):
- Left side: bold {brand.color_primary} sans-serif headline in two stacked lines: "{brand.name} vs. {competitor_category}"
- Right side, on the same vertical band as the headline: two product photos in a row — {brand.product_image_description} on the left, {competitor_image_description} on the right.
- Hairline thin grey divider beneath the header.

Comparison table (bottom ~78% of the image): six rows, each spanning the full width, with alternating row backgrounds — {row_accent_color} for odd rows and white for even rows. Each row has three columns: label (left, ~50% width), {brand.name} column (~25%), and competitor column (~25%).

{rows_rendered_with_label_brand_competitor}

Typography is clean modern sans-serif throughout. Iconography is consistent — same green-circle ✓ and red-circle ✗ across all check rows.

This is the standalone ad creative — only the comparison table and product header. No surrounding social platform UI.
```

**Model notes:**
- **gpt-image-2:** clean. Strong text legibility in table rows, consistent ✓/✗ glyph rendering.
- **nano-banana-pro:** clean structurally but the small row labels can lose sharpness at 2:3. Consider shipping at 1:1 with fewer rows if using nano-banana.

---

## T6 — Comparison table (dark, hooky)

**When to use:** stop-the-scroll dark-mode creative. More provocative tone than T5 — leads with "this RUINS X" hook. Strong for SaaS/info-product/supplement brands willing to be confrontational with the category.

**Aspect ratio:** `2:3`

**Reference image:** product hero (used for the right-side icon in the VS row)

**Variables:**
- `{hook_line_1}` — top line, white, large (e.g. `This RUINS`)
- `{hook_line_2}` — bottom line, white with one word in bright accent green (e.g. `Your {{Greens}} Powder` where the word in `{{}}` is colored)
- `{competitor_label}` — short caption under the left "VS" tile (e.g. `Generic Greens`, `Your Old Pre-Workout`)
- `{brand.name}` — the wordmark on the right tile
- `{brand.color_primary}` — the green/accent color used for highlights and the brand-column outline
- `{table_columns}` — three: `Ingredient` / `{competitor_label}` / `{brand.name}` (or analogous metric column names)
- `{table_rows[]}` — 5 rows of `{metric_label, competitor_value, brand_value}` — brand value rendered in accent green

**Template prompt:**
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a dark-mode comparison ad image. Standalone, upload-ready as a Meta ad creative. Near-black background ~#0A1A12 with a subtle radial deep-{brand.color_primary} glow at the center.

Tiny green "+" cross marks in the four corners of the image (decorative tick marks).

Top text in chunky white sans-serif (large, ~80pt feel), stacked across two lines centered horizontally: "{hook_line_1}" on line 1, "{hook_line_2}" on line 2 — the word(s) marked with double-braces in {hook_line_2} are colored bright vivid green ~#3FCB7E, the rest white.

Centered below the headline, a row of three small rounded-square icons:
- Left tile: black background with a stylized white {competitor_visual} graphic on it, captioned with small white text "{competitor_label}" beneath.
- Middle: a small angled bright-green "VS" badge in a parallelogram shape.
- Right tile: {brand.color_primary} background with white "{brand.name}" wordmark stamped boldly.

Below the icons, a dark comparison table with thin light-grey grid lines:
- Header row in regular grey caps: {table_columns[0]} | {table_columns[1]} | {table_columns[2]}
- The "{brand.name}" column is outlined / highlighted with a thin bright-green border framing it.
{table_rows_rendered}

Numbers in monospace IBM Plex Mono / Roboto Mono feel; labels in regular sans-serif.

The composition is the standalone dark-mode ad creative ONLY — no surrounding platform UI.
```

**Model notes:**
- **gpt-image-2:** clean. Strong on dark-mode UI, accent-color word highlighting, monospace numbers.
- **nano-banana-pro:** clean for the headline and "VS" tile row; small numbers in the table can blur. Reduce table to 4 rows for nano-banana.

---

## T7 — Sticky-note + product flatlay

**When to use:** tactile / UGC-aesthetic ads. Best for consumable products that can be physically scattered (gummies, sachets, capsules, sample packets). Works for "I tried this for N days" reviewer-voice angles.

**Aspect ratio:** `1:1`

**Reference image:** product photo showing the small / scatter-able product unit (sachet, gummy, packet)

**Variables:**
- `{handwritten_text_lines}` — 3-5 lines of bold all-caps text, marker-style. Should fit on a square sticky note. Personal/conversational voice.
- `{sticky_note_color}` — vivid post-it color (default `bright magenta-pink ~#E84F88`); could be neon yellow `#FCE96A`, lime `#B7E36B`, or orange `#F7931E`
- `{product_unit_description}` — what gets scattered around the note (e.g. `coral / orange-red AG1 travel sachets with white "AG1" wordmark`, `green sour gummy worms with sugar crystals`, `single-serve protein scoops`)
- `{powder_or_residue_hint}` — optional small detail to ground the product as real (e.g. `a few scattered green powder flecks near one of the open sachet ends`)

**Template prompt:**
```
Top-down 1:1 flatlay product photograph, 1080x1080, soft off-white seamless background. Center: a {sticky_note_color} square sticky note (3M Post-it style), slightly rotated counter-clockwise about 5 degrees, with hand-lettered black marker text in bold all-caps stacked over multiple lines: "{handwritten_text_lines}". Letters are hand-drawn with a chunky black permanent marker — slightly uneven baseline, irregular kerning, marker bleed at stroke edges, organic and imperfect.

Around all four sides of the sticky note, partially overlapping its edges in places: 8-12 individual {product_unit_description}. Scattered organically — some flat, some slightly tilted, some overlapping each other or the sticky-note edge.

Even diffuse soft overhead lighting, no harsh shadows. {powder_or_residue_hint}

Casual, organic, social-content aesthetic — feels homemade UGC, not over-styled.
```

**Example fill** (AG1):
- `{handwritten_text_lines}` = `I DRANK ONE / OF THESE EVERY / MORNING FOR / 30 DAYS`
- `{sticky_note_color}` = `bright magenta-pink ~#E84F88`
- `{product_unit_description}` = `AG1 travel sachets — small rectangular foil packets in warm coral / orange-red color, with white "AG1" wordmark visible on each, stamped boldly`
- `{powder_or_residue_hint}` = `A few scattered green powder flecks (a hint of spilled greens) on the background near one of the open sachet ends`

**Model notes:**
- **nano-banana-pro:** strong. Photorealism + marker text rendering is its strength. **Preferred backend.**
- **gpt-image-2:** clean but the flatlay can feel slightly stiff. Use if nano-banana unavailable.

---

## T8 — Handwritten whiteboard / posterboard comparison

**When to use:** UGC-aesthetic "real person made this" social proof. Strong for DTC, supplements, coaching/info-products. Especially effective in IG Reels-derived ads.

**Aspect ratio:** `2:3` (a tall held-up board needs vertical room — 1:1 clips the headline at the top)

**Reference image:** product hero (informs the brand color used for the "wins" column marker)

**Variables:**
- `{N}` — number of reasons (default 5)
- `{brand.name}` — wordmark for the LEFT (winning) column (e.g. `AG1`)
- `{competitor_label}` — what's being compared against (e.g. `Generic Multivitamins`, `Traditional Hiring`)
- `{brand.color_marker}` — color of the marker used on the brand side (e.g. `deep forest green`, `bright red`)
- `{brand_wins[]}` — N short bullet items, brand-side advantages
- `{competitor_cons[]}` — N short bullet items, competitor-side cons
- `{environment}` — outdoor patio / sunlit kitchen / bright office (the IRL setting in the soft background)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a real-world photograph of a hand-held whiteboard or foam posterboard with hand-written marker comparison content. Standalone ad creative, ready to upload as a Meta ad creative.

Composition: a single hand (visible from the wrist down at the bottom of the frame, slightly off-center, holding the bottom edge of the board) presents a white rectangular dry-erase whiteboard at a slight tilt. The board occupies roughly the central 70% of the frame — its top edge is at least 12% below the top of the canvas, and its bottom edge is at least 18% above the bottom of the canvas (where the hand and out-of-focus background are visible). The board is photographed in a soft-focus modern kitchen counter / bright open patio environment in the background, with bright natural daylight and shallow depth of field.

The board content is hand-written in chunky permanent marker, slightly imperfect lettering, mixed colors (deep forest green for the brand side, dim grey-black for the competitor side), with hand-drawn underlines for emphasis:

Top of board, large hand-lettered title centered (this title MUST be fully visible — its top must sit at least 8% below the canvas top, never clipped):
"5 Reasons Why"
(underlined twice with a hand-drawn line beneath)

Just below the title, in two columns separated by a hand-drawn ">" character:
LEFT column header (deep forest green marker, large, underlined twice): "AG1"
">" symbol in dim grey marker between the two
RIGHT column header (dim grey marker, large): "Generic Multivitamins"

Below the headers, two columns of bullet points separated by a vertical hand-drawn line:

LEFT column (deep forest green marker, bullets are filled circles or stars, plain words only — NO emoji, NO unicode symbols beyond bullet markers):
- Clinically Dosed
- 75+ Ingredients
- NSF Certified
- Travel Sachets
- One Scoop Daily

RIGHT column (dim grey marker, bullets are X marks or dashes, plain words only):
- Hidden Fillers
- 12-Pill Stack
- No Clinical Data
- Bulky Bottles
- Cheap Blends

Hand-lettering is organic and imperfect — slightly uneven baseline, varied stroke weight, occasional marker bleed. Letters look like a real person wrote them, not a font. The TITLE and column headers are fully visible inside the safe zone with comfortable padding.

Photography: bright natural daylight, soft shadows, casual UGC aesthetic — looks like a real screenshot from a Reels video where a creator is showing the board to camera.

No additional text, no overlays, no logos beyond what's hand-written on the board.
```

**Model notes:**
- **nano-banana-pro:** strong. Handheld board + handwritten marker is in its wheelhouse. **Preferred backend.**
- **gpt-image-2:** clean for the lettering, weaker on the held-board photograph realism. Acceptable fallback.

---

## T9 — Annotated product features (arrow callouts)

**When to use:** feature-rich product breakdowns. Best for products where each feature is a discrete selling point (watches, supplements, gadgets). Reads like a Goop / Apothékary product card.

**Aspect ratio:** `1:1`

**Reference image:** clean product hero (the central product is rendered faithfully from the ref)

**Variables:**
- `{testimonial_quote}` — short pull-quote at the top in italic serif (≤80 chars, in quotation marks)
- `{star_count}` — usually 5 (★★★★★)
- `{callouts[]}` — 4-6 feature labels, each with a positional hint (top-left, top-right, bottom-left, bottom-right, center-bottom). 1-3 word labels are best
- `{brand.name}` — wordmark to display at the bottom

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a clean product hero photograph with hand-drawn arrow annotations pointing to feature callouts. Standalone ad creative, ready to upload as a Meta ad creative. Soft cream / warm off-white background ~#F5F1EA.

Top of the image (~12% height): centered, a row of 5 small black filled stars (★★★★★), and immediately beneath in italic dark navy serif: "I haven't switched supplements in 4 years." in quotation marks (a short testimonial pull-quote, ≤80 chars).

Center of the image: a clean editorial product hero — a deep forest-green AG1 pouch with white "AG1" wordmark prominent, standing upright slightly tilted forward, with a clear shaker bottle of vibrant green liquid beside it. Subtle soft shadow beneath. The product occupies roughly 45-55% of the frame, centered.

Around the product, four to five hand-drawn thin black arrow lines (curved, lasso-like, slightly irregular as if drawn with a fine marker) sweep outward from specific spots on the product to feature-name callouts in clean black sans-serif:

- Top-left arrow → "75+ Ingredients" (bold sans, ~16pt)
- Top-right arrow → "NSF Certified for Sport"
- Bottom-left arrow → "Pre + Probiotics"
- Bottom-right arrow → "Adaptogens Included"
- Center-bottom arrow → "Clinically Dosed"

Each arrow originates near the relevant area of the product (e.g. label area for "75+ Ingredients", powder zone for "Pre + Probiotics") and curves out to the label text positioned in the white space around the product. Arrows are subtle — thin 1.5pt strokes, slight hand-drawn wobble, with small arrowhead at the callout end.

Bottom of the image (~10% height): the brand wordmark "AG1" rendered prominently in deep forest-green serif/sans-serif (matching the brand's actual wordmark, in a medium weight) centered.

Editorial wellness product photography aesthetic — soft daylight, neutral palette, premium and minimal. The composition feels like a Goop / Aesop / Apothékary product breakdown card.

No additional text, no logos beyond the brand wordmark and what's annotated.
```

**Model notes:**
- **both: clean.** Arrow rendering is fine on both models; product hero faithfulness depends on the `--image-ref` you pass.

---

## T10 — Letter board sign + product

**When to use:** UGC / influencer-flatlay aesthetic. Tactile, social-content feel. Best for consumer brands that fit a "morning routine" or "daily ritual" lifestyle frame.

**Aspect ratio:** `1:1`

**Reference image:** product hero (used for the product placed beside the letter board)

**Variables:**
- `{letter_board_text}` — 2-3 short stacked lines, all caps, fits a small letter board (e.g. `ONE SCOOP / REPLACED MY / 12-PILL STACK`)
- `{environment}` — sunlit kitchen / bedside / desk corner (the IRL setting)
- `{board_frame_color}` — wood color for the letter board frame (default `warm honey oak`)
- `{product_arrangement}` — what's arranged beside the board (e.g. `AG1 pouch upright + clear shaker bottle in front + small wooden scoop + 2 travel sachets casually placed`)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a real-world product flatlay-style photograph featuring a physical felt letter board with hand-arranged removable white plastic letters, displayed alongside the AG1 product. Standalone ad creative, ready to upload.

Setting: a sun-washed modern kitchen counter with light wood surface and a white-painted brick or shiplap wall in the soft-blurred background. Bright morning natural light from the side, soft shadows.

Centerpiece: a vintage-style felt letter board with a wooden frame (warm honey oak), classic black-felt grid background, holding small white plastic letters arranged in three centered lines:

ONE SCOOP
REPLACED MY
12-PILL STACK

The letters are slightly imperfect — some not perfectly aligned, a couple letters tilted a few degrees, conveying a hand-arranged feel. The board is photographed at a slight 3/4 angle (not perfectly head-on), leaning gently against something out-of-frame.

Beside the letter board, slightly to the right and overlapping its lower edge: the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark prominent, standing upright, with a clear shaker bottle of vibrant green liquid in front of it. A small AG1 wooden scoop and one or two coral / orange-red AG1 travel sachets rest casually on the counter near the base of the pouch.

Photography style: lifestyle product photography, premium-wellness aesthetic, soft natural light, shallow depth of field on the background. Looks like a real influencer flatlay shot for an Instagram Reel reveal.

The composition reads as: the letter board makes the value-prop statement, the product visually backs it up. No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **nano-banana-pro:** strong. Letter board with white plastic letters renders cleanly. **Preferred backend.**
- **gpt-image-2:** clean but letter spacing on the board can drift.

---

## T11 — Fake comment thread (user → brand)

**When to use:** social proof with response — show a real customer asking, brand giving a clean call-to-action answer. Strong for higher-consideration purchases where buyers want to see other buyers ask.

**Aspect ratio:** `1:1`

**Reference image:** product hero (for the product photo in the lower half)

**Variables:**
- `{user_name}` — first name + last initial (e.g. `Sarah K.`)
- `{user_avatar_description}` — 1-line for the small profile photo (e.g. `smiling brunette woman`)
- `{user_question}` — the prospect's question (≤80 chars)
- `{brand.name}` — brand wordmark
- `{brand.avatar_description}` — what the brand's circular avatar looks like
- `{brand_response}` — multi-line answer with a 3-step numbered list (avoid emoji — see "known issue")

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake Facebook-style comment thread between a user and the brand, paired with a product photograph beneath. Standalone ad creative, ready to upload. Light grey background ~#F0F2F5.

The image contains EXACTLY TWO comment bubbles total — no more, no fewer. Do not invent a third comment, header, or top-level post.

Upper half (~50% of the image): a vertical chain of EXACTLY TWO comment bubbles, both styled like Facebook comment-bubble UI. Each comment is a rounded grey speech-bubble (~#E4E6EB) with the commenter's name in bold black above the bubble text, a small circular profile avatar to the LEFT of the bubble, and a small "3h    Like    Reply    14 likes" engagement metadata row beneath each bubble in muted grey text. A faint thin grey vertical line connects the bottom of the first bubble to the top of the second bubble (the FB comment-thread connector).

COMMENT 1 (USER, top of the upper half, left-aligned):
- Avatar: small circular photo of a smiling brunette woman (~36px diameter)
- Name above bubble: "Sarah K." in bold black sans-serif
- Bubble text (plain text only, NO emoji): "Has anyone actually tried AG1? Worth the price?"
- Beneath the bubble: "3h    Like    Reply    14 likes" in small grey

COMMENT 2 (BRAND REPLY, slightly indented to the right, connector line from comment 1):
- Avatar: small circular tile, deep forest-green ~#1A4731 background with white "AG1" wordmark in chunky bold sans-serif
- Name above bubble: "AG1" in bold black + a small blue circular verified-checkmark badge beside the name
- Bubble text (plain text only, NO emoji, NO unicode symbols):
  "Hi Sarah! You are 3 steps away from finding out:

  1. Pick your starter pack
  2. Try AG1 risk-free for 30 days
  3. Wake up actually energized

  Most people feel a difference within a week."
- Beneath the bubble: "2h    Like    Reply    47 likes" in small grey

Lower half (~50% of the image): a clean product photograph of the AG1 product set on a soft warm-cream background. The product shot is FRAMED IN FULL — the AG1 pouch (deep forest-green with white "AG1" wordmark) is fully visible from cap to base, alongside a clear shaker bottle of vibrant green liquid (also fully framed) and a small fan of three coral / orange-red AG1 travel sachets. The bottom edge of the product photograph leaves comfortable safe-zone padding from the canvas bottom (at least 8% margin). Editorial product photography, soft natural light.

The composition feels like a real Facebook comment exchange screenshot, but rendered as a standalone static ad creative.

No additional UI: no FB header, no Sponsored badge, no engagement bar, no comment input, no platform tab navigation. EXACTLY two comments, no third comment, no phantom bubble at the top of the image.
```

**Note:** the script's `GLYPH_SAFETY_SUFFIX` (always on) handles both the "exactly N comments" constraint and the "no emoji in body text" rule globally — your prompt only needs to describe the desired content.

**Model notes:**
- **gpt-image-2:** clean. Comment bubble UI mimicry is its strength. **Preferred backend.**
- **nano-banana-pro:** weaker on small body text inside bubbles. If using nano-banana, keep bubble text to 1-2 lines max.

---

## T12 — Fake ChatGPT conversation

**When to use:** "AI agrees" social proof. Trending pattern in 2026. Effective when the brand naturally emerges as the answer to a category question — works best for category leaders, less for unknown brands.

**Aspect ratio:** `1:1`

**Reference image:** brand product (helps the green CTA bar pull from brand color)

**Variables:**
- `{user_question}` — the question typed to ChatGPT (1 sentence, no longer than 80 chars)
- `{user_avatar_description}` — small profile photo description
- `{chatgpt_response_short}` — KEEP THIS UNDER 4 short lines. Dense small text garbles — see known issue. Use 3-4 numbered points max, each 1 line.
- `{cta_text}` — green-bar CTA (e.g. `Try AG1 risk-free for 30 days`)
- `{cta_color}` — brand-color hex for the bottom CTA bar

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake ChatGPT-style conversation screenshot rendered as a standalone ad creative. Pure dark grey background ~#343541 (the ChatGPT dark mode chat backdrop).

Render text density LOW. Body text is at LARGE size — the user message and ChatGPT response together fill the canvas vertically without crowding. Every word must be legible and crisp.

Top section (~22% of the canvas height): the USER message row.
- Left: a small rounded-square user avatar (a smiling person profile photo, ~52px square).
- Right of the avatar: in white SF Pro / Inter sans-serif regular weight at LARGE size (~26pt feel): "What is the easiest way to cover all my daily nutrition?"

Subtle horizontal divider line in faint grey.

Middle section (~58% of the canvas height): the CHATGPT response row.
- Left: the ChatGPT logo — a small green rounded-square tile (~52px) with a stylized white spiral / hex-flower glyph centered inside it.
- Right of the logo: in white SF Pro sans-serif at LARGE size (~24pt feel), the response is INTENTIONALLY SHORT — exactly three lines, each a single short sentence. NO emoji, NO special unicode characters, just plain words. Generous line spacing between the three numbered points. The response text reads exactly:

"Look for a comprehensive greens powder that covers your daily basics in one scoop. Three things matter most:

1. Clinically dosed ingredients
2. Third-party tested for purity
3. Travel-friendly format

AG1 checks all three."

Top-right corner of the ChatGPT response, two small thin grey icons: a thumbs-up outline and a thumbs-down outline.

Bottom section (~12% of the canvas height): a horizontal CTA bar in deep AG1 forest green ~#1A4731 spanning the full canvas width, containing white sans-serif text "Try AG1 risk-free for 30 days" left-aligned, with a small white right-arrow ">" on the right edge.

The composition is the standalone static ad creative ONLY — no surrounding browser or app chrome (no URL bar, no tabs, no ChatGPT sidebar, no input box at the bottom). Just the conversation snippet styled like a ChatGPT exchange, with the green CTA bar grafted at the bottom.

CRITICAL: keep text density LOW. The response is intentionally three short numbered lines plus one closer sentence, rendered at large readable size. Do NOT pack the response with extra paragraphs or details — sparse, clean, fully legible.
```

**Note:** keep the ChatGPT response sparse — 3 short numbered lines + 1 closer line, rendered at LARGE text size. Dense / small body text will garble even with the global `GLYPH_SAFETY_SUFFIX`. Less is more.

**Model notes:**
- **gpt-image-2:** clean. Mimics its own ancestor's UI faithfully — ChatGPT logo + response card render reliably.
- **nano-banana-pro:** mixed — ChatGPT logo can drift, response body text legibility drops. **gpt-image-2 strongly preferred for this template.**

---

## T13 — Before/After two-panel split

**When to use:** transformation narratives. Universal pattern — works for fitness, supplements, productivity tools, hair/skin, anywhere a "messy before, clean after" makes the pitch instantly.

**Aspect ratio:** `1:1`

**Reference image:** product hero (for the "after" panel)

**Variables:**
- `{before_label}` — usually `HOW IT STARTED` (other variants: `BEFORE`, `WITHOUT {brand.name}`)
- `{after_label}` — usually `HOW IT'S GOING` (other variants: `AFTER`, `WITH {brand.name}`)
- `{before_scene_description}` — chaotic / messy / mid-pain-point flatlay
- `{after_scene_description}` — clean / styled / product-led flatlay using the brand's product
- `{before_tone}` — desaturated / muted background hex (e.g. grey-beige)
- `{after_tone}` — warm / bright background hex (e.g. cream)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a vertical split-screen "before/after" transformation comparison. Standalone ad creative, ready to upload as a Meta ad creative.

The image is divided EXACTLY down the center by a hairline 2px white vertical divider into two equal-width halves. No frame around either side.

LEFT HALF (50% width) — "HOW IT STARTED":
- Background tone: muted desaturated grey-beige ~#D6D2CC.
- Top of half, centered, in bold black uppercase sans-serif (~28pt, modern geometric — Söhne / GT America feel): "HOW IT STARTED"
- Centered below the headline (the bottom 75% of the half): a chaotic flat-lay photograph of a cluttered bathroom counter or kitchen counter showing a dozen+ generic supplement bottles of varying sizes, brands, and colors all crammed together — multivitamin bottles, fish-oil tubs, probiotic capsules, vitamin D pills, magnesium powder, etc. Some bottles tipped over, some with caps off, slightly chaotic and overwhelming. Dim natural light, slight desaturation. Conveys the "12-pill stack" pain.

RIGHT HALF (50% width) — "HOW IT'S GOING":
- Background tone: warm bright cream ~#F5F1EA.
- Top of half, centered, in bold black uppercase sans-serif (same size/font as left): "HOW IT'S GOING"
- Centered below the headline (the bottom 75% of the half): a clean, beautifully-styled flat-lay photograph of a single deep forest-green AG1 pouch (white "AG1" wordmark prominent), a clear shaker bottle of vibrant green liquid, and three coral / orange-red AG1 travel sachets neatly fanned out. Bright natural daylight, premium wellness aesthetic, calm and minimal. The contrast with the left side's chaos is the entire visual joke.

Both halves use IDENTICAL camera angle (top-down 90° flatlay) and identical headline placement and size, so the eye reads the difference as the contrast between the two stages.

No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **both: clean.** Tone contrast renders cleanly on both. nano-banana edges ahead for photoreal before-after; gpt-image-2 edges ahead if both halves contain rendered text.

---

## T14 — Fake Slack team conversation

**When to use:** B2B / SaaS / agency products where the buyer's "moment of consideration" happens in a work context. Also works for wellness brands with a "team / colleague recommendation" angle.

**Aspect ratio:** `1:1`

**Reference image:** product hero (used for color cues in the green CTA pill)

**Variables:**
- `{channel_name}` — Slack channel (e.g. `#wellness-team`, `#growth`, `#founders`)
- `{messages[]}` — 3 messages, each `{author_name, role, time, message_text}`. Avoid emoji in message text (see known issue)
- `{cta_text}` — pill button text (e.g. `TRY AG1 →`)
- `{cta_color}` — brand-color hex for the CTA pill

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake Slack-style team conversation rendered as a standalone ad creative. EXACTLY THREE messages, no more, no fewer.

Top section (~10% height): a Slack-style window header bar — deep aubergine / dark plum background ~#3F0E40 spanning the full canvas width. Left edge: three small rounded dots (red / yellow / green window controls). To the right of the dots, a small back arrow + forward arrow + clock-history icon, then a centered rounded grey search-bar pill containing a small magnifier icon and the word "Search". Far right: a small cartoon profile avatar (~24px).

Below the header, a thin grey divider, then the main chat content area (white background ~#FFFFFF, ~90% of the canvas):

Channel header row: in bold black sans-serif (~22pt), left-aligned, with comfortable padding from the canvas left edge: "#wellness-team" with a small dropdown chevron beside it. Far right (with safe-zone padding from canvas right edge): a small "12" face-pile of three tiny avatar circles + member count.

Below the channel header, a vertical thread of EXACTLY THREE messages. Each message has the same row structure: avatar on left, message content on right. Plain text only — NO emoji, NO unicode symbols, NO special characters in the message bodies.

MESSAGE 1:
- Avatar (left, ~44px rounded square): illustrated cartoon figure of a smiling brunette woman.
- Right of avatar: bold black "Sarah (Marketing)" + small grey "10:42 AM" beside it.
- Below the name row: regular black sans-serif text in a single paragraph: "Anyone else trying that AG1 stuff? Day 14 and I have not reached for coffee once."

MESSAGE 2:
- Avatar (left): illustrated cartoon woman with red hair.
- Right of avatar: bold black "Maria (Founder)" + small grey "10:43 AM".
- Below: regular black sans-serif: "Wait, AG1?"

MESSAGE 3:
- Avatar (left): same brunette cartoon as Message 1 (Sarah).
- Right of avatar: bold black "Sarah (Marketing)" + small grey "10:45 AM".
- Below: regular black sans-serif: "Yeah, picked it up after Huberman kept mentioning it. One scoop covers the whole day. Travel sachets are clutch."

Below the third message, with comfortable vertical spacing, centered horizontally and well within the safe zone (at least 10% padding from the canvas bottom): a large pill-shaped CTA button with rounded corners, deep AG1 forest green fill (~#1A4731), containing bold WHITE uppercase sans-serif text "TRY AG1" with a small white right-arrow ">" beside it.

The composition reads as a believable Slack team-chat snapshot — but rendered as a standalone static ad creative. No additional UI: no Slack sidebar (no workspace switcher, no channel list, no DM list), no message-input box at the bottom of the chat, no app navigation, no iOS or desktop OS chrome.

EXACTLY three messages — do not invent a fourth. Plain text only — no emoji or special glyphs in the message bodies.
```

**Note:** the script's global `GLYPH_SAFETY_SUFFIX` strips emoji from message bodies and enforces the "exactly N messages" count — you don't need to repeat those constraints in the prompt.

**Model notes:**
- **gpt-image-2:** clean. Slack UI mimicry is strong. **Preferred backend.**
- **nano-banana-pro:** weaker on the channel header + message body text. Use only if gpt-image-2 unavailable.

---

## T15 — Ingredient list + collage (left/right split)

**When to use:** ingredient-forward consumables — supplements, food, drinks, beauty. Visual proof that the labeled ingredients are real / present / sourced.

**Aspect ratio:** `1:1`

**Reference image:** brand product hero (the actual product image is reproduced on the right)

**Variables:**
- `{ingredients[]}` — 4-6 ingredient names, plain text, premium typography (no emoji needed)
- `{ingredient_visuals[]}` — for each ingredient, a 1-line visual description for the right-side collage tile (e.g. `extreme close-up of vibrant green spirulina powder texture`)
- `{brand.product_description}` — how the product looks (pulled from the reference image)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a clean ingredient-breakdown ad layout. Standalone, ready to upload as a Meta ad creative. Soft cream / warm off-white background ~#F5F1EA.

LEFT HALF (~55% width): a vertical list of five ingredient names, generously spaced, each on its own line, with a thin hairline grey horizontal divider beneath each. Typography: clean black sans-serif (Inter / Söhne feel), regular weight, ~28-32pt size, left-aligned. The list reads top-to-bottom:

Spirulina
———————————
Ashwagandha
———————————
Probiotic Blend
———————————
Vitamin C Complex
———————————
75+ Total Ingredients

(After each ingredient name, the thin grey hairline runs to the right edge of the left half.)

RIGHT HALF (~45% width): a vertical photo collage that visually represents each ingredient, rendered as a tall stack of small rectangular product photographs flowing into the AG1 product itself. Stack reads top to bottom:
- Top tile: extreme close-up of vibrant green spirulina powder texture
- Tile 2: a hand holding a small bunch of dried ashwagandha root with rough fibrous texture
- Tile 3: out-of-focus probiotic capsules / agar petri dish in soft warm light
- Tile 4: cross-section of a sliced citrus / orange wedge with bright pulp visible

These four small ingredient tiles are stacked vertically inside a tall vertical "window" cut-out shape on the right.

Just to the right of (or overlapping the bottom of) the collage stack: the actual AG1 product — a tall deep forest-green AG1 pouch with white "AG1" wordmark prominently visible, standing upright, occupying the bottom-right portion of the frame. The pouch slightly overlaps the ingredient-stack column, creating depth. Soft natural daylight, premium product photography aesthetic.

The composition reads as: list of what's inside on the left, visual proof of those ingredients flowing into the product on the right.

No additional text, no logos beyond the AG1 wordmark on the pouch.
```

**Model notes:**
- **nano-banana-pro:** strong on the photo-collage half (ingredient texture rendering). **Preferred backend.**
- **gpt-image-2:** clean for the typography list; photo-collage tiles can feel slightly composited.

---

## T17 — Stacked-bar with vs without comparison

**When to use:** data-viz framing of the brand's value prop. Reads as objective even though it's editorial. Strong for productivity, wellness, finance, time-saving brands where the "without" side has many discrete failure modes.

**Aspect ratio:** `2:3`

**Reference image:** product hero (informs brand color for the winning bar)

**Variables:**
- `{header_label}` — top label both columns share (e.g. `Time spent`, `Money spent`, `Brain space`)
- `{winning_bar_color}` — soft tone for the brand's solid bar (e.g. mint-sage `#D4E8D4`)
- `{winning_bar_text}` — short phrase centered in the brand bar (e.g. `feeling great`, `actually working`)
- `{losing_segments[]}` — EXACTLY 5 short pain-point labels (top to bottom), each on a different soft pastel. Be explicit: "five segments only, no more."
- `{brand.name}` and `{competitor_label}` — column footers

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a clean data-visualization-style "with brand vs without brand" stacked-bar comparison. Standalone ad creative, ready to upload. Pure white background.

The image is split into TWO equal-width columns side by side, with a thin grey hairline vertical divider between them.

EACH column has the EXACT same outer structure: header label "Time spent" at top, single tall vertical bar in the middle, footer label at bottom. Bars in both columns are EXACTLY the same total height.

LEFT COLUMN — winning side:
- Top label: "Time spent" in regular black sans-serif (~22pt)
- Single tall rectangular bar (filling ~75% of column height), filled SOLID with one soft mint-sage green color (~#D4E8D4). NO segments, NO divisions inside this bar — it is one solid rectangle. Centered vertically inside the bar, in dark forest-green sans-serif: "feeling great"
- Bottom label: "with AG1" in regular black sans-serif

RIGHT COLUMN — losing side:
- Top label: "Time spent" in regular black sans-serif (same size)
- Single tall rectangular bar (same height/width as left), divided into EXACTLY FIVE horizontal segments stacked top-to-bottom. The bar must contain FIVE segments, no more, no fewer — do not add a sixth segment.
- The five segments are equal height, each labeled with a short pain-point text centered inside, in dark text. From TOP to BOTTOM:
  1. SOFT BLUE ~#D9E5F2 — "worrying about energy"
  2. SOFT GREEN ~#D4E8D4 — "scrolling for solutions"
  3. SOFT YELLOW ~#F2EBC9 — "buying random supplements"
  4. SOFT PEACH ~#F2D9C9 — "questioning your routine"
  5. SOFT PINK ~#F2D4D9 — "actually feeling good"
- Bottom label: "without AG1" in regular black sans-serif

Five segments only on the right bar. Solid color block on the left bar. Both columns within the central 84% safe zone with comfortable padding from canvas edges. Headers and footers fully visible.

Modern minimal data-viz aesthetic — clean, Apple-Health-inspired. No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **gpt-image-2:** clean. Geometric shapes + text labels render reliably.
- **nano-banana-pro:** clean for the bars; small segment labels can blur. Bump pastel tones higher-contrast if using nano-banana.

**Documented limit — segment heights are drawn approximately.** The bars are sized by eye,
not computed from a value, so the stack reads as a proportion rather than measuring one.
Fine here, because this template's claim is "many things versus one thing" and not a
figure. If a run needs the segments to be numerically true, composite the chart instead of
generating it — same limit as T38, measured there at ~9% overshoot.

---

## T18 — Flowchart "old way" vs "new way"

**When to use:** workflow / habit transformation. Best when the brand replaces a complicated process with a simple one. Strong for SaaS, supplements, productivity, info-products.

**Aspect ratio:** `1:1`

**Reference image:** product hero (drives the brand color in the new-way pill + box borders)

**Variables:**
- `{old_way_steps[]}` — 5 short pain-point steps for the old-way column (each ≤4 words). Last step is a "give up" / failure state.
- `{new_way_steps[]}` — 3 short steps for the new-way column (≤6 words each). Ends with the brand's outcome.
- `{closing_outcome}` — short bold tagline beneath the new-way chain (e.g. `Calm Consistency`, `Just one step`)
- `{brand.color_primary}` — for the new-way header pill + box borders

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a side-by-side hand-drawn-feel flowchart comparing "The Old Way" to "The AG1 Way" as two contrasting workflows. Standalone ad creative, ready to upload. Cream / off-white background ~#F5F1EA.

LEFT HALF (~48% width) — "The Old Way":
- Header: a black rounded-rectangle pill at the top with white sans-serif text "The Old Way"
- Below it: a vertical chain of 5 small rectangular outlined boxes connected by thin black arrow lines pointing down, each box containing a short pain-point label in plain black sans-serif:
  1. Buy 12 pills
  2. Forget half of them
  3. Bloat from synthetic fillers
  4. No noticeable energy
  5. Stop the routine
- The bottom box has a small skull / crossed-out icon next to it (or text "Give Up")
- The arrows are slightly wonky, hand-drawn-feel — gives "messy chaotic process" energy

RIGHT HALF (~48% width) — "The AG1 Way":
- Header: a deep AG1 forest-green ~#1A4731 rounded-rectangle pill at the top with white sans-serif text "The AG1 Way"
- Below it: a shorter vertical chain of just 3 rounded-rectangle boxes connected by clean smooth arrow lines pointing down, each in a soft sage / cream tone with darker green border, containing:
  1. One scoop of AG1 daily
  2. Cover all your bases (75+ ingredients)
  3. Actually feel the difference
- Below the chain: a small flourish / star icon, and bold dark forest-green text "Calm Consistency"
- The arrows here are clean and confident — gives "simple effective process" energy

Between the two halves, a thin vertical hairline grey divider runs top to bottom.

The flowchart has a hand-drawn / sketched feel (slight wobble in lines, irregular pen strokes) but stays clearly readable. All text labels are in plain black sans-serif inside their boxes — short phrases, no emoji.

No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **gpt-image-2:** clean. Diagrammatic layout + small step labels render reliably.
- **nano-banana-pro:** acceptable; the hand-drawn arrow feel between boxes is sometimes too clean. Add "wobbly, marker-drawn, imperfect line weight" to the prompt for nano-banana.

---

## T19 — Fake AirDrop dialog (with before/after)

**When to use:** stop-the-scroll iOS modal pattern. The AirDrop dialog is so familiar that users instinctively look at it. Pair with a before/after to deliver the value prop in one glance. Strong for transformation-led brands (apparel, fitness, supplements, beauty, finance).

**Aspect ratio:** `1:1`

**Reference image:** product hero (only used for color cues in the after photo)

**Variables:**
- `{prompt_question}` — the dialog's two-line subhead, ending with the brand cue (e.g. `Looking to feel like yourself again? Try AG1.`)
- `{before_subject_description}` — what the left photo shows (the "before" pain state)
- `{after_subject_description}` — what the right photo shows (the "after" branded state)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake Apple AirDrop dialog mockup floating on a soft blurred background. Standalone ad creative, ready to upload.

Background: soft blurred neutral grey-beige photographic background ~#C9C6C0 (the look of a hand-held phone background, slightly out of focus, with no recognizable elements). The blurred background fills the entire canvas.

Centered in the canvas, occupying the central 80% width and 90% height: a white rounded-corner rectangular dialog card with subtle shadow. Inside the card, top to bottom:

1. Top section (~18% of card height): centered title "AirDrop" in bold black SF Pro Display, large (~52pt feel). Beneath the title, in regular black SF Pro at smaller size, two short stacked lines, centered:
   "Looking to feel like yourself again?"
   "Try AG1."

2. Middle section (~62% of card height): a horizontal split-screen photo, two equal-width images side by side with a thin white vertical divider between them. LEFT: a photo of a tired, slumped man in his early 40s, wearing an oversized faded t-shirt, slouching at home in dim warm light, scrolling on his phone. RIGHT: a photo of the SAME man (same face, same age) but transformed — standing confidently outdoors in bright golden-hour light, fitter, smiling, wearing fitted athletic gear, holding an AG1 shaker bottle of vibrant green liquid, looking energized.

3. Bottom section (~20% of card height): a thin grey hairline divider across the card width, then two button areas split evenly with a thin vertical hairline between them. Left button: "Decline" in light blue (~#3B82F6) SF Pro regular weight. Right button: "Accept" in bold dark blue (~#1E3A8A) SF Pro Semibold.

The dialog card is clean and pixel-faithful to a real iOS AirDrop dialog. Comfortable safe-zone padding from canvas edges (~10% on all sides).

No additional text, no logos overlay, no iOS status bar / chrome around the dialog. Just the dialog card floating on the soft blurred background.
```

**Model notes:**
- **gpt-image-2:** clean. iOS dialog UI mimicry is strong. **Preferred backend.**
- **nano-banana-pro:** the buttons can drift in color/position; iOS-modal proportions slip. Use gpt-image-2 unless unavailable.

---

## T20 — IG Story Q&A sticker over lifestyle photo

**When to use:** UGC / influencer authority — feels like a real creator answering a real question. Pair with an aspirational lifestyle background to bake the brand into the lifestyle the user wants.

**Aspect ratio:** `9:16`

**Reference image:** product hero (helps the answer text reference the actual product accurately)

**Variables:**
- `{lifestyle_photo_description}` — the full-bleed background (sunset coastline, mountain trail, kitchen at golden hour, etc.)
- `{question}` — the white-card question text (1-2 lines, conversational, ≤80 chars)
- `{answer}` — typewriter-style multi-line answer in 4 short lines, mentioning the brand naturally
- `{cta_text}` — bottom pill CTA (e.g. `🔗 SHOP NOW`)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge — an Instagram Story-style "Ask me anything!" Q&A sticker overlaid on a beautiful lifestyle photograph. Standalone ad creative.

Background: a stunning warm-light landscape photograph fills the entire 9:16 canvas. The scene is a sun-drenched Mediterranean coastal town at golden hour — pastel cream and terracotta-roofed buildings cascade down a hillside to a calm sea where small boats are anchored. Soft pink and orange sunset light, dreamy and aspirational. The photograph fills the canvas edge-to-edge with no border.

Overlaid on the upper third of the canvas, centered horizontally: a rectangular composite "AMA sticker + answer" element, occupying about 70% of the canvas width:

A. The TOP part is the IG Story "Ask me anything!" question sticker — a stacked two-block element:
   - Top block: a black rounded-rectangle bar containing centered white bold sans-serif text "Ask me anything!"
   - Bottom block (attached directly below the top): a white rounded-rectangle (matched corners) containing centered bold black sans-serif text in 2-3 lines: "What's the one supplement you actually stay consistent with?"
   - The two blocks visually read as a stacked sticker, cohesive unit.

B. Just below the sticker (with a small gap), the answer is rendered as a typewriter-style monospace text overlay on a translucent white panel, multi-line, centered horizontally with comfortable safe-zone padding from the canvas edges:
   "AG1!! One scoop in the morning,
   that's it. Travel sachets in my
   bag for trips. 4 years strong.
   Not sponsored — link in bio!!!"

Bottom of the canvas (~10% from the bottom edge, well within safe zone): a small white rounded-pill CTA containing dark sans-serif text "🔗 SHOP NOW" with a small link-chain icon. Centered horizontally.

The composition reads as a real "creator IG Story moment" — but rendered as the standalone ad creative. No iOS status bar, no Story progress bars, no story header at top, no swipe arrows at bottom, no home indicator, no tab nav.
```

**Model notes:**
- **nano-banana-pro:** strong on the lifestyle-photo full-bleed background. **Preferred backend.**
- **gpt-image-2:** clean for the Q&A sticker UI, weaker on the photographic background realism.

---

## T21 — Handwritten testimonial on napkin / paper

**When to use:** UGC raw-and-real aesthetic. Reads as authentic creator content, not branded. Best for brands with a "friend recommendation" angle.

**Aspect ratio:** `2:3`

**Reference image:** product hero (used for the small product element placed near the napkin)

**Variables:**
- `{handwritten_message}` — multi-line cursive ink text, friend-to-friend voice, ending with the brand mention
- `{table_setting}` — what's around the napkin (cafe table, kitchen counter, marble countertop)
- `{product_element_description}` — the single product cue placed near the napkin (a sachet, a bottle, packaging glimpse)
- `{cta_color}` — color for the bottom shop-now pill

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a real-world tabletop photograph of a paper napkin with hand-written ink testimonial, set on a casual restaurant or kitchen table. Standalone ad creative, ready to upload.

Setting: a top-down, slightly angled photograph of a wooden or marble cafe table. Centered in the frame: a folded white paper napkin (or a square white napkin laid flat), with hand-written black ink message scrawled across it in slightly imperfect cursive / casual handwriting. The handwriting is clearly readable but organic — uneven baseline, occasional ink bleed, real-pen-on-paper texture.

The hand-written message reads (verbatim, multi-line, allowing for natural line breaks):

"When I was tired all the time
my friend told me to try AG1 -

Saved my mornings. Covered all
the basics in one scoop. No more
12-pill stack. Worth every penny."

Surrounding the napkin on the table, casually placed (NOT staged):
- A small clear glass with the bottom half remaining of a vibrant green liquid (AG1 mixed with water).
- A few crumbs of green powder dusted near the napkin edge.
- One coral / orange-red AG1 travel sachet (with white "AG1" wordmark) lying just to the side of the napkin, open / empty.
- The lower-left corner of the frame catches the edge of a small dish of fruit or pastry — implying a real meal context.

Lighting: soft warm natural daylight from upper-left, casting gentle shadows. The aesthetic is HOMEMADE / UGC — like someone genuinely scribbled their thoughts at a coffee shop. NOT styled product photography.

Bottom 10% of the canvas (within safe-zone padding from bottom edge): a small white rounded-pill CTA containing red bold sans-serif text "🔗 SHOP NOW" with a small link-chain icon, centered horizontally.

The composition feels like an organic post a friend would share — casual, lived-in, real.

No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **nano-banana-pro:** strong. Photoreal table + handwritten cursive ink is in its wheelhouse. **Preferred backend.**
- **gpt-image-2:** acceptable; handwriting can feel slightly font-like rather than organic.

---

## T23 — POV calendar timeline of pain points

**When to use:** relatability humor for time-pressed audiences (founders, parents, students). The brand emerges in the last calendar block as the relief. Strong scroll-stopper.

**Aspect ratio:** `1:1`

**Reference image:** product hero (only color cues)

**Variables:**
- `{pov_headline}` — two-line "POV: A [target customer]'s [domain] schedule" (e.g. `POV: A burned-out founder's daily energy schedule`)
- `{calendar_blocks[]}` — EXACTLY 8 events, top-to-bottom: 6 pain-points + 1 sliver "lunch / break / promise" + 1 final brand-arrival event. Each has color, title, and time range.
- `{time_axis_labels[]}` — 8 labels, each appearing exactly once (do NOT duplicate any label like "3 PM" twice)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake Apple Calendar app screenshot styled as a "POV: a [target customer]'s calendar" relatable-pain-point ad. Standalone ad creative, ready to upload. Pure white background.

Top of the canvas (~14% height, within safe-zone padding from top): a centered headline in bold black sans-serif (~32pt feel) across two stacked lines:
"POV: A burned-out founder's"
"daily energy schedule"

Below the headline, occupying the central ~80% of canvas: a calendar timeline view rendered as Apple Calendar dark mode (rounded-corner black panel with thin border). Inside the panel, a left-side time axis runs vertically with EXACTLY these eight labels stacked top-to-bottom (each label appears EXACTLY ONCE — do NOT duplicate any label):

9 AM
10 AM
Noon
1 PM
2 PM
3 PM
4 PM
5 PM

Each time label sits beside a thin grey horizontal divider running across the panel.

Time-blocked event boxes fill the calendar in the right ~85% of the panel. Each event is a rounded rectangle with a soft pastel fill color and a thicker colored left-border accent. Each event contains, top to bottom: a bold colored title line, then a small clock icon + time-range label in muted text. Plain text only — NO emoji.

EXACTLY EIGHT event blocks, top to bottom — no more, no fewer:

1. Soft blue fill (bright blue left border): "Crash from yesterday's caffeine" — "9 - 10 AM"
2. Soft purple fill (bright purple border): "Doom-scroll for energy hacks" — "10 AM - 12 PM"
3. Thin teal sliver (small text only, no time row): "Eat lunch, bloat instantly"
4. Soft green fill (green border): "Try to actually get work done" — "12:20 - 2 PM"
5. Soft blue fill: "Buy 4th supplement this month" — "2 - 3 PM"
6. Soft purple fill: "Nap-craving spiral" — "3 - 4 PM"
7. Thin teal sliver (small text only, no time row): "Promise tomorrow will be different"
8. Soft green fill: "Open AG1 box that just arrived" — "4:20 - 5:20 PM"

The visual joke: every event until the last one is a relatable pain. The last event is the brand showing up.

Calendar panel sits centered with comfortable safe-zone padding from canvas edges (~8%). Headline at top fully visible, bottom of calendar panel doesn't touch the bottom edge of the canvas. Time labels in the left axis appear EXACTLY ONCE each — no duplicates like "3 PM" appearing twice.

No additional text, no logos overlay, no UI chrome.
```

**Model notes:**
- **gpt-image-2:** clean. Calendar UI mimicry + small block labels are reliably legible.
- **nano-banana-pro:** block labels at small size blur; time-axis labels can repeat. **gpt-image-2 strongly preferred.**

---

## T24 — Phone-in-phone Reel composite

**When to use:** "watch this Reel" pattern — the canvas itself looks like a Reel still, with a phone-frame inset showing UGC. Strong when paired with intrigue overlay text ("Watch this BEFORE…", "What I tried after…"). Works for personality-led / influencer brands.

**Aspect ratio:** `9:16`

**Reference image:** product hero (used for the brand-pattern background and the product visible in the UGC photo)

**Variables:**
- `{background_pattern}` — repeating wordmark / branded backdrop (e.g. low-opacity AG1 wordmark on forest green)
- `{ugc_subject}` — what the inset photo shows (creator with product, mid-action, golden hour, etc.)
- `{overlay_text}` — black rounded-rectangle text label across the UGC photo (e.g. `Watch this BEFORE / your morning coffee`)
- `{cta_color}` — color for the bottom CTA bar
- `{cta_text}` — bottom CTA text (e.g. `Learn more`)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge — a "phone-in-phone" composite where the canvas itself appears to be an Instagram Reel-style scene, with a stylized smartphone-frame inset in the center holding the actual ad creative content. Standalone ad creative, ready to upload.

Background: a deep saturated solid color fills the entire 9:16 canvas (use a deep AG1 forest-green ~#1A4731). Subtle pattern: faint white "AG1" wordmark text repeats in stylized graffiti / sticker-style across the background at a consistent angle (~15° clockwise rotation), with low opacity (~15%) — creating a textured "branded backdrop" feel without being too busy.

Centered in the canvas (occupying the central ~65% width, ~70% height — well within safe-zone padding): a portrait-oriented smartphone frame mockup rendered as a clean rounded-rectangle device shape (slightly tilted ~5° clockwise for dynamism, with a subtle drop shadow). The phone frame contains a vertical 9:16 image inside its screen — the ACTUAL ad content:

INSIDE THE PHONE SCREEN:
- A real-feeling UGC selfie photograph: a fit woman in her early 30s with tied-back brown hair, light golden-hour kitchen lighting, smiling slightly while raising a clear AG1 shaker bottle of vibrant green liquid up toward her face. She's mid-laugh, casually dressed in a soft athletic top.
- Across the lower-mid of the photo, a black rounded-rectangle overlay text label with white bold sans-serif: "Watch this BEFORE / your morning coffee"

Across the bottom 14% of the entire canvas (NOT inside the phone — overlaid on the green background, with comfortable safe-zone padding from the bottom edge): a horizontal red CTA bar (~#E84F2C or strong AG1-coral) spanning the full canvas width, containing white bold sans-serif text "Learn more" left-aligned, with a small white right-arrow ">" on the right edge.

The composition reads as a Reel preview where someone is showing a phone screen. No iOS status bar, no Reel UI (no IG header, like buttons, comment count), no home indicator.
```

**Model notes:**
- **both: clean.** Phone-frame mockup renders well on both. nano-banana edges ahead if the UGC inset is realistic.

---

## T25 — Newspaper crossword puzzle

**When to use:** clever editorial brand-puzzle moment. Plays well in lifestyle / wellness categories where a "Sunday morning, coffee and crossword" association is on-brand.

**Aspect ratio:** `1:1`

**Reference image:** product hero (props the small product accent)

**Variables:** `{newspaper_masthead}` (e.g. "The AG1 Daily"), `{date_string}`, `{across_clues[]}`, `{down_clues[]}`, `{filled_words[]}` (3-4 short crossing words, ≤5 letters each so each grid cell stays large enough to render legibly)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a top-down photograph of a fake newspaper page featuring a small partially-filled crossword puzzle, displayed on a wooden coffee-shop table with subtle props. Standalone ad creative.

The newspaper page fills ~75% of the frame, slightly tilted. Cream/beige aged-newsprint texture and crisp serif typography. Subtle warm shadow from morning daylight. Surrounding the newspaper on the wood surface: a small white cup of coffee with steam (top-right corner of frame), a few loose AG1 travel sachets (coral/orange-red) scattered along the top and right edges of the frame, and a green AG1 pouch tucked into the bottom-right corner.

Newspaper layout, top to bottom:

- Masthead: "The AG1 Daily" in classic black serif, large, with a horizontal rule beneath
- Sub-header: "Tuesday Crossword · March 17, 2026" in small italic serif

- Centered crossword grid: a SMALL 5x5 square grid (only 25 cells total — keep it small so each cell is large enough that letters render legibly). Cells alternate between black squares (separators) and white squares with bold black UPPERCASE Helvetica-style letters inside. Each white cell contains EXACTLY ONE big bold black capital letter, rendered at large readable size (~50pt feel inside its cell).

- The grid has THREE filled-in words crossing each other:
  - Horizontal across the middle row: "DAILY" (5 letters: D-A-I-L-Y fills 5 cells)
  - Vertical down a column intersecting the middle: "CALM" (4 letters: C-A-L-M, vertical, intersecting "DAILY" at the "A")
  - Vertical down another column: "SCOOP" (5 letters: S-C-O-O-P, vertical, intersecting "DAILY" at "I")

  Adjust if the geometry doesn't fit exactly — the goal is THREE fully-spelled crossing words rendered with ONE big crisp letter per cell, all clearly legible. Black squares fill any cells without letters.

- To the right of the grid, a numbered clue list in small black sans-serif:
  ACROSS:
  3. How often you take it

  DOWN:
  2. The state you're after
  5. One per day

- Faint "AG1" wordmark watermark at the bottom-right corner of the page in light grey

Photographic style: warm editorial, real newsprint texture, "good morning, coffee + paper" lifestyle moment. The crossword is small but the letters in each cell are big and crisp.
```

**Note:** Keep the grid SMALL (5x5 max) and use only 3-4 short crossing words. Letters in tiny crossword cells garble; a small grid with big letters renders clean.

**Model notes:**
- **gpt-image-2:** acceptable. Strict 5x5 grid with big letters still requires explicit prompting; even then expect 10-15% iteration to land clean.
- **nano-banana-pro:** weaker — letters in grid cells reliably scramble. Use gpt-image-2 unless you accept iteration cost.

---

## T26 — Cash register receipt

**When to use:** product-as-receipt joke. List the brand's "benefits received" as itemized line items + total. Strong for "you get [list]" value-prop positioning.

**Aspect ratio:** `1:1`

**Reference image:** product hero (sits beside the receipt as a real-world prop)

**Variables:** `{store_header}` (e.g. "AG1 WELLNESS CO.\ndrinkag1.com\n123 Foundation Way"), `{date_line}`, `{benefits[]}` (each `{label, value}` like `ENERGY  FREE`), `{total_line}` (e.g. "ONE GREAT DAY"), `{footer_text}`

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a top-down photograph of a long thermal-printer cash register receipt, slightly crumpled and curled at the bottom edge, lying on a clean cream/beige flat surface. The AG1 product sits to the right of the receipt as a real-world prop. Standalone ad creative.

Receipt details:
- White thermal paper, slightly textured, long and narrow (about 35% of canvas width, full canvas height plus a curl at the bottom)
- Header in monospaced black caps: "AG1 WELLNESS CO. / drinkag1.com / 123 Foundation Way / Tuesday, May 6, 2026"
- A "BENEFITS RECEIVED" label in bold caps
- Itemized list in monospace, each line: benefit name (left) and "FREE" or a number (right):
  ENERGY                FREE
  FOCUS                 FREE
  CALM                  FREE
  GUT HEALTH            FREE
  IMMUNE SUPPORT        FREE
  MORE ENERGY           +1
  CONSISTENCY           +1
  CONFIDENCE            +1
  ----------------------------
  SUBTOTAL              FREE
  TAX                   FREE
  ----------------------------
  TOTAL: ONE GREAT DAY
- Below the total, a faux barcode (vertical black lines) and small footer text "Thank you for prioritizing your day. / drinkag1.com"

The AG1 product (forest-green pouch with white "AG1" wordmark, glass shaker bottle of green liquid, one or two coral travel sachets) sits casually beside the receipt on the right side of the canvas, well within safe-zone padding.

Soft warm natural light from upper-left, gentle shadow under both the receipt and the product. Editorial flat-lay aesthetic, premium-wellness vibe.
```

**Model notes:**
- **nano-banana-pro:** strong on the receipt photo realism. Monospace text legibility holds at this scale.
- **gpt-image-2:** clean for the monospace text; receipt photo can feel composited. Either backend works.

---

## T27 — Handwritten founder letter

**When to use:** intimate brand storytelling. Founder voice, mission, gratitude, or insider-first-batch moment. Premium DTC brands use this to humanize at scale.

**Aspect ratio:** `2:3`

**Reference image:** product hero (placed beside the letter as a desk prop)

**Variables:** `{letter_body}` (handwritten cursive, 6-10 short lines max — keep it sparse), `{founder_name}`, `{footer}` (URL + role)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a top-down photograph of a handwritten founder's letter on cream stationery, with the AG1 product and a fountain pen as props on a warm walnut wood desk. Standalone ad creative.

Composition:
- Background: a warm walnut wood desk surface, slightly textured grain, with a leather notebook visible at the very edge (top-left corner) and a small chart/document peeking from the bottom-right corner.
- Centered: a single piece of cream/off-white stationery (~70% of canvas width, slightly tilted ~3° clockwise), with a printed dark-green AG1 wordmark in the top-left corner of the page.
- A black ink fountain pen rests across the bottom-right corner of the letter.
- One coffee-cup ring stain in faint brown on the bottom-left corner of the paper (organic detail).
- A handwritten letter in flowing dark-blue ink cursive fills the page. The handwriting is realistic, slightly imperfect, with natural ink flow and varying line weights. The letter reads (verbatim):

"Hey friend,

If you're reading this, you got 1
of the first 10,000 AG1 Next Gen
pouches. Thank you for trusting us.

I built AG1 because the supplement
aisle is a maze. We made the one
thing you need — clinically dosed,
third-party tested, in one daily scoop.

This isn't just a supplement. It's
foundational nutrition for the life
you actually want to live.

Let's keep building together.
Gratefully yours,

  — Chris (signed in casual cursive script)
  Founder, AG1
  drinkag1.com"

To the right of the letter (lower-right area, partially overlapping the page edge): the AG1 product — a deep forest-green AG1 pouch standing upright with white "AG1" wordmark visible, alongside one open coral travel sachet beside it.

Soft warm side lighting from the upper-left, casting gentle shadows. The composition feels like a thoughtful, personal founder's gesture — premium and intimate, not staged.
```

**Note:** Both models partially garble handwritten cursive — keep letter content under 10 lines and accept that 2-3 words may shift. The aesthetic and intent come through; word-perfect handwriting is hard.

**Model notes:**
- **nano-banana-pro:** strong on the desk-photo realism; cursive imperfection feels organic.
- **gpt-image-2:** cursive can feel slightly font-like. Pass an actual handwriting sample as `--image-ref` to anchor the script style.

---

## T28 — Dating app swipe card (Hinge-style)

**When to use:** brand personality / "what we're about" angle. Treats the brand as a dateable persona. Strong for personality brands and lifestyle products.

**Aspect ratio:** `2:3`

**Reference image:** product hero (the photo on the profile card)

**Variables:** `{brand_age_label}` (e.g. "AG1, 75" — using ingredient count as age), `{location_line}` (e.g. "Foundational Nutrition · Here for the long haul"), `{prompts[]}` (2 prompt+answer pairs in Hinge style)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a fake Hinge-style dating app profile card with the AG1 product as the "match" subject. Standalone ad creative. Soft cream/off-white background ~#F8F5F0 fills the entire canvas.

The image renders ONE single profile card, centered, occupying ~85% of the canvas with comfortable safe-zone padding. The card has rounded corners and a subtle drop shadow.

Card content, top to bottom:

1. Header bar (~6% of card height): bold black sans-serif "AG1, 75" (the brand name + ingredient count as "age"). Below: a small black location pin glyph + light grey text "Foundational Nutrition · Here for the long haul"

2. Hero image (~50% of card height): a clean editorial photograph of the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark prominent, alongside a clear shaker bottle of vibrant green liquid. Soft cream background continuing from the canvas, premium product photography. A small grey heart icon sits in the bottom-right corner of the photo (the Hinge "like a photo" indicator).

3. Below the photo, two stacked Hinge-style answer prompts. Each prompt has: a small light-grey label ("My most controversial opinion is...", "What I'm looking for..."), then below the label, a black sans-serif answer in larger type. The two prompts read:

PROMPT 1:
Label: "My most controversial opinion is..."
Answer: "Multivitamins are a scam. Real foundational nutrition needs 75+ ingredients in one daily scoop."

PROMPT 2:
Label: "What I'm looking for..."
Answer: "Someone who shows up consistently. Mornings, travel, busy weeks. Let's build healthy habits together."

Each prompt has a small grey heart icon in its bottom-right corner.

4. Bottom of card (~10% height): two large circular buttons side by side, centered horizontally with a gap between them. Left button: white circle with grey "X" inside (Pass). Right button: pink-purple gradient circle with white "♥" inside (Like).

The composition reads as a real Hinge profile, but rendered as a standalone ad creative.
```

**Model notes:**
- **gpt-image-2:** clean. App UI mimicry is strong. **Preferred backend.**
- **nano-banana-pro:** acceptable; the X / ♥ buttons can drift.

---

## T29 — TikTok creator video screenshot

**When to use:** UGC creator energy. "Influencer holding the product mid-explanation" with chunky white-on-black caption text + comments overlay sliding up from the bottom. Native to TikTok/Reels.

**Aspect ratio:** `9:16`

**Reference image:** product hero

**Variables:** `{creator_description}` (1-line — age, energy, setting), `{caption_text}` (3-4 short lines, white on black rounded-rectangles), `{comments[]}` (2 fake comments with @handle + body + heart count)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge — a fake TikTok video screenshot with a creator holding the product, captions, and a comments overlay. Standalone ad creative.

The full canvas is filled with a vertical TikTok-style video frame. Background: a fit, smiling man in his early 30s, casual hoodie, standing in a softly-lit kitchen at golden-hour. He holds a deep forest-green AG1 pouch up close to camera with one hand, his face slightly to the side, mid-grin like he's mid-explanation. Cinematic shallow depth of field, the background is softly blurred (kitchen counter, plants, a window).

Overlaid on the video, lower-mid area, in the chunky angled white-text-on-black-rounded-rectangles aesthetic typical of TikTok captions:
"How I survived Q4 without
losing my mind: AG1 every
morning. #notsponsored
#actuallyworks"

In the lower third of the canvas (below the captions, above the comments overlay), an OVERLAY panel rendered in semi-transparent dark grey appears to be the comments section sliding up from the bottom. Inside the panel, two visible comments rendered top to bottom:

Comment 1:
- Small circular avatar (cartoon person)
- "@morningroutine"
- Comment text: "Bro literally same. AG1 is a life saver during launches"
- Below: a small heart icon and "1.2K"

Comment 2:
- Small circular avatar
- "@dtcops"
- Comment text: "Picked it up after seeing your last video. 4 weeks in, no regrets"
- Below: heart icon and "847"

The composition reads as an organic TikTok creator post — but rendered as a standalone ad creative. No iOS chrome, no TikTok navigation tabs at the bottom, no like/share/comment side rail beyond the comments overlay panel.
```

**Model notes:**
- **nano-banana-pro:** strong on the creator photograph (mid-action, natural lighting). **Preferred backend** for the photo half.
- **gpt-image-2:** clean for the caption rectangles + comments overlay. Hybrid approach: generate the creator photo with nano-banana, then composite captions with gpt-image-2 if you want both.

---

## T30 — Billboard / OOH placement mockup

**When to use:** "we're a real brand" credibility through scale. Subway, transit, or street billboard imagery. Gives the brand the gravitas of an OOH campaign.

**Aspect ratio:** `1:1`

**Reference image:** product hero (small product photo at the bottom of the billboard)

**Variables:** `{environment}` (e.g. "modern subway platform"), `{billboard_headline}` (2 stacked lines, bold sans), `{billboard_subcopy}`, `{brand.color_primary}` (billboard background), `{brand.url}`

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a photograph of a real-world out-of-home billboard or subway/bus-stop digital ad placement featuring the brand. Standalone ad creative.

Setting: a modern subway / metro station platform or transit hallway, slightly out of focus with cinematic depth of field. The platform has soft cool blue lighting in the background, with a few blurred silhouettes of pedestrians walking past. A polished concrete or marble floor reflects subtle light.

Centered in the frame: a large rectangular vertical digital billboard (like a Vista Network or Lamar transit display), occupying ~70% of canvas width and ~80% of canvas height. The billboard has a thin dark frame with a clean lit display face inside.

Inside the billboard display:
- Background: deep AG1 forest-green ~#1A4731, edge-to-edge inside the frame
- Top-left corner: small white "AG1" wordmark
- Center, large bold white sans-serif headline (~40% of billboard height) in two stacked lines: "ONE SCOOP. / EVERYTHING YOU NEED."
- Below the headline, slightly smaller white sans-serif: "Foundational nutrition for the life you actually want."
- Bottom-center: a clean photograph of the AG1 product — deep forest-green pouch with white wordmark, a clear shaker bottle of green liquid, a few coral travel sachets fanned out beside them.
- Very bottom: small white URL "drinkag1.com"

The billboard is brightly lit (slight glow on the surrounding wall), set into a real-world environment with motion-blurred passers-by and atmospheric background. Premium DTC OOH aesthetic — feels like a real Vogue / Men's Health subway ad.
```

**Model notes:**
- **nano-banana-pro:** strong on environmental photo realism (motion blur, transit lighting). **Preferred backend.**
- **gpt-image-2:** clean for the billboard typography content; environment realism slightly composited.

---

## T31 — Scratch-off lottery ticket

**When to use:** novelty / interactive feel. Treats the brand's benefits as "scratch to win" panels. Tactile, fun, distinctive.

**Aspect ratio:** `2:3`

**Reference image:** product hero (one of the 6 panels shows the actual product photo)

**Variables:** `{ticket_title}` (e.g. "Match to Foundational Nutrition"), `{benefit_panels[]}` (5 panels, each `{icon, label}`), `{footer_line}` (e.g. "$0 LOSING TICKETS. EVERY SCOOP WINS."), `{ticket_serial}`

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a top-down photograph of a physical scratch-off lottery ticket on a slightly textured surface, with scratched-off silver foil flakes scattered around it. Standalone ad creative.

Background: a soft greige textured surface (like brushed concrete or matte cardstock). Faint silver scratch-off flakes dust the surface around the ticket.

Centered: a single rectangular scratch-off card (~75% of canvas width, slightly tilted ~3° clockwise), thick cardstock with rounded corners, a faint paper texture. The ticket has a deep AG1 forest-green border (~5% of card width) framing the central content.

Ticket content, top to bottom:
- Top header bar: white box containing "AG1 PRESENTS" in small forest-green caps, a small green leaf icon, and serial number "No. 075777 / NEXT GEN"
- Title: "Match to Foundational Nutrition" in bold dark forest-green serif (large)
- Centered: a 3x2 grid of six square panels — five of them are silver scratch-off panels (with realistic foil texture, partially scratched away revealing icons + words underneath), one is a clean white panel containing the AG1 product photo.

The five scratched-off icons reveal in white circles with dark forest-green icons + caps labels beneath:
1. Top-left: a leaf icon, label "ENERGY"
2. Top-middle: a brain icon, label "FOCUS"
3. Top-right: a heart icon, label "CALM"
4. Bottom-left: a smile icon, label "GUT HEALTH"
5. Bottom-middle: a star icon, label "WIN"
6. Bottom-right: clean white panel with the AG1 product photo (forest-green pouch with white wordmark, small)

- Below the grid, large bold serif: "WIN ALL FIVE = ONE SCOOP DAILY"
- Footer text in small caps: "$0 LOSING TICKETS. EVERY SCOOP WINS. drinkag1.com"
- Bottom-right corner: a small dime / quarter-sized round circle (the "scratching coin" prop) photographed beside the ticket

Soft top-down lighting, slight shadow under the card. Tactile, real-world product-photography aesthetic. Feels like a clever scratch-off card you'd actually want to play.
```

**Model notes:**
- **nano-banana-pro:** strong on the foil/scratch-off material texture. **Preferred backend.**
- **gpt-image-2:** clean for the icon labels + ticket typography; foil texture feels slightly flat.

---

## T32 — Pain-point checklist + product

**When to use:** problem-aware audiences. Lead with their pain via an unchecked-checkbox list, deliver the product as the answer below.

**Aspect ratio:** `1:1`

**Reference image:** product hero

**Variables:** `{headline}` (2-line bold all-caps question or statement), `{checklist_items[]}` (exactly 5 unchecked items, each conversational), `{tagline}` (1 closing line in bold serif), `{footer_url_line}`

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a clean editorial layout with a bold pain-point headline at top, an unchecked checklist of relatable pain points in the middle, the AG1 product photo in the lower portion, and a calm tagline + brand wordmark at bottom. Standalone ad creative. Pure white background.

Top section (~22% height): a centered bold black sans-serif headline in two stacked lines, large (~60pt feel), tight tracking:
"BURNED OUT BY YOUR
SUPPLEMENT ROUTINE?"

Middle section (~32% height, generous vertical spacing): a vertical list of EXACTLY FIVE checklist items, each row consisting of a hollow grey square checkbox on the left + the question text in regular black sans-serif. Items (verbatim):
☐ Forgetting half your morning pills again
☐ Bloating from synthetic fillers
☐ No energy by 10am despite the stack
☐ Endless scrolling for the "right" supplement
☐ Wishing it was just one simple step

Lower section (~32% height): a clean centered editorial photograph of the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark prominent, alongside a clear shaker bottle of vibrant green liquid. Soft natural light, premium product photography.

Bottom section (~14% height): centered, two stacked lines of black text:
- Line 1: bold serif: "ONE SCOOP. ZERO COMPROMISES."
- Line 2: smaller regular sans-serif: "AG1 — foundational nutrition for media buyers, founders, and anyone tired of the supplement aisle. drinkag1.com"

All text and product within the central 84% safe zone. Modern, premium, calm aesthetic.
```

**Model notes:**
- **both: clean.** Minimal layout, large text, single product hero — neither model struggles.

---

## T33 — Bold typography hero quote

**When to use:** stop-the-scroll brutalist statement. Strong for declarative or contrarian brand voice. Type IS the visual.

**Aspect ratio:** `1:1`

**Reference image:** product hero (small product accent in the lower-right)

**Variables:** `{statement}` (3-line punchy declaration in chunky condensed sans, ~140pt feel, period at the end), `{supporting_text}` (3-4 short lines in the lower-left), `{brand.color_primary}` (canvas background), `{type_color}` (cream off-white that contrasts the brand color)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a bold editorial typography hero with a punchy three-line statement filling most of the canvas, a small product photo as a footnote, and minimal supporting text. Standalone ad creative.

Background: deep AG1 forest-green ~#1A4731, edge-to-edge, with a subtle radial darker vignette centered on the canvas.

Top 60% of the canvas: a HUGE bold sans-serif statement (~140pt feel — chunky, condensed, brutalist) in cream off-white ~#F5F1EA, stacked across three lines, left-aligned with consistent left margin (~10% from canvas left edge):

"STOP STACKING
PILLS LIKE IT'S
2014."

Each line is a full uppercase sentence-fragment. The third line ends with a period. Letter-spacing is tight, line-height is tight (lines almost touch). The TYPE is the hero — not centered, intentionally left-aligned.

A small hand-drawn arrow (white outline, slightly wobbly, marker-style) curves down-right from the period at the end of "2014." pointing toward the lower-right corner of the canvas where the product sits.

Bottom-right corner (~28% of canvas, fully within safe zone): a clean editorial photograph of the AG1 product — deep forest-green pouch with white "AG1" wordmark visible, slightly tilted, with a faint soft drop shadow. The product is photographed against the same green background, color-matched.

To the left of the product (lower-left quadrant), in cream off-white sans-serif at smaller size (~28pt), three short stacked lines:
"One scoop. 75+ ingredients.
Foundational nutrition.
drinkag1.com"

Modern, brutalist-meets-premium typography aesthetic. The type makes the joke; the product punctuates it.
```

**Model notes:**
- **gpt-image-2:** clean. Type-led layouts are its strength. **Preferred backend.**
- **nano-banana-pro:** condensed-sans letterforms drift; tight letter-spacing slips. Use gpt-image-2 for this template.

---

## T34 — iMessage conversation (with rich link card)

**When to use:** "friend recommended it" social proof. Pixel-faithful iOS Messages screenshot, including a rich link preview card embedded in the conversation.

**Aspect ratio:** `9:16`

**Reference image:** product hero (used in the rich link preview card)

**Variables:** `{contact_name}`, `{messages[]}` (4 bubbles total: 2 incoming grey, 2 outgoing blue including 1 with a rich link card preview), `{rich_card.url}`, `{rich_card.title}`, `{rich_card.description}`

**Element structure:** grey text → blue text → blue link card → grey text. Four bubbles.
State the structure, not just the number — a bare count leaves the model to decide which
kind of bubble is missing, and the link card is the one that carries the product.

> **Declared divergence from the Kruse source.** Upstream opens this prompt at *three*
> bubbles and closes it at *four*; this copy says four throughout, which is what rendered
> correctly when measured on 2026-08-06.

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
9:16 portrait static ad creative, 1080x1920, edge-to-edge — a fake iOS Messages app conversation thread with EXACTLY FOUR message bubbles in this order: a grey incoming text, a blue outgoing text, a blue outgoing rich link card, a grey incoming text. Standalone ad creative. Pure white background ~#FFFFFF.

Top of the canvas (~10% height): a Messages app conversation header — centered, a small circular contact avatar (~40px) with a dark grey "A" letter inside, then below it the contact name "Alex" in regular black SF Pro, then below in smaller grey: "Today 9:47 AM". On the far right of the header, a small blue FaceTime-camera icon. NO iOS status bar, NO back button.

Below the header, an EXACT FOUR-bubble vertical chat sequence with comfortable spacing between bubbles. Plain text only, no emoji, no special glyphs.

BUBBLE 1 (incoming, left-aligned):
- Light grey rounded bubble (~#E9E9EB) with black sans-serif text inside:
  "I'm so stressed lately. Work, life, everything just feels overwhelming."

BUBBLE 2 (outgoing reply, right-aligned, blue):
- iMessage blue bubble (~#0B93F6) with white sans-serif text inside:
  "I've been there honestly. You should try this:"

BUBBLE 3 (outgoing follow-up, right-aligned): a "rich link preview" attachment card embedded as a message — white rounded card with a thin grey border. Inside the card top to bottom:
- Small editorial photograph of the AG1 product (forest-green pouch with white "AG1" wordmark + clear shaker bottle of green liquid)
- Below the photo, a thin hairline divider, then small black text:
  Title: "drinkag1.com"
  Subtitle: "AG1 — One scoop. Foundational calm + clarity. Game changer."

BUBBLE 4 (incoming, left-aligned):
- Light grey bubble:
  "omg need!! ordering now"

(Note: render exactly the four bubbles described above — two incoming grey, two outgoing blue, the last of which is a rich link preview card.)

Below the conversation, a thin grey divider, then a Messages app input row: rounded grey input pill containing the placeholder text "iMessage" in light grey, with a small camera icon on the left and a microphone icon on the right.

The composition reads like a real iPhone Messages screenshot — but rendered as a standalone ad creative. NO iOS status bar, NO home indicator, NO Messages tab bar at the bottom.
```

**Model notes:**
- **gpt-image-2:** clean. iOS Messages UI mimicry is strong, rich-link card renders faithfully. **Preferred backend.**
- **nano-banana-pro:** the rich-link card and iMessage chrome can drift in proportion. Use gpt-image-2.

---

## T35 — Magazine cover

**When to use:** premium brand spotlight. Editorial magazine masthead with the product as the cover hero. Pairs well with wellness, fashion, lifestyle categories.

**Aspect ratio:** `2:3`

**Reference image:** product hero (the cover photograph)

**Variables:** `{magazine_title}` (e.g. "VITALITY"), `{issue_subbar}` (e.g. "THE WELLNESS ISSUE · SUMMER 2026 · ISSUE 16"), `{cover_lines[]}` (3-4 cover-line headlines stacked down the left edge, each with a topic + 1-line description), `{spotlight_badge_text}`, `{bottom_band_text}` (italic serif, 2 lines)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
2:3 portrait static ad creative, 1080x1620, edge-to-edge — a fake premium wellness magazine cover with the brand product as the hero. Standalone ad creative.

Layout reads as a magazine cover from top to bottom:

TOP MASTHEAD (~14% height): the magazine title "VITALITY" in a chunky bold serif logo, large, centered, in black. Just beneath it in smaller all-caps serif: "THE WELLNESS ISSUE · SUMMER 2026 · ISSUE 16". A thin horizontal hairline divider beneath.

LEFT EDGE (~30% width, vertical column of cover-line text):
- "Nature's"
- "Answer to"
- "Stress" (the headline word in larger bold black serif, ~44pt)
- Below in smaller regular sans: "Discover the power of ashwagandha"
- A small bullet-list of three additional cover lines further down, each in caps small serif:
  "MENTAL CLARITY"
  "Herbs that help you stay focused"
  "—"
  "HOLISTIC WELLNESS"
  "Simple rituals for a calmer mind"
  "—"
  "ADAPTOGEN SUPPORT"
  "Balance stress and boost resilience"

CENTER (the hero): a large editorial photograph of the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark prominent, alongside a clear shaker bottle of vibrant green liquid, occupying the center-right of the cover (~50% of canvas width). Soft natural daylight. The product is the visual focal point of the cover.

UPPER-RIGHT CORNER overlay: a small circular badge in dusty rose color, with white serif text inside reading: "EXCLUSIVE BRAND SPOTLIGHT — [BRAND]"

BOTTOM (~14% height): an inset deep cream band edge-to-edge, with centered serif italic text in dark forest-green: "Rooted in Balance. / Powered by Ashwagandha." Below in tiny caps sans: "PREMIUM HERBAL SUPPLEMENT"

The aesthetic is glossy premium magazine — Vogue / Goop / Real Simple feel. Pixel-faithful to a real magazine cover photograph.
```

**Model notes:**
- **both: clean.** Both render the masthead + cover photo well. nano-banana edges ahead on hero photo richness.

---

## T36 — Lifestyle "operator's daily kit" flatlay

**When to use:** "what's in my bag/desk" lifestyle association. Curated flatlay of the brand product alongside aspirational everyday-carry items, each labeled with a small annotation. Strong for premium DTC trying to attach to a target audience's identity.

**Aspect ratio:** `1:1`

**Reference image:** product hero (centerpiece of the flatlay)

**Variables:** `{surface_color}` (typically charcoal-black or warm walnut), `{items[]}` (6-8 EDC items each with `{description, position, label}`), `{center_caption}` (small product label under the centerpiece)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a top-down "what's on my desk" lifestyle flatlay with the brand product as the centerpiece, surrounded by curated everyday-carry items each connected to a small annotation label. Standalone ad creative.

Background: a deep matte charcoal-black surface (slate or polished concrete), edge-to-edge, with subtle texture.

Centerpiece: the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark, alongside a clear shaker bottle filled half-way with vibrant green liquid, sitting roughly center-canvas.

Surrounding the product in a balanced top-down composition (each item separated by negative space and casually arranged, not perfectly grid-aligned):
- Top-left: a sleek black laptop with the lid slightly open
- Top-right: a small black insulated water bottle / thermos
- Right side: a phone showing a fitness/health dashboard (subtle teal-green chart)
- Bottom-right: a small leather-bound notebook with a fountain pen across it
- Bottom-left: a pair of black noise-cancelling earbuds (open case visible)
- Left side: a folded pair of dark glasses or blue-light blockers
- Far-left: a small black leather wallet with a few cards peeking out

For each surrounding item, a thin white hairline annotation line extends from the item to a small white sans-serif text label positioned near the canvas edge (well within safe zone). Labels read (one per item):
- Laptop: "Deep Work Audio"
- Thermos: "Fuel for Long Days"
- Phone: "Performance On Demand"
- Notebook: "More Tools & Resources"
- Earbuds: "Focus Soundtrack"
- Glasses: "Blue Light Blockers"
- Wallet: "Campaign Notes"

Center label, just under the product itself: a small white sans-serif title in two stacked lines: "[BRAND] · ULTIMATE ASHWAGANDHA / Stress Support That Performs"

Soft cinematic top-down lighting from upper-left, gentle shadows beneath each object. The composition reads as a curated "operator's daily kit" — every item tagged. Premium-DTC editorial aesthetic.
```

**Model notes:**
- **nano-banana-pro:** strong on flatlay realism + material differentiation (leather, metal, fabric textures). **Preferred backend.**
- **gpt-image-2:** clean for the annotation labels; flatlay can feel slightly synthetic.

---

## T37 — Weather-app forecast UI

**When to use:** "your day on the brand" wellness narrative styled as a weather forecast. Each "hour" is a brand-driven outcome (Clear Strategy, Stress-Free Sunset, etc.). Distinctive and on-trend.

**Aspect ratio:** `1:1`

**Reference image:** product hero

**Variables:** `{headline}` (2-line "0% Stress." style), `{forecast_columns[]}` (5 columns, each `{time, icon_shape, condition_label, subtitle}`)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a fake "Weather forecast" UI styled as a wellness/energy daily forecast for the brand. Standalone ad creative. Soft cream / warm off-white background ~#F5F1EA.

Top section (~22% height): a small grey caps label "FORECAST SOURCE" in muted text, then below a centered bold black sans-serif headline (~50pt feel) in two stacked lines:
"0% Stress."
"Foundational AG1 for founders."

Below the headline, a thin grey hairline divider running across most of the canvas width.

Middle section (~46% height): a horizontal hourly weather-forecast strip — five evenly-spaced columns, each containing top-to-bottom: a time label (small grey sans), a small soft-color weather-style icon (stylized minimal vector-style), a short weather-style condition label in black sans-serif, an even smaller subtitle in light grey. The five columns read:

Column 1: "9 AM"  ☀️-style sun icon (soft yellow)  "Clear Strategy"  "Mental clarity"
Column 2: "12 PM"  ⚡-style spark icon (soft amber)  "High ROAS Front"  "Peak performance"
Column 3: "3 PM"  ✨-style sparkle icon (soft mint)  "Zero Panic"  "Calm pressure"
Column 4: "6 PM"  🌅-style sunset icon (soft peach)  "Stress-Free Sunset"  "Energy holds"
Column 5: "9 PM"  🌙-style moon icon (soft lavender)  "Deep Unplug"  "Rested mind"

(Render the icons as SHAPES, not literal emoji — stylized minimal vector glyphs in soft pastel colors.)

Lower section (~28% height): a clean editorial photograph of the AG1 product (deep forest-green pouch with white wordmark + clear shaker bottle of green liquid + 1-2 coral travel sachets), centered, well within the safe zone. Soft natural light, premium product photography.

Bottom (~4% height): centered, small black sans-serif: "AG1 — drinkag1.com"

The composition reads like a calm, designed weather-app forecast widget, but the data is "your day on AG1." Modern minimal aesthetic.
```

**Model notes:**
- **gpt-image-2:** clean. UI mimicry + icon rendering reliable.
- **nano-banana-pro:** icons can drift toward emoji-style instead of vector shapes; column labels at small size blur.

---

## T38 — Big stat hero with chart

**When to use:** data-led credibility. Lead with a giant percentage/number, support with a minimal line chart, anchor with the product. Strong for outcome-driven brands (supplements, productivity, finance).

**Aspect ratio:** `1:1`

**Reference image:** product hero (right side of the canvas)

**Variables:** `{stat_value}` (e.g. "-37%" — the giant headline number in chunky condensed sans), `{stat_subhead}` (2-line bold black, e.g. "LESS STRESS. / MORE FOCUS."), `{stat_caption}` (1-line explanation), `{chart_axis_labels}` (e.g. weekly markers), `{benefit_icon_rows}` (3 small icon+label rows)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a bold statistic-led ad with a giant percentage headline, a small minimal chart underneath, and the product to the side. Standalone ad creative. Pure white background.

Top-left occupying ~50% width and ~50% height: a HUGE bold dark forest-green sans-serif percentage statistic, like "-37%" rendered in a chunky modern condensed sans (~180pt feel), with the minus sign and percent character full-size. Letter-spacing is tight.

Below the giant number, in slightly smaller bold black sans-serif (~36pt), a stacked two-line statement:
"LESS STRESS.
MORE FOCUS."

Below that, in regular black sans-serif at smaller size (~16pt), a single explanatory line:
"Average cortisol reduction during 8 weeks of daily AG1."

Below the explanatory line, a SMALL clean line-chart visualization (~30% of canvas width): a horizontal axis with 4 weekly tick labels (WEEK 1, WEEK 2, WEEK 3, WEEK 4), a vertical axis with a soft grid, and a single green line descending from the upper-left to the lower-right with small dot markers at each week. A single emphasized "-37%" label at the lowest point (small white pill on the green line). Below the chart, three tiny stacked icon+caption rows: "Sharper focus", "Better decisions", "Calmer mindset" with small icons (a brain, a target, a leaf) preceding each.

Right side of the canvas (~40% width, vertically centered): a clean editorial photograph of the AG1 product — deep forest-green pouch with white "AG1" wordmark, alongside a clear shaker bottle of green liquid. The product is photographed against a faintly cream background that fades into the white canvas, with subtle drop shadow.

Bottom (~6% height): small black sans-serif "AG1 · drinkag1.com" centered.

Modern data-led editorial design. The big number is the hero; the chart proves it; the product is the deliverable.
```

**Model notes:**
- **gpt-image-2:** clean. Strong on the stat number + chart axis labels.
- **nano-banana-pro:** stat number renders fine at giant size; chart axis labels can blur. Acceptable.

**Documented limit — the chart is drawn approximately, not plotted.** `gpt-image-2` sizes a
bar or a plotted point by eye, not by the number beside it: measured 2026-08-06, this
template's `204` bar overshot its own axis by about 9% while every label came back exact.
That is the model working as designed, not a defect to retry — a fresh render redraws it
approximately too. **If the chart has to be numerically true, composite it: generate the ad
without the chart and lay a real chart over it, or accept that the picture is decorative and
the number in the copy is the claim.** The same applies to T17's stacked bars.

---

## T39 — Museum exhibit display

**When to use:** "the brand as cultural artifact" prestige play. Treats the product as an art piece on a plinth with a museum placard. Aspirational, premium, tongue-in-cheek.

**Aspect ratio:** `1:1`

**Reference image:** product hero (placed on the plinth)

**Variables:** `{placard_title}` (e.g. "AG1 NEXT GEN"), `{placard_subtitle}` (e.g. "Foundational Nutrition, 2026"), `{placard_body}` (2-4 sentence "museum label" describing the artifact in dry institutional voice)

**Template prompt** (AG1-validated example — swap brand-specifics per Variables above):
```
1:1 static ad creative, 1080x1080, edge-to-edge — a photograph of the brand product displayed on a polished plinth in a hushed art-gallery / museum interior, with a small placard wall-mounted to the right. Standalone ad creative.

Setting: a clean, minimal modern art-gallery interior — pale beige or off-white wall (~#EDEAE3) extending across the canvas, smooth concrete or polished hardwood floor (visible at the bottom edge of the canvas), soft directional spot-lighting from above. Subtle architectural elements (a faint corner edge, a hint of a doorway in the deep background) add depth, but the wall is the dominant background element.

Center-left of the canvas: a slim rectangular plinth (warm walnut-wood top, deep matte charcoal sides), about 18% of canvas height, photographed from a slight 3/4 angle. On the plinth, dramatically lit from above: the AG1 product — a deep forest-green AG1 pouch with white "AG1" wordmark and a small clear shaker bottle of vibrant green liquid beside it. A soft warm spot-light highlight catches the top of the pouch, casting a gentle elongated shadow on the plinth surface.

Right of center, mounted on the wall at eye-level: a small white rectangular gallery placard (~22% of canvas width, ~28% of canvas height) with a thin grey border. Inside the placard, formal museum-label typography:
- Top line, small caps black serif: "[BRAND] —"
- Title line, black serif (~22pt): "AG1 NEXT GEN"
- Subtitle: "Foundational Nutrition, 2026"
- Body, small black sans-serif:
  "Daily multivitamin artifact. Composed of 75+ clinically-dosed adaptogens, vitamins, and minerals. Originally engineered to stabilize attention, energy, and mood across high-pressure 21st-century operating conditions. The single artifact replaces what was once known as 'the supplement aisle.'"
- Bottom right corner of placard, faint italic: "On loan from drinkag1.com"

Cinematic museum lighting: a soft warm pool of light around the plinth, rest of the canvas falling slightly into ambient light. The composition treats the product as art — quiet, premium, almost reverent. Photographic style is clean editorial, like a real Pace Gallery / MoMA installation shot.
```

**Note:** Both models partially garble the small placard body text. Keep it under 4 sentences and the title/subtitle will stay crisp.

**Model notes:**
- **nano-banana-pro:** strong on the gallery photo + plinth lighting. **Preferred backend** for the environment.
- **gpt-image-2:** clean for the placard typography; gallery realism slightly composited.

---

## T40 — Scratch-off ticket stat grid

**When to use:** a promo/offer ad that has to carry 4-6 hard numbers at once (feature count, language count, turnaround, price) without reading as a spec sheet. The lottery-ticket metaphor makes a stat grid feel like a prize reveal, and the unscratched sixth panel is a built-in "there's more" tease. Best for a limited-time discount or trial offer.

**Aspect ratio:** `1:1` — native on all three models.

**Reference image:** the brand's logo mark (and wordmark if it is a separate lockup). This template is a photoreal prop, not a product shot: the reference supplies the monogram that gets printed on the card and tiled inside the unscratched panel. `nano-banana-pro` picked up a circular monogram from a flat PNG and re-rendered it as printed ink on the card correctly.

**Variables:** `{brand.name}` (wordmark on the card header), `{brand.color_accent}` (hairline rules, headline, footer URL — one accent only; the rest of the card is black + silver foil), `{ad.headline}` (short all-caps promise, 3-4 words), `{serial}` (fake ticket serial, top-right), `{stat_panels[]}` (exactly 5 filled panels: an icon, a number/short value, and a 1-3 word label each — panel 4 is the offer and renders largest), `{ad.fine_print}` (two lines of legal/offer terms in caps), `{brand.url}` (footer, next to a globe icon)

**Template prompt** (fill the placeholders; validated fill below):
```
1:1 photorealistic product shot of a physical scratch-off lottery ticket.

BACKGROUND: matte black granular surface filling the frame, soft light from upper left falling off to near-black at lower right. Small silver scratch-foil flakes scattered around the card, crumbled into denser piles at the bottom-left and bottom-right corners, catching specular highlights.

SUBJECT: one square matte-black card-stock ticket lying flat, rotated 8 degrees counter-clockwise, 74% of frame width, fully visible with clear black margin on all four sides, soft contact shadow. A thin {brand.color_accent} hairline frames its inner border.

HEADER: centered {brand.color_accent} geometric-sans wordmark "{brand.name}" preceded by a small circular monogram badge. Top-right corner: small light-grey monospace serial "{serial}".

HEADLINE: under the wordmark, one line of heavy condensed italic caps in {brand.color_accent} reading "{ad.headline}", spanning nearly the full inner width, with a hand-drawn marker underline below it with uneven ends.

PANEL GRID: six rounded panels in two rows of three, each outlined by a thin {brand.color_accent} hairline. Five are scratched open — textured brushed-silver foil with scratch striations and torn edges revealing dark print:
- R1C1: small dark icon, then {stat_1_value} large in dark ink, then "{stat_1_label}" small dark bold caps.
- R1C2: small dark icon, then {stat_2_value} large in dark ink, then "{stat_2_label}" small dark bold caps.
- R1C3: small dark icon, then "{stat_3_line1}" dark caps, then "{stat_3_line2}" dark caps.
- R2C1 (wider): "{offer_value}" very large dark condensed caps, "{offer_label}" smaller dark caps below, hand-drawn dark underline.
- R2C2: small party-popper icon, then "MATCH" and "& WIN!" dark bold caps on two lines.
- R2C3: UNSCRATCHED — flat dark-grey panel, no foil, printed with a tiled 4x4 pattern of the small monogram in lighter grey.

FOOTER BAND: left, a real black-and-white barcode. Center, two lines of tiny light-grey caps: "{ad.fine_print_line1}" / "{ad.fine_print_line2}". Right, a small {brand.color_accent} globe icon then "{brand.url}" in small {brand.color_accent}.

TYPE: geometric grotesque throughout; heavy condensed italic headline, heavy panel numbers, tight small-caps labels, legible fine print.

EXCLUDE: no hands, no people, no device frames, no watermark.
```

**Example fill** (Northwind, a stand-in brand — swap in the real one):
`{brand.name}` = "Northwind" · `{brand.color_accent}` = warm cream `#EFE7D8` · `{ad.headline}` = "INSTANT WORKFLOW JACKPOT" · `{serial}` = "0000001" · panels = `40+ / TEMPLATES`, `12 / INTEGRATIONS`, `SET UP / IN 5 MINS`, offer `$1 / FIRST 7 DAYS`, `MATCH & WIN!` · fine print = "LIMITED TIME ONLY. 7-DAY TRIAL, THEN FROM $29/MO." / "CANCEL ANYTIME. TERMS APPLY." · `{brand.url}` = "northwind.example"

**Note — the numbers are the ad.** Every value in the panels is a claim in a distributable creative. Read them off the brand's own published pricing and feature pages at fill time; do not carry a number from memory and do not let the model round one for you. A stat grid is exactly the layout where an invented figure looks most authoritative.

**Note:** the accent is doing a lot of work here — one color against black and silver. A restrained brand (warm cream on black) reads as *premium foil stamping*; a saturated accent reads as *lottery kiosk*. Both are valid, they are different ads.

**Model notes:**
- **nano-banana-pro:** strong — **preferred**. Photoreal foil with real scratch striations and torn edges, correct 6-panel grid including the wider offer panel, card fully in frame with the black margin the prompt asked for.
- **gpt-image-2:** renders it legibly but takes a steeper camera angle and lets the card bleed off the left and right edges despite the always-on edge-safe suffix; the foil flattens to a uniform grey and the wider offer panel reverts to equal width. Usable as a variant, not as the primary.
- **reve-2.1:** untested — validate before using on that model.

---

## T41 — Brutalist headline over a social-post embed

**When to use:** social proof where the *proof* is a real post someone already wrote. The brutalist headline states the claim, the embedded post substantiates it, and the hand-drawn annotations keep it from reading as a corporate case study. Strong for founder-led or community-led brands.

**Aspect ratio:** `4:5` — native on all three models.

**Reference image:** the brand's wordmark and/or logo mark for the footer lockup. No product shot is needed; this template is entirely typographic.

**Requires `--allow-chrome`.** The embedded post is the creative, not a screenshot wrapper, so the always-on no-chrome suffix must be waived or the model strips the card's author row. This is the documented exception, not a workaround.

**Variables:** `{ad.headline_prefix}` (2 heavy sans words, e.g. "HOW TEAMS"), `{ad.headline_verb}` ("USE"), `{brand.name}` (rendered as the outlined script word), `{canvas.color}` (flat background hex), `{author.name}`, `{author.title}`, `{author.degree}` (e.g. "1st", "2e"), `{post_body[]}` (3-5 short paragraphs; exactly one gets a highlighter swash), `{highlight.color}`, `{brand.color_accent}` (starburst + marker annotations), `{platform_label}` (the circled callout, e.g. "on LinkedIn")

**Template prompt:**
```
4:5 vertical flat graphic ad composition, not a photograph.

BACKGROUND: flat {canvas.color} canvas, no texture or gradient.

HEADLINE: upper third, flush left, two lines with very tight leading. Line 1 "{ad.headline_prefix}" and the word "{ad.headline_verb}" on line 2 are set in an extremely heavy black condensed sans, all caps, near-black. The word "{brand.name}" follows on line 2 but is set in large hand-drawn cursive script rendered as white fill with a black outline only — wider and more playful than the sans beside it, same baseline.

ANNOTATION: just below the left end of the headline, the small handwritten marker word "By" in {brand.color_accent}, slightly tilted.

CENTER CARD: vertically centered white rounded-rectangle card with a soft shadow, inset from the canvas edges, containing a rendered professional-network post:
- Top row: small square profile photo of a person at far left; then "{author.name}" in bold dark text, a small blue-and-white verification badge, a grey dot, and grey "{author.degree}". Below the name, small grey text "{author.title}". Below that, small grey "21 h" and a small grey globe icon.
- Body: {N} short left-aligned dark-grey paragraphs in a plain UI sans, separated by blank lines:
  "{post_body_1}"
  "{post_body_2}" — this whole sentence sits on a {highlight.color} highlighter swash.
  "{post_body_3}"
  "{post_body_4}"

DECORATION: on the left edge, a solid {brand.color_accent} jagged starburst blob overlapping the card's lower-left corner, tucked behind the card.

CALLOUT: below the card on the right, the handwritten marker phrase "{platform_label}" in {brand.color_accent} tilted slightly upward, circled by a hand-drawn ellipse in the same ink.

FOOTER: bottom center, the "{brand.name}" wordmark preceded by a small monogram badge. Bottom right, a black pill-shaped outline button containing a long rightward arrow.

TYPE: two families only — ultra-heavy condensed grotesque for the headline, neutral UI sans for the card. Script word and marker notes are hand-lettered.

EXCLUDE: no photographic background, no phone or browser frame, no engagement row, no scrollbars, no nav bars.
```

**Example fill** (Northwind, a stand-in brand — swap in the real one, and see the warning below before you fill the author):
headline "HOW TEAMS / USE *Northwind*" · `{canvas.color}` = pale sand `#F3EFE7` · `{brand.color_accent}` = signal orange `#E8552D` · `{highlight.color}` = highlighter yellow `#FFE066` · author = the brand's own co-founder, "Co-founder at Northwind", 1st · body = four short paragraphs lifted verbatim from a post that founder actually published ("We shipped the thing we kept asking other people to build for us." / "Set it up once and the weekly status thread writes itself." highlighted / "No new tool to learn. It reads the boards you already keep." / "I answer every support message myself. No bots, no queue.") · callout = "on LinkedIn"

**Note — attribution is not a placeholder you may invent.** This template renders a named person with a verification badge. Fill it only with a post that person actually published, or with your own founder's words. A fabricated endorsement attributed to a real name is the one failure mode of this layout that no model will catch for you.

**Model notes:**
- **gpt-image-2:** clean — **preferred**. Closest to the source proportions, flat canvas stays flat, and the highlighter swashes land as tidy rectangles behind exactly the clause specified. The outlined script word renders with correct counter shapes.
- **nano-banana-pro:** also faithful and arguably more striking — it scales the headline and card up and tightens the margins, and renders the highlighter as a painted brush stroke rather than a flat swash. A different ad, not a worse one; pick by whether you want editorial or poster.
- **reve-2.1:** untested — validate before using on that model.

---

## T42 — Editorial testimonial card

**When to use:** the calmest social-proof layout in the library — one quote, three result bullets, one attribution. No product, no photography, no chrome. Good for a premium or B2B read, and cheap to re-fill for every customer you can quote.

**Aspect ratio:** `9:16` — native on all three models. The layout is vertically stacked with deliberate empty margins top and bottom, so it survives a `4:5` crop.

**Reference image:** brand wordmark / logo mark for the badge and footer lockup. Text-only template; no product shot needed.

**Variables:** `{brand.name}` (in the badge, lowercase with a period), `{headline.sans_clause}` (the first half of the sentence, e.g. "replaces the"), `{headline.serif_clause}` (second half, set in editorial serif italic — this is where the number or the punch goes), `{quote.body}` (one sentence, first person), `{result_bullets[]}` (exactly 3, short), `{author.name}`, `{author.title}`, `{brand.color_primary}` (badge fill), `{canvas.color}`

**Template prompt:**
```
9:16 vertical flat editorial ad composition, not a photograph.

BACKGROUND: flat {canvas.color} canvas, no texture, gradient or vignette.

HEADLINE LOCKUP: upper-middle third, horizontally centered, two lines reading as one sentence split across two typefaces:
- Line 1: a {brand.color_primary} rounded-rectangle badge holding the lowercase wordmark "{brand.name}" in a heavy sans, immediately followed on the same baseline by "{headline.sans_clause}" in medium-weight near-black neutral sans.
- Line 2: "{headline.serif_clause}" in a large editorial SERIF ITALIC, near-black, centered beneath line one.

QUOTE CARD: vertically centered white rounded-rectangle card, thin light-grey border, very soft shadow, inset from the canvas edges with generous internal padding:
- A large grey decorative opening double-quote at the top-left of the inner area.
- Left-aligned near-black neutral sans body: "{quote.body}" then a three-item bulleted list with small round dots:
  "{bullet_1}"
  "{bullet_2}"
  "{bullet_3}"
  A large grey decorative closing double-quote sits immediately after the last bullet's text.
- Below the list, an attribution pill: a smaller white rounded rectangle with a thin light-grey border holding, at left, a small square profile photo, then two stacked lines — "{author.name}" in bold dark small text with a small blue-and-white verification badge, and beneath it "{author.title}" in grey micro text. At the pill's right end, grey micro text "23h".

FOOTER: below the card, horizontally centered with generous space above and below, the "{brand.name}" wordmark preceded by a small monogram badge.

TYPE: two families plus the badge — neutral grotesque for UI and body, editorial serif italic for the second headline line. Hierarchy: headline largest, quote body medium, attribution smallest.

COMPOSITION: vertically stacked and centered — headline, card, wordmark — with large empty margins at the top and bottom. Calm, editorial, text-only.

EXCLUDE: no photographic background, no product shot, no device or browser frame, no platform nav, no engagement row, no emoji in the body.
```

**Example fill** (Northwind, a stand-in brand — swap in the real one):
badge "northwind." on ink navy `#16233A` · `{canvas.color}` = warm off-white `#F7F5F0` · sans clause "replaces the" · serif clause "Monday status meeting" · bullets "Set up in 5 minutes" / "12 integrations, one dashboard" / "$1 for the first 7 days" · `{quote.body}`, `{author.name}` and `{author.title}` = **left as placeholders on purpose** — fill them from a customer who has agreed to be quoted, and see the warning below.

**Note — never lift a testimonial from a brand's site into an ad fill without verifying the customer is real.** Marketing pages carry illustrative personas alongside genuine customers and rarely label which is which; a quote that is fine as landing-page copy becomes an advertising claim about a named individual the moment it lands in a creative. Get the name, the title and the sentence from someone you can point to. Same attribution warning as T41: only quote people who actually said it.

**Note:** the split-typeface headline is the whole idea — the sans clause sets up, the serif italic clause lands. Put the number in the serif half.

**Model notes:**
- **gpt-image-2:** clean — **preferred**. Card proportions and serif-italic weight are closest to the reference, and the three bullets stay on three lines.
- **nano-banana-pro:** faithful too, with a smaller card and more negative space around it — reads more like a print ad than a social card. Both are shippable; this one crops better to `4:5`.
- **reve-2.1:** untested — validate before using on that model.

---

## Adding new templates

When a new ad reference is worth turning into a template, use the `clone-image-ad-*` skill (one per model — chatgpt or nano-banana) to:

1. Generate a faithful reproduction with `--image-ref` set to the original reference (round 1).
2. Strip the chrome from the prompt and re-run (round 2) — verify the standalone creative still reads correctly.
3. Identify what's brand-specific vs. structural; replace brand-specific bits with `{placeholder}` variables.
4. Write a brand example fill against a different brand to verify the template generalizes.
5. Test against **both** target models and write a `Model notes` line for each — say where each shines, where each struggles.
6. Append the section to this file with: when-to-use, aspect ratio, reference image guidance, variable schema, template prompt, example fill, model notes, and path to the validated example.

## Known rendering limits (mitigated by always-on suffixes)

- **Dense small text still garbles** even with the glyph-safety suffix — true on both gpt-image-2 and nano-banana, especially in chat bubbles, table rows, calendar blocks, ChatGPT responses. Keep body-text blocks SPARSE — 3-4 short lines max for chat/response bubbles, large readable size. The fix is fewer words, not more rules.
- **Reference image bleeds.** When the reference is a product hero, the model sometimes draws extra product shots into negative space even when not requested. Usually harmless; constrain with "NO additional product shots beyond the one described" if it's a problem.
- **Tall content + 1:1 canvas = clipping.** Even with `SAFE_ZONE_SUFFIX`, a held-up board / letter sign / portrait product really benefits from a tall aspect ratio (`2:3` or `9:16`). Pick the canvas to match the focal subject's proportions.

**Solved by the always-on suffixes (no longer need to call out per template):**
- ~~iOS chrome / Sponsored badges / engagement rows leak in~~ — handled by `NO_CHROME_SUFFIX`
- ~~Headlines clipping at edges~~ — handled by `SAFE_ZONE_SUFFIX`
- ~~Emoji in chat bubbles becomes glyph soup~~ — handled by `GLYPH_SAFETY_SUFFIX`
- ~~Phantom 3rd comment / extra Slack message appears~~ — handled by `GLYPH_SAFETY_SUFFIX` count constraint
