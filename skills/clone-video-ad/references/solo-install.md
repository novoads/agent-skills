# clone-video-ad — installed without the rest of the pack

Read this only if `shared/` is missing from disk. Nothing here is needed during a clone that
runs inside the full pack.

## What is missing, and where to get it

Then `novoads-api` was installed on its own from skills.sh and the rest of the pack stayed behind.
Everything under `skills/novoads-api/` still travels with you; what is gone is
`shared/references/craft.md` (the doctrine step 3's transcript diff cites) and the
`caption-video` skill, which is the out-of-band caption burn and lives across
`shared/skills/caption-video/SKILL.md` plus `shared/skills/caption-video/prompting/guide.md`. Fetch any of
those from `https://raw.githubusercontent.com/novoads/agent-skills/main/<path>`. The b-roll overlay step is
a folder of scripts rather than one file and only exists in the full pack, so reach it with
`git clone https://github.com/novoads/agent-skills.git`. `scripts/check-novoads-env.sh` and
`MASTER_CONTEXT.md` are absent too: set `NOVOADS_API_KEY` in the environment yourself, and ask the
user for brand voice and product instead of reading it.

## The shot route needs this skill's `scripts/`

The shot-by-shot route (`references/shot-by-shot.md`) runs `shot_table.py`, `pace.py` and
`assemble.py` from the skill's own `scripts/` directory, which must sit beside `SKILL.md`. An
install that copied only `SKILL.md` and `references/` lacks them: copy `skills/clone-video-ad/scripts/`
from the same raw URL or the clone above. Their commands are written from the pack root
(`python3 skills/clone-video-ad/scripts/<name>.py`); outside the pack, point them at wherever
that directory landed. The single render needs none of them.

