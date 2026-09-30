#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Reusable YouTube thumbnail batch generator (Nano Banana Pro via Novoads API)
#
# This is a TEMPLATE. Copy to scripts/generate-thumbnails-vN.sh and customize:
#   1. Update REF_BASE and COMMON_REFS array with your reference file paths
#   2. Replace PROMPTS array with your composed prompts
#   3. Run: bash scripts/generate-thumbnails-vN.sh > output/run.log 2>&1 &
#   4. Monitor: tail -F output/run.log | grep -E "DONE|FAILED|charged"
#
# Features:
#   - Image preprocessing (Lanczos to 1080px longest side, RGB JPEG)
#   - Upload ONCE, reuse the assetIds across every prompt in the batch
#   - POST /v1/images returns the image, or answers "running" and is polled (API 2.39.0)
#   - Bounded parallelism that respects the API's concurrency ceiling
#
# Requires:
#   - .env with NOVOADS_API_KEY
#   - Python 3 with PIL/Pillow installed (for the preprocessing step)
#   - macOS bash 3.2+ or any bash 4+
#
# COST: every generation is charged, and there are no free re-rolls. Price the
# batch with POST /v1/estimates and get the user's OK BEFORE running this.
# This script deliberately does NOT retry a failed generation — see NO RETRY.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail
cd "$(dirname "$0")/.."
source .env

# ─── CONFIG ─────────────────────────────────────────────────────────────────
# NOVOADS_BASE_URL is the HOST only — this script appends /v1/...
API="${NOVOADS_BASE_URL:-https://api.novoads.ai}"
MODEL="nano-banana-pro"
ASPECT="16:9"  # thumbnails are 16:9; nano-banana-pro also takes 1:1 2:3 3:2 3:4 4:3 4:5 5:4 9:16 21:9
# PRODUCT_ID is optional and organizational only. Leave empty to use the
# account's default product; it does not influence what is generated.
PRODUCT_ID="${PRODUCT_ID:-}"
# The API allows 5 concurrent generations per organization. Stay under it —
# a 6th in flight is a 429 with details.reason=concurrency_limit, and waiting
# is the only thing that clears it.
MAX_PARALLEL=4

OUTPUT_DIR="${OUTPUT_BASE:-output}/thumbnails-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"
TMP_DIR="$OUTPUT_DIR/.tmp"
mkdir -p "$TMP_DIR"

# ─── REFERENCE IMAGES ───────────────────────────────────────────────────────
# Use absolute paths (filenames with spaces are fine).
#
# Aim for 5+ face references for good likeness alignment. nano-banana-pro takes
# up to 14; gpt-image-2 is capped at 4.
# You may UPLOAD more than 4 (assetIds are durable and cost nothing to keep) and
# pick the best 4 per prompt — but a single call may reference at most 4.
# For likeness work, spend those 4 on: one straight-on headshot, one 3/4 angle,
# one close-up, and the single most important brand asset.
REF_BASE="$(pwd)/references/youtube thumbnail"

declare -a COMMON_REFS=(
  "${REF_BASE}/face/headshot.png"
  "${REF_BASE}/face/three-quarter.png"
  "${REF_BASE}/face/close-up.png"
  "${REF_BASE}/face/smiling.png"
  "${REF_BASE}/face/neutral.png"
  "${REF_BASE}/logos/brand-1.png"
)

# nano-banana-pro takes 14 (fal's published ceiling for the /edit arm, probed
# 2026-08-03). gpt-image-2 is still 4 and reve-2.1 is 8, so this guard tracks
# the model this script actually calls.
REF_CAP=14
if [ "${#COMMON_REFS[@]}" -gt "$REF_CAP" ]; then
  echo "ERROR: ${#COMMON_REFS[@]} references configured; nano-banana-pro caps at $REF_CAP." >&2
  echo "Trim COMMON_REFS to the $REF_CAP that matter most for this batch." >&2
  exit 1
fi

# Verify all references exist before starting
for f in "${COMMON_REFS[@]}"; do
  if [ ! -f "$f" ]; then
    echo "MISSING: $f" >&2
    exit 1
  fi
done

# ─── HELPERS ────────────────────────────────────────────────────────────────

# Upscale to >=1080px longest side and convert to RGB JPEG.
#
# This is kept as good practice, not as an API requirement: the "<1080px returns
# 422 too small" rule was specific to the previous backend and has NOT been
# verified against Novoads. Small references still produce worse likeness, so the
# preprocessing earns its place either way.
prepare_image() {
  python3 - "$1" "$2" <<'PY'
import sys
from PIL import Image
inp, out = sys.argv[1], sys.argv[2]
img = Image.open(inp).convert("RGB")
w, h = img.size
longest = max(w, h)
if longest < 1080:
    scale = 1080.0 / longest
    img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
img.save(out, "JPEG", quality=92)
PY
}

