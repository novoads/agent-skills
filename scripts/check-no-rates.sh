#!/usr/bin/env bash
# Ratchet: a skill file may describe the METER. It may not state the RATE.
#
# The failure this exists for, which has now happened in both repos: someone
# writes "0.4 credits per billed minute" into a skill file because it was true
# the day they measured it. The agent reads that file at spend time, quotes the
# number to the user, and takes the money. When the price moves, nothing goes
# red — the file still parses, every test still passes, every link still
# resolves — and the skill keeps quoting a figure that stopped being true. The
# user is told one price and charged another, by a document that was correct
# when it was written.
#
# It is not fixed by "keeping the numbers up to date". Nothing can tell you a
# rate rotted; that is the whole problem. It is fixed by never writing the rate
# down: every one of these endpoints has a `POST /v1/estimates` arm, charging nothing, whose
# entire job is to answer this question at the moment it is asked. Quote the
# tool at spend, not the file.
#
# A rate kept "as rationale" still gets quoted, so this catches those too. What
# it deliberately does NOT catch is the meter's SHAPE — "per minute of source,
# rounded up, one-minute minimum", "flat per call, whatever comes back", "the
# stills are a fraction of the clips". That is durable behaviour and ordering,
# it is what a reader actually needs, and it is exactly what should survive the
# rewrite when this guard fires.
#
# Fenced code blocks are skipped, the same precedent check-links.sh sets. A
# A fenced json block showing what `POST /v1/estimates` RETURNS is documentation of
# response shape, not a price list — and its numbers are illustrative by
# construction, because the endpoint's whole purpose is to replace them.
#
# Usage: ./scripts/check-no-rates.sh   (exit 0 clean, 1 on any un-allowlisted hit)
set -uo pipefail
cd "$(dirname "$0")/.."

