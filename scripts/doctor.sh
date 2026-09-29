#!/usr/bin/env bash
# The doctor — every guard in this repo, run once, scored on one surface.
#
# WHAT IT IS. Orchestration and presentation, nothing else. Every dimension
# below shells out to a script that already exists and already runs in CI; the
# doctor adds no check of its own and reimplements none of them. If the doctor
# and a guard ever disagree, the guard is right — that is the whole point of it
# owning no logic.
#
# WHY IT EXISTS. `.github/workflows/guard.yml` runs sixteen checks across eight
# jobs, and a contributor's only local equivalent is the hand-maintained list in
# CONTRIBUTING.md — which is deliberately hand-maintained, and therefore
# deliberately incomplete: it has never listed the collisions, targets, toc,
# evals-present, routing-evals or generated checks. So the honest answer to "is
# this repo shippable right now" took eleven commands and a careful reading of
# eleven separate outputs, and the checks nobody remembered to list were the ones
# nobody ran. One command, one table, one verdict.
#
# It is NOT a CI job and must not become one. CI already runs each piece, in its
# own job, so a failure there names its own remedy on the check that failed. A
# doctor job would report one red X for sixteen possible causes, which is exactly
# the "sharing a red X would report the wrong fix" that guard.yml's comments
# refuse for the checks it keeps separate. This surface is for a human or an
# agent standing in the repo asking one question.
#
# ── CORE vs BADGE ────────────────────────────────────────────────────────────
#
# CORE (10). A failure means the repo is blocked: CI is red, or will be. These
# are the checks whose subject is CORRECTNESS — a claim that is false, a link
# that resolves nowhere, a description that truncates, a generated file that no
# longer matches its source.
#
# BADGE (5). A measurement, not a verdict. Their subject is DEBT: a table of
# contents nobody has written yet, a description that is correct and shipping but
# close to the cap, a skill over the 500-line spine and recorded in the baseline.
# None of that is wrong today, so none of it blocks. A badge is EARNED at zero
# debt and otherwise reports the number, because a badge that could be earned by
# picking a friendlier threshold measures the threshold instead of the repo.
#
# The one place badges DO block: if a badge's underlying script EXITS NONZERO,
# that is a real failure of a check CI also runs — a stale TOC entry, a broken
# unit suite — and the doctor exits nonzero for it. Un-earned is not failure;
# errored is. A doctor that exits 0 while CI is red would be worse than no
# doctor, and this is the seam where that could happen quietly.
#
# ── Reading it ───────────────────────────────────────────────────────────────
#
#   PASS   the script exited 0 and printed no warnings
#   warn   the script exited 0 and printed warnings — shipping, not blocking
#   FAIL   the script exited nonzero; the line under it is a paste-ready fix
#   skip   a system dependency is missing (media only); nothing is asserted
#
# Usage: ./scripts/doctor.sh          (exit 0 healthy, 1 if anything blocks)
#        ./scripts/doctor.sh --quiet  (table only, no fix hints)
set -uo pipefail
cd "$(dirname "$0")/.."

QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ── Dimension registry ───────────────────────────────────────────────────────
# Parallel arrays rather than a delimited string: a fix hint contains spaces,
# pipes and quotes, and a delimiter it can contain is a parser waiting to eat a
# hint. `dim <id> <command> <fix hint>`.
CORE_ID=(); CORE_CMD=(); CORE_HINT=()
core() { CORE_ID+=("$1"); CORE_CMD+=("$2"); CORE_HINT+=("$3"); }

core no-mcp        "./scripts/check-no-mcp.sh" \
     "./scripts/check-no-mcp.sh    # point the sentence at its /v1 endpoint, or use the canonical key-gate block verbatim"
core no-gag        "./scripts/check-no-gag.sh" \
     "./scripts/check-no-gag.sh    # rewrite as a preference with its reason; nothing here is confidential"
core no-rates      "./scripts/check-no-rates.sh" \
     "./scripts/check-no-rates.sh    # delete the figure, keep the meter, quote POST /v1/estimates at spend"
