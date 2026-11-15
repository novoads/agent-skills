#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Reusable YouTube thumbnail batch generator (Nano Banana Pro via Novoads API)
#
# This is a TEMPLATE. Copy to scripts/generate-thumbnails-vN.sh and customize:
#   1. Update REF_BASE and COMMON_REFS array with your reference file paths
#   2. Replace PROMPTS array with your composed prompts
#   3. Run: bash scripts/generate-thumbnails-vN.sh > output/run.log 2>&1 &
#   4. Monitor: tail -F output/run.log | grep --line-buffered -E "DONE|FAIL|ERROR|MISSING|resubmit|charged"
#
# Features:
#   - Image preprocessing (Lanczos to 1080px longest side, RGB JPEG)
#   - Upload ONCE, reuse the assetIds across every prompt in the batch
#   - POST /v1/images returns the image, or answers "running" and is polled (API 2.39.0)
#   - Bounded parallelism at the script's own cap, under the API's image queue
#
# Requires:
#   - .env with NOVOADS_API_KEY
#   - Python 3 with PIL/Pillow installed (for the preprocessing step)
#   - macOS bash 3.2+ or any bash 4+
#
# COST: every generation is charged, and there are no free re-rolls. Price the
# batch with POST /v1/estimates and get the user's OK BEFORE running this.
# Each thumbnail's POST carries its own idempotencyKey, so a call sent again is never
# charged twice; it goes out again only where that can help — see ONE KEY. A run
# prints its batch key: run it again unchanged with BATCH_KEY=<that key> within 24 hours
# and each thumbnail it sent gets its first call's answer back instead of a second, paid
# picture. After 24 hours the same keys draw and charge again.
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
# This cap is the script's own choice, not the API's limit. The API allows 12
# concurrent image generations per organization, counted apart from video in both
# directions, so 4 leaves room for other image calls the organization runs through
# the API. A 13th in flight is a 429 with details.reason=image_concurrency_limit,
# and waiting is the only thing that clears it.
MAX_PARALLEL=4

OUTPUT_DIR="${OUTPUT_BASE:-output}/thumbnails-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"
TMP_DIR="$OUTPUT_DIR/.tmp"
mkdir -p "$TMP_DIR"

# ─── REFERENCE IMAGES ───────────────────────────────────────────────────────
# Use absolute paths (any file name works: spaces, &, parentheses and quotes included).
#
# Aim for 5+ face references for good likeness alignment. nano-banana-pro takes
# up to 14; gpt-image-2 is capped at 4.
# You may UPLOAD more than a call cites (an assetId can be reused across calls) and
# pick the best per prompt: a single call may reference at most REF_CAP.
# For likeness work, start with one straight-on headshot, one 3/4 angle, one
# close-up, and the single most important brand asset.
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
# 2026-08-03). gpt-image-2 is still 4, so this guard tracks the model this
# script actually calls.
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

