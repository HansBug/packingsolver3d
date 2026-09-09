# packingsolver3d

[![PyPI](https://img.shields.io/pypi/v/packingsolver3d)](https://pypi.org/project/packingsolver3d/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/packingsolver3d)
![Loc](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/HansBug/d0126f7605b5f41d35257f38e15efb7e/raw/loc.json)
![Comments](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/HansBug/d0126f7605b5f41d35257f38e15efb7e/raw/comments.json)

[![Code Test](https://github.com/HansBug/packingsolver3d/workflows/Code%20Test/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Code+Test%22)
[![Release Test](https://github.com/HansBug/packingsolver3d/workflows/Release%20Test/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Release+Test%22)
[![Package Release](https://github.com/HansBug/packingsolver3d/workflows/Release/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Release%22)
[![codecov](https://codecov.io/gh/HansBug/packingsolver3d/branch/main/graph/badge.svg)](https://codecov.io/gh/HansBug/packingsolver3d)

[![GitHub stars](https://img.shields.io/github/stars/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/network)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/HansBug/packingsolver3d)
[![GitHub issues](https://img.shields.io/github/issues/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/issues)
[![GitHub pulls](https://img.shields.io/github/issues-pr/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/pulls)
[![Contributors](https://img.shields.io/github/contributors/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/graphs/contributors)
[![GitHub license](https://img.shields.io/github/license/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/blob/main/LICENSE)

Pythonic bindings for the two three-dimensional solvers of [PackingSolver](https://github.com/fontanf/packingsolver), `box` and `boxstacks`. The upstream C++ is compiled together with a thin pybind11 bridge into one extension module, so a wheel install needs no compiler and every solve runs in-process.

> **Unofficial distribution.** This project is maintained independently of PackingSolver and is not endorsed by its author. The solvers are built unmodified from the upstream commit recorded in `packingsolver3d/config/meta.py`; see [NOTICE.md](NOTICE.md) for the exact build configuration and licensing.

## Scope

PackingSolver covers several problem families. This package deliberately exposes only the two 3D ones:

| Module | Upstream solver | What it adds |
|---|---|---|
| `packingsolver3d.box` | `PackingSolver::box` | Plain 3D bin packing: bins, items, rotations, weight capacity, the full algorithm portfolio as keyword switches |
| `packingsolver3d.boxstacks` | `PackingSolver::boxstacks` | Everything above plus stacks, stackability ids, nesting, maximum weight above, stack density, semi-trailer truck axle weights, defects and unloading constraints |

`rectangle`, `rectangleguillotine`, `onedimensional` and `irregular` are out of scope; use upstream directly for those.

| `box`: ten items in one bin | `boxstacks`: two item types, coloured by stack |
|---|---|
| ![box bin packing](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/figures/box_bin_packing.png) | ![boxstacks stacks](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/figures/boxstacks_stacks.png) |
| `box`: four item types over several bins | `boxstacks`: a semi-trailer truck, axle limits leave one item out |
| ![box multi bin](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/figures/box_multi_bin.png) | ![boxstacks truck](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/figures/boxstacks_truck.png) |

The figures are real solves drawn with `packingsolver3d.visual` (optional dependency `plotly`, `pip install "packingsolver3d[plot]"`), the same drawing upstream's `scripts/visualize_box.py` produces; in the [documentation](https://packingsolver3d.readthedocs.io/en/latest/how_to/visualization/index.html) they are interactive.

## Benchmarks

A small, reproducible capability study is part of the documentation: three public instance families with proven or constructive optima (Egeblad-Pisinger 3D knapsack with 20 items, the Martello-Pisinger-Vigo generator's class 9 with 30 items cut from exactly three bins, and eight Ivancic-Mathur-Mohanty THPACK9 loading instances), run through `box.solve` with a 10 s time limit next to py3dbp, jerry800416/3D-bin-packing, gedex/bp3d, the five 3D strategies of U-Nesting, an exact CP-SAT model and the Martello-Pisinger-Vigo branch-and-bound as references. Every solution, ours and third-party, is re-validated by an independent geometry checker and every objective is recomputed from the placements. Totals over all cases, lower gap is better:

| Participant | EP 3D knapsack, profit (gap to proven optimum) | MPV class 9, bins (optimum 30) | THPACK9, containers (bound 49) |
|---|---|---|---|
| packingsolver3d (PackingSolver `box`) | 15,181,510 (0, all ten proven optimal) | 30 (all ten proven optimal) | 50 (+1, seven of eight proven optimal) |
| py3dbp / jerry800416, rotation relaxed on the first two | 13,752,808 (-9.4%) | 41 (+11) | 79 (+30) |
| gedex/bp3d, rotation relaxed on the first two | 13,352,723 (-12.0%) | 46 (+16) | 81 (+32) |
| U-Nesting SA / ExtremePoint (best of five strategies) | 13,627,093 (-10.2%) | 42 (+12) | 79 (+30) |
| OR-Tools CP-SAT exact model (reference, 20 s) | 15,181,510 (0) | - | - |
| Martello-Pisinger-Vigo 3dbpp.c (reference, 1 s) | - | 40 (+10) | - |

| packingsolver3d: three bins, proven optimal | py3dbp: four bins, rotation relaxed |
|---|---|
| ![ours on MPV class 9](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png) | ![py3dbp on MPV class 9](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png) |

The instances are small and constraint-free, each number is a single run, and the greedy libraries were designed for speed rather than optimality, so this is a capability study, not a ranking of packing software. Sources, versions, the protocol, the full per-case leaderboards and the side-by-side gallery are in the [benchmark section of the documentation](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/index.html); `make benchmarks` regenerates everything from `tools/make_benchmarks.py`.

## Installation

```shell
pip install packingsolver3d
```

Wheels are published for Linux (x86_64, aarch64), macOS (x86_64, arm64) and Windows (AMD64, ARM64), for every CPython the platform has an official build of: 3.7 through 3.14 on Linux x86_64 and Windows AMD64, 3.8 through 3.14 on Linux aarch64 and macOS, 3.11 through 3.14 on Windows ARM64. No compiler is needed for a wheel install. Other architectures (i686, ppc64le, s390x, armv7l, riscv64, loongarch64) are not built as wheels; `pip` falls back to the sdist there. Installing from the sdist compiles PackingSolver and the bridge from the vendored sources and needs CMake >= 3.28, a C++17 compiler and network access for upstream's `FetchContent` dependencies.

## Quick start

```python
from packingsolver3d import BinType, Instance, ItemType, Objective, box

instance = Instance(
    bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
    item_types=[ItemType(x=20, y=30, z=40, copies=6)],
    objective=Objective.BIN_PACKING,
)
result = box.solve(instance, time_limit=2.0)

print(result.status)          # Status.OPTIMAL
print(result.number_of_bins)  # 1
for placement in result.placements:
    print(placement.bin_id, placement.x, placement.y, placement.z, placement.rotation)
```

Stacking rules switch the engine:

```python
from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks

instance = Instance(
    bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5, maximum_weight=1000)],
    item_types=[ItemType(x=20, y=30, z=40, copies=6, weight=5,
                         stackability_id=0, maximum_stackability=3, maximum_weight_above=100)],
    objective=Objective.BIN_PACKING,
)
result = boxstacks.solve(instance, time_limit=2.0)
print(len(result.bins[0].stacks))  # 3
```

Passing that instance to `box.solve` raises `UnsupportedFeatureError` instead of silently dropping the stacking fields, which is what the upstream CSV reader would do.

Any result can be drawn:

```python
from packingsolver3d.visual import plot_result   # needs plotly

figure = plot_result(result, color_by='stack')    # or 'item_type' (default), 'same'
figure.show()                                     # interactive; figure.write_html('packing.html') to save
```

## Design

* **Value in, value out.** Public types are frozen dataclasses. There is no live solver handle, mutable session or callback; each `solve` call builds the upstream instance, runs `optimize()` and copies the best solution back into Python values.
* **No Python object owns C++ memory.** The bridge in `packingsolver3d/_core.cpp` takes plain dicts and returns plain dicts; no upstream object outlives the call.
* **Auditable.** `Result.run` records the problem type, the exact options handed to upstream, upstream's captured log and the wall time.
* **Honest statuses.** `OPTIMAL` requires a solver-reported bound for the requested objective and an achieved value meeting it; otherwise the result is `FEASIBLE`, however good it looks.
* **In-process, by design.** `time_limit` and `memory_limit` are upstream's own checks. There is no process boundary: a crash inside upstream takes the interpreter with it, so callers who need isolation run `solve` in a worker process of their own.

## Behaviours inherited from upstream

packingsolver3d is a faithful binding: it does what PackingSolver does at the pinned commit and does not paper over it. These points were found while building the package; each is backed by an upstream source location or a reproducible observation, and the documentation page [Upstream behaviours you should know](https://packingsolver3d.readthedocs.io/en/latest/explanations/upstream_behaviours/index.html) carries the details.

* **The LP backend is HiGHS and is always set.** Upstream defaults the name to CLP and throws "no linear programming solver found" once column generation starts; the bundled build has HiGHS only.
* **`copies_min` defaults to "all copies".** Upstream's `-1` means every copy is mandatory (none under knapsack); an explicit `0` makes an empty packing the correct bin-packing optimum. `ItemType.copies_min` is therefore `None` unless you mean a minimum.
* **`boxstacks` groups stacks by `(group_id, stackability_id)` without checking footprints**, and its solution builder then throws. `boxstacks.validate` refuses such instances up front with `StackSemanticsError`; give differently shaped items different `stackability_id` values.
* **`boxstacks` keeps items upright.** Only the `XYZ` and `YXZ` rotations are placed; item types allowing neither are refused with `UnsupportedFeatureError`. `box` places all six rotations.
* **`boxstacks` accepts floor defects but places stacks over them** at the pinned commit (observed with corner, interior and full-width defects). `defects` are forwarded faithfully; do not rely on them being avoided.
* **Limits are upstream's own checks and the solver runs in-process.** `time_limit` and `memory_limit` are checked at algorithm checkpoints; there is no hard memory limit and a crash inside upstream ends the interpreter. The [budgets guide](https://packingsolver3d.readthedocs.io/en/latest/how_to/budgets/index.html) shows the worker-process pattern that restores both.
* **Unset profit and cost default to geometry**: item profit to `x * y * z`, bin cost to `x * y` (an area).
* **`OPTIMAL` is only reported when the achieved value meets a bound upstream reported for that objective**; otherwise the result is `FEASIBLE`, however good it looks. Keep `value` and `bound` as two columns when you publish numbers.

## Development

```shell
git clone --recursive https://github.com/HansBug/packingsolver3d.git
cd packingsolver3d
pip install -r requirements-build.txt -r requirements-test.txt -r requirements-cov.txt -r requirements-plot.txt
make build      # compile upstream + the pybind11 bridge into packingsolver3d/_core
make unittest   # pytest + docstring examples, with coverage
make doctest    # only the docstring examples (pytest --doctest-modules)
LINETRACE=1 make build && make unittest   # coverage.xml then also covers the C++ bridge
make rst_auto   # regenerate API reference pages
make docs       # sphinx html
make package    # sdist + wheel
```

`make help` lists every target; `RANGE_DIR=<subdir>` narrows `unittest` and `rst_auto` to one directory.

## License

This repository is released under the [MIT License](LICENSE). PackingSolver is released under the MIT License, reproduced in [LICENSE-packingsolver](LICENSE-packingsolver).
