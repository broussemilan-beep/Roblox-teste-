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
6. **Show it.** Add the animation to a scene in `examples/scenes.py`, run
   `python tools/build_viewer.py`, render frames with `node tools/render_frames.js` and a
   contact sheet with `tools/contact_sheet.py`, and *look at the images* before judging. Publish
   `viewer/output/<scene>.artifact.html` so the user can scrub it.
7. **Report honestly**: findings fixed, findings accepted (with reason), and what the linter
   cannot judge (silhouette appeal, weight, style). Ask the user to review in their viewer.

## Ultimates and cinematics

For long set-pieces (ultimates, finishers) author a `Scene` with a `Cinematic` (see
`examples/ultimate.py`, ~13 s, four acts). The loop is: author an act, `python tools/build_viewer.py <scene>`,
render the `film` camera on key frames, build a contact sheet, **look**, fix, repeat.

- `tsb_engine/authoring.py`: `K(anim, frame, easing, T=, H=, RA=, LA=, RL=, LL=, R=)` keys several parts at
  once; `tremble`, `attach` (victim's part sits on the holder's hand), `lying_root_rot`,
  `keep_above_ground`. Sprint: `footwork.gait_steps` + `bake_footwork` — bake legs **after** every torso/root key,
  or the feet will not match the body.
- `tsb_engine/cinematic.py`: camera shots (`dolly`, `orbit`, `tracking`; later shots override earlier ones), shake,
  props, debris/`shatter`, rings, domes, particles (`emit`, `converge` for charge-ups), trails, ground
  `strip`, cracks, and screen tracks (bright, vignette, bars, speed lines, tint, flashes).
- Camera traps seen while building the demo: a camera inside rubble/dust fills the frame with one polygon
  (raise it or pull back); additive glows wash out on a bright floor (cap alpha); particle clusters on the
  character hide the pose (keep the silhouette readable).
- **Work like an animator, with your eyes.** For every shot: (1) render it *without fx* (strip `cine.fx` and debris)
  and judge pose, silhouette and camera first; (2) only then add fx and re-render. A pose that does not read from its
  camera (arms pointing at the lens, a body hidden by its own arm) is fixed by the pose or the camera, never by fx.
- VFX vocabulary (`Cinematic`): `burst` hit star, `emit(shape=spark|flame|smoke|shard)`, `slash` crescent smear,
  `bolt` lightning, `glow` (+flare), `ring`, `strip`, `cracks` (dark fissure + molten core), `punch_in` fov kick,
  `shake`. In the viewer fx are split around the characters (ground decals and far fx behind, near fx in front),
  so auras wrap the body instead of hiding it. Additive glows need a darker ground: this demo uses a dusk palette.
- The viewer only imitates Roblox primitives (parts, ParticleEmitter, Beam, Trail, PointLight,
  ColorCorrection). No custom shaders, no global hitstop, no impact frames: do not rely on them.

### Matching a reference: the "basic models, high-level animation" lesson

When the user shows a reference clip, study it first (`docs/research/reference-analysis.md` is the worked example:
30 fps clock, shot lengths, per-hit layers, impact/black frames) and reproduce the **craft**, not the choreography.
Plain Roblox blocks are enough; the level comes from pace, camera, graphic fx and secondary motion.

- `examples/short.py` (`duel_short`, 11 s at a 30 fps look) is the reference implementation: crouch anticipation,
  dash hidden behind `slices` + an empty-stage blink, cut straight to the contact pose, 4 layers per hit
  (`burst`, `ink_trail` on the limb path, `streaks`, thin white `ink_arc`), pose-cycle juggle, smirk close-up with
  a `bubble`, slash storm (`ink_path` strokes with a cyan `glow`), macro hold.
- Graphic primitives (`Cinematic`): `ink_trail` / `ink_path` / `ink_arc` (brush strokes), `streaks`, `slices`,
  `screen_fx("bw" | "black" | "white" | "glint" | "burst" | "bubble")`, handheld camera, `Scene(hold=2)` to animate
  characters on twos.
