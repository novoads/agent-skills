#!/usr/bin/env python3
"""
Generate one or more standalone Meta ad creatives via Novoads' POST /v1/images
with ChatGPT Image 2 (gpt-image-2).

Brand contract: this script REFUSES to use any model other than `gpt-image-2`. The
sibling `nano-banana-image-ad/scripts/generate_image.py` handles Nano Banana Pro.

Novoads usually returns the finished images from the POST itself, which blocks for
the render (typically 60-90 seconds). Since API 2.39.0 a render still going after
about 105 seconds answers status "running" with no images; generate() then polls
GET /v1/generations/{jobId} to a terminal status. It never resubmits: that job is paid.

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
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL_DEFAULT = "https://api.novoads.ai"  # host only; this script appends /v1/...
# gpt-image-2's own aspect-ratio grid. Nano Banana Pro and Reve 2.1 accept four more
# (3:2, 3:4, 4:3, 5:4) — this model does not, and the request schema is strict.
ALLOWED_RATIOS = {"1:1", "4:5", "2:3", "9:16", "16:9", "21:9"}
LOCKED_MODEL = "gpt-image-2"
# This model's two caps, both PER MODEL and neither uniform across the set. Read off
# the live per-model request schemas at /v1/openapi.json and verified against deployed
# spec 2.16.0 on 2026-08-08. The whole table, which ./scripts/verify-image-caps.sh
# re-checks against the live spec for all three scripts at once:
#
#   model             referenceAssetIds   prompt chars
#   gpt-image-2                       4         32,000
#   nano-banana-pro                  14         50,000
#   reve-2.1                          8          4,000
#
# 2.16.0 is what ended the single 4,000 budget: only reve-2.1 still carries it, and
# reve-2.1 is reachable only from the clone-image-ad validator.
MAX_REFS = 4
MAX_IMAGES = 4  # numImages enum: 1, 2, 3, 4
MAX_PROMPT_CHARS = 32000  # gpt-image-2 prompt ceiling; the API 400s above it
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


def _api_error(e: urllib.error.HTTPError, url: str) -> RuntimeError:
    """Turn a Novoads error envelope into a message worth reading."""
    raw = e.read().decode("utf-8", errors="replace")
    try:
        err = json.loads(raw).get("error", {})
    except json.JSONDecodeError:
        # Not our envelope at all -> it never reached the application. The one
        # that bites: Cloudflare's bot rule refusing the default urllib UA.
        if "1010" in raw:
            return RuntimeError(
                f"HTTP {e.code} on {url}: Cloudflare error 1010 — the edge refused "
                f"this client, NOT your API key. This is a User-Agent problem: "
                f"send a non-default one (see USER_AGENT above) or use curl. Do not "
                f"regenerate the key or check the subscription."
            )
        return RuntimeError(f"HTTP {e.code} on {url}: {raw}")
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
    return RuntimeError(f"HTTP {e.code} {code} on {url}: {msg}{hint}")


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
    """Upload a local image via POST /v1/uploads. Returns a durable assetId.

    The assetId keeps working across later calls, so callers should cache it rather
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
    from the POST survive a poll that omits them.
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
            return {**job, **{k: v for k, v in polled.items() if v is not None}}
    log(f"jobId={job_id} still {status} after {POLL_DEADLINE_S}s. Fetch it later with "
        f"GET /v1/generations/{job_id}; do not resubmit.")
    return {**job, "status": status}


