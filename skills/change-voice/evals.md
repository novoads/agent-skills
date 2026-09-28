# Evals — change-voice

Written **before** `SKILL.md`, which is the work order this repo uses and which lives in
this sentence because the repo squash-merges and commit order does not survive the merge.

A is an **acceptance run**: every command below was run against production on 2026-08-12
with a real key, and every number is a measurement rather than a design intention. B and C
are assertions about behaviour that costs nothing to check — B is read off the deployed
spec's own words, C is measured on thirteen real audio files.

The one thing A had to prove is the ratchet: **that the founder-approved re-voice of this
pack's own promo ad can be reproduced end to end from the public API plus this skill's
scripts** — no dashboard, no vendor call, no hand-driven ffmpeg. It can.

---

## A — the robotic voice on a UGC ad (the acceptance run)

**Scenario.** A 15-second UGC ad rendered by this pack. The picture is right and the
delivery is right; the synthesized voice is the thing a viewer notices first. There is a
glass-shatter sound effect in the first second and a half, before anyone speaks. The ask is
"same ad, better voice".

**Source.** `7FdK5uP1qDmyemLKE3tkiQ.mp4`, 15.072s, h264 720x1280, aac 32 kHz stereo.
**Target voice.** `DnMVYO7fIYmpGP33wLSZ`, "Aaron - Social & Charismatic" (platform, male,
young, american). **Deployed spec at the time: `2.21.0`.**

### What was run, in order

```bash
# 1. the free local gate -- before any HTTP call at all
python3 scripts/check-speech.py 7FdK5uP1qDmyemLKE3tkiQ.mp4
#    SPEECH: 93% of loud frames are one periodic voice, pitch spread 27 Hz around 124 Hz
#      speech runs 2.19s to 14.86s of 15.07s
#    exit 0

# 2. upload the source
curl -sS -X POST https://api.novoads.ai/v1/uploads -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"contentType":"video/mp4","sizeBytes":4343383}'
#    201, then PUT the bytes with the returned headers verbatim -> http 200

# 3. price it, and show the number before spending
curl -sS -X POST https://api.novoads.ai/v1/estimates -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"kind":"voice-change","assetId":"<assetId>"}'
#    {"credits":1,"balance":146.8,"sufficient":true}

# 4. cast by measurement, then STOP for the human
curl -sS "https://api.novoads.ai/v1/voices?gender=male&age=young&accent=american&language=en" \
  -A novoads-skill/change-voice -H "Authorization: Bearer $NOVOADS_API_KEY" > voices.json
python3 scripts/match-voice.py --source 7FdK5uP1qDmyemLKE3tkiQ.mp4 --voices voices.json \
  --sample 20 --include DnMVYO7fIYmpGP33wLSZ --top 5

# 5. convert (the only charged generation in this run)
curl -sS -X POST https://api.novoads.ai/v1/voice-changes -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"assetId":"<assetId>","voiceId":"DnMVYO7fIYmpGP33wLSZ"}'

# 6. assemble locally: fence the effect, lay the take over the picture, verify
python3 scripts/assemble-voice-change.py --source 7FdK5uP1qDmyemLKE3tkiQ.mp4 \
  --converted take.mp3 --speech-start 2.19 --out acceptance-change-voice.mp4

# 7. verify by transcribing OUR OWN output and reading it against the source's
curl -sS -X POST https://api.novoads.ai/v1/transcripts ... -d '{"assetId":"<output>"}'
```

### What it cost

| Call | Result |
|---|---|
| `POST /estimates` `{kind:"voice-change", assetId}` | `credits: 1`, `sufficient: true`. Free. |
| `POST /estimates` `{kind:"voice-change"}`, no source | also `credits: 1` — a 15s source and a sourceless quote agree, because both land on the one-minute minimum |
| `POST /voice-changes` | `creditsCharged: 1`, `billedMinutes: 1`, `200` in **7.1s** |
| **the same call again, same source and voice** | **`creditsCharged: 0`**, byte-identical `jobId` and `assetId`, a freshly minted `url`, `200` in 1.9s |
| `POST /voice-changes` with a made-up `voiceId` | `404 not_found`, naming the id. **No substitute voice, nothing charged** |
| `POST /transcripts` × 2 (source, then output) | `creditsCharged: 0.1` each |

Balance moved 146.8 → 145.8 across the two conversion calls: **one charge for two calls**,
which is the cache contract holding in the ledger and not just in the response body.

### What came out

