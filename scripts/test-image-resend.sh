#!/usr/bin/env bash
# What the four image scripts do when POST /v1/images fails, and the idempotencyKey
# they send. Spends nothing: every call goes to a stand-in server this test starts on
# 127.0.0.1, and no case waits out a real Retry-After (sleep is a stub that writes its
# seconds down; the timeout cases wait a second or two for a real client timeout).
#
# Each case plays one row of the scripts' resend table. An answer that charged nothing
# (a 429, the API's 503) goes out once more after the wait it names, up to 60 s. An answer
# that was lost (a timeout, a dropped connection, a 500) goes out once more with the SAME
# key, which the API answers with the first call's job, so it is never a second charge.
# The key's 409 is asked again every 15 s for up to 120 s, and a 429 met in that time
# waits the same way. A refusal stops at once. A resend under a new key would be a
# second, paid picture, so every resend here is checked to carry the first send's body
# and key, and a run that is cut off is checked to have printed the key that gets its
# call back and the time it sent it, from which every stop's look for the job starts
# (a day earlier for a key an earlier run may have sent). The batch's own main loop is
# run too: each prompt sent with its own key.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "image-resend tests"

python3 -I - "$(pwd)" <<'PY'
import http.server, json, os, re, signal, subprocess, sys, tempfile, threading, time, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1])
PY_SCRIPTS = [
    ("chatgpt", ROOT / "skills/chatgpt-image-ad/scripts/generate_image.py", []),
    ("nano", ROOT / "skills/nano-banana-image-ad/scripts/generate_image.py", []),
    ("validate", ROOT / "skills/clone-image-ad/scripts/validate_image.py", ["--model", "gpt-image-2"]),
]
BATCH = ROOT / "skills/generate-youtube-thumbnail/scripts/generate-batch.sh"
PROMPT = "a plain prompt for a stand-in server"
PNG = (b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4, "big") + b"IHDR" + (1024).to_bytes(4, "big")
       + (1024).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00" + b"\x00" * 20)
BUSY_MSG = ("Several requests were charging credits at the same moment. Nothing was charged for "
            "this one; send it again in a few seconds.")
CONFLICT_MSG = ("A picture with this idempotencyKey is still being made, or its first call failed with its "
                "charge standing. Retry in a moment with the same key and the first answer comes back, or "
                "find its job with GET /v1/generations and poll it. If it still answers conflict after two "
                "minutes, its answer was not recorded.")


def envelope(code, message, **details):
    return {"error": {"code": code, "message": message, "requestId": "req_test", "details": details or None}}


# --- the stand-in server: each POST takes the next planned answer -------------------
class State:
    lock = threading.Lock()
    plan = []
    posts = []
    read = None
    release = threading.Event()


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def answer(self, a):
        payload = a["body"] if isinstance(a["body"], bytes) else json.dumps(a["body"]).encode()
        try:
            self.send_response(a["status"])
            self.send_header("Content-Type", a.get("type", "application/json"))
            for k, v in (a.get("headers") or {}).items():
                self.send_header(k, v)
            # An answer cut short promises more than it sends, then closes.
            self.send_header("Content-Length", str(len(payload) + (1000 if a.get("short") else 0)))
            self.end_headers()
            self.wfile.write(payload)
            if a.get("short"):
                self.close_connection = True
        except OSError:
            pass  # the client gave up first: a timeout case

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        with State.lock:
            State.posts.append({"raw": raw, "headers": {k.lower(): v for k, v in self.headers.items()}})
            a = State.plan.pop(0) if State.plan else {"status": 418, "body": envelope("no_plan", "no answer planned")}
            release = State.release
        if a.get("drop"):
            self.close_connection = True
            return
        if a.get("hold"):
            release.wait(a["hold"])  # until the next case starts
        if a.get("conflict"):
            try:
                key = json.loads(raw).get("idempotencyKey")
            except ValueError:
                key = None
            a = {"status": 409, "headers": a.get("headers"),
                 "body": envelope("conflict", CONFLICT_MSG, idempotencyKey=key)}
        self.answer(a)

    def do_GET(self):
        if self.path == "/img.png":
            self.answer({"status": 200, "type": "image/png", "body": PNG})
        elif self.path.startswith("/v1/generations/") and State.read is not None:
            self.answer({"status": 200, "body": State.read})
        else:
            self.answer({"status": 404, "body": envelope("not_found", "no such path")})


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # A client that gave up or was killed mid-call is what the timeout and cut-off
        # cases do on purpose; any other error is the stand-in's own, and is shown.
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)


server = Server(("127.0.0.1", 0), Handler)
BASE = "http://127.0.0.1:%d" % server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()


def reset(plan, read=None):
    with State.lock:
        State.release.set()
        State.release = threading.Event()
        State.plan[:] = list(plan)
        State.posts[:] = []
        State.read = read


def posts():
    with State.lock:
        return list(State.posts)


# --- the answers ---------------------------------------------------------------------
def ok(n=1):
    return {"status": 200, "body": {"jobId": "job-1", "status": "succeeded", "model": "m", "creditsCharged": 5 * n,
                                    "images": [{"url": BASE + "/img.png", "width": 1024, "height": 1024}] * n}}


def busy(header="1", details=1):
    d = {"reason": "credit_balance_busy"}
    if details is not None:
        d["retryAfterSeconds"] = details
    return {"status": 429, "headers": {"Retry-After": header} if header else {},
            "body": envelope("rate_limited", BUSY_MSG, **d)}


