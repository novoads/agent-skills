#!/usr/bin/env bash
# Claims audit for the per-model image caps: referenceAssetIds AND prompt characters.
#
# This repo states API limits in scripts and docs; the API moves without asking us.
# Both caps have drifted already. Spec 2.7.0 raised nano-banana-pro's references from
# 4 to 14 and the pack said 4 for two days. Spec 2.16.0 then split the prompt ceiling,
# which had been a single 4,000 on every model, into three different numbers, and the
# pack enforced 4,000 locally for a day: generators died pre-network on prompts the
# API would have taken whole. So this script is the standing alarm for both:
#
#   1. Fetches the LIVE openapi.json (public, no key) and extracts each image
#      model's referenceAssetIds maxItems and prompt maxLength — matched by the
#      schema's `model` enum value, never by schema name, so a schema rename cannot
#      mis-map a cap.
#   2. Asserts the three generator/validator scripts ENFORCE those caps, by
#      running them: cap+1 refs must be refused naming the cap; cap refs must
#      pass the gate (and then die at a nonexistent --env-file, BEFORE any
#      network call — nothing here needs a key and nothing can spend). The prompt
#      ceiling gets the same treatment, measured at the exact boundary: a body one
#      character past what the always-on suffixes leave must be refused naming the
#      cap, and a body exactly at it must pass.
#   3. Greps the docs for resurrected universal-cap claims, of either kind.
#
# Modes:
#   (default)  full audit, hard exit 1 on any mismatch — run before shipping cap
#              or doc changes, paste the output into the PR.
#   --soft     spec-vs-expected only, WARN and always exit 0 — wired into
#              check-novoads-env.sh so every skill preflight surfaces drift
#              without ever blocking an offline machine.
#
# No jq, no API key, no spend. python3 stdlib only.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOFT=0
[[ "${1:-}" == "--soft" ]] && SOFT=1
BASE="${NOVOADS_BASE_URL:-https://api.novoads.ai}"

# The one expected table, `model=refs:promptchars`. Scripts and docs are checked
# AGAINST this; this is checked against the live spec. Update it only from verified
# spec output. Last verified: deployed spec 2.25.0 on 2026-09-10.
#
# The two GPT Image 2.5 ids joined in 2.25.0 and are audited by section 1 only:
# section 2 runs the pack's own generators, and those lock the model they render
# on, so there is nothing local to assert a cap against for a model no script
# here will send. Section 1 is the half that matters for them anyway, because the
# claim this repo makes about them is a DOCUMENTED cap and that is what drifts.
EXPECTED='gpt-image-2=4:32000 gpt-image-2.5-flare=4:32000 gpt-image-2.5-sunburst=4:32000 nano-banana-pro=14:50000 reve-2.1=8:4000'

STATUS=0
problem() {
  if [[ $SOFT -eq 1 ]]; then echo "WARN(image-caps): $*" >&2
  else echo "FAIL(image-caps): $*" >&2; STATUS=1; fi
}

# ── 1. live spec vs EXPECTED ─────────────────────────────────────────────────
SPEC_JSON="$(curl -sS -m 15 "$BASE/v1/openapi.json" 2>/dev/null || true)"
if [[ -z "$SPEC_JSON" ]]; then
  problem "could not fetch $BASE/v1/openapi.json — cap claims unverified this run"
else
  MISMATCH="$(printf '%s' "$SPEC_JSON" | python3 -c "
import json, sys
expected = {}
for kv in '''$EXPECTED'''.split():
    name, _, caps = kv.partition('=')
    refs, _, chars = caps.partition(':')
    expected[name] = (int(refs), int(chars))
spec = json.load(sys.stdin)
live = {}
for schema in spec.get('components', {}).get('schemas', {}).values():
    props = schema.get('properties') or {}
    model = props.get('model') or {}
    names = model.get('enum') or ([model['const']] if 'const' in model else [])
    refs = props.get('referenceAssetIds') or {}
    prompt = props.get('prompt') or {}
    for name in names:
        # Only the /images arms carry BOTH a reference cap and a prompt cap. The
        # estimate arm names the same models but publishes one maxLength across
        # every kind, so requiring both keys is what keeps it out of this table.
        if name in expected and 'maxItems' in refs and 'maxLength' in prompt:
            live[name] = (refs['maxItems'], prompt['maxLength'])
for name, want in sorted(expected.items()):
    got = live.get(name) or (None, None)
    if got[0] != want[0]:
        print(f'{name} references: repo says {want[0]}, live spec says {got[0]}')
    if got[1] != want[1]:
        print(f'{name} prompt chars: repo says {want[1]}, live spec says {got[1]}')
