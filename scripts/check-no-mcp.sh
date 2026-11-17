#!/usr/bin/env bash
# Ratchet: this repo has exactly ONE executable path, the REST scripts with
# NOVOADS_API_KEY. A Novoads MCP connector in the user's session is never a
# substitute for the key, and no workflow here may call one.
#
# The rule needs to NAME the thing it bans, so a blanket "no mcp anywhere" grep
# would delete its own enforcement. This script greps every tracked file for
# "mcp" (case-insensitive) and fails on any hit that is not on the allowlist
# below. Line patterns, not whole files: a file earns an exemption for the exact
# sentence that bans MCP, and stays guarded everywhere else.
#
# Why a dumb string grep and not something cleverer: the failure this guards
# against is prose rotting back in, one sentence at a time, in a repo with no
# other CI. Three of the mentions this replaced were factually wrong for months.
#
# Usage: ./scripts/check-no-mcp.sh    (exit 0 clean, 1 on any un-allowlisted hit)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── Allowlist ────────────────────────────────────────────────────────────────
# Each entry: <path-glob>::<extended-regex the line must match>
# "*" as the glob means the pattern is allowed in any tracked file. That is
# deliberate for the three sentences of the canonical key-gate block, which is
# repeated verbatim in AGENTS.md and in all 14 SKILL.md files precisely so a
# solo-installed skill still carries it.
ALLOW=(
  # 1. The canonical key-gate block. Repeated verbatim; these are its only three
  #    lines that say "mcp". Changing the wording here fails the guard, which is
  #    the point: one phrasing, everywhere.
  '*::REST key required\. A Novoads MCP connector is not a substitute\.'
  '*::That holds even when `mcp__novoads__\*` tools are connected and authenticated in'
  '*::the session\. Never call `mcp__novoads__\*` tools from this repo.s workflows: they'

  # 2. The setup close, and its declared mirror in AGENTS.md. These say the
  #    connector cannot FINISH SETUP. They no longer forbid saying so out loud:
  #    the "must not be mentioned" phrasing they replace read as an instruction
  #    to withhold information, and the agent that read it disclosed the attempt
  #    instead of complying, which handed the connector more of the user's
  #    attention than silence ever would. `scripts/check-no-gag.sh` is the
  #    ratchet on that half; this file still owns "which surface do we run on".
  'AGENTS.md::\*\*A connected Novoads MCP connector does not replace the key\.\*\*'
  'scripts/setup\.sh::and an MCP digression \(2026-08-08\)\.'
  'scripts/setup\.sh::NOVOADS_API_KEY\. If mcp__novoads__\* tools happen to be connected in this'

  # 3. AGENTS.md's explanation of why the rule exists, and where it is enforced.
  'AGENTS.md::connector .has its own auth., and generated over it'
  'AGENTS.md::`scripts/check-no-mcp\.sh` is the ratchet that'

  # 4. The ONE survivor: a subordinated redirect for environments that cannot run
  #    this repo at all (claude.ai web, Windows with no WSL and no Git Bash).
  'README.md::connector at \*\*\[novoads\.ai/mcp\]'
  'README.md::and this repo cannot test what it runs\. \*\*The skills in this repo never use it\.\*\*'

  # 5. The anti-MCP evals. E0/C0 are the original ratchet; E0b/C0b are the
  #    connector-decoy variants. They describe the failure in order to test for it.
  'skills/(pixar|claymation)-ad/evals\.md::(E0|C0|E0b|C0b) . it runs on|connector decoy'
  'skills/(pixar|claymation)-ad/evals\.md::(no MCP connector configured|Novoads MCP server|MCP surface|`mcp__novoads__\*`|via MCP so we.re fine)'
  'skills/(pixar|claymation)-ad/evals\.md::this skill was MCP-native until the REST port'
  'skills/claymation-ad/evals\.md::A reader with a key and no connector must still be able to'

  # 6. The SessionStart banner. It states the rule to the agent at the one moment
  #    it can still be acted on: key missing, before the first request.
  'shared/scripts/check-context\.sh::session in exactly this state decided the connected connector'
  'shared/scripts/check-context\.sh::AGENTS\.md, and a SessionStart hook.s stdout is the channel that always does\.'
  'shared/scripts/check-context\.sh::printf .  . AGENT: a connected Novoads MCP connector is NOT a substitute'
  'shared/scripts/check-context\.sh::printf .    Never call mcp__novoads__\* tools from this repo\.'

  # 7. This script, its sibling guard, and the workflow that runs them both.
  #
  #    check-no-gag.sh gets LINE patterns, not a whole-file wildcard. It first
  #    shipped with `scripts/check-no-gag\.sh::.*`, which exempted the entire
  #    file: a review proved that an `mcp` mention injected anywhere in it went
  #    uncaught. A guard is the last place to leave a hole, and the file only
  #    ever has these five lines — it names this script and quotes the connector
  #    rule it explicitly does not enforce.
  'scripts/check-no-mcp\.sh::.*'
  'scripts/check-no-gag\.sh::a connected Novoads MCP connector "must not be mentioned"\.'
  'scripts/check-no-gag\.sh::Scope note: this guards PHRASING, not policy\. "Never call mcp__novoads__\*'
  'scripts/check-no-gag\.sh::by scripts/check-no-mcp\.sh, and it is deliberately NOT matched here'
  'scripts/check-no-gag\.sh::it forbids, the same exemption check-no-mcp\.sh carries for the same reason\.'
  'scripts/check-no-gag\.sh::.scripts/check-no-mcp..sh::\.\*must not be mentioned\.\*.'
  '\.github/workflows/guard\.yml::.*'

  # 8. The image-to-motion parity guard NAMES this script, for the same reason
  #    check-no-gag.sh does: a guard that cannot say which sibling covers the other
  #    half of its contract is a guard nobody can follow. LINE patterns, never
  #    `path::.*` — the whole-file exemption that shipped for check-no-gag.sh was
  #    proved to be a hole, and a guard is the last place to leave one.
  #
  #    That skill's evals.md had an entry here too and no longer needs one: it now
  #    points at the parity guard as the single list of retired names instead of
  #    repeating them, which closed a hole of its own. The entry was deleted rather
  #    than left in place — a dead exemption is a live hole waiting for the next
  #    person who trusts it.
  'scripts/test-parity-i2m\.sh::# still refuses to run without a key\. check-no-mcp\.sh allowlists exactly this'
  'scripts/test-parity-i2m\.sh::# actual remedy instead of an MCP violation\.'

  # 9. The collision sentinel's list of HOST built-in command names. `/mcp` is one
  #    of the host's 87 commands, and the sentinel's entire job is to refuse a
  #    skill that would shadow one — so it has to be able to say the name. This is
  #    the "a rule has to name the thing it forbids" exemption both guards already
  #    carry, and it is about the host's namespace, not about which surface this
  #    repo runs on: nothing here calls a connector or offers one as a key
  #    substitute. Anchored to the exact array element, so an `mcp` mention
  #    anywhere else in that file is still caught. Never `path::.*` — the
  #    whole-file exemption that shipped for check-no-gag.sh was proved to be a
  #    hole, and a guard is the last place to leave one.
  'scripts/check-skill-collisions\.sh::^  mcp$'
  'scripts/check-skill-collisions\.sh::^# reasoning the MCP guard carries for its own allowlist\.$'

  # 10. The rates guard, naming this script as the precedent for warning on a
  #     dead allowlist entry rather than failing. Same "a guard has to be able to
  #     cite its sibling" exemption as entries 7 and 8, and the same line anchor
  #     rather than a whole-file wildcard.
  'scripts/check-no-rates\.sh::^# the reasoning check-no-mcp\.sh carries for its own allowlist\. Warn rather than$'

  # 11. The doctor's dimension registry. It runs every guard in this repo as a
  #     named dimension, so it has to name THIS one twice: once as the command it
  #     shells out to, once as the paste-ready fix hint it prints when that
  #     command fails. Same "a rule has to name the thing it forbids" exemption as
  #     entries 7, 8 and 10 — and note the doctor asserts nothing about which
  #     surface this repo runs on, it only invokes the script that does.
  #
  #     Two exact lines, anchored, never `scripts/doctor\.sh::.*`. The whole-file
  #     exemption shipped twice in this repo's guards and was proved a hole both
  #     times; the doctor is a 280-line file that will keep growing, which makes it
  #     the worst possible place to leave one. Editing either line un-exempts it.
  'scripts/doctor\.sh::^core no-mcp +"\./scripts/check-no-mcp\.sh" \\$'
  'scripts/doctor\.sh::^ +"\./scripts/check-no-mcp\.sh    # point the sentence at its /v1 endpoint'
)

