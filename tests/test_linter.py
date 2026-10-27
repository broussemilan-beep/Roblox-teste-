import copy
import json
import tempfile
import unittest
from pathlib import Path

from examples.builders import clipping_crouch, heavy_punch, robotic_punch
from tsb_engine import lint, serialization
from tsb_engine.cli import main as cli_main
from tsb_engine.model import Animation, Pose


def codes(anim: Animation, severity: str | None = None) -> set[str]:
    return {f.code for f in lint(anim) if severity is None or f.severity == severity}


def clone(anim: Animation) -> Animation:
    return serialization.from_dict(copy.deepcopy(serialization.to_dict(anim)))


class ReferenceAnimationsTest(unittest.TestCase):
    def test_heavy_punch_has_no_errors_or_warnings(self):
        findings = lint(heavy_punch())
        bad = [f for f in findings if f.severity in ("error", "warning")]
        self.assertEqual(bad, [], msg="\n".join(f"{f.code}: {f.message}" for f in bad))

    def test_robotic_punch_trips_the_expected_rules(self):
        self.assertTrue({"TSB002", "TSB003", "TSB004", "TSB005"} <= codes(robotic_punch()))

    def test_clipping_crouch_is_an_error(self):
        self.assertIn("TSB001", codes(clipping_crouch(), "error"))


class MutationTest(unittest.TestCase):
    """Start from the good animation and break exactly one thing."""

    def test_slow_strike(self):
        a = clone(heavy_punch())
        a.events["windup"] = 8  # 8 frames of travel
        self.assertIn("TSB002", codes(a))

    def test_small_torso_twist(self):
        a = clone(heavy_punch())
        for k in list(a.tracks["Torso"]):
            a.set_key("Torso", k.frame, Pose(k.pose.pos, (k.pose.rot[0], 0.0, k.pose.rot[2])), k.easing)
        self.assertIn("TSB003", codes(a))

    def test_symmetric_arms_at_impact(self):
        a = clone(heavy_punch())
        right = a.sample_part("Right Arm", 16)
        a.set_key("Left Arm", 16, Pose(right.pos, (right.rot[0], -right.rot[1], -right.rot[2])))
        findings = [f for f in lint(a) if f.code == "TSB004" and f.frames == (16, 16)]
        self.assertTrue(findings)

    def test_all_parts_peak_together(self):
        a = clone(heavy_punch())
        # make the head and arm move on the same frame as the torso's big snap (frame 15)
        a.set_key("Head", 14, Pose(rot=(0, 58, 0)))
        a.set_key("Head", 15, Pose(rot=(0, -12, 0)))
        a.set_key("Head", 16, Pose(rot=(0, -12, 0)))
        self.assertIn("TSB005", codes(a))

    def test_dislocation_too_far(self):
        a = clone(heavy_punch())
        k = next(k for k in a.tracks["Right Arm"] if k.frame == 16)
        a.set_key("Right Arm", 16, Pose((0, 0, -2.4), k.pose.rot))
        self.assertIn("TSB006", codes(a, "error"))

    def test_dislocation_never_returns(self):
        a = clone(heavy_punch())
        for k in list(a.tracks["Right Arm"]):
            if k.frame >= 19:
                a.set_key("Right Arm", k.frame, Pose((0, 0, -0.9), k.pose.rot), k.easing)
        self.assertIn("TSB006", codes(a, "warning"))

    @staticmethod
    def _freeze(a: Animation, start: int, end: int) -> None:
        """Hold every part exactly on its pose at ``start`` until ``end``."""
        for part in list(a.tracks):
            ref = a.sample_part(part, start)
            a.tracks[part] = [k for k in a.tracks[part] if not (start < k.frame < end)]
            a.set_key(part, start, ref, "linear")
            a.set_key(part, end, ref, "linear")

    def test_frozen_pose_outside_hitstop(self):
        a = clone(heavy_punch())
        del a.events["hitstop"]
        self._freeze(a, 16, 30)
        self.assertIn("TSB007", codes(a))

    def test_declared_hitstop_allows_a_freeze(self):
        a = clone(heavy_punch())
        a.events["hitstop"] = [16, 30]
        self._freeze(a, 16, 30)
        self.assertNotIn("TSB007", codes(a))

    def test_missing_events_skips_checks(self):
        a = clone(heavy_punch())
        a.events = {}
        self.assertIn("TSB009", codes(a))
        self.assertTrue(codes(a).isdisjoint({"TSB002", "TSB003", "TSB004", "TSB005"}))

    def test_windup_after_impact_is_an_error(self):
        a = clone(heavy_punch())
        a.events = {"windup": 20, "impact": 16}
        self.assertIn("TSB011", codes(a, "error"))


class SerializationAndCliTest(unittest.TestCase):
    def test_roundtrip_preserves_lint_result(self):
        a = heavy_punch()
        b = serialization.from_dict(json.loads(json.dumps(serialization.to_dict(a))))
        self.assertEqual([f.to_dict() for f in lint(a)], [f.to_dict() for f in lint(b)])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d, "good.json"), Path(d, "bad.json")
            serialization.save(heavy_punch(), good)
            serialization.save(clipping_crouch(), bad)
            self.assertEqual(cli_main(["lint", str(good)]), 0)
            self.assertEqual(cli_main(["lint", str(bad)]), 1)

    def test_rejects_unknown_schema_version(self):
        with self.assertRaises(ValueError):
            serialization.from_dict({"version": 2, "name": "x"})


if __name__ == "__main__":
    unittest.main()
