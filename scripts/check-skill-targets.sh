#!/usr/bin/env bash
# Ratchet: a sentence that ROUTES to a skill must name a skill that is here.
#
# The failure, from #87: two descriptions deflected users to skills this pack
# does not ship — "that's `pixar-style-ad`", "that's `adtable-light`" — and one
# more sent them to "a hook skill" that has never existed. A dangling route is
# worse than no route at all. The agent reads it, reports the named skill
# unavailable, and the user is left holding a name they cannot act on and no idea
# what to do instead. Nothing errors, and the description that did it was the
# most-read line in the file.
#
# check-links.sh cannot catch this: these are BARE NAMES in prose, not markdown
# links, so there is no path for it to resolve. That is the whole gap.
#
# ── How it decides something is a route, which is the hard part ───────────────
#
# This pack's vocabulary is ad-shaped, so hyphenated tokens ending in "-ad" are
# everywhere and almost none of them are skill names: `image-ad` appears 85 times
# as an ordinary noun, `novoads-env` is a dotfile, `competitor-ads` is an
# endpoint, `rank-ads` is a script. A grep for name-shaped tokens alone returns
# 250 hits and is unusable — it would be ignored within a week.
#
# Every hit needs a ROUTING phrase — "use X", "that's X", "switch to X", "hand
# off to X", "route to X", "offer X", "invoke X", "see X", "is X", or "X skill".
# On top of that, one of two things must be true of the token:
#
#   A. it is in `backticks`, and hyphenated. A name written as a code span inside
#      a routing sentence is a route whatever it is called — this is the rule
#      that catches an arbitrary name like `adtable-light`, which no shape rule
#      could predict, because it shares nothing with our vocabulary.
#
#   B. it is bare (no backticks) and shaped like one of this pack's skill names:
#      starts with novoads- / clone- / spy-, or ends in -ad / -ads / -to-motion.
#      Bare names do get written ("a STATIC IMAGE ad is clone-image-ad"), but
#      bare prose is where the false positives live, so the shape requirement
#      earns its keep here and only here.
#
#      `-to-motion` joined the list when `novoads-image-to-motion` de-prefixed to
#      `image-to-motion`: the old name was covered by the `novoads-` arm, and
#      without a replacement the bare arm went blind to the whole family, so
#      "use still-to-motion" would route nowhere and pass. Measured: the suffix
#      must be `-to-motion` and not `-motion`, because `stop-motion` is ordinary
#      prose in the clay skill and appears inside routing sentences ("use
#      stop-motion clay"), which a `-motion` arm would report as 20+ dangling
#      routes on its first run — a guard that arrives red gets deleted rather
#      than satisfied.
#
# Measured on this corpus: rule B's shape test over ALL bare tokens returns 250
# candidates and would be ignored within a week; adding the routing cue takes it
# to zero. Rule A returns three, all model IDs, which is what KNOWN_NON_SKILLS
# below is for. Together they catch every shape #87 fixed and leave prose its
# nouns.
#
# Tokens with a capital letter are skipped: a directory name is lowercase, so
# "## Image-ad skill ecosystem" is a heading about a topic, not a route to a
# skill named Image-ad.
#
# Usage: ./scripts/check-skill-targets.sh   (exit 0 clean, 1 on any dangling route)
set -uo pipefail
cd "$(dirname "$0")/.."

# ── Allowlist ────────────────────────────────────────────────────────────────
# Each entry: <path-regex>::<extended-regex the line must match>
#
# EMPTY, and measured rather than assumed: every routing phrase in the pack
# currently names a skill that exists. Wave 1 (#87) closed the last three.
#
# Add an entry only for a route that legitimately names something outside this
# tree — the likely case is an attribution citing another repository's layout,
# the way references/NOTICE.md cites `shared/skills/pixar-style-ad/prompting/` in
# krusemediallc/arcads-claude-code. Those are paths in someone else's repo, not
# routes into ours, and they read as dangling to a lexical check. They do not
# trip this guard today because a citation is not a routing phrase; if one ever
# is, exempt the LINE, never the file.
ALLOW=()

# ── Scan ─────────────────────────────────────────────────────────────────────
read -r -d '' PY_SCAN <<'PY' || true
import os, re, subprocess

# Routable skills, and the shared/ library directories other skills read. Both
# are legitimate targets for a sentence that says "go read X".
known = set()
for parent in ("skills", "shared/skills"):
    if os.path.isdir(parent):
        known.update(
            name for name in os.listdir(parent)
            if os.path.isdir(os.path.join(parent, name))
        )