# Upload one file via POST /v1/uploads, PUT the bytes, echo the durable assetId.
#
# The PUT must send the signed headers byte for byte — Content-Type and
# Content-Length are both part of the URL signature, so storage 403s if either
# differs from what the server returned.
upload_file() {
  local file="$1"
  local base prepared
  base=$(basename "$file" | tr ' ' '_')
  prepared="$TMP_DIR/${base}_$$_$RANDOM.jpg"
  prepare_image "$file" "$prepared"

  local size resp asset_id upload_url
  size=$(wc -c < "$prepared" | tr -d ' ')

  resp=$(curl -sS -X POST \
    -H "Authorization: Bearer $NOVOADS_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"contentType\":\"image/jpeg\",\"sizeBytes\":$size}" \
    "$API/v1/uploads")

  asset_id=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('assetId',''))" 2>/dev/null || echo "")
  upload_url=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('uploadUrl',''))" 2>/dev/null || echo "")

  if [ -z "$asset_id" ] || [ -z "$upload_url" ]; then
    echo "UPLOAD PRESIGN FAIL: $resp" >&2
    return 1
  fi

  # Replay the signed headers exactly as returned.
  local hdr_args
  hdr_args=$(echo "$resp" | python3 -c "
import json,sys,shlex
h = json.load(sys.stdin).get('headers', {})
print(' '.join('-H ' + shlex.quote(f'{k}: {v}') for k, v in h.items()))
")
  eval curl -sS -X PUT $hdr_args --data-binary "@$prepared" "$upload_url" >/dev/null
  echo "$asset_id"
}

POLL_INTERVAL_S=15
POLL_DEADLINE_S=900

# Generate one thumbnail. The POST blocks for the render (typically 60-90s)
# and usually returns the finished image; a slow one answers "running" and is polled.
generate_one() {
  local idx=$1
  local prompt=$2
  local ref_json=$3

  echo "[#$idx] Submitting (blocks ~60-90s for the render)..."

  local body response
  body=$(REF_JSON="$ref_json" PROMPT="$prompt" MODEL="$MODEL" ASPECT="$ASPECT" PRODUCT_ID="$PRODUCT_ID" python3 -c "
import json, os
body = {
  'model': os.environ['MODEL'],
  'prompt': os.environ['PROMPT'].strip(),
  'aspectRatio': os.environ['ASPECT'],
  'numImages': 1,
  'referenceAssetIds': json.loads(os.environ['REF_JSON']),
}
if os.environ.get('PRODUCT_ID'):
    body['productId'] = os.environ['PRODUCT_ID']
print(json.dumps(body))
")

  # --fail-with-body keeps the error envelope readable on a non-2xx.
  response=$(curl -sS --fail-with-body --max-time 300 \
    -H "Authorization: Bearer $NOVOADS_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$body" \
    "$API/v1/images" 2>&1) || {
      echo "[#$idx] ERROR: $response"
      echo "$response" > "$OUTPUT_DIR/${idx}_error.json"
      return 1
    }

  echo "$response" > "$OUTPUT_DIR/${idx}_job.json"

  # creditsCharged comes from the POST: read it before a poll replaces $response.
  local url credits status job_id waited=0
  credits=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('creditsCharged',''))" 2>/dev/null || echo "?")
  status=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('status',''))" 2>/dev/null || echo "")
  job_id=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('jobId',''))" 2>/dev/null || echo "")

  # Since API 2.39.0 a render still going after about 105 s answers 200 with
  # status "running", the same jobId and no images. It is paid and still
  # rendering: poll GET /v1/generations/{jobId} to a terminal status and read
  # images[] there. Never resubmit it.
  while [ -n "$job_id" ] && { [ "$status" = "queued" ] || [ "$status" = "running" ] || [ "$status" = "finalizing" ]; }; do
    if [ "$waited" -ge "$POLL_DEADLINE_S" ]; then
      echo "[#$idx] still $status after ${waited}s. Fetch it later with GET /v1/generations/$job_id; do not resubmit."
      return 1
    fi
    echo "[#$idx] $status (jobId=$job_id), polling in ${POLL_INTERVAL_S}s..."
    sleep "$POLL_INTERVAL_S"
    waited=$((waited + POLL_INTERVAL_S))
    # Retry only what can clear on its own (429, 5xx, no answer). Any other 4xx
    # (a bad key, an unknown jobId) will not change in 900 s: stop and say so.
    local code
    code=$(curl -sS --max-time 60 -o "$OUTPUT_DIR/${idx}_poll.tmp" -w '%{http_code}' \
      -H "Authorization: Bearer $NOVOADS_API_KEY" \
      "$API/v1/generations/$job_id" 2>/dev/null) || code="000"
    response=$(cat "$OUTPUT_DIR/${idx}_poll.tmp" 2>/dev/null || true)
    rm -f "$OUTPUT_DIR/${idx}_poll.tmp"
    case "$code" in
      2??) ;;
      429|5??|000)
        echo "[#$idx] poll failed (HTTP $code), retrying: $response"
        continue ;;
      *)
        echo "[#$idx] poll refused (HTTP $code): $response. Fetch it later with GET /v1/generations/$job_id; do not resubmit."
        return 1 ;;
    esac
    echo "$response" > "$OUTPUT_DIR/${idx}_job.json"
    status=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('status',''))" 2>/dev/null || echo "")
  done

  url=$(echo "$response" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read(), strict=False)
