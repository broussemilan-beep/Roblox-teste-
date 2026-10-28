# GitHub survey: Roblox VFX, Roblox animation export, Blender, cross-engine VFX

Four research passes (web only) on public GitHub and docs. Every repo below was opened by the researcher; the
summaries went through a small summarising model, so **re-read the raw file before hard-coding a number**. Stars and
dates are as seen at the time (late Oct 2026). `[INF]` = inference, not source content. Nothing was copied verbatim
from a repo whose license forbids it; ideas and public facts (formats, enum values, formulas) were re-implemented.

## 0. What does not exist (so nobody searches again)

* No open-source **TSB / battlegrounds** VFX or moveset with real effect data (searches return exploit scripts, paid packs, empty repos).
* No open-source **slash / shockwave / impact-star generator for Blender** (all hits are paid: Superhive, Gumroad).
* No open-source **Moon Animator clone**, animation compressor or battlegrounds moveset pack.
* No free **Roblox-specific texture sheets** except the CC0 pack inside EasyVFX (below).
* No real Studio-exported **R6** KeyframeSequence with markers found (examples were R15 or script-generated).

## 1. Roblox VFX (recipes with numbers)

| Source | License | What is in it |
|---|---|---|
| `adnvli/vfxskill` (31★, Oct 2026) | MIT | Claude-skill with numeric docs measured on ~5,000 published emitters (`references/vfx-*.md`, `templates/vfx/emit.lua`). Best recipe source. **Numbers only: it ships no textures.** Combat timings are R15-based. |
| `VuxSussy/EasyVFX` | MIT | 45 presets with per-layer numbers (`src/Plugin/Shared/Presets.luau`), docs on impact/hit-stop/curved beams, and `pack/cc0/` (327 textures, per-file source/licence manifest: Kenney, Brackeys, Picster, all CC0 per the docs). |
| `nonlooped/roblox-suite` | MIT | Emitter/flipbook limits, pooling checklist. |
| `Sleitnick/RbxCameraShaker` (128★) | MIT | Shake presets `new(magnitude, roughness, fadeIn, fadeOut)`. |
| `SamyBlue/Lightning-Beams`, `evaera/EvLightning` | MIT | Neon-part lightning (not Beams). |
| `rbxrootx/Spark`, `zilibobi/forge-vfx` | MIT / **custom VFX-DL 1.1** | Attribute convention `EmitCount` / `EmitDelay` / `EmitDuration`. **forge-vfx's licence forbids use in tools/plugins and requires the same licence for derivatives: do not copy its code.** |
| `nezuo/roblox-flipbook-packer` | MIT | Packs sheets 2x2/4x4/8x8 on 1024x1024. |
| `Roblox/creator-docs` | CC-BY-4.0 / MIT | Official spark-burst example (Drag 10, Lifetime 0.2-0.6, Speed 20-40, SpreadAngle 180, Emit 100). |
| `sebasvcx/ViewportStencil` | MIT | Ground cracks "inside" the floor via ViewportFrames (client-only, no shadows). |

### Recipes we kept (all from the sources above; tune in game)

