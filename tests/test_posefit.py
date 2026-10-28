import unittest

import numpy as np

from tsb_engine import posefit


class PoseFitTest(unittest.TestCase):
    def truth(self):
        p = np.zeros(16)
        p[0], p[3], p[6] = 270.0, -18.0, 14.0
        p[8], p[10] = -50.0, 55.0     # arms swing
        p[12], p[14] = 40.0, -45.0    # legs split
        return p

    def test_rendered_pose_can_be_recovered_from_its_own_silhouette(self):
        p = self.truth()
        target = posefit.render(p, 64.0, 70.0, 16.0)
        self.assertGreater(int(target.sum()), 300)
        f = posefit.fit_frame(target, None, None, pop=60, iters=24, seed=1)
        self.assertGreater(f.iou, 0.8)

    def test_normalised_mask_is_square_and_centred(self):
        m = np.zeros((200, 300), bool)
        m[40:120, 150:190] = True
        mc, (x0, y0, side) = posefit.normalise_mask(m)
        self.assertEqual(mc.shape, (posefit.CANVAS, posefit.CANVAS))
        ys, xs = np.nonzero(mc)
        self.assertLess(abs((xs.min() + xs.max()) / 2 - posefit.CANVAS / 2), 4)
        self.assertLess(abs((ys.min() + ys.max()) / 2 - posefit.CANVAS / 2), 4)

    def test_sequence_skips_blank_masks(self):
        p = self.truth()
        m = posefit.render(p, 64.0, 70.0, 16.0).astype(bool)
        fits = posefit.fit_sequence([m, np.zeros_like(m), m], restarts=1, pop=40, iters=10)
        self.assertEqual(len(fits), 3)
        self.assertIs(fits[1], fits[0])


if __name__ == "__main__":
    unittest.main()
