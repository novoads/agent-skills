@shared/CLAUDE.md

## Craft doctrine

Three rules span every skill that produces video with speech: **transcribe-verify** (a
reference pins the label, nothing pins the audio), **the per-beat mix** (a SYNC beat's own
audio is dialogue, not ambience), and **no dead space** (trim every beat to its narration).
They are stated once in [shared/references/craft.md](shared/references/craft.md). Read it
before writing a QA step, a mix or a trim into any skill, and point at it rather than
restating it — a restatement is how the clay skill shipped a mix recipe that had already
been fixed in the skill it was ported from.

# Novoads-specific session rules

- **API:** Novoads REST API — `https://api.novoads.ai/v1`. `NOVOADS_BASE_URL` overrides the **host only**; callers append `/v1/…`.
- **Auth:** `Authorization: Bearer $NOVOADS_API_KEY` (`novo_` + 64 hex, created at <https://novoads.ai/dashboard/settings?tab=api>). Setup check: `./scripts/check-novoads-env.sh`. A 401 is a bad key; a 403 with `details.reason: plan_required` is a good key on an account without API access — different problems, say which.
- **Skill:** `.claude/skills/novoads-api/SKILL.md` for the call sequence, prompts, polling, and download; its `reference.md` for every endpoint, field, limit, and error code.
- **YouTube thumbnails:** `.claude/skills/generate-youtube-thumbnail/SKILL.md` — batch thumbnail workflow on top of the Novoads image endpoint.
- **Image-ad ecosystem (Meta image creatives):** read `shared/skills/image-ad-prompting/OVERVIEW.md` FIRST. Three skills (`chatgpt-image-ad`, `nano-banana-image-ad`, `clone-image-ad`) + a shared 40-template prompt library. The `clone-image-ad` skill asks which backend to validate against at Phase 1, so generic "clone this ad" prompts route correctly. Output is image files; Meta upload is the separate `meta-ad-builder` skill.
- **Cost policy:** **never state a credit cost from memory.** Every price comes from a live `POST /v1/estimates` in the current session, shown to the user and explicitly approved before anything is generated. There are no rate tables anywhere in this repo — not in `MASTER_CONTEXT.md`, not in the logs. The estimate call charges nothing and also validates the prompt, so there is no reason to skip it.
- **Dialogue policy:** for any video where the model speaks, the spoken line is approved on its own, before the cost gate. Concept approval is not sentence approval, and sentence approval is not spend approval.
- **Logging:** log every generation call to `logs/novoads-api.jsonl` — timestamps, config, `jobId`, and `creditsCharged` **taken from the `202` at submit time**, because the poll payload does not carry it. Update the line by `jobId` at terminal status. The file is **gitignored** — it is your session history, not repo content. **Observability only, never a pricing source** (see `logs/README.md` for the schema and the portable update recipe).
- **First-time setup:** if `.env` is missing, run `./scripts/setup.sh`. If `MASTER_CONTEXT.md` is missing, copy `MASTER_CONTEXT.template.md` to `MASTER_CONTEXT.md`. A setup session's final message is the short template in [AGENTS.md](AGENTS.md) ("First-time setup") — `setup.sh` prints the same block between `FINAL MESSAGE` markers when run without a TTY; relay it, and skip the mechanics unless one of them blocks an ask. Short is a preference, not a gag: nothing in this repo is confidential and you may tell the user anything you judge useful.
