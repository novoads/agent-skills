#!/usr/bin/env bash
# Parity guard for skills/image-to-motion/.
#
# That skill is a PORT. Its craft arrived whole from a vendor-connector skill of
# the same shape and only the transport was rewritten, so it has two failure
# modes that pull in opposite directions and a reviewer reliably only looks for
# one of them:
#
#   drift       a craft section quietly thinned in the move. The port is worth
#               nothing if the part worth porting did not arrive.
#
#   half-port   a retired tool name or a retired API claim left in place. Worse
#               than drift, because it does not read as wrong: the agent follows
#               it and either stalls on a tool that does not exist or spends a
#               render on a 400 this repo already knows about.
#
# So this checks BOTH directions. The judgement half — has the craft been
# softened rather than deleted — is in the skill's evals.md and cannot be
# grepped. This file owns only what a string match can settle, which is the half
# that should never have needed a human.
#
# Costs nothing and touches no network. Usage: ./scripts/test-parity-i2m.sh
set -uo pipefail
cd "$(dirname "$0")/.."

SKILL=skills/image-to-motion/SKILL.md
EVALS=skills/image-to-motion/evals.md
fail=0
pass=0

ok()   { pass=$((pass + 1)); }
bad()  { echo "FAIL  $1"; fail=$((fail + 1)); }

[ -f "$SKILL" ] || { echo "FAIL  $SKILL is missing"; exit 1; }
[ -f "$EVALS" ] || { echo "FAIL  $EVALS is missing"; exit 1; }

# ── 1. Half-port: retired names and retired claims ───────────────────────────
# Each pattern is a thing the SOURCE skill said that is false or unreachable on
# /v1. `nbGenerations` and a 1080p ask are both live-verified 400s (2026-08-10);
# the other three name a vendor tool or a vendor behaviour we do not have.
#
# SCOPE is the table's first column. Tool NAMES are banned in every file of the
# skill (`all`) -- nothing in this pack can call one, wherever it is written, and a
# reference file added later inherits the ban instead of escaping it. Retired
# CLAIMS about API behaviour are scoped to SKILL.md (`skill`), because that is the
# file an agent follows at runtime while evals.md has to quote the old wording
# plainly to say what it tests.
#
# That split replaced a whole-file exemption for evals.md, which a review proved
# was a hole: the retired names could be appended there and the guard stayed green
# at 23/23. Same self-exemption failure that shipped in check-no-gag.sh once
# already. But removing it outright left evals.md green only because it happened to
# punctuate around the literals, which makes the real coverage "strings nobody
# repunctuated". Hence scope-with-a-reason rather than exemption-by-convenience.
while IFS='|' read -r scope pattern why; do
  [ -z "$pattern" ] && continue
  case "$scope" in
    all)   target="skills/image-to-motion/" ;;
    skill) target="$SKILL" ;;
    *)     bad "unknown scope '$scope' in the PATTERNS table"; continue ;;
  esac
  # -F: these are literal names, never regexes. A pattern that is accidentally a
  # regex is how a guard silently stops matching what it claims to match.
  if hits=$(grep -rniF -e "$pattern" "$target" 2>/dev/null); then
    bad "retired '$pattern' survives ($why)"
    printf '%s\n' "$hits" | sed 's/^/        /'
  else
    ok
  fi
done <<'PATTERNS'
all|arcads_|vendor tool name; nothing here can call it
all|register_image|no analogue on /v1; the warning is meaningless
all|nbGenerations|not a field; live-verified 400 Unrecognized key
skill|720p or higher|never "or higher": 4k is a 400 here, and 1080p only where GET /v1/models lists it
skill|expire quickly|inverted: the upload URL expires, not the assetId
PATTERNS

# ── 2. Drift: the craft that the port exists to carry ─────────────────────────
# Seven motion classes and five prompt clauses. Anchored on the distinctive
# phrase rather than a heading, because none of the clauses IS a heading and a
# heading-only check passes on a section emptied of its content.
while IFS='|' read -r needle what; do
  [ -z "$needle" ] && continue
  if grep -qF -e "$needle" "$SKILL"; then ok; else bad "craft lost: $what"; fi
done <<'CRAFT'
UI, app screens, toolbars|motion class 1 of 7 (UI)
Marketing hero|motion class 2 of 7 (hero)
Flat-lay, evidence board|motion class 3 of 7 (flat-lay)
Painted key art|motion class 4 of 7 (key art)
Collage, paper-cut|motion class 5 of 7 (collage)
Product still, object|motion class 6 of 7 (product)
Character, mascot, avatar|motion class 7 of 7 (character)
stagger paired elements|the stagger rule, the single highest-value craft line
accent structure|the accent-structure read in step 1
quote every string|clause 1 of 5 (text fidelity)
including anything that is ABSENT|clause 2 of 5 (the 0.0s frame)
holds completely still|clause 3 of 5 (declared holds)
No fade out|clause 4 of 5 (explicit final hold)
One object per beat|clause 5 of 5 (one beat, one motion, easing named)
add specificity rather than emphasis|the iteration rule
CRAFT

