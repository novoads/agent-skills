# Video out: `output: "video"` on `POST /v1/voice-changes`

Read with [SKILL.md](../SKILL.md): the gates named here are its gates. Every HTTP
mechanic belongs to [`novoads-api`](../../novoads-api/SKILL.md) and its
[`reference.md`](../../novoads-api/reference.md), where the endpoint's Video out section
is the contract this file applies.

`POST /v1/voice-changes` takes an optional `output`. `"audio"` is the default and everything
above is it, unchanged: a synchronous `200` with the mp3, and the mux is yours. `"video"`
hands back the finished video instead, so Gate 6 becomes the server's work.

```bash
curl -sS -X POST https://api.novoads.ai/v1/voice-changes -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"assetId":"<assetId>","voiceId":"<the one the human picked>","output":"video"}'
# → 202 { jobId, status: "queued", credits, output: "video" }

curl -sS https://api.novoads.ai/v1/generations/<jobId> -A novoads-skill/change-voice \
  -H "Authorization: Bearer $NOVOADS_API_KEY"
# poll until status is "succeeded" (outputUrl is the new mp4, voiceChange.videoId names
# the copy) or "failed" (voiceChange.reasonCode; the message says whether anything was charged)
```

- **It is a job, not an answer.** `202`, then poll `GET /v1/generations/{jobId}` the way
  [`novoads-api`](../../novoads-api/SKILL.md) polls any render. Write down `jobId` and `credits`
  the moment the `202` lands.
- **`succeeded`:** `outputUrl` is the new mp4 and `voiceChange.videoId` names that copy.
  The source is not modified.
- **`failed`:** `voiceChange.reasonCode` says why, and the message says whether anything
  was charged. The charge lands once the job finds speech; a job that fails after that is
  refunded.
- **Already made.** Ask for the same change again and the `202` already says
  `status: "succeeded"` with the finished copy, and nothing is charged. The same rule as
  audio out's free repeat.
- **The price is the same as audio out for the same source.** Quote it at Gate 2 with the
  same `kind: "voice-change"` estimate. Never a typed number.
- **A video source only.** An audio upload with `output: "video"` is a `400`, and nothing
  is charged: there is no picture to put the voice back on. Use audio out.
- **Enabled per workspace.** Where it is off, the call is a `400` whose message says to
  omit `output`. Do that, and run Gate 6 locally: the same result, done by you. Not a retry.
- **What changes and what does not.** The picture is stream-copied, never re-encoded. The
  words, the timing and the accent are the source's; only the voice changes. So Gate 1
  (refuse a file with no speech before the call) and Gate 3 (no accent or pronunciation
  fix) hold exactly as written.

**Choose audio out** when the spans are a creative decision you want to make yourself
(Gate 6's fence), or when the source is audio. **Choose video out** when you want the
finished file and the spans are not in question.

**Gate 7 still runs, on the file you download**: upload it and read it back exactly as
written there, then watch the lip window. There is no assembly step, so no loudness delta
is printed for you: measure both files (`ffmpeg -i <file> -af volumedetect -f null -`) and
report the difference. Listen to any sound effect or music bed that sits under a line:
"only the voice changes" is the contract, and that is the place to check it.
