import logging

from Sofa.Core import Node

from template.utils import Params, NodeHelper as Nh, BaseFactory, VisualStyle


def create_graph(root: Node, params: Params):
    fa = Factory()
    fa.cfg = lambda x: params[x].value

    root.findData("dt").value = params.dt.value
    root.findData("gravity").value = [0, 0, 0]

    Nh(root).add(*fa.HEADER(VisualStyle.showForceFields, VisualStyle.hideVisualModels))

    meca = root.addChild("meca_node")
    Nh(meca).add(*fa.MECA())
    Nh(meca.addChild("visu_meca")).add(*fa.VISU_MECA())


class Factory(BaseFactory):
    """
    fa = Factory()
    fa.cfg = lambda x: params[x].value
    """

    def HEADER(self, *v):
        lts = dict(color="1 1 0.6 1", attenuation=0, fixed=True)
        return (
            self.DefaultAnimationLoop(),
            self.DefaultVisualManagerLoop(),
            self.VisualStyle(displayFlags=" ".join(v)),
            self.LightManager(),
            self.PositionalLight(position=[0, 0, 300], name=f"light_0", **lts),
            self.PositionalLight(position=[0, 0, -600], name=f"light_1", **lts),
        )

    def MECA(self):
        return (
            self.MeshVTKLoader(name="meca_loader", filename=self.cfg("mesh_tetra")),
            self.EulerImplicitSolver(),
            self.CGLinearSolver(iterations=100, tolerance=1e-7, threshold=1e-7),
            self.MechanicalObject(position="@meca_loader.position"),
            self.TetrahedronSetTopologyContainer(tetrahedra="@meca_loader.tetrahedra"),
            self.TetrahedronSetTopologyModifier(),
            self.TetrahedronSetGeometryAlgorithms(),
            self.TetrahedronHyperelasticityFEMForceField(
                ParameterSet=" ".join(map(str, self.cfg("mat"))),
                materialName=self.cfg("mat_name"),
            ),
            self.DiagonalMass(massDensity=self.cfg("density")),
        )

    def VISU_MECA(self):
        return (
            self.MeshObjLoader(name="visu_loader", filename=self.cfg("mesh_visu")),
            self.OglModel(src="@visu_loader", color="#800000"),
            self.BarycentricMapping(),
        )


log = logging.getLogger(__name__)
