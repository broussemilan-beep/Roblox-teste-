"""Read BVH motion capture (CMU Graphics Lab database layout), run its forward kinematics and retarget it to the engine's R6 rig.

CMU: "places no restrictions on the use of the original dataset" (the BVH conversion by Bruce Hahne adds none either); the raw data must not be re-sold, so it is never
copied into this repository: only the derived R6 angles of the clips actually used are stored (``docs/research/reference-poses``).

R6 has rigid, elbow-less limbs, so each human limb collapses to ONE direction (shoulder -> wrist, hip -> ankle) expressed in the chest / pelvis frame; the torso is the
chest frame; the head is its own orientation relative to the chest.  Twist about a limb's own axis is dropped.

Convention: BVH Y up, Z forward (CMU), engine Y up.  Everything is computed in a body frame, so the world heading becomes the root yaw ``ry`` of ``root_pose``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Bvh:
    names: list[str]
    parent: list[int]
    offset: np.ndarray          # (J, 3)
    channels: list[list[str]]   # per joint
    data: np.ndarray            # (F, C)
    dt: float
    slices: list[tuple[int, int]]   # per joint: column range in ``data``

    @property
    def fps(self) -> float:
        return 1.0 / self.dt

    def index(self, name: str) -> int:
        return self.names.index(name)


def parse(path: str | Path) -> Bvh:
    text = Path(path).read_text().replace("\r", "")
    head, motion = text.split("MOTION", 1)
    names, parent, offset, chans = [], [], [], []
    stack: list[int] = []
    cur = -1
    toks = re.findall(r"[^\s{}]+|[{}]", head)
    i = 0
    pending_end = False
    while i < len(toks):
        t = toks[i]
        if t in ("ROOT", "JOINT"):
            names.append(toks[i + 1])
            parent.append(stack[-1] if stack else -1)
            offset.append([0, 0, 0])
            chans.append([])
            cur = len(names) - 1
            i += 2
        elif t == "End":
            pending_end = True
            i += 2
        elif t == "{":
            if not pending_end:
                stack.append(cur)
            i += 1
        elif t == "}":
            if pending_end:
                pending_end = False
            else:
                stack.pop()
                cur = stack[-1] if stack else -1
            i += 1
        elif t == "OFFSET":
            if not pending_end:
                offset[cur] = [float(toks[i + 1]), float(toks[i + 2]), float(toks[i + 3])]
            i += 4
        elif t == "CHANNELS":
            n = int(toks[i + 1])
            chans[cur] = toks[i + 2 : i + 2 + n]
            i += 2 + n
        else:
            i += 1
    lines = [l for l in motion.strip().split("\n") if l.strip()]
    nf = int(lines[0].split(":")[1])
    dt = float(lines[1].split(":")[1])
    data = np.array([[float(v) for v in l.split()] for l in lines[2 : 2 + nf]], float)
    slices, c = [], 0
    for ch in chans:
        slices.append((c, c + len(ch)))
        c += len(ch)
    return Bvh(names, parent, np.array(offset, float), chans, data, dt, slices)


def _rot(axis: str, deg: np.ndarray) -> np.ndarray:
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    if axis == "X":
        m = [[o, z, z], [z, c, -s], [z, s, c]]
    elif axis == "Y":
        m = [[c, z, s], [z, o, z], [-s, z, c]]
    else:
        m = [[c, -s, z], [s, c, z], [z, z, o]]
    return np.moveaxis(np.array(m), (0, 1), (-2, -1))


def fk(b: Bvh) -> tuple[np.ndarray, np.ndarray]:
    """World positions (F, J, 3) and world rotation matrices (F, J, 3, 3) of every joint."""
    F, J = b.data.shape[0], len(b.names)
    pos = np.zeros((F, J, 3))
    rot = np.zeros((F, J, 3, 3))
    for j in range(J):
        a, e = b.slices[j]
        ch = b.channels[j]
        loc = np.zeros((F, 3))
        R = np.broadcast_to(np.eye(3), (F, 3, 3)).copy()
        # positions
        for k, name in enumerate(ch):
            if name.endswith("position"):
                loc[:, "XYZ".index(name[0])] = b.data[:, a + k]
        for k, name in enumerate(ch):
            if name.endswith("rotation"):
                R = R @ _rot(name[0], b.data[:, a + k])
        p = b.parent[j]
        if p < 0:
            pos[:, j] = loc + b.offset[j]
            rot[:, j] = R
        else:
            pos[:, j] = pos[:, p] + np.einsum("fij,j->fi", rot[:, p], b.offset[j] + 0.0) + 0.0
            rot[:, j] = rot[:, p] @ R
    return pos, rot


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# retargeting to the engine's R6 rig

def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


_K = np.diag([-1.0, 1.0, -1.0])   # CMU world (character faces +Z, its left is +X) -> engine world (character faces -Z, its right is +X): a half turn about Y
NAMES16 = ["ry", "rx", "rz", "T_rx", "T_ry", "T_rz", "H_rx", "H_ry", "RA_rx", "RA_rz", "LA_rx", "LA_rz", "RL_rx", "RL_rz", "LL_rx", "LL_rz"]


@dataclass
class Clip:
    """A retargeted clip at the capture rate: the 16 R6 joint angles (degrees, order of ``NAMES16``), the root's horizontal path in studs and its height above the floor."""

    ang: np.ndarray       # (F, 16)
    xz: np.ndarray        # (F, 2) hip-centre path in studs (engine world)
    air: np.ndarray       # (F,)  height of the lowest foot above the clip's floor, studs
    fps: float
    name: str = ""

    def __len__(self) -> int:
        return len(self.ang)