" 2>/dev/null || echo "spec parse failed")"
  [[ -n "$MISMATCH" ]] && problem "live-spec drift — $MISMATCH"
fi

if [[ $SOFT -eq 1 ]]; then
  exit 0
fi

# ── 2. the scripts enforce EXPECTED (behavior, not constants) ────────────────
check_script() { # <script> <cap> [extra args...]
  local script="$1" cap="$2"; shift 2
  local refs=() i
  for ((i = 0; i <= cap; i++)); do refs+=(--image-ref "/tmp/vc-ref-$i.png"); done
  local out
  # cap+1 refs → must refuse, naming the cap, before anything else happens.
  out="$(python3 "$ROOT/$script" "$@" --prompt probe --aspect-ratio 1:1 \
    --out /tmp/vc-out --env-file /nonexistent/none "${refs[@]}" 2>&1)" \
    && problem "$script accepted $((cap + 1)) refs (expected refusal at $cap)"
  [[ "$out" == *"$cap"* ]] || problem "$script refusal does not name cap $cap: $out"
  # exactly cap refs → the gate must OPEN (script then dies at the fake .env,
  # which proves it got past the cap check without touching the network).
  out="$(python3 "$ROOT/$script" "$@" --prompt probe --aspect-ratio 1:1 \
    --out /tmp/vc-out --env-file /nonexistent/none "${refs[@]:0:$((cap * 2))}" 2>&1)" \
    && problem "$script with $cap refs exited 0 (should die at the fake .env)"
  [[ "$out" == *".env not found"* ]] || problem "$script with $cap refs died before/after the env gate unexpectedly: $out"
}
check_script "skills/chatgpt-image-ad/scripts/generate_image.py" 4
check_script "skills/nano-banana-image-ad/scripts/generate_image.py" 14
check_script "skills/clone-image-ad/scripts/validate_image.py" 4 --model gpt-image-2
check_script "skills/clone-image-ad/scripts/validate_image.py" 14 --model nano-banana-pro
check_script "skills/clone-image-ad/scripts/validate_image.py" 8 --model reve-2.1

# The prompt ceiling, at the exact boundary. The gate measures the FINAL prompt,
# meaning the body plus the three always-on suffixes, so the boundary is not the
# cap itself: it is the cap minus whatever those suffixes weigh. Read that weight
# from the script under test rather than restating it here, so an edited suffix
# moves this check along with it.
suffix_chars() { # <script>
  python3 - "$ROOT/$1" <<'PY'
import importlib.util, sys
path = sys.argv[1]
spec = importlib.util.spec_from_file_location("_gen", path)
mod = importlib.util.module_from_spec(spec)
sys.argv = [path]  # the module parses args only under __main__
spec.loader.exec_module(mod)
print(len(mod.NO_CHROME_SUFFIX) + len(mod.SAFE_ZONE_SUFFIX) + len(mod.GLYPH_SAFETY_SUFFIX))
PY
}