imgs=d.get('images') or []
print(imgs[0].get('url','') if imgs else '')
" 2>/dev/null || echo "")

  if [ -z "$url" ]; then
    echo "[#$idx] FAILED: no image (status=$status, jobId=$job_id)"
    return 1
  fi

  curl -sS -o "$OUTPUT_DIR/${idx}_thumbnail.png" "$url"
  echo "[#$idx] DONE — $credits credits charged"
  return 0
}

# ─── NO RETRY, ON PURPOSE ───────────────────────────────────────────────────
# The API has no idempotency keys, so a blind retry after a timeout or a 500 can
# render and charge twice. If a generation fails, check GET /v1/generations for a
# job that already landed before resubmitting it by hand.

# ─── PROMPTS ────────────────────────────────────────────────────────────────
# Define your prompts here. Each entry generates one thumbnail.
# See ../prompting/guide.md and ../prompting/formulas.md for templates.
# Prompts are capped per generation; the API names the limit if you exceed it.

declare -a PROMPTS=(

# Example 1 — Peace-sign / branding formula
"YouTube thumbnail, 16:9 landscape. CRITICAL CHARACTER LIKENESS: The subject is the exact same person shown in ALL the face reference photos. Match his face EXACTLY: [DESCRIBE FEATURES]. Maintain the exact same facial proportions, eye shape, beard style, and skin tone as the reference photos. Do not generalize — this is a specific real person and his exact likeness must be preserved. He is wearing [CLOTHING]. The shot is a tight head-and-shoulders crop with his face large and prominent, filling the central 50 percent of the frame. NO HANDS VISIBLE. Just head and upper shoulders, facing camera. Expression: wide excited open-mouth smile showing teeth, eyebrows raised in genuine excitement, eyes wide. To his LEFT side at chest level is a large rounded-square app icon containing [LOGO 1 DESCRIPTION] — use the logo reference exactly. Across the very top of the frame in massive bold yellow block letters with a thick black outline reads [TITLE]. Background: dark navy gradient with subtle blue glow. Style: clean high-impact YouTube thumbnail. Avoid: distorted face, hands visible, peace signs, generic face, blurry logos, illegible text."

# Add more prompts here, one per array entry
)

# ─── EXECUTION ──────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════"
echo "Uploading ${#COMMON_REFS[@]} reference(s) once for the whole batch..."

REF_IDS=""
for f in "${COMMON_REFS[@]}"; do
  aid=$(upload_file "$f") || { echo "Reference upload failed: $f" >&2; exit 1; }
  if [ -z "$REF_IDS" ]; then REF_IDS="\"$aid\""; else REF_IDS="$REF_IDS,\"$aid\""; fi
done
REF_JSON="[$REF_IDS]"
echo "Reference assetIds: $REF_JSON"
echo "(assetIds are durable — reuse them in later runs instead of re-uploading.)"

echo "═══════════════════════════════════════"
echo "Generating ${#PROMPTS[@]} thumbnail(s), max $MAX_PARALLEL in flight..."
echo "Output: $OUTPUT_DIR"
echo "═══════════════════════════════════════"

for i in "${!PROMPTS[@]}"; do
  idx=$((i + 1))
  # Block until a slot frees up, so we never exceed the concurrency ceiling.
  while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$MAX_PARALLEL" ]; do
    sleep 1
  done
  generate_one "$idx" "${PROMPTS[$i]}" "$REF_JSON" &
done

wait

echo "═══════════════════════════════════════"
echo "DONE. Results in: $OUTPUT_DIR"
DOWNLOADED=$(ls "$OUTPUT_DIR"/*_thumbnail.png 2>/dev/null | wc -l | tr -d ' ')
ERRORS=$(ls "$OUTPUT_DIR"/*_error.json 2>/dev/null | wc -l | tr -d ' ')
echo "$DOWNLOADED downloaded, $ERRORS errors"
TOTAL=$(python3 - "$OUTPUT_DIR" <<'PY'
import glob, json, sys
total = 0.0
for p in glob.glob(sys.argv[1] + "/*_job.json"):
    try:
        total += float(json.load(open(p)).get("creditsCharged") or 0)
    except Exception:
        pass
print(round(total, 4))
PY
)
echo "Total credits charged this run: $TOTAL"
echo "═══════════════════════════════════════"
open "$OUTPUT_DIR" 2>/dev/null || xdg-open "$OUTPUT_DIR" 2>/dev/null || true
