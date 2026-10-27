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