def _unwrap_deg(a: np.ndarray) -> np.ndarray:
    return np.degrees(np.unwrap(np.radians(a), axis=0))


def _limb_angles(d: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(rx, rz) in degrees of an R6 limb (pose rotation (rx, 0, rz), rest direction (0, -1, 0)) whose axis points along ``d`` (F, 3) in torso-local coordinates."""
    d = _unit(d)
    g = np.arcsin(np.clip(d[:, 0], -1, 1))                       # rz: out to the side
    a = np.arctan2(-d[:, 2], -d[:, 1])                            # rx: forward (positive) / back
    return _unwrap_deg(np.degrees(a)), np.degrees(g)


def retarget(b: Bvh, pos: np.ndarray, rot: np.ndarray, leg_scale: float | None = None, name: str = "") -> Clip:
    ix = {n: i for i, n in enumerate(b.names)}
    P = pos @ _K.T                                                # engine world
    Rm = np.einsum("ij,fnjk,lk->fnil", _K, rot, _K)                 # world rotation of every joint, engine world (conjugated by the half turn)
    hips = (P[:, ix["LeftUpLeg"]] + P[:, ix["RightUpLeg"]]) / 2
    up = _unit(P[:, ix["Neck"]] - hips)
    lat = _unit(P[:, ix["RightArm"]] - P[:, ix["LeftArm"]])
    back = _unit(np.cross(lat, up))
    lat = _unit(np.cross(up, back))
    Mt = np.stack([lat, up, back], axis=-1)                       # torso -> world, columns = local x (right), y (up), z (back)
    rx = np.degrees(np.arcsin(np.clip(-Mt[:, 1, 2], -1, 1)))
    ry = _unwrap_deg(np.degrees(np.arctan2(Mt[:, 0, 2], Mt[:, 2, 2])))
    rz = np.degrees(np.arctan2(Mt[:, 1, 0], Mt[:, 1, 1]))
    inv = np.swapaxes(Mt, -1, -2)
    loc = lambda v: np.einsum("fij,fj->fi", inv, v)               # world vector -> torso-local
    leg_len = np.linalg.norm(P[:, ix["RightFoot"]] - P[:, ix["RightUpLeg"]], axis=1).max()
    s = (2.0 / leg_len) if leg_scale is None else leg_scale      # horizontal scale that keeps an R6 foot planted when the human foot is planted
    ra_rx, ra_rz = _limb_angles(loc(P[:, ix["RightHand"]] - P[:, ix["RightArm"]]))
    la_rx, la_rz = _limb_angles(loc(P[:, ix["LeftHand"]] - P[:, ix["LeftArm"]]))
    def leg(side: str) -> np.ndarray:
        """R6 legs cannot bend: keep the height the human hip really has above the ankle by tilting the rigid leg more (a crouch becomes a splayed stance)."""
        hip, knee, ank = P[:, ix[side + "UpLeg"]], P[:, ix[side + "Leg"]], P[:, ix[side + "Foot"]]
        drop = (hip[:, 1] - ank[:, 1]) * s                                    # vertical drop hip -> ankle, in studs
        cos_t = np.clip(drop / 2.0, -1.0, 1.0)
        sin_t = np.sqrt(1.0 - cos_t ** 2)
        h = (ank - hip)[:, [0, 2]] + 0.6 * (knee - hip)[:, [0, 2]]            # which way the leg leans: the foot, and where the knee points
        hn = np.linalg.norm(h, axis=1, keepdims=True)
        fwd_h = -back[:, [0, 2]]
        h = np.where(hn > 1e-6, h / np.maximum(hn, 1e-9), fwd_h / np.maximum(np.linalg.norm(fwd_h, axis=1, keepdims=True), 1e-9))
        return np.stack([sin_t * h[:, 0], -cos_t, sin_t * h[:, 1]], 1)

    rl_rx, rl_rz = _limb_angles(loc(leg("Right")))
    ll_rx, ll_rz = _limb_angles(loc(leg("Left")))
    # head: its own forward (CMU +Z at rest -> engine -Z) and up, in torso-local coordinates
    Rh = Rm[:, ix["Head"]]
    f_loc = loc(np.einsum("fij,j->fi", Rh, np.array([0.0, 0.0, -1.0])))
    h_ry = np.degrees(np.arctan2(-f_loc[:, 0], -f_loc[:, 2]))
    h_rx = np.degrees(np.arcsin(np.clip(f_loc[:, 1], -1, 1)))
    ang = np.zeros((len(P), 16))
    ang[:, 0], ang[:, 1], ang[:, 2] = ry, rx, rz
    ang[:, 6], ang[:, 7] = h_rx, np.clip(h_ry, -70, 70)
    ang[:, 8], ang[:, 9], ang[:, 10], ang[:, 11] = ra_rx, ra_rz, la_rx, la_rz
    ang[:, 12], ang[:, 13], ang[:, 14], ang[:, 15] = rl_rx, rl_rz, ll_rx, ll_rz
    foot_low = np.min(np.stack([P[:, ix[n], 1] for n in ("LeftFoot", "RightFoot", "LeftHand", "RightHand", "Head")], 0), axis=0)   # the lowest part: feet, or hands / head in a cartwheel or a roll
    air = np.maximum(foot_low - np.percentile(foot_low, 2), 0.0) * s
    return Clip(ang, hips[:, [0, 2]] * s, air, b.fps, name)


def segment(c: Clip, t0: float, t1: float, n: int, heading0: float | None = None) -> Clip:
    """Resample [t0, t1] seconds of a clip to ``n`` images (this is where a gesture is stretched or squeezed to the time it gets in the combo)."""
    t = np.linspace(t0 * c.fps, t1 * c.fps, n)
    i0 = np.clip(np.floor(t).astype(int), 0, len(c) - 2)
    w = (t - i0)[:, None]
    lerp = lambda a: a[i0] * (1 - w) + a[i0 + 1] * w
    ang, xz = lerp(c.ang), lerp(c.xz)
    air = (c.air[i0] * (1 - w[:, 0]) + c.air[i0 + 1] * w[:, 0])
    return Clip(ang, xz, air, 30.0, c.name)


def body_frame(pos: np.ndarray, names: list[str]):
    """Chest frame per image: up (hips -> neck), right (left shoulder -> right shoulder, character's right = +X of the engine's torso), forward = right x up."""
    ix = {n: i for i, n in enumerate(names)}
    hips = pos[:, ix["Hips"]]
    neck = pos[:, ix["Neck"]]
    ls, rs = pos[:, ix["LeftArm"]], pos[:, ix["RightArm"]]
    up = _unit(neck - hips)
    lat = rs - ls                                   # towards the character's right in the CMU convention?  checked below with the sign of forward . hips motion
    back = _unit(np.cross(lat, up))
    lat = _unit(np.cross(up, back))
    return up, lat, back


def euler_xyz_deg(m: np.ndarray) -> np.ndarray:
    """Euler angles (degrees) of the engine's order X then Y then Z about the parent's axes (as in tsb_engine.mathutil.euler)."""
    from .mathutil import euler  # noqa: F401  (documented convention)
    sy = np.clip(m[..., 0, 2], -1, 1)
    y = np.arcsin(sy)
    x = np.arctan2(-m[..., 1, 2], m[..., 2, 2])
    z = np.arctan2(-m[..., 0, 1], m[..., 0, 0])
    return np.degrees(np.stack([x, y, z], -1))


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# assembling a combo from stored clips

def load_library(path: str | Path) -> dict[str, Clip]:
    z = np.load(path)
    out: dict[str, Clip] = {}
    for k in z.files:
        if k.endswith("_ang"):
            cid = k[:-4]
            out[cid] = Clip(z[k].astype(float), z[cid + "_xz"].astype(float), z[cid + "_air"].astype(float), float(z[cid + "_fps"]), cid)
    return out


def _ry_matrix(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def assemble(spec: list[dict], lib: dict[str, Clip], blend: int = 3, follow: np.ndarray | None = None, start_xz=(0.0, 0.0)):
    """Chain gestures into one animation.  Each ``spec`` item: ``clip``, ``t0``/``t1`` (seconds of the stored clip), ``n`` (images it gets), optional ``yaw`` (world heading at
    its start, degrees; default: keep turning from where the previous gesture ended), ``path`` (multiplier on the clip's travel; the clip's own travel is already scaled so that an R6 foot
    stays planted), ``air`` (multiplier on its jump height), ``rev`` (play it backwards).  Gestures are cross-faded over ``blend`` images.

    ``follow`` (N, 2): world positions the root should reach at the end of every gesture (the reference's measured track): a gesture's travel is stretched (x0.4 to x3) toward it
    and the rest is spread smoothly over the gesture.

    Returns (ang (N, 16), xz (N, 2), air (N,)) at 30 images per second."""
    angs: list[np.ndarray] = []
    xzs: list[np.ndarray] = []
    airs: list[np.ndarray] = []
    heading = None
    cum = 0
    last_pos = np.array(start_xz, float)
    for k, sp in enumerate(spec):
        c = lib[sp["clip"]]
        n = int(sp["n"])
        t0, t1 = sp["t0"], sp["t1"]
        seg = segment(c, t1 if sp.get("rev") else t0, t0 if sp.get("rev") else t1, n + (blend if k else 0))
        a, p, h = seg.ang.copy(), seg.xz.copy(), seg.air.copy() * sp.get("air", 1.0)
        # heading: the gesture's own turning is kept, its starting heading is ours
        ry0 = a[0, 0]
        start = sp["yaw"] if sp.get("yaw") is not None else (heading if heading is not None else 0.0)
        d = p - p[0]
        d3 = np.stack([d[:, 0], np.zeros(len(d)), d[:, 1]], 1)
        d3l = d3 @ _ry_matrix(-ry0).T                           # the gesture's travel in its own heading frame
        if sp.get("align") and follow is not None and np.linalg.norm(d3l[-1]) > 0.4:
            cum_end = min(sum(int(x["n"]) for x in spec[: k + 1]) - 1, len(follow) - 1)
            want = np.asarray(follow[cum_end], float) - last_pos
            if np.linalg.norm(want) > 0.4:                      # turn the whole gesture so that its travel points where the reference goes
                start = math.degrees(math.atan2(d3l[-1][2], d3l[-1][0]) - math.atan2(want[1], want[0]))
        a[:, 0] = a[:, 0] - ry0 + start
        d3 = d3l @ _ry_matrix(start).T                          # undo the clip's heading, apply ours
        p = np.stack([d3[:, 0], d3[:, 2]], 1) * sp.get("path", 1.0)
        cum += int(sp["n"])
        if follow is not None:
            target = np.asarray(follow[min(cum - 1, len(follow) - 1)], float) - last_pos
            end = p[-1]
            L = float(np.linalg.norm(end))
            if L > 0.4:
                m = float(np.clip(float(target @ end) / (L * L), 0.4, 3.0))
                p = p * m
            resid = target - p[-1]
            u = np.linspace(0.0, 1.0, len(p))
            p = p + resid[None, :] * (u * u * (3 - 2 * u))[:, None]
        p = p + last_pos
        last_pos = p[-1].copy()
        if angs:
            # angles that wrap (limbs, torso) are put on the branch nearest to the previous gesture's last image
            prev_last = angs[-1][-1]
            for j in range(1, 16):
                a[:, j] += 360.0 * np.round((prev_last[j] - a[0, j]) / 360.0)
        angs.append(a); xzs.append(p); airs.append(h)
        heading = a[-1, 0]
    # cross-fades
    ang, xz, air = angs[0], xzs[0], airs[0]
    for a, p, h in zip(angs[1:], xzs[1:], airs[1:]):
        w = np.linspace(0, 1, blend + 2)[1:-1][:, None]
        ov = ang[-blend:] * (1 - w) + a[:blend] * w
        # positions: cross-fade the velocity, i.e. continue ``p`` from the faded point
        ovp = xz[-blend:] * (1 - w) + p[:blend] * w
        ovh = air[-blend:] * (1 - w[:, 0]) + h[:blend] * w[:, 0]
        ang = np.vstack([ang[:-blend], ov, a[blend:]])
        xz = np.vstack([xz[:-blend], ovp, p[blend:]])
        air = np.concatenate([air[:-blend], ovh, h[blend:]])
    return ang, xz, air