# Upload one file via POST /v1/uploads, PUT the bytes, echo the assetId.
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

  # Replay the signed headers exactly as returned, one -H each, kept in an array so
  # nothing is parsed twice: the presigned URL carries & and a file name may carry
  # ( or ', and an eval cut the URL at its first &, so storage refused every PUT.
  local -a hdr_args=()
  local hdr
  while IFS= read -r hdr; do
    [ -n "$hdr" ] && hdr_args+=(-H "$hdr")
  done < <(echo "$resp" | python3 -c "
import json,sys
for k, v in json.load(sys.stdin).get('headers', {}).items():
    print(f'{k}: {v}')
")
  # The upload is done when the PUT answers 200. Anything else ends the batch here,
  # before any image call, with storage's own error (its XML names the cause).
  local put_code put_body="${prepared}.put.txt"
  put_code=$(curl -sS -o "$put_body" -w '%{http_code}' -X PUT ${hdr_args[@]+"${hdr_args[@]}"} \
    --data-binary "@$prepared" "$upload_url") || true
  if [ "$put_code" != "200" ]; then
    echo "UPLOAD PUT FAIL: HTTP ${put_code:-000} $(head -c 300 "$put_body" 2>/dev/null | tr -d '\n')" >&2
    return 1
  fi
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

  # One idempotencyKey for this thumbnail, in the body of each of its POSTs: the one
  # thumbnail_keys drew for it, else a new one (see ONE KEY). Printed before the POST, with
  # the time it was sent, which bounds a stop's look for its job.
  local body response key=${4:-} sent_at
  [ -n "$key" ] || key=$(python3 -c "import uuid; print(uuid.uuid4())")
  sent_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "[#$idx] Submitting with idempotencyKey $key, sent $sent_at (blocks ~60-90s for the render)..."
  body=$(KEY="$key" REF_JSON="$ref_json" PROMPT="$prompt" MODEL="$MODEL" ASPECT="$ASPECT" PRODUCT_ID="$PRODUCT_ID" python3 -c "
import json, os
body = {
  'model': os.environ['MODEL'],
  'prompt': os.environ['PROMPT'].strip(),
  'aspectRatio': os.environ['ASPECT'],
  'numImages': 1,
  'referenceAssetIds': json.loads(os.environ['REF_JSON']),
  'idempotencyKey': os.environ['KEY'],
}
if os.environ.get('PRODUCT_ID'):
    body['productId'] = os.environ['PRODUCT_ID']
print(json.dumps(body))
")

  # --fail-with-body keeps the error envelope readable on a non-2xx, and -D keeps the
  # answer's status line and Retry-After. A failed POST goes out again, the same body
  # and key, only where that can help (see ONE KEY).
  local send=0 rc=0 verdict kind prev="" again=0 resent=0 maybe_charged=0 looping=0 seen_conflict=0
  local conflict_waited=0 conflict_total=120
  local post_status="" post_ra="" post_wait=2 post_errline=""
  # A key from an earlier run (BATCH_KEY given) may already stand charged: never "nothing was charged".
  if [ -n "${BATCH_KEY_GIVEN:-}" ]; then maybe_charged=1; fi
  local post_hdr="$OUTPUT_DIR/${idx}_post.headers" post_err="$OUTPUT_DIR/${idx}_post.err"
  while :; do
    send=$((send + 1))
    rc=0
    : > "$post_hdr"
    response=$(curl -sS --fail-with-body --max-time 300 -D "$post_hdr" \
      -H "Authorization: Bearer $NOVOADS_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$body" \
      "$API/v1/images" 2>"$post_err") || rc=$?
    # curl exits 22 on an answer of 400 or more; any other failure is no answer at all.
    post_status=$(tr -d '\r' < "$post_hdr" 2>/dev/null | awk '/^HTTP\//{s=$2} END{print s}') || post_status=""
    post_ra=$(tr -d '\r' < "$post_hdr" 2>/dev/null | awk 'tolower($1) == "retry-after:" {v = $2} END {print v}') || post_ra=""
    post_errline=$(head -c 300 "$post_err" 2>/dev/null | tr -d '\n') || post_errline=""
    # The answer's kind, then the wait before a resend. ok; busy, lost, vendor (once) and
    # conflict (every 15 s, up to 120 s) are sent again; refunded, refused stop. The table
    # generate_image.py's post_image uses.
    verdict=$(RC="$rc" STATUS="$post_status" RA="$post_ra" python3 -c "
import json, math, os, sys
rc, ra = int(os.environ['RC']), os.environ['RA'].strip()
status = int(os.environ['STATUS']) if os.environ['STATUS'].isdigit() else 0
try:
    answer = json.loads(sys.stdin.read(), strict=False)
except ValueError:
    answer = None
err = answer.get('error') if isinstance(answer, dict) else None
err = err if isinstance(err, dict) else {}
code = err.get('code')
details = err.get('details') if isinstance(err.get('details'), dict) else {}
if rc == 0:
    kind = 'ok' if isinstance(answer, dict) else 'lost'
elif rc != 22:
    kind = 'lost'
elif not code:
    kind = 'lost' if status >= 500 else 'refused'
elif (status, code) in ((429, 'rate_limited'), (503, 'unavailable')):
    kind = 'busy'
elif status == 409 and code == 'conflict' and details.get('idempotencyKey'):
    kind = 'conflict'
elif status == 502 and code == 'provider_failed':
    kind = 'vendor' if details.get('reasonCode') in (None, 'vendor_error', 'vendor_timeout') else 'refunded'
else:
    kind = 'lost' if status >= 500 else 'refused'
w = details.get('retryAfterSeconds')
w = int(ra) if ra.isdigit() else (w if isinstance(w, (int, float)) and not isinstance(w, bool) and w >= 0 else None)
if w is None:
    w = 15 if kind == 'conflict' else 2
print(kind, min(math.ceil(w), 60 if kind == 'busy' else 30))
" <<<"$response" 2>/dev/null) || verdict=""
    [ -n "$verdict" ] || verdict="lost 2"
    kind=${verdict%% *}
    post_wait=${verdict##* }
    [ "$kind" = ok ] && break
    case "$kind" in lost|conflict) maybe_charged=1 ;; esac
    # One resend for the first failure that is not the key's 409; the key's 409 is asked
    # again after each wait until the waits since the first 409 would pass 120 s, and a
    # busy answer met after it waits the same way (see ONE KEY).
    looping=0
    if [ "$kind" = conflict ]; then
      looping=1
      seen_conflict=1
    elif [ "$kind" = busy ] && [ "$seen_conflict" -eq 1 ]; then
      looping=1
    fi
    if [ "$looping" -eq 1 ] && [ "$post_wait" -lt 1 ]; then post_wait=1; fi
    again=0
    if [ "$looping" -eq 1 ]; then
      if [ $((conflict_waited + post_wait)) -le "$conflict_total" ]; then
        again=1
        conflict_waited=$((conflict_waited + post_wait))
      fi
    elif [ "$resent" -eq 0 ]; then
      case "$kind" in busy|lost|vendor) again=1; resent=1 ;; esac
    fi
    if [ "$again" -eq 1 ]; then
      case "$kind" in
        busy)
          if [ "$looping" -eq 1 ]; then
            echo "[#$idx] HTTP $post_status, nothing was charged for this send: asking again in ${post_wait}s with the same idempotencyKey (${conflict_waited}s of ${conflict_total}s). $response"
          else
            echo "[#$idx] HTTP $post_status, nothing was charged: sending it once more in ${post_wait}s with the same idempotencyKey. $response"
          fi ;;
        lost) echo "[#$idx] ${post_status:+HTTP $post_status, }it may have been made: sending it once more in ${post_wait}s with the same idempotencyKey, which is never charged twice. ${response:-no answer: $post_errline}" ;;
        vendor) echo "[#$idx] HTTP 502, refunded: drawing it once more in ${post_wait}s, charged once if it works. $response" ;;
        conflict)
          # The server's message once per run of 409s; then one short line each.
          if [ "$prev" = conflict ]; then
            echo "[#$idx] HTTP 409 again, still being made and charged once at most: asking again in ${post_wait}s (${conflict_waited}s of ${conflict_total}s)."
          else
            echo "[#$idx] HTTP 409, the first send is still being made, charged once at most: asking again in ${post_wait}s with the same idempotencyKey (${conflict_waited}s of ${conflict_total}s). $response"
          fi ;;
      esac
      prev=$kind
      sleep "$post_wait"
      continue
    fi
    echo "$response" > "$OUTPUT_DIR/${idx}_error.json"
    echo "[#$idx] ERROR: ${post_status:+HTTP $post_status: }${response:-no answer: $post_errline}"
    # Where to look for the job: every image job written since a minute before this thumbnail
    # was sent (a clock a little ahead of the API's), a day more when BATCH_KEY was given (an
    # earlier run may have sent this key), page by page. The list shows a prompt's first 120
    # characters, which every thumbnail prompt of a batch shares, so each match is read whole.
    # The API writes a job in the same step as its charge, so no job there is no charge.
    local since lookup before="a minute before this thumbnail's first send"
    [ -z "${BATCH_KEY_GIVEN:-}" ] || before="a day and a minute before this send, since BATCH_KEY may be an earlier run's"
    since=$(SENT_AT="$sent_at" GIVEN="${BATCH_KEY_GIVEN:-}" python3 -c "
import datetime, os
t = datetime.datetime.strptime(os.environ['SENT_AT'], '%Y-%m-%dT%H:%M:%SZ')
print((t - datetime.timedelta(days=1 if os.environ['GIVEN'] else 0, seconds=60)).strftime('%Y-%m-%dT%H:%M:%SZ'))
" 2>/dev/null) || since=$sent_at
    lookup="GET /v1/generations?kind=image&limit=50&updatedSince=$since ($before) and its further pages (offset while hasMore): read with GET /v1/generations/{jobId} each job created since then whose promptPreview, the first 120 characters of its prompt, begins as this thumbnail's prompt does, since every thumbnail prompt of a batch starts alike, and take the one whose whole prompt is this thumbnail's"
    if [ "$kind" = conflict ]; then
      echo "[#$idx] idempotencyKey $key still answered 409 after ${conflict_waited}s of asking: its first call's answer was not recorded, and that call is charged once at most. Find its job in $lookup. Poll it to its end: one still in progress may still be drawing, or may be waiting for the API to fail it and refund it, usually within about 30 minutes of the charge and at the latest about 2 hours after it, and no such job since then means nothing was charged. This key keeps answering 409 for its 24 hours, and the same BATCH_KEY sends it again for this thumbnail: once that job has failed or is not there, run this thumbnail alone with a new batch key (only its prompt in PROMPTS, no BATCH_KEY), one new key, charged once. Sooner, it may stand charged twice: that call and the new one. The whole batch without BATCH_KEY draws and charges every thumbnail again."
    elif [ "$maybe_charged" -eq 1 ] && [ -n "${BATCH_KEY:-}" ]; then
      echo "[#$idx] This may have rendered and been charged, once (every send carried idempotencyKey $key): run the batch again unchanged with BATCH_KEY=$BATCH_KEY within 24 hours: its answer comes back if it was made, or it is drawn if it was not, charged once either way, or, where that call failed with its charge standing, it answers 409 until its 24 hours pass, and the run then stops with where to find its job. After 24 hours that key draws and charges again, so look first: $lookup; no such job since then means nothing was charged. A new BATCH_KEY sends a new key: a second picture, charged again, if the first was made."
    elif [ "$maybe_charged" -eq 1 ]; then
      echo "[#$idx] This may have rendered and been charged, once (every send carried idempotencyKey $key): before running it again, look in $lookup; no such job since then means nothing was charged. A new run sends a new key: a second picture, charged again, if the first was made."
    elif [ "$kind" = busy ]; then
      echo "[#$idx] HTTP $post_status, refused again after the wait. Nothing was charged: send it again later."
    fi
    rm -f "$post_hdr" "$post_err"
    return 1
  done
  rm -f "$post_hdr" "$post_err"

  echo "$response" > "$OUTPUT_DIR/${idx}_job.json"

  # creditsCharged comes from the POST: read it before a poll replaces $response.
  local url credits status job_id waited=0
  credits=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('creditsCharged',''))" 2>/dev/null || echo "?")
  status=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('status',''))" 2>/dev/null || echo "")
  job_id=$(echo "$response" | python3 -c "import json,sys; print(json.loads(sys.stdin.read(), strict=False).get('jobId',''))" 2>/dev/null || echo "")

  # Since API 2.39.0 a render still going after about 105 s answers 200 with
  # status "running", the same jobId and no images. It is paid and still
  # rendering: poll GET /v1/generations/{jobId} to a terminal status and read
  # the picture there: a one-picture job's read has it in outputUrl, with no
  # images[]. Never resubmit it.
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
print(imgs[0].get('url','') if imgs else (d.get('outputUrl') or ''))
" 2>/dev/null || echo "")

  if [ -z "$url" ]; then
    # A job that stopped says why in reasonCode, where that is known, and in error.
    local why
    why=$(echo "$response" | python3 -c "
import json,sys
d=json.loads(sys.stdin.read(), strict=False)
print(''.join(', %s=%s' % (k, d[k]) for k in ('reasonCode', 'error') if d.get(k)))
" 2>/dev/null || echo "")
    echo "[#$idx] FAILED: no image (status=$status, jobId=$job_id$why)"
    return 1
  fi

  curl -sS -o "$OUTPUT_DIR/${idx}_thumbnail.png" "$url"
  echo "[#$idx] DONE — $credits credits charged"
  return 0
}

