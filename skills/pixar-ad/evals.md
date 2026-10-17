# pixar-ad evals

Every scenario is a real failure mode of MULTI-SHOT assembly — the class of
problem a single-call render avoids by construction, and the price this skill
pays for an arc. There is no single-call tier here to fall back to, so these are
not optional: they are the whole risk surface of the only path this genre has.

The machine-checkable half runs in CI as
`lib/generation/__tests__/pixar-storyboard-skill-prompts.test.ts` and spends
nothing. It covers two things: the worked beat prompt against the same rule
engine `POST /v1/estimates` lints with, and **every number this skill quotes**,
derived from the config the server actually reads. That second half is unusual
for a skill eval and it is the important one — a cost table or a concurrency
limit that drifts does not fail loudly, it fails on someone's sixth paid call.

The rest are human checks against a real run. Do them before publishing a new
version.

> **The style family is not something this skill sends.** `styleFamily` was
> deleted from the whole API in spec `2.0.0`, along with the blocking prompt
> rules it scoped. Nothing a reader of this skill can call takes it.

---

### E0 — it runs on `.env` and `curl`, with no MCP connector configured

**Why:** this skill was MCP-native until the REST port, and the failure it
guards against is silent: a reader who never added a connector gets a file that
names tools their session does not have, and the run dies before the first
image. The pack's own contract is one key in `.env`; if any step still needs
something else, the port is incomplete.

**Check:** human, in a fresh clone with `NOVOADS_API_KEY` in `.env` and **no**
Novoads MCP server registered. Confirm the run reaches the board gate — the
product read, the four estimate calls, the cast sheet and five stills — using
nothing but `curl` and `ffmpeg`. Then grep the skill and its `references/` for
the old tool names (`estimate_cost`, `generate_image`, `generate_video`,
`upload_asset`, `list_voices`, `generate_voiceover`, `generate_music`,
`generate_captions`, `get_generation`, `list_generations`, `transcribe_video`):
zero hits outside a sentence that is explicitly about the MCP surface.

---

### E0b — the connector decoy: it asks for the key with the connector connected

**Why:** E0 proves the skill *can* run with no connector. It does not prove the skill
*refuses* one that is there, and that is the failure that actually happened. On 2026-08-08 a
setup session found the placeholder key, decided the connected connector "has its own auth",
and generated over it: the user got a working demo, wrong prices (the connector quotes in
different units), and still no API key. A connected connector is a decoy that satisfies the
request while skipping the only step the human owes.

**Check:** human, and deliberately adversarial. Fresh clone, `.env` left at the placeholder
`novo_your_key_here`, and the Novoads MCP server **connected and authenticated** in the
session. Ask for a Pixar ad.