* **Impact stack** (adnvli `vfx-craft.md`): flash at t=0 (Lifetime 0.06-0.1, Brightness ~10, Size 4->16); stars at +0.03 s (4x4 spiky sheet, Lifetime 0.075-0.15, EmitCount 2-6); **black twin** of each colour layer at z..z+0.25 and a dark backing blob 2-4R behind the star (Transparency 0.35->1) so the hit reads on bright surroundings; streaks `VelocityParallel`, Speed 60-160, Drag 10, Squash 3->1, 12 particles; ring `VelocityPerpendicular` Size 2->16, 0.35 s; smoke Lifetime 1-1.5; PointLight Brightness 7-16, Range 7-15 fading over 0.5 s.
* **Star hold** (EasyVFX `impact.md`): white star held ~0.09 s (2-3 frames), then the hollow-out flipbook; ring 0.2-0.3 s.
* **Shockwave** (adnvli): cylinder `(0.1,2,2) -> (0.05,20,20)`, Transparency 0.55->1, 0.35 s, Cubic Out. EasyVFX: three rings staggered 0.1 s, radius 1->16, width 1.2->0.05 + dust burst. Domes: keep Transparency 0.85-0.96 (below ~0.75 they look solid against a bright sky).
* **Crescent slash with a Trail only** (adnvli `vfx-motion.md`): two Attachments at inner/outer radius on an invisible part spinning 160 deg in 0.14 s (Quart Out), `FaceCamera=false`, width tapering to 0.
* **Curved Beam arc**: `CurveSize0 = CurveSize1 = 4/3 * tan(arc/4) * radius` (up to ~200 deg); a full ring = 4 beams with `CurveSize ~ 0.5523 * radius` (EasyVFX `sharp-vfx.md`).
* **Lightning**: chain of Beams, shared attachments, re-roll every ~0.05 s; Lightning-Beams defaults PartCount 30, AnimationSpeed 7; EvLightning bends 6, fork_chance 50.
* **Camera**: light hit magnitude 0.3-0.55 / roughness 3-23 / fade 0.15-0.3 s; heavy 2.5-5 / 6-10 / 0.9-1.5 s; FOV punch 5-7 deg over 4 frames; RbxCameraShaker `Bump (2.5,4,0.1,0.75)`, `Explosion (5,10,0,1.5)`. Apply with `BindToRenderStep` at `Camera.Value-1` (undo) and `+1` (apply) or offsets accumulate.
* **Charge-up**: glow shrinking 1.5R->0 in 0.1-0.15 s or ring 11->0 in 0.15-0.2 s; `ShapeInOut = Inward`; lead 0.1-0.6 s.
* **Ground**: 6-36 rocks, radius 3-54, tilt 8-55 deg, copy the hit surface's Material/Color; grow 0.4 s, hold 1.5-5 s, sink 1.5-3 s; cooling crack = decal Color3 ~10 -> black over ~1.3 s.
* **Performance** (nonlooped): ~400 particles/s per emitter on desktop (100 mobile), disable far emitters at 100-300 studs, 255 simultaneous `Highlight`s, pool and reset (`Enabled=false` + `:Clear()`), 40-60 emitters per hit effect.
* **Flipbooks**: 1024x1024, Grid4x4 is used on 81% of studied emitters, `FlipbookFramerate` <= 30, ~4 px padding per cell, white-on-transparent tinted by `Color`.
* **Effect-side hit-stop** (EasyVFX docs): 50-100 ms; effects hold via `TimeScale = 0`. Only the effect half applies to us (no global hit-stop in this project).

## 2. Roblox animation export (verified structure)

| Source | License | Use |
|---|---|---|
| `gat516/martial-world` (`art/player/techniques/green_dragon_whirlwind.py`) | none found | Pure-Python R6 `.rbxmx` writer: stock **R6 Motor6D C0/C1 table**, FK formula, KeyframeMarker XML. Closest to our case. |
| `Chrrxs/kimodo-r15-retarget` (`retarget/rbxmx.py`) | MIT | Cleanest XML writer (R15). |
| `jiwonz/anim2rbx` | MIT | Rust: FBX/glTF -> KeyframeSequence `.rbxm`; proves a minimal sequence (Priority, Time, Pose Name/CFrame/Easing) is accepted by tools. |
| `SyphoDev-yt/roblox-ai-skills` | custom "free" licence | Docstring facts + a Luau edit-mode builder as fallback to XML. |
| `rojo-rbx/rbx-dom` + https://dom.rojo.space/xml.html | MIT | Format spec: `<roblox version="4">`, `Item class/referent`, `CoordinateFrame` = X Y Z R00..R22 row-major, enums as `token`. |
| `jackTabsCode/asphalt` | MIT | Uploads `.rbxm/.rbxmx` animations via Open Cloud. |
| `Cautioned/Blender-Animations-Plugin` (111★) | GPL-3.0 | Live Sync Blender -> Studio, `.rbxanim`. Not copied (GPL). |

Facts used by `tsb_engine/roblox_export.py`:

* `Pose.CFrame` is the Motor6D `Transform`: `world(Part1) = Part0 * C0 * Transform * C1^-1`. R6 tree: `HumanoidRootPart (Weight 0) > Torso > Head, Right/Left Arm, Right/Left Leg`.
* Stock R6: each joint's C0 and C1 share one rotation matrix `M` (RootJoint and Neck: `(-1,0,0, 0,0,1, 0,1,0)`; right shoulder/hip `(0,0,1, 0,1,0, -1,0,0)`; left `(0,0,-1, 0,1,0, 1,0,0)`). Our engine uses plain translations, so `Transform = M^-1 * X * M`; **checked in tests by re-running Roblox's FK and comparing with `kinematics.part_transforms` (max error < 1e-9).**
* `Priority` token: Idle 0, Movement 1, Action 2, Action2 3, Action3 4, Action4 5, Core 1000. `PoseEasingStyle`: Linear 0, Constant 1, Elastic 2, Cubic 3 (deprecated), Bounce 4, CubicV2 5. `PoseEasingDirection`: In 0, Out 1, InOut 2. `MaskWeight` deprecated: omitted.
* Markers: `KeyframeMarker` children of a `Keyframe`, on exact keyframe times; read with `AnimationTrack:GetMarkerReachedSignal`.
* Upload: Open Cloud `POST apis.roblox.com/assets/v1/assets` accepts `.rbxm/.rbxmx` for Animation (DevForum, 2025-10-23) but the docs warn that files "edited outside of Roblox Studio might not upload or function". **Not verified end-to-end for a Python-written file: test it. The Luau builder is the fallback.**
* `RegisterKeyframeSequence` returns temporary ids usable only inside Studio.