# ─── ONE KEY PER THUMBNAIL, AND WHEN A CALL GOES OUT AGAIN ──────────────────
# generate_one puts each thumbnail's idempotencyKey in the body of its POST /v1/images
# and keeps it for that call's resends. The API answers a key it has seen within 24
# hours with that first send's job (the same jobId, charge and image), answers 409
# while the first send is still being made, and gives the key back only when nothing
# stands charged (a call it refused, or a draw that failed at once and was refunded),
# so a resend with the same key is never a second charge. A failed POST goes out once
# more, after the answer's Retry-After (else error.details.retryAfterSeconds, else 2 s;
# never more than 30 s), on a 429 or the API's own 503 (nothing charged, waited up to
# 60 s, since a per-minute limit names the rest of its minute; credit_balance_busy, the
# credit balance held by other paid calls at that moment, is one of them); on no answer
# (a timeout, a dropped connection), a 500 or another 5xx (the key answers with the first
# send if it was made); and on a 502 provider_failed whose reasonCode is vendor_error,
# vendor_timeout or none (refunded, so a new draw; the API gives the key back only where
# the credits all came back, and where they did not the resend meets a 409 and takes the
# 409's path, never a second charge). A 409 for the key, the first send
# still being made, never uses that one resend: it is asked again after each
# Retry-After, else 15 s, until the waits since the first 409 reach 120 s (the API
# answers a call within about 105 s of its start), and a 429 or 503 met in that time
# waits the same way, since several thumbnails asking at once can meet the per-key
# limit. Past that the API says its answer was not recorded and the key keeps answering
# 409, so the thumbnail stops and says where to find its job. Anything else stops at
# once: another 4xx, or a 502 whose reasonCode names the picture or the prompt, which
# fails the same way again. A stop says whether the thumbnail may stand charged.
#
# The keys come from the run's batch key (BATCH_KEY, else a new one, printed at the
# start and saved in the output folder): thumbnail_keys draws each as a uuid5 of the
# batch key, the model, the shape, each reference file's path and contents, the prompt
# and how many identical prompts came before it. So a run that was cut off, run again
# unchanged with BATCH_KEY=<its key> within 24 hours, sends every thumbnail the key it
# sent before and gets each first call's answer back, charged once, instead of a second,
# paid picture; a thumbnail whose prompt, model, shape or references changed (a file
# replaced at the same path included) draws a new key by itself, and two identical
# prompts still get two keys. After 24 hours the same keys draw and charge again.

