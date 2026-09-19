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

## Installation

```shell
pip install packingsolver3d
```

Wheels are published for Linux (x86_64, aarch64), macOS (x86_64, arm64) and Windows (AMD64, ARM64), for every CPython the platform has an official build of: 3.7 through 3.14 on Linux x86_64 and Windows AMD64, 3.8 through 3.14 on Linux aarch64 and macOS, 3.11 through 3.14 on Windows ARM64. No compiler is needed for a wheel install. Other architectures (i686, ppc64le, s390x, armv7l, riscv64, loongarch64) are not built as wheels; `pip` falls back to the sdist there. Installing from the sdist compiles PackingSolver and the bridge from the vendored sources and needs a C++17 compiler, `git`, network access for upstream's `FetchContent` dependencies and CMake 3.28 or newer (installed into the build environment by `pip` where a `cmake` wheel exists). The optional plotting extra pulls in plotly:

```shell
pip install "packingsolver3d[plot]"
```

## Quick start

A 55 x 40 x 23 cm carry-on, the things you would like to take and how much you want each of them. The solver picks the subset with the highest total value that really fits, places every piece, and the result draws itself:

```python
from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, box
from packingsolver3d.visual import plot_result       # needs the plot extra

luggage = {  # name: (x, y, z, value, copies)
    'laptop': (36, 25, 3, 10, 1), 'camera': (15, 10, 8, 9, 1), 'shoes': (30, 20, 12, 8, 1),
    'jacket': (35, 20, 15, 6, 1), 'sweater': (30, 25, 8, 5, 2), 'toiletry bag': (25, 12, 10, 4, 1),
    'hair dryer': (22, 9, 20, 3, 1), 'book': (24, 16, 4, 3, 4), 'souvenir': (10, 10, 10, 2, 6),
    'water bottle': (8, 8, 25, 1, 1),
}
names = list(luggage)
instance = Instance(
    bin_types=[BinType(x=55, y=40, z=23)],
    item_types=[ItemType(x=x, y=y, z=z, profit=value, copies=n, rotations=ALL_ROTATIONS)
                for x, y, z, value, n in luggage.values()],
    objective=Objective.KNAPSACK,                       # maximise the value of what fits
)
result = box.solve(instance, time_limit=3.0)

print(result.status, result.value, result.bound)         # Status.FEASIBLE 69.0 72.0
packed = [0] * len(names)
for placement in result.placements:
    packed[placement.item_type_id] += 1
for name, count in zip(names, packed):
    print(f'{name:13s} {count}/{luggage[name][4]}' + ('' if count == luggage[name][4] else '   <- left out'))

plot_result(result, title='What fits in the carry-on').show()   # rotate, zoom, hover a box for its item type
```

```text
Status.FEASIBLE 69.0 72.0
laptop        1/1
camera        1/1
shoes         1/1
jacket        0/1   <- left out
sweater       2/2
toiletry bag  1/1
hair dryer    1/1
book          4/4
souvenir      6/6
water bottle  1/1
```

