#!/usr/bin/env bash
# Connectivity check for the Novoads REST API. Loads .env if present.
# Never prints the key.
#
# Probes GET /v1/models because it is free, read-only, has no side effects, and
# still requires a valid key, so a 200 proves auth without generating anything.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

# Host only — the request path below supplies /v1.
BASE="${NOVOADS_BASE_URL:-https://api.novoads.ai}"

if [[ -z "${NOVOADS_API_KEY:-}" ]] || [[ "$NOVOADS_API_KEY" == "novo_your_key_here" ]]; then
  echo "No API key found in .env." >&2
  echo "" >&2
  echo "Need a Novoads account? Plans start at \$49/month:" >&2
  echo "  https://novoads.ai/en?utm_source=claude-code&utm_medium=github&utm_campaign=skill-pack" >&2
  echo "" >&2
  echo "Already have one? Create a key at:" >&2
  echo "  https://novoads.ai/dashboard/settings?tab=api" >&2
  echo "" >&2
  echo "Then run ./scripts/setup.sh, or paste it into .env as NOVOADS_API_KEY." >&2
  exit 1
fi

# Body and status in ONE request. The body carries the error code the 403 arm
# branches on, and `-w $'\n%{http_code}'` (rather than `-o /dev/null -w
# "%{http_code}"`) is what makes an offline run report a clean 000.
response="$(curl -sS -m 20 -w $'\n%{http_code}' \
  -H "Authorization: Bearer $NOVOADS_API_KEY" \
  "$BASE/v1/models" 2>/dev/null || printf '\n000')"
code="${response##*$'\n'}"
body="${response%$'\n'*}"

echo "GET $BASE/v1/models → HTTP $code"

# Every arm names a DIFFERENT fix. 401 vs 403 is the pair that matters most:
# a 401 means the key itself is wrong; a 403 plan_required means the key is
# perfect and the account is the problem. Same red ✗, opposite remedies.
case "$code" in
  200)
    echo "OK. Connection verified."
    # Claims audit (soft): warn — never block — if the repo's per-model reference
    # caps have drifted from the live spec. Full audit: ./scripts/verify-image-caps.sh
    "$ROOT/scripts/verify-image-caps.sh" --soft || true
    ;;
  401)
    echo "" >&2
    echo "Bad or revoked key (401). It is mistyped, revoked, or from another account." >&2
    echo "Create a fresh one at https://novoads.ai/dashboard/settings?tab=api" >&2
    exit 1
    ;;
  403)
    echo "" >&2
    if [[ "$body" == *"plan_required"* ]]; then
      echo "The key is fine (403). This organization's plan does not include API access yet," >&2
      echo "so there is nothing to change about the key itself." >&2
      echo "Check your plan at https://novoads.ai/dashboard/settings?tab=billing" >&2
    else
      echo "The key is fine (403), but the REST API is not enabled for this account yet." >&2
      echo "$body" >&2
    fi
    exit 1
    ;;
  429)
    echo "" >&2
    echo "Rate limited (429). Wait a moment and run this again." >&2
    exit 1
    ;;
  000)
    echo "" >&2
    echo "Could not reach $BASE. Check your network." >&2
    exit 1
    ;;
  *)
    echo "" >&2
    echo "Unexpected response:" >&2
    echo "$body" >&2
    exit 1
    ;;
esac
