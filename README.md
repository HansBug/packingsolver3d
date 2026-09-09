# packingsolver3d

[![PyPI](https://img.shields.io/pypi/v/packingsolver3d)](https://pypi.org/project/packingsolver3d/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/packingsolver3d)

[![Code Test](https://github.com/HansBug/packingsolver3d/workflows/Code%20Test/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Code+Test%22)
[![Release Test](https://github.com/HansBug/packingsolver3d/workflows/Release%20Test/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Release+Test%22)
[![Package Release](https://github.com/HansBug/packingsolver3d/workflows/Release/badge.svg)](https://github.com/HansBug/packingsolver3d/actions?query=workflow%3A%22Release%22)
[![codecov](https://codecov.io/gh/HansBug/packingsolver3d/branch/master/graph/badge.svg)](https://codecov.io/gh/HansBug/packingsolver3d)

[![GitHub stars](https://img.shields.io/github/stars/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/network)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/HansBug/packingsolver3d)
[![GitHub issues](https://img.shields.io/github/issues/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/issues)
[![GitHub pulls](https://img.shields.io/github/issues-pr/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/pulls)
[![Contributors](https://img.shields.io/github/contributors/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/graphs/contributors)
[![GitHub license](https://img.shields.io/github/license/HansBug/packingsolver3d)](https://github.com/HansBug/packingsolver3d/blob/master/LICENSE)

Pythonic bindings for the two three-dimensional solvers of [PackingSolver](https://github.com/fontanf/packingsolver), `box` and `boxstacks`. The upstream C++ is compiled together with a thin pybind11 bridge into one extension module, so a wheel install needs no compiler and every solve runs in-process.

> **Unofficial distribution.** This project is maintained independently of PackingSolver and is not endorsed by its author. The solvers are built unmodified from the upstream commit recorded in `packingsolver3d/config/meta.py`; see [NOTICE.md](NOTICE.md) for the exact build configuration and licensing.

## Scope

PackingSolver covers several problem families. This package deliberately exposes only the two 3D ones:

| Module | Upstream solver | What it adds |
|---|---|---|
| `packingsolver3d.box` | `PackingSolver::box` | Plain 3D bin packing: bins, items, rotations, weight capacity, the full algorithm portfolio as keyword switches |
| `packingsolver3d.boxstacks` | `PackingSolver::boxstacks` | Everything above plus stacks, stackability ids, nesting, maximum weight above, stack density, defects and unloading constraints |

`rectangle`, `rectangleguillotine`, `onedimensional` and `irregular` are out of scope; use upstream directly for those.

## Installation

```shell
pip install packingsolver3d
```

Wheels are published for CPython 3.7 through 3.14 on Linux (x86_64, aarch64, ppc64le, s390x), macOS (x86_64, arm64) and Windows (AMD64). No compiler is needed for a wheel install. Installing from the sdist compiles PackingSolver and the bridge from the vendored sources and needs CMake >= 3.28, a C++17 compiler and network access for upstream's `FetchContent` dependencies.

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

## Design

* **Value in, value out.** Public types are frozen dataclasses. There is no live solver handle, mutable session or callback; each `solve` call builds the upstream instance, runs `optimize()` and copies the best solution back into Python values.
* **No Python object owns C++ memory.** The bridge in `packingsolver3d/_core.cpp` takes plain dicts and returns plain dicts; no upstream object outlives the call.
* **Auditable.** `Result.run` records the problem type, the exact options handed to upstream, upstream's captured log and the wall time.
* **Honest statuses.** `OPTIMAL` requires a solver-reported bound for the requested objective and an achieved value meeting it; otherwise the result is `FEASIBLE`, however good it looks.
* **In-process, by design.** `time_limit` and `memory_limit` are upstream's own checks. There is no process boundary: a crash inside upstream takes the interpreter with it, so callers who need isolation run `solve` in a worker process of their own.

## Development

```shell
git clone --recursive https://github.com/HansBug/packingsolver3d.git
cd packingsolver3d
pip install -r requirements-test.txt -r requirements-build.txt
make build      # compile upstream + the pybind11 bridge into packingsolver3d/_core
make unittest   # pytest with coverage
make rst_auto   # regenerate API reference pages
make docs       # sphinx html
make package    # sdist + wheel
```

`make help` lists every target; `RANGE_DIR=<subdir>` narrows `unittest` and `rst_auto` to one directory.

## License

This repository is released under the [MIT License](LICENSE). PackingSolver is released under the MIT License, reproduced in [LICENSE-packingsolver](LICENSE-packingsolver).
