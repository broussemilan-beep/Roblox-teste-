# Roblox / Blender facts and known traps

Verified = checked against an official source during this project. Everything else is
unverified: say so.

## Verified

- `ParticleEmitter.Orientation` uses `Enum.ParticleOrientation`: `FacingCamera`,
  `FacingCameraWorldUp`, `VelocityParallel`, `VelocityPerpendicular`.
  (A source in the analysed conversation wrote `FaceCameraWorldUp` — wrong.)
  <https://create.roblox.com/docs/reference/engine/enums/ParticleOrientation.md>
- `ParticleEmitter.ShapeInOut`: `Outward`, `Inward`, `InAndOut`; `ShapeStyle`: `Volume`,
  `Surface`. `Shape` values per a third-party mirror: Box, Sphere, Cylinder, Disc
  (no "Ring").
- Blender 5.0 removed `Action.fcurves`, `Action.groups`, `Action.id_root` (slotted actions;
  use `action.layers[].strips[].channelbag(slot).fcurves`).
  <https://docs.blender.org/api/5.0/change_log.html>
  Any bpy script written for <= 4.3 that touches `action.fcurves` breaks on 5.0.

## Unverified (treat with suspicion)

- Whether `ParticleEmitter:Emit()` called on the **server** shows on clients. Safe default:
  server fires a RemoteEvent, each client calls `Emit` on its own copy.
- `Speed` threshold for `VelocityPerpendicular` particles: sources said 0.01 and 0.001. Use a
  small non-zero value and test.
- `Color3 = 900,900,900` on Decals to force glow; a "Fallout" velocity setting; Moon Animator
  shortcuts; the exact `.rbxmx` KeyframeSequence XML; Blender<->Roblox axis conversion.
- Any `rbxassetid://` ID quoted from the conversation. Open it in the catalogue first.
- Frame-by-frame "measurements" and timecodes of TSB/JJS videos quoted by Gemini: not
  reproducible (the model admitted sampling video at ~1 frame per second).

## Rig facts used by the engine (standard R6, verify on the target rig)

Torso 2x2x1, head 1x1x1, arms/legs 1x2x1. Shoulder pivot is 0.5 studs below the arm top, so a
90 deg forward arm reaches 1.5 studs. Legs hinge at the outer top corner and are 2 studs long.