# Each thumbnail's idempotencyKey, one line per prompt given, in order (see ONE KEY).
# Each reference in COMMON_REFS counts by its path and its contents; one that cannot be
# read draws no key at all.
thumbnail_keys() {
  [ "$#" -gt 0 ] || return 0
  printf '%s\0' "$@" | BATCH_KEY="$BATCH_KEY" MODEL="$MODEL" ASPECT="$ASPECT" python3 -c '
import hashlib, os, sys, uuid
refs = []
for path in sys.argv[1:]:
    try:
        with open(path, "rb") as fh:
            refs.append(path + "\t" + hashlib.sha256(fh.read()).hexdigest())
    except OSError as e:
        sys.exit("cannot read reference %s: %s" % (path, e))
seen = {}
for prompt in sys.stdin.buffer.read().decode("utf-8").split("\0")[:-1]:
    prompt = prompt.strip()
    n = seen.get(prompt, 0)
    seen[prompt] = n + 1
    parts = ["novoads-thumbnail", os.environ["BATCH_KEY"], os.environ["MODEL"],
             os.environ["ASPECT"], "\n".join(refs), str(n), prompt]
    print(uuid.uuid5(uuid.NAMESPACE_URL, "\n".join(parts)))
' ${COMMON_REFS[@]+"${COMMON_REFS[@]}"}
}

