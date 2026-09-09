# packingsolver3d — Design Charter

Status: draft, pre-implementation. Written 2026-09-09. This document is the agreed scope, naming, architecture and milestone plan; it is not a record of shipped behavior.


> **Amendment (2026-09-09).** The delivery model changed from "bundle the upstream executables and drive them through a subprocess" to "compile upstream together with a pybind11 bridge into one extension module, `packingsolver3d._core`". The value-in / value-out surface, the frozen models, the status rules and the submodule boundary are unchanged; what changed is that every solve now runs in-process, `time_limit` / `memory_limit` are upstream's own checks rather than a wall-clock guard and an `RLIMIT_AS`, and a crash inside upstream is no longer contained by a process boundary. Sections below that describe executables, CSV files, `_runner.py` or `RunRecord.argv` are historical; the tree in section 4 and `CLAUDE.md` are authoritative.

## 1. Scope decision: box **and** boxstacks

The candidate scope reduction "boxstacks only, drop box" is rejected. The measured evidence in the companion research repository (`~/packing-software-study`) points the other way: `box` is the mandatory engine and `boxstacks` is the conditional sidecar.

| Evidence | Source | Consequence |
|:--|:--|:--|
| fork `box` carries every 3D benchmark: B01 `700/700`, B03 `60/60`, B04 `44/44` at mean `15.48` bins, B05 `150/150`, B07 `900/900`, B11 `3/3` | `README.md`, `results/test-summary.md` | `box` is the default placement engine |
| `boxstacks` returns `44/44 ERROR + NO_SOLUTION` on the 44 valid THPACK9/IMM instances at both the 1 s and 10 s budgets, first cause being the stack range check in `SolutionBuilder::add_item` | `report.md:464`, `results/comprehensive/runs/B04-packingsolver-*-boxstacks-*.jsonl` | `boxstacks` cannot consume ordinary multi-item-type input |
| `boxstacks` returns `3/3 ERROR + NO_SOLUTION` on the B11 open-X fixtures while both fork and upstream `box` return `3/3 VALID_COMPLETE` | `report.md:466`, `results/comprehensive/runs/B11-packingsolver.jsonl` | same conclusion on a second, independent input family |
| On the B31 `STACKABLE` fixture `boxstacks` passes while plain `box` violates the maximum-weight-above constraint | `report.md:381` | `boxstacks` is *not* removable either — it is the only engine for the stack/weight-above/axle constraint set |
| `boxstacks::optimize` calls `optimize_box_bound`, which runs the full `box::optimize` | `src/boxstacks/optimize.cpp:158` | the `boxstacks` binary already links the entire `box` solver; shipping both costs one extra CMake target and one extra CLI wrapper, not a second solver |

Therefore the scope is exactly the two 3D problem types. `rectangle`, `rectangleguillotine`, `onedimensional` and `irregular` are out of scope and must not creep in.

Division of labor to be reflected in the public API:

- `box` — closed-bin orthogonal placement, variable-sized bin packing, knapsack, open dimensions. The general engine.
- `boxstacks` — same-base-footprint stacks, stack count limits, nesting, maximum weight above, axle-weight and unloading constraints. Requires the caller's input to carry constructible stack semantics; refuses everything else, and that refusal is a documented, typed error rather than a silent empty solution.

## 2. Package name

**PyPI / import name: `packingsolver3d`.** Repository: `HansBug/packingsolver3d`.

Rationale against the three stated requirements: the upstream token `packingsolver` appears verbatim and unprefixed, so a search for the upstream project finds this package and its attribution; `3d` states precisely which slice of upstream's six problem types is covered. All of `packingsolver`, `pypackingsolver`, `packingsolver-box`, `packingsolver-py` and `boxstacks` are currently unclaimed on PyPI, so the name is available. Fallback if the house `py`-prefix convention is preferred: `pypackingsolver3d`.

Attribution is carried by metadata and documentation, not by the name alone, and is mandatory:

