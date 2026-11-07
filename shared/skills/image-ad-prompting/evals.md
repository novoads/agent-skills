# image-ad-prompting evals

The shared template library is not a skill — it has no `SKILL.md` and it never
makes a call. It is the input three skills paste into a paid endpoint, which
makes its failures quieter than a skill's: nothing here throws, and a template
that is wrong renders beautifully and charges normally.

Every scenario below is a real failure observed in a run, not a hypothetical.

The mechanical half runs as:

```bash
python3 shared/skills/image-ad-prompting/scripts/check_library.py            # the checks
python3 shared/skills/image-ad-prompting/scripts/check_library.py --verbose  # + per-template budgets
python3 shared/skills/image-ad-prompting/scripts/check_library.py --selftest # prove each check can fail
```

No network, no key, no credits — it reads markdown and does arithmetic. Run it
before landing any library change. `--selftest` exists because a check that
cannot fail is not a check: each row mutates the real library in memory and
asserts the corresponding check goes red.

The three always-on suffixes are **imported** from
`skills/chatgpt-image-ad/scripts/generate_image.py` rather than restated, so the
budget arithmetic cannot drift from the script that enforces it. The per-model
caps the arithmetic subtracts from are a table in `check_library.py`, and
`./scripts/verify-image-caps.sh` is what reconciles every copy of that table in
the pack against the live spec.

The rest are human checks against a real run. Do them before publishing a
template.

---

## Automated

### L1 — the template fits the cap it will be sent under

**Why:** the cap is measured on the *final* prompt, and the final prompt is not
the one you wrote — the generator appends 1,575 characters of always-on suffix
first. A template that reads as 2,900 characters is a 4,484-character request.
The API answers `400` and the script refuses before the network, so this costs a
round trip rather than credits, but a template nobody can send is not a template.

**The cap it will be sent under is per model.** Deployed spec 2.16.0 (verified
2026-08-08) split what had been a single 4,000 into three, so a body's room is
its model's cap minus 1,575:

| model | cap | body room | reachable from |
|---|---|---|---|
| `gpt-image-2` | 32,000 | 30,425 | `chatgpt-image-ad`, `clone-image-ad` |
| `nano-banana-pro` | 50,000 | 48,425 | `nano-banana-image-ad`, `clone-image-ad` |

**Check, two tiers. Automated.** A body over **30,425** fails: templates are
authored and validated on `gpt-image-2`, so a body no generator can send is a
broken template. Nothing in the library is within 27,000 characters of that line
today. A body over the TIGHTEST model's room is tracked instead, against an exact
baseline. Since the API retired `reve-2.1` (API 2.48.0) the tightest model is
`gpt-image-2` itself, so that tier is empty, and it stays in the checker for the
next route that adds a model with less room.

**The baseline is empty.** Until the retirement it held the three templates over the
`reve-2.1` line (its 4,000 left 2,425, and it was retired in API 2.48.0):
T8 (+170), T11 (+377), T14 (+484). They had not simply been
shortened because **every body in this library is a validated artifact** — the
text is worth what it is worth because someone round-tripped it through a model
and looked at the output. Trimming one to buy a green check, without the credits
to re-render and confirm the trim was cosmetic, degrades the library to satisfy
its own test. So the baseline records the debt instead, and it may only shrink: a
template that starts fitting fails until its row is deleted, and a new template
that overflows fails immediately.

The trim itself is not hard when someone funds it. T11 and T14 both repeat
constraints their own `**Note:**` says the suffixes already enforce — T11 states
"exactly two comments" four separate times, T14 closes with a no-chrome list that
`NO_CHROME_SUFFIX` carries verbatim. That is where the characters are.

### L1b — the pin-block headroom is published, and current

**Why:** pinning every brand mark is mandatory (see L-H2), and the pin block
costs 400 characters. On a tight model, part of the library is too long to carry
it (on the retired `reve-2.1`, 17 of 40 templates were). A run discovers
this *after* writing a full brand fill, and the natural repair — trimming the pin
block — removes the guard that stops the model inventing label copy. Whichever
way it resolves, the run has already been shaped by a number nobody published.

**Check:** the library header states how many templates have room for the
standard pin block **on the tightest model, named**, and the checker recomputes it.
**40 of 40 on `gpt-image-2`** as of 2026-11-07: `gpt-image-2` and `nano-banana-pro`
leave over 30,000 characters pinned, so every template clears them. Until it was
retired (API 2.48.0) the named model was `reve-2.1`, at 23 of 40 as of 2026-08-08.
Editing any template body past the line moves the number and reddens the check.
Automated.

### L2 — one count per countable element

**Why:** `GLYPH_SAFETY_SUFFIX` promises to "render the EXACT count of
conversation elements the prompt specifies". Hand it two counts and the guard
becomes the bug — it enforces one of them, and which one is a draw.