# Every thumbnail, at most MAX_PARALLEL in flight, each POST with its own key (see ONE
# KEY). Args: the reference assetIds as JSON, then the prompts. Sets BATCH_KEY (from the
# environment, else a new one) and BATCH_KEY_GIVEN, and saves the batch key in the output
# folder; when the keys cannot be drawn, one per prompt, it sends nothing.
generate_all() {
  local ref_json=$1
  shift
  # The batch key: BATCH_KEY from the environment (a run that was cut off), else a new one.
  BATCH_KEY_GIVEN="${BATCH_KEY:+1}"
  BATCH_KEY="${BATCH_KEY:-$(python3 -c 'import uuid; print(uuid.uuid4())')}"
  local -a keys=()
  local k prompt i=0
  while IFS= read -r k; do keys+=("$k"); done < <(thumbnail_keys ${1+"$@"})
  if [ "${#keys[@]}" -ne "$#" ]; then
    echo "ERROR: ${#keys[@]} idempotencyKeys drawn for $# prompts; nothing was sent." >&2
    return 1
  fi
  echo "$BATCH_KEY" > "$OUTPUT_DIR/batch_key.txt"

  echo "═══════════════════════════════════════"
  echo "Generating $# thumbnail(s), max $MAX_PARALLEL in flight..."
  echo "Output: $OUTPUT_DIR"
  echo "Batch key: $BATCH_KEY (saved in $OUTPUT_DIR/batch_key.txt). If this run is cut off, run it again unchanged with BATCH_KEY=$BATCH_KEY within 24 hours: each thumbnail it sent answers with its first call, charged once, instead of a second, paid picture. After 24 hours those keys draw and charge again, so look in GET /v1/generations first."
  echo "═══════════════════════════════════════"

  for prompt in ${1+"$@"}; do
    # Block until a slot frees up, so we never exceed MAX_PARALLEL.
    while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$MAX_PARALLEL" ]; do
      sleep 1
    done
    generate_one "$((i + 1))" "$prompt" "$ref_json" "${keys[$i]}" &
    i=$((i + 1))
  done
  wait
}

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
echo "(An assetId can be reused across calls: every prompt in this batch uses these.)"

# The batch key, every thumbnail's idempotencyKey, and the thumbnails (see ONE KEY).
generate_all "$REF_JSON" ${PROMPTS[@]+"${PROMPTS[@]}"}

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
        job = json.loads(open(p).read(), strict=False)
        # A failed or blocked job's credits come back on their own, so it is not counted.
        if job.get("status") not in ("failed", "blocked"):
            total += float(job.get("creditsCharged") or 0)
    except Exception:
        pass
print(round(total, 4))
PY
)
if [ -n "$BATCH_KEY_GIVEN" ]; then
  # A replay is the first answer as it was, so a thumbnail an earlier run made counts here.
  echo "Total credits the jobs report: $TOTAL (BATCH_KEY was given: a thumbnail a run made with it in the last 24 hours shows that run's charge, charged there once; past 24 hours each one here is a new charge)"
else
  echo "Total credits charged this run: $TOTAL"
fi
echo "═══════════════════════════════════════"
open "$OUTPUT_DIR" 2>/dev/null || xdg-open "$OUTPUT_DIR" 2>/dev/null || true