- `LICENSE` (this repository, MIT) plus `LICENSE-packingsolver` (verbatim copy of upstream MIT).
- `NOTICE.md` naming Florian Fontan / `fontanf/packingsolver`, the pinned upstream commit, and the exact CMake options the shipped binaries were built with.
- README first paragraph states plainly that this is an unofficial third-party distribution, links upstream, and lists the four problem types that are *not* included.
- `Project-URL` metadata points at both this repository and upstream.
- Before the first PyPI upload, open a courtesy issue on `fontanf/packingsolver` announcing the package and asking whether the author objects to the name or prefers a different attribution wording.

## 3. Architecture: bundled native binaries behind a pure-Python typed facade

The hard constraint from the outset is that Python must never participate in the C++ side's resource management. Two consequences follow.

**No object-graph binding.** `box::Solution` and `boxstacks::Solution` hold references into their `Instance`. Exposing those objects to Python would push lifetime management into the caller (`py::keep_alive<>` chains, use-after-free if an `Instance` is dropped first). The API is therefore value-in / value-out: the caller passes an immutable description, and receives an immutable result. No Python object ever owns, borrows, or outlives a C++ allocation.

**No in-process extension module for v1.** The solver has four independently confirmed crash or hard-failure paths (the null-`logger` dereference behind `FFOT_LOG*`, the axle-repair out-of-bounds read, the `USE_HIGHS=OFF` runtime throw whose fix was never merged, and the degenerate-truck case now guarded by `SemiTrailerTruckData::check()`). In-process, any of those takes the interpreter down with it. Out of process:

- a crash is an exit code, not a segfault in the host;
- `setrlimit` makes a memory ceiling real, which an in-process binding cannot offer — and the research repository's whole methodology depends on a hard 10 s / 1 GiB gate for PackingSolver subtasks;
- the wheel matrix collapses from roughly 8 Python versions x 5 platforms to 5 platform-only wheels tagged `py3-none-<platform>`, decoupled from CPython releases entirely;
- the coupling is to the CLI and certificate-CSV contract, which has been stable across the whole campaign, rather than to churning C++ headers;
- the certificate parser already exists and is validated in the research repository and can be ported rather than written.

The native side is still fully precompiled into the wheel — the binaries are built during the wheel build and shipped inside the package. Nothing is compiled on the user's machine, and there is no runtime dependency on a system toolchain, CMake, or an LP solver.

An in-process pybind11 layer stays on the table as a later, additive option for callers who need many small solves without process startup cost. It would sit behind the same value-in / value-out facade, so it can be introduced without an API break. It is explicitly not v1 work.

### The process boundary

Input: instance CSVs written to a scratch directory (`--items`, `--bins`, and `--defects` for `boxstacks`). Output: the certificate CSV `TYPE,ID,COPIES,BIN,X,Y,Z,LX,LY,LZ,ROTATION` plus the `--output` JSON statistics file. Every run captures argv, stdout, stderr, exit code, wall time, peak RSS, and the upstream commit and binary SHA-256, and returns them attached to the result.

The two CLIs are not interchangeable and the facade must not pretend otherwise: `box` exposes the algorithm-selection switches (`--use-tree-search`, `--use-sequential-value-correction`, `--use-column-generation`, `--use-dichotomic-search`, `--use-sequential-single-knapsack`, `--use-dual-feasible-functions`, and their queue-size tunables), while `boxstacks` exposes none of them and instead accepts `--unloading-constraint` and `--defects`. Modelling those as one uniform options bag would be a lie about the tool.

### Public API sketch

```python
from packingsolver3d import BinType, ItemType, Objective, box, boxstacks

instance = box.Instance(
    bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
    item_types=[ItemType(x=20, y=30, z=40, copies=10)],
    objective=Objective.BIN_PACKING,
)
result = box.solve(instance, time_limit=10.0, memory_limit="1GiB", seed=42)

result.status          # OPTIMAL | FEASIBLE | NO_SOLUTION | INFEASIBLE_REPORTED | ERROR
result.number_of_bins
result.cost
result.bins            # tuple[PackedBin]; each carries its placements
result.run             # RunRecord: argv, exit code, stdout, stderr, timings, binary hash
```