core links         "./scripts/check-links.sh" \
     "./scripts/check-links.sh    # fix the path or the file; a link to nothing fails silently at runtime"
core frontmatter   "./scripts/check-skill-frontmatter.sh" \
     "./scripts/check-skill-frontmatter.sh    # trim the description under 1024, or split the body under 500"
core collisions    "./scripts/check-skill-collisions.sh" \
     "./scripts/check-skill-collisions.sh    # git mv the skill directory; its name IS its slash command"
core targets       "./scripts/check-skill-targets.sh" \
     "./scripts/check-skill-targets.sh    # name a skill that is in this checkout, or say plainly that there is none"
core routing-evals "./scripts/check-routing-evals.sh" \
     "./scripts/check-routing-evals.sh    # add fixtures phrased the way a user asks, never quoting the description"
core evals-present "./scripts/check-evals-present.sh" \
     "./scripts/check-evals-present.sh    # write <skill>/evals.md — scenarios from real failures, lowercase name"
core generated     "python3 scripts/build-skill-md.py --check" \
     "python3 scripts/build-skill-md.py    # put the change in sections/*.md.in first; this rebuilds the artifact"

# ── Run the core ─────────────────────────────────────────────────────────────
core_pass=0; core_warn=0; core_fail=0
blocked=0

# The one-line detail: an `OK:` summary when the script printed one (most do,
# as their last line), otherwise the last non-empty line — which on a failure is
# the count summary every guard here prints before exiting.
detail() {
  local f="$1" line
  line="$(grep -h '^OK: ' "$f" 2>/dev/null | tail -1)"
  [ -n "$line" ] || line="$(grep -v '^[[:space:]]*$' "$f" 2>/dev/null | tail -1)"
  printf '%s' "${line#OK: }" | cut -c1-88
}

row() { printf '  %-6s %-16s %s\n' "$1" "$2" "$3"; }

echo
echo "novoads/agent-skills — doctor"
echo "$(git rev-parse --short HEAD 2>/dev/null || echo '?') on $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')  ·  pack v$(cat VERSION 2>/dev/null || echo '?')"
echo

# The guards read TRACKED files only, so a green from an unstaged new file means
# nothing — the gap that shipped a red CI after a clean local run on #51. Said
# once, up front, where it can still change what you do next.
untracked="$(git ls-files --others --exclude-standard -- skills shared scripts 2>/dev/null | wc -l | tr -d ' ')"
if [ "${untracked:-0}" -gt 0 ]; then
  echo "  note  $untracked untracked file(s) under skills/ shared/ scripts/ — these checks read TRACKED"
  echo "        files only, so run 'git add -A' before trusting anything below."
  echo
fi

echo "CORE — a failure here blocks"
for i in "${!CORE_ID[@]}"; do
  id="${CORE_ID[$i]}"
  out="$WORK/core-$id.out"
  eval "${CORE_CMD[$i]}" >"$out" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then
    row FAIL "$id" "$(detail "$out")"
    [ "$QUIET" -eq 1 ] || printf '         fix: %s\n' "${CORE_HINT[$i]}"
    core_fail=$((core_fail + 1)); blocked=1
  elif grep -q '^warn ' "$out" 2>/dev/null; then
    # Show the WARNING, not the `OK:` line. A row flagged warn whose detail reads
    # "every skill ... within budget" makes the reader hunt for what was warned
    # about, which is the whole thing the row was supposed to save them.
    n="$(grep -c '^warn ' "$out")"
    first="$(grep -m1 '^warn ' "$out" | sed 's/^warn  *//')"
    row warn "$id" "$(printf '%s warning(s) — %s' "$n" "$first" | cut -c1-88)"
    core_warn=$((core_warn + 1)); core_pass=$((core_pass + 1))
  else
    row PASS "$id" "$(detail "$out")"
    core_pass=$((core_pass + 1))
  fi
done

# ── Badges ───────────────────────────────────────────────────────────────────
echo
echo "BADGES — measurements, not verdicts"

badges_earned=0
badges_total=0
badge_fail=0