T34 opened at "EXACTLY THREE message bubbles", defined `BUBBLE 1` through
`BUBBLE 4`, and closed at "exactly the four bubbles". Measured 2026-08-06:
restated as four throughout, it rendered four correctly.

**Check:** for every template, the counts stated in prose agree with each other
and with the number of rows the prompt goes on to define (`BUBBLE 1:`,
`MESSAGE 2:`, …). Automated.

**The count alone is not the fix.** T34 now names the structure —
*grey text → blue text → blue link card → grey text* — because a bare number
leaves the model to choose which kind of bubble to drop, and the link card is the
one carrying the product. Prefer a structure to a count wherever the elements are
not interchangeable. That is a **declared divergence from the Kruse source**,
recorded on the entry.

### L3 — art that encodes a number is a documented limit, not a bug

**Why:** `gpt-image-2` draws a bar or a plotted point by eye. Measured
2026-08-06 on T38: the `204` bar overshot its own axis by about **9%**, while
every label came back exact. This reads like a defect and is not one — a retry
redraws it approximately too, so the retry is a second charge for the same
result. Filed as a bug it burns credits; filed as a limit it changes the design.

**Check:** every template in `NUMERIC_ART_TEMPLATES` (T17, T38) says so in its
Model notes, where the consuming skill reads it. Automated.

The recorded answer: if a chart must be numerically true, composite it — generate
the ad without it and lay a real chart over it. Otherwise the picture is
decorative and the claim lives in the copy.

### L4 — spoken audio implies transcribe-verify

**Why:** this library ships still images and has no audio at all, which is
exactly why the rule needs an owner outside the skill that discovered it. A
reference asset pins the **label**; nothing pins the **audio**; they fail
independently. Measured 2026-08-06 across three clones of one source: every glyph
of the on-screen wordmark was perfect in all three, while the brand name was
spoken as "Magnesium", "Magnesium" and "Magneum" — never once as written — and
one clip substituted **L-Thiamine** for L-theanine, a different compound, in a
script that had already passed the dialogue gate. Each render returned
`succeeded` and charged.

So the perfect label an image skill produces is **not** evidence about a sibling
skill's voice track, and a session that has just watched this library pin a
wordmark faithfully is exactly the session likely to assume otherwise.

**Check:** every skill in `SPOKEN_AUDIO_SKILLS` carries a transcribe-verify step.
Automated. Landed for `clone-video-ad` in public #28.

### L5 — the entry format holds

**Why:** the format is what makes an entry usable without reading the whole file:
a missing `Model notes` means a consuming skill cannot route, and an aspect ratio
off the grid is a `400` on a strict request schema.

**Check:** every entry carries When to use / Aspect ratio / Reference image /
Variables / Model notes, and the ratio is on some model's grid. Automated.

### L6 — every stated template count is the real one

**Why:** the library said **"37 templates" in 26 places across 12 files** while
shipping 40. T40–T42 were appended and no counter moved. Every one of those
claims is load-bearing in the way that matters: a session reads "37 validated
templates", finds T1–T39, and stops looking — so the three newest templates were
invisible to the skills that exist to use them. Nothing failed; the library just
quietly got smaller than it was.

**Check:** every `.md` and `.sh` in the repo that claims a library template count
claims the measured one. Automated.

The pattern deliberately matches *library* claims only. **"across 34 templates on
one real product"** is a measured run size — a historical fact that stays 34
forever — and rewriting it to match the library would turn a true sentence into a
false one. `--selftest` asserts both directions.

---

## Human

### L-H1 — visual QA reads the whole frame, not the changed part

**Why:** an edit is a fresh render. The 2026-08-05 T36 edit stripped the
third-party logo it was asked to strip and also moved the thermos and changed a
dashboard stat. Checking only the region you named certifies an image that
drifted everywhere else.

**Check:** human. Read the full output against the reference, not the diff you
intended.

### L-H2 — unpinned means invented

**Why:** across 34 templates on one real product, the label was faithful in all
34 because a reference pinned it, and **every** brand element that was not pinned
drifted or was fabricated: a back-of-pack view invented whole, carrying a
sourcing claim about a real brand that appeared in no prompt; a third-party logo
on a prop; a publication wordmark drifted. The model fills unspecified surfaces
with plausible brand-shaped content.

**Check:** human. Before generating, list every mark that will appear in the
frame — product, publication, prop, competitor — and confirm each is either a
reference asset or named in the standard pin block. After generating, read every
word in the image and confirm it was specified or is printed on a reference.

### L-H3 — the fill still says what the template meant

**Why:** the checks above read the template, not your fill. A faithful fill of
template prose plus a real product runs longer than the AG1 example it was
validated on, and the natural response to a refusal is to cut whichever sentence
looks least load-bearing.

**Check:** human. When a fill overflows, cut from the *description* half of the
pin block or trim your own copy — never the guard clause, and never the
structural instructions the template's Model notes call out as fragile.