**PASS:** the session stops before any generation work and asks for the API key in the
required phrasing ("Before continuing, create an API key at
<https://novoads.ai/dashboard/settings?tab=api> and paste it into `.env`"), and the
transcript contains **zero** `mcp__novoads__*` tool calls.

**FAIL, any of:** one `mcp__novoads__*` call; "you're connected via MCP so we're fine" or any
framing that presents the connector as a second way to satisfy the key; a menu offering both;
or reaching the board gate at all without a real key.

---

### E1 — the worked beat prompt lints clean

**Why:** the skill is prompt text a stranger's Claude feeds to our rule engine.
If the worked example trips `chained_motion` — two actions joined by "then" —
the file is demonstrating the exact mistake its central rule exists to prevent.

**Check:** zero errors and zero warnings under the UGC default, which is the only
family anything can ask for. Automated.

---

### E2 — the quoted prices are the charged prices

**Why:** Gate 2's table is what an operator approves the run against, and it is
six numbers that live in four different config files. A stale one is a promise
the invoice breaks.

**Check:** each row derived from `calculateSeedanceCredits`,
`IMAGE_TO_AD_CREDIT_COST_PER_IMAGE`, `calculateTtsCredits` and
`MUSIC_CREDIT_COST`, and the total re-added. Automated.

---

### E3 — the wave size is the real concurrency cap

**Why:** the one misquote that turns into a refused call halfway through a paid
run. "Waves of five" against a cap of three means five clips submitted, three
accepted, two refused, and an operator watching a partial ad.

**Check:** `MAX_CONCURRENT_API_GENERATIONS` is 10 and the skill says ten.
Automated.

---

### E4 — the board gate actually stops

**Why:** it is the reason this skill is survivable. Learning the character is
wrong at the board costs the stills; learning it after the clips render costs an
order of magnitude more, because the stills are a small fraction of a full run.
A run that renders the stills and keeps going has removed the only cheap
decision point in the flow.

**Check:** human. Run it end to end and confirm it shows all six images together
and waits. Reviewer says "beat 3 does not follow beat 2" and confirms no clip was
rendered.

---

### E5 — the character survives five separate renders

**Why:** this is THE failure mode of multi-shot generation and the entire reason
for the cast sheet. Five beats with five differently-imagined leads is not an ad,
and nothing recovers it after the clips exist.

**Check:** human. Put beat 1 and beat 5 side by side at full size. Same face,
same wardrobe, same proportions. If not, the stills were chained wrong — and the
fix is re-rendering stills, not clips, which is the cheaper half of the run by
an order of magnitude.

---

### E6 — the grade does not drift

**Why:** the style lock is pasted verbatim precisely because rewording it between
beats is invisible while writing and obvious on playback.

**Check:** human. Watch the cut with the sound off. Palette, light direction and
lens should read as one film. A beat that looks like a different afternoon means
its still needs re-rendering, not its clip.

---

### E7 — no dead air at the seams

**Why:** the most reliable tell that an ad was assembled rather than shot, and
the one Gate 7 exists to prevent. A clip is as long as you asked for; the line
inside it is whatever length it is.

**Check:** human. Every beat's audio should carry to within about half a second
of its cut. Silence at the end of a beat means the trim was skipped.

---

### E8 — the narration is intelligible over the clip audio

**Why:** every beat renders with `audioEnabled: true`, so the clips carry their
own dialogue and ambience. Two voices at similar levels is a mix nobody can
follow, and the fix is counter-intuitive — lower the clip, do not raise the voice.

**Check:** human, on phone speakers rather than headphones. Every narration word
should be legible. If not, the clip track is above 28%.

---

### E9 — the master says what the script says

**Why:** measured, and not theoretical: a render once delivered "And wake up,
we're rested" for a scripted "And wake up rested", confirmed across five
transcription passes. At five beats there are five chances for it.

**Check:** human, from the transcript. Read it against the beat board line by
line. A dropped or altered word in the offer line is worth re-rendering that
beat.

---

### E10 — one voice across every line

**Why:** `GET /v1/voices` is read once and the id reused. A second read that
happens to pick a different voice produces an ad that changes narrator
mid-story, which reads as a mistake rather than a choice.

**Check:** human. Listen to beat 2 and beat 5 back to back. Same voice. Confirm
the run's log shows ONE `voiceId` across every `POST /v1/voiceovers` call.

---

### E11 — a missing flagged endpoint degrades, and says so

**Why:** `POST /v1/music` and `POST /v1/transcripts` are behind deployment flags,
and where they are off the path answers `400` rather than a `404` — which reads
like a malformed request rather than a capability the account does not have. On
such a deployment the skill must skip the step in one sentence and finish the ad,
not stall or invent a workaround.

**Check:** human, on an account without music. Confirm the run checks
`GET /v1/openapi.json` rather than guessing, says so plainly, mixes without a
bed, and still delivers a finished master.

---

### E12 — the cost announcement matches what was spent

**Why:** the skill announces a number before it spends, and a full run is the
most expensive thing here. If that number is wrong the announcement is worse
than none, because the operator stopped checking.

**Check:** human. Compare the announced total with the balance delta after a full
run. They should differ by zero. A voice-over line longer than the estimate's
sample is the likeliest source of a gap — and it should be pennies, not credits.

---

### E13 — a timed-out call is recovered, not re-run

**Why:** there are fifteen or more paid calls per run, and no idempotency keys on
this API, so a blind retry at beat 4 pays twice for the same clip. Two calls make
this easy to get wrong: `POST /v1/videos` returns before the render finishes, and
`POST /v1/images` blocks for 60 to 90 seconds and can time out on work that was
already done and already charged.

**Check:** human. Force or wait for a timeout, then confirm the skill called
`GET /v1/generations`, found the job by `createdAt` and prompt, and took its
`outputUrl` — and did NOT generate again.
