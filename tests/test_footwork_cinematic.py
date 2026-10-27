import math
import unittest

from tsb_engine.authoring import K, P, attach, keep_above_ground, tp
from tsb_engine.cinematic import Cinematic, Track, dolly
from tsb_engine.footwork import Step, bake_footwork, gait_steps, sole_positions
from tsb_engine.kinematics import corners, lowest_y, root_transform
from tsb_engine.model import Animation
from tsb_engine.scene import Character


def crouched() -> Animation:
    a = Animation("t", fps=60, archetype="cinematic")
    K(a, 0, T=tp(0.6, -25))
    K(a, 30, T=tp(0.6, -25))
    return a


class FootworkTest(unittest.TestCase):
    def test_planted_feet_stay_near_ground_in_a_crouch(self):
        a = crouched()
        bake_footwork(a, {"Right Leg": (1.3, 0.2), "Left Leg": (-1.3, 0.2)}, [], 0, 30)
        for f in (0, 15, 30):
            self.assertGreater(lowest_y(a.sample(f), root=root_transform(a.sample_root(f))), -0.35)

    def test_planted_feet_do_not_move(self):
        a = crouched()
        bake_footwork(a, {"Right Leg": (1.3, 0.2), "Left Leg": (-1.3, 0.2)}, [], 0, 30)
        p0, p1 = sole_positions(a, 0), sole_positions(a, 30)
        for leg in p0:
            self.assertLess(math.dist(p0[leg], p1[leg]), 0.05)

    def test_step_moves_foot_to_target_with_lift(self):
        a = crouched()
        step = Step("Left Leg", 5, 15, (-1.3, -1.0), 0.6)
        bake_footwork(a, {"Right Leg": (1.3, 0.2), "Left Leg": (-1.3, 0.2)}, [step], 0, 30)
        mid = sole_positions(a, 10)["Left Leg"]
        end = sole_positions(a, 20)["Left Leg"]
        self.assertGreater(mid[1], 0.2)  # swing foot is lifted
        self.assertLess(end[2], -0.6)  # and it landed ahead (-Z)

    def test_gait_steps_alternate_legs(self):
        a = Animation("t", fps=60, archetype="cinematic")
        K(a, 0, R=P(pos=(0, 0, 0)), T=tp(0.3, -20))
        K(a, 60, R=P(pos=(0, 0, -24)))
        steps = gait_steps(a, 0, 60, interval=7, swing=6)
        self.assertGreater(len(steps), 4)
        self.assertTrue(all(s1.leg != s2.leg for s1, s2 in zip(steps, steps[1:])))


class CinematicTest(unittest.TestCase):
    def test_new_fx_are_exported_and_kick_changes_fov(self):
        c = Cinematic(30)
        c.shot(0, 29, dolly((0, 0, 5), (0, 0, 5), (0, 0, 0), (0, 0, 0), fov=50))
        c.burst(5, 8, (0, 1, 0), 0.3, 2.0)
        c.bolt(5, 9, a=(0, 0, 0), b=(0, 5, 0))
        c.slash(5, 8, (0, 1, 0), (1, 0, 0), 2.0, 0, 90)
        c.glow(0, 10, c=(0, 1, 0))
        c.emit(0, 5, origin=(0, 0, 0), shape="spark")
        c.punch_in(10, 0.2, 8)
        kinds = {e["type"] for e in c.to_dict()["fx"]}
        self.assertTrue({"burst", "bolt", "slash", "glow", "emit"} <= kinds)
        self.assertLess(c.camera_state(10)[2], 50.0)
        self.assertEqual(c.camera_state(25)[2], 50.0)


    def test_track_holds_and_eases(self):
        t = Track(1.0).key(10, 0.0).key(20, 1.0, "linear")
        self.assertEqual(t.at(0), 0.0)
        self.assertAlmostEqual(t.at(15), 0.5)
        self.assertEqual(t.at(99), 1.0)

    def test_shot_must_cover_frame(self):
        c = Cinematic(30)
        c.shot(0, 10, dolly((0, 0, 5), (0, 0, 5), (0, 0, 0), (0, 0, 0)))
        c.camera_state(5)
        with self.assertRaises(ValueError):
            c.camera_state(20)

    def test_later_shot_overrides_and_shake_moves_camera(self):
        c = Cinematic(30)
        c.shot(0, 29, dolly((0, 0, 5), (0, 0, 5), (0, 0, 0), (0, 0, 0)))
        c.shot(10, 20, dolly((9, 0, 5), (9, 0, 5), (0, 0, 0), (0, 0, 0)))
        self.assertEqual(c.camera_state(15)[0][0], 9)
        before = c.camera_state(15)[0]
        c.shake(12, 8, 0.5)
        self.assertNotEqual(c.camera_state(15)[0], before)


