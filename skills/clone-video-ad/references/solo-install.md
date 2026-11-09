# clone-video-ad — installed without the rest of the pack

Read this only if `shared/` is missing from disk. Nothing here is needed during a clone that
runs inside the full pack.

## What is missing, and where to get it

Then `novoads-api` was installed on its own from skills.sh and the rest of the pack stayed behind.
Everything under `skills/novoads-api/` still travels with you; what is gone is
`shared/references/craft.md` (the doctrine step 3's transcript diff cites) and the
`caption-video` skill, which is the out-of-band caption burn and lives across
`shared/skills/caption-video/SKILL.md` plus `shared/skills/caption-video/prompting/guide.md`, and the Omni
guide, `shared/skills/gemini-omni-flash/prompting/guide.md`, whose *A scene where someone talks* a talking
clip follows. Fetch any of
those from `https://raw.githubusercontent.com/novoads/agent-skills/main/<path>`. The b-roll overlay step is
a folder of scripts rather than one file and only exists in the full pack, so reach it with
`git clone https://github.com/novoads/agent-skills.git`. `scripts/check-novoads-env.sh` and
`MASTER_CONTEXT.md` are absent too: set `NOVOADS_API_KEY` in the environment yourself, and ask the
user for brand voice and product instead of reading it.