- Secondary motion (`tsb_engine/secondary.py`): `coat_and_hair()` gives hat, belt, cuffs, coat tails and hair
  locks simulated as verlet ropes. They are **preview only**: not part of the exported KeyframeSequence.
- `bw` impact frames and black frames exist in the reference, but the in-game constraint (no impact frame, no
  global hitstop) still holds: treat them as optional punctuation for cinematic cuts.
- **Measure against the reference** (`tools/eyes.py`, needs `requirements-eyes.txt`): `ref VIDEO DIR` (screen recording -> 30 fps frames),
  `film SCENE DIR` (render the film camera, clean), then `compare REF DIR OUT --anchors "ref:mine,..."` -> `diagnosis.txt` (LOW/HIGH numbers
  with what to change), `beats.md` (per reference shot), `pairs.png` (ref above mine, shot by shot), `compare.png` (curves). Use it after every
  restage; numbers catch scale/pace/coverage errors, `pairs.png` catches what numbers hide (an ink ring counted as "character size").
  `trail` / `flow` show where things move (use windows of <= 10 frames).
- Always run `keep_above_ground` on every character of a short (the linter's TSB001 catches sunken legs).
- **Read the reference before building** (all frames at 30 fps, 12 per sheet, not a sparse overview): the first reading of the study clip was wrong
  on scale, staging and the avatar's design. `secondary.reference_outfit()` gives the round-brim hat, hair mass and flared coat;
  `screen_fx("strokes")` is the storm wall; `burst(outline=...)` the black star; profile cameras, a *held* hero with a cycling victim for juggles.

### The loop that produced `examples/short.py` (v2): solve, frame, measure, look

Guessing joint angles and filming from a fixed far camera gave unreadable poses (see `docs/analysis/method-comparison.md`).
Work like this instead:

1. **Solve contacts** with `tsb_engine/solver.py`: `reach_root(char, frame, part, target, hint)` puts a limb tip on a
   world point (it slides the Root if out of reach). Key the extreme pose, solve the striking limb, *then* shape around it.
2. **Shape the motion**: anticipation that keeps moving (`moving_hold`), kinetic chain with late head/arms (`chain`),
   a 2-frame `dislocate` of the striking limb block at the hit, an overshoot, a victim that folds first at the hit
   (`react` in the short) and lags the head by 2 frames.
3. **Frame with `autoframe`** (3/4 angles; the fight axis must not point at the camera) so bodies stay 40-80 % of the
   frame height; macro whip-ins use `tracking`.
4. **Measure** with `python tools/check_poses.py <scene> 62,104,...` (screen height, hidden limbs, cut by frame) and look at
   contact sheets with **two views** (3/4 + profile) plus a 2-frame stride strip to judge the motion.
5. Lint (`TSB001/007` must be clean), then show it. Your eye, not the metric, decides.

## Modelling (real meshes, not boxes)

Characters get recognisable through *accessories*: build them with `tsb_engine.modeling` (`bevel_box`, `lathe`, `sweep`, `cone`, `torus`, `merge`), glue them with `secondary.Attach(name, part, mesh, offset, tilt)` in the part's local frame, hide a box part with `Character(hide=("Head",))` when a mesh replaces it. `examples/ronin_model.py` is the worked example (hair spikes from cones, katana from a swept blade + lathe handle). Check `Mesh.stats()` and render close-ups (`tools/render_frames.js ... film`) before judging; the viewer shades flat per face. Not verified: Studio import, MeshPart triangle limit. Details: `docs/research/modeling.md`.

## Running, and following a runner (what "marionette" and "weird follow" were)

* **Run with `tsb_engine/gait.py`**, never with hand-keyed flapping limbs: `run_keys` (legs in opposite phase, trailing leg swings further back, arms counter-swing, torso counter-rotates,
  head level), then `rest_on_ground` (the root height comes from the planted foot - R6 legs are rigid sticks) and `add_air` (flight phases). **Tie speed to stride**:
  `stride_speed(amp, period)` studs/image, or the feet skate. A stylised accent pose every ~9th image pair keeps the silhouette jumping without breaking the gait.
* **Never guess a reference's camera.** Track the hero in the reference (`tools/eyes.py hero DIR OUT.json --prompt F --points X,Y X,Y ...`, points on head, torso and legs) and read
  `cx, cy, h` (centre and size in picture heights): the follow is either **locked** (cx, cy constant: the sprint) or a **sweep** (he crosses the frame: the run at the mannequin).
  Build the camera from the track (`framed_cam`, `chase_framed` in `examples/calm.py`) and check with `tools/eyes.py match SCENE TRACK.json` (error in picture heights).
* **Read the story before animating it**: list what happens in each shot, who runs which way, where each actor stands, and which beats are the *same action seen again from another angle*
  (the final blow of the reel is one blow in three camera angles). A wrong story cannot be fixed by polish.

## Roblox integration facts (verified on the official docs, 2026-10-28; details in `docs/research/rnd-audit.md`)

- Procedural offsets on `Motor6D.Transform` (fake limb, dislocation, tilt) must be written in `RunService.PreSimulation`; otherwise the Animator overwrites them next frame.
- No Pause/Freeze on `AnimationTrack`: hitstop = `AdjustSpeed(0)` on every playing track, restore after, **per client** (Willikk's roblox-mesh-vfx does this within ~90 studs).
- Animation priorities Idle 0 .. Action4 5, Core 1000 (same as `roblox_export.PRIORITY`). Markers are read with `GetMarkerReachedSignal(name)`.
- NOT verified: whether an animation played from a LocalScript replicates to others, how `AnimationConstraint` relates to R6/Motor6D, whether a hand-written `.rbxmx` imports with its markers. Test in Studio before relying on them.
- Before exporting with fewer keys than frames run `python tools/check_export.py <scene> <char> --optimize`: it re-reads the exported file, plays it with Roblox's interpolation and reports the error in studs (a 60-stud blink-cut turned into a slide at a coarse step; fixed by keeping authored keys, but fast spins still need dense keys).
- Reusable code only from MIT sources (Willikk, RoClicks, Chrrxs/robloxstudio-mcp), with credit; RigBridge / Motion Tools have no licence, Staticaliza is GPL, Roqer is AGPL: ideas only.

## Reading a reference video (do this BEFORE any analysis; details in `docs/research/eyes-validation.md`)

The eyes are **not** reliable for poses (black limbs on a black coat, dark ink, camera parallax). They are reliable for black/white
punctuation frames, empty stage, walls of strokes and clear camera moves. Never state a hit count, "held hero" or "VFX-made multi-hit"
from the measurements alone. Protocol:

1. `python tools/eyes.py ref VIDEO DIR` (add `--fps 60` for fast effects), then `python tools/eyes.py read DIR OUT --mask-right 0.17`.
2. Open `OUT/hot_windows.png` and the numbered sheets; look at EVERY frame around each peak (a 2-frame smear is invisible when sampling).
3. Tell apart before writing: a **real hit** (pose changes, victim reacts, flash once per hit) / a **VFX-made multi-hit** (one or two
   arm poses flipping every image + a new flash/streak fan on every image + the victim shaken back and forth) / a **held pose with VFX**
   (effects fire, nobody reacts) / a **camera move** (the whole background shifts consistently) / a **cut** (the background is replaced).
4. Fill `OUT/reading.json` (`viewed`, `camera`, `punct`, `hits`, `vfx_multihit`, `victim`) and run `python tools/eyes.py check DIR OUT/reading.json`;
   re-open the frames behind every contradiction.
5. To read **poses and hits** (what thresholds cannot): `python tools/eyes.py propose DIR FRAME OUT.png` -> look at the numbered candidates -> `python tools/eyes.py track DIR OUT --first A --last B --obj name=F:X,Y ...`
   (F = frame index inside A..B, X,Y = a point on the object). It follows each object with SAM 2, reports track reliability (good >= 7 logit) and the motion kind:
   `strobe` (flips between two extensions every image = ONE gesture + VFX / multi-hit illusion), `cycling`, `moving`, `steady` (held).
   Trust the kind only when the track is `good` (8/8 on the bench); on `doubtful`/`lost` open `track.png`. Never use the masks' area/IoU (mean IoU 0.25 on the bench).
6. Validate the tools themselves with `python tools/eyes_bench.py --reference DIR` after changing them (bench 28/30, reference 7/7 reliable checkpoints).

## Rules of engagement

- Tag every number you introduce: `[physical]` follows from the rig, `[heuristic]` a starting
  value to tune, `[style]` aesthetic, `[unverified]` unknown. Never present a heuristic as a
  measurement or as "what TSB does". No public source documents TSB's real numbers.
- Do not invent asset IDs, plugin shortcuts or engine properties. Check
  `references/roblox-facts.md` first; if it is not there, say it is unverified.
- Do not silently "auto-fix". Prefer explicit helpers and report what you changed.
- The linter reports; the user decides. The user's eye is the final judge, not the linter.
- Roblox export exists (`tsb_engine/roblox_export.py`: `.rbxmx` + a Luau builder script). The pose mapping is
  verified against Roblox's forward kinematics in the tests, but **Studio import of a Python-written file is not
  verified** (Roblox warns such files "might not upload or function"): say so, and offer the Luau builder as fallback.
  Root travel of many studs belongs to game code, not to the animation.
- Textures: `python -m tsb_engine.textures` bakes flipbook sheets; the frame order inside a sheet is unverified in
  Roblox, so have the user check `assets/flipbooks/order_test_*.png` in Studio first.
- Before inventing a VFX recipe, read `docs/research/github-survey.md` (numbers, licences, traps such as forge-vfx's licence).

## Conventions (must match the engine)

Y up, character faces **-Z**, +X is the character's right. Rotations in degrees, `CFrame.Angles`
order. For hanging limbs (arms, legs) `rx > 0` swings forward; for the torso and head `rx < 0`
leans/nods forward. Negative torso `ry` winds the right shoulder back.
`Pose.pos` z < 0 pushes a limb forward (used for dislocation). Standing: root y = 3, feet y = 0.
Limb rotations are in the torso frame, not raw Motor6D axes (the real R6 joints have rotated
C0/C1 — verify when writing an exporter).

## Files

- `tsb_engine/` – model, forward kinematics, `moves.py`/`footwork.py` (planted feet, steps, gaits), `authoring.py`, `cinematic.py`, `linter.py`, CLI.
- `examples/builders.py` – a worked heavy punch plus two deliberately bad animations; `examples/ultimate.py` – the 13 s berserker ultimate; `examples/short.py` – the reference-level 11 s short.
- `tsb_engine/secondary.py` – hair, coat and hat secondary motion (preview only).
- `tsb_engine/perception.py`, `reading.py`, `examples/eyes_bench.py`, `tools/eyes_bench.py` – the reader, the reading ledger and the labelled bench (results and limits: `docs/research/eyes-validation.md`).
- `tsb_engine/export_check.py` + `tools/check_export.py` – round-trip check of the `.rbxmx` export (Roblox interpolation + Motor6D FK vs the engine) and adaptive keyframe optimisation.
- `docs/research/rnd-audit.md` – verified audit of the Roblox/Blender/VFX repos and docs (licences, what is verified, test plan for Studio).
- `tsb_engine/solver.py` – limb aiming/contact solving, dislocation, moving hold, kinetic chain; `tsb_engine/readability.py` + `tools/check_poses.py` – picture-space pose checks.
- `docs/research/reference-analysis.md` – frame-level study of a user-supplied reference clip.
- `examples/scenes.py` + `viewer/` + `tools/` – attacker/victim scene, HTML viewer, frame rendering.
- `references/principles.md` – craft rules by archetype, with confidence tags.
- `references/roblox-facts.md` – verified facts and known traps.
- `references/vfx-notes.md` – VFX layering notes (reference only; no VFX tooling yet).
- `tests/` – `python -m unittest discover -s tests`.
