"""
Regenerate the packing figures used by README.md and the documentation.

Every figure is a real solve of a small instance in a deterministic mode,
rendered with :mod:`packingsolver3d.visual` -- the same plotly drawing users
get -- and written twice: an interactive HTML fragment (plotly.js from the CDN,
embedded by the docs with ``.. raw:: html``) and a PNG (through kaleido, which
needs a Chrome or Chromium binary) for README.md and static pages.

Example::

    python tools/make_figures.py --output docs/source/_static/figures
"""

import argparse
import os
import sys

from packingsolver3d import BinType, Instance, ItemType, Objective, OptimizationMode, SemiTrailerTruck, box, boxstacks
from packingsolver3d.visual import plot_result

MODE = OptimizationMode.NOT_ANYTIME_DETERMINISTIC


def quick_start():
    """The ten-item bin packing instance of the quick start tutorial."""
    instance = Instance(
        bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
        item_types=[ItemType(x=20, y=30, z=40, copies=6), ItemType(x=15, y=15, z=15, copies=4)],
        objective=Objective.BIN_PACKING,
    )
    return plot_result(box.solve(instance, time_limit=5.0, optimization_mode=MODE),
                       title='box: bin packing, 10 items in one 100x100x100 bin')


def multi_bin():
    """A mixed instance that needs several bins, to show the scene grid."""
    instance = Instance(
        bin_types=[BinType(x=120, y=80, z=100, cost=1, copies=10)],
        item_types=[
            ItemType(x=60, y=40, z=50, copies=6),
            ItemType(x=40, y=40, z=30, copies=8),
            ItemType(x=30, y=20, z=20, copies=12),
            ItemType(x=20, y=20, z=50, copies=6),
        ],
        objective=Objective.BIN_PACKING,
    )
    return plot_result(box.solve(instance, time_limit=10.0, optimization_mode=MODE),
                       title='box: bin packing, four item types over several 120x80x100 bins')


def stacks():
    """The boxstacks tutorial instance, coloured by stack."""
    instance = Instance(
        bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5, maximum_weight=1000, maximum_stack_density=10)],
        item_types=[
            ItemType(x=20, y=30, z=40, copies=6, weight=5, stackability_id=0,
                     maximum_stackability=3, maximum_weight_above=100),
            ItemType(x=30, y=30, z=25, copies=4, weight=8, stackability_id=1,
                     maximum_stackability=2, maximum_weight_above=20),
        ],
        objective=Objective.BIN_PACKING,
    )
    return plot_result(boxstacks.solve(instance, time_limit=5.0, optimization_mode=MODE), color_by='stack',
                       title='boxstacks: two item types, coloured by stack')


def truck():
    """Upstream's semi-trailer truck knapsack instance: axle weights leave one item out."""
    truck_data = SemiTrailerTruck(
        tractor_weight=8000, front_axle_middle_axle_distance=380, front_axle_tractor_gravity_center_distance=100,
        front_axle_harness_distance=320, empty_trailer_weight=6000, harness_rear_axle_distance=800,
        trailer_gravity_center_rear_axle_distance=400, trailer_start_harness_distance=100,
        rear_axle_maximum_weight=20000, middle_axle_maximum_weight=9300,
    )
    instance = Instance(
        bin_types=[BinType(x=1360, y=240, z=260, copies=1, maximum_weight=24000, maximum_stack_density=1000,
                           semi_trailer_truck=truck_data)],
        item_types=[ItemType(x=100, y=200, z=200, copies=3, weight=2000, stackability_id=0, maximum_stackability=1)],
        objective=Objective.KNAPSACK,
    )
    return plot_result(boxstacks.solve(instance, time_limit=5.0, optimization_mode=MODE),
                       title='boxstacks: semi-trailer truck, 2 of 3 items fit the axle limits')


FIGURES = {
    'box_bin_packing': quick_start,
    'box_multi_bin': multi_bin,
    'boxstacks_stacks': stacks,
    'boxstacks_truck': truck,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--output', default=os.path.join('docs', 'source', '_static', 'figures'))
    parser.add_argument('--only', nargs='*', choices=sorted(FIGURES), help='subset of figures to regenerate')
    parser.add_argument('--no-png', action='store_true', help='skip the PNG export (no kaleido / Chrome needed)')
    parser.add_argument('--width', type=int, default=900)
    parser.add_argument('--height', type=int, default=650)
    args = parser.parse_args(argv)

    os.makedirs(args.output, exist_ok=True)
    for name in args.only or sorted(FIGURES):
        figure = FIGURES[name]()
        html = os.path.join(args.output, name + '.html')
        figure.write_html(html, include_plotlyjs='cdn', full_html=False, default_width='100%', default_height='520px')
        print('wrote', html, os.path.getsize(html), 'bytes', flush=True)
        if not args.no_png:
            png = os.path.join(args.output, name + '.png')
            figure.write_image(png, width=args.width, height=args.height, scale=2)
            print('wrote', png, os.path.getsize(png), 'bytes', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