def generate(
    prompt: str,
    aspect_ratio: str | None,
    num_images: int,
    ref_asset_ids: list[str],
    product_id: str | None,
    base_url: str,
    auth_hdr: str,
    source_asset_id: str | None = None,
) -> dict:
    """One POST /v1/images, polled to a terminal status if it answers `running`. Returns the ImageJob."""
    body: dict = {
        "model": LOCKED_MODEL,
        "prompt": prompt,
        "numImages": num_images,
    }
    # Exactly one of these two ever goes on the wire. The API 400s if both are
    # sent, deliberately: an edit's output tracks the source's shape, so an
    # aspectRatio alongside it would reframe the thing you asked to preserve.
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
    job = http_post_json(
        f"{base_url}/v1/images", headers, body, timeout=GENERATE_TIMEOUT_S
    )
    return wait_for_images(job, base_url, headers)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Generate gpt-image-2 image(s) via Novoads. Brand contract: gpt-image-2 only.",
    )
    p.add_argument("--prompt", required=True, help="Image prompt (post-rewrite).")
    p.add_argument(
        "--aspect-ratio",
        choices=sorted(ALLOWED_RATIOS),
        help=(
            "Canvas ratio. Required for a GENERATION — the API defaults to 1:1 if "
            "omitted, which is rarely the ad you want. Must be OMITTED for an edit: "
            "an edit's output tracks the source's shape and the API 400s if both are sent."
        ),
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
            f"Reference image path (PNG/JPG/WEBP). Repeatable, max {MAX_REFS}. "
            "Uploaded once each; order is preserved and may be addressed positionally "
            "by the prompt."
        ),
    )
    p.add_argument(
        "--source-image",
        type=Path,
        metavar="PATH",
        help=(
            "EDIT this local image instead of drawing a new one (uploaded for you). "
            "The prompt then describes the CHANGE, not the whole picture. Mutually "
            "exclusive with --aspect-ratio: the output tracks the source's shape."
        ),
    )
    p.add_argument(
        "--source-asset-id",
        metavar="ASSET_ID",
        help=(
            "Same as --source-image but for an assetId already uploaded. Use this "
            "when editing something this API generated, or re-editing across runs."
        ),
    )
    p.add_argument(
        "--ref-asset-id",
        action="append",
        default=[],
        metavar="ASSET_ID",
        help=(
            "An assetId already returned by POST /v1/uploads, used as a reference "
            "without re-uploading the bytes. Repeatable, and counts against the same "
            "cap as --image-ref. An assetId is durable, so a batch that reuses one "
            "product photo across many prompts should upload it once and pass the id "
            "here. These are sent before any --image-ref ids."
        ),
    )
    p.add_argument(
        "--model",
        default=LOCKED_MODEL,
        help=f"Locked to {LOCKED_MODEL} by brand contract.",
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
    args = p.parse_args()

    if args.model != LOCKED_MODEL:
        log(
            f"error: brand contract violation — model must be '{LOCKED_MODEL}', got '{args.model}'. "
            f"This skill is locked to ChatGPT Image 2. For Nano Banana Pro, use the "
            f"nano-banana-image-ad skill instead."
        )
        return 2

    if args.source_image and args.source_asset_id:
        log("error: pass --source-image OR --source-asset-id, not both.")
        return 2

    editing = bool(args.source_image or args.source_asset_id)
    if editing and args.aspect_ratio:
        log(
            "error: --aspect-ratio cannot be combined with a source. An edit's output "
            "tracks the source image's shape; the API refuses the pair with a 400. "
            "Drop --aspect-ratio, or drop the source and generate fresh."
        )
        return 2
    if not editing and not args.aspect_ratio:
        log(
            "error: --aspect-ratio is required for a generation. The API defaults to "
            "1:1 when it is omitted, which is rarely the ad you want."
        )
        return 2
    if args.source_image and not args.source_image.exists():
        log(f"error: --source-image not found: {args.source_image}")
        return 2

    if not (1 <= args.n <= MAX_IMAGES):
        log(f"error: --n must be 1..{MAX_IMAGES} (got {args.n})")
        return 2

    # The source counts against the SAME cap: it becomes a reference at the
    # provider, so four refs plus a source is five images and a 400 we paid for.
    total_refs = len(args.image_ref) + len(args.ref_asset_id) + (1 if editing else 0)
    if total_refs > MAX_REFS:
        log(
            f"error: too many references ({len(args.image_ref)} --image-ref + "
            f"{len(args.ref_asset_id)} --ref-asset-id"
            + (" + 1 source" if editing else "")
            + f"); the cap is {MAX_REFS} on {LOCKED_MODEL}"
        )
        return 2

    final_prompt = build_prompt(
        args.prompt, args.allow_chrome, args.no_safe_zone, args.pin_block
    )
    if len(final_prompt) > MAX_PROMPT_CHARS:
        # Pre-network on purpose: the API would answer 400 and charge nothing, but
        # a refusal here also names what to cut, and it names the pin block's share
        # rather than leaving a run to trim the guard that stops invented copy.
        overflow = len(final_prompt) - MAX_PROMPT_CHARS
        pin_chars = len(build_pin_block(args.pin_block)) if args.pin_block else 0
        suffix_chars = len(final_prompt) - len(args.prompt) - pin_chars
        pin_note = (
            f" and the pin block {pin_chars}" if pin_chars else ""
        )
        log(
            f"error: prompt is {len(final_prompt)} characters after the always-on safety "
            f"suffixes; {LOCKED_MODEL} caps at {MAX_PROMPT_CHARS}. Trim about {overflow} "
            f"characters from --prompt (the suffixes add ~{suffix_chars}{pin_note}). "
            f"Your --prompt must be <= "
            f"{MAX_PROMPT_CHARS - suffix_chars - pin_chars} characters with the current flags."
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
    log(
        f"generating {args.n} image(s) model={LOCKED_MODEL} aspect={args.aspect_ratio} "
        f"chrome={chrome_state} refs={len(args.image_ref) + len(args.ref_asset_id)} "
        f"mode={'edit' if editing else 'generate'} -> {args.out}/"
    )

    # Already-uploaded ids go first so their prompt positions are stable across a
    # batch; local files are uploaded after and appended in the order given.
    ref_asset_ids: list[str] = list(args.ref_asset_id)
    if args.image_ref:
        log(f"uploading {len(args.image_ref)} reference image(s)…")
        for ref in args.image_ref:
            ref_asset_ids.append(upload_reference(ref, base_url, auth_hdr))

    source_asset_id = args.source_asset_id
    if args.source_image:
        log("uploading the source image to edit…")
        source_asset_id = upload_reference(args.source_image, base_url, auth_hdr)

    if source_asset_id:
        log(f"EDIT mode — source {source_asset_id}; output shape follows the source")

    log(f"submitting (this blocks for the render, typically 60-90s)…")
    try:
        job = generate(
            final_prompt, args.aspect_ratio, args.n, ref_asset_ids,
            product_id, base_url, auth_hdr, source_asset_id,
        )
    except Exception as e:  # noqa: BLE001
        log(f"generation FAILED — {e}")
        # The render blocks inside the POST for 60-90s, so a lost response does
        # NOT mean a lost render: the job may have landed and been CHARGED while
        # the body never arrived (observed live 2026-08-05 — 55s render, no
        # response, credits gone). There are no idempotency keys, so re-sending
        # renders and charges again. Check before you retry.
        log(
            "  before retrying: this may have rendered and been charged anyway. "
            "Check `GET /v1/generations?limit=5` for a job matching this prompt "
            "and createdAt — a succeeded row carries the image in `outputUrl`. "
            "Re-sending renders and charges a SECOND time; there are no "
            "idempotency keys."
        )
        return 1

    job_id = job.get("jobId", "")
    credits = job.get("creditsCharged")
    images = job.get("images") or []
    if not images:
        log(f"generation returned no images (status={job.get('status')}, jobId={job_id})")
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
            "aspect_ratio": args.aspect_ratio,
            "model": job.get("model", LOCKED_MODEL),
            "credits_charged": credits,
        })

    for r in results:
        print(json.dumps(r), flush=True)

    log(f"all {len(results)} image(s) succeeded — {credits} credits charged for this call")
    return 0


if __name__ == "__main__":
    sys.exit(main())
