# Universal safety suffixes (auto-appended to every image-ad prompt)

Every generation script in the image-ad family (`chatgpt-image-ad`, `nano-banana-image-ad`) auto-appends three always-on guard suffixes to the user-supplied prompt. They are model-agnostic — they fix rendering failures that surface across **every** modern image model when generating static social-ad creatives.

You do **not** need to repeat these constraints in your prompt library entries. The script handles them.

---

## 1. `NO_CHROME_SUFFIX` — strip platform/screenshot UI

Auto-appended unless `--allow-chrome` is passed. Forces the output to be the **standalone ad creative** (the static image an advertiser uploads), not a screenshot of how the ad displays in-feed.

```
[NO PLATFORM CHROME] Render only the standalone ad creative (the static image uploaded to Meta),
not a screenshot of how it displays in-feed. Exclude: iOS device chrome (status bar, home indicator);
platform brand-row above the ad (avatar + handle + Sponsored / Saved label); post body / caption text;
link-card footer (URL + headline + button); engagement rows (likes / comments / shares counts,
Followed-by, View comments); action buttons (Like / Comment / Share / Save); comment input boxes;
platform tab/nav bars (Instagram, Facebook, Twitter); Story chrome (progress bars, story header,
swipe-up arrows). Just the standalone image.
```

**When to override (`--allow-chrome`):** rare. Use only when the ad's concept *requires* simulated platform chrome — e.g. a screen-recording-style UGC ad that mimics a Reels view. The chrome then becomes part of the creative on purpose.

---

## 2. `SAFE_ZONE_SUFFIX` — keep text and focal subjects in the central 84%

On by default; `--no-safe-zone` waives it for one run. Solves the "headline clipped at the edge" failure mode.

```
[EDGE-SAFE] All text, headlines, CTAs, table headers, sign/board content, product wordmarks, and
key focal subjects must fit within the central 84% of the canvas (~8% padding from every edge).
Backgrounds and divider lines may bleed; text and focal elements may NOT touch or extend off any edge.
If a tall focal subject doesn't fit at the requested aspect ratio, scale it DOWN — never crop a
headline, never let text run off-frame, never cut off the top/bottom of a sign, board, or product.
```

---

## 3. `GLYPH_SAFETY_SUFFIX` — no emoji or unicode garbage inside body-text blocks

Always on. Solves the "exactly 2 comments turned into 3" + "chat bubble emoji becomes glyph soup" failure modes.

```
[TEXT FIDELITY] Inside body-text blocks (chat bubbles, message threads, comment text, ChatGPT
responses, dense paragraphs): plain words only — NO emoji, NO unicode glyphs, NO special characters
mid-sentence. Emoji OK in headlines and short large-text positions where the prompt explicitly calls
for them. Render the EXACT count of conversation elements the prompt specifies — do not invent
additional comments, messages, replies, or responses.
```

---

## Why all three are on by default

- They fix actual, recurring rendering failures observed across uni-1, gpt-image-2, and Nano Banana.
- The total guard text is ~1,575 chars — well below every model's prompt cap.
- None of them constrain creative choice; they only constrain what the model wasn't supposed to be drawing in the first place.

If you find a model that struggles with one of these (e.g. follows the guard so literally that the layout becomes stiff), pass `--no-safe-zone` or `--allow-chrome` to opt out per-run. Do not silently remove them from the script.
