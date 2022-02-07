import logging

from MeshObject import Mesh


def create_data(self):
    m0 = Mesh.Sphere(theta_res=20, phi_res=20)
    m0.write(self.simu_tree.mesh_visu)

    m1 = m0.copy()
    m1.tetrahedralize(m0.mmg_options(hmin=0.1, hmax=0.1, hgrad=1, nr=True))
    m1.clip_at_height(0.75, to_polydata=False)
    m1.write(self.simu_tree.mesh_tetra, support_new_type=False)

    # m2 = m0.copy()
    # m2.clip_at_height(0.75, to_polydata=False)
    # m2.convertToPolyData()
    # m2.triangulate(m2.mmg_options(hmin=0.07, hmax=0.07, hgrad=1, nr=True))

    # m3 = m0.copy()
    # m3.triangulate(m3.mmg_options(hmin=0.2, hmax=0.2, hgrad=1, nr=True))
    # m3.write(self.simu_tree.mesh_visu)

    # with tf.PvPlot(shape=(1, 2)) as p:
    #     p.subplot(0, 0)
    #     p.add_mesh(m0.pv.clip("x"), show_edges=True)
    #     p.subplot(0, 1)
    #     p.add_mesh(m1.pv.clip("x"), show_edges=True)
    #     # p.subplot(0, 2)
    #     # p.add_mesh(m2.pv.clip("x"), show_edges=True)
    #     # p.subplot(0, 3)
    #     # p.add_mesh(m3, show_edges=True)


log = logging.getLogger(__name__)