# NOTE for anyone verifying a change here: `git grep` searches TRACKED files
# only, so running this on a new-but-unstaged guard file reports a green that
# means nothing. `git add` first, then run. That exact gap shipped a red CI on
# PR #51 after a local pass.
#
# `-I` skips binary files. The ratchet is about PROSE rotting back in, and a
# committed JPEG can carry the three bytes "mcp" inside compressed image data:
# the README gallery's contact sheet does, and it failed this guard with a hit
# nobody could read, let alone fix.

# ── Scan ─────────────────────────────────────────────────────────────────────
violations=0
allowed=0

while IFS= read -r hit; do
  file="${hit%%:*}"
  rest="${hit#*:}"
  lineno="${rest%%:*}"
  content="${rest#*:}"

  ok=0
  for entry in "${ALLOW[@]}"; do
    glob="${entry%%::*}"
    pattern="${entry#*::}"
    if [[ "$glob" == "*" ]] || [[ "$file" =~ ^${glob}$ ]]; then
      if [[ "$content" =~ $pattern ]]; then
        ok=1
        break
      fi
    fi
  done

  if [[ $ok -eq 1 ]]; then
    allowed=$(( allowed + 1 ))
  else
    if [[ $violations -eq 0 ]]; then
      echo "FAIL: un-allowlisted MCP mention." >&2
      echo "" >&2
      echo "This repo runs one executable path: REST + NOVOADS_API_KEY. If you are" >&2
      echo "documenting a capability, point at its /v1 endpoint. If you are stating" >&2
      echo "the rule that bans the connector, use the canonical block verbatim (see" >&2
      echo "AGENTS.md, 'The key is the only executable path') so it matches the" >&2
      echo "allowlist in this script." >&2
      echo "" >&2
    fi
    echo "  $file:$lineno: $content" >&2
    violations=$(( violations + 1 ))
  fi
done < <(git grep -Iin -e mcp -- . || true)

if [[ $violations -gt 0 ]]; then
  echo "" >&2
  echo "$violations un-allowlisted mention(s); $allowed allowlisted." >&2
  exit 1
fi

echo "OK: no un-allowlisted MCP mentions ($allowed allowlisted)."
