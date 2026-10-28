import unittest

from examples.run_test import build
from tsb_engine.gait import stride_speed
from tsb_engine.kinematics import corners


class GaitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hero = build().characters[0]

    def test_stride_speed_formula(self):
        # a foot planted for half a cycle travels 2 L sin(amp) relative to the body: speed = 4 L sin(amp) / period
        self.assertAlmostEqual(stride_speed(45, 12), 4 * 2 * 0.7071 / 12, places=3)
        self.assertGreater(stride_speed(55, 8), stride_speed(45, 12))

    def test_feet_touch_the_ground_at_mid_stance_and_leave_it_in_flight(self):
        # flight height = 0.45 sin^2(phase): planted when the legs pass (phase 0 mod pi), 0.45 above the ground when they are split
        lows = []
        for f in range(0, 60):
            tf = self.hero.world_parts(f)
            lows.append(min(min(c[1] for c in corners(p, t)) for p, t in tf.items()))
        self.assertAlmostEqual(min(lows), 0.0, places=2)
        self.assertGreater(max(lows), 0.3)
        self.assertLess(max(lows), 0.5)

    def test_torso_bobs_because_the_root_comes_from_the_feet(self):
        ys = [self.hero.world_parts(f)["Torso"][1][1] for f in range(12, 60)]
        self.assertGreater(max(ys) - min(ys), 0.3)

    def test_legs_swing_in_opposite_phase(self):
        for f in range(10, 40):
            r = self.hero.anim.sample_part("Right Leg", f).rot[0]
            l = self.hero.anim.sample_part("Left Leg", f).rot[0]
            self.assertLessEqual(r * l, 1e-6, msg=f"frame {f}")

    def test_arms_counter_swing_the_legs_when_free(self):
        from tsb_engine.gait import run_keys  # a free-arm run: the right arm goes forward while the left leg does
        from tsb_engine.model import Animation

        a = Animation("t", fps=30, archetype="cinematic")
        run_keys(a, 0, 23, lambda f: (0.4 * f, 0.0, 270.0), period=12.0, amp=45.0)
        for f in range(1, 23):
            self.assertLessEqual(a.sample_part("Right Arm", f).rot[0] * a.sample_part("Right Leg", f).rot[0], 1e-6)


if __name__ == "__main__":
    unittest.main()
