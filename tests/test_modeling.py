import unittest

import numpy as np

from tsb_engine import modeling as M


class ModelingTest(unittest.TestCase):
    def test_primitives_are_closed_and_outward(self):
        cases = {
            "box": (M.bevel_box((2, 2, 1), 0.2), 3.0, 4.0),
            "cyl": (M.cylinder(1, 2, 16), 5.8, 6.3),
            "cone": (M.cone(1, 2, 12), 1.9, 2.1),
            "sphere": (M.sphere(1, 24, 14), 4.0, 4.2),
            "torus": (M.torus(1, 0.2, 32, 12), 0.7, 0.82),
        }
        for name, (m, lo, hi) in cases.items():
            self.assertTrue(lo < m.volume() < hi, f"{name}: volume {m.volume():.3f}")

    def test_sweep_tapers(self):
        m = M.sweep(M.ngon(0.1, 4), [(0, 0, 0), (0, 1, 0), (0, 2, 0.4)], [1.0, 0.7, 0.1])
        self.assertGreater(m.volume(), 0.0)
        self.assertEqual(M.merge([m, m]).stats()["triangles"], 2 * len(m.f))

    def test_obj_round_trip_keeps_faces_and_materials(self):
        m = M.merge([M.bevel_box(color="#112233"), M.cone().translate(0, 1, 0).recolor("#aabbcc")])
        back = M.parse_obj(M.to_obj(m, "x.mtl"))
        self.assertEqual(len(back.f), len(m.f))
        self.assertEqual(back.materials, m.materials)
        self.assertTrue(np.allclose(back.v, m.v, atol=1e-4))
        self.assertIn("newmtl", M.to_mtl(m))

    def test_mirror_keeps_faces_outward(self):
        m = M.cone().translate(1, 0, 0).transform(scale=(-1, 1, 1))
        self.assertGreater(m.volume(), 0.0)

    def test_ronin_kit_is_within_triangle_budget(self):
        from examples.ronin_model import ronin_outfit

        meshes = ronin_outfit(drawn=True).meshes()
        self.assertTrue({"ronin_hair", "ronin_goggles", "ronin_katana_saya"} <= set(meshes))
        for m in meshes.values():
            self.assertTrue(m.stats()["roblox_ok"], m.name)
            self.assertGreater(m.volume(), 0.0, m.name)

    def test_scene_exports_meshes_and_hidden_parts(self):
        from examples.ronin_showcase import build
        from tsb_engine.scene import export_viewer_data

        d = export_viewer_data(build())
        self.assertIn("ronin_hair", d["meshes"])
        names = {e["shape"] for c in d["characters"] for e in c["extras"]}
        self.assertIn("mesh:ronin_hair", names)
        self.assertEqual([c["hide"] for c in d["characters"]], [[], ["Head"]])


if __name__ == "__main__":
    unittest.main()
