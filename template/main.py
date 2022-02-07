import logging

import treefiles as tf

from template.meshing import create_data
from template.scene import create_graph
from template.utils import Params, Model


def main():
    out = tf.f(__file__) / "out"
    params = Params.from_file(
        simu_path=out,
        yaml_path=out.p / "params.yaml",
        tree_path=out.p / "main.tree",
    )

    model = Model(create_graph, params)
    create_data(model)
    model.run(gui=True, title="Template scene")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = tf.get_logger()

    main()