# ── 3. The pack's own invariants, on this file ────────────────────────────────
# The key-gate block is quoted verbatim in every SKILL.md so a solo install
# still refuses to run without a key. check-no-mcp.sh allowlists exactly this
# phrasing, so a reworded copy fails CI there; catching it here reports the
# actual remedy instead of an MCP violation.
grep -qF 'REST key required. A Novoads MCP connector is not a substitute.' "$SKILL" \
  && ok || bad "the canonical key-gate block is missing or reworded"

# The cost gate has to actually run. The first version of this skill showed an
# estimate body with no `prompt`, which is REQUIRED on a strict schema: live, that
# is `400 prompt: Invalid input: expected string, received undefined`. An agent
# following it would have had to improvise past the one guard rail between the
# user and a charge, and the warnings section below it would have had nothing to
# lint. Found by an independent parity review, not by a human reading the file.
# PARSED, not grepped. The first version of this check asked whether the token
# "prompt" appeared on the same LINE as the kind, and an adversarial review broke
# it four ways in a minute: a trailing `// send the prompt separately` comment
# passed, `"promptText"` passed (a 400 Unrecognized key on a strict body), an
# empty `"prompt":""` passed (the field is .min(1)), and the CORRECT body failed
# whenever it was pretty-printed, which is this pack's own house format. A guard
# that a comment defeats is worse than none, because it certifies the defect.
if python3 - "$SKILL" <<'PY'
import json, re, sys
text = open(sys.argv[1], encoding="utf-8").read()
bodies = []
# ANY fence tag, and `~~~` as well as backticks. The first version matched only
# untagged and `json` fences, so a `kind:video` body with no prompt hid inside a
# ```jsonc or ~~~json fence and passed. A guard that only inspects the fences it
# expects is a guard whose coverage is a typo away from zero.
for block in re.findall(r"(?:```|~~~)[a-zA-Z0-9_-]*\n(.*?)(?:```|~~~)", text, re.S):
    block = block.strip()
    if '"kind"' not in block:
        continue
    try:
        obj = json.loads(block)
    except json.JSONDecodeError as exc:
        print(f"        estimate example is not valid JSON: {exc}")
        raise SystemExit(1)
    if obj.get("kind") == "video":
        bodies.append(obj)

# A block may be marked as a deliberate counter-example -- showing the body that
# 400s is a legitimate way to teach the rule, and the guard must not forbid it.
# Explicit and greppable so it can never be earned by accident.
if "<!-- parity: counter-example -->" in text:
    marked = len(re.findall(r"<!-- parity: counter-example -->", text))
    print(f"        note: {marked} block(s) marked as counter-examples are still checked;")
    print("        move a counter-example OUT of a fenced kind:video block to exempt it")

if not bodies:
    print("        no {\"kind\": \"video\"} estimate example in a fenced block; the cost gate is unshowable")
    raise SystemExit(1)

for obj in bodies:
    p = obj.get("prompt")
    if not isinstance(p, str) or not p.strip():
        print(f'        estimate body has no usable "prompt" (got {p!r}); live that is')
        print("        400 prompt: Invalid input: expected string, received undefined")
        raise SystemExit(1)
    # .strict() means a near-miss key is a 400 rather than a default.
    for key in obj:
        if key != "prompt" and "prompt" in key.lower():
            print(f'        "{key}" is not "prompt"; a strict body answers 400 Unrecognized key')
            raise SystemExit(1)
PY
then
  ok
else
  bad "the estimate example is not a body this API would accept (detail above)"
fi

# A price written into a skill file rots silently, and this repo's rule is that
# every credit number comes from a live estimate. Digits followed by a credit
# word are the shape that keeps coming back.
# NO exemption. The first version filtered out lines matching `credits?Charged`
# as a BRE, where `?` is literal, so the exemption never fired and nothing was
# lost. "Fixing" it to `-E` made it real, and it immediately became a hole: a
# review demonstrated that `creditsCharged, which for an 8s 720p take is 130
# credits` passed 23/23 with the actual price in it. The exemption bought nothing
# either way -- the unfiltered pattern matches zero lines in a clean file, because
# no digit ever sits beside the field name. So it is gone. A guard on the one rule
# this pack treats as non-negotiable is the last place to carry a convenience.
if grep -nEi '[0-9]+(\.[0-9]+)?[[:space:]]*(cc|credits?)\b' "$SKILL"; then
  bad "a credit figure is written into the skill; price it live instead"
else
  ok
fi

echo
if [ "$fail" -gt 0 ]; then
  echo "$fail FAILURE(S), $pass check(s) passed"
  exit 1
fi
echo "OK: $pass parity checks passed (no half-port, no craft drift)."
