import unittest

import numpy as np

try:
    import cv2

    from tsb_engine import perception, reading
except Exception:
    cv2 = None


def scene(bg=140, h=100, w=200):
    f = np.full((h, w, 3), bg, np.uint8)
    f[:, :, 0] = np.clip(bg + 8, 0, 255)  # slight blue-grey sky
    cv2.rectangle(f, (40, 30), (70, 90), (20, 20, 24), -1)     # dark actor
    cv2.rectangle(f, (130, 30), (150, 90), (236, 236, 238), -1)  # light actor
    rng = np.random.RandomState(3)
    for _ in range(120):                                      # background texture so the camera can be tracked
        x, y = rng.randint(0, w), rng.randint(0, h)
        if not (30 < x < 160 and 20 < y < 95):
            cv2.circle(f, (x, y), 2, (110, 112, 118), -1)
    return f


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class PerceptionTest(unittest.TestCase):
    def read(self, frames):
        return perception.perceive(np.stack(frames), fps=30)

    def labels(self, pc):
        return {e.label for e in pc.events}

    def test_black_white_and_empty_frames_are_named(self):
        base = scene()
        frames = [base] * 10 + [np.zeros_like(base)] * 2 + [base] * 10 + [np.full_like(base, 255)] * 3 + [base] * 10
        pc = self.read(frames)
        black = [e for e in pc.events if e.label == "PUNCT_BLACK"]
        white = [e for e in pc.events if e.label == "PUNCT_WHITE"]
        self.assertEqual((black[0].start, black[0].end), (10, 11))
        self.assertEqual((white[0].start, white[0].end), (22, 24))

    def test_an_empty_stage_is_detected(self):
        bg = np.full((100, 200, 3), 140, np.uint8)
        pc = self.read([scene()] * 8 + [bg] * 6 + [scene()] * 8)
        self.assertIn("EMPTY", self.labels(pc))

    def test_a_static_clip_has_no_events_of_the_hit_kind(self):
        pc = self.read([scene()] * 30)
        self.assertFalse(self.labels(pc) & {"MULTIHIT_VFX", "REAL_COMBO", "SINGLE_HIT_SMEAR", "CAMERA_MOVE", "CUT"})

    def test_a_steady_pan_is_a_camera_move_not_a_cut(self):
        base = scene(w=400)
        frames = [base[:, 2 * i : 2 * i + 200].copy() for i in range(30)]
        pc = self.read(frames)
        self.assertIn("CAMERA_MOVE", self.labels(pc))
        self.assertNotIn("CUT", self.labels(pc))


class FakePC:
    def __init__(self, events, n=40):
        self.n, self.fps, self.events = n, 30, events

    def in_range(self, a, b):
        return [e for e in self.events if e.start <= b and e.end >= a]


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class ReadingTest(unittest.TestCase):
    def pc(self, *labels):
        from tsb_engine.perception import Event

        return FakePC([Event(lab, a, b) for lab, a, b in labels])

    def entry(self, **kw):
        base = {"start": 0, "end": 39, "viewed": [[0, 39]], "camera": "", "hits": None, "vfx_multihit": None, "victim": "", "punct": "", "notes": ""}
        base.update(kw)
        return {"fps": 30, "frames": 40, "shots": [base]}

    def test_unviewed_frames_are_flagged(self):
        issues = reading.validate(self.entry(start=0, end=5, viewed=[[0, 2]]), self.pc())
        self.assertTrue(any(i.kind == "unviewed" for i in issues))

    def test_claiming_distinct_hits_over_a_vfx_train_is_a_contradiction(self):
        issues = reading.validate(self.entry(hits=4), self.pc(("MULTIHIT_VFX", 0, 39)))
        self.assertTrue(any("ONE pose + VFX" in str(i) for i in issues))

    def test_a_static_camera_claim_against_a_measured_move(self):
        issues = reading.validate(self.entry(camera="static"), self.pc(("CAMERA_MOVE", 5, 30)))
        self.assertTrue(any("static camera" in str(i) for i in issues))

    def test_an_unwritten_black_frame_is_reported(self):
        issues = reading.validate(self.entry(), self.pc(("PUNCT_BLACK", 10, 11)))
        self.assertTrue(any("black/white punctuation" in str(i) for i in issues))

    def test_a_consistent_reading_has_no_issue(self):
        self.assertEqual(reading.validate(self.entry(camera="static", punct="none"), self.pc()), [])


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class NegativeAndVictimTest(unittest.TestCase):
    def read(self, frames):
        return perception.perceive(np.stack(frames), fps=30)

    def labels(self, pc):
        return {e.label for e in pc.events}

    def test_negative_frames_are_named_and_normal_scene_is_not_negative_and_normal_scene_is_not_negative(self):
        base = scene()
        neg = 255 - base
        frames = [base] * 10 + [neg] * 3 + [base] * 10
        pc = self.read(frames)
        found = [e for e in pc.events if e.label == "PUNCT_NEGATIVE"]
        self.assertEqual([(e.start, e.end) for e in found], [(10, 12)])
        self.assertNotIn("PUNCT_NEGATIVE", self.labels(self.read([base] * 24)))

    def test_compact_blob_sees_a_body_but_not_a_line_or_a_ring(self):
        body = np.zeros((100, 200), bool)
        body[30:90, 130:150] = True
        line = np.zeros((100, 200), bool)
        line[50, 10:190] = True
        ring = np.zeros((100, 200), np.uint8)
        cv2.circle(ring, (100, 50), 40, 1, 3)
        self.assertGreater(perception._compact_blob(body), 0.04)
        self.assertEqual(perception._compact_blob(line), 0.0)
        self.assertEqual(perception._compact_blob(ring.astype(bool)), 0.0)


if __name__ == "__main__":
    unittest.main()
