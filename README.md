# Roblox animation & VFX sandbox

Work in progress toward a skill + toolkit for TSB-style **R6 combat animation**.

- `tsb_engine/` – animation model, R6 forward kinematics, explicit pose helpers
  (`plant_legs`, `bake_footwork`, `gait_steps`), a **cinematic** layer (cameras, debris, particles, screen effects), a **linter** with confidence-tagged rules, JSON I/O, CLI.
- `.claude/skills/tsb-animator/` – the skill (workflow, principles, verified facts).
- `viewer/` + `tools/` – self-contained HTML viewer (scrub, slow-mo, cameras, fist trail) and frame/contact-sheet renderers (`python tools/build_viewer.py`).
- `tsb_engine/roblox_export.py` – R6 animation -> KeyframeSequence `.rbxmx` + Luau builder (pose mapping tested against Roblox's forward kinematics); `tsb_engine/textures.py` – procedural flipbook baker (`python -m tsb_engine.textures assets/flipbooks`); `tsb_engine/roblox_cues.py` – VFX cue sheet in Roblox units.
- `docs/research/github-survey.md` – survey of GitHub (Roblox VFX, export, Blender, other engines) with licences and what was applied.
- `examples/` – a worked heavy punch, two bad animations used by the tests, and `ultimate.py` (a 13 s, 4-act ultimate) and `short.py` (an 11 s short at the level of a TikTok reference: ink smears, impact frames, secondary motion).
- `tsb_engine/solver.py` / `readability.py` – solve a limb onto a contact point, dislocation/chain helpers, and a numpy z-buffer that measures how readable a pose is from the shot camera (`python tools/check_poses.py duel_short 62,104`); `docs/analysis/method-comparison.md` compares the Gemini method with ours.
- `tsb_engine/eyes.py` + `tools/eyes.py` – "eyes": measure a clip (pace, holds, subject size, fx coverage, optical flow, cuts) and diff a render against a reference video with a numbered diagnosis and ref-above-mine pictures (`pip install -r requirements-eyes.txt`).
- `tsb_engine/secondary.py` – verlet hair / coat tails / hat for the preview; `docs/research/reference-analysis.md` – the reference study.
- `docs/gemini/` – raw export of the source conversation; `docs/analysis/` – analysis of it;
  `docs/research/` – research on TSB's animators.

```bash
python -m unittest discover -s tests          # 71 tests, no dependencies (~30 s)
python tools/build_viewer.py berserker_ultimate   # then open viewer/output/berserker_ultimate.html
python tools/build_viewer.py duel_short           # the 11 s short
python -m tsb_engine lint examples/heavy_punch.json
python -m tsb_engine lint examples/robotic_punch.json --json
```

Status: no Roblox export yet (`KeyframeSequence`/`.rbxmx` not implemented), no VFX tooling,
thresholds are starting heuristics to calibrate on animations you consider good.
