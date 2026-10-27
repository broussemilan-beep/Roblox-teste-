# VFX layering notes (reference only — no tooling yet)

Distilled from the analysed conversation; same tags as `principles.md`. Check the project
constraints first: the user's viewer imitates Roblox primitives (MeshPart + TextureID,
ParticleEmitter + flipbook, Beam, Trail, PointLight, ColorCorrection) with **no custom
shaders, no global hitstop and no impact frames**.

- **Layer by role.** A dark non-emissive underlay (`LightEmission = 0`, negative `ZOffset`) so
  bright additive layers stay readable on light maps; a coloured body; a small white core.
  [heuristic]
- **Different lifetimes per layer** (flash shortest, smoke longest) instead of everything
  dying together. [heuristic]
- **Expansion: fast pop then braking**, not linear growth. Dissolve by thinning an axis as
  well as fading. [heuristic]
- **Readable fights.** Keep the area around the fighters clear (ring/crown rather than a solid
  blob), keep heavy smoke low, make charge effects hug the limb that will strike, make
  hit-confirm look different from a whiff. [heuristic]
- **Texture "matter".** The user's complaint was flat white blobs: bake eroded, multi-tone
  flipbooks (noise + hard threshold + constant colour ramp) in Blender, with
  `view_transform = 'Standard'`, instead of drawing flat shapes in code. [heuristic]
- **Layer counts** quoted in the conversation (26 vs 205, 60/25/15 colour split) are the
  user's/Gemini's rough metrics, not standards. [unverified]
- Ideas that need engine support the user may not have: impact frames (Highlight + 
  ColorCorrection), contrast drop, global hitstop. Ask before using.
