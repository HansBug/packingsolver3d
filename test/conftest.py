import pytest
from hbutils.testing import TextAligner

from packingsolver3d import BinType, Defect, Instance, ItemType, Objective, Rotation


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


# A 40' HQ container with five cargo types (three carton sizes, loaded EUR pallets, IBC tanks), 1036 items, knapsack:
# more items than fit and a search tree the anytime algorithms do not exhaust, so a solve keeps improving until its time
# limit -- the instance to use when a test needs the solver to still be running when something happens.
_CONTAINER_CARGO = [(530, 290, 370, 300, 8), (530, 230, 290, 300, 6), (430, 210, 270, 400, 4),
                    (1200, 800, 1200, 24, 450), (1200, 1000, 1150, 12, 1100)]


def _container(stacked):
    items = []
    for index, (x, y, z, copies, weight) in enumerate(_CONTAINER_CARGO):
        extra = {'stackability_id': index} if stacked else {}
        items.append(ItemType(x=x, y=y, z=z, copies=copies, weight=weight, rotations=(Rotation.XYZ, Rotation.YXZ), **extra))
    return Instance(
        bin_types=[BinType(x=12032, y=2352, z=2698, copies=1, cost=1, maximum_weight=26460)],
        item_types=items,
        objective=Objective.KNAPSACK,
    )


@pytest.fixture()
def container_instance():
    return _container(False)


@pytest.fixture()
def container_stack_instance():
    return _container(True)
