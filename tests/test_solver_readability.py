import math
import unittest

from tsb_engine.authoring import K, P, char_points, tp
from tsb_engine.cinematic import Cinematic, autoframe, dolly
from tsb_engine.model import ROOT, Animation
from tsb_engine.readability import PoseReport, render_ids, report
from tsb_engine.scene import Character, Scene
from tsb_engine.solver import aim_limb, chain, dislocate, moving_hold, reach_root, tip_world


def standing() -> Character:
    a = Animation("t", fps=60, archetype="cinematic")
    K(a, 0, T=tp(0.0, 0))
    K(a, 30, T=tp(0.0, 0))
    return Character("c", a)


class SolverTest(unittest.TestCase):
    def test_aim_limb_touches_a_reachable_point(self):
        c = standing()
        c.anim.set_key("Right Arm", 0, P((70, 0, 10)))
        target = tip_world(c, 0, "Right Arm")  # a point the arm can certainly reach
        c.anim.set_key("Right Arm", 0, P((0, 0, 0)))
        pose, res = aim_limb(c, 0, "Right Arm", target, (60, 0))
        self.assertLess(res, 0.1)
        c.anim.set_key("Right Arm", 0, pose)
        self.assertLess(math.dist(tip_world(c, 0, "Right Arm"), target), 0.1)

    def test_reach_root_moves_the_root_when_out_of_reach(self):
        c = standing()
        target = (0.0, 3.0, -6.0)  # far beyond an arm
        pose, res = reach_root(c, 0, "Right Arm", target, (90, 0))
        self.assertLess(res, 0.15)
        self.assertLess(c.anim.sample_root(0).pos[2], -2.0)

    def test_dislocate_returns_to_the_rest_position(self):
        c = standing()
        K(c.anim, 10, "linear", RL=P((60, 0, 0)))
        K(c.anim, 30, "linear", RL=P((60, 0, 0)))
        dislocate(c.anim, "Right Leg", 10, (0.0, -0.6, 0.0), settle=3)
        self.assertAlmostEqual(c.anim.sample_part("Right Leg", 10).pos[1], -0.6)
        self.assertAlmostEqual(c.anim.sample_part("Right Leg", 20).pos[1], 0.0)

    def test_chain_delays_the_head_after_the_torso(self):
        a = Animation("t", archetype="cinematic")
        K(a, 0, T=tp(0, 0), H=P((0, 0, 0)))
        chain(a, 10, "linear", T=tp(0, -20), H=P((30, 0, 0)))
        self.assertEqual(a.tracks["Torso"][-1].frame, 10)
        self.assertEqual(a.tracks["Head"][-1].frame, 12)

    def test_moving_hold_adds_a_key_between_the_ends(self):
        a = Animation("t", archetype="cinematic")
        K(a, 0, RA=P((30, 0, 0)))
        K(a, 20, RA=P((30, 0, 0)))
        moving_hold(a, "Right Arm", 0, 20)
        self.assertNotEqual(a.sample_part("Right Arm", 10).rot, a.sample_part("Right Arm", 0).rot)


class FramingAndReadabilityTest(unittest.TestCase):
    def scene(self):
        c = standing()
        cine = Cinematic(31)
        cine.shot(0, 30, autoframe(lambda f: char_points(f, c), 0, 30, azimuth=40, fill=0.9, follow=1.0))
        return Scene("s", [c], cine=cine)

    def test_autoframe_looks_at_the_character_and_fills_the_frame(self):
        sc = self.scene()
        pos, tgt, fov, _ = sc.cine.camera_state(5)
        self.assertLess(math.dist(tgt, (0, 3, 0)), 1.5)
        rep = report(sc, 5, solo=False)[0]
        self.assertGreater(rep.height, 0.45)

    def test_render_ids_has_pixels_for_each_part_in_a_standing_pose(self):
        sc = self.scene()
        ids = render_ids(sc, 5)
        for pid in range(1, 7):
            self.assertGreater(int((ids == pid).sum()), 0)

    def test_report_flags_a_tiny_character(self):
        r = PoseReport("c", 0, 0.1, 1.0, 0.5, {p: 1.0 for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}, 1.0, 50)
        self.assertTrue(any("tiny" in f for f in r.flags()))

    def test_report_flags_a_hidden_limb(self):
        vis = {p: 1.0 for p in ("Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")}
        vis["Left Arm"] = 0.05
        r = PoseReport("c", 0, 0.5, 1.0, 0.5, vis, 0.05, 500)
        self.assertTrue(any("Left Arm hidden" in f for f in r.flags()))


if __name__ == "__main__":
    unittest.main()