badge_row() { printf '  %-8s %-20s %s\n' "$1" "$2" "$3"; }

# 1. toc coverage. Its script is check-toc.sh, which is not core: its WARNING
#    half (a long file with no TOC at all) is debt, and that is what this badge
#    counts. Its FAILING half (a TOC that exists and no longer matches its file)
#    is a real red and blocks, per the seam described in the header.
badges_total=$((badges_total + 1))
toc_out="$WORK/badge-toc.out"
./scripts/check-toc.sh >"$toc_out" 2>&1
toc_rc=$?
toc_missing="$(grep -c "no '## Contents' table of contents" "$toc_out" 2>/dev/null || echo 0)"
toc_have="$(sed -n 's/^OK: \([0-9]*\) table(s) of contents.*/\1/p' "$toc_out" | tail -1)"
: "${toc_have:=0}"
if [ "$toc_rc" -ne 0 ]; then
  badge_row FAIL "toc coverage" "$(detail "$toc_out")"
  [ "$QUIET" -eq 1 ] || printf '           fix: %s\n' \
    "./scripts/check-toc.sh    # a file that opts into a TOC promises it is complete and resolvable"
  blocked=1; badge_fail=$((badge_fail + 1))
elif [ "${toc_missing:-0}" -eq 0 ]; then
  badge_row EARNED "toc coverage" "every file over 100 lines carries a table of contents"
  badges_earned=$((badges_earned + 1))
else
  badge_row debt "toc coverage" \
    "$toc_have file(s) carry a TOC; $toc_missing over 100 lines do not"
fi

# 2. warn-band headroom. Derived from the frontmatter run above rather than a
#    second invocation — the doctor runs each script once, and re-running one to
#    read a different half of its output is how two dimensions start disagreeing.
badges_total=$((badges_total + 1))
fm_out="$WORK/core-frontmatter.out"
band="$(grep -c 'description [0-9]* chars, [0-9]* from the' "$fm_out" 2>/dev/null || echo 0)"
tightest="$(sed -n 's/.*description [0-9]* chars, \([0-9]*\) from the.*/\1/p' "$fm_out" | sort -n | head -1)"
if [ "${band:-0}" -eq 0 ]; then
  badge_row EARNED "warn-band" "no description within 124 chars of the 1024 cap"
  badges_earned=$((badges_earned + 1))
else
  badge_row debt "warn-band" \
    "$band description(s) in the 900-1024 band; tightest is $tightest from the cap"
fi

# 3. size-baseline headroom. The recorded debt in scripts/skill-size-baseline.txt:
#    files already over the 500-line spine. Forward-only by construction — the
#    baseline may shrink and never grow — so this number only ever falls.
badges_total=$((badges_total + 1))
BASELINE=scripts/skill-size-baseline.txt
over="$(grep -cE '^[0-9]+ ' "$BASELINE" 2>/dev/null || echo 0)"
largest="$(grep -oE '^[0-9]+' "$BASELINE" 2>/dev/null | sort -rn | head -1)"
if [ "${over:-0}" -eq 0 ]; then
  badge_row EARNED "size-baseline" "no SKILL.md over the 500-line spine"
  badges_earned=$((badges_earned + 1))
else
  badge_row debt "size-baseline" \
    "$over SKILL.md over 500 lines and recorded; largest is $largest"
fi

# 4. Unit suites. The six credential-free test scripts guard.yml runs in its
#    brand-context job. All six or the badge is not earned; any nonzero blocks,
#    because CI runs these exact scripts.
badges_total=$((badges_total + 1))
UNIT=(test-brand-context test-rank-ads test-make-picker test-sweep test-placeholder-lint test-parity-i2m)
unit_ok=0; unit_bad=""
for t in "${UNIT[@]}"; do
  if ./scripts/"$t".sh >"$WORK/unit-$t.out" 2>&1; then
    unit_ok=$((unit_ok + 1))
  else
    unit_bad="${unit_bad:+$unit_bad }$t"
  fi
done
if [ -z "$unit_bad" ]; then
  badge_row EARNED "unit suites" "all ${#UNIT[@]} credential-free suites pass"
  badges_earned=$((badges_earned + 1))