## 3. Blender

Headline: nothing open-source generates stylised VFX shapes; what is reusable is sprite-sheet baking, Roblox bridges, SMEAR, and Blender 5 API notes.

| Source | License | Nugget |
|---|---|---|
| `bgivenb/blender-spritesheet` (Blender 3.6+/4.5) | **CC0** | Even frame sampling `[round(start + i*span/(count-1))]`, Y-flip for cell origin, row-wise buffer copy, headless command line. |
| `MoStyle/SMEAR` (70★) | CeCILL v2.1 | Smear: per vertex `delta = ((v - centroid) . v_dir) / max`, skeletal ribbon normals, temporal smoothing `(1-x^2)^2`. **Re-implement the idea, do not copy.** |
| `EL4CTEO/blender-skills` (548★, MIT) | MIT | Blender 5 API table: `Action.fcurves` -> channelbags (`anim_utils.action_get_channelbag_for_slot`), `BLENDER_EEVEE_NEXT` -> `BLENDER_EEVEE`, `id_root` -> `action_slot.target_id_type`. |
| `Staticaliza/...Animation-Tools`, Stop Motion Style Animator | GPL-3 | Blender 5-compatible 2s/3s stepping, onion skin, Roblox rig import (zips only). |
| `dillydog580/animate-roblox-characters` | MIT (+GPL ext.) | R6/R15 Blender pipeline, `.rbxanim` or animation-only FBX. |
| `Roblox/roblox-blender-plugin` (MIT) | MIT | Open Cloud mesh upload reference. |
| `GSGarciaML/lightning-sim` | MIT | Dielectric-breakdown lightning (eta 0.9): overkill for stylised bolts. |

Roblox FBX animation export settings (official): Apply Scalings = FBX Unit Scale; Add Leaf Bones off; NLA Strips + All Actions on, Force Start/End off; Simplify 0.0. Headless Blender is **not installed in this sandbox**, so the texture baker is pure numpy/Pillow (the path the Blender researcher also recommends for flat 2D effects).

## 4. Cross-engine techniques

* **Game-feel numbers** (Godot hit-stop/shake tutorial, MIT): trauma shake = `trauma^2`, light +0.4 / heavy +0.7, decay 1-2.5/s; hit-stop light 0.04-0.08 s, heavy 0.10-0.18 s; overlapping hits extend, never restore early. Bevy: max 10 deg / 20 px, decay 0.5/s. SSBWiki hitlag: Ultimate `floor((damage*0.65+6)*mults)` capped at 30 frames.
* **Smear**: 1 frame on TV, 1-2 in games, between two strong keys, never on the impact pose; "multiples" for flurries.
* **Timing grid**: ones 24, twos 12, threes 8 drawings/s; anime mostly threes.
* **Procedural textures** (written in `tsb_engine/textures.py`): starburst = angular lobes `exp(-(da/w)^2)` x `exp(-r/L)` (Godot-Shaders CC0 formula), lightning = midpoint displacement + branches + 3-pass glow, smoke = fBm + domain warp + noise dissolve + posterise, slash = disc minus offset disc wiped along the arc, ring = gaussian annulus with angular ripple.
* **Traps avoided**: the Godot-Shaders "cartoon explosion" is CC BY-NC-SA (not copied); some repos created in one burst with identical metadata looked like bait (not opened); `taozhuo/game-dev-skills` could not be verified; a cluster of pirated-asset dumps was excluded.

## 5. What was applied in this repo

