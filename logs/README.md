# Novoads API logs

Append-only logs of every generation call the agent makes against the Novoads API.

**The log file is not in this repo, by design.** `novoads-api.jsonl` is created on your first
generation and stays on your machine — `logs/*.jsonl` is gitignored. This file is the schema; the
data is yours. A committed log would ship somebody else's real `creditsCharged` values to every
clone, which is a price table by another name and goes stale the moment a schedule moves. It also
means your prompts, job ids and spend history never travel with a `git push`.

**These logs are observability, never pricing.** They record what was submitted, how long it took, and what it ended up costing — *after the fact*. They are **not** an input to any quote. Every credit number shown to a user comes from a live `POST /v1/estimates` call in the current session (see `skills/novoads-api/SKILL.md`, gate 2). A past `creditsCharged` value is history, not a rate card, and this repo holds no rate tables anywhere.

## Files

- **`novoads-api.jsonl`** — one JSON object per line, one line per generation call. **Local-only; create it on first write** (`mkdir -p logs && touch logs/novoads-api.jsonl`, or just append — the directory is already there because this README is in it).
  - **Videos are asynchronous:** append the line the moment `POST /v1/videos` returns `202` with a `jobId`, then **update that same line** when polling reaches a terminal status (`succeeded`, `failed`, `blocked`, `canceled`).
  - **Images are synchronous:** `POST /v1/images` returns the finished images in the response body, so the line is written once, complete. It still carries a `jobId` — log it, there is just nothing to poll and nothing to update.

## Entry schema

```json
{
  "timestamp": "2026-08-01T19:18:24.611Z",
  "endpoint": "POST /v1/videos",
  "model": "seedance-2.0",
  "jobId": "gen_9f2c1b7a4e8d",
  "productId": "10b24deb-2ce7-47f7-8cf3-624b844658b8",
  "request": {
    "durationSeconds": 12,
    "aspectRatio": "9:16",
    "language": "en",
    "startImageAssetId": true,
    "referenceAssetIdsCount": 0,
    "promptWordCount": 340
  },
  "response": {
    "status": "succeeded",
    "creditsCharged": 3.2,
    "generationTimeSec": 287,
    "error": null
  }
}
```

**Every value in that example is synthetic**, `creditsCharged` included. It shows the shape of a
line, not what anything costs. Real numbers come from `POST /v1/estimates` at call time.

Image lines use the same shape with `"endpoint": "POST /v1/images"`, `numImages` in place of `durationSeconds`, and `generationTimeSec` measured as the request round trip. They carry a `jobId` like video lines do; the difference is that the line is complete when written, not that the field is absent. Add `"qaRetryOf": "<timestamp of the original line>"` on a line that is an image QA regeneration, so the extra credits are attributable.

Field notes:

- `status` is the **terminal** value, not the first one polled. A line whose `response` is still absent is a job that never reached a terminal state in that session.
- `creditsCharged` comes off the API response — never computed locally.
- `startImageAssetId` is logged as a boolean and `referenceAssetIds` as a count. Asset ids belong to the user's uploads, not in a log.
- `request` mirrors the body that was actually sent. Log no field the API does not have — `styleFamily` was deleted from the API in spec `2.0.0` and must not appear on a line written after that, or a later reader will infer a request shape that would 400 today.

## How the agent uses this file

- **Before generating:** nothing. Do not read this file to build an estimate — call `POST /v1/estimates`.
- **On submit:** append the request metadata immediately, before polling starts, so a crashed session still leaves a trace of a charge that was incurred.
- **On terminal status:** update the line with the final status and elapsed time. Carry `creditsCharged` over from the `202` you already logged — `GET /v1/generations/{jobId}` does **not** return it (its schema is `createdAt`, `error`, `jobId`, `kind`, `model`, `outputUrl`, `outputUrlExpiresInSeconds`, `prompt`, `status`). Verified live 2026-08-02. If it is missing from your submit line it is gone; never reconstruct it from a rate.

  **Update the line by `jobId`, not by position, and do not reach for `head -n -1`.** Up to ten
  video generations run at once, so the line you need is often not the last one — and `head -n -1` is a
  GNU extension that fails on stock macOS (`head: illegal line count -- -1`), which is this repo's
  first target. Portable, keyed, and atomic:

  ```bash
  LOG=logs/novoads-api.jsonl
  jq -c --arg id "$JOB_ID" --arg st succeeded --argjson el 171 \
    'if .jobId == $id then .response.status = $st | .response.generationTimeSec = $el else . end' \
    "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  ```

  `jq -c` reads the file as a stream of objects and writes one per line, so the shape survives.
  Writing to `.tmp` and `mv`-ing means an interrupted update cannot truncate the log. Note the
  recipe never touches `creditsCharged` — it is already on the line from the submit, and that is
  the only place it was ever available.
- **Afterwards:** use it to answer "how long did that take", "what did last week cost", and "which config failed" — latency, spend history, and failure patterns.

## What must never be logged

API keys, the `Authorization` header, presigned URLs (`uploadUrl`, `outputUrl` — they expire and they are credentials while they live), and full prompt text. Store a **word count** instead of the prompt.

Logs **are** gitignored (`logs/*.jsonl`), so the exclusion list above is not enforced by review —
nobody will catch a leaked key in a file that never reaches a pull request. It is a hard rule
anyway: the file sits in a working tree that gets shared, pasted, and backed up, and a presigned
URL in it is a live credential until it expires.
