# Brand voice starter (copy into MASTER_CONTEXT.md)

Replace the placeholders with your real brand rules. Agents read `MASTER_CONTEXT.md` first when it exists.

## Brand

- **Name:** {{BRAND_NAME}}
- **One-liner:** {{WHAT_YOU_SELL}}
- **Tone:** e.g. direct, warm, playful, clinical — {{TONE}}
- **Words we use:** {{PREFERRED_TERMS}}
- **Words we avoid:** {{BANNED_TERMS}}

## Audience

- **Primary:** {{AUDIENCE}}
- **Objection to address:** {{OBJECTION}}

## Creative defaults

- **Aspect ratio:** {{9_16_OR_16_9}} — Seedance also takes `1:1`, `4:3`, `3:4` and `21:9`; `omni-flash` takes `9:16` or `16:9` only
- **Language:** {{EN_ES_PT_OR_OTHER}} — the language ads are written and rendered in
- **Typical length:** {{SECONDS}} — `seedance-2.0` and mini render any integer 4–15s, `seedance-2.5` any integer 4–30s, `omni-flash` only 4, 6, 8 or 10
- **Default video model:** {{SEEDANCE_2_0_OR_MINI}} — mini is half price for drafts
- **Default product:** {{PRODUCT_NAME_AND_ID}} — from `GET /v1/products`
- **On-screen CTA style:** {{CTA_STYLE}}

**No prices here.** Credit costs come from a live `POST /v1/estimates` in the session that spends them, never from a stored table.

## Reference prompts that worked

_Add dated bullets as you learn what these models return for your account._

- YYYY-MM-DD — {{SHORT_NOTE}} — model: {{MODEL}} — prompt: "…"