def e502(reason):
    d = {"jobId": "job-9"}
    if reason:
        d["reasonCode"] = reason
    return {"status": 502, "body": envelope("provider_failed", "The image service could not finish this job. "
                                            "Credits were refunded.", **d)}


def c409(retry_after=None):
    return {"conflict": True, "headers": {"Retry-After": str(retry_after)} if retry_after else {}}


OK = ok()
E500 = {"status": 500, "body": envelope("internal_error", "Something went wrong on our side.")}
E500_WAIT_120 = dict(E500, headers={"Retry-After": "120"})
E503 = {"status": 503, "headers": {"Retry-After": "1"},
        "body": envelope("unavailable", "The picture service was full; nothing was charged.",
                         reason="image_capacity", retryAfterSeconds=1)}
E503_WAIT_45 = dict(E503, headers={"Retry-After": "45"})
E400 = {"status": 400, "body": envelope("invalid_input", "Invalid request body.",
                                        issues=[{"path": ["aspectRatio"], "message": "bad"}])}
OTHER409 = {"status": 409, "body": envelope("conflict", "The object is not in a state that allows this.")}
EDGE403 = {"status": 403, "type": "text/plain", "body": b"error code: 1010"}
EDGE502 = {"status": 502, "type": "text/html", "body": b"<html>502 Bad Gateway</html>"}
BARE500 = {"status": 500, "body": {"message": "no envelope code"}}
ERRSTR500 = {"status": 500, "body": {"error": "upstream failed"}}
HTML200 = {"status": 200, "type": "text/html", "body": b"<html>not the API</html>"}
DROP = {"drop": True}
HELD = dict(OK, hold=30)
RUNNING = {"status": 200, "body": {"jobId": "job-1", "status": "running", "model": "m", "creditsCharged": 5,
                                   "images": []}}
READ_OK = {"jobId": "job-1", "status": "succeeded", "kind": "image", "model": "m", "creditsCharged": 5,
           "outputUrl": BASE + "/img.png", "outputUrlExpiresInSeconds": 3600}

# What each family prints. {k} is the key every send of the call carried. None: that family
# does not say it in that case (the batch's stops name BATCH_KEY only when the batch set it).
LOOKUP = "GET /v1/generations?kind=image&limit=50&updatedSince="
NO_JOB = "no such job since then means nothing was charged"
REAPER = ("may be waiting for the API to fail it and refund it, usually within about 30 minutes of the charge "
          "and at the latest about 2 hours after it")
# A rerun with a key whose call failed with its charge standing: 409, then the conflict stop.
KEPT = ("or, where that call failed with its charge standing, it answers 409 until its 24 hours pass, "
        "and the run then stops with where to find its job")
SAYS = {
    "py": {
        "busy": "nothing was charged; sending it once more in",
        "busy-loop": "nothing was charged for this send; asking again in",
        "lost": "it may have been made; sending it once more in",
        "vendor": "refunded; drawing it once more in",
        "conflict": "the first send with this key is still being made; asking again in",
        "again": "HTTP 409 again: ",
        "stop-busy": "nothing was charged: it was refused again after the wait",
        "stop-maybe": ("this may have rendered and been charged, once (every send carried idempotencyKey {k}). "
                       "Run it again with `--idempotency-key {k}`"),
        "stop-conflict": "idempotencyKey {k} still answered 409 after 120s of asking",
        "after-24h": "After 24 hours that key draws and charges again",
        "lookup": LOOKUP,
        "no-job": NO_JOB,
        "reaper": REAPER,
        "kept": KEPT,
        "redraw": ("This key keeps answering 409 for its 24 hours: once that job has failed or is not there, run "
                   "it again without --idempotency-key, a new key, charged once. Sooner, the picture may stand "
                   "charged twice"),
        "past-post": ("this may have rendered and been charged. Run it again with `--idempotency-key {k}` within "
                      "24 hours to get that call's answer"),
        "keyline": "idempotencyKey {k}, sent ",
        "cut-off": "if this run is cut off, run it again with --idempotency-key {k} within 24 hours",
        "edge": "Cloudflare error 1010",
        "input": "(reasonCode: input_image_unreadable)",
    },
    "batch": {
        "busy": "nothing was charged: sending it once more in",
        "busy-loop": "nothing was charged for this send: asking again in",
        "lost": "it may have been made: sending it once more in",
        "vendor": "refunded: drawing it once more in",
        "conflict": "HTTP 409, the first send is still being made, charged once at most: asking again in",
        "again": "HTTP 409 again, still being made and charged once at most",
        "stop-busy": "refused again after the wait. Nothing was charged",
        "stop-maybe": "This may have rendered and been charged, once (every send carried idempotencyKey {k})",
        "stop-conflict": "idempotencyKey {k} still answered 409 after 120s of asking",
        "after-24h": None,
        "lookup": LOOKUP,
        "no-job": NO_JOB,
        "reaper": REAPER,
        "kept": None,
        "redraw": ("This key keeps answering 409 for its 24 hours, and the same BATCH_KEY sends it again for this "
                   "thumbnail: once that job has failed or is not there, run this thumbnail alone with a new batch "
                   "key (only its prompt in PROMPTS, no BATCH_KEY), one new key, charged once. Sooner, it may stand "
                   "charged twice"),
        "past-post": None,
        "keyline": "[#1] Submitting with idempotencyKey {k}, sent ",
        "cut-off": None,
        "edge": "ERROR: HTTP 403:",
        "input": "input_image_unreadable",
    },
}
# The stop lines without the key, for "this run must not say it".
NOT = {
    "py": {"stop-busy": "nothing was charged: it was refused again", "stop-maybe": "may have rendered and been charged",
           "stop-conflict": "still answered 409 after"},
    "batch": {"stop-busy": "Nothing was charged: send it again later", "stop-maybe": "may have rendered and been charged",
              "stop-conflict": "still answered 409 after"},
}
STOPS = ("stop-busy", "stop-maybe", "stop-conflict")

