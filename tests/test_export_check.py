import unittest

from tsb_engine.authoring import K, P, tp
from tsb_engine.export_check import check_export, lerp_cframe, optimize_keys, parse_rbxmx
from tsb_engine.model import Animation
from tsb_engine.roblox_export import keyframe_times, to_rbxmx


def punch() -> Animation:
    a = Animation("t", fps=60, archetype="cinematic")
    K(a, 0, T=tp(0.0, 0), RA=P((0, 0, 10)))
    K(a, 10, "cubic_out", T=tp(0.3, -20, 40), RA=P((-90, 0, 20)))
    K(a, 14, "linear", RA=P((-100, 0, 20)))
    K(a, 30, "linear", T=tp(0.0, 0), RA=P((0, 0, 10)))
    return a


def with_teleport() -> Animation:
    a = punch()
    K(a, 40, "linear", R=P(pos=(0, 0, 0)))
    K(a, 41, "linear", R=P(pos=(0, 0, 60)))
    K(a, 50, "linear", R=P(pos=(0, 0, 60)))
    return a


class ExportCheckTest(unittest.TestCase):
    def test_every_frame_export_matches_the_engine(self):
        self.assertLess(check_export(punch(), step=1).max_error, 0.01)

    def test_authored_keys_are_kept_on_a_coarse_grid(self):
        a = with_teleport()
        frames = keyframe_times(a, step=8)
        for f in (10, 14, 40, 41, 50):
            self.assertIn(f, frames)
        self.assertEqual(keyframe_times(a, step=8, authored=False)[1], 8)

    def test_held_segments_get_a_key_just_before_the_jump(self):
        a = Animation("t", archetype="cinematic")
        K(a, 0, "constant", RA=P((0, 0, 10)))
        K(a, 20, "linear", RA=P((90, 0, 10)))
        self.assertIn(19, keyframe_times(a, step=30))

    def test_a_teleport_is_not_smeared_by_a_coarse_step(self):
        a = with_teleport()
        self.assertLess(check_export(a, step=8).worst["Torso"], 0.2)

    def test_optimized_keys_stay_within_tolerance(self):
        a = with_teleport()
        keys = optimize_keys(a, tolerance=0.05, base_step=8)
        self.assertLess(len(keys), a.last_frame + 1)
        self.assertLess(check_export(a, keys_at=keys).max_error, 0.06)

    def test_exported_text_parses_back(self):
        keys = parse_rbxmx(to_rbxmx(punch(), step=5))
        self.assertGreater(len(keys), 3)
        self.assertEqual(set(keys[0][1]), {"HumanoidRootPart", "Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"})

    def test_lerp_cframe_interpolates_position_and_rotation(self):
        ident = (((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.0, 0.0, 0.0))
        rot90 = (((0, -1, 0), (1, 0, 0), (0, 0, 1)), (2.0, 0.0, 0.0))
        mid = lerp_cframe(ident, rot90, 0.5)
        self.assertAlmostEqual(mid[1][0], 1.0)
        self.assertAlmostEqual(mid[0][0][0], 0.7071, places=3)


if __name__ == "__main__":
    unittest.main()
