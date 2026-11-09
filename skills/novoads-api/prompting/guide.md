# Creative brief playbook

Use this **before** opening a formula in `prompting/prompt-library/`. It turns a marketing intent into the one paragraph the model actually reads.

## 1. Capture the intent (ask the user)

- **Audience:** who is this for? One sentence.
- **Job to be done:** what should the viewer feel or do after watching?
- **Offer / proof:** product name, one concrete benefit, optional social proof.
- **Hook:** the first 1–2 seconds — pattern interrupt, curiosity, or a relatable moment.
- **CTA:** the exact words, if spoken or on screen ("Shop the drop", "Book a demo").
- **Constraints:** length, aspect ratio, banned topics, brand words to avoid.
- **Language:** the language the ad ships in. Write the prompt in it; do not translate a Spanish ad into English.

Check `references/` at the repo root before asking for anything visual. Product shots, actor stills and style boards live there (`references/products/`, `references/influencers/`, `references/aesthetics/`), it is gitignored, and a file already sitting in it beats a file you asked for twice.

## 2. Turn the intent into one coherent prompt

- Prefer **one paragraph** of clear direction over a bag of keywords. Bullets and `Label: value` pairs come back rendered as literal on-screen text.
- Name the **subject**, **setting and light source**, **camera and motion**, **style**, and — for video — the **spoken line in double quotes**. The video model renders the dialogue and lip-sync in the same call, so the line is part of the prompt, not a later step.
- If the user gave a vague adjective ("premium", "fun"), **translate it into visual specifics**: materials, wardrobe, location, pace, the actual light source.
- Real brands only. Never substitute a blank or unbranded stand-in for a product the user has not shown you: the API will render and bill it, and the most you get is a `blank_label` warning on an image estimate. Ask for the photo instead.

## 3. Map the brief to a route

1. Pick the route from the decision tree in [SKILL.md](../SKILL.md); field-level detail is in [reference.md](../reference.md).
2. Open the matching formula and follow it:
   - Video, Seedance: [seedance-2.md](prompt-library/seedance-2.md) for the platform rules, then [ugc](prompt-library/seedance-2-ugc.md), [premium reveal](prompt-library/seedance-2-premium-reveal.md), [product hero](prompt-library/seedance-2-product-hero.md), [studio lookbook](prompt-library/seedance-2-studio-lookbook.md), or [feature walkthrough](prompt-library/seedance-2-feature-walkthrough.md).
   - Video, someone talking on camera, or a fast vertical clip with a long prompt: `omni-flash`, guided by `shared/skills/gemini-omni-flash/prompting/guide.md`.
   - Image: `shared/skills/image-ad-prompting/OVERVIEW.md` routes between `gpt-image-2` and `nano-banana-pro`.
3. Resolve `productId` once per session from `GET /v1/products` — the list comes back under **`.items`**, not `.products` (verified live 2026-08-04). Default to the product named in `MASTER_CONTEXT.md`. It is optional, and it is what makes `GET /v1/generations?productId=…` a useful history later. There are no projects or scripts on this API, and folders are read-only.
4. Upload each reference image once with `POST /v1/uploads`. The `assetId` can be reused across calls and models: re-uploading the same bytes only mints a second id for the same picture.

## 4. Merge with project memory

If `MASTER_CONTEXT.md` at the repo root carries brand voice, banned phrases, or prompts that worked, **prefer those** over the generic templates. It carries no prices — that is deliberate.

## 5. Quality check before sending

- [ ] Required fields present for the chosen model, per [reference.md](../reference.md) — and nothing extra: the request bodies are strict and an unknown key is a `400`.
- [ ] `durationSeconds` and `aspectRatio` set explicitly. The defaults differ by model (on `seedance-2.0`, 5 seconds and `16:9`) and are almost never what an ad wants.
- [ ] One reference mode only: `startImageAssetId` **or** `referenceAssetIds`, never both. Every `@ImageN` token points at an id you actually send.
- [ ] The prompt matches the formula's structure, in the ad's own language.
- [ ] No secrets in the request body — ids and creative text only.
- [ ] **Priced live** at `POST /v1/estimates` in this session, the number shown to the user, and the user said yes. Never quote a credit number from memory, from the logs, or from `MASTER_CONTEXT.md`.
- [ ] For any video where someone speaks: the spoken line approved on its own first, per gate 1 in [SKILL.md](../SKILL.md).