class AuthoringTest(unittest.TestCase):
    def test_lying_root_rot_is_face_down_head_first(self):
        from tsb_engine.authoring import lying_root_rot

        v = Character("v", Animation("v", archetype="cinematic"), base_pos=(0, 0, -6), base_yaw=180.0)
        for face_down in (True, False):
            rot = lying_root_rot(v, (0.0, -1.0), face_down)
            v.anim.set_key("Root", 0, P(rot), "linear")
            tf = v.world_parts(0)
            head, torso = tf["Head"][1], tf["Torso"][1]
            self.assertLess(head[2] - torso[2], -1.0)  # head points to world -Z
            front_y = -tf["Torso"][0][1][2]
            self.assertTrue((front_y < -0.9) if face_down else (front_y > 0.9))

    def test_attach_puts_head_on_hand(self):
        atk = Character("a", Animation("a", archetype="cinematic"))
        vic = Character("v", Animation("v", archetype="cinematic"), base_pos=(0, 0, -6), base_yaw=180.0)
        K(atk.anim, 0, RA=P((90, 0, 0)))
        K(atk.anim, 5, RA=P((90, 0, 0)))
        attach(vic, atk, range(0, 6), "Head", (0, 0, 0), "Right Arm", (0, -1.0, 0))
        hand = atk.world_parts(3)["Right Arm"]
        from tsb_engine.kinematics import apply

        h = apply(hand, (0, -1.0, 0))
        head = apply(vic.world_parts(3)["Head"], (0, 0, 0))
        self.assertLess(math.dist(h, head), 1e-6)

    def test_keep_above_ground_only_raises(self):
        c = Character("v", Animation("v", archetype="cinematic"))
        K(c.anim, 0, R=P(pos=(0, -1.0, 0)))
        keep_above_ground(c, [0])
        low = min(min(v[1] for v in corners(p, t)) for p, t in c.world_parts(0).items())
        self.assertAlmostEqual(low, 0.0, places=6)
        K(c.anim, 1, R=P(pos=(0, 2.0, 0)))
        keep_above_ground(c, [1])
        self.assertEqual(c.anim.sample_root(1).pos[1], 2.0)


if __name__ == "__main__":
    unittest.main()


class RobloxExportTest(unittest.TestCase):
    def test_pose_mapping_matches_roblox_forward_kinematics(self):
        from tsb_engine.kinematics import part_transforms, root_transform
        from tsb_engine.model import PARTS
        from tsb_engine.roblox_export import pose_cframe, roblox_forward_kinematics

        a = Animation("t", archetype="cinematic")
        K(a, 0, T=tp(0.4, -20, 15), H=P((10, 20, 5)), RA=P((90, 10, 30), (0.1, 0, -0.5)), LA=P((-40, 0, -20)),
          RL=P((30, 5, 8)), LL=P((-25, 0, -4)), R=P((10, 40, 0), (1.0, 0.5, -2.0)))
        s, r = a.sample(0), a.sample_root(0)
        rb = roblox_forward_kinematics({p: pose_cframe(p, s, r) for p in PARTS})
        ours = part_transforms(s, root=root_transform(r))
        worst = 0.0
        for p in PARTS:
            worst = max(worst, math.dist(rb[p][1], ours[p][1]),
                        max(abs(rb[p][0][i][j] - ours[p][0][i][j]) for i in range(3) for j in range(3)))
        self.assertLess(worst, 1e-9)
        # the test is sensitive: an identity CFrame for a rotated arm would not match
        bad = {p: pose_cframe(p, s, r) for p in PARTS}
        bad["Right Arm"] = ((( 1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0))
        self.assertGreater(math.dist(roblox_forward_kinematics(bad)["Right Arm"][1], ours["Right Arm"][1]), 0.1)

    def test_rbxmx_is_wellformed_and_has_markers(self):
        import xml.dom.minidom as minidom

        from tsb_engine.roblox_export import to_luau, to_rbxmx

        a = Animation("punch", archetype="heavy")
        K(a, 0, T=tp(0, 0))
        K(a, 10, T=tp(0.2, -10))
        a.events["impact"] = 6
        text = to_rbxmx(a)
        doc = minidom.parseString(text)
        classes = [n.getAttribute("class") for n in doc.getElementsByTagName("Item")]
        self.assertEqual(classes.count("Keyframe"), 11)
        self.assertEqual(classes.count("KeyframeMarker"), 1)
        self.assertEqual(classes.count("Pose"), 11 * 7)
        self.assertIn("Instance.new(\"KeyframeSequence\")", to_luau(a))


class TexturesAndCuesTest(unittest.TestCase):
    def test_flipbook_sheet_layout_and_alpha(self):
        from tsb_engine import textures

        frames = textures.starburst(n=64, frames=8)
        self.assertEqual(len(frames), 8)
        self.assertEqual(frames[0].shape, (64, 64, 4))
        sheet = textures.pack_flipbook(frames, 4, size=256, pad=2)
        self.assertEqual(sheet.size, (256, 256))
        self.assertGreater(max(f[..., 3].max() for f in frames), 0.9)  # a bright frame exists
        self.assertEqual(frames[-1][..., 3].max() < frames[3][..., 3].max(), True)  # it fades out
        with self.assertRaises(ValueError):
            textures.pack_flipbook(textures.smoke(n=32, frames=20), 4, size=256)

    def test_cue_sheet_converts_units(self):
        from tsb_engine.roblox_cues import cue_sheet

        c = Cinematic(60)
        c.shot(0, 59, dolly((0, 0, 5), (0, 0, 5), (0, 0, 0), (0, 0, 0)))
        c.emit(6, 6, origin=(0, 1, 0), rate=0, burst=10, vel=(0.5, 1.0), dir=(0, 1, 0), life=(30, 60), grav=0.01, shape="spark")
        c.ring(12, 30, (0, 0, 0), 1, 10, 1, 0.1, "#ffffff")
        sheet = cue_sheet(c)
        self.assertIn("Speed 30-60", sheet)  # 0.5-1.0 studs/frame at 60 fps
        self.assertIn("Lifetime 0.50-1.00s", sheet)
        self.assertIn("shockwave ring", sheet)
