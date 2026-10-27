# VFX cue sheet (starting values, tune in game)

| time | frame | effect | Roblox implementation |
|---|---|---|---|
| 0.50s | 30 | particles (flame) | ParticleEmitter at (0.0, 0.9, 0.0): Rate 60/s for 1.52s, Speed 2-6, Lifetime 0.43-0.77s, Acceleration Y 11 , flipbook `fire` (Grid8x8, 24 fps) or 3 stacked emitters, LightEmission 1. Alpha NumberSequence 0.70->0.00. |
| 0.50s | 30 | particles (spark) | ParticleEmitter at (0.0, 0.2, 0.0): Rate 78/s for 2.33s, Speed 1-4, Lifetime 1.00-1.83s, Acceleration Y 5 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 0.87s | 52 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 0.87s to 0.95s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.17s | 70 | glow | PointLight Brightness 1->4, Range 5->16 + one billboard emitter (round glow, flare=0.0) for 1.67s. |
| 1.17s | 70 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.17s to 1.25s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.33s | 80 | ground/wall cracks | Decal or thin dark Parts radiating 6 studs (9 branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s). |
| 1.42s | 85 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.42s to 1.50s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.63s | 98 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.63s to 1.72s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.82s | 109 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.82s to 1.90s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.82s | 109 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.82s to 1.90s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.83s | 110 | camera shake | magnitude 0.3, roughness 10, fade 0.20s (RbxCameraShaker-style, rotation + offset) |
| 1.87s | 112 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.0, 0.1, 0.0), radius 0.6->6.0 in 0.40s (Tween Quart/Expo Out), Transparency 0.30->1, thickness 0.9->0.15. Stagger repeated rings by 0.1 s. |
| 1.97s | 118 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.97s to 2.05s; branch chance 0.20. Colour #ff5a1f, core white. |
| 1.97s | 118 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 1.97s to 2.05s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.03s | 122 | particles (flame) | ParticleEmitter at (0.0, 0.9, 0.0): Rate 96/s for 0.80s, Speed 3-10, Lifetime 0.43-0.83s, Acceleration Y 14 , flipbook `fire` (Grid8x8, 24 fps) or 3 stacked emitters, LightEmission 1. Alpha NumberSequence 0.75->0.00. |
| 2.03s | 122 | ground/wall cracks | Decal or thin dark Parts radiating 12 studs (14 branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s). |
| 2.03s | 122 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.0, 0.1, 0.0), radius 0.6->16.0 in 0.40s (Tween Quart/Expo Out), Transparency 0.30->1, thickness 0.9->0.15. Stagger repeated rings by 0.1 s. |
| 2.03s | 122 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.20s, Size 1.0->8.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 14 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.0, 4.9, 0.5). |
| 2.03s | 122 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.25s, Size 1.0->8.8. |
| 2.03s | 122 | glow | PointLight Brightness 4->0, Range 10->5 + one billboard emitter (round glow, flare=1.4) for 0.20s. |
| 2.03s | 122 | dome | Neon sphere at (0.0, 3.0, 0.0), size 2.0->14.0 in 0.33s, Transparency 0.88->1 (keep >= 0.85: lower values look solid on bright skies). |
| 2.03s | 122 | light beam | Neon cylinder/Beam (0.0, 0.0, 0.0) -> (0.0, 34.0, 0.0), width 2.0->0.0 over 0.67s, Transparency 0.50->1. |
| 2.03s | 122 | particles (smoke) | ParticleEmitter at (0.0, 0.3, 0.0): 90, Speed 15-39, Lifetime 0.50-1.17s, Acceleration Y -14 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.55->0.00. |
| 2.03s | 122 | particles (spark) | ParticleEmitter at (0.0, 0.3, 0.0): 60, Speed 18-54, Lifetime 0.33-0.77s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 2.03s | 122 | camera shake | magnitude 1.8, roughness 10, fade 0.47s (RbxCameraShaker-style, rotation + offset) |
| 2.03s | 122 | screen flash | ColorCorrection Brightness +0.25, TintColor #ffd9a8 for 0.10s |
| 2.03s | 122 | screen flash | ColorCorrection Brightness +0.30, TintColor #ffd9a8 for 0.13s |
| 2.10s | 126 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.10s to 2.18s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.10s | 126 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.10s to 2.18s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.10s | 126 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.10s to 2.18s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.18s | 131 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.0, 0.1, 0.0), radius 0.6->22.0 in 0.40s (Tween Quart/Expo Out), Transparency 0.30->1, thickness 0.9->0.15. Stagger repeated rings by 0.1 s. |
| 2.20s | 132 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.20s to 2.28s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.20s | 132 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.20s to 2.28s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.20s | 132 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.20s to 2.28s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.30s | 138 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.30s to 2.38s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.30s | 138 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.30s to 2.38s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.30s | 138 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.30s to 2.38s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.38s | 143 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.38s to 2.47s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.38s | 143 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.38s to 2.47s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.38s | 143 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.38s to 2.47s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.47s | 148 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.47s to 2.55s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.47s | 148 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.47s to 2.55s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.47s | 148 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.47s to 2.55s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.55s | 153 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.55s to 2.63s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.55s | 153 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.55s to 2.63s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.55s | 153 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.55s to 2.63s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.63s | 158 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.63s to 2.72s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.63s | 158 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.63s to 2.72s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.63s | 158 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.63s to 2.72s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.72s | 163 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.72s to 2.80s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.72s | 163 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.72s to 2.80s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.72s | 163 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.72s to 2.80s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.77s | 166 | trail | Trail on Torso: Lifetime 0.17s, width 1.4->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.33s. |
| 2.77s | 166 | particles (smoke) | ParticleEmitter attached to character 0 Right Leg: Rate 66/s for 0.33s, Speed 1-5, Lifetime 0.40-0.67s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.50->0.00. |
| 2.77s | 166 | particles (smoke) | ParticleEmitter attached to character 0 Left Leg: Rate 66/s for 0.33s, Speed 1-5, Lifetime 0.40-0.67s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.50->0.00. |
| 2.77s | 166 | ground streak | Flat Neon part growing along the path over 0.33s (2 stacked layers wide->narrow, hottest on top); fade after. |
| 2.80s | 168 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.80s to 2.88s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.80s | 168 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.80s to 2.88s; branch chance 0.20. Colour #ff5a1f, core white. |
| 2.80s | 168 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.5; re-roll the offsets every 0.05 s from 2.80s to 2.88s; branch chance 0.20. Colour #ff5a1f, core white. |
| 3.02s | 181 | trail | Trail on Right Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.07s | 184 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.10s | 186 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->3.6 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-0.0, 2.5, -9.8). |
| 3.10s | 186 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->3.6. |
| 3.10s | 186 | particles (spark) | ParticleEmitter at (-0.0, 2.5, -9.8): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.10s | 186 | shockwave ring | upright Neon ring MeshPart/cylinder at (-0.0, 2.5, -9.8), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.10s | 186 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -12.7): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.10s | 186 | camera shake | magnitude 0.5, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.10s | 186 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.10s | 186 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.15s | 189 | trail | Trail on Left Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.20s | 192 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.23s | 194 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->3.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.1, 2.2, -10.2). |
| 3.23s | 194 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->3.8. |
| 3.23s | 194 | particles (spark) | ParticleEmitter at (0.1, 2.2, -10.2): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.23s | 194 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.1, 2.2, -10.2), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.23s | 194 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -13.1): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.23s | 194 | camera shake | magnitude 0.4, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.23s | 194 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.23s | 194 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.28s | 197 | trail | Trail on Right Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.33s | 200 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.37s | 202 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->4.1 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-0.1, 2.5, -10.5). |
| 3.37s | 202 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->4.1. |
| 3.37s | 202 | particles (spark) | ParticleEmitter at (-0.1, 2.5, -10.5): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.37s | 202 | shockwave ring | upright Neon ring MeshPart/cylinder at (-0.1, 2.5, -10.5), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.37s | 202 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -13.4): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.37s | 202 | camera shake | magnitude 0.5, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.37s | 202 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.37s | 202 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.42s | 205 | trail | Trail on Left Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.47s | 208 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.50s | 210 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->4.3 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.1, 2.2, -10.9). |
| 3.50s | 210 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->4.3. |
| 3.50s | 210 | particles (spark) | ParticleEmitter at (0.1, 2.2, -10.9): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.50s | 210 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.1, 2.2, -10.9), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.50s | 210 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -13.8): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.50s | 210 | camera shake | magnitude 0.4, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.50s | 210 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.50s | 210 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.55s | 213 | trail | Trail on Right Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.60s | 216 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.63s | 218 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->4.6 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-0.1, 2.5, -11.3). |
| 3.63s | 218 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->4.6. |
| 3.63s | 218 | particles (spark) | ParticleEmitter at (-0.1, 2.5, -11.3): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.63s | 218 | shockwave ring | upright Neon ring MeshPart/cylinder at (-0.1, 2.5, -11.3), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.63s | 218 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -14.2): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.63s | 218 | camera shake | magnitude 0.5, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.63s | 218 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.63s | 218 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.68s | 221 | trail | Trail on Left Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.73s | 224 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.77s | 226 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->4.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.2, 2.1, -11.7). |
| 3.77s | 226 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->4.8. |
| 3.77s | 226 | particles (spark) | ParticleEmitter at (0.2, 2.1, -11.7): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.77s | 226 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.2, 2.1, -11.7), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.77s | 226 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -14.6): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.77s | 226 | camera shake | magnitude 0.4, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.77s | 226 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.77s | 226 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.82s | 229 | trail | Trail on Right Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 3.87s | 232 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 3.90s | 234 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->5.1 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-0.2, 2.4, -12.0). |
| 3.90s | 234 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->5.1. |
| 3.90s | 234 | particles (spark) | ParticleEmitter at (-0.2, 2.4, -12.0): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 3.90s | 234 | shockwave ring | upright Neon ring MeshPart/cylinder at (-0.2, 2.4, -12.0), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 3.90s | 234 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -14.9): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 3.90s | 234 | camera shake | magnitude 0.5, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 3.90s | 234 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 3.90s | 234 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 3.95s | 237 | trail | Trail on Left Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 4.00s | 240 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 4.03s | 242 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->5.3 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.2, 2.1, -12.4). |
| 4.03s | 242 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->5.3. |
| 4.03s | 242 | particles (spark) | ParticleEmitter at (0.2, 2.1, -12.4): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 4.03s | 242 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.2, 2.1, -12.4), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 4.03s | 242 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -15.3): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 4.03s | 242 | camera shake | magnitude 0.4, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 4.03s | 242 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 4.03s | 242 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 4.08s | 245 | trail | Trail on Right Arm: Lifetime 0.12s, width 0.8->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 4.13s | 248 | glow | PointLight Brightness 5->0, Range 3->5 + one billboard emitter (round glow, flare=0.6) for 0.08s. |
| 4.17s | 250 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.15s, Size 0.5->5.6 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 8 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-0.2, 2.4, -12.8). |
| 4.17s | 250 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.5->5.6. |
| 4.17s | 250 | particles (spark) | ParticleEmitter at (-0.2, 2.4, -12.8): 22, Speed 12-37, Lifetime 0.17-0.37s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 4.17s | 250 | shockwave ring | upright Neon ring MeshPart/cylinder at (-0.2, 2.4, -12.8), radius 0.3->2.3 in 0.15s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 0.4->0.04. Stagger repeated rings by 0.1 s. |
| 4.17s | 250 | particles (smoke) | ParticleEmitter at (0.0, 0.1, -15.7): 7, Speed 3-8, Lifetime 0.30-0.50s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.45->0.00. |
| 4.17s | 250 | camera shake | magnitude 0.5, roughness 10, fade 0.10s (RbxCameraShaker-style, rotation + offset) |
| 4.17s | 250 | FOV punch | -6% FOV (~4 deg) in 4 frames, recover over 0.12s (Back Out) |
| 4.17s | 250 | screen flash | ColorCorrection Brightness +0.10, TintColor #ffe9c4 for 0.05s |
| 4.32s | 259 | slash crescent | Trail between two Attachments at radius 2.8/4.0 on an invisible part spinning 140 deg in 0.17s (Quart Out), FaceCamera false, width taper to 0; or flipbook `slash`. Core Brightness 10-15. |
| 4.37s | 262 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.8->10.9 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 12 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (1.0, 5.3, -12.0). |
| 4.37s | 262 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.25s, Size 0.8->10.9. |
| 4.37s | 262 | lightning | Chain of 14 Beams (FaceCamera false, shared Attachments), width 0.20, jitter 1.2; re-roll the offsets every 0.05 s from 4.37s to 4.57s; branch chance 0.30. Colour #ffd27a, core white. |
| 4.37s | 262 | lightning | Chain of 10 Beams (FaceCamera false, shared Attachments), width 0.12, jitter 1.0; re-roll the offsets every 0.05 s from 4.37s to 4.53s; branch chance 0.20. Colour #ffd27a, core white. |
| 4.37s | 262 | shockwave ring | flat Neon ring MeshPart/cylinder at (1.0, 0.1, -12.6), radius 0.6->15.0 in 0.43s (Tween Quart/Expo Out), Transparency 0.15->1, thickness 1.2->0.15. Stagger repeated rings by 0.1 s. |
| 4.37s | 262 | light beam | Neon cylinder/Beam (1.0, 0.0, -12.6) -> (1.0, 28.0, -12.6), width 1.4->0.0 over 0.47s, Transparency 0.50->1. |
| 4.37s | 262 | particles (spark) | ParticleEmitter at (1.0, 0.3, -12.6): 60, Speed 18-54, Lifetime 0.40-0.93s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 4.37s | 262 | particles (smoke) | ParticleEmitter at (1.0, 0.3, -12.6): 70, Speed 12-33, Lifetime 0.50-1.17s, Acceleration Y -14 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.55->0.00. |
| 4.37s | 262 | camera shake | magnitude 2.2, roughness 10, fade 0.37s (RbxCameraShaker-style, rotation + offset) |
| 4.37s | 262 | FOV punch | -12% FOV (~8 deg) in 4 frames, recover over 0.17s (Back Out) |
| 4.37s | 262 | screen flash | ColorCorrection Brightness +0.25, TintColor #ffffff for 0.07s |
| 4.42s | 265 | shockwave ring | flat Neon ring MeshPart/cylinder at (1.0, 0.1, -12.6), radius 0.6->10.0 in 0.43s (Tween Quart/Expo Out), Transparency 0.40->1, thickness 0.8->0.10. Stagger repeated rings by 0.1 s. |
| 5.57s | 334 | ground/wall cracks | Decal or thin dark Parts radiating 7 studs (12 branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s). |
| 5.57s | 334 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.5, 0.1, -14.2), radius 0.5->13.0 in 0.37s (Tween Quart/Expo Out), Transparency 0.15->1, thickness 1.1->0.15. Stagger repeated rings by 0.1 s. |
| 5.57s | 334 | dome | Neon sphere at (0.5, 0.4, -14.2), size 1.2->10.0 in 0.20s, Transparency 0.85->1 (keep >= 0.85: lower values look solid on bright skies). |
| 5.57s | 334 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.20s, Size 0.6->6.3 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 12 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.5, 0.8, -14.2). |
| 5.57s | 334 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.25s, Size 0.6->6.3. |
| 5.57s | 334 | particles (spark) | ParticleEmitter at (0.5, 0.4, -14.2): 40, Speed 12-42, Lifetime 0.23-0.57s, Acceleration Y -50 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 5.57s | 334 | particles (smoke) | ParticleEmitter at (0.5, 0.3, -14.2): 40, Speed 7-24, Lifetime 0.40-0.83s, Acceleration Y -14 Drag 3, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.50->0.00. |
| 5.57s | 334 | camera shake | magnitude 2.0, roughness 10, fade 0.33s (RbxCameraShaker-style, rotation + offset) |
| 5.57s | 334 | FOV punch | -12% FOV (~8 deg) in 4 frames, recover over 0.15s (Back Out) |
| 5.57s | 334 | screen flash | ColorCorrection Brightness +0.25, TintColor #ffffff for 0.07s |
| 5.67s | 340 | ground streak | Flat Neon part growing along the path over 0.67s (3 stacked layers wide->narrow, hottest on top); fade after. |
| 5.67s | 340 | particles (spark) | ParticleEmitter attached to character 1 Head: Rate 300/s for 1.83s, Speed 6-24, Lifetime 0.13-0.30s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 0.95->0.00. |
| 5.67s | 340 | particles (smoke) | ParticleEmitter attached to character 1 Head: Rate 84/s for 1.83s, Speed 1-6, Lifetime 0.40-0.77s, Acceleration Y 4 , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.40->0.00. |
| 5.67s | 340 | glow | PointLight Brightness 6->6, Range 5->5 + one billboard emitter (round glow, flare=0.9) for 1.83s. |
| 5.67s | 340 | trail | Trail on Torso: Lifetime 0.20s, width 1.1->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 1.83s. |
| 6.33s | 380 | ground streak | Flat Neon part growing along the path over 1.17s (3 stacked layers wide->narrow, hottest on top); fade after. |
| 6.60s | 396 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.18s, Size 0.8->8.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 10 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.7, 2.2, -24.6). |
| 6.60s | 396 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.23s, Size 0.8->8.8. |
| 6.60s | 396 | particles (spark) | ParticleEmitter at (-0.3, 2.0, -24.8): 36, Speed 12-42, Lifetime 0.23-0.57s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 6.60s | 396 | shockwave ring | flat Neon ring MeshPart/cylinder at (-0.3, 0.1, -24.8), radius 0.6->9.0 in 0.23s (Tween Quart/Expo Out), Transparency 0.40->1, thickness 1.0->0.10. Stagger repeated rings by 0.1 s. |
| 6.60s | 396 | particles (smoke) | ParticleEmitter at (-0.3, 1.0, -25.5): 44, Speed 6-27, Lifetime 0.50-1.00s, Acceleration Y -11 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.55->0.00. |
| 6.60s | 396 | camera shake | magnitude 1.6, roughness 10, fade 0.23s (RbxCameraShaker-style, rotation + offset) |
| 6.60s | 396 | screen flash | ColorCorrection Brightness +0.18, TintColor #ffffff for 0.05s |
| 7.18s | 431 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.18s, Size 0.8->8.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 10 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.7, 2.2, -38.6). |
| 7.18s | 431 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.23s, Size 0.8->8.8. |
| 7.18s | 431 | particles (spark) | ParticleEmitter at (-0.3, 2.0, -38.8): 36, Speed 12-42, Lifetime 0.23-0.57s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 7.18s | 431 | shockwave ring | flat Neon ring MeshPart/cylinder at (-0.3, 0.1, -38.8), radius 0.6->9.0 in 0.23s (Tween Quart/Expo Out), Transparency 0.40->1, thickness 1.0->0.10. Stagger repeated rings by 0.1 s. |
| 7.18s | 431 | particles (smoke) | ParticleEmitter at (-0.3, 1.0, -39.5): 44, Speed 6-27, Lifetime 0.50-1.00s, Acceleration Y -11 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.55->0.00. |
| 7.18s | 431 | camera shake | magnitude 1.6, roughness 10, fade 0.23s (RbxCameraShaker-style, rotation + offset) |
| 7.18s | 431 | screen flash | ColorCorrection Brightness +0.18, TintColor #ffffff for 0.05s |
| 7.52s | 451 | trail | Trail on Torso: Lifetime 0.20s, width 1.6->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.45s. |
| 7.97s | 478 | ground/wall cracks | Decal or thin dark Parts radiating 15 studs (18 branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s). |
| 7.97s | 478 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.0, 6.4, -88.0), radius 0.8->13.0 in 0.33s (Tween Quart/Expo Out), Transparency 0.15->1, thickness 1.3->0.20. Stagger repeated rings by 0.1 s. |
| 7.97s | 478 | dome | Neon sphere at (0.0, 6.4, -88.5), size 2.0->12.0 in 0.20s, Transparency 0.85->1 (keep >= 0.85: lower values look solid on bright skies). |
| 7.97s | 478 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.20s, Size 1.0->10.5 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 12 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.0, 6.4, -87.2). |
| 7.97s | 478 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.25s, Size 1.0->10.5. |
| 7.97s | 478 | particles (spark) | ParticleEmitter at (0.0, 6.4, -87.4): 50, Speed 15-48, Lifetime 0.23-0.60s, Acceleration Y -43 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 7.97s | 478 | particles (smoke) | ParticleEmitter at (0.0, 6.4, -87.5): 60, Speed 6-24, Lifetime 0.50-1.17s, Acceleration Y -11 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.55->0.00. |
| 7.97s | 478 | camera shake | magnitude 3.6, roughness 10, fade 0.53s (RbxCameraShaker-style, rotation + offset) |
| 7.97s | 478 | FOV punch | -10% FOV (~7 deg) in 4 frames, recover over 0.17s (Back Out) |
| 7.97s | 478 | screen flash | ColorCorrection Brightness +0.35, TintColor #ffffff for 0.07s |
| 7.98s | 479 | lightning | Chain of 9 Beams (FaceCamera false, shared Attachments), width 0.10, jitter 0.9; re-roll the offsets every 0.05 s from 7.98s to 8.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 7.98s | 479 | lightning | Chain of 9 Beams (FaceCamera false, shared Attachments), width 0.10, jitter 0.9; re-roll the offsets every 0.05 s from 7.98s to 8.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 7.98s | 479 | lightning | Chain of 9 Beams (FaceCamera false, shared Attachments), width 0.10, jitter 0.9; re-roll the offsets every 0.05 s from 7.98s to 8.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 7.98s | 479 | lightning | Chain of 9 Beams (FaceCamera false, shared Attachments), width 0.10, jitter 0.9; re-roll the offsets every 0.05 s from 7.98s to 8.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 7.98s | 479 | lightning | Chain of 9 Beams (FaceCamera false, shared Attachments), width 0.10, jitter 0.9; re-roll the offsets every 0.05 s from 7.98s to 8.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 8.68s | 521 | ground/wall cracks | Decal or thin dark Parts radiating 10 studs (14 branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s). |
| 8.68s | 521 | glow | PointLight Brightness 2->8, Range 2->16 + one billboard emitter (round glow, flare=1.6) for 0.58s. |
| 8.68s | 521 | particles (flame) | ParticleEmitter at (-1.0, 0.8, -55.0): Rate 108/s for 0.58s, Speed 3-11, Lifetime 0.43-0.83s, Acceleration Y 14 , flipbook `fire` (Grid8x8, 24 fps) or 3 stacked emitters, LightEmission 1. Alpha NumberSequence 0.70->0.00. |
| 8.75s | 525 | particles (spark) | ParticleEmitter attached to character 0 Right Arm: Rate 210/s for 0.52s, Speed 0-0, Lifetime 0.43-0.43s, , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+; ShapeInOut Inward, ShapeStyle Volume radius 5.5. Alpha NumberSequence 0.00->1.00. |
| 8.78s | 527 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 8.78s to 8.85s; branch chance 0.20. Colour #ff6a2a, core white. |
| 8.83s | 530 | shockwave ring | flat Neon ring MeshPart/cylinder at (-1.0, 0.1, -55.0), radius 0.6->8.0 in 0.37s (Tween Quart/Expo Out), Transparency 0.50->1, thickness 0.8->0.15. Stagger repeated rings by 0.1 s. |
| 8.92s | 535 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 8.92s to 8.98s; branch chance 0.20. Colour #ff6a2a, core white. |
| 8.92s | 535 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 8.92s to 8.98s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.00s | 540 | light beam | Neon cylinder/Beam (-1.0, 0.0, -55.0) -> (-1.0, 34.0, -55.0), width 1.8->0.0 over 0.40s, Transparency 0.78->1. |
| 9.03s | 542 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.03s to 9.10s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.03s | 542 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.03s to 9.10s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.07s | 544 | shockwave ring | flat Neon ring MeshPart/cylinder at (-1.0, 0.1, -55.0), radius 0.6->12.0 in 0.37s (Tween Quart/Expo Out), Transparency 0.50->1, thickness 0.8->0.15. Stagger repeated rings by 0.1 s. |
| 9.13s | 548 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.13s to 9.20s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.13s | 548 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.13s to 9.20s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.22s | 553 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.22s to 9.28s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.22s | 553 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.22s to 9.28s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.22s | 553 | lightning | Chain of 8 Beams (FaceCamera false, shared Attachments), width 0.08, jitter 0.7; re-roll the offsets every 0.05 s from 9.22s to 9.28s; branch chance 0.20. Colour #ff6a2a, core white. |
| 9.23s | 554 | shockwave ring | flat Neon ring MeshPart/cylinder at (-1.0, 0.1, -55.0), radius 0.6->16.0 in 0.37s (Tween Quart/Expo Out), Transparency 0.50->1, thickness 0.8->0.15. Stagger repeated rings by 0.1 s. |
| 9.28s | 557 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.13s, Size 0.8->7.1 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 10 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (-1.0, 0.6, -55.0). |
| 9.28s | 557 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.18s, Size 0.8->7.1. |
| 9.28s | 557 | trail | Trail on Torso: Lifetime 0.17s, width 1.6->0.2, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 9.28s | 557 | trail | Trail on Right Arm: Lifetime 0.17s, width 1.0->0.1, FaceCamera false, LightEmission 1, Transparency 0->1; enabled 0.13s. |
| 9.28s | 557 | shockwave ring | flat Neon ring MeshPart/cylinder at (-1.0, 0.1, -55.0), radius 0.6->20.0 in 0.30s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 1.2->0.10. Stagger repeated rings by 0.1 s. |
| 9.28s | 557 | particles (soft) | ParticleEmitter at (-1.0, 0.5, -55.0): 60, Speed 12-36, Lifetime 0.33-0.83s, Acceleration Y -14 Drag 3, round glow texture, LightEmission 0.5-1. Alpha NumberSequence 0.50->0.00. |
| 9.28s | 557 | FOV punch | -10% FOV (~7 deg) in 4 frames, recover over 0.10s (Back Out) |
| 9.30s | 558 | light beam | Neon cylinder/Beam (-1.0, 2.4, -55.0) -> (0.0, 5.0, -88.0), width 2.2->0.0 over 0.40s, Transparency 0.20->1. |
| 9.38s | 563 | slash crescent | Trail between two Attachments at radius 8.1/9.9 on an invisible part spinning 180 deg in 0.20s (Quart Out), FaceCamera false, width taper to 0; or flipbook `slash`. Core Brightness 10-15. |
| 9.40s | 564 | dome | Neon sphere at (0.0, 5.0, -88.0), size 2.0->40.0 in 0.37s, Transparency 0.85->1 (keep >= 0.85: lower values look solid on bright skies). |
| 9.40s | 564 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.23s, Size 1.3->11.8 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 18 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.0, 5.0, -86.5). |
| 9.40s | 564 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.28s, Size 1.3->11.8. |
| 9.40s | 564 | glow | PointLight Brightness 6->0, Range 14->7 + one billboard emitter (round glow, flare=2.0) for 0.67s. |
| 9.40s | 564 | shockwave ring | upright Neon ring MeshPart/cylinder at (0.0, 5.0, -88.0), radius 1.0->30.0 in 0.50s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 1.6->0.20. Stagger repeated rings by 0.1 s. |
| 9.40s | 564 | light beam | Neon cylinder/Beam (0.0, 5.0, -48.0) -> (0.0, 5.0, -148.0), width 2.2->0.0 over 0.50s, Transparency 0.45->1. |
| 9.40s | 564 | particles (smoke) | ParticleEmitter at (0.0, 5.0, -89.0): 70, Speed 12-66, Lifetime 0.83-1.83s, Acceleration Y -14 Drag 2, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.40->0.00. |
| 9.40s | 564 | particles (spark) | ParticleEmitter at (0.0, 5.0, -88.0): 160, Speed 18-78, Lifetime 0.23-0.73s, Acceleration Y -36 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 0.95->0.00. |
| 9.40s | 564 | particles (shard) | ParticleEmitter at (0.0, 5.0, -88.0): 60, Speed 12-54, Lifetime 0.50-1.17s, Acceleration Y -54 , dark rock-chip texture, LightEmission 0, spinning (RotSpeed +-300). Alpha NumberSequence 1.00->1.00. |
| 9.40s | 564 | camera shake | magnitude 6.4, roughness 10, fade 1.00s (RbxCameraShaker-style, rotation + offset) |
| 9.40s | 564 | FOV punch | -20% FOV (~14 deg) in 4 frames, recover over 0.23s (Back Out) |
| 9.40s | 564 | screen flash | ColorCorrection Brightness +0.50, TintColor #ffffff for 0.05s |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.42s | 565 | lightning | Chain of 11 Beams (FaceCamera false, shared Attachments), width 0.14, jitter 1.4; re-roll the offsets every 0.05 s from 9.42s to 9.55s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.45s | 567 | hit star | ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~30), Rate 0, EmitCount 1, Lifetime 0.20s, Size 1.0->7.6 (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); 10 radial streaks = second emitter VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At (0.0, 5.0, -86.5). |
| 9.45s | 567 | flipbook impact_star | ParticleEmitter flipbook `impact_star`, Rate 0, EmitCount 1, Lifetime 0.25s, Size 1.0->7.6. |
| 9.45s | 567 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.0, 0.1, -88.0), radius 1.0->40.0 in 0.50s (Tween Quart/Expo Out), Transparency 0.20->1, thickness 2.0->0.20. Stagger repeated rings by 0.1 s. |
| 9.45s | 567 | screen flash | ColorCorrection Brightness +0.22, TintColor #ffd9a8 for 0.23s |
| 9.50s | 570 | particles (smoke) | ParticleEmitter at (0.0, 6.0, -96.0): Rate 30/s for 0.73s, Speed 2-7, Lifetime 1.17-2.17s, , flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.18->0.00. |
| 9.50s | 570 | particles (spark) | ParticleEmitter at (0.0, 8.0, -94.0): Rate 84/s for 2.83s, Speed 1-5, Lifetime 1.50-3.33s, Acceleration Y 2 , Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+. Alpha NumberSequence 1.00->0.00. |
| 9.63s | 578 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 9.63s to 9.68s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.73s | 584 | glow | PointLight Brightness 2->1, Range 19->16 + one billboard emitter (round glow, flare=0.0) for 1.93s. |
| 9.83s | 590 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 9.83s to 9.88s; branch chance 0.30. Colour #ffb43a, core white. |
| 9.87s | 592 | shockwave ring | flat Neon ring MeshPart/cylinder at (0.0, 0.1, -125.7), radius 0.6->12.0 in 0.43s (Tween Quart/Expo Out), Transparency 0.40->1, thickness 1.0->0.10. Stagger repeated rings by 0.1 s. |
| 9.87s | 592 | particles (smoke) | ParticleEmitter at (0.0, 0.4, -123.7): Rate 360/s for 0.23s, Speed 6-21, Lifetime 0.50-1.17s, Acceleration Y -11 Drag 3, flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1. Alpha NumberSequence 0.50->0.00. |
| 9.87s | 592 | camera shake | magnitude 2.0, roughness 10, fade 0.23s (RbxCameraShaker-style, rotation + offset) |
| 9.93s | 596 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 9.93s to 9.98s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.08s | 605 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.08s to 10.13s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.32s | 619 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.32s to 10.37s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.40s | 624 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.40s to 10.45s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.53s | 632 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.53s to 10.58s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.70s | 642 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.70s to 10.75s; branch chance 0.30. Colour #ffb43a, core white. |
| 10.92s | 655 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 10.92s to 10.97s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.03s | 662 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.03s to 11.08s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.20s | 672 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.20s to 11.25s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.28s | 677 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.28s to 11.33s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.48s | 689 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.48s to 11.53s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.60s | 696 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.60s to 11.65s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.77s | 706 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.77s to 11.82s; branch chance 0.30. Colour #ffb43a, core white. |
| 11.90s | 714 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 11.90s to 11.95s; branch chance 0.30. Colour #ffb43a, core white. |
| 12.05s | 723 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 12.05s to 12.10s; branch chance 0.30. Colour #ffb43a, core white. |
| 12.27s | 736 | lightning | Chain of 7 Beams (FaceCamera false, shared Attachments), width 0.07, jitter 0.6; re-roll the offsets every 0.05 s from 12.27s to 12.32s; branch chance 0.30. Colour #ffb43a, core white. |
