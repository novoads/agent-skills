#!/usr/bin/env python3
"""Executable evals for the shared image-ad prompt library. No network, no credits.

Runs the mechanical half of evals.md against
`prompting/prompt-library.md` and the skills that consume it:

  L1  every template + the always-on suffixes fits the prompt cap of the model it
      is sent under, which since spec 2.16.0 is a different number per model
  L1b the library publishes how many templates still have room for the pin block
  L2  no template states two different counts for the same countable element
  L3  a template whose art must be numerically true carries the approximation note
  L4  every skill whose output has spoken audio carries the transcribe-verify step
  L5  every template has the fields the format requires, with a real aspect ratio
  L6  every doc that states a library template count states the real one

The three always-on safety suffixes are IMPORTED from the generator script rather
than restated here, so this file cannot drift from the script it is checking. If
someone edits a suffix, L1's arithmetic moves with it.

L1 carries a dated BASELINE of templates that exceed the TIGHTEST cap among the
models the pack's scripts send a template to. They are grandfathered, not forgiven:
the list may only shrink, and it is exact in both directions. A template that is
not on it must fit that model, and a template on it that starts fitting fails until
it is removed, which is how a ratchet stays a ratchet instead of becoming a
suppression list. Nothing here edits a prompt to buy a green check; every body in
this library is a validated artifact, and trimming one costs a re-validation render
to prove the render did not change.

reve-2.1, retired in API 2.48.0, was the tightest (4,000), and the baseline held
T8, T11 and T14. The tightest is now gpt-image-2, which is also the default: every
template fits it, so the baseline is empty, and the ratchet stays for the next
route that adds a model with less room.

  python3 check_library.py [--verbose]

exit 0 = every check passed · 1 = a check failed · 2 = could not run
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parent / "prompting" / "prompt-library.md"
REPO = HERE.parents[3]  # shared/skills/image-ad-prompting/scripts -> repo root

# The prompt cap PER MODEL, for the models the pack's scripts send a library
# template to. It stopped being one number in spec 2.16.0, which raised
# gpt-image-2 to 32,000 and nano-banana-pro to 50,000. The one model it left on
# the old 4,000, reve-2.1, was retired in API 2.48.0 and left this table. The API
# 400s above a model's own number, before anything is charged, so an overflow
# costs a round trip and not credits.
#
# Verified against deployed spec 2.16.0 on 2026-08-08, re-read at 2.59.0 on
# 2026-11-07. The repo's one reconciler for this table, which also proves the
# three scripts enforce it, is ./scripts/verify-image-caps.sh.
MAX_PROMPT_CHARS = {
    "gpt-image-2": 32000,
    "nano-banana-pro": 50000,
}
# Templates are authored and validated against gpt-image-2 (their Model notes say
# so), and the two generator skills that consume this file are locked to
# gpt-image-2 and nano-banana-pro. So a body over gpt-image-2's room is a template
# nobody can send on the default path, and that is L1's hard failure.
DEFAULT_MODEL = "gpt-image-2"
# The model with the least room. A body that fits the default but not this one is
# not broken, it is narrower than the library implies, so L1 tracks it against an
# exact baseline instead of failing on it. Since reve-2.1 was retired (API 2.48.0)
# the tightest is the default itself, so that tier is empty until a route adds a
# model with less room.
TIGHTEST_MODEL = min(MAX_PROMPT_CHARS, key=MAX_PROMPT_CHARS.get)

# The standard pin block's invariant half — the guard clause from the library
# header. The variable half (the product description) is budgeted separately,
# because that is the part a run writes and therefore the part it can overrun.
PIN_GUARD_CHARS = 346
PIN_DESCRIPTION_BUDGET = 54  # a terse product description; 400 all-in
PIN_BLOCK_CHARS = PIN_GUARD_CHARS + PIN_DESCRIPTION_BUDGET

# The library header publishes how many templates still have room for that block
# ON THE TIGHTEST MODEL, and names that model. Until reve-2.1 was retired it was
# the only place the answer was not "all of them"; the number stays published so
# a model with less room shows up in it. It is one number in prose, and this is
# what stops it going stale.
PIN_ROOM_SENTENCE = re.compile(
    r"\*\*(\d+) of the (\d+) templates\*\* have room for the standard pin block "
    r"on `" + re.escape(TIGHTEST_MODEL) + r"`"
)

# Aspect ratios that exist on at least one model. A template asking for anything
# else is a 400 from a strict request schema.
KNOWN_RATIOS = {"1:1", "4:5", "2:3", "3:2", "3:4", "4:3", "5:4", "9:16", "16:9", "21:9"}

REQUIRED_FIELDS = ("When to use", "Aspect ratio", "Reference image", "Variables", "Model notes")

# ── L1 baseline ───────────────────────────────────────────────────────────────
# Templates over the tightest model's room, each with its prompt-body length; an
# entry is grandfathered only while the body is unchanged. Fixing one means
# trimming the body AND re-rendering it to prove the trim was cosmetic, then
# deleting the row. See evals.md L1.
#
# Empty since reve-2.1 was retired (API 2.48.0). Re-measured 2026-08-08, it held
# the three templates a run on that model was refused on before any brand fill:
# T8 (2,595 characters), T11 (2,802) and T14 (2,909). All three fit gpt-image-2
# and nano-banana-pro with more than 27,000 characters to spare.
BASELINE_OVER_TIGHTEST: dict[str, int] = {}

# ── L3 registry ───────────────────────────────────────────────────────────────
# Templates whose art encodes a number the viewer can read off the picture — a
# bar length, a plotted line, a filled gauge. gpt-image-2 draws these
# approximately (measured ~9% overshoot on T38's own axis, 2026-08-06), so each
# must say so where the consuming skill reads it: in Model notes.
NUMERIC_ART_TEMPLATES = {"T17", "T38"}
NUMERIC_ART_PHRASE = "approximat"

# ── L4 registry ───────────────────────────────────────────────────────────────
# Skills whose deliverable contains speech. Each must carry the transcribe-verify
# step: a reference image pins the LABEL, nothing pins the AUDIO, and the two fail
# independently. Measured 2026-08-06 — three clones of one source spoke a coined
# brand name three different wrong ways while every on-screen glyph was perfect.
SPOKEN_AUDIO_SKILLS = (
    "skills/novoads-api/SKILL.md",
    "skills/clone-video-ad/SKILL.md",
    "skills/pixar-ad/SKILL.md",
    "skills/claymation-ad/SKILL.md",
)
TRANSCRIBE_PATTERN = re.compile(r"transcri(be|pt)", re.I)

COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
# Countable conversation elements, normalised to one class per synonym group so
# "message bubbles" and "bubbles" are not read as two independent counts.
ELEMENT_CLASSES = {
    "bubble": "bubble",
    "bubbles": "bubble",
    "message bubble": "bubble",
    "message bubbles": "bubble",
    "message": "message",
    "messages": "message",
    "comment": "comment",
    "comments": "comment",
    "reply": "reply",
    "replies": "reply",
}
# T34 and T11 mix the two vocabularies for one physical stack of chat rows. Any
# template that defines rows as "BUBBLE n:" is counting bubbles whatever the prose
# calls them, so those synonyms collapse into the defined class.
CHAT_CLASSES = {"bubble", "message", "comment", "reply"}


def load_suffixes() -> dict[str, str]:
    """The three always-on suffixes, read from the generator that appends them."""
    script = REPO / "skills" / "chatgpt-image-ad" / "scripts" / "generate_image.py"
    if not script.exists():
        raise SystemExit(f"error: cannot find the generator script at {script}")
    spec = importlib.util.spec_from_file_location("_gen", script)
    module = importlib.util.module_from_spec(spec)
    sys.argv = [str(script)]  # the module parses args only under __main__
    spec.loader.exec_module(module)
    return {
        "NO_CHROME": module.NO_CHROME_SUFFIX,
        "SAFE_ZONE": module.SAFE_ZONE_SUFFIX,
        "GLYPH_SAFETY": module.GLYPH_SAFETY_SUFFIX,
    }


def parse_templates(text: str) -> list[dict]:
    """Every `## T<n> — title` section with its prompt body and field set."""
    out = []
    for section in re.split(r"\n(?=## T\d+ — )", text):
        head = re.match(r"## (T\d+) — (.*)", section)
        if not head:
            continue
        body = re.search(
            r"\*\*Template prompt\*?\*?:?\*?\*?[^\n]*\n```\n(.*?)\n```", section, re.S
        )
        ratio = re.search(r"\*\*Aspect ratio:\*\*\s*`([^`]+)`", section)
        notes = re.search(r"\*\*Model notes:\*\*(.*?)(?=\n---|\Z)", section, re.S)
        out.append(
            {
                "tag": head.group(1),
                "title": head.group(2).strip(),
                "prompt": body.group(1) if body else None,
                "ratio": ratio.group(1) if ratio else None,
                "notes": notes.group(1) if notes else "",
                "section": section,
            }
        )
    return out


def stated_counts(prompt: str) -> dict[str, set[int]]:
    """Counts the prose asserts, e.g. 'EXACTLY THREE message bubbles' -> bubble:3."""
    found: dict[str, set[int]] = {}
    pattern = re.compile(
        r"\b(?:exactly\s+|exact\s+)?(" + "|".join(COUNT_WORDS) + r"|\d+)[\s-]+"
        r"(message bubbles|message bubble|bubbles|bubble|messages|message|"
        r"comments|comment|replies|reply)\b",
        re.I,
    )
    for raw, noun in pattern.findall(prompt):
        raw = raw.lower()
        n = COUNT_WORDS.get(raw, int(raw) if raw.isdigit() else None)
        if n is None:
            continue
        cls = ELEMENT_CLASSES[noun.lower()]
        found.setdefault(cls, set()).add(n)
    return found


def defined_count(prompt: str) -> tuple[str | None, int]:
    """Highest index of an explicitly defined row, e.g. 'BUBBLE 4:' -> (bubble, 4)."""
    best_cls, best_n = None, 0
    for cls_word, n in re.findall(r"^(BUBBLE|MESSAGE|COMMENT|REPLY)\s+(\d+)\s*[:(]", prompt, re.M):
        cls = ELEMENT_CLASSES[cls_word.lower()]
        if int(n) > best_n:
            best_cls, best_n = cls, int(n)
    return best_cls, best_n


def selftest() -> int:
    """Prove each check fires. A check that cannot fail is not a check.

    Every case is a mutation of the real library text, held in memory — nothing
    is written, so this runs against the shipped file without touching it.
    """
    text = LIBRARY.read_text()
    cases: list[tuple[str, bool]] = []

    # L2 — the T34 regression: reintroduce the upstream "THREE" opener.
    broken = text.replace("EXACTLY FOUR message bubbles", "EXACTLY THREE message bubbles", 1)
    t34 = next(t for t in parse_templates(broken) if t["tag"] == "T34")
    counts = {n for c, ns in stated_counts(t34["prompt"]).items() if c in CHAT_CLASSES for n in ns}
    cls, defined = defined_count(t34["prompt"])
    cases.append(("L2 catches a reintroduced conflicting count", len(counts) > 1 and defined == 4))

    # L2 — the prose stays self-consistent at four while a row goes missing. This
    # exercises the second branch: one stated count, and it is not the number of
    # rows the prompt actually defines. Dropping a bubble is the realistic edit.
    skewed = text.replace("BUBBLE 4 (incoming", "BUBBLE (incoming", 1)
    t34b = next(t for t in parse_templates(skewed) if t["tag"] == "T34")
    c2 = {n for c, ns in stated_counts(t34b["prompt"]).items() if c in CHAT_CLASSES for n in ns}
    _, d2 = defined_count(t34b["prompt"])
    cases.append(("L2 catches a stated count the rows do not match",
                  len(c2) == 1 and d2 not in c2))

    # L2 — the fixed library really is consistent (no false positive).
    ok = True
    for t in parse_templates(text):
        if not t["prompt"]:
            continue
        cc = {n for c, ns in stated_counts(t["prompt"]).items() if c in CHAT_CLASSES for n in ns}
        _, dd = defined_count(t["prompt"])
        if dd and len(cc) > 1:
            ok = False
    cases.append(("L2 is silent on the library as shipped", ok))

    # L1 — the arithmetic matches each generator's own gate, per model. One number
    # per model is the point: a single figure here is the bug 2.16.0 introduced.
    suffix_chars = sum(len(s) for s in load_suffixes().values())
    room = {m: cap - suffix_chars for m, cap in MAX_PROMPT_CHARS.items()}
    cases.append(("L1 arithmetic matches each generator's own gate",
                  room == {"gpt-image-2": 30425,
                           "nano-banana-pro": 48425}))
    cases.append(("L1 caps are one number per model, not one for the set",
                  len(set(MAX_PROMPT_CHARS.values())) == len(MAX_PROMPT_CHARS)))
    bodies = {t["tag"]: len(t["prompt"]) for t in parse_templates(text) if t["prompt"]}
    cases.append(("L1 baseline lengths are the measured lengths",
                  all(bodies.get(k) == v for k, v in BASELINE_OVER_TIGHTEST.items())))
    cases.append(("L1 baseline is exactly the set over the tightest cap",
                  {k for k, v in bodies.items() if v > room[TIGHTEST_MODEL]}
                  == set(BASELINE_OVER_TIGHTEST)))
    # L1 — the hard branch still fires. Nothing in the shipped library is within
    # 27,000 characters of the default model's room any more, so proving it can
    # fail means growing a real template past it: pad T1's body and re-parse.
    victim = next(t for t in parse_templates(text) if t["prompt"])
    padding = room[DEFAULT_MODEL] - len(victim["prompt"]) + 1
    bloated = text.replace(
        victim["prompt"], victim["prompt"] + ("\nx" * padding), 1
    )
    grown = {t["tag"]: len(t["prompt"]) for t in parse_templates(bloated) if t["prompt"]}
    cases.append(("L1 catches a body over the default model's room",
                  grown[victim["tag"]] > room[DEFAULT_MODEL]
                  and all(v <= room[DEFAULT_MODEL] for v in bodies.values())))

    # L1b — the published number moves when the library does, and it is the
    # tightest model's number, which is the only one that is not "all of them".
    stated_pin = PIN_ROOM_SENTENCE.search(text)
    measured = sum(1 for v in bodies.values()
                   if v <= room[TIGHTEST_MODEL] - PIN_BLOCK_CHARS)
    cases.append(("L1b header number is present and correct",
                  bool(stated_pin) and int(stated_pin.group(1)) == measured))
    cases.append(("L1b names the model its number is about",
                  bool(stated_pin) and TIGHTEST_MODEL in stated_pin.group(0)))
    cases.append(("L1b would be all-of-them on the default model",
                  sum(1 for v in bodies.values()
                      if v <= room[DEFAULT_MODEL] - PIN_BLOCK_CHARS) == len(bodies)))

    # L3 — losing the limit from T38's Model notes fails. The whole paragraph has
    # to go, which is what a well-meaning "tighten the docs" edit would actually do.
    t38_live = next(t for t in parse_templates(text) if t["tag"] == "T38")
    stripped = text.replace(t38_live["notes"], "\n- **gpt-image-2:** clean.\n", 1)
    t38 = next(t for t in parse_templates(stripped) if t["tag"] == "T38")
    cases.append(("L3 catches a dropped approximation note",
                  NUMERIC_ART_PHRASE in t38_live["notes"].lower()
                  and NUMERIC_ART_PHRASE not in t38["notes"].lower()))

    # L4 — the registry points at files that exist and every one mentions it.
    cases.append(("L4 registry paths all resolve",
                  all((REPO / p).exists() for p in SPOKEN_AUDIO_SKILLS)))

    # L6 — a stale count is caught, and a run size is not mistaken for one.
    count_claim = re.compile(r"\b(\d+)[- ](?:ready-to-use )?validated"
                             r"(?: full| prompt| parameterizable| ad)?[- ](?:templates?|prompts)\b")
    run_size = re.compile(r"\b(\d+)-template run\b")
    cases.append(("L6 catches a stale library count",
                  count_claim.findall("a 37-template library of 37 validated templates") == ["37"]))
    cases.append(("L6 leaves a measured run size alone",
                  not count_claim.findall("across 34 templates on one real product")
                  and run_size.findall("the 34-template run") == ["34"]))

    width = max(len(n) for n, _ in cases)
    failed = 0
    print("\nselftest — each row proves a check can fail\n")
    for name, passed in cases:
        print(f"  {'PASS' if passed else 'FAIL'}  {name:<{width}}")
        failed += not passed
    print()
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verbose", action="store_true", help="print every template's budget")
    ap.add_argument("--selftest", action="store_true", help="prove each check can fail")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    if not LIBRARY.exists():
        print(f"error: no library at {LIBRARY}", file=sys.stderr)
        return 2

    suffixes = load_suffixes()
    suffix_chars = sum(len(s) for s in suffixes.values())
    templates = parse_templates(LIBRARY.read_text())
    if not templates:
        print("error: parsed zero templates — the library format changed", file=sys.stderr)
        return 2

    failures: list[str] = []
    notes: list[str] = []

    # ── L1 — the template is usable on the model it is sent under ────────────
    # The generator appends the suffixes and refuses above the named model's cap.
    # Since 2.16.0 that cap is three numbers, so "does it fit" is three answers:
    # a body over the DEFAULT model's room is unsendable on the path the library
    # actually routes to and fails; a body over the TIGHTEST model's room is only
    # unsendable there, and is held to an exact baseline instead.
    room = {m: cap - suffix_chars for m, cap in MAX_PROMPT_CHARS.items()}
    room_default = room[DEFAULT_MODEL]
    room_tightest = room[TIGHTEST_MODEL]
    room_pinned = room_tightest - PIN_BLOCK_CHARS
    if args.verbose:
        for m in sorted(MAX_PROMPT_CHARS, key=lambda k: -MAX_PROMPT_CHARS[k]):
            roles = [r for r, who in (("default", DEFAULT_MODEL), ("tightest", TIGHTEST_MODEL))
                     if m == who]
            tag = f" ({', '.join(roles)})" if roles else ""
            print(f"{m:<16} cap {MAX_PROMPT_CHARS[m]:>6} − suffixes {suffix_chars} "
                  f"= {room[m]:>6} for a body{tag}")
        print(f"  …{TIGHTEST_MODEL} minus the standard pin block ({PIN_BLOCK_CHARS}) "
              f"= {room_pinned} pinned\n")
    over_default, over_tightest, over_pinned = set(), set(), set()
    for t in templates:
        if t["prompt"] is None:
            failures.append(f"L1 {t['tag']} — no template prompt block to measure")
            continue
        n = len(t["prompt"])
        if args.verbose:
            state = "OVER EVERY CAP" if n > room_default else (
                f"{TIGHTEST_MODEL} only: over" if n > room_tightest else (
                    f"{TIGHTEST_MODEL} only: no pin room" if n > room_pinned
                    else f"fits pinned everywhere ({room_pinned - n} spare on "
                         f"{TIGHTEST_MODEL})"))
            print(f"  {t['tag']:<4} body {n:>5}  {state}")
        if n > room_pinned:
            over_pinned.add(t["tag"])
        if n > room_default:
            over_default.add(t["tag"])
            failures.append(
                f"L1 {t['tag']} — body is {n} chars; with the always-on suffixes "
                f"({suffix_chars}) that is {n + suffix_chars}, over {DEFAULT_MODEL}'s "
                f"{MAX_PROMPT_CHARS[DEFAULT_MODEL]} cap by "
                f"{n + suffix_chars - MAX_PROMPT_CHARS[DEFAULT_MODEL]}. Every generator "
                f"refuses this template as written, for every brand. Trim it."
            )
            continue
        if n <= room_tightest:
            if t["tag"] in BASELINE_OVER_TIGHTEST:
                failures.append(
                    f"L1 {t['tag']} — now fits {TIGHTEST_MODEL} ({n} chars) but is still in "
                    f"BASELINE_OVER_TIGHTEST. Delete the row; the baseline may only shrink."
                )
            continue
        over_tightest.add(t["tag"])
        if t["tag"] not in BASELINE_OVER_TIGHTEST:
            failures.append(
                f"L1 {t['tag']} — body is {n} chars, which fits {DEFAULT_MODEL} but is "
                f"{n + suffix_chars - MAX_PROMPT_CHARS[TIGHTEST_MODEL]} over "
                f"{TIGHTEST_MODEL}'s {MAX_PROMPT_CHARS[TIGHTEST_MODEL]} cap with the "
                f"suffixes. That is a template a run on {TIGHTEST_MODEL} cannot send. "
                f"Trim it, or baseline it with the reason."
            )
        elif BASELINE_OVER_TIGHTEST[t["tag"]] != n:
            failures.append(
                f"L1 {t['tag']} — body changed from the baselined "
                f"{BASELINE_OVER_TIGHTEST[t['tag']]} to {n} chars while still over "
                f"{TIGHTEST_MODEL}'s cap. Re-measure and update the baseline."
            )
    for tag in BASELINE_OVER_TIGHTEST:
        if tag not in {t["tag"] for t in templates}:
            failures.append(f"L1 {tag} — baselined but no longer in the library; delete the row")
    if over_tightest and not over_default:
        notes.append(
            f"L1: every template fits {DEFAULT_MODEL} and nano-banana-pro. "
            f"{len(over_tightest)} exceed {TIGHTEST_MODEL}'s tighter cap as written "
            f"({', '.join(sorted(over_tightest, key=lambda s: int(s[1:])))}) — "
            f"grandfathered, see evals.md L1"
        )

    # ── L1b — the published pin-block headroom is the measured one ───────────
    # On the tightest model a template can be too long to carry the pin block the
    # library itself makes mandatory (on reve-2.1, retired in API 2.48.0, half the
    # library was). That is a fact a run needs BEFORE it writes a fill, so it is
    # published in the header, and this is what stops the number going stale. The
    # sentence names the model it is about.
    with_room = len(templates) - len(over_pinned)
    stated = PIN_ROOM_SENTENCE.search(LIBRARY.read_text())
    if not stated:
        failures.append(
            f"L1b — the library header no longer states the pin-block headroom for "
            f"{TIGHTEST_MODEL}. Restore the sentence '**{with_room} of the "
            f"{len(templates)} templates** have room for the standard pin block on "
            f"`{TIGHTEST_MODEL}`'."
        )
    elif (int(stated.group(1)), int(stated.group(2))) != (with_room, len(templates)):
        failures.append(
            f"L1b — the header says {stated.group(1)} of {stated.group(2)} templates have room "
            f"for the standard pin block on {TIGHTEST_MODEL}; measured {with_room} of "
            f"{len(templates)}."
        )

    # ── L2 — one count per countable element ─────────────────────────────────
    for t in templates:
        if not t["prompt"]:
            continue
        stated = stated_counts(t["prompt"])
        cls, defined = defined_count(t["prompt"])
        chat_counts = {n for c, ns in stated.items() if c in CHAT_CLASSES for n in ns}
        if cls and defined:
            if len(chat_counts) > 1:
                failures.append(
                    f"L2 {t['tag']} — the prompt states {sorted(chat_counts)} for one stack of "
                    f"chat rows while defining {defined} of them. GLYPH_SAFETY_SUFFIX enforces "
                    f"'the EXACT count the prompt specifies' and is being handed two."
                )
            elif chat_counts and defined not in chat_counts:
                failures.append(
                    f"L2 {t['tag']} — the prompt states {sorted(chat_counts)[0]} chat rows but "
                    f"defines {defined} ({cls.upper()} 1..{defined})."
                )
        for element, counts in stated.items():
            if element in CHAT_CLASSES:
                continue
            if len(counts) > 1:
                failures.append(
                    f"L2 {t['tag']} — two different counts stated for '{element}': {sorted(counts)}"
                )

    # ── L3 — numerically-true art is a documented limit ──────────────────────
    by_tag = {t["tag"]: t for t in templates}
    for tag in sorted(NUMERIC_ART_TEMPLATES, key=lambda s: int(s[1:])):
        t = by_tag.get(tag)
        if not t:
            failures.append(f"L3 {tag} — registered as numeric art but not in the library")
            continue
        if NUMERIC_ART_PHRASE not in t["notes"].lower():
            failures.append(
                f"L3 {tag} — draws a value the viewer reads off the picture, but Model notes "
                f"never says the model draws it approximately. Record the limit where the "
                f"consuming skill reads it."
            )

    # ── L4 — spoken audio implies transcribe-verify ──────────────────────────
    for rel in SPOKEN_AUDIO_SKILLS:
        path = REPO / rel
        if not path.exists():
            failures.append(f"L4 {rel} — registered as a spoken-audio skill but missing")
            continue
        if not TRANSCRIBE_PATTERN.search(path.read_text()):
            failures.append(
                f"L4 {rel} — ships spoken audio with no transcribe-verify step. A reference "
                f"asset pins the label, not the voice."
            )

    # ── L6 — every stated template count is the real one ─────────────────────
    # The library said "37 templates" in 26 places across 12 files while shipping
    # 40: T40-T42 were appended and no counter moved. Every one of those claims is
    # load-bearing — a session reads "37 validated templates" and stops looking.
    # A claim must name the LIBRARY, not a run. "34 templates on one real product"
    # is a measured historical fact and stays 34 forever; "34 validated templates"
    # would be a lie about the file. The patterns below only match the latter.
    counted = len(templates)
    claims = [
        re.compile(r"\b(\d+)[- ](?:ready-to-use )?validated"
                   r"(?: full| prompt| parameterizable| ad)?[- ](?:templates?|prompts)\b"),
        re.compile(r"\b(\d+)-template (?:image-ad )?library\b"),
        re.compile(r"\b(\d+) templates in this file\b"),
    ]
    for path in sorted(REPO.rglob("*")):
        if path.is_dir() or path.suffix not in {".md", ".sh"} or ".git" in path.parts:
            continue
        for line_no, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            for claim in claims:
                for stated in claim.findall(line):
                    if int(stated) != counted:
                        failures.append(
                            f"L6 {path.relative_to(REPO)}:{line_no} — claims {stated} library "
                            f"templates; the library has {counted}"
                        )

    # ── L5 — the entry format holds ──────────────────────────────────────────
    for t in templates:
        for field in REQUIRED_FIELDS:
            if f"**{field}" not in t["section"]:
                failures.append(f"L5 {t['tag']} — missing the '{field}' field")
        if t["ratio"] and t["ratio"] not in KNOWN_RATIOS:
            failures.append(f"L5 {t['tag']} — aspect ratio '{t['ratio']}' is on no model's grid")

    print(f"\nchecked {len(templates)} templates in {LIBRARY.name}")
    for n in notes:
        print(f"  note: {n}")
    if failures:
        print(f"\n{len(failures)} failure(s):\n", file=sys.stderr)
        for f in failures:
            print(f"  · {f}", file=sys.stderr)
        print("", file=sys.stderr)
        return 1
    print("  L1 prompt cap · L1b pin headroom · L2 element counts · L3 documented limits · "
          "L4 transcribe-verify · L5 entry format · L6 stated counts — all pass\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