# Model IDs and tool names that appear in routing sentences and are NOT skills.
# "use `gpt-image-2`" is a routing sentence about a MODEL. Exempted as tokens
# rather than as lines, because the claim is true everywhere: these names can
# never be a skill in this pack, so a line-by-line exemption would be busywork
# that has to be re-done at every new mention.
#
# `sora-2` came off this list when the model left the API (2026-09): a routing
# sentence that still sends an agent to it now fails here, like a dangling skill
# name, and the fix is to name a live model instead.
#
# An id with a dot (`wan-3.0`, `veo-3.1`, `reve-2.1`) needs no entry: a name must
# run straight into its closing backtick, so the pattern below never matches one.
KNOWN_NON_SKILLS = {
    "gpt-image-2", "gpt-image-1", "nano-banana-pro", "nano-banana-2",
    "nano-banana-edit", "omni-flash", "veo-3-1", "seedance-2",
    "seedance-2-ugc", "dall-e-3", "captions-v1", "kling-v3-pro",
    "seedream-5-lite", "seedream-5-pro",
}

FAMILY = (r'(?:novoads|clone|spy)-[a-z0-9]+(?:-[a-z0-9]+)*'
          r'|[a-z][a-z0-9]*(?:-[a-z0-9]+)*-ads?'
          r'|[a-z][a-z0-9]*(?:-[a-z0-9]+)*-to-motion')
ANY_HYPHENATED = r'[a-z][a-z0-9]*(?:-[a-z0-9]+)+'

CUE = (r'\buse\s+(?:the\s+)?|\bthat(?:\'|’)s\s+|\bswitch\s+to\s+'
       r'|\bhand\s+off\s+to\s+|\broute\s+to\s+|\boffer\s+|\binvoke\s+'
       r'|\bsee\s+|\bis\s+')

ROUTE = re.compile(
    # A. cue + a BACKTICKED name of any shape
    r'(?:' + CUE + r')`(' + ANY_HYPHENATED + r')`'
    r'|`(' + ANY_HYPHENATED + r')`\s+skill\b'
    # B. cue + a BARE name shaped like one of ours
    r'|(?:' + CUE + r')(' + FAMILY + r')\b'
    r'|\b(' + FAMILY + r')\s+skill\b',
    re.I)

files = [f for f in subprocess.run(
    ["git", "ls-files", "*.md"], capture_output=True, text=True).stdout.split()
    if f.startswith(("skills/", "shared/"))]

for path in sorted(files):
    with open(path) as fh:
        for lineno, line in enumerate(fh, 1):
            for match in ROUTE.finditer(line):
                token = next(g for g in match.groups() if g)
                # A directory name is lowercase. A capitalised token is prose.
                if token != token.lower():
                    continue
                if token in known or token in KNOWN_NON_SKILLS:
                    continue
                print(f"{path}\t{lineno}\t{token}\t{line.rstrip()}")
PY

HITS="$(printf '%s' "$PY_SCAN" | python3 -)"

violations=0
allowed=0

while IFS=$'\t' read -r file lineno token content; do
  [ -n "${file:-}" ] || continue

  ok=0
  for entry in ${ALLOW[@]+"${ALLOW[@]}"}; do
    glob="${entry%%::*}"
    pattern="${entry#*::}"
    if [[ "$file" =~ ^${glob}$ ]] && [[ "$content" =~ $pattern ]]; then
      ok=1
      break
    fi
  done

  if [ "$ok" -eq 1 ]; then
    allowed=$((allowed + 1))
  else
    if [ "$violations" -eq 0 ]; then
      echo "FAIL: a routing sentence names a skill that is not in this pack." >&2
      echo "" >&2
      echo "A dangling route is worse than no route. The agent reports the named" >&2
      echo "skill unavailable and the user is left holding a name and no remedy." >&2
      echo "" >&2
      echo "Fix it one of three ways:" >&2
      echo "  - the skill exists under another name here: use that name;" >&2
      echo "  - it does not exist here: say so and name what to do instead" >&2
      echo "    ('this pack has no hook-only skill: clone the whole ad and cut');" >&2
      echo "  - it is not a route at all: reword so it does not read as one." >&2
      echo "" >&2
    fi
    echo "  $file:$lineno: routes to '$token', which is not a skill here" >&2
    echo "      $content" >&2
    violations=$((violations + 1))
  fi
done <<< "$HITS"

if [ "$violations" -gt 0 ]; then
  echo "" >&2
  echo "$violations dangling route(s); $allowed allowlisted." >&2
  exit 1
fi

echo "OK: every routing sentence names a skill that exists ($allowed allowlisted)."
