"""VFX cue sheet: translate a Cinematic into Roblox-primitive implementation notes, sorted by time.

The viewer only imitates Roblox primitives; this module says how each fx would be built in Roblox with
numbers converted to Roblox units (seconds, studs/s). Recipes come from docs/research/github-survey.md; the
parameters are **starting points to tune in game**, not measurements of any game.
"""

from __future__ import annotations

from .cinematic import Cinematic

FPS = 60


def _s(frames: float, fps: int = FPS) -> str:
    return f"{frames / fps:.2f}s"


def _v(c) -> str:
    return "(" + ", ".join(f"{x:.1f}" for x in c) + ")"


def describe(e: dict, fps: int = FPS) -> tuple[int, str, str]:
    """(start frame, effect name, Roblox implementation) for one fx entry."""
    t = e["type"]
    if t == "burst":
        d = e["dur"] / fps
        return e["t0"], "hit star", (
            f"ParticleEmitter, flipbook `impact_star` (Grid4x4, FlipbookFramerate ~{min(30, int(8 / max(d, 0.05)))}), Rate 0, EmitCount 1, "
            f"Lifetime {d:.2f}s, Size {e['r0'] * 1.6:.1f}->{e['r1'] * 2.1:.1f} (NumberSequence, fast ease-out), LightEmission 0.6, ZOffset 2; "
            f"dark twin behind it (Color black, LightEmission 0, ZOffset 1, Transparency 0.4->1); {e['streaks']} radial streaks = second emitter "
            f"VelocityParallel, Speed 60-160, Drag 10, Squash 3->1. At {_v(e['c'])}.")
    if t == "sprite":
        return e["t0"], f"flipbook {e['sheet']}", (
            f"ParticleEmitter flipbook `{e['sheet']}`, Rate 0, EmitCount 1, Lifetime {e['dur'] / fps:.2f}s, Size {e['size0']:.1f}->{e['size1']:.1f}.")
    if t == "emit":
        shape = e.get("shape", "soft")
        n = e["burst"] if e["burst"] else f"Rate {e['rate'] * fps:.0f}/s for {_s(e['t1'] - e['t0'], fps)}"
        speed = f"Speed {e['vel'][0] * fps:.0f}-{e['vel'][1] * fps:.0f}"
        life = f"Lifetime {e['life'][0] / fps:.2f}-{e['life'][1] / fps:.2f}s"
        acc = f"Acceleration Y {-e['grav'] * fps * fps:.0f}" if e["grav"] else ""
        drag = f"Drag {e['drag'] * fps:.0f}" if e["drag"] else ""
        look = {"spark": "Orientation VelocityParallel, Squash > 0, LightEmission 1, Brightness 2+",
                "flame": "flipbook `fire` (Grid8x8, 24 fps) or 3 stacked emitters, LightEmission 1",
                "smoke": "flipbook `smoke` (Grid8x8, ~15 fps, OneShot), LightEmission 0, Transparency 0.5->1",
                "shard": "dark rock-chip texture, LightEmission 0, spinning (RotSpeed +-300)",
                "soft": "round glow texture, LightEmission 0.5-1"}.get(shape, "")
        place = f"attached to character {e['attach']['char']} {e['attach']['part']}" if e.get("attach") else f"at {_v(e['origin'])}"
        conv = f"; ShapeInOut Inward, ShapeStyle Volume radius {e['converge']:.1f}" if e.get("converge") else ""
        return e["t0"], f"particles ({shape})", f"ParticleEmitter {place}: {n}, {speed}, {life}, {acc} {drag}, {look}{conv}. Alpha NumberSequence {e['alpha'][0]:.2f}->{e['alpha'][1]:.2f}.".replace("  ", " ")
    if t == "ring":
        flat = abs(e["n"][1]) > 0.9
        return e["t0"], "shockwave ring", (
            f"{'flat' if flat else 'upright'} Neon ring MeshPart/cylinder at {_v(e['c'])}, radius {e['r0']:.1f}->{e['r1']:.1f} in {_s(e['dur'], fps)} "
            f"(Tween Quart/Expo Out), Transparency {1 - e['a0']:.2f}->1, thickness {e['w0']:.1f}->{e['w1']:.2f}. Stagger repeated rings by 0.1 s.")
    if t == "dome":
        return e["t0"], "dome", (
            f"Neon sphere at {_v(e['c'])}, size {2 * e['r0']:.1f}->{2 * e['r1']:.1f} in {_s(e['dur'], fps)}, Transparency {max(0.85, 1 - e['a0']):.2f}->1 "
            "(keep >= 0.85: lower values look solid on bright skies).")
    if t == "line":
        return e["t0"], "light beam", (
            f"Neon cylinder/Beam {_v(e['a'])} -> {_v(e['b'])}, width {e['w0']:.1f}->{e['w1']:.1f} over {_s(e['dur'], fps)}, Transparency {1 - e['a0']:.2f}->1.")
    if t == "bolt":
        return e["t0"], "lightning", (
            f"Chain of {e['segs']} Beams (FaceCamera false, shared Attachments), width {e['w']:.2f}, jitter {e['jitter']:.1f}; re-roll the offsets every "
            f"0.05 s from {_s(e['t0'], fps)} to {_s(e['t1'], fps)}; branch chance {e['branch']:.2f}. Colour {e['color']}, core white.")
    if t == "slash":
        return e["t0"], "slash crescent", (
            f"Trail between two Attachments at radius {e['r'] - e['w'] / 2:.1f}/{e['r'] + e['w'] / 2:.1f} on an invisible part spinning {abs(e['a1'] - e['a0']):.0f} deg "
            f"in {_s(e['dur'], fps)} (Quart Out), FaceCamera false, width taper to 0; or flipbook `slash`. Core Brightness 10-15.")
    if t == "glow":
        return e["t0"], "glow", (
            f"PointLight Brightness {e['a0'] * 8:.0f}->{e['a1'] * 8:.0f}, Range {e['r0'] * 6:.0f}->{e['r1'] * 6:.0f} + one billboard emitter (round glow, "
            f"flare={e['flare']:.1f}) for {_s(e['t1'] - e['t0'], fps)}.")
    if t == "trail":
        return e["t0"], "trail", (
            f"Trail on {e['part']}: Lifetime {e['len'] / fps:.2f}s, width {e['w0']:.1f}->{e['w1']:.1f}, FaceCamera false, LightEmission 1, "
            f"Transparency 0->1; enabled {_s(e['t1'] - e['t0'], fps)}.")
    if t == "strip":
        return e["t0"], "ground streak", (
            f"Flat Neon part growing along the path over {_s(e['dur'], fps)} ({len(e['layers'])} stacked layers wide->narrow, hottest on top); fade after.")
    if t == "cracks":
        return e["t0"], "ground/wall cracks", (
            f"Decal or thin dark Parts radiating {e['len']:.0f} studs ({e['branches']} branches) + molten core Part (Neon, Color3 > 1 cooling to black over ~1.3 s).")
    return e.get("t0", 0), t, "see Cinematic"