# ── Allowlist ────────────────────────────────────────────────────────────────
# Each entry: <path-regex>::<extended-regex the line must match>
#
# LINE patterns, never `<path>::.*`. A whole-file exemption shipped twice in this
# repo's guards and was proved to be a hole both times; the anchors below are
# long on purpose, so that EDITING an exempted line un-exempts it and forces the
# decision to be made again.
#
# Two sections, and the difference is load-bearing.
ALLOW=(
  # ── §A. Not a rate at all ──────────────────────────────────────────────────
  # The unit DEFINITION. It exists to stop an agent reporting a charge in the
  # wrong unit, and its instruction is literally "echo the number as given" —
  # the opposite of quoting a figure from a file. Nothing here rots: the
  # credit/centi-credit ratio is the API's own arithmetic, not a price.
  'skills/novoads-api/reference\.md::Internally 1 credit is 10 centi-credits; the API has already converted'

  # ── §B. Recorded debt ──────────────────────────────────────────────────────
  # Real rate literals that this PR did not fix, because they live outside its
  # file set. Recorded rather than ignored, on the same forward-only principle
  # as scripts/skill-size-baseline.txt: today's debt is written down, tomorrow's
  # is refused. This section only ever SHRINKS. Do not add to it to make a red
  # run green — fix the line, or the guard buys nothing.
  #
  # B1 — the Seedance prompt library. Owned by a concurrent wave-2 node that is
  #      rewriting these files right now; editing them here would collide. These
  #      are A/B measurements used to argue that one generation with beats beats
  #      three stitched clips — an ORDERING claim that survives losing its
  #      numbers, which is what the rewrite should do.
  'skills/novoads-api/prompting/prompt-library/evals\.md::one generation with beats \(7\.0 credits, 15s, no post-production\)'
  'skills/novoads-api/prompting/prompt-library/evals\.md::stitched \(13\.8 credits, 24s, voice absent for half the runtime\)'
  'skills/novoads-api/prompting/prompt-library/evals\.md::Result: 24s, 13\.8 credits'
  'skills/novoads-api/prompting/prompt-library/evals\.md::cost 7\.0 credits, needed no editing'
  'skills/novoads-api/prompting/prompt-library/seedance-2-ugc-v2\.md::generation with beats cost \*\*7\.0 credits, 15s, no post-production\*\*'
  'skills/novoads-api/prompting/prompt-library/seedance-2-ugc-v2\.md::stitched cost \*\*13\.8 credits, 24s\*\*'
  'skills/novoads-api/prompting/prompt-library/seedance-2-ugc-v2\.md::Cost \(measured\) \| 7\.0cr / 15s \| 13\.8cr / 24s'
  'skills/novoads-api/prompting/prompt-library/seedance-2-ugc-v2\.md::worth a same-prompt A/B when someone has 14 credits to spend'

  # B2 — the flat `/analyses` fee and the per-clip transcript rate, restated in
  #      clone-video-ad. Same defect as the copies fixed when this section was
  #      written and the same remedy (defer to the estimate arm); left for the
  #      owner of that file.
  #
  #      This group used to hold analyze-video's copy of the `/analyses` line too,
  #      and that entry is GONE rather than commented out: the line now names the
  #      flat SHAPE of the fee and sends the reader to the estimate arm for the
  #      number, which is exactly the rewrite this guard asks for. The section only
  #      ever shrinks, and a fixed line's exemption is deleted along with it — a
  #      dead exemption is a live hole waiting for the next person who trusts it.
  'skills/clone-video-ad/SKILL\.md::synchronous call, flat \*\*1 credit\*\*, priced through'
  'skills/clone-video-ad/SKILL\.md::per clip, 0\.1 credits each, and it is the only thing that catches'
  'skills/clone-video-ad/evals\.md::5 segments, an .srt., for \*\*0\.1 credits\*\*'
  'skills/clone-video-ad/evals\.md::synchronously for \*\*0\.3 credits\*\*'

  # B3 — change-voice's eval table, asserting what the estimate arm (it charges nothing) returns.
  #      Closer to legitimate than the rest of §B: the assertion is that a
  #      sourceless quote and a 15s quote agree, which is a statement about the
  #      one-minute minimum rather than about the price. It still pins a number
  #      that will move, so it is recorded rather than exempted.
  'skills/change-voice/evals\.md::.credits: 1., .sufficient: true.\. Charges nothing\.'
  'skills/change-voice/evals\.md::also .credits: 1. . a 15s source and a sourceless quote agree'

  # B4 — the clone-image-ad prompting guide. Dated MEASUREMENTS from named runs
  #      ("a 2026-08-05 nine-call run reported…"), not a rate card, and the date
  #      is carried in the sentence — a reader can see how old the figure is,
  #      which is the property every other entry here lacks. Lowest-priority
  #      cleanup of the four groups; still debt, because it is a number an agent
  #      can quote.
  'shared/skills/clone-image-ad/prompting/guide\.md::a 2026-08-05 nine-call run reported 3\.00 credits'
  'shared/skills/clone-image-ad/prompting/guide\.md::the balance moved 3\.4 credits between two'
  'shared/skills/clone-image-ad/prompting/guide\.md::Measured on a 2026-08-06 A/B \(one source, three renders'
)

# ── Scan ─────────────────────────────────────────────────────────────────────
# Scoped to skill markdown — the files an agent reads mid-run, which is where a
# quoted rate does its damage. README.md, AGENTS.md and CHANGELOG.md were checked
# against these same patterns while this was written and carry no rate literals;
# widening the glob below is a one-line change if that stops being true.
#
# The scanner is read into a variable FIRST and piped to python3 second, rather
# than living inside HITS="$(python3 - <<PY ...)". A quoted heredoc nested inside
# a command substitution is not reliably literal: bash keeps scanning it for the
# closing paren, and a lone apostrophe or backtick in a Python comment reads as
# an unterminated quote, which fails as "unexpected EOF" pointing at a line with
# nothing wrong on it. Hoisting the heredoc to the top level removes the trap
# instead of tiptoeing around it.
read -r -d '' PY_SCAN <<'PY' || true
import re, subprocess

