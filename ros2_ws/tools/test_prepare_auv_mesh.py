"""Offline conversion checks; run in the mesh conversion environment."""
import unittest
import numpy as np
import trimesh
from prepare_auv_mesh import finish_mesh, simplify_cad_mesh


class MeshFinishTest(unittest.TestCase):
    def test_reduction_preserves_panel_area_and_bounds(self):
        mesh=trimesh.creation.box(extents=(.6,.4,.02))
        reduced=simplify_cad_mesh(mesh,2)
        np.testing.assert_allclose(reduced.bounds,mesh.bounds,atol=.0005)
        self.assertLessEqual(abs(reduced.area-mesh.area)/mesh.area,.015)

    def test_sharp_box_edges_and_degenerate_face(self):
        mesh=trimesh.creation.box(extents=(.6,.4,.2))
        bounds=mesh.bounds.copy()
        mesh.faces=np.vstack((mesh.faces,[0,0,0]))
        result=finish_mesh(mesh)
        self.assertEqual(len(result.faces),12)
        np.testing.assert_allclose(result.bounds,bounds,atol=1e-12)
        dots=np.einsum('ij,ikj->ik',result.face_normals,result.vertex_normals[result.faces])
        self.assertTrue((dots>.999).all())
        self.assertTrue(np.isfinite(result.vertex_normals).all())


if __name__=='__main__':
    unittest.main()
