import pytest
from hbutils.testing import TextAligner

from packingsolver3d import BinType, Defect, Instance, ItemType, Objective


@pytest.fixture(scope="session")
def text_aligner():
    return TextAligner()


@pytest.fixture()
def box_instance():
    """Ten items that fit one 100^3 bin; solved to proven optimality in milliseconds."""
    return Instance(
        bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
        item_types=[
            ItemType(x=20, y=30, z=40, copies=6),
            ItemType(x=15, y=15, z=15, copies=4),
        ],
        objective=Objective.BIN_PACKING,
    )


@pytest.fixture()
def stack_instance():
    """Same shape with stacking rules, so only boxstacks may accept it."""
    return Instance(
        bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5,
                           maximum_weight=1000, maximum_stack_density=10)],
        item_types=[
            ItemType(x=20, y=30, z=40, copies=6, weight=5, stackability_id=0, group_id=0,
                     nesting_height=0, maximum_stackability=3, maximum_weight_above=100),
            ItemType(x=20, y=30, z=40, copies=4, weight=5, stackability_id=0, group_id=0,
                     maximum_stackability=3, maximum_weight_above=100),
        ],
        objective=Objective.BIN_PACKING,
    )


@pytest.fixture()
def defect_instance(stack_instance):
    return Instance(
        bin_types=stack_instance.bin_types,
        item_types=stack_instance.item_types,
        objective=stack_instance.objective,
        defects=[Defect(bin_type_id=0, x=0, y=0, lx=10, ly=10)],
    )