else
  badge_row FAIL "unit suites" "$unit_ok of ${#UNIT[@]} pass; failing: $unit_bad"
  [ "$QUIET" -eq 1 ] || printf '           fix: %s\n' \
    "./scripts/${unit_bad%% *}.sh    # read the whole output, these do not stop at the first case"
  blocked=1; badge_fail=$((badge_fail + 1))
fi

# 5. Media suites. The two ffmpeg-backed suites. broll_overlay.py needs the rw/rh
#    reference constants that arrived in ffmpeg 7.1, so the capability is PROVED
#    rather than parsed out of a version string — builds report versions in
#    several shapes and "master" is not a number, which is why guard.yml proves it
#    the same way. No usable ffmpeg is a SKIP, never a failure: a missing system
#    dependency on a laptop asserts nothing about the repo.
badges_total=$((badges_total + 1))
if ! command -v ffmpeg >/dev/null 2>&1 || \
   ! ffmpeg -hide_banner -loglevel error \
        -f lavfi -i color=red:s=64x64:d=0.1 \
        -f lavfi -i color=blue:s=32x32:d=0.1 \
        -filter_complex "[1:v][0:v]scale=w=rw:h=rh:force_original_aspect_ratio=decrease[o]" \
        -map "[o]" -frames:v 1 -f null - >/dev/null 2>&1; then
  badge_row skip "media suites" "no ffmpeg >= 7.1 with rw/rh reference scaling — not run"
else
  media_bad=""
  ./shared/skills/music-mix/scripts/test_music_mix.py >"$WORK/media-mix.out" 2>&1 \
    || python3 shared/skills/music-mix/scripts/test_music_mix.py >"$WORK/media-mix.out" 2>&1 \
    || media_bad="music-mix"
  python3 shared/skills/broll-overlay/scripts/test_broll_overlay.py >"$WORK/media-broll.out" 2>&1 \
    || media_bad="${media_bad:+$media_bad }broll-overlay"
  python3 skills/clone-video-ad/scripts/test_shot_clone.py >"$WORK/media-shot.out" 2>&1 \
    || media_bad="${media_bad:+$media_bad }clone-video-ad-shot-route"
  if [ -z "$media_bad" ]; then
    badge_row EARNED "media suites" "music-mix, broll-overlay and the clone-video-ad shot route all pass"
    badges_earned=$((badges_earned + 1))
  else
    badge_row FAIL "media suites" "failing: $media_bad"
    case "${media_bad%% *}" in
      clone-video-ad-shot-route) media_fix="python3 skills/clone-video-ad/scripts/test_shot_clone.py" ;;
      *) media_fix="python3 shared/skills/${media_bad%% *}/scripts/test_${media_bad%% *}.py" ;;
    esac
    [ "$QUIET" -eq 1 ] || printf '           fix: %s\n' \
      "$media_fix    # measured with ffprobe, read the case"
    blocked=1; badge_fail=$((badge_fail + 1))
  fi
fi

# ── Verdict ──────────────────────────────────────────────────────────────────
echo
printf '  core     %d/%d' "$core_pass" "${#CORE_ID[@]}"
[ "$core_warn" -gt 0 ] && printf '   (%d carrying warnings)' "$core_warn"
printf '\n'
printf '  badges   %d/%d\n' "$badges_earned" "$badges_total"
echo
if [ "$blocked" -ne 0 ]; then
  # Name BOTH counts. A badge whose script errored blocks too, and a verdict
  # reading "0 core dimension(s) failing" beside a red exit code is the kind of
  # contradiction that gets a tool distrusted and then ignored.
  what=""
  [ "$core_fail" -gt 0 ] && what="$core_fail core dimension(s)"
  [ "$badge_fail" -gt 0 ] && what="${what:+$what and }$badge_fail badge script(s)"
  echo "  BLOCKED — $what failing. Fix hints are above, one per line."
  exit 1
fi
echo "  READY — nothing blocks. Un-earned badges are debt, not breakage."
exit 0
