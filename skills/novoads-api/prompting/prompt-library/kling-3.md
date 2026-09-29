# Kling 3.0: prompt craft

> **Kling 3.0 is on this API as `kling-v3-pro` since API 2.38.0**, where `GET /v1/models` lists it:
> any integer 3 to 15 seconds, `16:9`, `9:16` or `1:1`, one resolution, `audioEnabled`, and a text
> prompt or a `startImageAssetId` as the first frame. The request body is in
> [reference.md](../../reference.md#kling-v3-pro-api-2380); this file is **prompt craft only**.
> Any route, DTO or field named below belongs to the **upstream fork's API, not this one**:
> do not send them to `api.novoads.ai`. For what you can generate today, use the decision
> tree in [SKILL.md](../../SKILL.md).

**Vendor guide:** [Kling — video model user guide](https://kling.ai/quickstart/klingai-video-3-model-user-guide)

## Checklist (from Kling guide habits)

- [ ] Subject, environment, and **motion path** described clearly.
- [ ] Separate **style** vs **content** when the guide recommends it.
- [ ] If using reference or start frames, say how motion should treat them.

## Template

```text
{{SUBJECT}}. {{ACTION_MOTION}}. Environment: {{ENV}}. Camera: {{CAM}}. Mood: {{MOOD}}. Avoid: {{NEGATIVE}}.
```

## Example

```text
Coffee pours in slow motion into a ceramic mug on a wooden counter, steam rising. Soft window light, shallow depth of field, calm ASMR pacing. No text overlays.
```

## Request body

See the note at the top: call `kling-v3-pro` with the body in reference.md, never with the fork's fields. The upstream fork reached Kling-style output through
b-roll and scene DTOs; neither those DTOs nor those endpoints exist on this API, so there is
nothing to document here until the model lands.