---

## Conversation

`L*` checks read the library. `L-H*` checks read a render. These read the
**transcript**: what the user was asked, and in what order. They are human checks,
and they are the only ones here whose failure produces no artifact at all, because a
run that stalls on a question never generates anything to inspect.

E1 is the observed failure. E2 and E3 fence the two paths that lead out of it, so
the fix cannot be undone one branch at a time.

The doctrine they test lives in
[OVERVIEW.md § Presenting choices to the user](OVERVIEW.md#presenting-choices-to-the-user).

### E1: a bare request gets one question, not a syllabus

**Why:** observed 2026-08-07. A first-time user typed "I want to create image ads"
and the reply was a two-engine capability matrix plus a four-item brief (seed
prompt, reference paths, variant count, aspect ratio). Both are real content, and
both were aimed at the wrong reader: the matrix is this file's sibling routing
table, and the four items are what Phase 2 of each generator skill collects.
Someone who has not named a product cannot pick an engine, and cannot pick an
aspect ratio for an ad that does not exist yet. The menu reads as homework and the
run ends before the first image.

**Check:** human. The reply asks the single question from rule A, with its two
numbered options, and stops there.

**Fails if:** the reply names an image model, reproduces a model comparison table,
asks for aspect ratio, variant count or reference paths before a product exists, or
states a credit figure.

### E2: a custom concept arrives with the engine already picked

**Why:** the template path never surfaces the engine, because the entry's `Model
notes:` block decides it. The custom path is the one place no template decides, so
it is the one place the fork is real, and handing it back to the user rebuilds the
matrix of E1 in miniature. The decision is cheap to make and expensive to explain:
the concept itself carries the signal.

**Check:** human. The user supplies a photo and a concept in one message. The reply
names one engine as the recommendation with a one-line reason **drawn from that
concept**, offers the other as option 2 in the shape rule C gives, and quotes a
live `POST /v1/estimates` total before anything renders.

**Fails if:** the reply asks which engine to use, lists engine capabilities side by
side, gives a reason that would fit any concept, or generates before the estimate
is shown.

### E3: accepting the default runs the set, and does not come back to ask

**Why:** the plan is where a menu regrows. A template set has one obvious total and
one obvious order, and its real risk is a *systematic* miss (the product rendered
from the wrong angle, a wordmark drifting across every output) that shows up in the
first few and repeats through the rest. That risk is answered by looking, which the
agent can do at any point, not by a pilot-or-everything question, which the user
cannot answer before seeing anything.

**Check:** human. The user accepts option 1. One total from a live
`POST /v1/estimates`, shown against `balance`, before the first render. The engine
is never named in the user-facing plan. The first three to five outputs are read
back against product identity, brand voice and text legibility. The remaining
templates continue in the same run, with no further decision asked of the user. The
plan covers every fitting template in the library, whichever generator skill renders
each one.

**Fails if:** the agent asks pilot-or-everything, shows a model comparison table,
quotes a price from a markdown file rather than from an estimate response, stops
for approval when its own self-check found nothing wrong, or scopes the run to one
generator skill's subset and parks the rest of the fitting library behind a later
question (observed 2026-08-08: 26 of 40 quoted, the photoreal remainder deferred
behind "if you want them").

### E4: the reference fetch is shown, not proposed

**Why:** observed 2026-08-08. The user named their brand's site and accepted the
full-set path. The agent found the product images on the brand's own CDN, listed
filenames and byte sizes in a table, and stalled on "okay to download these two?". A
read-only fetch of a public asset is free and reversible, so the question guarded
nothing, and it displaced the one question that matters. Showing an image in the chat
requires the bytes on disk, so gating the download also guarantees the user decides
blind: they approve a filename instead of seeing their own product.

**Check:** human. The user has pointed at their brand's site. The product image is
fetched without a consent question, lands under `references/products/`, appears in the
chat, and the next question the user gets is the spend gate, with the image already
visible above it.

**Fails if:** the agent asks permission to download or read a public asset, describes
an image by filename and size instead of showing it, or quotes the price before the
product image has been shown in the chat.

### E5: the tighter option curates, and still takes one go

**Why:** written when option 2 was introduced, to fence it at birth rather than after
a failure. The middle intent (less spend, agent judgment) is real, but it sits one
step from two regressions: a pick-list that asks for per-item approval, which rebuilds
the menu, and a curation that quietly runs the full library anyway, which makes the
option a lie.

**Check:** human. The user picks option 2. The plan names 8 to 12 templates, each with
a half line on why it fits this product, spanning more than one ad family, with at
least one photoreal pick when the product suits it. One total from a live
`POST /v1/estimates` against `balance`, one go for the whole set, and the rendered set
matches the named picks.

**Fails if:** the plan asks any per-pick question, every pick comes from one ad
family, the named set and the rendered set differ, or the total covers more templates
than the plan names.
