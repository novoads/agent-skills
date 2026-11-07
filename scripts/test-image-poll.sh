#!/usr/bin/env bash
# Unit tests for what the three image scripts read off an answer. Spends nothing,
# touches no network: every HTTP call is a stub.
#
# I1 is the one that matters most. A render that outlasts the POST's wait answers
# "running" and is polled, and the read of a one-picture job carries its picture in
# outputUrl with no images[]. A script that reads only images[] reports that paid,
# finished picture as "no images" and exits 1, which invites a second, paid send.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "image-poll tests"

python3 -I - "$(pwd)" <<'PY'
import contextlib, importlib.util, io, json, os, sys, tempfile, urllib.error
from pathlib import Path

sys.dont_write_bytecode = True
root = Path(sys.argv[1])
SCRIPTS = [
    ("chatgpt", root / "skills/chatgpt-image-ad/scripts/generate_image.py", []),
    ("nano", root / "skills/nano-banana-image-ad/scripts/generate_image.py", []),
    ("validate", root / "skills/clone-image-ad/scripts/validate_image.py", ["--model", "gpt-image-2"]),
]
passed = failed = 0


def check(case, cond, label):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok    {case:<5} {label}")
    else:
        failed += 1
        print(f"  FAIL  {case:<5} {label}")


def load(name, path):
    spec = importlib.util.spec_from_file_location("image_poll_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.time.sleep = lambda seconds: None
    mod.probe_dimensions = lambda path: (1080, 1080)
    return mod


def run(mod, path, extra, post, get):
    """main() against stubbed calls: (exit code, stdout JSON lines, log lines, downloaded URLs)."""
    logs, fetched = [], []
    mod.log = logs.append
    mod.http_post_json = lambda url, headers, body, timeout=60: json.loads(json.dumps(post))
    mod.http_get_json = get
    mod.http_download = lambda url, dest, timeout=120: (fetched.append(url), Path(dest).write_bytes(b"png"))
    with tempfile.TemporaryDirectory() as d:
        env = os.path.join(d, ".env")
        with open(env, "w") as fh:
            fh.write("NOVOADS_API_KEY=novo_" + "0" * 64 + "\n")
        argv = sys.argv
        sys.argv = [str(path), "--prompt", "a plain prompt for a stubbed call", "--aspect-ratio", "1:1",
                    "--out", d, "--env-file", env] + extra
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                try:
                    rc = mod.main()
                except SystemExit as e:
                    rc = e.code
        finally:
            sys.argv = argv
    lines = [json.loads(l) for l in out.getvalue().splitlines() if l.startswith("{")]
    return rc, lines, logs, fetched


def reads(body):
    def get(url, headers, timeout=60):
        return json.loads(json.dumps(body))
    return get


def never(url, headers, timeout=60):
    raise AssertionError("a finished POST was polled")


def http_error(code, envelope):
    return urllib.error.HTTPError("https://example.invalid/v1/images", code, "x", {},
                                  io.BytesIO(json.dumps(envelope).encode()))


RUNNING = {"jobId": "j1", "status": "running", "model": "gpt-image-2", "creditsCharged": 5, "images": []}
READ_BASE = {"jobId": "j1", "kind": "image", "model": "gpt-image-2", "prompt": "p",
             "createdAt": "2026-11-07T00:00:00Z", "creditsCharged": 5}
ONE = "https://example.invalid/one.png"
TWO = ["https://example.invalid/a.png", "https://example.invalid/b.png"]

for name, path, extra in SCRIPTS:
    mod = load(name, path)

    # I1: a one-picture job polled to succeeded: outputUrl, no images[].
    rc, lines, logs, fetched = run(mod, path, extra, RUNNING, reads(
        {**READ_BASE, "status": "succeeded", "outputUrl": ONE, "outputUrlExpiresInSeconds": 3600,
         "outputAssetId": "gen/1"}))
    check("I1", rc == 0 and len(lines) == 1 and fetched == [ONE],
          f"{name}: a one-picture job read after a poll is downloaded from outputUrl "
          f"(exit {rc}, {len(lines)} result(s), last log: {logs[-1] if logs else None})")

    # I2: a job of one row per picture polled to succeeded: images[] as before.
    rc, lines, logs, fetched = run(mod, path, extra, RUNNING, reads(
        {**READ_BASE, "status": "succeeded", "outputUrl": TWO[0], "outputUrlExpiresInSeconds": 3600,
         "images": [{"url": u, "expiresInSeconds": 3600} for u in TWO]}))
    check("I2", rc == 0 and len(lines) == 2 and fetched == TWO,
          f"{name}: a job of several rows still reads images[] (exit {rc}, {len(lines)} result(s))")

    # I3: a POST that finished inline is read as it came, with no poll.
    rc, lines, logs, fetched = run(mod, path, extra,
                                   {**RUNNING, "status": "succeeded", "images": [{"url": ONE}]}, never)
    check("I3", rc == 0 and len(lines) == 1 and fetched == [ONE],
          f"{name}: a finished POST is read as it came and never polled (exit {rc})")

    # I4: a job that stopped: no download, and the line says why.
    rc, lines, logs, fetched = run(mod, path, extra, RUNNING, reads(
        {**READ_BASE, "status": "failed", "reasonCode": "vendor_timeout",
         "error": "Generation failed. Credits for this job were refunded."}))
    said = logs[-1] if logs else ""
    check("I4", rc == 1 and not fetched and "reasonCode=vendor_timeout" in said
          and "error=Generation failed." in said,
          f"{name}: a stopped job downloads nothing and its line names reasonCode and error")

    # I5: a refused call prints details.reasonCode; the older branches print as before.
    url = "https://example.invalid/v1/images"
    e = mod._api_error(http_error(502, {"error": {"code": "provider_failed", "message": "m",
                                                  "details": {"jobId": "j1", "reasonCode": "input_image_size"}}}), url)
    e2 = mod._api_error(http_error(429, {"error": {"code": "rate_limited", "message": "m", "details": {
        "reason": "image_concurrency_limit", "retryAfterSeconds": 7}}}), url)
    check("I5", "(reasonCode: input_image_size)" in str(e)
          and "(reason: image_concurrency_limit, retry after 7s)" in str(e2),
          f"{name}: a refused call prints details.reasonCode, and details.reason as before")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
PY