| Measurement | Source | Acceptance output | Founder-approved reference (`swap-aaron-v4`, 0–11.95s) |
|---|---|---|---|
| `volumedetect` mean, whole file | −22.6 dB | **−23.3 dB** (delta −0.70, tolerance 1.5) | — |
| mean over 0–11.95s | −23.4 dB | −24.1 dB | −23.6 dB |
| pitch over the speech span | 130.1 Hz, IQR 28.2 | **127.0 Hz, IQR 18.5** | 125.0 Hz, IQR 17.9 |
| duration | 15.072s | 15.072s | — |
| video stream MD5 | `beb3006e…` | **`beb3006e…`** (identical: stream copy) | — |
| transcript | 33 words | **33 words, word for word** | — |
| max per-word start drift | — | **0.021s across all 33 words** | — |

The take arrived from the endpoint at −23.2 dB against a −22.6 dB source: **0.6 dB apart,
already matched**, so the assembly step's own gain correction was a measured no-op
(`gain applied +0.00 dB`). The 14–15 dB gap the pre-endpoint experiments had to fix by hand
is gone from the caller's side of the line.

**Assertions.**

- The local speech check runs **before** the upload, and the run says what it found.
- The number shown to the human comes from `POST /v1/estimates` in the same session.
  Nothing here is quoted from memory, and this skill states no price anywhere.
  **The run priced the conversion only.** The two transcripts it then spent on were not
  estimated first, which is the gap SKILL.md's Gate 2 now closes by announcing the
  read-backs alongside the conversion and quoting each at its own step. A re-run under the
  current text prices three calls, not one; the numbers in the table below are unaffected,
  because what changed is what gets said before the spend, not what the spend costs.
- The catalog is read **filtered** (`gender`, `age`, `accent`, `language`), never whole:
  unfiltered it is thousands of voices, and `gender=male&language=en` alone returned 5,362
  entries and 3.8 MB of JSON on the day of the run.
- Candidates are **auditioned and measured**, and a human picks. No `voiceId` is defaulted.
- The effect in the first 1.5s comes from the **original** track. The output's head measures
  −27.2 dB mean / −4.2 dB peak against the source's −27.2 / −4.2.
- The picture is copied, not re-encoded, and the check for that is the video stream's MD5.
- The finished file is verified by transcribing **our own output** — not by trusting that a
  render preserved words it was never shown.

**Fails if:** any charged call fires before its estimate is shown — the conversion or either
transcript; or the skill picks the voice;
or the whole source is overwritten and the effect comes back as vocal noise; or the output
is delivered without a loudness number and a transcript read against the source.

### What the casting script actually returned

Source measured at 124 Hz median, 27 Hz spread. Twenty catalog voices sampled evenly across
the 875 the filters returned, plus the one the operator named:

```
 #  name                    median  spread   apart
 1  Val - Marketing & Hook    123H     26H   0.1st
 2  Jake – Children Story     126H     47H   0.3st
 3  Jordan - Friendly and     121H     14H   0.4st
 4  Aaron - Social & Chari    118H     15H   0.9st
 5  Timber – Southern US S    118H     32H   0.9st
```

**The voice a human had already approved by ear came back inside one semitone of the
source**, ranked fourth of twenty-one on a measurement that has never heard the ad. That is
the claim this script is allowed to make and the only one: it puts the right voices in front
of a person. It did not pick Aaron, and it is not supposed to — the three above him are
plausible casts of the same register, and choosing between them is listening, not
arithmetic.

For contrast, the casting method this replaced — reading the catalog's written descriptions
— returned a top pick measured at 113 Hz with a 16 Hz spread (a monotone) and a second at
188 Hz, most of an octave above the actor on screen.

### Two defects this run found in the skill's own scripts

Both were found by the verification step failing, which is the argument for having one.

1. **A 3 dB loss in the mux.** The take is mono, the ad's track is stereo, and ffmpeg's
   default mono-to-stereo rematrix drops the level by 1/sqrt(2). The output measured 3.4 dB
   under the source with every segment boundary correct and no gain anywhere in the graph.
   Fixed by stating the matrix (`pan=stereo|c0=c0|c1=c0`) instead of accepting the default.
2. **`ffprobe -of csv` returns fields in the stream's order, not the order you asked for.**
   `stream=channels,sample_rate` came back `sample_rate,channels`, which built
   `aresample=2` — a graph that ran, wrote a file, and measured 12 dB down. Fixed by reading
   JSON and looking the fields up by name.

Both are the same shape of bug: a step that succeeds, writes a plausible file, and is wrong.
Neither would have been caught by anything except measuring the finished object.

---

## B — "the accent is wrong" is a casting problem, not a conversion

**Scenario.** The ad is fine but the operator wants it to sound British, and asks for the
voice to be swapped to a British voice from the catalog.