[![What fits in the carry-on](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/figures/quick_start_suitcase.png)](https://packingsolver3d.readthedocs.io/en/latest/tutorials/quick_start/index.html)

Everything but the jacket fits, for a value of 69 out of 75. `result.bound` is what the solver proved: no packing is worth more than 72, so the status stays `FEASIBLE` rather than `OPTIMAL` -- the package never relabels a good incumbent as a proven optimum. The figure is interactive in the [documentation](https://packingsolver3d.readthedocs.io/en/latest/tutorials/quick_start/index.html); on another machine the anytime search may leave a different low-value item out.

Stacking rules, weights, trucks and unloading order switch the engine to `boxstacks`:

```python
from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks

pallets = Instance(
    bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5, maximum_weight=1000)],
    item_types=[ItemType(x=20, y=30, z=40, copies=6, weight=5,
                         stackability_id=0, maximum_stackability=3, maximum_weight_above=100)],
    objective=Objective.BIN_PACKING,
)
result = boxstacks.solve(pallets, time_limit=2.0)
print(result.status, result.number_of_bins, len(result.bins[0].stacks))   # Status.OPTIMAL 1 3
```

Passing that instance to `box.solve` raises `UnsupportedFeatureError` instead of silently dropping the stacking fields, which is what the upstream CSV reader would do. Every result can be drawn with `plot_result(result, color_by='stack')`; see the [visualisation guide](https://packingsolver3d.readthedocs.io/en/latest/how_to/visualization/index.html).

Long solves can be watched, and stopped, through `progress_callback`: it is called with a `ProgressEvent` (time, items, bins, profit, cost, upstream's label) on every improvement, and returning `False` ends the solve with the current incumbent (`result.run.stop_reason == 'callback'`). `stop_when_unimproved_for=10.0` ends an anytime solve once ten seconds have passed without a new incumbent (`stop_reason == 'unimproved'`), which is the termination anytime search normally needs on top of a time limit. See the [budgets guide](https://packingsolver3d.readthedocs.io/en/latest/how_to/budgets/index.html).

Not sure how long to wait? `recommend_time_budget(instance, solver='box')` returns a `TimeBudget` -- a `time_limit` that is a loose upper bound plus matching `stop_when_unimproved_*` knobs -- from a model fitted on 3158 recorded improvement curves, one formula per upstream algorithm path (`algorithm_path` tells you which one your instance takes). `alpha` weighs quality against waiting (4 balanced, 8 thorough; the default is 4 for `box` and 8 for `boxstacks`); `speed` rescales for your machine. Pass `**budget.as_options()` to `solve`. The model, a replay of stopping policies (time limit only, stagnation only, both) and guidance for applications are in the docs under *Explanations / How the time budget is estimated*.

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

A reproducible capability study is part of the documentation: 97 cases from three public instance families with known or proven optima (all twenty 20-item Egeblad-Pisinger 3D knapsack instances, thirty Martello-Pisinger-Vigo generator class-9 instances of 30, 60 and 90 items cut from exactly three bins, and all 47 Ivancic-Mathur-Mohanty THPACK9 loading instances), run through `box.solve` with a 10 s time limit next to py3dbp, jerry800416/3D-bin-packing, gedex/bp3d, the five 3D strategies of U-Nesting, an exact CP-SAT model and the Martello-Pisinger-Vigo branch-and-bound as references. Every solution, ours and third-party, is re-validated by an independent geometry checker and every objective is recomputed from the placements. Totals over all cases; a smaller gap is better:

| Participant | EP 3D knapsack, 20 cases: profit (gap to bound) | MPV class 9, 30 cases: bins (bound 90) | THPACK9, 47 cases: containers (bound 655) |
|---|---|---|---|
| packingsolver3d (PackingSolver `box`) | 42,650,877 (-3.4%, all 16 proven optima reached) | 109 (+19, all ten 30-item cuts proven) | 689 (+34, 31 proven) |
| OR-Tools CP-SAT exact model (reference, 20 s) | 42,808,814 (-3.0%, 13 proofs) | - | - |
| jerry800416 / py3dbp, rotation relaxed on the first two | 41,234,099 / 40,933,828 (-6.6% / -7.2%) | 125 (+35) | 822 (+167) |
| gedex/bp3d, rotation relaxed on the first two | 39,480,331 (-10.5%) | 155 (+65) | 890 (+235) |
| U-Nesting, best of five strategies | 37,233,229 (-15.6%, SA) | 139 (+49, ExtremePoint) | 821 (+166, ExtremePoint) |
| Martello-Pisinger-Vigo 3dbpp.c (reference, 1 s) | - | 168 (+78) | - |

| packingsolver3d: three bins, proven optimal | py3dbp: four bins, rotation relaxed |
|---|---|
| [![ours on MPV class 9](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__packingsolver3d.png)](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/gallery/index.html) | [![py3dbp on MPV class 9](https://raw.githubusercontent.com/HansBug/packingsolver3d/main/docs/source/_static/benchmarks/mpv_t9__MPV-GEN-T9-N30-R01__py3dbp.png)](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/gallery/index.html) |

The pictures above are static previews because GitHub cannot run plotly; the [gallery in the documentation](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/gallery/index.html) has the same scenes as rotatable, zoomable figures for our solution and four or five other participants on one case of each benchmark. The instances are small and constraint-free, each number is a single run, and the greedy libraries were designed for speed rather than optimality, so this is a capability study, not a ranking of packing software. Sources, versions, the protocol, the [complete per-case tables](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/leaderboards/index.html) (roster, cases and bounds, leaderboards, items placed, times) and the gallery are in the [benchmark section of the documentation](https://packingsolver3d.readthedocs.io/en/latest/benchmarks/index.html); `make benchmarks` regenerates everything from `tools/make_benchmarks.py`.

## Design

* **Value in, value out.** Public types are frozen dataclasses. There is no live solver handle, mutable session or callback; each `solve` call builds the upstream instance, runs `optimize()` and copies the best solution back into Python values.
* **No Python object owns C++ memory.** The bridge in `packingsolver3d/_core.cpp` takes plain dicts and returns plain dicts; no upstream object outlives the call.
* **Auditable.** `Result.run` records the problem type, the exact options handed to upstream, upstream's captured log and the wall time.
* **Honest statuses.** `OPTIMAL` requires a solver-reported bound for the requested objective and an achieved value meeting it; otherwise the result is `FEASIBLE`, however good it looks.
* **Thread-friendly.** The GIL is released while upstream runs and its log is collected through a per-call stream, not by redirecting `std::cout`, so several threads may solve at once (sixteen concurrent solves are in the test suite).
* **In-process, by design.** `time_limit` and `memory_limit` are upstream's own checks. There is no process boundary: a crash inside upstream takes the interpreter with it, so callers who need isolation run `solve` in a worker process of their own.

## Behaviours inherited from upstream

packingsolver3d is a faithful binding: it does what PackingSolver does at the pinned commit and does not paper over it. These points were found while building the package; each is backed by an upstream source location or a reproducible observation, and the documentation page [Upstream behaviours you should know](https://packingsolver3d.readthedocs.io/en/latest/explanations/upstream_behaviours/index.html) carries the details.

* **The LP backend is HiGHS and is always set.** Upstream defaults the name to CLP and throws "no linear programming solver found" once column generation starts; the bundled build has HiGHS only.
* **`copies_min` defaults to "all copies".** Upstream's `-1` means every copy is mandatory (none under knapsack); an explicit `0` makes an empty packing the correct bin-packing optimum. `ItemType.copies_min` is therefore `None` unless you mean a minimum.
* **`boxstacks` groups stacks by `(group_id, stackability_id)` without checking footprints**, and its solution builder then throws. `boxstacks.validate` refuses such instances up front with `StackSemanticsError`; give differently shaped items different `stackability_id` values.
* **`boxstacks` keeps items upright.** Only the `XYZ` and `YXZ` rotations are placed; item types allowing neither are refused with `UnsupportedFeatureError`. `box` places all six rotations.
* **`boxstacks` accepts floor defects but places stacks over them** at the pinned commit (observed with corner, interior and full-width defects). `defects` are forwarded faithfully; do not rely on them being avoided.
* **Limits are upstream's own checks and the solver runs in-process.** `time_limit` and `memory_limit` are checked at algorithm checkpoints; there is no hard memory limit and a crash inside upstream ends the interpreter. The [budgets guide](https://packingsolver3d.readthedocs.io/en/latest/how_to/budgets/index.html) shows the worker-process pattern that restores both.
* **Anytime mode runs until it is stopped.** In `ANYTIME` mode (the default) the search ends only on the time limit, a stop signal or a proof of optimality; `box` widens its tree search without bound and, since the pinned commit ([fontanf/packingsolver#578](https://github.com/fontanf/packingsolver/pull/578)), so does the single-bin algorithm of `boxstacks`, which in exchange no longer reports a truncated pass when the limit is short. Always pass `time_limit` to anytime solves; without one they do not return on instances that do not pack fully ([fontanf/packingsolver#580](https://github.com/fontanf/packingsolver/issues/580)).
* **Unset profit and cost default to geometry**: item profit to `x * y * z`, bin cost to `x * y` (an area).
* **The `default` objective produces no solution.** It is upstream's unset placeholder, so `Instance` requires an explicit `objective` and `Objective.DEFAULT` is refused with `InvalidInstanceError`.
* **`OPTIMAL` is only reported when the achieved value meets a bound upstream reported for that objective**; otherwise the result is `FEASIBLE`, however good it looks. Keep `value` and `bound` as two columns when you publish numbers.

## Supported platforms

| Platform | Wheels for CPython | Why the range stops where it does |
|---|---|---|
| Linux x86_64 (manylinux) | 3.7 -- 3.14 | full range |
| Linux aarch64 (manylinux) | 3.8 -- 3.14 | no 3.7 build exists for arm64 on the CI toolchain; 3.7 has been end-of-life since 2023 |
| macOS x86_64 and arm64 (11.0+) | 3.8 -- 3.14 | same 3.7 gap |
| Windows AMD64 | 3.7 -- 3.14 | full range |
| Windows ARM64 | 3.11 -- 3.14 | see below |
| everything else (i686, ppc64le, s390x, armv7l, riscv64, loongarch64, PyPy, free-threaded builds) | none | `pip` builds the sdist; see Installation |

**Windows on ARM and older Pythons.** CPython 3.7 and 3.8 never had a Windows ARM64 build at all. 3.9 and 3.10 exist for ARM64 only as python.org's `pythonarm64` nuget package (marked experimental at the time, meant for embedding and CI): there was no installer and no Store package before 3.11, and the CI toolchain (`actions/setup-python`) provides ARM64 hosts from 3.11 on. Wheels for 3.9/3.10 on Windows ARM64 are deliberately not built: the scientific stack does not ship them either (numpy and scipy start at 3.12, pandas at 3.11), 3.9 is end-of-life and 3.10 reaches end-of-life in October 2026, and users of those interpreters on ARM hardware almost always run the x64 build under emulation, which the AMD64 wheels cover. On such a machine `pip` falls back to the sdist, which builds with the MSVC ARM64 toolchain.

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
make try_sdist  # install the sdist from source in a clean docker image and run the unit tests there
```

`make help` lists every target; `RANGE_DIR=<subdir>` narrows `unittest` and `rst_auto` to one directory.

## License

This repository is released under the [MIT License](LICENSE). PackingSolver is released under the MIT License, reproduced in [LICENSE-packingsolver](LICENSE-packingsolver).
