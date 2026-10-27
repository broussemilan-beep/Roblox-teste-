# Craft principles for R6 combat animation

Source: synthesis of a long Gemini conversation (see `docs/analysis/`) plus general animation
practice. Tags: **[physical]** follows from the rig, **[heuristic]** starting value to tune,
**[style]** aesthetic choice, **[unverified]** claimed but not confirmed. None of the numbers
below were measured from TSB; they are defaults for the linter and for first drafts.

## Always

- **Pose-to-pose first.** Block key poses with `constant`/`linear`, check the silhouette,
  then refine. [heuristic]
- **Anticipation that keeps moving.** Never hold the coil perfectly still; keep compressing
  slowly into the snap ("moving hold"). The linter flags fully frozen stretches (TSB007). [heuristic]
- **Snap in few frames.** Heavy/power: <= 2 frames from windup to impact; light: <= 4 at
  60 fps (TSB002). [heuristic]
- **Torso drives, limbs follow.** Hips/torso start, then arm, then head, 1-3 frames apart
  (TSB005). [heuristic]
- **Counter-weight.** When one arm strikes, the other is thrown back; the head keeps the gaze
  on the target until the torso has passed. [heuristic]
- **Break symmetry** in key poses: arms and legs should differ by more than ~10 deg (TSB004). [heuristic]
- **Feet planted.** Dropping the torso needs tilted legs (`plant_legs`); no body part below
  the floor (TSB001). [physical]
- **Fast torso twists slide the feet** on R6 because the hips sit on the torso corners
  (TSB008 info). Hide it with a dash/VFX/camera or accept it. [physical]

## Dislocation / smear

A brief forward offset of the striking limb at impact (`Pose.pos` z < 0). Keep it <= ~1.5 studs
and a few frames, then return (TSB006). Optional, a style choice for heavy/power hits. [style]
Visible detachment > 4 frames reads as a glitch. [heuristic]

## Archetypes (starting values)

| Archetype | Windup -> impact | Torso yaw change | Notes |
|---|---|---|---|
| light | <= 4 frames | >= 20 deg | quick jabs, alternating sides |
| heavy | <= 2 frames | >= 90 deg | big arc, limb pulled far back, long recovery |
| power | <= 2 frames | >= 80 deg | "arm tucked": compress and drop the torso, snap from the hip; less arm travel |

The heavy vs power distinction came from the user's own correction of a charged punch
(a bigger back-swing is not automatically more powerful). [style]

## Reactions and rhythm [heuristic]

- Hit parts react first, the rest lags 2-3 frames (fold at the point of impact).
- Launched bodies: fast rise, slow near the apex (hang time), fast fall; a small bounce on the
  ground sells weight.
- Contrast of speeds beats constant speed: slow/held, then explosive, then held.
- Micro-motion everywhere (breathing, head lag, hands) kills the "robot" look.
- Style reference (user insight): TSB-like movement borrows from stick-figure fight animation:
  silhouette and exaggeration before anatomy. [style]

## Not covered by the linter (needs eyes)

Silhouette clarity, appeal, perceived weight, camera, VFX timing, sound sync.
