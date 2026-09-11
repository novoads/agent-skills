#!/usr/bin/env bash
# First-run setup for the Novoads skill pack.
# Creates .env, MASTER_CONTEXT.md, syncs skills, and verifies API connectivity.
#
# The credential is validated against a live endpoint BEFORE it is written to
# disk. A .env holding a key that has never been probed is the most expensive
# state to debug, because every later failure looks like a different bug.
#
# TWO MODES, because an agent is a first-class user of this script:
#
#   interactive      (a TTY on stdin) prompts for the key, hidden, up to 3 times.
#   non-interactive  (--non-interactive, or stdin is not a TTY) prompts for
#                    NOTHING. It creates the files, syncs the skills, reports
#                    the exact remaining human step, and exits 0.
#
# The second mode is not a convenience. An agent driving this repo cannot type
# into a hidden `read -rs`, so without it the agent either hangs or reimplements
# the script by hand, and the setup that ships is not the setup anyone runs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Host only — every request below appends /v1/…
BASE_URL="${NOVOADS_BASE_URL:-https://api.novoads.ai}"
SIGNUP_URL="https://novoads.ai/en?utm_source=claude-code&utm_medium=github&utm_campaign=skill-pack"
KEYS_URL="https://novoads.ai/dashboard/settings?tab=api"
BILLING_URL="https://novoads.ai/dashboard/settings?tab=billing"
KEY_PLACEHOLDER="novo_your_key_here"

usage() {
  cat <<'EOF'
Usage: ./scripts/setup.sh [--non-interactive]

  --non-interactive, -n   Never prompt. Create .env and MASTER_CONTEXT.md, sync
                          skills, print the remaining step, exit 0. This is also
                          the automatic behavior when stdin is not a terminal.
  --help, -h              This text.

Environment:
  NOVOADS_BASE_URL   Override the API host (default https://api.novoads.ai).
EOF
}

INTERACTIVE=1
# No TTY means nobody can answer a prompt. Detected rather than assumed, so an
# agent, a CI step and a `| tee` all get the same non-blocking behavior.
[[ -t 0 ]] || INTERACTIVE=0

# Set to 1 only if we actually put .env in front of the user. The closing message
# branches on it, so a failed or skipped open must never claim the file is open.
ENV_OPENED=0

# Holds the in-flight temp copy of .env so a signal cannot strand a plaintext
# copy of the key on disk. Declared here so `set -u` is safe before any write.
_SETUP_ENV_TMP=""

while (( $# > 0 )); do
  case "$1" in
    -n|--non-interactive) INTERACTIVE=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

echo "=== Novoads Skill Pack Setup ==="
if [[ "$INTERACTIVE" == "0" ]]; then
  echo "(non-interactive: nothing will prompt)"
fi
echo ""

# `novo_` + 64 lowercase hex. Checked locally first so an obvious typo costs a
# reprompt instead of a round trip. There is exactly one key format now — the
# Basic-auth guessing this replaces existed only because the old API's Basic auth had two formats.
key_shape_ok() {
  [[ "$1" =~ ^novo_[0-9a-f]{64}$ ]]
}

# ONE probe, body and status together, into two globals.
#
# `-w $'\n%{http_code}'` rather than `-o /dev/null -w "%{http_code}"`: the
# latter emits `000` with no trailing newline on a connection failure, so a
# `|| echo "000"` fallback produces `000000`, misses the `000)` arm, and tells
# an offline user their key returned "HTTP 000000". Probing once rather than
# twice matters too — a transient failure followed by a 200 announced
# "Unexpected response from Novoads (HTTP 200)".
#
# GET /v1/models is free, read-only, and still requires a valid key, so a 200
# proves auth while generating nothing and charging nothing.
PROBE_CODE=""
PROBE_BODY=""
probe_key() {
  local response
  response="$(curl -sS -m 20 -w $'\n%{http_code}' \
    -H "Authorization: Bearer $1" "$BASE_URL/v1/models" 2>/dev/null || printf '\n000')"
  PROBE_CODE="${response##*$'\n'}"
  PROBE_BODY="${response%$'\n'*}"
}

# Explain a non-200 probe. Every arm names a DIFFERENT fix, which is the only
# reason to have arms at all.
#
# The two 403s are genuinely different account-level states and the API tells
# them apart in the body: a plan problem carries `"reason":"plan_required"`,
# and the rollout-disabled answer carries no reason at all. Reading only the
# status code blames billing for both.
explain_probe_failure() {
  local code="$1" body="$2"
  case "$code" in
    401)
      echo "✗ Novoads rejected that key (401). It is mistyped, revoked, or from another account."
      echo "  Create a fresh one at $KEYS_URL"
      ;;
    403)
      if [[ "$body" == *"plan_required"* ]]; then
        echo "⚠️  The key is valid (403). This organization has no plan with API access yet."
        echo "  Check your plan at $BILLING_URL"
      else
        echo "⚠️  The key is valid (403), but the REST API is not enabled for this account yet."
        echo "  Nothing to fix on your side. $body"
      fi
      ;;
    429)
      echo "✗ Rate limited (429). Wait a minute and run this again."
      ;;
    000)
      echo "✗ Could not reach $BASE_URL. Check your network."
      ;;
    *)
      echo "✗ Unexpected response from Novoads (HTTP $code)."
      [[ -n "$body" ]] && echo "  $body"
      ;;
  esac
}

