---
name: tsb-animator
description: Animate R6 combat moves (punches, kicks, slams, victim reactions) in the snappy, exaggerated style of Roblox battlegrounds games like The Strongest Battlegrounds. Use when creating, reviewing or fixing an R6 combat animation, or when an animation feels stiff, robotic, weightless or "AI-made". Builds the animation with the tsb_engine package and checks it with its linter.
---

# TSB-style R6 combat animation

You are building animation **data**, not describing it. Work through `tsb_engine` so every
choice is explicit, testable and reproducible. You cannot see the result: do not claim the
animation "looks great". Say what the linter measured and what still needs the user's eyes.

## Workflow

1. **Intent first (one short paragraph).** Archetype (`light` / `heavy` / `power`), who is hit
   and where, the 3 key poses (coil, contact, follow-through), what should read in silhouette.
   See `references/principles.md` ("Archetypes").
2. **Block in poses.** Use `Animation.set_key` with `easing="linear"`/`"constant"`; torso first,
   then limbs. Declare events: `windup`, `impact`, and `hitstop` if the game freezes frames.
3. **Plant the feet.** Never lower the torso without re-solving the legs:
   `moves.bake_planted_legs(anim, start, end, lateral=..., front_leg=...)`.
4. **Lint.** `python -m tsb_engine lint anim.json` (or `tsb_engine.lint`). Fix every error;
   for each warning either fix it or state why it is intentional.
5. **Refine** using the archetype checklist in `references/principles.md`, re-lint, repeat.
6. **Report honestly**: findings fixed, findings accepted (with reason), and what the linter
   cannot judge (silhouette appeal, weight, style). Ask the user to review in their viewer.

## Rules of engagement

- Tag every number you introduce: `[physical]` follows from the rig, `[heuristic]` a starting
  value to tune, `[style]` aesthetic, `[unverified]` unknown. Never present a heuristic as a
  measurement or as "what TSB does". No public source documents TSB's real numbers.
- Do not invent asset IDs, plugin shortcuts or engine properties. Check
  `references/roblox-facts.md` first; if it is not there, say it is unverified.
- Do not silently "auto-fix". Prefer explicit helpers and report what you changed.
- The linter reports; the user decides. The user's eye is the final judge, not the linter.
- The export to Roblox (`KeyframeSequence`/`.rbxmx`) is **not implemented** yet. Do not claim
  the JSON loads in Roblox Studio. Ask the user which format their pipeline expects.

## Conventions (must match the engine)

Y up, character faces **-Z**, +X is the character's right. Rotations in degrees, `CFrame.Angles`
order. `rx > 0` swings a limb forward; negative torso `ry` winds the right shoulder back.
`Pose.pos` z < 0 pushes a limb forward (used for dislocation). Standing: root y = 3, feet y = 0.
Limb rotations are in the torso frame, not raw Motor6D axes (the real R6 joints have rotated
C0/C1 — verify when writing an exporter).

## Files

- `tsb_engine/` – model, forward kinematics, `moves.py` (pose helpers), `linter.py`, CLI.
- `examples/builders.py` – a worked heavy punch plus two deliberately bad animations.
- `references/principles.md` – craft rules by archetype, with confidence tags.
- `references/roblox-facts.md` – verified facts and known traps.
- `references/vfx-notes.md` – VFX layering notes (reference only; no VFX tooling yet).
- `tests/` – `python -m unittest discover -s tests`.