**Why this is its own eval.** It is the most plausible wrong turn available here, and the
endpoint will not stop it: a British-labelled `voiceId` is a valid id, the call succeeds, and
it charges. What comes back is the source's own pronunciation in a different timbre. The
deployed spec says so in its own description of the endpoint — *"It does not fix
PRONUNCIATION. The model reproduces the source's phonemes, mistakes included"* — and an
accent is very largely which phonemes a speaker reaches for.

**Assertions.**

- The run says, **before** any estimate, that a voice change moves timbre and register and
  does not re-pronounce anything, so a label reading `british` is not an accent change.
- It names the routes that do change the read: re-render the ad with a different actor
  (`clone-video-ad`, or the UGC route in [`novoads-api`](../novoads-api/SKILL.md)), or lay a
  fresh `POST /v1/voiceovers` take over a span with no lips in frame.
- If the operator wants it anyway, it is their call and it fires — after the sentence above,
  not instead of it.
- The same sentence is used for the neighbouring ask, "can it say the brand name properly":
  same answer, same two routes, and the re-render one carries the phonetic spelling
  (`Git-Hub`) into the new render's script.

**Fails if:** the run converts first and explains afterwards; or it describes the result as
"now with a British accent"; or it presents re-rendering as impossible rather than as the
route that actually answers the ask.

---

## C — a music bed is refused locally, before anything is charged

**Scenario.** The operator points the skill at a music bed, or at an ad whose audio is a
track with no voice on it, and asks for a voice change.

**Why this is its own eval.** `POST /v1/voice-changes` gates on *"does this have an audio
track"*, not on *"is anyone talking"*. Its own documentation is explicit that a music bed
sent here "is converted into musical noise, **charged in full**, and that is a charged
success rather than an error". There is no server-side refusal to rely on and no refund to
ask for. **The gate is this skill's, it is free, and it runs first.**

So this eval tests the skill's own check, not a `409`.

**Measured 2026-08-12** on thirteen real files, with `scripts/check-speech.py`. The same
set is listed in that script's own docstring, beside the constants it chose:

| File | voiced fraction | pitch spread | verdict |
|---|---|---|---|
| the 15s UGC ad above | 0.93 | 27 Hz | speech, exit 0 |
| its speech span alone, from 2.2s | 0.96 | 26 Hz | speech |
| its first 2.1s — the effect, before anyone speaks | 0.18 | 35 Hz | **no speech, exit 2** |
| a re-voiced cut of the same ad | 0.91 | 18 Hz | speech |
| three synthesized voice-over takes (en, es) | 0.97–1.00 | 49–56 Hz | speech |
| a 5s UGC voice track | 0.99 | 33 Hz | speech |
| an 85s phone recording of one speaker | 0.98 | 19 Hz | speech |
| an instrumental hip-hop track, full and a 30s cut | 0.77–0.78 | 158–222 Hz | **no speech, exit 2** |
| an instrumental film cue, full and a 30s cut | 0.48–0.49 | 58–212 Hz | **no speech, exit 2** |

Every speech file sits at 0.91 or above, every non-speech file at 0.78 or below, and the
thresholds sit in the gap rather than on either edge.

**Assertions.**

- `check-speech.py` runs before the upload. On exit 2 there is **no** `POST /v1/uploads`, **no**
  `POST /v1/estimates` and **no** `POST /v1/voice-changes`.
- The refusal says why in the user's terms — no talking voice in this file — and says the
  thing that makes it worth reading: the endpoint would have converted it and billed it.
- It offers the two real routes: convert a cut of the audio that HAS the speech in it
  (`--json` reports `speechStart`), or, if the ask was a music bed all along, that is
  `POST /v1/music` and a different skill.
- Exit 3 (the measurements disagree) stops and asks a human to listen. It does not proceed
  on the optimistic reading.
- A source with no audio stream at all is refused by the same gate, at zero cost. The
  endpoint would answer `409` here and charge nothing, so this one is a courtesy rather than
  a save — the skill does not claim otherwise.

**Fails if:** the skill uploads first and checks later; or treats a `200` as proof the source
had speech in it; or reads the local gate's refusal as a reason to retry the call.

---

## Known blind spots in C's gate, stated because a gate that oversells itself is worse than none

- **Singing reads as speech.** One singer is one periodic voice in the same range as a
  talking one. A song sent to the endpoint converts and charges like any other source.
- **Narration over a music bed reads as speech**, which is correct — but the endpoint
  converts the whole track, bed and all. The fence in assembly is what saves the bed, and
  only where the bed plays alone.
- **It measures the whole file.** A source that is thirty seconds of music and then four
  seconds of speech has speech in it. Read `speechStart` from `--json` and cut.
