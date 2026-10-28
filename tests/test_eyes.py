import tempfile
import unittest
from pathlib import Path

import numpy as np

try:
    import cv2

    from tsb_engine import eyes
except Exception:  # the eyes tools are optional (requirements-eyes.txt)
    cv2 = None


def grey(v, h=90, w=160):
    return np.full((h, w, 3), v, np.uint8)


def with_block(v, frac=0.4, h=90, w=160):
    im = grey(v, h, w)
    bh = int(h * frac)
    im[(h - bh) // 2 : (h + bh) // 2, w // 3 : w // 2] = 8
    return im


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class EyesTest(unittest.TestCase):
    def clip(self, frames):
        return eyes.analyze(np.stack(frames), "t")

    def test_hold_and_cut_detection(self):
        a, b = with_block(130), grey(220)
        c = self.clip([a] * 8 + [b] * 6)
        self.assertIn(8, c.cuts)
        self.assertGreaterEqual(max(e - s + 1 for s, e in eyes.hold_runs(c)), 5)
        s = eyes.summarize(c)
        self.assertEqual(s["frames"], 14)
        self.assertGreater(s["held_frac"], 0.6)

    def test_subject_height_is_measured(self):
        c = self.clip([with_block(130, 0.4)] * 3)
        self.assertAlmostEqual(float(c.m["subject_h"][1]), 0.4, delta=0.12)

    def test_black_and_white_frames_are_counted(self):
        c = self.clip([grey(130)] * 3 + [grey(0)] * 2 + [grey(255)] * 2)
        s = eyes.summarize(c)
        self.assertEqual(s["black_frames"], 2)
        self.assertEqual(s["white_frames_gt60"], 2)

    def test_anchor_path_hits_the_anchors_and_is_monotonic(self):
        ref = self.clip([grey(130)] * 20)
        mine = self.clip([grey(130)] * 30)
        path = eyes.anchor_path(ref, mine, [(10, 22)])
        self.assertIn((10, 22), path)
        self.assertEqual(path[-1], (19, 29))
        js = [j for _, j in path]
        self.assertEqual(js, sorted(js))

    def test_diagnose_flags_low_and_high(self):
        ref = eyes.summarize(self.clip([with_block(130, 0.6)] * 5))
        mine = dict(ref)
        mine["subject_h_median"] = ref["subject_h_median"] * 0.4
        mine["black_frames"] = ref["black_frames"] + 9
        lines = eyes.diagnose(ref, mine)
        self.assertTrue(any(l.startswith("[LOW]") and "character height" in l for l in lines))
        self.assertTrue(any(l.startswith("[HIGH]") and "black frames" in l for l in lines))

    def test_load_clip_crops_letterbox_bars(self):
        with tempfile.TemporaryDirectory() as d:
            for i in range(4):
                im = grey(130, 100, 160)
                im[:12] = 0
                im[-12:] = 0
                cv2.imwrite(str(Path(d) / f"f_{i}.png"), im)
            fr = eyes.load_clip(d, width=160)
        self.assertEqual(fr.shape[1], 76)

    def test_pictures_have_the_frame_size(self):
        fr = np.stack([with_block(130), with_block(140), with_block(150)])
        self.assertEqual(eyes.motion_trail(fr, 0, 2).shape, fr[0].shape)
        self.assertEqual(eyes.flow_picture(fr, 1).shape, fr[0].shape)


if __name__ == "__main__":
    unittest.main()