| Brick | Where |
|---|---|
| `.rbxmx` KeyframeSequence + Luau builder, R6 joint mapping, markers, tested against Roblox FK | `tsb_engine/roblox_export.py`, `exports/*.rbxmx|.luau` |
| Procedural flipbook baker (hit star, starburst, slash, ring, lightning, smoke, fire), RGB bleed, numbered order-test sheet | `tsb_engine/textures.py`, `assets/flipbooks/` |
| Flipbook sprites played in the viewer exactly like a ParticleEmitter flipbook (hit stars, smoke) | `Cinematic.use_sheet/sprite`, viewer `sprite` fx |
| Black twin behind hit stars (readability on bright surroundings) | viewer `burst` |
| FOV punch, trauma-style shake values, impact stack ordering | `examples/ultimate.py` |
| Cue sheet: every fx of the film translated to Roblox primitives with converted units (s, studs/s) | `tsb_engine/roblox_cues.py`, `exports/ultimate_vfx_cues.md` |

Open items: confirm flipbook frame order in Studio with `assets/flipbooks/order_test_*.png`; test that Studio imports `exports/*.rbxmx`; the 780-frame root travel (50+ studs) must be driven by game code, not by the animation.

## 6. Second batch (repos supplied by the user)

Checked by three more readers (they read the code, not only the READMEs). Verdicts:

