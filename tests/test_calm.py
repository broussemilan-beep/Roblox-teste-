import unittest

from examples.calm import DX, N, build
from tsb_engine.scene import export_viewer_data


class CalmFilmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = build()

    def test_length_and_clock_match_the_reference(self):
        self.assertEqual((self.scene.n_frames, self.scene.fps), (386, 30))
        self.assertEqual(N, 386)

    def test_every_frame_has_a_camera(self):
        for f in range(N):
            self.scene.cine.camera_state(f)

    def test_negative_frames_and_silhouettes_are_where_the_reading_puts_them(self):
        neg = [(s["t0"], s["dur"]) for s in self.scene.cine.screenfx if s["kind"] == "negative"]
        self.assertEqual(neg, [(63, 3), (149, 2), (181, 3), (257, 3), (274, 2)])
        bw = [s["t0"] for s in self.scene.cine.screenfx if s["kind"] == "bw"]
        self.assertEqual(bw, [306, 309])

    def test_sprint_changes_pose_on_almost_every_image(self):
        hero = self.scene.characters[0]
        changed = sum(1 for f in range(73, 239) if hero.world_parts(f)["Right Arm"][0] != hero.world_parts(f - 1)["Right Arm"][0])
        self.assertGreater(changed / 166, 0.9)

    def test_mannequin_stays_far_until_the_slam(self):
        dummy = self.scene.characters[1]
        self.assertAlmostEqual(dummy.world_parts(100)["Torso"][1][0], DX, delta=0.5)

    def test_exports_with_bubbles_and_meshes(self):
        d = export_viewer_data(self.scene)
        self.assertTrue(any(e["type"] == "bubble" for e in d["cine"]["fx"]))
        self.assertIn("ronin_hair", d["meshes"])


if __name__ == "__main__":
    unittest.main()