# Everything but the last 4 characters becomes `*`.
#
# Two `local` statements, not one. `local s="$1" n=${#s}` expands ${#s} BEFORE
# the builtin runs, so `n` reads the outer scope and comes back 0, and every key
# masks to a bare `****`.
mask_secret() {
  local s="$1"
  local n=${#s}
  if (( n <= 4 )); then
    printf '****'
  else
    printf '%s%s' "$(printf '%*s' $((n - 4)) '' | tr ' ' '*')" "${s: -4}"
  fi
}

write_key_to_env() {
  # Rewrite the single line rather than appending, so re-running setup on a
  # placeholder .env does not leave two NOVOADS_API_KEY rows.
  #
  # mktemp, not a shell redirect into a fixed `.env.tmp`. A redirect creates the
  # file at the caller's umask — 0644 on a default macOS shell — so the live key
  # sat world-readable in a predictably-named file, and .env itself was 0644 for
  # the window between the mv and the chmod, permanently if the process died
  # there or the chmod failed (it was swallowed by `|| true`). mkstemp opens at
  # 0600, and chmod-before-mv means the key is never on disk group-readable.
  local tmp
  tmp="$(mktemp "$ROOT/.env.XXXXXX")" || return 1
  _SETUP_ENV_TMP="$tmp"
  # Cleanup on EXIT, and the SIGNAL arms TERMINATE. A handler that only cleans up
  # and falls through swallows the signal, and a bash trap is global and outlives
  # the function — so a cleanup-only INT arm left Ctrl-C dead for the whole rest
  # of setup. Torn down again once the file is safely in place.
  trap 'rm -f "${_SETUP_ENV_TMP:-}"' EXIT
  trap 'rm -f "${_SETUP_ENV_TMP:-}"; exit 130' INT TERM HUP
  # awk + ENVIRON, not sed "s|...|$1|": the key would be an argv element, visible
  # in `ps` to every local user for the life of the process. ENVIRON also sidesteps
  # replacement-metacharacter mangling (`&`, `|`) on the same line.
  if ! NOVOADS_NEW_KEY="$1" awk '
    /^NOVOADS_API_KEY=/ { print "NOVOADS_API_KEY=" ENVIRON["NOVOADS_NEW_KEY"]; next }
    { print }
  ' "$ROOT/.env" > "$tmp"; then
    rm -f "$tmp"; _SETUP_ENV_TMP=""
    trap - EXIT INT TERM HUP
    return 1
  fi
  chmod 600 "$tmp" 2>/dev/null || true
  if ! mv "$tmp" "$ROOT/.env"; then
    rm -f "$tmp"; _SETUP_ENV_TMP=""
    trap - EXIT INT TERM HUP
    return 1
  fi
  _SETUP_ENV_TMP=""
  trap - EXIT INT TERM HUP
  chmod 600 "$ROOT/.env" 2>/dev/null || true
}

# What the pack makes, said at the end of both successful exit paths. Setup's
# last words used to be about files; the user's next move is an ask, so the
# close names the asks. Plain text rather than a prompt or a menu on purpose:
# the same block has to land in Claude Code, Cursor, and a bare terminal, and
# setup asks a human for exactly one thing — the key, never the product. The
# product question belongs to the first ad request (see AGENTS.md), where the
# answer is used immediately and saved to MASTER_CONTEXT.md.
print_orientation() {
  echo ""
  echo "── What you can ask for ─────────────────────────────────────────────"
  echo "  Open this folder in Claude Code or Cursor and describe the ad:"
  echo "    • \"Make a UGC video ad for my product\" — a presenter speaks your script"
  echo "    • \"Make static image ads from this photo\" — the 40-template library, run in batches"
  echo "    • \"Clone my competitors' ads\" — finds their live ads, ranks them, and"
  echo "      clones the best one for your product. No image needed; it prices it first"
  echo "    • \"Clone this ad for my product\" plus an image — three ready-to-run ads,"
  echo "      and the layout saved as a reusable template"
  echo "    • \"Clone this video ad\" plus a competitor's clip — beat map, adapted script, your product"
  echo "    • \"Make a Pixar-style ad\" or \"a claymation ad\" — storyboard, voice-over, music, captions"
  echo "    • \"Find my competitor's live ads\" — pulls their real creatives from the Meta Ad Library"
  echo "    • \"Publish this to Meta Ads\" — needs Meta credentials, added to .env"
  echo "    • Also: YouTube thumbnails, burned-in captions, b-roll cutaways, a music bed"
  echo "  Drop product photos into references/products/ — the agent asks about"
  echo "  your product the first time you ask for an ad, not before."
  echo "─────────────────────────────────────────────────────────────────────"
}

# Put .env in front of the user instead of describing where it lives.
#
# The advertised flow is an agent running this script with no TTY, so the hidden
# input prompt further down is unreachable on exactly the path most people take,
# and the one human step degrades into a sentence asking someone to go find a
# dotfile in a folder they just cloned. Opening the file is the whole fix.
#
# The opening itself belongs to shared/scripts/open-env.sh, which owns the
# platform rules — GUI editors only, because $EDITOR on this path is vim with no
# terminal attached, which hangs or dies and either way the run stops being
# about the key; skipped over SSH, in CI, with no display server, and under
# NOVOADS_SETUP_NO_OPEN=1. Its contract is three exit codes: 0 the file is
# genuinely on screen, 3 deliberately skipped, 2 called wrong (the only one that
# prints anything, to stderr). This caller always passes exactly one argument, so
# only 0 and 3 are reachable from here, and the helper is silent on both — the
# caller prints its own sentence. So this function decides one thing, which
# sentence the closing message uses, and it can never fail the run.
#
# The helper may be ABSENT. Skills here install standalone, and someone may run
# this script from a partial tree, so a missing shared/ is an ordinary state
# rather than a broken one: skip silently, leave ENV_OPENED at 0, and let the
# closing message fall back to "paste it into .env".
#
# Written with `if` rather than `[[ ... ]] && return`: under `set -e` a bare
# AND-list is the kind of construct that takes an exit status with it, and the
# same footgun already cost this script a run (see the `read -rs` note below).
open_env_file() {
  local helper="$ROOT/shared/scripts/open-env.sh"
  if [[ ! -f "$helper" ]]; then return 0; fi

  # `|| rc=$?` rather than a bare call: the helper exits 3 on every skip, and
  # under `set -e` an unguarded non-zero would end the run right here — the one
  # thing this function promises never to do.
  #
  # Only 0 is treated as "opened". Every other status skips, which is stricter
  # than the documented 0/3 pair on purpose: an unexpected code is a bug in the
  # helper, and the safe reading of one is that the file is NOT on screen. The
  # closing message then says "paste it into .env", which is true either way.
  local rc=0
  bash "$helper" "$ROOT/.env" || rc=$?
  if [[ "$rc" != "0" ]]; then return 0; fi

  ENV_OPENED=1
  # Status only, no instruction. The FINAL MESSAGE block below already tells the
  # user where to paste the key, and saying it twice is precisely what
  # print_agent_close's own header warns produces a menu: an agent shown two
  # phrasings of the same remaining step relays both.
  echo "Opened .env for you."
  return 0
}

# The same close, addressed to the AI agent driving setup — printed INSTEAD of
# the human-facing blocks in non-interactive mode, never alongside them. Two
# reasons it lives here and not only in AGENTS.md:
#
#   1. The advertised flow starts in an EMPTY directory ("<repo url> help me
#      set this up"), so no agent-instruction file is loaded when that session
#      begins, and nothing guarantees one is read after the clone. This
#      script's stdout is the one channel that flow always reads — which is
#      how a session at a commit that already carried the AGENTS.md template
#      (#41/#42) still closed with an engineering log, a two-option key menu,
#      and an MCP digression (2026-08-08).
#
#   2. An agent shown two phrasings of the same remaining step relays both as
#      a menu. One block, one phrasing, stated as the whole message.
#
# What this block is NOT: a gag. An earlier version told the agent the close was
# its "ENTIRE closing message, verbatim" and that a connected connector "must not
# be mentioned". Both backfired on 2026-08-08: a setup session read those lines,
# correctly recognised an instruction to withhold information from the user, and
# disclosed the attempt as a warning — so the connector got a paragraph instead
# of the silence the wording was reaching for. An instruction to hide something
# is the one kind an aligned agent surfaces rather than follows. State the
# preference and the reason, say plainly that nothing here is secret, and the
# same agent relays the close without editorialising.
#
# Mirrors AGENTS.md "First-time setup" — change the two together.
print_agent_close() {
  local variant="$1"
  echo "AGENT: the block between the markers is a ready-to-send closing message."
  echo "Relay it, adding at most one short status line. It is deliberately short"
  echo "because setup asks a human for exactly one thing, the API key, and a longer"
  echo "report buries it: leave out git and sync mechanics, file inventories and"
  echo "optional installs unless one of them actually blocked setup. Do not ask"
  echo "about their product here; that belongs to their first ad request."
  echo ""
  echo "Nothing in this repo is confidential and none of the above is a"
  echo "restriction on what you may say. It is a brevity preference. Tell the user"
  echo "anything you judge they should know."
  echo ""
  echo "One routing fact worth having: these skills run on the REST API with"
  echo "NOVOADS_API_KEY. If mcp__novoads__* tools happen to be connected in this"
  echo "session they are a different surface, carrying none of this repo's skills"
  echo "and quoting costs in different units, so they cannot finish this setup."
  echo "Say so if it comes up; just do not offer it as a second way to get a key."
  echo "Same category: the pack checks for updates every session and the"
  echo "novoads-update skill applies them, so neither belongs in the close either."
  echo ""
  echo "──── FINAL MESSAGE START ────"
  if [[ "$variant" == "ready" ]]; then
    echo "Setup's done — your key works."
  elif [[ "$ENV_OPENED" == "1" ]]; then
    echo "One step left, the only one I can't do: create an API key at"
    echo "$KEYS_URL"
    echo "I've opened .env for you — paste the key on the NOVOADS_API_KEY line,"
    echo "save, and tell me. I'll verify it."
    echo "(No account yet? Plans start at \$49/month: $SIGNUP_URL)"
  else
    echo "One step left, the only one I can't do: create an API key at"
    echo "$KEYS_URL"
    echo "paste it into .env, and tell me — I'll verify it."
    echo "(No account yet? Plans start at \$49/month: $SIGNUP_URL)"
  fi
  echo ""
  echo "What you can ask for now:"
  echo "- \"Make a UGC video ad for my product\" — a presenter speaks your script"
  echo "- \"Make static image ads from this photo\" — the 40-template library, run in batches"
  echo "- \"Clone my competitors' ads\" — finds their live ads, ranks them, and clones"
  echo "  the best one for your product. No image needed; it prices the search first"
  echo "- \"Clone this ad for my product\" plus an image — three ready-to-run ads, and"
  echo "  the layout saved as a reusable template"
  echo "- \"Clone this video ad\" plus a competitor's clip — beat map, adapted script, your product"
  echo "- \"Make a Pixar-style ad\" or \"a claymation ad\" — storyboard, voice-over, music, captions"
  echo "- \"Find my competitor's live ads\" — pulls their real creatives from the Meta Ad Library"
  echo "- \"Publish this to Meta Ads\" — needs Meta credentials; I'll open .env and walk you through"
  echo "- Also: YouTube thumbnails, burned-in captions, b-roll cutaways, a music bed"
  echo ""
  echo "Drop product photos into references/products/ and describe the ad you want."
  echo "Every generation is priced by a live estimate and shown to you before"
  echo "anything is spent."
  echo "──── FINAL MESSAGE END ────"
}

# ── Step 1: .env ──────────────────────────────────────────────────────────────
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  chmod 600 "$ROOT/.env" 2>/dev/null || true
  echo "Created .env from template (chmod 600)."
  needs_key=1
elif grep -q "$KEY_PLACEHOLDER" "$ROOT/.env"; then
  echo ".env exists but still has the placeholder key."
  needs_key=1
else
  echo ".env already exists with a key. Skipping prompt."
  needs_key=0
fi

if [[ "$needs_key" == "1" && "$INTERACTIVE" == "1" ]]; then
  echo ""
  echo "Need a Novoads account? Plans start at \$49/month:"
  echo "  $SIGNUP_URL"
  echo ""
  echo "Then create an API key at:"
  echo "  $KEYS_URL"
  echo ""

  attempts=0
  while (( attempts < 3 )); do
    attempts=$((attempts + 1))
    # -s so the key never echoes or lands in shell scrollback.
    printf "Paste your Novoads API key (input hidden, Enter to skip): "
    # Tested, not assumed: a bare `read` returns non-zero at EOF, and under
    # `set -e` that kills the run right here — Ctrl-D at this prompt would skip
    # MASTER_CONTEXT.md and the skill sync and report nothing about either.
    if ! read -rs input; then
      printf "\n"
      echo "No input. Add your key to .env before using the skill."
      break
    fi
    printf "\n"

    if [[ -z "$input" ]]; then
      echo "Skipped. Add your key to .env before using the skill."
      break
    fi

    if ! key_shape_ok "$input"; then
      echo "✗ That does not look like a Novoads key. Expected novo_ followed by 64 hex characters."
      echo "  Attempts left: $((3 - attempts))"
      unset input
      continue
    fi

    echo "Validating against $BASE_URL/v1/models ..."
    probe_key "$input"

    if [[ "$PROBE_CODE" == "200" ]]; then
      # Checked, because write_key_to_env can now `return 1` and this script runs
      # under `set -e`: an unguarded call would abort the whole run right here,
      # AFTER the key validated 200, with no message, no MASTER_CONTEXT.md, no
      # skill sync and no closing message. Say what happened and carry on.
      if write_key_to_env "$input"; then
        echo "✓ Valid. Saved to .env as $(mask_secret "$input")"
      else
        echo "✓ Valid — but $ROOT/.env could not be written."
        echo "  Add this line to it by hand: NOVOADS_API_KEY=<the key you just pasted>"
      fi
      unset input
      break
    fi

    # A 403 is a real key against an account that cannot call the API yet.
    # Saving it is correct: re-prompting would only collect the same key again,
    # and the fix is on the billing page, not in this file. A 401 is never
    # saved — that key is wrong and .env would just memorialize the typo.
    if [[ "$PROBE_CODE" == "403" ]]; then
      if write_key_to_env "$input"; then
        explain_probe_failure "$PROBE_CODE" "$PROBE_BODY"
        echo "  Saved to .env anyway as $(mask_secret "$input") — the key is real, the plan is the blocker."
      else
        explain_probe_failure "$PROBE_CODE" "$PROBE_BODY"
        echo "  The key is real, but $ROOT/.env could not be written."
        echo "  Add this line to it by hand: NOVOADS_API_KEY=<the key you just pasted>"
      fi
      echo "  Re-run ./scripts/check-novoads-env.sh once the plan is active."
      unset input
      break
    fi

    explain_probe_failure "$PROBE_CODE" "$PROBE_BODY"
    echo "  Attempts left: $((3 - attempts))"
    unset input
  done
fi

echo ""

# ── Step 2: MASTER_CONTEXT.md ────────────────────────────────────────────────
if [[ ! -f "$ROOT/MASTER_CONTEXT.md" ]]; then
  cp "$ROOT/MASTER_CONTEXT.template.md" "$ROOT/MASTER_CONTEXT.md"
  echo "Created MASTER_CONTEXT.md from template."
  echo "The agent asks for your default product the first time you request an ad,"
  echo "and saves the answer here so it never asks again."
else
  echo "MASTER_CONTEXT.md already exists. Skipping."
fi

echo ""

# ── Step 3: Sync skills to .claude/, .cursor/ and .agents/ ───────────────────
# The third path is the Codex one and is a symlink rather than a copy; the
# wrapper explains why. Setup is where it gets created, because a Codex user
# never triggers the SessionStart hook that keeps the other two warm.
bash "$ROOT/scripts/sync-skill.sh"

echo ""

# ── Step 3b: Replay any migrations this clone has not run ────────────────────
# A clone made months ago is not a fresh clone plus some commits: a renamed
# skill leaves its old copy registered, a renamed config key still parses and
# means nothing, and generated output orphaned by a move is never collected.
# `git pull` fixes none of that and reports success. The runner replays the
# one-time repairs above `.update-state/last-setup-version`; a fresh install
# adopts the current VERSION and replays nothing.
#
# It runs HERE, before the connectivity check, because both branches below can
# exit 0 — a clone with no key yet still needs its tree repaired. The `|| echo`
# is load-bearing under `set -e`: the runner is non-fatal by contract, and a
# repair that did not happen must not take the setup with it.
bash "$ROOT/migrations/run.sh" || echo "Setup continued; see the migration warnings above."

echo ""

# ── Step 4: Verify API connectivity ──────────────────────────────────────────
# In non-interactive mode this step REPORTS and never fails the run. Asserting
# connectivity is check-novoads-env.sh's job and it exits non-zero for exactly
# that; this script's contract here is "prepare the workspace and say what is
# left", and a missing key on a fresh clone is the expected state, not an error.
if grep -q "$KEY_PLACEHOLDER" "$ROOT/.env" 2>/dev/null; then
  echo "No key set in .env yet. Skipping the connectivity check."
  echo ""
  if [[ "$INTERACTIVE" == "0" ]]; then
    # Only on this path. Interactive runs already asked for the key with hidden
    # input a few lines up, and opening an editor on top of an answered prompt
    # is a second place to type the same secret.
    open_env_file
    print_agent_close needs_key
    exit 0
  fi
  echo "── What is left for a human ─────────────────────────────────────────"
  echo "  1. Create a key at $KEYS_URL"
  echo "     No Novoads account yet? Plans start at \$49/month: $SIGNUP_URL"
  echo "  2. Open $ROOT/.env and replace $KEY_PLACEHOLDER on the"
  echo "     NOVOADS_API_KEY= line with that key. Keys are novo_ plus 64 hex characters."
  echo "  3. Run ./scripts/check-novoads-env.sh to confirm it works."
  echo "─────────────────────────────────────────────────────────────────────"
  echo ""
  echo "Everything else is done: .env, MASTER_CONTEXT.md, and the synced skills."
  print_orientation
  exit 0
fi

# Do not let `set -e` swallow the closing message. A user who ends on a bare
# error and no next step is a user who has to guess whether anything worked.
if bash "$ROOT/scripts/check-novoads-env.sh"; then
  echo ""
  if [[ "$INTERACTIVE" == "0" ]]; then
    print_agent_close ready
    exit 0
  fi
  echo "Setup complete."
  print_orientation
  exit 0
fi

echo ""
echo "Setup wrote your files, but the key in .env cannot call the API yet."
echo "The check above says whether that is the key (401 — replace it) or the"
echo "account (403 — activate a plan). Re-run ./scripts/check-novoads-env.sh after fixing."
# Non-interactive callers get the diagnosis on stdout and a 0, because in that
# mode this script reports state rather than asserting it. An `if` rather than a
# trailing `&&`: under `set -e` a final AND-list whose test fails takes the exit
# status with it, which is how a "succeeded" run ends on 1.
if [[ "$INTERACTIVE" == "1" ]]; then
  exit 1
fi
echo ""
echo "AGENT: report the diagnosis above and its one fix in a sentence or two, then"
echo "stop. No orientation, no alternatives — nothing works until the key does."
exit 0