| Repo | License | Verdict | What we took |
|---|---|---|---|
| `Willikk/Roblox` (4 commits, Claude co-authored, but tested and coherent) | MIT | **HIGH** for feel/VFX plumbing | Camera trauma settings (angles 2.2/2.2/3.5 deg, offset 0.25/0.25/0.1 studs, 16 Hz, decay 1.3/s, exponent 2, offset undone at `Camera-1` and re-applied at `Camera+1`), trauma by hit class (jab 0.08-0.12, heavy 0.25-0.35, slam 0.4-0.6, ultimate 0.8), `ScreenFlash.impact{duration 0.18, contrast 0.2, bloom 1.2, blur 6}`, per-fighter hit-stop durations (light 0.04-0.06 s, heavy 0.08-0.12 s) via `AnimationTrack:AdjustSpeed`, seeded 31-byte VFX replication records (effects never call `math.random`; attacker predicts cosmetics), pooling and "fade a snapshot, not just Transparency". No dash/sprint/hitbox code in it. |
| `zriptic/roclicks-skills` `roblox-vfx/` (MIT, notices "RoClicks 2026" + "TabooHarmony 2026", adapted from Roqer's skills) | MIT (keep the notices) | **HIGH** | Impact skeleton and timings (flash at 0, everything else +0.03 s or later in 0.025-0.05 s steps, "intensity only goes down"), black-twin rules (twin lifetime 1.1-1.2x, black backing 1.1-4.5x at ZOffset -1..-3, lopsided shapes must share Rotation/RotSpeed), brightness/bloom rules, motion numbers, slash recipes, camera/FOV tables, flipbook facts, and the *sheet checker + `.flipbook.json` sidecar* idea (implemented in `textures.check_frames`). Same upstream as `adnvli/vfxskill`, which omits the attribution: we credit roclicks. |
| `yansha-os/motion-tools` (no licence) | none: **ideas only** | MEDIUM | Marker phase taxonomy (anticipation / action / follow-through / recovery / event), contact intervals, lint heuristics (synchronized timing, key density, loop-seam velocity), retarget math, mirror = matrix conjugation. Implemented independently as lint rules TSB012 and TSB014. |
| `alycoulibal2-sketch/Cadence-Animator` (MIT, 269 commits, Claude co-authored) | MIT | MEDIUM-HIGH for ideas | **Independent confirmation of our R6 Motor6D data** (Right Shoulder C0 `[1,0.5,0, 0,0,1, 0,1,0, -1,0,0]`, Neck C0 `[0,1,0, -1,0,0, 0,0,1, 0,1,0]`...). Rule: only Linear/Constant/Cubic/Elastic/Bounce are native to Roblox; any other curve (Bezier, Back, Expo...) **must be baked** into keyframes (our exporter bakes every frame). Combat heuristics from its video-derived notes (unvalidated): do not ease into the impact, do not ease idle into wind-up, combo hits defer follow-through to the last hit, use ones for very short actions. Implemented as lint rule TSB013. |
| `UseLuna/luna-runtime` (MIT, 26 commits) | MIT | MEDIUM | Data shape only: 6 scalar channels per joint with Linear/Bezier/Easing keys, markers, bone masks, quantised export. No events/markers at runtime. Not adopted (it replaces Roblox's Animator). |
| `Bloodhundur/OpenVFX` | **none** (README only says "use, add, modify") | LOW | A plugin + JSON list of third-party texture asset IDs of unknown rights. Only the category taxonomy (Wind, Swirl, Ground, Flare, Beam, Grid; Static/2x2/4x4/8x8) is reusable. Do not ship its IDs in a commercial game. |
| `rbxrootx/Spark` (93 lines) | MIT | LOW | Only the `EmitCount/EmitDelay/EmitDuration` attribute names, which roclicks' `Emit.luau` implements far better (one clock, absolute delays, cap 500, slow-mo and freeze with one restore). |
| `CoverTheWeb/ArenaAnimator` | MIT (per README) | LOW | AI-style plugin with a weaker exporter (flat Cubic InOut, duplicated parent poses). Nothing to take. |
| `quantumsrt/movement` | **none** | LOW | Single-session AI output, procedural locomotion (max lean 9 deg, exp smoothing `1 - exp(-13*dt)`). Not copied. |
| `luizguilhermevalentinecreis-ai/Visual-Director` | - | **not openable (HTTP 404)** | Private, deleted or misspelled: send the right URL if it matters. |

Not found in any of the ten: dash / sprint / `LinearVelocity` / hitbox / combo state-machine code. Search elsewhere for those.

### Applied from the second batch

| Brick | Where |
|---|---|
| Impact skeleton timing: flash at the hit frame, star +1, ring/sparks/smoke +2 | `examples/ultimate.py` (punch loop) |
| Hit events as game data (class, trauma, FOV punch, screen-flash, seeded VFX id, *optional* per-fighter hit-stop) + `CameraShaker` settings | `tsb_engine/roblox_cues.py`, `exports/ultimate_hit_events.json` |
| Marker phases (Windup / Hit / Recovery...) in the exported KeyframeSequence | `examples/ultimate.roblox_markers`, `tools/export_roblox.py` |
| Lint: `TSB012` synchronized tracks, `TSB013` ease into impact, `TSB014` key density (baked tracks exempt) | `tsb_engine/linter.py` |
| Flipbook checker + `.flipbook.json` sidecar; edge window so nothing touches the cell border | `tsb_engine/textures.py` |
| One command to export everything | `python tools/export_roblox.py` |

Credits: the numbers taken from `zriptic/roclicks-skills` (MIT, Copyright (c) 2026 RoClicks, roblox-vfx adapted from Roqer's skills, Copyright (c) 2026 TabooHarmony) and `Willikk/Roblox` (MIT) are used under their licences; their notices are reproduced here as required.


## 7. "Eyes": tools to read motion and fx (searched on request, 2026-10-28)

Goal: stop judging a reel only by looking at contact sheets; measure pace, holds, scale, fx coverage and motion, and diff a
render against a reference. GitHub/PyPI search results (popular first):

| what | repos / packages | verdict |
|---|---|---|
| deep optical flow | NVIDIA/flownet2-pytorch (3.3k), NVlabs/PWC-Net, open-mmlab/mmflow, haofeixu/gmflow | needs GPU + weights; overkill for 900x400 clips. **Not used.** OpenCV's DIS / Farneback flow is enough |
| shot / cut detection | Breakthrough/PySceneDetect (5.3k, BSD-3), albanie/shot-detection-benchmarks | **Used** as an optional cross-check (`eyes.scenedetect_cuts`); own cut detector (histogram + frame difference + black/white flips) is the default because punctuation frames (1-2 f) matter |
| frame differencing / motion energy | many small OpenCV demos (surveillance style) | trivial; reimplemented with proper normalisation |
| anime / sakuga | KytraScript/SakugaDataset (Sakuga-42M, 87 stars), bconstantine/SketchColour, Sakuga-Engine (a Godot fighting game) | a dataset and unrelated engines; **no tool that reads timing/smears or compares two clips**. Ideas only |
| animation timing charts | Unarmed1000/mb-framepacing-explained (frame pacing, 1 star) | about display frame pacing, not animation craft |

Conclusion: nothing existing does "read an animation clip and diff it against another". The pieces (OpenCV, scikit-image,
matplotlib, PySceneDetect) are standard, so `tsb_engine/eyes.py` + `tools/eyes.py` assemble them (see `requirements-eyes.txt`).
What it measures: update energy, optical-flow speed/direction, subject height, screen coverage by black/white/cyan, edge density,
shot cuts and holds, cadence; aligns two clips by hand-picked anchors (or DTW) and prints a numbered diagnosis, a per-shot table
and a ref-above-mine picture for every reference shot. It does **not** judge appeal or weight: that stays with human eyes.
