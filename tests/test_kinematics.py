import math
import unittest

from tsb_engine.kinematics import SIZES, corners, lowest_y, part_transforms
from tsb_engine.model import Animation, Pose
from tsb_engine.moves import plant_legs, torso_pose


class RestPoseTest(unittest.TestCase):
    def test_standing_feet_on_ground_and_head_height(self):
        sample = {}
        self.assertAlmostEqual(lowest_y(sample), 0.0, places=6)
        tf = part_transforms(sample)
        head_top = max(c[1] for c in corners("Head", tf["Head"]))
        self.assertAlmostEqual(head_top, 5.0, places=6)

    def test_arms_flush_with_torso(self):
        tf = part_transforms({})
        arm_x = [c[0] for c in corners("Right Arm", tf["Right Arm"])]
        self.assertAlmostEqual(min(arm_x), 1.0, places=6)
        self.assertAlmostEqual(max(arm_x), 2.0, places=6)

    def test_arm_pitch_90_points_forward_minus_z(self):
        tf = part_transforms({"Right Arm": Pose(rot=(90.0, 0.0, 0.0))})
        z = [c[2] for c in corners("Right Arm", tf["Right Arm"])]
        # the shoulder pivot sits 0.5 below the arm top, so the arm reaches 1.5 studs forward
        self.assertAlmostEqual(min(z), -1.5, places=6)


class PlantLegsTest(unittest.TestCase):
    def assertFeetOnGround(self, torso, legs):
        sample = {"Torso": torso, **legs}
        self.assertAlmostEqual(lowest_y(sample, ("Right Leg", "Left Leg")), 0.0, delta=0.01)

    def test_without_planting_the_feet_go_through_the_floor(self):
        # the legs hang from the torso: dropping it 0.55 pushes the feet 0.55 below the ground
        clipped = lowest_y({"Torso": torso_pose(drop=0.55)}, ("Right Leg", "Left Leg"))
        self.assertAlmostEqual(clipped, -0.55, places=6)

    def test_crouch_with_front_leg(self):
        torso = torso_pose(drop=0.55)
        legs = plant_legs(torso, lateral=0.8, front_leg="Right Leg")
        self.assertFeetOnGround(torso, legs)
        # rx > 0 swings a limb forward (-Z): front foot forward, back foot backward
        self.assertGreater(legs["Right Leg"].rot[0], 0)
        self.assertLess(legs["Left Leg"].rot[0], 0)

    def test_crouch_symmetric_sideways(self):
        torso = torso_pose(drop=0.8)
        legs = plant_legs(torso)
        self.assertFeetOnGround(torso, legs)
        self.assertAlmostEqual(legs["Right Leg"].rot[2], -legs["Left Leg"].rot[2], places=6)

    def test_leaning_and_twisted_torso(self):
        torso = torso_pose(drop=0.5, pitch=20, yaw=-50)
        legs = plant_legs(torso, lateral=0.6, front_leg="Left Leg", stance_yaw=-20)
        self.assertFeetOnGround(torso, legs)

    def test_too_high_torso_raises(self):
        with self.assertRaises(ValueError):
            plant_legs(Pose(pos=(0.0, 0.5, 0.0)))  # torso raised: legs cannot reach the ground

    def test_standing_returns_straight_legs(self):
        legs = plant_legs(Pose())
        for leg in legs.values():
            self.assertAlmostEqual(leg.rot[0], 0.0, places=6)
            self.assertAlmostEqual(leg.rot[2], 0.0, places=6)


class SamplingTest(unittest.TestCase):
    def test_constant_holds_then_jumps(self):
        a = Animation("t")
        a.set_key("Torso", 0, Pose(rot=(0, 0, 0)), "constant")
        a.set_key("Torso", 10, Pose(rot=(0, 90, 0)), "linear")
        self.assertEqual(a.sample_part("Torso", 5).rot[1], 0)
        self.assertEqual(a.sample_part("Torso", 10).rot[1], 90)

    def test_linear_midpoint_and_clamping(self):
        a = Animation("t")
        a.set_key("Head", 0, Pose(rot=(0, 0, 0)))
        a.set_key("Head", 10, Pose(rot=(0, 100, 0)))
        self.assertAlmostEqual(a.sample_part("Head", 5).rot[1], 50)
        self.assertEqual(a.sample_part("Head", 99).rot[1], 100)
        self.assertEqual(a.sample_part("Head", -3).rot[1], 0)

    def test_unknown_part_or_easing_rejected(self):
        a = Animation("t")
        with self.assertRaises(ValueError):
            a.set_key("Tail", 0, Pose())
        with self.assertRaises(ValueError):
            a.set_key("Head", 0, Pose(), "bouncy")


if __name__ == "__main__":
    unittest.main()
