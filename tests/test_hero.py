import math
import unittest

from tsb_engine import hero


class HeroCadenceTest(unittest.TestCase):
    def test_cadence_from_a_spread_signal(self):
        n = 40
        h = [0.3] * n
        w = [0.2 + 0.08 * math.sin(2 * math.pi * i / 6.0) + 0.002 * i for i in range(n)]  # width peaks every 6 images, plus a slow zoom
        c = hero.cadence(w, h)
        self.assertIsNotNone(c)
        self.assertEqual(c["width_period"], 6)
        self.assertEqual(c["cycle_period"], 12)

    def test_flat_signal_has_no_cadence(self):
        self.assertIsNone(hero.cadence([0.2] * 30, [0.3] * 30))

    def test_gaps_are_tolerated(self):
        w = [0.2 + 0.05 * math.sin(2 * math.pi * i / 8.0) for i in range(32)]
        h = [0.3] * 32
        w[5] = h[5] = None
        self.assertEqual(hero.cadence(w, h)["width_period"], 8)


if __name__ == "__main__":
    unittest.main()


class FramingMatchTest(unittest.TestCase):
    def test_calm_framing_follows_the_reference_tracks(self):
        import json
        from pathlib import Path

        from examples.calm import build

        sc = build()
        root = Path(__file__).resolve().parent.parent / "docs" / "research" / "reference-tracks"
        for name in ("hero_284_299", "hero_72_148"):
            ref = json.loads((root / f"{name}.json").read_text())
            f0 = ref["first_frame"]
            err = hero.compare_framing(hero.my_framing(sc, f0, f0 + len(ref["cx"]) - 1), ref)
            self.assertLess(err["cx"], 0.1, name)
            self.assertLess(err["cy"], 0.1, name)
            self.assertLess(err["h"], 0.08, name)