# One pattern per shape, so the failure names the shape that matched instead of
# making the reader diff it out.
PATTERNS = [
    (r'\b\d[\d.,]*\s*(?:display\s+)?credits?\b',            'N credits'),
    (r'\b\d[\d.,]*\s*cc\b',                                 'N cc'),
    (r'\b\d[\d.,]*\s*centi-?credits?\b',                    'N centi-credits'),
    (r'\b\d[\d.,]*\s*cr\s*/',                               'N cr/unit'),
    (r'\bcredits?\s*(?:/|per\s)\s*(?:billed\s+)?'
     r'(?:minute|second|image|call|clip|generation|ad\b|sweep|character)', 'credits per unit'),
    (r'\bcredits"?\s*:\s*\d',                               'credits: N'),
]

files = subprocess.run(
    ["git", "ls-files", "skills/*.md", "skills/**/*.md", "shared/skills/**/*.md"],
    capture_output=True, text=True).stdout.split()

# chr(96) * 3, not the literal three characters: this heredoc lives inside a
# $( ) command substitution, and bash's parser reaches into it looking for a
# matching backtick even though the delimiter is quoted. Spelling the fence
# marker this way is the difference between this script running and this script
# dying with "unexpected EOF while looking for matching".
FENCE = chr(96) * 3

for path in sorted(files):
    fenced = False
    with open(path) as fh:
        for lineno, line in enumerate(fh, 1):
            if line.lstrip().startswith(FENCE):
                fenced = not fenced
                continue
            if fenced:
                continue
            for pattern, label in PATTERNS:
                if re.search(pattern, line, re.I):
                    print(f"{path}\t{lineno}\t{label}\t{line.rstrip()}")
                    break
PY

HITS="$(printf '%s' "$PY_SCAN" | python3 -)"

violations=0
allowed=0
matched_entries=()

while IFS=$'\t' read -r file lineno label content; do
  [ -n "${file:-}" ] || continue

  ok=0
  for entry in "${ALLOW[@]}"; do
    glob="${entry%%::*}"
    pattern="${entry#*::}"
    if [[ "$file" =~ ^${glob}$ ]] && [[ "$content" =~ $pattern ]]; then
      ok=1
      matched_entries+=("$entry")
      break
    fi
  done

  if [ "$ok" -eq 1 ]; then
    allowed=$((allowed + 1))
  else
    if [ "$violations" -eq 0 ]; then
      echo "FAIL: a credit RATE is written into a skill file." >&2
      echo "" >&2
      echo "The agent reads these files at spend time and quotes what it finds." >&2
      echo "When the price moves nothing here goes red, so the skill keeps" >&2
      echo "quoting a number that stopped being true and the user is told one" >&2
      echo "price and charged another." >&2
      echo "" >&2
      echo "Remedy: delete the figure and point at the live quote instead —" >&2
      echo "'price it with the <kind> arm of POST /v1/estimates and quote that'." >&2
      echo "Keep the METER (per minute, rounded up, one-minute minimum, flat per" >&2
      echo "call) and keep ordering claims ('the stills are a fraction of the" >&2
      echo "clips'). Those are durable; the number is not." >&2
      echo "" >&2
    fi
    echo "  $file:$lineno: [$label] $content" >&2
    violations=$((violations + 1))
  fi
done <<< "$HITS"

# A dead exemption is a live hole waiting for the next person who trusts it —
# the reasoning check-no-mcp.sh carries for its own allowlist. Warn rather than
# fail: an entry goes dead the moment its owner FIXES the line, and that PR must
# not be reddened by this one's bookkeeping.
for entry in "${ALLOW[@]}"; do
  hit=0
  for m in ${matched_entries[@]+"${matched_entries[@]}"}; do
    [ "$m" = "$entry" ] && { hit=1; break; }
  done
  [ "$hit" -eq 1 ] || echo "warn  allowlist entry matched nothing (the line was fixed?) — delete it: ${entry%%::*}"
done

if [ "$violations" -gt 0 ]; then
  echo "" >&2
  echo "$violations un-allowlisted rate literal(s); $allowed allowlisted." >&2
  exit 1
fi

echo "OK: no un-allowlisted credit rates in skill markdown ($allowed allowlisted)."