def cue_sheet(cine: Cinematic, fps: int = FPS) -> str:
    rows = [describe(e, fps) for e in cine.fx]
    rows += [(f0, "camera shake", f"magnitude {amp * 4:.1f}, roughness 10, fade {_s(dur, fps)} (RbxCameraShaker-style, rotation + offset)") for f0, dur, amp in cine.shakes]
    rows += [(f0, "FOV punch", f"-{amt * 100:.0f}% FOV (~{amt * 70:.0f} deg) in 4 frames, recover over {_s(dur, fps)} (Back Out)") for f0, dur, amt in cine.kicks]
    rows += [(int(f["t0"]), "screen flash", f"ColorCorrection Brightness +{f['peak']:.2f}, TintColor {f['color']} for {_s(f['dur'], fps)}") for f in cine.flashes]
    rows.sort(key=lambda r: r[0])
    out = ["# VFX cue sheet (starting values, tune in game)\n", "| time | frame | effect | Roblox implementation |", "|---|---|---|---|"]
    for f, name, text in rows:
        out.append(f"| {f / fps:.2f}s | {f} | {name} | {text} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- hit events
# Starting values for the Roblox runtime, from MIT sources (see docs/research/github-survey.md):
#   Willikk/Roblox (CameraShaker, Hitstop, ScreenFlash) and zriptic/roclicks-skills (vfx-camera-world).
TRAUMA = {"light": 0.10, "heavy": 0.30, "slam": 0.50, "ultimate": 0.80}  # jab 0.08-0.12, heavy 0.25-0.35, slam 0.4-0.6, ultimate 0.8
FOV_PUNCH_DEG = {"light": 3.0, "heavy": 5.0, "slam": 6.0, "ultimate": 7.0}  # hit punch 5-7 deg over 4 frames, Back Out
HITSTOP_S = {"light": 0.05, "heavy": 0.10, "slam": 0.12, "ultimate": 0.14}  # per-fighter AnimationTrack speed freeze; OPTIONAL
SCREEN_FLASH = {"duration": 0.18, "contrast": 0.2, "bloom": 1.2, "blur": 6}  # ScreenFlash.impact defaults
CAMERA_SHAKER = {  # Willikk CameraShaker.settings
    "maxAnglesDeg": (2.2, 2.2, 3.5), "maxOffsetStuds": (0.25, 0.25, 0.1), "frequencyHz": 16, "traumaDecayPerS": 1.3, "exponent": 2,
    "applyAt": "RenderPriority.Camera + 1", "undoAt": "RenderPriority.Camera - 1",
}


def hit_event(frame: int, kind: str, name: str, seed: int, pos, attacker: str = "attacker", victim: str = "victim", fps: int = FPS) -> dict:
    """One hit as game data: what the runtime needs to react (camera, VFX seed, optional per-fighter hit-stop)."""
    return {
        "frame": frame, "time_s": round(frame / fps, 4), "name": name, "class": kind, "attacker": attacker, "victim": victim,
        "pos": [round(float(x), 3) for x in pos], "seed": seed % 65536,
        "camera": {"trauma": TRAUMA[kind], "fov_punch_deg": FOV_PUNCH_DEG[kind]},
        "screen_flash": SCREEN_FLASH if kind in ("slam", "ultimate") else None,
        "hitstop_s": HITSTOP_S[kind],  # null it if your game has no hit-stop (this project excludes a GLOBAL one)
        "marker": "Hit",
    }
