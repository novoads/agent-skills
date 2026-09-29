# clone-video-ad — what this API changes about cloning

History, moved out of `SKILL.md` on 2026-09-29 because none of it is needed mid-run: the rules a
clone needs while it runs are in `SKILL.md`'s constraints table. Step numbers below are
`SKILL.md`'s. The table has since been kept current with the API: the old "no video-to-video path" claim
no longer holds (Seedance takes mp4 and mp3 references in their own fields from API 2.35.0,
and `omni-flash` takes a reference video), though a clone still never feeds the original in.

## What this API changes about cloning

The analysis half is nearly untouched: frames and the beat structure are local work on the
user's file, and the transcript is one cheap API call instead of a local install (step 2).
The generation half has three differences worth knowing before you promise anything. All three were established with free `400` probes that reject
before any charge, and re-verified field-for-field against the deployed spec `2.12.0`
(2026-08-06):

| The old shape | Here |
|---|---|
| Chain clip 1 → clip 2 → clip 3 as reference **videos**, so each clip inherits the last | **Chaining a clip's output in is not how a series holds.** `referenceVideos` is `400 (root): Unrecognized key`; since API 2.35.0 the Seedance variants take mp4 references in `referenceVideoAssetIds` (see novoads-api), but this skill does not rely on them. What holds a series together is passing the **same image `assetId`s to every clip** plus repeating the actor tag verbatim — see step 5 |
| `audioEnabled: true` to switch speech on, `false` for a silent clone | **`audioEnabled` exists here now, on the two Seedance variants only** (added in spec `2.2.0`; `400 Unrecognized key` on `omni-flash`, `veo-3.1` and `sora-2`). It defaults to `true`, so a clone with dialogue needs nothing. Send `false` only for a deliberately silent clone — and **still write the silence into the prose**, because the flag mutes the render while the prose is what stops the model staging a talking shot. It does not change the price, and `POST /v1/estimates` refuses the field |
| Upload the source audio as `referenceAudios` to clone the voice | **There is no voice cloning on this API** (`referenceAudios` is `400 Unrecognized key`; the Seedance `referenceAudioAssetIds` field from API 2.35.0 takes an mp3 reference, and nothing in this pack has verified it matches a voice). Describe the voice in the prompt — age, accent, pace, energy — and accept that it is a different person's voice. Do not offer the user a voice match you cannot deliver |

Also gone, in the same probe: `endFrame`, `projectId` (this
API has products, not projects), `duration` (it is `durationSeconds`) and `referenceImages`
(it is `referenceAssetIds`).

**`resolution` was on that list and has come back.** It is a real field on `seedance-2.0` — `480p`, `720p`, `1080p`, `4k`, default `720p` (verified live against spec 2.12.0, 2026-08-06). A clone should normally match the source's tier, which for a social ad is `720p`; going above it is a **spend** decision (`1080p` ≈2.5x the base, `4k` ≈5x) that gets priced with `POST /v1/estimates` and approved like any other. **`480p` costs ≈half of `720p`** since the 2026-08-07 family reprice — measured live 2026-08-12, exactly half on both `seedance-2.0` and `seedance-2.5` — so it is a real draft tier, worth offering when a clone is a rehearsal rather than the deliverable. (The older line here, that it cost the same and bought nothing, described the pre-reprice deployment.) **A clone rendered as a series pays the multiplier on every clip** — check the tier before you fan out. On `seedance-2.0-mini` send it only where `GET /v1/models` lists more than one tier (API 2.34.0 on; before it Mini rendered 720p only and the key was a `400`).

**And one the old shape got wrong in the other direction:** aspect ratio is not
`9:16`-or-`16:9`. Seedance takes `16:9` `9:16` `1:1` `4:3` `3:4` `21:9` — probed live, `1:1`
and `4:3` both pass validation — so a square or landscape source clones at its own ratio
instead of being letterboxed into a vertical frame.
