# Video out: `output: "video"` on `POST /v1/voice-changes`

Read with [SKILL.md](../SKILL.md): the gates named here are its gates. Every HTTP
mechanic belongs to [`novoads-api`](../../novoads-api/SKILL.md) and its
[`reference.md`](../../novoads-api/reference.md), where the endpoint's Video out section
is the contract this file applies.

`POST /v1/voice-changes` takes an optional `output`. `"audio"` is the default and everything
above is it, unchanged: a synchronous `200` with the mp3, and the mux is yours. `"video"`
hands back the finished video instead: the mux becomes the server's; Gate 6's span choices
are not made for you.

```bash
curl -sS -X POST https://api.novoads.ai/v1/voice-changes -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"assetId":"<assetId>","voiceId":"<the one the human picked>","output":"video"}'
# → 202 { jobId, status, credits, output: "video" }
#   status: "queued" (new job) | "running" (the same change, already rendering)
#         | "succeeded" (already made: the finished copy, nothing charged)

curl -sS https://api.novoads.ai/v1/generations/<jobId> -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY"
# on "queued" or "running", poll until "succeeded" (outputUrl is the new mp4,
# voiceChange.videoId names the copy) or "failed" (voiceChange.reasonCode names the cause)
```

- **It is a job, not an answer.** `202`, then poll `GET /v1/generations/{jobId}` the way
  [`novoads-api`](../../novoads-api/SKILL.md) polls any render. Write down `jobId` and `credits`
  the moment the `202` lands.
- **The `202`'s `status` is the job's real lifecycle, so branch on it.** `queued`: a new
  job; poll it. `running`: a retried POST found the same change already rendering; it is
  the same job, not a new one; poll it. `succeeded`: the same change was already made; the
  `202` carries the finished copy and nothing is charged; download it, there is nothing to poll. The
  same rule as audio out's free repeat.
- **`succeeded`:** `outputUrl` is the new mp4 and `voiceChange.videoId` names that copy.
  The source is not modified.
- **`failed`:** `voiceChange.reasonCode` names the cause.
- **When the charge lands differs by output.** Audio out is charged at the request. Video
  out is charged only once the job finds speech in the source: a source with no speech ends
  `failed` with nothing charged, and a job that fails after that is refunded. Gate 1 still runs
  before the call: it is free, and it does not depend on what the job counts as speech.
- **The price is the same as audio out for the same source.** Quote it at Gate 2 with the
  same `kind: "voice-change"` estimate. Never a typed number.
- **A video source only.** An audio upload with `output: "video"` is a `400`, and nothing
  is charged: there is no picture to put the voice back on. Use audio out.
- **Enabled per workspace.** Where it is off, the call is a `400` whose message says to
  omit `output`. Do that, and run Gate 6 locally: the same result, done by you. Not a retry.
- **What changes and what does not.** The words, the timing and the accent are the
  source's; only the voice changes. So Gate 1 (refuse a file with no speech before the
  call) and Gate 3 (no accent or pronunciation fix) hold exactly as written.

**Choose audio out** when the spans are a creative decision you want to make yourself
(Gate 6's fence), or when the source is audio. **Choose video out** when you want the
finished file and the spans are not in question.

**Gate 7 still runs, on the file you download**: upload it and read it back exactly as
written there, then watch the lip window. There is no assembly step, so no loudness delta
is printed for you: measure both files (`ffmpeg -i <file> -af volumedetect -f null -`) and
report the difference. Listen to any sound effect or music bed that sits under a line:
"only the voice changes" is the contract, and that is the place to check it.