# What a stop says beyond its first line: where to look, what an empty look means, and how
# a key the API kept is met (MAYBE) or drawn again under a new key (CONFLICT_STOP).
MAYBE = ["stop-maybe", "after-24h", "lookup", "no-job", "kept"]
CONFLICT_STOP = ["stop-conflict", "lookup", "no-job", "reaper", "redraw"]

# name, plan, exit, POSTs, waits slept, said, not said, the server message count (msg, n)
CASES = [
    ("429>200", [busy("1"), OK], 0, 2, [1], ["busy"], STOPS, None),
    ("429-details", [busy(None, 1), OK], 0, 2, [1], ["busy"], STOPS, None),
    ("429-no-wait", [busy(None, None), OK], 0, 2, [2], ["busy"], STOPS, None),
    ("429x2", [busy("1"), busy("1"), OK], 1, 2, [1], ["stop-busy"], ("stop-maybe", "stop-conflict"), (BUSY_MSG, 2)),
    ("429-wait-45", [busy("45", 45), OK], 0, 2, [45], ["busy"], STOPS, None),
    ("503>200", [E503, OK], 0, 2, [1], ["busy"], STOPS, None),
    ("503-wait-45", [E503_WAIT_45, OK], 0, 2, [45], ["busy"], STOPS, None),
    ("503x2", [E503, E503], 1, 2, [1], ["stop-busy"], ("stop-maybe",), None),
    ("500>200", [E500, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("500x2", [E500, E500, OK], 1, 2, [2], MAYBE, ("stop-busy", "stop-conflict"), None),
    ("500-wait-capped-30", [E500_WAIT_120, OK], 0, 2, [30], ["lost"], STOPS, None),
    ("drop>200", [DROP, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("cut-short>200", [dict(OK, short=True), OK], 0, 2, [2], ["lost"], STOPS, None),
    ("html-200>200", [HTML200, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("error-string-500", [ERRSTR500, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("no-code-500", [BARE500, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("edge-502", [EDGE502, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("edge-403", [EDGE403, OK], 1, 1, [], ["edge"], STOPS, None),
    ("400", [E400, OK], 1, 1, [], [], STOPS, None),
    ("502-vendor", [e502("vendor_error"), OK], 0, 2, [2], ["vendor"], STOPS, None),
    ("502-no-reason", [e502(None), OK], 0, 2, [2], ["vendor"], STOPS, None),
    ("502x2", [e502("vendor_timeout"), e502("vendor_timeout"), OK], 1, 2, [2], [], STOPS, None),
    ("502-input", [e502("input_image_unreadable"), OK], 1, 1, [], ["input"], STOPS, None),
    ("502-moderation", [e502("moderation"), OK], 1, 1, [], [], STOPS, None),
    ("409>200", [c409(), OK], 0, 2, [15], ["conflict"], STOPS, (CONFLICT_MSG, 1)),
    ("409x3>200", [c409(), c409(), c409(), OK], 0, 4, [15, 15, 15], ["conflict", "again"], STOPS, (CONFLICT_MSG, 1)),
    ("409-wait-7", [c409(7), OK], 0, 2, [7], ["conflict"], STOPS, None),
    ("409-for-120s", [c409()] * 9 + [OK], 1, 9, [15] * 8, CONFLICT_STOP, ("stop-busy", "stop-maybe"), None),
    ("409-wait-30", [c409(30)] * 5 + [OK], 1, 5, [30] * 4, CONFLICT_STOP, ("stop-busy",), None),
    ("500>409>200", [E500, c409(), OK], 0, 3, [2, 15], ["lost", "conflict"], STOPS, None),
    # A 502 whose credits did not all come back keeps its key: the resend meets the 409 and is asked like one.
    ("502>409>200", [e502("vendor_error"), c409(), OK], 0, 3, [2, 15], ["vendor", "conflict"], STOPS, None),
    ("502>409-for-120s", [e502(None)] + [c409()] * 9 + [OK], 1, 10, [2] + [15] * 8, ["vendor"] + CONFLICT_STOP,
     ("stop-busy", "stop-maybe"), None),
    ("drop>409x2>200", [DROP, c409(), c409(), OK], 0, 4, [2, 15, 15], ["lost", "again"], STOPS, None),
    ("409>500>200", [c409(), E500, OK], 0, 3, [15, 2], ["conflict", "lost"], STOPS, None),
    ("409>500x2", [c409(), E500, E500, OK], 1, 3, [15, 2], MAYBE, ("stop-busy", "stop-conflict"), None),
    # Once the key has answered 409, a 429 or 503 waits like a 409 and never uses the one resend.
    ("409>429>200", [c409(), busy("1"), OK], 0, 3, [15, 1], ["conflict", "busy-loop"], STOPS, None),
    ("409>429x3>200", [c409()] + [busy("1")] * 3 + [OK], 0, 5, [15, 1, 1, 1], ["conflict", "busy-loop"], STOPS, None),
    ("409>503>200", [c409(), E503, OK], 0, 3, [15, 1], ["conflict", "busy-loop"], STOPS, None),
    ("409>429>409>200", [c409(), busy("1"), c409(), OK], 0, 4, [15, 1, 15], ["conflict", "busy-loop"], STOPS,
     (CONFLICT_MSG, 2)),
    ("409>429-0s>200", [c409(), busy("0", 0), OK], 0, 3, [15, 1], ["busy-loop"], STOPS, None),
    ("429>409>429>200", [busy("1"), c409(), busy("1"), OK], 0, 4, [1, 15, 1], ["busy", "conflict", "busy-loop"],
     STOPS, None),
    ("409x7>429-30s", [c409()] * 7 + [busy("30", 30), OK], 1, 8, [15] * 7, MAYBE, ("stop-busy", "stop-conflict"),
     None),
    ("409-no-key", [OTHER409, OK], 1, 1, [], [], STOPS, None),
    ("drop>429", [DROP, busy("1"), OK], 1, 2, [2], MAYBE, ("stop-busy",), None),
    ("429>500", [busy("1"), E500, OK], 1, 2, [1], MAYBE, ("stop-busy",), None),
    ("wait-capped-60", [busy("120", 120), OK], 0, 2, [60], ["busy"], STOPS, None),
]
# A real client timeout: the server holds the answer, the client gives up after 1 s.
TIMEOUT_CASES = [
    ("timeout>200", [HELD, OK], 0, 2, [2], ["lost"], STOPS, None),
    ("timeoutx2", [HELD, HELD], 1, 2, [2], MAYBE, ("stop-busy",), None),
]

results = []


def check(name, cond, label):
    results.append(bool(cond))
    print("  %s  %-30s %s" % ("ok  " if cond else "FAIL", name, label), flush=True)


def bodies(ps):
    out = []
    for p in ps:
        try:
            out.append(json.loads(p["raw"]))
        except ValueError:
            out.append(None)
    return out


def keys_of(ps):
    return [b.get("idempotencyKey") if isinstance(b, dict) else None for b in bodies(ps)]


def is_uuid(k, version):
    try:
        u = uuid.UUID(k)
    except (TypeError, ValueError, AttributeError):
        return False
    return u.version == version and str(u) == k


def one_call(ps, key=None):
    """Every POST of one call: the same body, its key in the body (a new uuid4, or the one given), no key header."""
    bs = bodies(ps)
    if not bs or not isinstance(bs[0], dict):
        return False
    k = bs[0].get("idempotencyKey")
    right_key = is_uuid(k, 4) if key is None else k == key
    return right_key and all(b == bs[0] for b in bs) and not any("idempotency-key" in p["headers"] for p in ps)


STAMP = r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)"


def utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def stamps(out, k, given, when, looked):
    """What is wrong with the key line's send time and the lookups' bound, or None.

    The key line says when its call was sent, in UTC, as the run's clock read it; every
    lookup a stop prints starts a minute before that, and a day more for a given key.
    `when` is (before, after) the run, in UTC.
    """
    sent = re.findall(r"idempotencyKey %s(?: \(given\))?, sent %s" % (re.escape(str(k)), STAMP), out)
    if len(sent) != 1:
        return "%d key lines with a send time" % len(sent)
    t = utc(sent[0])
    if not when[0] - timedelta(seconds=2) <= t <= when[1]:
        return "sent %s, not the run's UTC time" % sent[0]
    looks = re.findall(re.escape(LOOKUP) + STAMP, out)
    back = timedelta(days=1 if given else 0, seconds=60)
    if looked and (not looks or any(utc(s) != t - back for s in looks)):
        return "lookup since %s for a send at %s" % (looks, sent[0])
    return None


def judge(family, label, run, case, key=None, given=False):
    rc, out, ps, pics, waits = run[:5]
    _, _, want_rc, want_posts, want_waits, said, not_said, count = case
    k = keys_of(ps)[0] if ps else None
    bad = []
    # Every run that sent a call printed when; every lookup it printed starts from that time.
    why = stamps(out, k, given, run[-1], "lookup" in said) if ps else None
    if why:
        bad.append(why)
    if rc != want_rc:
        bad.append("exit %s" % rc)
    if len(ps) != want_posts:
        bad.append("%d POSTs" % len(ps))
    if ps and not one_call(ps, key):
        bad.append("a resend changed the body or the key")
    if waits != [float(w) for w in want_waits]:
        bad.append("waited %s" % waits)
    if pics != (1 if want_rc == 0 else 0):
        bad.append("%d picture(s)" % pics)
    for s in said:
        if SAYS[family][s] is not None and SAYS[family][s].format(k=k) not in out:
            bad.append("did not say " + s)
    for s in not_said:
        if NOT[family][s] in out:
            bad.append("said " + s)
    if count and out.count(count[0]) != count[1]:
        bad.append("the server's message %d times" % out.count(count[0]))
    if family == "batch":
        files = run[5]
        if any("_post." in f for f in files):
            bad.append("left " + ", ".join(f for f in files if "_post." in f))
        if (want_rc != 0) != ("1_error.json" in files):
            bad.append("error file %s" % ("missing" if want_rc else "written"))
    check(label, not bad, "; ".join(bad) or "exit %s, %d POST(s), waits %s" % (rc, len(ps), waits))


# --- the Python scripts, each run in its own interpreter -------------------------------
# sleep is a stub that writes its seconds down; IMAGE_RESEND_TIMEOUT caps the client's
# timeout so a held answer is a real timeout in one second.
BOOT = r'''
import os, runpy, sys, time, urllib.request
def _sleep(seconds):
    with open(os.environ["IMAGE_RESEND_SLEPT"], "a") as fh:
        fh.write("%g\n" % seconds)
time.sleep = _sleep
_cap = os.environ.get("IMAGE_RESEND_TIMEOUT")
if _cap:
    _urlopen = urllib.request.urlopen
    def _capped(*args, **kwargs):
        kwargs["timeout"] = min(float(kwargs.get("timeout") or 60), float(_cap))
        return _urlopen(*args, **kwargs)
    urllib.request.urlopen = _capped
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
CLEAN = {k: v for k, v in os.environ.items() if not k.startswith(("NOVOADS_", "PRODUCT_ID", "BATCH_KEY"))}
WORK = Path(tempfile.mkdtemp(prefix="image-resend."))


def py_argv(path, fixed, out_dir, env_file, extra):
    return [sys.executable, "-I", "-c", BOOT, str(path), *fixed, "--prompt", PROMPT, "--aspect-ratio", "1:1",
            "--out", str(out_dir), "--env-file", str(env_file), "--base-url", BASE, *extra]


def py_run(path, fixed, plan, extra=(), cap=None, read=None):
    reset(plan, read)
    d = Path(tempfile.mkdtemp(dir=WORK))
    env_file = d / ".env"
    env_file.write_text("NOVOADS_API_KEY=novo_" + "0" * 64 + "\n")
    slept = d / "slept.txt"
    env = dict(CLEAN, IMAGE_RESEND_SLEPT=str(slept))
    if cap:
        env["IMAGE_RESEND_TIMEOUT"] = str(cap)
    began = datetime.now(timezone.utc)
    try:
        p = subprocess.run(py_argv(path, fixed, d, env_file, extra), capture_output=True, text=True, env=env,
                           timeout=120)
        rc, out = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        rc, out = "timeout", ""
    pics = len(list(d.glob("*.png")))
    waits = [float(w) for w in slept.read_text().split()] if slept.exists() else []
    return rc, out, posts(), pics, waits, (began, datetime.now(timezone.utc))


def until_posted(n, seconds=20):
    end = time.time() + seconds
    while time.time() < end and len(posts()) < n:
        time.sleep(0.05)
    return len(posts()) >= n


try:
    for name, path, fixed in PY_SCRIPTS:
        for case in CASES:
            judge("py", "%s:%s" % (name, case[0]), py_run(path, fixed, case[1]), case)
        for case in TIMEOUT_CASES:
            judge("py", "%s:%s" % (name, case[0]), py_run(path, fixed, case[1], cap=1), case)

        # One key covers every picture of numImages, and stays on the resend.
        rc, out, ps, pics, waits = py_run(path, fixed, [E500, ok(2)], extra=["--n", "2"])[:5]
        nb = [b.get("numImages") for b in bodies(ps)]
        check("%s:n2" % name, rc == 0 and len(ps) == 2 and one_call(ps) and nb == [2, 2] and pics == 2,
              "--n 2, a 500 then 200: one key for both pictures, kept on the resend (numImages %s, exit %s)" % (nb, rc))

        # Two runs draw two keys.
        r1, r2 = py_run(path, fixed, [OK]), py_run(path, fixed, [OK])
        k1, k2 = (keys_of(r1[2]) or [None])[0], (keys_of(r2[2]) or [None])[0]
        check("%s:new-key-per-run" % name, r1[0] == 0 and r2[0] == 0 and is_uuid(k1, 4) and is_uuid(k2, 4) and k1 != k2,
              "two runs send two different uuid4 keys")

        # A run cut off mid-call has printed its key; run again with it, the first call answers.
        reset([HELD])
        d = Path(tempfile.mkdtemp(dir=WORK))
        env_file = d / ".env"
        env_file.write_text("NOVOADS_API_KEY=novo_" + "0" * 64 + "\n")
        began = datetime.now(timezone.utc)
        with open(d / "err.txt", "w") as err:
            p = subprocess.Popen(py_argv(path, fixed, d, env_file, []), stdout=subprocess.DEVNULL, stderr=err,
                                 env=dict(CLEAN, IMAGE_RESEND_SLEPT=str(d / "slept.txt")))
            arrived = until_posted(1)
            p.kill()
            p.wait()
        said = (d / "err.txt").read_text()
        k = (keys_of(posts()) or [None])[0]
        check("%s:cut-off-prints-key" % name, arrived and is_uuid(k, 4) and SAYS["py"]["keyline"].format(k=k) in said
              and SAYS["py"]["cut-off"].format(k=k) in said
              and not stamps(said, k, False, (began, datetime.now(timezone.utc)), False),
              "a run killed while its POST is held has printed its key, when it sent it, and how to send it again")
        run = py_run(path, fixed, [OK], extra=["--idempotency-key", k or "missing"])
        check("%s:cut-off-run-again" % name, run[0] == 0 and len(run[2]) == 1 and one_call(run[2], k) and run[3] == 1
              and "idempotencyKey %s (given)" % k in run[1] and "charged once for idempotencyKey %s" % k in run[1],
              "run again with --idempotency-key: the body carries that key and the answer is saved (exit %s)" % run[0])

        # A given key whose first answer was `running`: polled to its picture, not sent again.
        run = py_run(path, fixed, [RUNNING], extra=["--idempotency-key", "key-from-an-earlier-run"], read=READ_OK)
        check("%s:given-running" % name, run[0] == 0 and len(run[2]) == 1 and one_call(run[2], "key-from-an-earlier-run")
              and run[3] == 1 and run[4] == [15.0],
              "a given key answered `running` is polled once to its picture (exit %s, waits %s)" % (run[0], run[4]))
        # With a given key, a stop never says nothing was charged: an earlier run may have been,
        # so its look for the job reaches a day further back.
        judge("py", "%s:given-429x2" % name,
              py_run(path, fixed, [busy("1"), busy("1")], extra=["--idempotency-key", "key-from-an-earlier-run"]),
              ("", [], 1, 2, [1], MAYBE, ("stop-busy",), None), key="key-from-an-earlier-run", given=True)
        given = py_run(path, fixed, [c409(), OK], extra=["--idempotency-key", "key-from-an-earlier-run"])
        judge("py", "%s:given-409>200" % name, given, ("", [], 0, 2, [15], ["conflict"], STOPS, None),
              key="key-from-an-earlier-run", given=True)
        # A given key may be older than 24 hours: the run says so before its call.
        check("%s:given-key-after-24h" % name,
              re.search(r"idempotencyKey key-from-an-earlier-run \(given\), sent %s: a call made with it in the "
                        r"last 24 hours" % STAMP, given[1]) is not None
              and "after 24 hours it draws and charges again" in given[1],
              "the given-key line says when it was sent and that a key older than 24 hours draws and charges again")
        # A given key that still answers 409 after 120 s was kept by the API: the stop looks a day
        # back and says to draw the picture again under a new key once its job has failed.
        judge("py", "%s:given-409-for-120s" % name,
              py_run(path, fixed, [c409()] * 9 + [OK], extra=["--idempotency-key", "key-from-an-earlier-run"]),
              ("", [], 1, 9, [15] * 8, CONFLICT_STOP, ("stop-busy", "stop-maybe"), None),
              key="key-from-an-earlier-run", given=True)
        # A poll refused after the POST was accepted: that job is charged, and the stop says where it is.
        judge("py", "%s:poll-refused" % name, py_run(path, fixed, [RUNNING]),
              ("", [], 1, 1, [15], ["past-post", "lookup", "no-job"], ("stop-busy", "stop-conflict"), None))
        # The API's bounds: 1 to 255 characters after trimming, refused before any call.
        for label, given, want in (("blank", "   ", None), ("256-chars", "k" * 256, None),
                                   ("255-chars", "k" * 255, "k" * 255), ("trimmed", "  key-1  ", "key-1")):
            run = py_run(path, fixed, [OK], extra=["--idempotency-key", given])
            if want is None:
                check("%s:key-%s" % (name, label), run[0] == 2 and not run[2] and "--idempotency-key must be" in run[1],
                      "a key %s is refused before any call (exit %s, %d POSTs)" % (label, run[0], len(run[2])))
            else:
                check("%s:key-%s" % (name, label), run[0] == 0 and one_call(run[2], want),
                      "a key %s is sent as %d characters (exit %s)" % (label, len(want), run[0]))

    # --- generate-batch.sh: its own functions, under its own shell options ---------------
    runner = WORK / "run_batch.sh"
    runner.write_text(r'''#!/usr/bin/env bash
# generate-batch.sh's own generate_one, thumbnail_keys and generate_all (the main loop),
# against the stand-in server. Args: batch-path api-base output-dir sleep-log mode [prompt ...]
set -euo pipefail
B="$1"; API="$2"; OUTPUT_DIR="$3"; SLEPT="$4"; MODE="$5"; shift 5
NOVOADS_API_KEY=x PRODUCT_ID="" POLL_INTERVAL_S=15 POLL_DEADLINE_S=60 MAX_PARALLEL=4
MODEL="${T_MODEL:-nano-banana-pro}"; ASPECT="${T_ASPECT:-16:9}"
declare -a COMMON_REFS=()
while IFS= read -r r; do [ -z "$r" ] || COMMON_REFS+=("$r"); done <<EOF
${T_REFS:-}
EOF
sleep() { echo "$1" >> "$SLEPT"; }
if [ -n "${CURL_MAX_TIME:-}" ]; then
  curl() {
    local -a a
    local x prev=""
    a=()
    for x in "$@"; do
      if [ "$prev" = "--max-time" ]; then a+=("$CURL_MAX_TIME"); else a+=("$x"); fi
      prev=$x
    done
    command curl "${a[@]}"
  }
fi
eval "$(awk '/^generate_one\(\) \{/{on=1} on{print} on && /^\}$/{n++; if (n == 2) exit}' "$B")"
eval "$(awk '/^thumbnail_keys\(\) \{/{on=1} on{print} on && /^\}$/{exit}' "$B")"
eval "$(awk '/^generate_all\(\) \{/{on=1} on{print} on && /^\}$/{exit}' "$B")"
case "$MODE" in
  one) generate_one 1 "$1" "[]" "${T_KEY:-}" ;;
  two) generate_one 1 "$1" "[]"; generate_one 2 "$2" "[]" ;;
  keys) thumbnail_keys "$@" ;;
  all) generate_all "[]" "$@"; echo "BATCH_KEY_GIVEN=[$BATCH_KEY_GIVEN] BATCH_KEY=[$BATCH_KEY]" ;;
esac
''')

    def batch_argv(out_dir, slept, mode, prompts):
        return ["bash", str(runner), str(BATCH), BASE, str(out_dir), str(slept), mode, *prompts]

    def batch_run(plan, mode="one", prompts=(PROMPT,), env_extra=None, cap=None, read=None):
        reset(plan, read)
        d = Path(tempfile.mkdtemp(dir=WORK))
        out_dir = d / "out"
        out_dir.mkdir()
        slept = d / "slept.txt"
        env = dict(CLEAN, **(env_extra or {}))
        if cap:
            env["CURL_MAX_TIME"] = str(cap)
        began = datetime.now(timezone.utc)
        try:
            p = subprocess.run(batch_argv(out_dir, slept, mode, prompts), capture_output=True, text=True, env=env,
                               timeout=180)
            rc, out = p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            rc, out = "timeout", ""
        files = sorted(f.name for f in out_dir.iterdir())
        pics = sum(1 for f in files if f.endswith("_thumbnail.png"))
        waits = [float(w) for w in slept.read_text().split()] if slept.exists() else []
        return rc, out, posts(), pics, waits, files, out_dir, (began, datetime.now(timezone.utc))

    for case in CASES:
        judge("batch", "batch:%s" % case[0], batch_run(case[1]), case)
    for case in TIMEOUT_CASES:
        judge("batch", "batch:%s" % case[0], batch_run(case[1], cap=1), case)

    run = batch_run([OK, OK], mode="two", prompts=(PROMPT, PROMPT + " again"))
    ks = keys_of(run[2])
    check("batch:new-key-per-thumbnail", run[0] == 0 and len(ks) == 2 and all(is_uuid(k, 4) for k in ks) and ks[0] != ks[1],
          "two thumbnails with no key drawn send two different uuid4 keys")

    # The key a thumbnail is given goes in its body, and is printed before its POST.
    run = batch_run([OK], env_extra={"T_KEY": "key-from-thumbnail-keys"})
    check("batch:given-key", run[0] == 0 and one_call(run[2], "key-from-thumbnail-keys")
          and SAYS["batch"]["keyline"].format(k="key-from-thumbnail-keys") in run[1],
          "the key generate_one is handed is the one it sends and prints (exit %s)" % run[0])
    # A run cut off mid-call has printed the key; that key, sent again, gets the first answer.
    reset([HELD])
    d = Path(tempfile.mkdtemp(dir=WORK))
    (d / "out").mkdir()
    began = datetime.now(timezone.utc)
    with open(d / "out.txt", "w") as fh:
        p = subprocess.Popen(batch_argv(d / "out", d / "slept.txt", "one", (PROMPT,)), stdout=fh, stderr=fh,
                             env=CLEAN, start_new_session=True)
        arrived = until_posted(1)
        os.killpg(p.pid, signal.SIGKILL)  # the runner and the curl it started: this test's own
        p.wait()
    k = (keys_of(posts()) or [None])[0]
    said = (d / "out.txt").read_text()
    check("batch:cut-off-prints-key", arrived and is_uuid(k, 4) and SAYS["batch"]["keyline"].format(k=k) in said
          and not stamps(said, k, False, (began, datetime.now(timezone.utc)), False),
          "a run killed while its POST is held has printed its key and when it sent it")
    run = batch_run([OK], env_extra={"T_KEY": k or "missing"})
    check("batch:cut-off-run-again", run[0] == 0 and len(run[2]) == 1 and one_call(run[2], k) and run[3] == 1,
          "that key sent again: one POST, the same key, the thumbnail saved (exit %s)" % run[0])
    # A stop that may leave a charge names the batch key, its 24 hours, a kept key's 409, and
    # where to look first, from a minute before the thumbnail was sent (a batch key this run drew).
    run = batch_run([E500, E500], env_extra={"BATCH_KEY": "batch-1"})
    check("batch:500x2-names-batch-key", run[0] == 1 and "run the batch again unchanged with BATCH_KEY=batch-1" in run[1]
          and SAYS["py"]["after-24h"] in run[1] and LOOKUP in run[1] and NO_JOB in run[1] and KEPT in run[1]
          and not stamps(run[1], (keys_of(run[2]) or [None])[0], False, run[-1], True),
          "a stop that may leave a charge says to run the batch again with its BATCH_KEY within 24 hours, "
          "what a kept key answers, and where to look first")

    # thumbnail_keys: the same batch run again draws the same keys; a change draws a new one.
    def keys(prompts, batch_key="batch-1", **env):
        e = {"BATCH_KEY": batch_key}
        e.update(env)
        run = batch_run([], mode="keys", prompts=prompts, env_extra=e)
        return run[1].split() if run[0] == 0 else ["exit %s: %s" % (run[0], run[1][-200:])]

    a = keys(["first prompt", "second prompt", "first prompt"])
    check("batch:keys-drawn", len(a) == 3 and all(is_uuid(k, 5) for k in a) and len(set(a)) == 3 and not posts(),
          "one key per prompt, a uuid5 each, three different keys for a prompt given twice, no call made")
    check("batch:keys-same-batch-key", keys(["first prompt", "second prompt", "first prompt"]) == a,
          "the same batch key and prompts draw the same keys again")
    check("batch:keys-reordered", keys(["second prompt", "first prompt", "first prompt"]) == [a[1], a[0], a[2]],
          "a reordered list keeps each prompt's key")
    b = keys(["first prompt", "second prompt, corrected", "first prompt"])
    check("batch:keys-changed-prompt", b[0] == a[0] and b[2] == a[2] and b[1] not in a,
          "a corrected prompt draws a new key; the others keep theirs")
    check("batch:keys-new-batch-key", not set(keys(["first prompt", "second prompt", "first prompt"], "batch-2")) & set(a),
          "a new batch key draws new keys for every prompt")
    ref = WORK / "face ref (1).png"
    ref.write_bytes(PNG)
    check("batch:keys-shape-model-refs",
          all(not set(keys(["first prompt", "second prompt", "first prompt"], **env)) & set(a)
              for env in ({"T_ASPECT": "9:16"}, {"T_MODEL": "gpt-image-2"}, {"T_REFS": str(ref)})),
          "another shape, model or reference list draws new keys")
    c = keys(["one prompt\nwith a second line", "  first prompt  "])
    check("batch:keys-multiline", len(c) == 2 and c[1] == a[0],
          "a prompt with a line break is one prompt; spaces around a prompt are not part of it")
    # A reference counts by its contents too: a file replaced at the same path draws new keys.
    with_ref = keys(["first prompt", "second prompt"], T_REFS=str(ref))
    again = keys(["first prompt", "second prompt"], T_REFS=str(ref))
    ref.write_bytes(PNG + b"another picture")
    replaced = keys(["first prompt", "second prompt"], T_REFS=str(ref))
    ref.write_bytes(PNG)
    back = keys(["first prompt", "second prompt"], T_REFS=str(ref))
    check("batch:keys-ref-replaced", len(with_ref) == 2 and all(is_uuid(k, 5) for k in with_ref) and again == with_ref
          and back == with_ref and len(replaced) == 2 and not set(replaced) & set(with_ref),
          "the same reference file draws the same keys; the file replaced at the same path draws new ones")
    run = batch_run([], mode="keys", prompts=["first prompt"],
                    env_extra={"BATCH_KEY": "batch-1", "T_REFS": str(WORK / "no-such-ref.png")})
    check("batch:keys-ref-unreadable", run[0] == 1 and "cannot read reference" in run[1]
          and not any(is_uuid(w, 5) for w in run[1].split()),
          "a reference that cannot be read draws no key (exit %s)" % run[0])

    # --- generate_all: the batch's main loop, keys drawn and paired with their prompts ---
    def batch_key_file(run):
        f = run[6] / "batch_key.txt"
        return f.read_text().strip() if f.exists() else None

    pair = ("first prompt", "second prompt")
    run = batch_run([OK, OK], mode="all", prompts=pair, env_extra={"BATCH_KEY": "batch-1"})
    sent = {b.get("prompt"): b.get("idempotencyKey") for b in bodies(run[2]) if isinstance(b, dict)}
    check("batch:all-pairs-keys", run[0] == 0 and len(run[2]) == 2 and run[3] == 2
          and sent == dict(zip(pair, keys(list(pair)))) and batch_key_file(run) == "batch-1"
          and "BATCH_KEY_GIVEN=[1] BATCH_KEY=[batch-1]" in run[1],
          "two prompts, BATCH_KEY given: each POST carries its own prompt's key, and the batch key is saved")
    run = batch_run([OK, OK], mode="all", prompts=pair)
    drawn = batch_key_file(run)
    sent = {b.get("prompt"): b.get("idempotencyKey") for b in bodies(run[2]) if isinstance(b, dict)}
    check("batch:all-new-batch-key", run[0] == 0 and is_uuid(drawn, 4) and "Batch key: %s (saved in" % drawn in run[1]
          and sent == dict(zip(pair, keys(list(pair), drawn))) and "BATCH_KEY_GIVEN=[] " in run[1],
          "no BATCH_KEY: a new one is drawn, printed, saved and used for every key")
    run = batch_run([busy("1"), busy("1")], mode="all", prompts=(PROMPT,), env_extra={"BATCH_KEY": "batch-1"})
    check("batch:all-batch-key-given-429x2", len(run[2]) == 2 and "1_error.json" in run[5]
          and "run the batch again unchanged with BATCH_KEY=batch-1" in run[1] and NOT["batch"]["stop-busy"] not in run[1]
          and KEPT in run[1] and not stamps(run[1], (keys_of(run[2]) or [None])[0], True, run[-1], True),
          "BATCH_KEY from the environment: a 429 twice may stand charged from that earlier run, never 'nothing was "
          "charged', and the look for its job reaches a day further back")
    # A thumbnail whose key the API kept: the same BATCH_KEY sends that key again, which answers
    # 409 for its 24 hours, so the stop says to run that thumbnail alone with a new batch key.
    kept_key = keys([PROMPT])[0]
    run = batch_run([c409()] * 9 + [OK], mode="all", prompts=(PROMPT,), env_extra={"BATCH_KEY": "batch-1"})
    check("batch:all-409-stop-alone", len(run[2]) == 9 and one_call(run[2], kept_key) and run[4] == [15.0] * 8
          and "1_error.json" in run[5] and run[3] == 0
          and all(SAYS["batch"][s].format(k=kept_key) in run[1] for s in CONFLICT_STOP)
          and "a day and a minute before this send, since BATCH_KEY may be an earlier run's" in run[1]
          and not stamps(run[1], kept_key, True, run[-1], True),
          "BATCH_KEY given, its key still 409 after 120 s: the stop looks a day back and says to run that "
          "thumbnail alone with a new batch key")
    run = batch_run([busy("1"), busy("1")], mode="all", prompts=(PROMPT,))
    check("batch:all-no-batch-key-429x2", len(run[2]) == 2 and NOT["batch"]["stop-busy"] in run[1]
          and NOT["batch"]["stop-maybe"] not in run[1],
          "a new batch key: a 429 twice stops with nothing charged")
    run = batch_run([OK], mode="all", prompts=(PROMPT,), env_extra={"T_REFS": str(WORK / "no-such-ref.png")})
    check("batch:all-ref-unreadable", run[0] == 1 and not run[2] and "nothing was sent" in run[1]
          and batch_key_file(run) is None, "a reference that cannot be read: no key, no POST, no batch key saved")
finally:
    server.shutdown()
    subprocess.run(["rm", "-rf", str(WORK)])

failed = results.count(False)
print("  image-resend: %d passed, %d failed" % (len(results) - failed, failed))
sys.exit(1 if failed else 0)
PY
