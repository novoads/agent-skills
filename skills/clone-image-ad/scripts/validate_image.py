#!/usr/bin/env python3
"""
Round-trip a clone-workflow prompt through gpt-image-2 or nano-banana-pro.

This is the clone-image-ad skill's validator, NOT a production generator. The two
generator skills are deliberately model-locked (chatgpt-image-ad to gpt-image-2,
nano-banana-image-ad to nano-banana-pro) so a production run cannot drift models by
accident. Cloning has the opposite requirement: Phase 4 validates against one model
and Phase 8 re-runs the SAME template on another to fill in the Model notes block.
So this one takes --model gpt-image-2 or nano-banana-pro, applies that model's own grid, and
refuses the retired reve-2.1 by name and any other id as an invalid choice.

`reve-2.1` was retired in API 2.48.0. `--model reve-2.1` stops here, before the network,
with a line that says so and names the model to validate on instead.

It also carries the clone workflow's EDIT path: --source-image / --source-asset-id
send `sourceAssetId` (a GPT-model field, sent here on gpt-image-2), which repaints named zones of an existing
image while leaving the rest of the frame alone. That is Phase 7's second instrument
— see the guide. It is mutually exclusive with --aspect-ratio, because an edit's
output tracks the source's shape.

Novoads usually returns the finished images from the POST itself, which blocks for
the render (typically 60-90 seconds). Since API 2.39.0 a render still going after
about 105 seconds answers status "running" with no images; generate() then polls
GET /v1/generations/{jobId} to a terminal status. It never resubmits: that job is paid.
Every POST carries an idempotencyKey, a new one per call: the API answers a key it has
seen with that first send's job, so a call sent again with it is never charged twice. A
failed POST is sent once more with the same key where that can help (see post_image).
The key is printed before the POST, and --idempotency-key sends it again from a new run,
so a run that was cut off gets its call's answer back instead of a second, paid picture.

Output contract:
  stdout: one JSON object per generated image, one per line
          {"variant": int, "path": str, "job_id": str,
           "width": int, "height": int, "prompt": str,
           "aspect_ratio": str, "model": str, "credits_charged": float}
  stderr: human-readable progress + errors
  exit:   0 on success; 1 if the generation failed; 2 on bad args.

Stdlib only. No requests, no python-dotenv.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_URL_DEFAULT = "https://api.novoads.ai"  # host only; this script appends /v1/...
# Each model carries its own typed grid in the API schema, and the schemas are strict —
# an aspect ratio from the wrong grid is a 400 before anything is charged. The same
# goes for max_refs (referenceAssetIds maxItems) and max_prompt_chars (prompt
# maxLength): both are PER MODEL, neither is one number across the set. The prompt
# ceilings stopped being uniform in spec 2.16.0, which raised gpt-image-2 to 32,000
# and nano-banana-pro to 50,000 while reve-2.1 kept 4,000. reve-2.1 has since been retired
# (API 2.48.0): see RETIRED below.
#
# This table is the whole file's source for every cap below. Read off the live
# per-model request schemas at /v1/openapi.json and verified against deployed spec
# 2.16.0 on 2026-08-08 (re-read at 2.59.0 on 2026-11-07) — re-check:
# ./scripts/verify-image-caps.sh
_WIDE_RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
MODELS = {
    "gpt-image-2":     {"ratios": {"1:1", "4:5", "2:3", "9:16", "16:9", "21:9"},
                        "max_refs": 4,  "max_prompt_chars": 32000},
    "nano-banana-pro": {"ratios": _WIDE_RATIOS, "max_refs": 14, "max_prompt_chars": 50000},
}
# Ids the API's spec still names only to refuse them. A --model naming one stops in
# argument parsing, before the network, with what happened and where to go instead,
# rather than reaching the API's own 400 after an upload.
RETIRED = {
    "reve-2.1": (
        "reve-2.1 was retired in API 2.48.0: the API refuses it before any charge "
        "(400 invalid_input, details.reason \"model_retired\"). For a second opinion, "
        "validate on the other model: nano-banana-pro if gpt-image-2 drew it, "
        "gpt-image-2 if nano-banana-pro did."
    ),
}


def model_arg(value: str) -> str:
    """argparse type for --model: a retired id is refused with its own message."""
    if value in RETIRED:
        raise argparse.ArgumentTypeError(RETIRED[value])
    return value


ALL_RATIOS = set().union(*(m["ratios"] for m in MODELS.values()))
MAX_IMAGES = 4  # numImages enum: 1, 2, 3, 4
MIN_DIMENSION = 1024
# The render happens inside the POST, typically 60-90s. Leave generous headroom.
GENERATE_TIMEOUT_S = 300

NO_CHROME_SUFFIX = (
    "\n\n[NO PLATFORM CHROME] Render only the standalone ad creative (the static image uploaded to Meta), "
    "not a screenshot of how it displays in-feed. Exclude: iOS device chrome (status bar, home indicator); "
    "platform brand-row above the ad (avatar + handle + Sponsored / Saved label); post body / caption text; "
    "link-card footer (URL + headline + button); engagement rows (likes / comments / shares counts, "
    "Followed-by, View comments); action buttons (Like / Comment / Share / Save); comment input boxes; "
    "platform tab/nav bars (Instagram, Facebook, Twitter); Story chrome (progress bars, story header, "
    "swipe-up arrows). Just the standalone image."
)

SAFE_ZONE_SUFFIX = (
    "\n\n[EDGE-SAFE] All text, headlines, CTAs, table headers, sign/board content, product wordmarks, and "
    "key focal subjects must fit within the central 84% of the canvas (~8% padding from every edge). "
    "Backgrounds and divider lines may bleed; text and focal elements may NOT touch or extend off any edge. "
    "If a tall focal subject doesn't fit at the requested aspect ratio, scale it DOWN — never crop a "
    "headline, never let text run off-frame, never cut off the top/bottom of a sign, board, or product."
)

GLYPH_SAFETY_SUFFIX = (
    "\n\n[TEXT FIDELITY] Inside body-text blocks (chat bubbles, message threads, comment text, ChatGPT "
    "responses, dense paragraphs): plain words only — NO emoji, NO unicode glyphs, NO special characters "
    "mid-sentence. Emoji OK in headlines and short large-text positions where the prompt explicitly calls "
    "for them. Render the EXACT count of conversation elements the prompt specifies — do not invent "
    "additional comments, messages, replies, or responses."
)

# The standard pin block from the shared library header. Everything a run writes
# is the product description; the guard clause below is fixed, and it is fixed
# because the hand-written ones ran ~700 characters and were the single largest
# cause of a refused prompt.
#
# It exists because of what happens without it: across 34 templates on one real
# product, every brand element NOT pinned by a reference either drifted or was
# invented — including a back-of-pack view carrying a sourcing claim about a real
# brand that appeared in no prompt. The model fills unspecified surfaces with
# plausible brand-shaped content; silence reads as an invitation.
#
# Full text and budget: shared/skills/image-ad-prompting/prompting/prompt-library.md
PIN_BLOCK_PREFIX = "\n\n[BRAND PIN] "
PIN_BLOCK_GUARD = (
    ", reproduced exactly as it appears in the reference image — same wordmark, same colours, "
    "same proportions, front face only. Do NOT render the back of the pack, invented label copy, "
    "ingredient lists, sourcing or health claims, or a barcode. Every word in this image is one "
    "this prompt specifies or one already printed on the reference."
)

# Novoads POST /v1/uploads accepts exactly these image types. GIF is not among them.
MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_env(env_path: Path) -> dict:
    """Parse a .env file into a dict. No external deps."""
    if not env_path.exists():
        raise SystemExit(f"error: .env not found at {env_path}")
    out: dict[str, str] = {}
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def auth_header(env: dict) -> str:
    """Build the Authorization header value. Novoads uses Bearer auth."""
    key = env.get("NOVOADS_API_KEY") or os.environ.get("NOVOADS_API_KEY")
    if not key:
        raise SystemExit(
            "error: NOVOADS_API_KEY not set in .env (or shell environment). "
            "Run ./scripts/setup.sh, or create a key at "
            "https://novoads.ai/dashboard/settings?tab=api"
        )
    return f"Bearer {key}"


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len] or "image"


class ApiError(RuntimeError):
    """An HTTP answer that refused a call, with the parts the script decides on.

    `code` is the envelope's `error.code`, or None when the answer is not the
    API's own (an edge page). `retry_after` is the wait the answer named, in
    seconds (`Retry-After`, else `error.details.retryAfterSeconds`), or None.
    `details` is the envelope's `error.details`, or {}.
    """

    def __init__(self, message: str, url: str, status: int,
                 code: str | None = None, retry_after: float | None = None,
                 details: dict | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.status = status
        self.code = code
        self.retry_after = retry_after
        self.details = details if isinstance(details, dict) else {}


def _seconds(value: object) -> float | None:
    """A wait the server named, in seconds, or None when it named none."""
    if isinstance(value, str) and value.strip().isdigit():
        return float(value.strip())
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None


def _api_error(e: urllib.error.HTTPError, url: str) -> ApiError:
    """Turn a Novoads error envelope into a message worth reading."""
    raw = e.read().decode("utf-8", errors="replace")
    wait = _seconds(e.headers.get("Retry-After")) if e.headers is not None else None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Not our envelope at all -> it never reached the application. The one
        # that bites: Cloudflare's bot rule refusing the default urllib UA.
        if "1010" in raw:
            return ApiError(
                f"HTTP {e.code} on {url}: Cloudflare error 1010 — the edge refused "
                f"this client, NOT your API key. This is a User-Agent problem: "
                f"send a non-default one (see USER_AGENT above) or use curl. Do not "
                f"regenerate the key or check the subscription.",
                url, e.code,
            )
        return ApiError(f"HTTP {e.code} on {url}: {raw}", url, e.code)
    # JSON that is not the envelope (no `error` object) is read as not the API's own.
    err = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(err, dict):
        err = {}
    code = err.get("code", "?")
    msg = err.get("message", raw)
    details = err.get("details")
    hint = ""
    if isinstance(details, dict):
        reason = details.get("reason")
        if reason:
            hint = f" (reason: {reason}"
            if details.get("retryAfterSeconds"):
                hint += f", retry after {details['retryAfterSeconds']}s"
            hint += ")"
        elif details.get("issues"):
            hint = f" (issues: {json.dumps(details['issues'])[:300]})"
        elif details.get("reasonCode"):
            hint = f" (reasonCode: {details['reasonCode']})"
        if wait is None:
            wait = _seconds(details.get("retryAfterSeconds"))
    return ApiError(f"HTTP {e.code} {code} on {url}: {msg}{hint}", url, e.code, err.get("code"), wait, details)


# api.novoads.ai sits behind Cloudflare, whose bot rule 403s the default
# "Python-urllib/x.y" User-Agent with a bare `error code: 1010` page — no JSON
# envelope, no requestId, and it reads exactly like a revoked key or a lapsed
# plan. Any non-default UA clears it (verified 2026-08-02). The presigned PUT is
# NOT affected: it goes to R2, not to the API zone, and its signed headers are
# sent verbatim on purpose.
USER_AGENT = "novoads-claude-code/1.0"


def http_post_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise _api_error(e, url) from e


def http_put_file(upload_url: str, file_path: Path, headers: dict, timeout: int = 300) -> None:
    """PUT raw bytes to a presigned URL, echoing the signed headers byte for byte.

    Both Content-Type and Content-Length are part of the URL's signature — storage
    returns 403 if either differs from what was signed, so we send the server's
    `headers` object verbatim rather than letting urllib infer anything.
    """
    data = file_path.read_bytes()
    req = urllib.request.Request(upload_url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 300:
                raise RuntimeError(f"presigned PUT failed: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(
            f"presigned PUT failed: HTTP {e.code}. The signed headers must be sent "
            f"exactly as returned by POST /v1/uploads. Response: {body}"
        ) from e


def http_download(url: str, dest: Path, timeout: int = 120) -> None:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as out:
        while chunk := resp.read(64 * 1024):
            out.write(chunk)


def probe_dimensions(path: Path) -> tuple[int, int]:
    """Return (width, height) for a PNG/JPEG/WebP using stdlib only — cross-platform.

    Reads the file header bytes directly so we don't need ImageMagick, sips
    (macOS), or Pillow. Returns (0, 0) on any error.
    """
    try:
        with path.open("rb") as f:
            header = f.read(32)
        if len(header) < 24:
            return 0, 0
        # PNG: signature 89 50 4E 47 0D 0A 1A 0A, then IHDR chunk:
        # [4B length][4B "IHDR"][4B width BE][4B height BE]...
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            w = int.from_bytes(header[16:20], "big")
            h = int.from_bytes(header[20:24], "big")
            return w, h
        # JPEG: walk SOF markers to find dimensions. SOFn = 0xFFC0..0xFFCF
        # (excluding 0xFFC4 DHT, 0xFFC8 reserved, 0xFFCC DAC).
        if header[:2] == b"\xff\xd8":
            with path.open("rb") as f:
                data = f.read()
            i = 2
            while i < len(data) - 8:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xD8, 0xD9):  # SOI / EOI
                    i += 2
                    continue
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    h = int.from_bytes(data[i + 5:i + 7], "big")
                    w = int.from_bytes(data[i + 7:i + 9], "big")
                    return w, h
                seg_len = int.from_bytes(data[i + 2:i + 4], "big")
                i += 2 + seg_len
            return 0, 0
        # WebP (VP8/VP8L/VP8X): "RIFF????WEBP"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            chunk = header[12:16]
            if chunk == b"VP8X" and len(header) >= 30:
                # VP8X: width-1 (3B LE) at offset 24, height-1 at offset 27
                w = int.from_bytes(header[24:27], "little") + 1
                h = int.from_bytes(header[27:30], "little") + 1
                return w, h
            if chunk == b"VP8 ":
                with path.open("rb") as f:
                    data = f.read(40)
                if len(data) >= 30:
                    w = int.from_bytes(data[26:28], "little") & 0x3FFF
                    h = int.from_bytes(data[28:30], "little") & 0x3FFF
                    return w, h
            if chunk == b"VP8L":
                with path.open("rb") as f:
                    data = f.read(25)
                if len(data) >= 25 and data[20] == 0x2F:
                    b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
                    w = ((b1 & 0x3F) << 8 | b0) + 1
                    h = ((b3 & 0x0F) << 10 | b2 << 2 | (b1 >> 6)) + 1
                    return w, h
        return 0, 0
    except Exception as e:  # noqa: BLE001
        log(f"warn: could not probe dimensions for {path}: {e}")
        return 0, 0


def upload_reference(local_path: Path, base_url: str, auth_hdr: str) -> str:
    """Upload a local image via POST /v1/uploads. Returns a reusable assetId.

    The assetId can be reused across calls, so callers should cache it rather
    than re-uploading the same file per variant.
    """
    if not local_path.exists():
        raise SystemExit(f"error: image not found: {local_path}")
    mime = MEDIA_TYPES.get(local_path.suffix.lower())
    if not mime:
        raise SystemExit(
            f"error: unsupported image extension '{local_path.suffix}' for {local_path}. "
            f"Novoads uploads accept: {sorted(MEDIA_TYPES)}"
        )
    size = local_path.stat().st_size
    resp = http_post_json(
        f"{base_url}/v1/uploads",
        {
            "Authorization": auth_hdr,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        {"contentType": mime, "sizeBytes": size},
    )
    asset_id = resp.get("assetId")
    upload_url = resp.get("uploadUrl")
    signed_headers = resp.get("headers") or {}
    if not asset_id or not upload_url:
        raise RuntimeError(f"uploads response missing fields: {resp}")
    max_bytes = resp.get("maxBytes")
    if max_bytes and size > max_bytes:
        raise SystemExit(
            f"error: {local_path.name} is {size} bytes; the upload endpoint caps at {max_bytes}."
        )
    http_put_file(upload_url, local_path, signed_headers)
    return asset_id


def build_pin_block(description: str) -> str:
    """The standard pin block, wrapped around a one-line product description."""
    return PIN_BLOCK_PREFIX + description.strip().rstrip(".") + PIN_BLOCK_GUARD


def build_prompt(
    prompt: str, allow_chrome: bool, no_safe_zone: bool, pin_block: str | None = None
) -> str:
    final = prompt
    # The pin block sits inside the safety suffixes: it is part of what to draw,
    # they are constraints on the whole frame, and they stay outermost.
    if pin_block:
        final += build_pin_block(pin_block)
    if not allow_chrome:
        final += NO_CHROME_SUFFIX
    if not no_safe_zone:
        final += SAFE_ZONE_SUFFIX
    final += GLYPH_SAFETY_SUFFIX
    return final


# Since API 2.39.0 an image render still going after about 105 seconds answers
# 200 with status "running", the same jobId and images: []. That job is paid and
# still rendering, so it is polled to a terminal status and never resubmitted.
POLL_INTERVAL_S = 15
POLL_DEADLINE_S = 900
TERMINAL_STATUSES = {"succeeded", "failed", "blocked", "canceled"}


def http_get_json(url: str, headers: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # strict=False: the echoed prompt can carry raw newlines.
        return json.loads(resp.read().decode("utf-8"), strict=False)


def wait_for_images(job: dict, base_url: str, headers: dict) -> dict:
    """Poll GET /v1/generations/{jobId} until a `running` image job is terminal.

    A job that is already terminal (the usual case) comes back untouched. The
    poll payload is merged over the POST response, so creditsCharged and model
    from the POST survive a poll that omits them. The read lists `images` only on
    a job of one row per picture; a one-picture job's picture is its `outputUrl`,
    so that becomes the one entry of `images`.
    """
    job_id = job.get("jobId")
    status = job.get("status")
    if not job_id or status in TERMINAL_STATUSES:
        return job
    log(f"jobId={job_id} status={status}: still rendering, polling every {POLL_INTERVAL_S}s (not resubmitting)")
    poll_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
    url = f"{base_url}/v1/generations/{job_id}"
    deadline = time.monotonic() + POLL_DEADLINE_S
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_S)
        try:
            polled = http_get_json(url, poll_headers)
        except urllib.error.HTTPError as e:
            if e.code >= 500 or e.code == 429:
                log(f"poll answered HTTP {e.code}, retrying")
                continue
            raise _api_error(e, url) from None
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            log(f"poll failed, retrying: {e}")
            continue
        status = polled.get("status")
        if status in TERMINAL_STATUSES:
            done = {**job, **{k: v for k, v in polled.items() if v is not None}}
            if not polled.get("images") and polled.get("outputUrl"):
                done["images"] = [{"url": polled["outputUrl"]}]
            return done
    log(f"jobId={job_id} still {status} after {POLL_DEADLINE_S}s. Fetch it later with "
        f"GET /v1/generations/{job_id}; do not resubmit.")
    return {**job, "status": status}


# Every POST /v1/images carries an `idempotencyKey`: a new one per call, made in
# main() (or given back with --idempotency-key) and kept for that call's resends.
# The API answers a key it has seen within 24 hours with that first call's answer
# (the same jobId, charge and images) instead of drawing and charging again,
# answers 409 while the first call is still being made, and gives the key back
# when it refuses a call or a draw fails at once and is refunded. So a resend with
# the same key is never a second charge, and a failed POST is sent once more where
# that can help:
#   busy      a 429 (`rate_limited`) or the API's own 503 (`unavailable`): nothing
#             was charged;
#   lost      no answer (a timeout, a dropped connection), an answer that is not
#             JSON, a 500, or another 5xx that is not the API's own 502 or 503: the
#             first send may have been made, and the key answers with it if it was;
#   vendor    the API's 502 `provider_failed` for the vendor's own failure
#             (`reasonCode` vendor_error, vendor_timeout or none): refunded, so the
#             resend is a new draw, charged once if it works.
# Each waits the answer's Retry-After, else error.details.retryAfterSeconds, else
# 2 s, never more than 30 s, and a call gets one such resend. A refusal (any other
# 4xx) and a 502 that names the picture or the prompt (`moderation`,
# `input_image_*`) fail the same way again, so they stop at once.
#   conflict  a 409 for the key: the first call with it is still being made, after a
#             lost answer or when --idempotency-key gives back the key of a run that
#             was cut off. It is asked again after each Retry-After, else 5 s, until
#             the waits on 409s reach 120 s, and never uses the one resend: the API
#             answers a call within about 105 s of its start, which came before the
#             first 409. Past that the API says its answer was not recorded and the
#             same key keeps answering 409, so the script stops and says to find the job.
RESEND_WAIT_DEFAULT_S = 2
RESEND_WAIT_MAX_S = 30
CONFLICT_WAIT_DEFAULT_S = 5
CONFLICT_WAIT_TOTAL_S = 120
KEY_MAX_CHARS = 255  # the API's bound on idempotencyKey, after trimming
VENDOR_REASONS = (None, "vendor_error", "vendor_timeout")
RESEND_SAYS = {
    "busy": "nothing was charged; sending it once more",
    "lost": "it may have been made; sending it once more",
    "vendor": "refunded; drawing it once more",
    "conflict": "the first send with this key is still being made; asking again",
}
# What a POST raises when its answer is lost or cut short.
NO_ANSWER = (OSError, http.client.HTTPException, json.JSONDecodeError, UnicodeDecodeError)


class PostStopped(RuntimeError):
    """POST /v1/images gave up: its last failure, the key every send carried, and the charge it may leave.

    `kind` is the last answer's (failure_kind). `maybe_charged` says a send's answer
    was lost or was the key's 409, or the key came from an earlier run, so the call
    may stand charged, once. `waited` is the seconds waited on the key's 409s.
    """

    def __init__(self, last: BaseException, key: str, kind: str, maybe_charged: bool,
                 waited: float = 0) -> None:
        super().__init__(str(last) or type(last).__name__)
        self.key = key
        self.kind = kind
        self.maybe_charged = maybe_charged
        self.waited = waited


def failure_kind(e: BaseException) -> str:
    """What a failed POST says: busy, lost, vendor, conflict (sent again) or refunded, refused."""
    if not isinstance(e, ApiError):
        return "lost"
    if e.code is None:  # not the API's own answer: an edge page
        return "lost" if e.status >= 500 else "refused"
    if (e.status, e.code) in ((429, "rate_limited"), (503, "unavailable")):
        return "busy"
    if e.status == 409 and e.code == "conflict" and e.details.get("idempotencyKey"):
        return "conflict"
    if e.status == 502 and e.code == "provider_failed":
        return "vendor" if e.details.get("reasonCode") in VENDOR_REASONS else "refunded"
    return "lost" if e.status >= 500 else "refused"


def post_image(url: str, headers: dict, body: dict, key_given: bool = False) -> dict:
    """POST /v1/images, sent again with the same idempotencyKey where that can help (above).

    `key_given` says the key came from --idempotency-key: an earlier run may have sent
    it, so a stop never says that nothing was charged.
    """
    kinds: list[str] = []
    resent = False
    waited = 0.0  # seconds waited on the key's 409s, in all
    while True:
        try:
            return http_post_json(url, headers, body, timeout=GENERATE_TIMEOUT_S)
        except (ApiError, *NO_ANSWER) as e:
            kind = failure_kind(e)
            kinds.append(kind)
            named = e.retry_after if isinstance(e, ApiError) else None
            if kind == "conflict":
                wait = min(max(CONFLICT_WAIT_DEFAULT_S if named is None else named, 1), RESEND_WAIT_MAX_S)
                again = waited + wait <= CONFLICT_WAIT_TOTAL_S
            else:
                wait = min(RESEND_WAIT_DEFAULT_S if named is None else named, RESEND_WAIT_MAX_S)
                again = kind in RESEND_SAYS and not resent
            if not again:
                raise PostStopped(e, body["idempotencyKey"], kind,
                                  key_given or any(k in ("lost", "conflict") for k in kinds),
                                  waited) from e
            if kind == "conflict":
                waited += wait
                # The server's message once per run of 409s; then one short line each.
                said = f"{e}\n  " if kinds[-2:-1] != ["conflict"] else "  HTTP 409 again: "
                log(f"{said}{RESEND_SAYS[kind]} in {wait:g}s with the same idempotencyKey "
                    f"({waited:g}s of {CONFLICT_WAIT_TOTAL_S}s)")
            else:
                resent = True
                log(f"{str(e) or type(e).__name__}\n  {RESEND_SAYS[kind]} in {wait:g}s "
                    f"with the same idempotencyKey, which is never charged twice")
            time.sleep(wait)


def generate(
    model: str,
    prompt: str,
    aspect_ratio: str | None,
    num_images: int,
    ref_asset_ids: list[str],
    product_id: str | None,
    base_url: str,
    auth_hdr: str,
    source_asset_id: str | None = None,
    idempotency_key: str | None = None,
    key_given: bool = False,
) -> dict:
    """One POST /v1/images, polled to a terminal status if it answers `running`. Returns the ImageJob.

    The body carries `idempotency_key` (a new one when none is passed), which every
    resend of it keeps (post_image).
    """
    body: dict = {
        "model": model,
        "prompt": prompt,
        "numImages": num_images,
        "idempotencyKey": idempotency_key or str(uuid.uuid4()),
    }
    # An edit's output tracks the source's shape, so the two are mutually
    # exclusive — the API answers the pair with a 400.
    if source_asset_id:
        body["sourceAssetId"] = source_asset_id
    else:
        body["aspectRatio"] = aspect_ratio
    if ref_asset_ids:
        body["referenceAssetIds"] = ref_asset_ids
    if product_id:
        body["productId"] = product_id

    headers = {
        "Authorization": auth_hdr,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    job = post_image(f"{base_url}/v1/images", headers, body, key_given)
    return wait_for_images(job, base_url, headers)


# Scaffolding that must never reach a render. A finished ad with "Placeholder
# Name" in it is useful to nobody: the person reviewing it cannot judge the
# layout, and the person who ships it ships the word "Placeholder".
#
# The distinction that makes this coherent: a TEMPLATE carries {slots}; a RENDER
# never does. Template mode writes the slots into the library entry, and the
# image it produces is still filled in with plausible content.
#
# Found by rendering one: an ad went out reading "Placeholder Name" over
# "agency.com / partner", beside a blank card and two grey skeleton bars.
PLACEHOLDER_PATTERNS = [
    (r"\bplaceholder\b", "the word 'placeholder'"),
    (r"\blorem ipsum\b", "lorem ipsum"),
    (r"\{[a-z_][a-z0-9_.]*\}", "an unfilled {template slot}"),
    (r"\[[A-Z_]{3,}\]", "an unfilled [TOKEN]"),
    (r"\byour \w+ here\b", "'your ... here'"),
    (r"\bexample\.(com|org|net)\b", "example.com"),
    (r"\bTBD\b", "TBD"),
    (r"\bxxx+\b", "xxx filler"),
    (r"\bskeleton (bar|placeholder)", "a skeleton bar"),
    # Redundant with the first pattern (anything matching this contains
    # "placeholder"), kept only because it names the defect more precisely in the
    # refusal message. No test pins it on purpose — deleting it changes wording,
    # never coverage.
    (r"\bgrey placeholder bar", "a grey placeholder bar"),
    # --- slot-shaped VALUES ---------------------------------------------------
    # The word "placeholder" is the easy tell. These are the ones that shipped
    # anyway: a value that IS a slot without ever saying so. Both of the first
    # two were in the render that motivated this lint, and neither matched
    # anything above it.
    (
        r"\b(?:your|my|our)?(?:brand|company|business|agency|client|store|shop|site|domain)"
        r"\.(?:com|co|io|net|org)\b",
        "a slot-shaped domain (agency.com, yourbrand.com)",
    ),
    (r"@(?:your|creator|user|brand|my)?(?:handle|username|name)\b", "a slot-shaped @handle"),
    (r"\b(?:john|jane) doe\b", "John/Jane Doe"),
    (r"\b(?:name|text|copy|headline|logo|title|image|photo) goes here\b", "'... goes here'"),
    (
        r"\b(?:sample|dummy|filler|mock) (?:text|name|copy|content|data|logo|headline)\b",
        "sample/dummy filler",
    ),
    (r"\binsert (?:name|text|headline|logo|copy|title|brand)\b", "'insert ...'"),
]

# Deliberately NOT patterns, and this is load-bearing rather than an oversight:
# "brand name" and "company name" on their own. A well-written prompt says "the
# company name is set in bold condensed caps" or "the brand name appears once,
# lowercase" — describing a zone, not filling it with a slot. Matching those
# would refuse the careful prompts and let the careless ones through, which is
# the guard backwards. The test file pins both readings: `S` cases must be
# refused, `C` cases must pass. Extend one and re-run BOTH.


def lint_placeholders(prompt: str) -> list[str]:
    """Return a human-readable list of scaffolding found in the prompt."""
    found = []
    for pattern, label in PLACEHOLDER_PATTERNS:
        if re.search(pattern, prompt, re.I):
            found.append(label)
    return found


def main() -> int:
    p = argparse.ArgumentParser(
        description="Round-trip a clone prompt through gpt-image-2 or nano-banana-pro (validator, not a generator).",
    )
    p.add_argument("--prompt", required=True, help="Image prompt (post-rewrite).")
    p.add_argument(
        "--model",
        required=True,
        type=model_arg,
        choices=sorted(MODELS),
        help="Which model to validate against. Each has its own aspect-ratio grid.",
    )
    p.add_argument(
        "--aspect-ratio",
        choices=sorted(ALL_RATIOS),
        help="Canvas ratio. Checked against the chosen model's grid. Required UNLESS "
             "you pass a source to edit, with which it is mutually exclusive. The API "
             "defaults to 1:1 if omitted, which is rarely the ad you want.",
    )
    p.add_argument(
        "--source-image",
        type=Path,
        metavar="PATH",
        help=(
            "EDIT this local image instead of drawing a new one (uploaded for you). "
            "gpt-image-2 only. Phase 7's second instrument: pass the ORIGINAL ad and a "
            "prompt naming only the brand zones that change. Counts against the "
            "reference cap, since that is what it becomes at the provider."
        ),
    )
    p.add_argument(
        "--source-asset-id",
        metavar="ASSET_ID",
        help="Same as --source-image but for an assetId already uploaded — including "
             "the assetId of an image this API generated.",
    )
    p.add_argument(
        "--n",
        type=int,
        default=1,
        help=f"How many images, 1-{MAX_IMAGES}. Sent as numImages in ONE call. Charged per image.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("./generated"),
        help="Output directory for PNGs.",
    )
    p.add_argument(
        "--image-ref",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Reference image path (PNG/JPG/WEBP). Repeatable; the cap depends on "
            "--model ("
            + ", ".join(f"{n}: {m['max_refs']}" for n, m in sorted(MODELS.items()))
            + "). "
            "Uploaded once each; order is preserved and may be addressed positionally "
            "by the prompt."
        ),
    )
    p.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env (default: ./.env).",
    )
    p.add_argument(
        "--product-id",
        help="Novoads productId (defaults to PRODUCT_ID env / .env). "
             "Organizational only — it does not influence what is generated.",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help=f"Novoads API host, no /v1 (default: {BASE_URL_DEFAULT} or NOVOADS_BASE_URL).",
    )
    p.add_argument(
        "--allow-chrome",
        action="store_true",
        help="Allow platform/screenshot UI in the output. Default is to strip all such UI.",
    )
    p.add_argument(
        "--no-safe-zone",
        action="store_true",
        help="Skip the edge-safe suffix. Use only if you genuinely need text to bleed.",
    )
    p.add_argument(
        "--pin-block",
        metavar="PRODUCT_DESCRIPTION",
        help=(
            "Append the shared library's standard brand-pin block, wrapped around this "
            "one-line product description (e.g. 'forest-green pouch with white AG1 "
            "wordmark'). Keep it terse — the guard clause is 346 characters and every "
            "character here comes off your prompt's budget. Unpinned marks get invented."
        ),
    )
    p.add_argument(
        "--idempotency-key",
        metavar="KEY",
        help=(
            "Send this idempotencyKey instead of a new one: the key a run that was cut off "
            "printed before its call. Within 24 hours the API answers it with that call's "
            "answer, charged once, whatever this run's prompt says, so pass it only to run "
            "the same call again, never for a corrected prompt."
        ),
    )
    args = p.parse_args()

    # Before anything that costs: a render must ship finished.
    scaffolding = lint_placeholders(args.prompt)
    if scaffolding:
        log("error: the prompt still contains placeholder scaffolding — "
            + ", ".join(scaffolding) + ".")
        log("A rendered ad must be finished. Invent plausible copy, a plausible "
            "name, a plausible domain; never ship the word 'placeholder', an "
            "empty card or a grey skeleton bar. If you are building a TEMPLATE, "
            "the {slots} belong in the library entry — the image it validates "
            "with is still filled in.")
        return 2

    if args.source_image and args.source_asset_id:
        log("error: pass --source-image OR --source-asset-id, not both.")
        return 2

    editing = bool(args.source_image or args.source_asset_id)

    if editing and args.model != "gpt-image-2":
        log(
            f"error: this validator edits on gpt-image-2 only; {args.model} has no edit "
            f"mode on this API. Drop the source, or switch --model."
        )
        return 2

    if editing and args.aspect_ratio:
        log(
            "error: --aspect-ratio cannot be combined with a source. An edit's output "
            "tracks the source image's shape; the API refuses the pair with a 400. "
            "Preserving that shape is the point of an edit."
        )
        return 2

    if not editing and not args.aspect_ratio:
        log("error: --aspect-ratio is required unless you pass a source to edit.")
        return 2

    if args.source_image and not args.source_image.exists():
        log(f"error: --source-image not found: {args.source_image}")
        return 2

    allowed = MODELS[args.model]["ratios"]
    if args.aspect_ratio and args.aspect_ratio not in allowed:
        log(
            f"error: {args.model} does not accept aspect ratio '{args.aspect_ratio}'. "
            f"It takes: {' '.join(sorted(allowed))}. The request schema is strict, so "
            f"sending it would be a 400."
        )
        return 2

    if not (1 <= args.n <= MAX_IMAGES):
        log(f"error: --n must be 1..{MAX_IMAGES} (got {args.n})")
        return 2

    given_key = None if args.idempotency_key is None else args.idempotency_key.strip()
    if given_key is not None and not 1 <= len(given_key) <= KEY_MAX_CHARS:
        log(f"error: --idempotency-key must be 1 to {KEY_MAX_CHARS} characters after trimming "
            f"(got {len(given_key)}). Pass the key a run printed, as it printed it.")
        return 2

    max_refs = MODELS[args.model]["max_refs"]
    # A source becomes a reference at the provider, so it spends one slot.
    total_refs = len(args.image_ref) + (1 if editing else 0)
    if total_refs > max_refs:
        log(
            f"error: too many reference images ({total_refs} = {len(args.image_ref)} "
            f"--image-ref" + (" + 1 source" if editing else "") + f"); {args.model} "
            f"caps at {max_refs}"
        )
        return 2

    final_prompt = build_prompt(
        args.prompt, args.allow_chrome, args.no_safe_zone, args.pin_block
    )
    max_prompt_chars = MODELS[args.model]["max_prompt_chars"]
    if len(final_prompt) > max_prompt_chars:
        # Pre-network on purpose: the API would answer 400 and charge nothing, but
        # a refusal here also names what to cut, and it names the pin block's share
        # rather than leaving a run to trim the guard that stops invented copy.
        overflow = len(final_prompt) - max_prompt_chars
        pin_chars = len(build_pin_block(args.pin_block)) if args.pin_block else 0
        suffix_chars = len(final_prompt) - len(args.prompt) - pin_chars
        pin_note = (
            f" and the pin block {pin_chars}" if pin_chars else ""
        )
        roomier = sorted(
            (n for n, m in MODELS.items() if m["max_prompt_chars"] > max_prompt_chars),
            key=lambda n: MODELS[n]["max_prompt_chars"],
        )
        log(
            f"error: prompt is {len(final_prompt)} characters after the always-on safety "
            f"suffixes; {args.model} caps at {max_prompt_chars}. Trim about {overflow} "
            f"characters from --prompt (the suffixes add ~{suffix_chars}{pin_note}). "
            f"Your --prompt must be <= "
            f"{max_prompt_chars - suffix_chars - pin_chars} characters with the current flags."
        )
        if roomier:
            # The ceilings are per model, so an overflow here is not an overflow
            # everywhere. Naming the roomier models beats trimming a prompt that
            # the model the run actually wants would have taken whole.
            log(
                "note: this ceiling is this model's, not the API's. Room elsewhere: "
                + ", ".join(f"{n} {MODELS[n]['max_prompt_chars']}" for n in roomier)
                + ". Switch --model rather than trim, when the clone allows it."
            )
        if pin_chars:
            log(
                "note: trim your own copy or the pin block's product description — never the "
                "guard clause. An unpinned mark is an invented mark."
            )
        return 2

    env = load_env(args.env_file)
    auth_hdr = auth_header(env)
    base_url = (
        args.base_url
        or env.get("NOVOADS_BASE_URL")
        or os.environ.get("NOVOADS_BASE_URL")
        or BASE_URL_DEFAULT
    ).rstrip("/")
    product_id = args.product_id or env.get("PRODUCT_ID") or os.environ.get("PRODUCT_ID")

    args.out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = slugify(args.prompt)

    chrome_state = "allowed" if args.allow_chrome else "stripped"
    shape = "source-shaped (edit)" if editing else args.aspect_ratio
    log(
        f"validating {args.n} image(s) model={args.model} aspect={shape} "
        f"chrome={chrome_state} refs={len(args.image_ref)} -> {args.out}/"
    )

    source_asset_id = args.source_asset_id
    if args.source_image:
        log("uploading the source image to edit…")
        source_asset_id = upload_reference(args.source_image, base_url, auth_hdr)

    ref_asset_ids: list[str] = []
    if args.image_ref:
        log(f"uploading {len(args.image_ref)} reference image(s)…")
        for ref in args.image_ref:
            ref_asset_ids.append(upload_reference(ref, base_url, auth_hdr))

    # The key goes out on the wire only once this line is printed, so a run that is
    # cut off (a tool's own timeout, a closed session) has said how to get its call back.
    key = given_key or str(uuid.uuid4())
    if given_key:
        log(f"idempotencyKey {key} (given): a call already made with it answers with its "
            "first answer, charged once")
    else:
        log(f"idempotencyKey {key}: if this run is cut off, run it again with "
            f"--idempotency-key {key} within 24 hours to get this call's answer instead of "
            "a second, paid picture")
    log(f"submitting (this blocks for the render, typically 60-90s)…")
    try:
        job = generate(
            args.model, final_prompt, args.aspect_ratio, args.n, ref_asset_ids,
            product_id, base_url, auth_hdr, source_asset_id,
            idempotency_key=key, key_given=bool(given_key),
        )
    except PostStopped as e:
        log(f"generation FAILED — {e}")
        if e.kind == "conflict":
            log(f"  idempotencyKey {e.key} still answered 409 after {e.waited:g}s of asking: the "
                "API says its first call's answer was not recorded, and that call is charged once "
                "at most. Find its job with `GET /v1/generations?limit=5` and poll it. The same "
                "key keeps answering 409, and a run without it sends a new key, which renders and "
                "charges again.")
        elif e.maybe_charged:
            # The render blocks inside the POST for 60-90s, so a lost answer does
            # NOT mean a lost render: the first send may have landed and been
            # CHARGED while its answer never arrived. Every send carried the same
            # key, so that is once at most, and the same key gets that answer back.
            log(
                "  before running it again: this may have rendered and been charged, once "
                f"(every send carried idempotencyKey {e.key}). Run it again with "
                f"`--idempotency-key {e.key}` within 24 hours: that call's answer comes back "
                "if it was made, or it is drawn if it was not, charged once either way. Or "
                "check `GET /v1/generations?limit=5` for a job matching this prompt and "
                "createdAt — a succeeded row carries the image in `outputUrl`. A run without "
                "the flag sends a new key, so it would render and charge again."
            )
        elif e.kind == "busy":
            log("  nothing was charged: it was refused again after the wait. "
                "Send it again later.")
        return 1
    except Exception as e:  # noqa: BLE001
        # Past the POST (a poll that failed: that job was accepted), or a fault of
        # this script's own: the charge is unknown, so check before running it again.
        log(f"generation FAILED — {e}")
        log(
            "  before running it again: this may have rendered and been charged. Run it "
            f"again with `--idempotency-key {key}` within 24 hours to get that call's answer, "
            "charged once, or check `GET /v1/generations?limit=5` for a job matching this "
            "prompt and createdAt — a succeeded row carries the image in `outputUrl`. "
            "A run without the flag sends a new key, so it would render and charge again."
        )
        return 1

    job_id = job.get("jobId", "")
    credits = job.get("creditsCharged")
    images = job.get("images") or []
    if not images:
        stopped = (f", reasonCode={job.get('reasonCode')}, error={job.get('error')}"
                   if job.get("reasonCode") or job.get("error") else "")
        log(f"generation returned no images (status={job.get('status')}, jobId={job_id}{stopped})")
        return 1

    log(f"jobId={job_id} status={job.get('status')} images={len(images)} credits={credits}")

    results: list[dict] = []
    for i, img in enumerate(images, start=1):
        dest = args.out / f"{ts}-{slug}-v{i}.png"
        log(f"image {i}: downloading -> {dest.name}")
        http_download(img["url"], dest)
        w = img.get("width") or 0
        h = img.get("height") or 0
        if not (w and h):
            w, h = probe_dimensions(dest)
        if w and h and (w < MIN_DIMENSION or h < MIN_DIMENSION):
            log(
                f"image {i}: WARNING {w}x{h} is below the {MIN_DIMENSION}x{MIN_DIMENSION} "
                f"floor. Regenerate or upscale."
            )
        results.append({
            "variant": i,
            "path": str(dest),
            "job_id": job_id,
            "width": w,
            "height": h,
            "prompt": args.prompt,
            "aspect_ratio": args.aspect_ratio or "source",
            "model": job.get("model", args.model),
            "credits_charged": credits,
        })

    for r in results:
        print(json.dumps(r), flush=True)

    if given_key:
        log(f"all {len(results)} image(s) succeeded — {credits} credits, charged once for "
            f"idempotencyKey {key}")
    else:
        log(f"all {len(results)} image(s) succeeded — {credits} credits charged for this call")

    # The lint above runs BEFORE the charge and reads the PROMPT. Nothing here
    # reads the PICTURE. That gap is why the first shipped clone said
    # "Placeholder Name": the prompt was linted, the render never was, and the
    # word was only ever visible in the image. A prompt that simply forgets to
    # name a zone leaves the model free to fill it, and no pattern can see that.
    #
    # Reading an image back is judgement, not a regex, so it belongs with the
    # agent rather than in here — but it must not be optional, and a step nobody
    # is told to take is a step nobody takes. So the script ends by naming it.
    log("")
    log("NOT DONE YET — open each PNG above and read it before calling this finished:")
    log("  1. every zone carries real content — no 'Placeholder', no slot-shaped")
    log("     name, domain or @handle, no empty card, no grey bar, no lorem")
    log("  2. the wordmark is spelled right, letter by letter, against the prompt")
    log("  3. no text from the SOURCE brand survived into the render")
    log("If a zone came back blank or slot-shaped, the prompt under-specified it.")
    log("Name that zone's content in the prompt and re-run — do not ship it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
