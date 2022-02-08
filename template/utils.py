import json
import logging
import os
import re
from typing import Callable
from typing import List

import treefiles as tf
from Sofa import Simulation
from Sofa.Core import Node
from Sofa.Gui import GUIManager
from SofaRuntime.SofaRuntime import importPlugin
from treefiles.baseio_.param import r

PLUGINS = {
    # "SofaOpenglVisual",
    "SofaMiscFem",
    "SofaGraphComponent",
    "SofaGeneralLoader",
    "SofaImplicitOdeSolver",
    "SofaExporter",
    "SofaOpenglVisual",
    "SofaDeformable",
    "SofaMeshCollision",
    "SofaSimpleFem",
}


def import_plugins(*args):
    pl = set(PLUGINS)
    for x in args:
        pl.add(x)
    for x in pl:
        importPlugin(x)


def rou(x, k=2):
    if isinstance(x, str):
        return x
    elif isinstance(x, (int, float)):
        return round(x, k)


class Param(tf.Param):
    def __init__(self, *args, parents: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parents = tf.none(parents, ("DEFAULT",))
        self.registered.add("parents")

    @property
    def table(self):
        return Params(self).table

    show = table

    @property
    def parentname(self) -> str:
        return f"{'.'.join(self.parents+[self.name])}"

    def __call__(self, value=None, **kwargs):
        self.value = value
        for k, v in kwargs.items():
            if k in self.registered:
                setattr(self, k, v)
        return self

    def __eq__(self, other):
        if isinstance(other, Param):
            return self.value == other.value
        return self.value == other


class InvalidParam(Param):
    def __init__(self, *args, **kwargs):
        super().__init__(None, *args, **kwargs)


class DefaultParam(Param):
    def __call__(self, value=None, **kwargs):
        obj = self.copy()
        obj.value = value
        for k, v in kwargs.items():
            if k in self.registered:
                setattr(obj, k, v)
        return obj


class Params(tf.Params[str, Param]):
    def __init__(self, *items, tree_path: str = None, simu_path: str = None):
        super().__init__(*items)

        self.simu_tree = None
        if tree_path is not None:
            self.simu_tree = tf.Tree.from_file(tree_path)
            self.simu_tree.root = tf.none(simu_path, tf.basename(tree_path))
            self.simu_tree.dump()

            for x in self.simu_tree.get_file_keys():
                self[x] = Param(x, getattr(self.simu_tree, x))

    @classmethod
    def from_file(cls, yaml_path: str, **kwargs):
        return cls(flatten(tf.load_yaml(yaml_path)), **kwargs)

    def build_table(self):
        def pts(x):
            m = re.search(r"(.+)\.", x)
            return m.group(1) if m else ""

        header = ["Parents", "Name", "Value", "Initial value", "Bounds", "Unit"]
        data = [
            [
                pts(x.parentname),
                x.name,
                rou(x.value),
                x.initial_value,
                x.bounds,
                x.unit,
            ]
            for x in self.values()
        ]
        return header, data

    def __getitem__(self, item):
        cand = [
            x.copy()
            for x in self.values()
            if len(x.parents) > 0 and x.parents[0] == item
        ]
        if len(cand) > 0:
            for x in cand:
                x.parents = x.parents[1:]
            return Params(cand)
        else:
            return super().__getitem__(item)

    def to_yaml(self):
        d = {}
        for x in self.values():
            p = d
            for k in x.parents:
                p = p.setdefault(k, {})
            if isinstance(x.value, tf.Tree):
                x.value = x.value.abs()
            p.update({x.name: x.value})
        return json.loads(json.dumps(d, cls=tf.NumpyEncoder))


def flatten(d, parents=None):
    if parents is None:
        parents = []
    items = []
    for k, v in d.items():
        new_parents = parents + [k]
        if isinstance(v, dict):
            items.extend(flatten(v, new_parents))
        else:
            try:
                v = float(v)
            except (TypeError, ValueError):
                pass
            items.append(Param(new_parents[-1], v, parents=new_parents[:-1]))
    return items


class Model:
    def __init__(self, graph: Callable, params: Params):
        self.graph = graph
        self.params = params
        self.root = None

    @property
    def simu_tree(self):
        return self.params.simu_tree

    def init_scene(self, plugins=None, **k):
        import_plugins(*tf.none(plugins, tuple()))

        self.root = Node("root")
        self.graph(self.root, self.params, **k)
        Simulation.init(self.root)

    def print_scene(self):
        Simulation.print(self.root)

    @tf.timer
    def run(
        self,
        gui: bool = False,
        cb_begin: Callable = None,
        cb_end: Callable = None,
        title: str = tf.get_timestamp(),
        plugins=None,
    ):
        assert (
            "SOFA_ROOT" in os.environ
        ), "Add 'SOFA_ROOT' to your environment variables"

        tf.dump_yaml(self.params.simu_tree.params, self.params.to_yaml())

        if self.root is None:
            self.init_scene(plugins=plugins)

        if gui:
            GUIManager.Init("")
            GUIManager.createGUI(self.root, title)
            GUIManager.SetDimension(900, 700)
            gui = GUIManager.GetGUI()
            gui.setBackgroundImage(tf.f(__file__) / "SOFA_logo_white.dds"),
            GUIManager.MainLoop(self.root)
            GUIManager.closeGUI()
        else:

            for i in range(self.params.n.value):
                if cb_begin is not None:
                    cb_begin(i, self.root)

                Simulation.animate(self.root, self.params.dt.value)

                if cb_end is not None:
                    cb_end(i, self.root)

                # access graph data: self.root["Node.Component"].findData("Data").value


class NodeHelper:
    def __init__(self, node: Node):
        self.node = node

    def add(self, *objs):
        for obj in objs:
            self.node.addObject(obj[0], **obj[1])
        return self.node


class BaseFactory:
    def __getattr__(self, item):
        if item[0] == item[0].upper():

            def w_(**kw):
                return item, kw

            return w_


class VisualStyle:
    showAll = "showAll"
    hideAll = "hideAll"
    showVisual = "showVisual"
    hideVisual = "hideVisual"
    showVisualModels = "showVisualModels"
    hideVisualModels = "hideVisualModels"
    showBehavior = "showBehavior"
    hideBehavior = "hideBehavior"
    showBehaviorModels = "showBehaviorModels"
    hideBehaviorModels = "hideBehaviorModels"
    showForceFields = "showForceFields"
    hideForceFields = "hideForceFields"
    showInteractionForceFields = "showInteractionForceFields"
    hideInteractionForceFields = "hideInteractionForceFields"
    showMapping = "showMapping"
    hideMapping = "hideMapping"
    showMappings = "showMappings"
    hideMappings = "hideMappings"
    showMechanicalMappings = "showMechanicalMappings"
    hideMechanicalMappings = "hideMechanicalMappings"
    showCollision = "showCollision"
    hideCollision = "hideCollision"
    showCollisionModels = "showCollisionModels"
    hideCollisionModels = "hideCollisionModels"
    showBoundingCollisionModels = "showBoundingCollisionModels"
    hideBoundingCollisionModels = "hideBoundingCollisionModels"
    showOptions = "showOptions"
    hideOptions = "hideOptions"
    showNormals = "showNormals"
    hideNormals = "hideNormals"
    showWireframe = "showWireframe"
    hideWireframe = "hideWireframe"


log = logging.getLogger(__name__)