`Instance`, `BinType`, `ItemType`, `Solution`, `PackedBin` and `Placement` are frozen dataclasses: hashable, picklable, and JSON round-trippable. `boxstacks.Instance` adds the stack, nesting, weight-above, axle and unloading fields, and `boxstacks.solve` raises a typed `StackSemanticsError` carrying upstream's own stderr when the input cannot form valid stacks — the failure the research campaign hit 47 times must surface as a diagnosable error, never as an empty solution.

`status` must keep the research repository's distinction intact: a solver-reported closed bound is `SOLVER_REPORTED_BOUND_CLOSED`, not `PROVEN_OPTIMAL`. The Python layer never upgrades a self-reported bound into a proof.

### Build configuration

Upstream pins all of its dependencies through CMake `FetchContent` (Boost 1.84.0, HiGHS v1.13.1, googletest, optimizationtools, shape, mathoptsolverscmake, knapsacksolver, multiplechoicesubsetsumsolver, treesearchsolver, columngenerationsolver), so a wheel build is self-contained given network access at build time. CLP is not fetched by upstream and is what drags in CoinUtils, LAPACK and bz2.

Open gate, to be resolved in M0 before the build configuration is frozen: whether `-DPACKINGSOLVER_USE_CLP=OFF -DPACKINGSOLVER_USE_HIGHS=ON` covers every code path reachable from `box` and `boxstacks`. No `CLP_FOUND` or `HIGHS_FOUND` guard exists under `src/box` or `src/boxstacks`, but `src/box/optimize.cpp` and both `main.cpp` files reach column generation, which may need an LP backend underneath. **Never build with both backends off**: the compile-time half of the `USE_HIGHS=OFF` failure was merged upstream, the runtime half still throws. Whatever combination is chosen is recorded in `config/meta.py` and in `NOTICE.md`.

## 4. Repository structure

```text
.
|- AGENTS.md -> CLAUDE.md            # symlink; never edit the two separately
|- CLAUDE.md                         # agent-facing engineering charter
|- README.md                         # unofficial-distribution notice, install, quick start, upstream links
|- LICENSE                           # this repository, MIT
|- LICENSE-packingsolver             # verbatim upstream MIT
|- NOTICE.md                         # attribution, pinned commit, build options
|- pyproject.toml                    # build-system + [tool.cibuildwheel]
|- setup.py                          # CMakeExtension: builds upstream + the pybind11 bridge into _core
|- CMakeLists.txt                    # add_subdirectory(upstream/packingsolver) + pybind11_add_module(_core)
|- Makefile                          # unified local build / test / package / docs entrypoint
|- pytest.ini
|- requirements.txt                  # runtime (aim: stdlib only)
|- requirements-build.txt            # cmake, ninja
|- requirements-test.txt
|- requirements-doc.txt
|- codecov.yml
|- .readthedocs.yaml
|- .gitmodules
|- upstream/packingsolver/           # git submodule -> fontanf/packingsolver, pinned; NEVER patched
|- mds/                              # internal design and plan docs (this file)
|- packingsolver3d/
|  |- __init__.py                    # public re-exports
|  |- config/
|  |  |- __init__.py
|  |  `- meta.py                     # __VERSION__, __UPSTREAM_COMMIT__, __LP_SOLVER__
|  |- _core.cpp                      # pybind11 bridge: InstanceBuilder -> optimize() -> plain values
|  |- model.py                       # frozen dataclasses shared by both problem types
|  |- result.py                      # Status, Placement, Stack, PackedBin, RunRecord, Result
|  |- errors.py                      # PackingSolverError, InvalidInstanceError, UnsupportedFeatureError, ...
|  |- _encode.py                     # Instance -> plain payload for the bridge
|  |- _solve.py                      # shared pipeline: encode, call _core, decode, classify
|  |- box.py                         # validate() + solve() for packingsolver_box
|  `- boxstacks.py                   # solve() for packingsolver_boxstacks
|- test/
|  |- __init__.py
|  |- conftest.py
|  |- config/test_meta.py
|  |- test_model.py
|  |- test_csv.py
|  |- test_encode.py
|  |- test_core.py
|  |- test_solve.py
|  |- test_box.py
|  |- test_boxstacks.py
|- docs/
|  |- Makefile
|  `- source/                        # sphinx; api_doc/, index_en.rst, index_zh.rst
`- .github/workflows/
   |- test.yaml                      # build binaries + pytest on the support matrix
   |- release_test.yaml              # cibuildwheel dry run to TestPyPI
   |- release.yaml                   # cibuildwheel + PyPI publish on release
   `- badge.yaml