- **A sustained single pitch reads as speech** — a drone, a synth pad, an organ note, a
  stack of steady tones. It is one periodic thing in the human range, which is what the
  first measurement asks for, and its spread is narrow, which is what the second asks for.
  Reproduced 2026-08-12 on four mixed sine tones: `voiced 0.99, spread 0 Hz`, exit 0. The
  tell is in the output rather than the exit code — the narrowest real voice in the table
  above is 18 Hz, and a spread near zero is a machine. No floor is set on the spread
  because thirteen files is not enough to place one honestly.

---

## D — video out: the finished file from the server, and the default untouched

**Evidence.** Contract-backed, not measured: the `output` field is the change-voice plan's
WAVE=2 contract, and no run from this pack has spent on it yet. The first run that does
records its numbers here, the way A did.

### D1 — `output: "video"` on a video source polls to `succeeded`

**Scenario.** The acceptance ad from A, the voice already picked, and the operator wants the
finished video from the server rather than a local mux. The workspace has video out on.

**Assertions.**

- Gates 1 to 4 run as written, and the Gate 2 quote is the same `kind: "voice-change"`
  estimate on the same source. No separate video price is asked for or stated.
- The call is `POST /v1/voice-changes` with `"output":"video"`, and the run expects a `202`
  carrying `jobId`, `status`, `credits` and `output: "video"`, and writes down `jobId` and
  `credits` at once. Any of the job's lifecycle statuses passes, because a re-run of this
  case meets a change already made: `queued` or `running` means poll, `succeeded` means
  download the copy and report nothing charged.
- On `queued` or `running` it polls `GET /v1/generations/{jobId}` until `succeeded`,
  downloads `outputUrl` (an mp4), and names the copy by `voiceChange.videoId`. It does not
  run `assemble-voice-change.py`.
- Gate 7 runs on the downloaded file: read back against the source, the lip window watched,
  and a loudness delta measured and reported, since no assembly step printed one.
- **Re-run.** Asked for the same change again once it has succeeded, the `202` carries
  `status: "succeeded"`, the finished copy and a zero `credits`; the run asserts all three,
  reports that nothing was charged, downloads that copy, and does not poll a new render
  into existence.

**Fails if:** it treats the `202` as a failure, or a `queued` or `running` one as the
finished file; it muxes locally on
top of the server's mux; it quotes a price from anywhere but the estimate; or it reports
success without the Gate 7 read-back.

### D2 — an audio upload with `output: "video"` is refused, nothing charged

**Scenario.** On a workspace with video out on, the source is an `audio/mpeg` upload (a
voice note, no picture) and the operator asks for "the video back".

**Assertions.**

- The run says before the call that video out needs a video source, and offers audio out
  instead. If the call is sent anyway, the `400` is read as a refusal with nothing charged,
  and the balance is not described as changed.
- It does not retry the same body, and it does not invent a picture to satisfy the field.

**Fails if:** it retries on the `400`, reports a charge, or promises a video from an audio
source.

### D3 — omitting `output` changes nothing

**Scenario.** A run exactly like A, with no `output` in the body.

**Assertions.**

- The response is A's: a synchronous `200` with `jobId`, `assetId`, `url`,
  `expiresInSeconds`, `creditsCharged`, `billedMinutes`, `voiceId`, and nothing to poll.
- Gate 6's local assembly runs as written, fences included.
- Where the workspace does not have video out, a run that sent `output` and got the `400`
  saying to omit it lands here: same body without the field, the same result done locally.

**Fails if:** the run polls on a `200`, sends `output: "audio"` as if it were required, or
treats a workspace without video out as unable to change a voice at all.

---

## Notes on evidence strength

- **A is the strongest thing in this file** and the only one that spent money: every number
  is a measurement taken during the run, and the run reproduced an artifact a human had
  already approved by ear, from the public API alone.
- **A's comparison against `swap-aaron-v4` covers 0–11.95s only.** That file's tail came from
  a separate re-render of a mispronounced beat, which is a different operation and out of
  scope for this skill.
- **B is spec-backed, not measured.** Nothing was converted to prove it, deliberately: the
  proof would be a charged call whose result the deployed spec already describes in its own
  words. If a future run does spend one, the measurement belongs here.
- **C's thresholds are calibrated on thirteen files, which is not many.** They are two
  independent measurements that must agree, with a deliberate "ask a human" band between the
  two verdicts, precisely because the calibration set is small.
- **No credit figures appear in `SKILL.md`.** The numbers in this file are a dated record of
  one run. The price of the next one comes from `POST /v1/estimates`.

---

## Open question for the next run — how long a source stays worth converting in one call

The endpoint caps a source at five minutes and this run converted fifteen seconds in 7.1
seconds. Nothing here measures where that curve goes, and the endpoint is synchronous behind
an edge timeout, so a five-minute source is the case worth timing before a skill recommends
it. Until someone runs it, this skill's advice is what it measured: short ads convert in
seconds, and a long source is split rather than assumed.
