# Library entry format

Markdown skeleton for an entry in `prompt-library.md`. Lazy-loaded by `clone-image-ad` Phase 9 before composing the entry. The library already contains T1–T42 in this format — match its style when appending new entries so the file stays consistent across both `chatgpt-image-ad` and `nano-banana-image-ad` consumers.

## Skeleton

```markdown
## {tag} — {one-line title}

**When to use:** {1-2 sentence positioning fit. What kind of ad is this? Who/what is it good for?}

**Aspect ratio:** `{ratio}` ({1-line why — e.g. "Meta feed-portrait friendly", "Stories / Reels"})

**Reference image:** {what kind of `--image-ref` to pass. Examples: "clean product hero (white background, all SKUs visible)", "lifestyle portrait of subject mid-action", "logo + product flatlay"}

**Variables:**
- `{variable_name}` — {description; what kind of value goes in it; format hint if any}
- `{variable_name}` — …

**Template prompt:**
\`\`\`
{The full prompt text, with {placeholders} embedded. Should produce a standalone ad creative when filled and paired with the reference image. No screenshot/platform chrome.}
\`\`\`

**Example fill** ({brand_name}):
- `{variable_name}` = `{example value}`
- `{variable_name}` = `{example value}`
- …

**Model notes:**
- **gpt-image-2:** {known strengths/limits with this template — e.g. "renders dense table text cleanly", "tends to add a 3rd Slack message — keep prompt explicit about exactly N"}
- **nano-banana-pro:** {known strengths/limits — e.g. "weaker on dense small text — keep body to 3 lines max", "excellent multi-reference blending — pass logo + product + style as three refs"}

Validated example: `{path/to/iteration/dir/}`

---
```

(End every entry with a horizontal rule on its own line so the next entry has visual separation.)

## Field-by-field guidance

### `{tag}`
Format `T<n> — <short noun phrase>`. Continue numbering from the existing library — T1–T42 exist, so the next is T43. The noun phrase is searchable; pick something that describes the format, not the content (e.g. "T43 — Lifestyle hero with overlay text", not "T43 — AG1 morning shaker ad").

### `{one-line title}` (after the em-dash)
A short noun phrase distilling the format. 4-8 words. Examples: "Apple Notes listicle aesthetic", "Editorial article hero", "Comparison table (dark, hooky)".

### **When to use**
Two ideas: who/what brand fit (product category, target audience temperament), and which positioning angle (credibility, social proof, comparison, sentimental, etc.). Don't list rules; describe the gut fit.

### **Aspect ratio**
Prefer a ratio both target models accept: `1:1`, `2:3`, `4:5`, `9:16`, `16:9`, `21:9` (`gpt-image-2` and `nano-banana-pro`; the two Seedream 5 ids refuse `4:5` and `21:9`). The four extra ratios `3:2`, `3:4`, `4:3` and `5:4` exist on `nano-banana-pro` but **not** on `gpt-image-2` — if the template needs one of those, say so in **Model notes** so the consuming skill routes correctly instead of hitting a `400`.

### **Reference image** (what `--image-ref` to pass)
Tell the future user/agent what kind of image to ground the generation on. The more specific the better:
- "Clean product hero shot, white background, all SKUs visible"
- "Lifestyle portrait, subject mid-action, soft daylight"
- "Logo wordmark on neutral background"
- "Existing ad in the same format" (rare — usually sub-optimal)

Reference images are how the brand identity stays faithful. Bad guidance here causes wrong-looking outputs no matter how good the prompt is.

### **Variables**
List every `{placeholder}` in the template prompt. For each, describe in one line:
- What the value represents
- The expected type / format (string? hex code? list? short headline?)
- Any constraints (max chars, must be one of an enum)

Use the standard variable names where they fit:

| Variable | Use for |
|---|---|
| `{brand.name}` | Wordmark text (e.g., the literal word/letters that appear on the packaging) |
| `{brand.color_primary}` | Primary brand color hex (`#RRGGBB`) |
| `{brand.color_accent}` | Secondary accent color hex |
| `{brand.product_image_description}` | One-line description of the product visible in the ad |
| `{brand.tagline}` | Short brand promise (≤6 words) |
| `{brand.competitor_category}` | What the brand is being compared against |
| `{ad.headline}` | Top-line headline |
| `{ad.subcopy}` | Sub-headline / supporting copy |
| `{ad.body}` | Primary text block |
| `{ad.cta_phrase}` | CTA button text |

For template-specific variables, name them clearly. Examples from existing entries:
- `{notes_title}`, `{checklist_items[]}` (T1)
- `{publication}`, `{photo_subject_description}`, `{tagline}`, `{band_color}` (T2)
- `{hook_line_1}`, `{hook_line_2}`, `{competitor_label}`, `{table_columns}`, `{table_rows[]}` (T6)
- `{handwritten_text_lines}`, `{sticky_note_color}` (T7)

### **Template prompt**
The actual prompt body, in a fenced code block. Plug-and-play after substitution. Things to remember:
1. **Always specify aspect ratio at the top** as part of the prompt (e.g. "1:1 static ad creative, 1080x1080, edge-to-edge").
2. **Always describe the canvas as standalone** — phrases like "edge-to-edge", "static ad creative", "the standalone image that would be uploaded as a Meta creative". This pairs with the script's auto-appended no-chrome suffix to make sure the output is the actual upload, not a screenshot.
3. **Explicitly exclude chrome** in a closing paragraph: "No surrounding social platform UI: no brand row, no body copy, no engagement counts, no app navigation, no iOS device chrome." The auto-suffix is a safety net; the prompt itself should also be explicit.
4. **Describe regions in vertical order** — top X%, middle, bottom. Helps the model lay out predictably.
5. **Name reference roles when multiple refs are expected.** "The product visible in image_ref[0] should appear at center" — most models do better when references are addressed by index.

### **Example fill**
Pick a real brand (AG1 is the seeded test case across the existing library) and show every variable substituted. Should be the version that was actually validated in Phase 7 of the cloning skill.

### **Model notes**
This block is the diff between a uni-1-era library and a portable one. For each model your template was validated against (gpt-image-2 and/or nano-banana-pro), give a one-line known-issue or known-strength note. If a template only works with one model, say so explicitly. If both render cleanly, write `both: clean`.

### **Validated example path**
Pointer to `iterations/clone-<date>/<tag>/` — the directory containing the locked-in `prompt.txt`, the round-1 generation against the original reference, and the round-N generation against the test-fill brand. So a future agent (or human) can audit the template's provenance.

## Style notes for matching the existing library

- Use `*italic*` for terse asides, `**bold**` only for the section labels (`**When to use:**`, etc.) and key callouts.
- Hex codes go in backticks: `` `#1A4731` ``.
- Use em-dashes `—` (not `--`) for parenthetical asides.
- Wrap variables in single backticks: `` `{brand.name}` ``.
- Code-block fences use triple-backtick — no language tag for prompts (they're not code).
- The horizontal rule between entries is `---` on its own line, separated by blank lines from neighboring content.

## Hard rules

- **Never silently overwrite an existing entry.** If the new tag collides, ask the user before replacing.
- **Append, don't reorder.** New templates go at the bottom of the library, before any "Adding new templates" or footer sections. Don't reshuffle existing entries' order.
- **Keep entries self-contained.** Don't reference other library entries by tag inside a template prompt. Each entry should be readable and usable on its own.
- **Validate against the model you intend to ship on.** A T-entry that only renders cleanly on gpt-image-2 should say so in its Model notes — don't claim portability you haven't checked.