# The probe body is repeated "probe ", never repeated "x".
#
# This is the fix for a guard-vs-guard collision that made the whole prompt-cap
# half of this audit test NOTHING while reporting red. validate_image.py runs the
# placeholder lint (PR #72) BEFORE the length gate, deliberately — a render must
# ship finished, and refusing scaffolding is worth doing before anything else. But
# a body of `'x' * N` is one long `xxxxxx…` token, and `\bxxx+\b` is one of the
# lint's patterns. So every probe was refused as "xxx filler", the refusal never
# named the cap, and all six assertions failed for a reason unrelated to caps: the
# script could have had NO length check at all and this audit would have looked
# exactly the same.
#
# Fixed on the probe side rather than by exempting the caps guard from the lint.
# A probe-mode bypass would put a door in a spend-time guard for the convenience
# of a test, and the lint is the one guard whose whole job is refusing text that
# looks like a stand-in. "probe " repeated is a real word, matches no pattern in
# PLACEHOLDER_PATTERNS, and costs the audit nothing.
#
# If you change this filler, check it against PLACEHOLDER_PATTERNS in
# skills/clone-image-ad/scripts/validate_image.py first. Anything with a {slot},
# an [TOKEN], a bare domain, "TBD", or three consecutive x's puts the collision
# straight back.
probe_body() { # <length>
  python3 -c "
n = $1
print(('probe ' * (n // 6 + 1))[:n])
"
}

check_prompt_cap() { # <script> <cap> [extra args...]
  local script="$1" cap="$2"; shift 2
  local suffixes out body
  suffixes="$(suffix_chars "$script")"
  if ! [[ "$suffixes" =~ ^[0-9]+$ ]]; then
    problem "$script — could not read the always-on suffix length; prompt cap unchecked"
    return
  fi
  # One character past the boundary → must refuse, naming the cap.
  body="$(probe_body "$((cap - suffixes + 1))")"
  out="$(python3 "$ROOT/$script" "$@" --prompt "$body" --aspect-ratio 1:1 \
    --out /tmp/vc-out --env-file /nonexistent/none 2>&1)" \
    && problem "$script accepted a prompt 1 char over the $cap ceiling"
  [[ "$out" == *"$cap"* ]] || problem "$script prompt refusal does not name cap $cap: $out"
  # Exactly at the boundary → the gate must OPEN (the script then dies at the fake
  # .env, which proves it got past the length check without touching the network).
  body="$(probe_body "$((cap - suffixes))")"
  out="$(python3 "$ROOT/$script" "$@" --prompt "$body" --aspect-ratio 1:1 \
    --out /tmp/vc-out --env-file /nonexistent/none 2>&1)" \
    && problem "$script with a prompt exactly at $cap exited 0 (should die at the fake .env)"
  [[ "$out" == *".env not found"* ]] || problem "$script refused a prompt exactly at the $cap ceiling: $out"
}
check_prompt_cap "skills/chatgpt-image-ad/scripts/generate_image.py" 32000
check_prompt_cap "skills/nano-banana-image-ad/scripts/generate_image.py" 50000
check_prompt_cap "skills/clone-image-ad/scripts/validate_image.py" 32000 --model gpt-image-2
check_prompt_cap "skills/clone-image-ad/scripts/validate_image.py" 50000 --model nano-banana-pro
check_prompt_cap "skills/clone-image-ad/scripts/validate_image.py" 4000 --model reve-2.1

# ── 3. docs carry no resurrected universal-cap claim ─────────────────────────
#
# These patterns match the CLAIM, in every phrasing found in the pack — not just
# the sentences that existed when this check was written. That distinction is the
# whole point: the first version of this grep passed on a tree where three files
# still said the caps were uniform, because each said it a different way
# ("All three cap reference images at 4", "Every image model here accepts max 4",
# a bare "(max 4)"). A checker that only knows yesterday's wording reports
# "docs agree" while the most-read file in the family says the opposite.
# Add a pattern here whenever you find a new way to say it.
RESIDUE="$(grep -rn -i \
  -e "caps at .* on every" \
  -e "cap is .* on every" \
  -e "max 4 on every" \
  -e "cap is the same on every" \
  -e "cap is the same everywhere" \
  -e "all three cap" \
  -e "every image model here accepts" \
  -e "same on every image model" \
  -e "cap[s]* .* all three" \
  -e "all three .* at 4" \
  --include="*.md" --include="*.py" "$ROOT/skills" "$ROOT/shared" "$ROOT/README.md" 2>/dev/null || true)"
[[ -n "$RESIDUE" ]] && problem "universal-cap claim resurfaced:
$RESIDUE"

# The same check for the PROMPT ceiling, which spec 2.16.0 split three ways. Scoped
# to the image-ad family, because "4,000 characters" is still the true and current
# figure for five video models and a repo-wide grep would drown in them. Inside these
# paths a universal 4,000 claim is by definition about images, and wrong.
IMAGE_PATHS=()
for p in "$ROOT/skills/chatgpt-image-ad" "$ROOT/skills/nano-banana-image-ad" \
         "$ROOT/skills/clone-image-ad" "$ROOT/shared/skills/chatgpt-image-ad" \
         "$ROOT/shared/skills/nano-banana-image-ad" "$ROOT/shared/skills/clone-image-ad" \
         "$ROOT/shared/skills/image-ad-prompting"; do
  [[ -e "$p" ]] && IMAGE_PATHS+=("$p")
done
PROMPT_RESIDUE="$(grep -rn -i \
  -e "4,\?000 characters on every" \
  -e "4,\?000-char\(acter\)\? cap" \
  -e "every image model's prompt ceiling" \
  -e "prompt ceiling is 4,\?000" \
  -e "cap is 4,\?000" \
  -e "the 4,\?000-character cap" \
  --include="*.md" --include="*.py" "${IMAGE_PATHS[@]}" 2>/dev/null || true)"
[[ -n "$PROMPT_RESIDUE" ]] && problem "universal 4,000 prompt-cap claim resurfaced (it is per model since 2.16.0):
$PROMPT_RESIDUE"

if [[ $STATUS -eq 0 ]]; then
  echo "image-caps audit OK — spec, scripts, and docs agree on refs:prompt-chars: $EXPECTED"
fi
exit $STATUS
