import unittest

import numpy as np

try:
    from tsb_engine import tracker
except Exception:
    tracker = None


@unittest.skipIf(tracker is None, "tracker module not importable")
class TrackerMeasureTest(unittest.TestCase):
    ones = staticmethod(lambda n: np.ones(n))

    def test_two_state_flip_is_a_strobe(self):
        r = np.array([0.5, 0.3] * 14)
        self.assertEqual(tracker.strobe(r, self.ones(28))["kind"], "strobe")

    def test_smooth_sweep_is_not_a_strobe(self):
        r = np.sin(np.linspace(0, 6, 28)) * 0.3
        self.assertEqual(tracker.strobe(r, self.ones(28))["kind"], "moving")

    def test_jumping_through_many_poses_is_cycling(self):
        r = np.array([0.1, 0.5, 0.9, 0.2, 0.7, 0.3, 0.8, 0.1, 0.6, 0.95, 0.2, 0.55] * 2)
        self.assertEqual(tracker.strobe(r, self.ones(24))["kind"], "cycling")

    def test_a_held_limb_is_steady_even_with_jitter(self):
        r = 0.5 + 0.004 * np.random.RandomState(0).randn(28)
        self.assertEqual(tracker.strobe(r, self.ones(28))["kind"], "steady")

    def test_reliability_follows_the_presence_logit(self):
        self.assertEqual(tracker.reliability(np.array([20, 8, 9, 9, 10.0]), 0)[0], "good")
        self.assertEqual(tracker.reliability(np.array([17, 2.5, 1.4, 0.9, 0.7]), 0)[0], "lost")
        self.assertEqual(tracker.reliability(np.array([17, 6, 5.5, 6, 6.5]), 0)[0], "doubtful")

    def test_measure_reports_reach_toward_the_other_actor(self):
        m = np.zeros((3, 40, 80), bool)
        m[:, 10:30, 10:30] = True
        m[1, 18:22, 30:60] = True  # an arm shoots out to the right on frame 1
        out = tracker.measure(m, toward=1)
        self.assertGreater(out["reach"][1], out["reach"][0] + 0.3)

    def test_iou(self):
        a = np.zeros((10, 10), bool); a[:5] = True
        b = np.zeros((10, 10), bool); b[:10] = True
        self.assertAlmostEqual(tracker.iou(a, b), 0.5)


if __name__ == "__main__":
    unittest.main()