```

Layout, `setup.py` metadata-via-`config/meta.py`, `requirements-*.txt` groups, `Makefile` entrypoint, `docs/source` with `api_doc` generation, `mds/` for internal plan docs, and the `AGENTS.md -> CLAUDE.md` symlink all follow the conventions already in use in `pyudbm` and `pyfcstm`.

## 5. Non-negotiable rules for CLAUDE.md

1. **Upstream is a submodule and is never patched.** `upstream/packingsolver/` may only move its version pointer. A needed fix goes upstream as a pull request (four are already merged: #540-#543); until it lands, adapt the wrapper or document the limitation.
2. **No Python object owns C++ memory.** The only artifacts crossing the boundary are files and process exit statuses. No handle, pointer, buffer view, or reference into solver memory is ever exposed.
3. **Value-in / value-out.** Public models are frozen dataclasses. There is no mutable session, no live solver handle, no partial-result callback in v1.
4. **Every solve is auditable.** A result always carries argv, exit code, stdout, stderr, timings, the upstream commit, and the binary SHA-256, so any published number can be reproduced.
5. **A solver-reported bound is never relabelled as proven optimal.** Heuristic incumbent, reported bound, and proof are three distinct statuses.
6. **Never build or ship with both LP backends disabled**; the chosen combination is recorded in `config/meta.py` and `NOTICE.md`.
7. **Refusals are typed and carry upstream's own message.** An input `boxstacks` cannot accept raises `StackSemanticsError`; it never returns an empty solution.
8. **Scope is the two 3D problem types.** Adding a fifth problem type is a scope change requiring an explicit decision, not an incremental commit.
9. No broad `except Exception:` — name every expected class and justify it inline, following the same policy as `pyfcstm` and `pyudbm`.
10. Code, comments, docstrings, commit messages, issue and pull-request bodies in English.

## 6. Milestones

| Milestone | Content | Exit criterion |
|:--|:--|:--|
| M0 | Repository skeleton, `CLAUDE.md` + `AGENTS.md` symlink, submodule pinned at the post-merge upstream commit `a7e53303`, `tools/build_upstream.py`, Linux x86_64 CI that builds both executables and runs one smoke solve | the `USE_CLP=OFF USE_HIGHS=ON` question is answered with a recorded experiment, and the build option set is frozen |
| M1 | `model.py`, `_csv.py`, `_process.py`, `box.solve`, golden fixtures ported from the campaign | `box.solve` reproduces the campaign's B11 and B25 results bit-for-bit on the same inputs |
| M2 | `boxstacks.solve`, stack / nesting / weight-above / axle / unloading fields, typed `StackSemanticsError` | the B31 `STACKABLE` fixture passes where plain `box` violates weight-above, and the B04 IMM input raises a diagnosable error rather than returning nothing |
| M3 | `pyproject.toml` cibuildwheel config, five platform wheels (`manylinux_2_17` x86_64 / aarch64, `macosx_11_0_arm64`, `macosx_10_15_x86_64`, `win_amd64`), sdist that builds from the submodule, release workflows, TestPyPI dry run | `pip install packingsolver3d` works in a clean container with no toolchain present, on every published wheel |
| M4 | Sphinx docs (en / zh), `NOTICE.md`, an upstream-parity table stating what is and is not covered, courtesy notice to the upstream author, first PyPI release | published on PyPI and readthedocs |

Note on platform coverage: upstream ships no macOS arm64 release binary, so an arm64 wheel is a genuine addition rather than a repackaging.

## 7. Deliberately out of scope for v1

Pure-Python fallback solver; a mutable solver session or streaming/anytime callbacks; the four non-3D problem types; visualization; an in-process pybind11 extension; a CLI of our own (upstream's is not being replaced).
