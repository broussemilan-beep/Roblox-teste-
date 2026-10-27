# Roblox animation & VFX sandbox

Work in progress toward a skill + toolkit for TSB-style **R6 combat animation**.

- `tsb_engine/` – animation model, R6 forward kinematics, explicit pose helpers
  (`plant_legs`, `bake_planted_legs`), a **linter** with confidence-tagged rules, JSON I/O, CLI.
- `.claude/skills/tsb-animator/` – the skill (workflow, principles, verified facts).
- `viewer/` + `tools/` – self-contained HTML viewer (scrub, slow-mo, cameras, fist trail) and frame/contact-sheet renderers (`python tools/build_viewer.py`).
- `examples/` – a worked heavy punch and two bad animations used by the tests.
- `docs/gemini/` – raw export of the source conversation; `docs/analysis/` – analysis of it;
  `docs/research/` – research on TSB's animators.

```bash
python -m unittest discover -s tests          # 28 tests, no dependencies
python -m tsb_engine lint examples/heavy_punch.json
python -m tsb_engine lint examples/robotic_punch.json --json
```

Status: no Roblox export yet (`KeyframeSequence`/`.rbxmx` not implemented), no VFX tooling,
thresholds are starting heuristics to calibrate on animations you consider good.
