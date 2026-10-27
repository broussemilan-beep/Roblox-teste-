import math
import unittest

from examples.scenes import SCENES
from tsb_engine.authoring import K, tp
from tsb_engine.cinematic import Cinematic, dolly
from tsb_engine.model import Animation
from tsb_engine.scene import Character, Scene, export_viewer_data
from tsb_engine.secondary import Rigid, Strand, coat_and_hair


def idle_then_lunge() -> Animation:
    a = Animation("t", fps=60, archetype="cinematic")
    K(a, 0, T=tp(0.0, 0))
    K(a, 20, T=tp(0.0, 0))
    K(a, 40, T=tp(0.0, 0))
    return a


class SecondaryMotionTest(unittest.TestCase):
    def test_outfit_produces_one_track_per_part_with_one_frame_each(self):
        c = Character("h", idle_then_lunge(), outfit=coat_and_hair())
        tracks = c.outfit.simulate(c, 30, hold=1, fps=60)
        self.assertGreater(len(tracks), 10)
        for t in tracks:
            self.assertEqual(len(t.frames), 30)

    def test_strand_keeps_segment_lengths_and_stays_above_ground(self):
        c = Character("h", idle_then_lunge())
        s = Strand("s", "Torso", (0.0, -0.95, 0.5), 4, 0.6, 0.5, 0.2, "#000000")
        tracks = s.simulate(c, 40, 1, 60)
        for f in (0, 20, 39):
            centres = [t.frames[f][1] for t in tracks]
            for a, b in zip(centres, centres[1:]):
                self.assertLess(math.dist(a, b), 0.6 * 1.25)
            self.assertGreater(min(p[1] for p in centres), 0.0)

    def test_hold_freezes_extras_between_updates(self):
        c = Character("h", idle_then_lunge())
        tr = Rigid("r", "Head", (0, 1, 0), (1, 1, 1), "#fff").simulate(c, 10, hold=2)[0]
        self.assertEqual(tr.frames[2], tr.frames[3])


class CinematicPrimitivesTest(unittest.TestCase):
    def test_ink_arc_and_screen_fx_serialise(self):
        cine = Cinematic(60)
        cine.shot(0, 60, dolly((15, 3.4, -3.5), (15, 3.4, -3.5), (0, 1.9, -3.5), (0, 1.9, -3.5), fov=44))
        cine.ink_arc(5, 10, (0, 2, 0), (0, 1, 0), 2.0, 0, 180, 0.3)
        cine.ink_path(5, 8, [(0, 0, 0), (1, 1, 0)], 0.4)
        cine.streaks(5, 4, (0, 0, 0), (1, 0, 0))
        cine.slices(5, 2, (0, 1, 0))
        cine.screen_fx("bw", 10, 4, accent="#7ff0ff")
        d = cine.to_dict()
        self.assertEqual({f["type"] for f in d["fx"]} >= {"ink", "streaks", "slices"}, True)
        self.assertEqual(d["screen"]["fx"][0]["kind"], "bw")

    def test_scene_hold_repeats_pose_data_on_pairs_of_frames(self):
        a = Animation("t", fps=60, archetype="cinematic")
        K(a, 0, T=tp(0.0, 0))
        K(a, 20, T=tp(0.0, 40))
        sc = Scene("x", [Character("h", a, outfit=coat_and_hair())], hold=2)
        d = export_viewer_data(sc)
        fr = d["characters"][0]["frames"]
        self.assertEqual(fr[4], fr[5])
        self.assertNotEqual(fr[4], fr[6])
        self.assertTrue(d["characters"][0]["extras"])


class ShortSceneTest(unittest.TestCase):
    def test_duel_short_builds_and_exports(self):
        sc = SCENES["duel_short"]()
        self.assertEqual(sc.n_frames, 660)
        self.assertEqual(sc.hold, 2)
        d = export_viewer_data(sc)
        self.assertEqual(len(d["characters"]), 2)
        self.assertTrue({"bw", "black", "glint"} <= {f["kind"] for f in d["cine"]["screen"]["fx"]})


if __name__ == "__main__":
    unittest.main()


class ReferenceStyleTest(unittest.TestCase):
    def test_reference_outfit_exports_round_volumes(self):
        from tsb_engine.secondary import reference_outfit

        a = Animation("t", fps=60, archetype="cinematic")
        K(a, 0, T=tp(0.0, 0))
        sc = Scene("x", [Character("h", a, outfit=reference_outfit())])
        d = export_viewer_data(sc)
        shapes = {e["shape"] for e in d["characters"][0]["extras"]}
        self.assertTrue({"cyl", "ell", "box"} <= shapes)

    def test_screen_strokes_and_outlined_burst_serialise(self):
        cine = Cinematic(30)
        cine.shot(0, 29, dolly((15, 3.4, -3.5), (15, 3.4, -3.5), (0, 1.9, -3.5), (0, 1.9, -3.5), fov=44))
        cine.screen_fx("strokes", 4, 20, n0=9, n1=2, w=0.15, glow="#7ff0ff", seed=3)
        cine.burst(5, 8, (0, 3, 0), 0.3, 2.0, "#0b0b0f", "#0b0b0f", outline="#ffffff", sprite=False)
        d = cine.to_dict()
        self.assertEqual(d["screen"]["fx"][0]["kind"], "strokes")
        bursts = [f for f in d["fx"] if f["type"] == "burst"]
        self.assertEqual(bursts[0]["outline"], "#ffffff")
        self.assertFalse([f for f in d["fx"] if f["type"] == "sprite"])
