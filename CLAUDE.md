# CLAUDE.md

`AGENTS.md` and `CLAUDE.md` are the same file via symlink. Edit only one of them and avoid duplicate changes.

## Project Identity

`packingsolver3d` is an unofficial Python distribution of two solvers from [PackingSolver](https://github.com/fontanf/packingsolver) by Florian Fontan: `box` (plain three-dimensional bin packing) and `boxstacks` (three-dimensional packing with stacks, nesting, weight-above, stack density, defects and unloading constraints). The upstream C++ libraries are compiled together with a thin pybind11 bridge into one extension module, `packingsolver3d._core`; the Python layer is a value-in / value-out façade that turns a frozen `Instance` into plain values, calls the bridge once, and turns the plain values that come back into a frozen `Result`.

The package name is deliberate: it names the upstream project, so credit stays with it, and it says `3d` so nobody expects the rectangle, guillotine, one-dimensional or irregular solvers. Adding a fifth problem type is a scope change that needs an explicit decision, not an incremental commit.

The design charter, including the reasoning behind every rule below and the amendment that moved the project from bundled executables to an in-process bridge, lives in `mds/DESIGN_CHARTER.md`. Read it before changing the architecture.

## Hard Boundary: The Upstream Submodule

`upstream/packingsolver/` is a git submodule pinned to the commit recorded as `__UPSTREAM_COMMIT__` in `packingsolver3d/config/meta.py`. It is never patched in this repository. The only permitted change to it is moving the version pointer, and every such move must update `__UPSTREAM_COMMIT__` in the same commit. A fix upstream needs goes to `fontanf/packingsolver` as a pull request; until it lands, adapt the bridge or the façade, or document the limitation in the docstring of the affected function.

Build-system adaptations happen from the outside, in the top-level `CMakeLists.txt`: options are forced with `set(... CACHE ... FORCE)` before `add_subdirectory`, and target properties (for example the MSVC runtime) are rewritten after it. Nothing under `upstream/` is edited.

## Non-Negotiable Rules

1. **No Python object owns C++ memory.** The bridge takes plain dicts and returns plain dicts; no upstream object outlives the call, and no handle, pointer, buffer view or reference into solver memory is ever exposed.
2. **Value in, value out.** Public models are frozen dataclasses. There is no mutable session, live solver handle or partial-result callback.
3. **Every solve is auditable.** A `Result` always carries its `RunRecord`: problem type, the exact options handed to the bridge, upstream's captured stdout and stderr, and the wall time. Never drop these to make a result smaller.
4. **A solver-reported bound is never relabelled as proven optimal.** `Status.OPTIMAL` requires a bound reported for the requested objective and an achieved value meeting it. Heuristic incumbent, reported bound and proof are three distinct things; keep them distinct in code, tests and docs.
5. **Never build with both LP backends disabled.** The module is built with `PACKINGSOLVER_USE_CLP=OFF PACKINGSOLVER_USE_HIGHS=ON`, recorded in `CMakeLists.txt`, `config/meta.py` (`__LP_SOLVER__`) and `NOTICE.md`. Because upstream defaults the solver name to `CLP` and throws when no matching backend was compiled in, `linear_programming_solver` is set on every call.
6. **Refusals are typed and carry upstream's own message.** Structural problems raise `InvalidInstanceError`; features the `box` model has no notion of raise `UnsupportedFeatureError`; stackability buckets upstream would assemble and then reject raise `StackSemanticsError`; a `std::invalid_argument` from upstream's `InstanceBuilder` surfaces as `InvalidInstanceError` and any other upstream exception as `SolverFailedError` with the partial `RunRecord` attached. Nothing returns an empty solution where an error is due.
7. **Limits are upstream's.** `time_limit` goes to upstream's timer and `memory_limit` to its own memory check. There is no process boundary: a crash inside upstream takes the interpreter with it, and the docstrings say so. Do not add a hidden subprocess or thread-kill layer; callers who need isolation own their worker process.
8. **No broad `except Exception:`.** Name every expected exception class and justify it inline; in the bridge, let pybind11 translate `std::exception` rather than catching it.
9. Code, comments, docstrings, commit messages, issue and pull-request bodies are in English.
10. Python must run on CPython 3.7 through 3.14 on Linux, macOS and Windows; the bridge must compile with GCC 10+, Clang and MSVC 2022 as C++17.

## Bridge Contract

`packingsolver3d._core` exposes `box_solve(instance, options)` and `boxstacks_solve(instance, options)`. Both take the payload built by `packingsolver3d._encode.instance_payload` and the options built by `packingsolver3d._solve.core_options`, and return `{"output": <upstream Output JSON as a string>, "stdout": str, "stderr": str, "bins": [...]}`. Keep the three pieces in step.

| Payload key | Content |
|---|---|
| `objective` | upstream token, e.g. `bin-packing`, `knapsack`, `default` |
| `bins` | dicts with `x, y, z` plus any of `cost, copies, copies_min, maximum_weight, maximum_stack_density` |
| `items` | dicts with `x, y, z` plus any of `profit, weight, copies, copies_min, rotations, group_id, stackability_id, nesting_height, maximum_stackability, maximum_weight_above` |
| `defects` | dicts with `bin_type_id, x, y, lx, ly` (`boxstacks` only) |
| `unloading_constraint` | upstream token or `None` (`boxstacks` only) |

A key that is absent is not set on the builder, so upstream's own default applies -- the same default its CSV readers use when a column is missing. `copies_min` is therefore `None` on `ItemType`: upstream's `-1` means "every copy is mandatory, except under knapsack where none is", and an explicit `0` makes bin packing return zero bins as the true optimum. Rotation tokens are `XYZ, YXZ, ZYX, YZX, XZY, ZXY`; the bridge computes placed extents from upstream's `ItemType::x(Rotation)` tables. Returned bins carry `bin_type_id, copies, x, y, z, placements, stacks`; placements carry `item_type_id, x, y, z, lx, ly, lz, rotation` plus `stack_id, group_id` for `boxstacks`; stacks carry `stack_id, x, y, lx, ly, lz`.

Two upstream behaviours are encoded in the façade rather than hidden: `tree_search.cpp` buckets item types by `(group_id, stackability_id)` without comparing footprints and `SolutionBuilder::add_item` then throws, so `boxstacks.validate` refuses buckets with no footprint in common (rotation-aware); and at the pinned commit `boxstacks` reads defects but places stacks over them, which the docstrings state and the tests only assert acceptance for.

## Repository Structure

```text
.
|- AGENTS.md -> CLAUDE.md            # symlink; never edit the two separately
|- CLAUDE.md                         # this file
|- README.md                         # unofficial-distribution notice, install, quick start
|- LICENSE                           # this repository, MIT
|- LICENSE-packingsolver             # verbatim upstream MIT
|- NOTICE.md                         # attribution, pinned commit, build options
|- CMakeLists.txt                    # add_subdirectory(upstream) + pybind11_add_module(_core)
|- pyproject.toml                    # build-system (setuptools, pybind11, cmake) + [tool.cibuildwheel]
|- setup.py                          # metadata from config/meta.py; CMakeExtension driving CMakeLists.txt
|- Makefile                          # unified local build / test / package / docs entrypoint
|- pytest.ini
|- requirements.txt                  # runtime: empty on purpose, the package is stdlib-only
|- requirements-build.txt            # setuptools, wheel, build, cmake, pybind11
|- requirements-test.txt
|- requirements-doc.txt
|- codecov.yml
|- .readthedocs.yaml
|- .gitmodules
|- upstream/packingsolver/           # git submodule -> fontanf/packingsolver, pinned; NEVER patched
|- mds/                              # internal design and plan docs
|- packingsolver3d/
|  |- __init__.py                    # public re-exports
|  |- _core.cpp                      # pybind11 bridge: InstanceBuilder -> optimize() -> plain values
|  |- config/meta.py                 # __VERSION__, __UPSTREAM_COMMIT__, __LP_SOLVER__
|  |- model.py                       # Objective, Rotation, ItemType, BinType, Defect, Instance
|  |- result.py                      # Status, Placement, Stack, PackedBin, RunRecord, Result
|  |- errors.py
|  |- _encode.py                     # Instance -> payload, structural validation
|  |- _solve.py                      # shared pipeline: encode, call _core, decode, classify
|  |- box.py                         # validate() + solve() for PackingSolver::box
|  `- boxstacks.py                   # validate() + solve() for PackingSolver::boxstacks
|- test/                             # pytest; mirrors the package layout
|- docs/                             # sphinx; source/api_doc is generated by `make rst_auto` and committed
`- .github/workflows/
   |- test.yaml                      # build _core + pytest on 3.7-3.14 per OS (cached CMake tree), wheel smoke
   |- release_test.yaml              # full cibuildwheel matrix, no publishing
   |- release.yaml                   # full cibuildwheel matrix + PyPI publish on release
   `- badge.yaml
```

The built module (`packingsolver3d/_core.*.so` / `.pyd`) and the CMake tree (`build/cmake`) are build products and gitignored.

## Where Changes Belong

- A new solver option is a keyword argument of `box.solve` or `boxstacks.solve`, a key in the options dict, a `set_switch` / `read` call in `_core.cpp`, and a test asserting `result.run.options[...]`.
- A new instance field goes into `model.py`, into `_encode.py` (payload key and validation), into the builder calls in `_core.cpp`, into `box.validate` if the `box` model has no notion of it, and into `test/test_encode.py` plus `test/test_core.py`.
- Anything about status classification belongs in `_solve._classify` and must keep rule 4.
- Anything about how upstream is configured or linked belongs in `CMakeLists.txt`; `setup.py` only drives it and `pyproject.toml` only lists what the isolated build needs.

## Local Development

Required tooling: CPython 3.7 to 3.14 (3.12 recommended for development), CMake >= 3.28, a C++17 compiler (GCC 10+, Clang, or MSVC 2022), GNU make, git with submodule support. `pip install -r requirements-build.txt` provides CMake and pybind11 on every platform.

```shell
git clone --recursive https://github.com/HansBug/packingsolver3d.git
cd packingsolver3d
pip install -r requirements-build.txt -r requirements-test.txt -r requirements-doc.txt
make build        # cmake configure + build of upstream and the bridge, module placed in packingsolver3d/
make unittest     # pytest -m unittest with coverage (RANGE_DIR=<subdir> narrows it)
make rst_auto     # regenerate docs/source/api_doc from the package
make docs         # sphinx html into docs/build
make package      # sdist + wheel into dist/
```

`make help` lists every target and variable. `RANGE_DIR`, `COV_TYPES`, `MIN_COVERAGE`, `WORKERS` and `JOBS` are the supported knobs; do not add targets for tooling this repository does not have (there is no logo, no CLI, no PyInstaller build).

Native build notes: the first configure fetches Boost, HiGHS and six solver libraries through CMake `FetchContent` and needs network access; the build takes several minutes on a workstation. The CMake tree lives in `build/cmake` (override with `PACKINGSOLVER3D_BUILD_DIR`) and is reused across interpreters: `setup.py` drops the cached `Python_*` / `pybind11_*` entries before each configure so switching interpreters only rebuilds the bridge. `make build_clean` removes the tree and the module. `CMAKE_GENERATOR`, `CMAKE_BUILD_PARALLEL_LEVEL` and `PACKINGSOLVER3D_CMAKE_ARGS` are honoured.

## Packaging and Release

Wheels are built with cibuildwheel from `[tool.cibuildwheel]` in `pyproject.toml`; the isolated build environment gets `pybind11` and `cmake` from `[build-system].requires`, and `setup.py` drives `CMakeLists.txt`. Within one cibuildwheel job the shared `build/cmake` tree means the first wheel pays for upstream and the other seven pay for the bridge only; keep that property when touching `setup.py`. auditwheel and delocate repair `_core` like any other extension module. The sdist grafts `upstream/packingsolver` minus `data/`, `test/` and `.git` so a source install can build.

Release and Release Test share one matrix: `ubuntu-22.04` (x86_64 native; aarch64, ppc64le, s390x through QEMU), `windows-2022` (AMD64), `macos-14` (arm64), `macos-15-intel` (x86_64), for CPython 3.7 through 3.14, minus 3.7 on macOS. The Python 3.7 jobs deliberately install the last cibuildwheel line that still targets cp37; keep `pip install cibuildwheel` unpinned so each interpreter resolves the line it can run. Runner images are the lowest version still offered, to maximise artifact compatibility. Architectures left out are commented in the matrix with the reason; keep it that way rather than deleting the line.

Tests inside cibuildwheel copy `test/` into a scratch directory before running pytest so the installed wheel, not the source tree, is what gets imported.

## Engineering Expectations

- Preserve upstream terminology: objective tokens, rotation names, option names and field names are upstream's, verbatim, parsed through upstream's own stream operators in the bridge.
- Prefer thin wrappers over opinionated abstractions. If upstream exposes a parameter, expose it faithfully as a keyword argument.
- When behaviour is inherited from upstream rather than decided here, say so in the docstring or test, with the upstream file and function when it is not obvious.
- Do not assume Linux. Paths go through `os.path`, encodings are explicit, and the bridge has no platform-specific code.
- Every published number about solver behaviour must be reproducible from a `RunRecord`; do not report measurements without one.

## Python Code Style

- Compatible with CPython 3.7 through 3.14. No `list[str]` or `X | None` annotations, no `match`, no walrus, no `functools.cached_property`, no `dataclasses(slots=True)`, no `typing.Literal`, no `tomllib`. Use `typing.List`, `Optional`, `Tuple`, `Dict`, `Sequence`.
- `UPPER_SNAKE_CASE` constants, `CapWords` classes, `snake_case` everything else. Module-private helpers start with one underscore; private modules do too (`_encode.py`, `_solve.py`, `_core`).
- Public functions and classes have type annotations and reST docstrings with `:param:`, `:return:`, `:raise:` and, where a short one exists, an `Example::` block that doctest could run.
- Standard library first. The runtime has no third-party dependency and should stay that way. Test code may use `hbutils` (`hbutils.testing.TextAligner` is already a fixture); check `hbutils` before writing a generic helper under `test/`.
- Never `except Exception:`; catch the class you expect and say why.
- Frozen dataclasses for public models; keep `__post_init__` to normalisation such as turning sequences into tuples.

## C++ Style for the Bridge

- `_core.cpp` stays a bridge: it builds upstream objects, calls upstream, and copies results out. No solving logic, no caching, no state between calls.
- Use upstream's types (`Length`, `BinPos`, `ItemTypeId`, ...) and upstream's stream operators for tokens; never re-implement a parser upstream already has.
- Release the GIL around `optimize()` and touch no Python object while it is released.
- Capture `std::cout` / `std::cerr` for the duration of the call only, restored by RAII on every exit path.
- Comments explain why, in English, and reference the upstream file when a workaround exists because of it.

## Testing Rules

- Tests live under `test/`, mirror the package layout, and are marked `@pytest.mark.unittest`. `make unittest` runs only that marker.
- New or changed behaviour comes with tests. A forwarded option is asserted in `result.run.options`; a payload change is asserted against the exact dict in `test/test_encode.py`; a bridge change is asserted through `test/test_core.py` on plain values.
- Tests that run the solver use instances that solve to proven optimality in well under a second; `pytest.ini` sets a 60 s timeout per test. Shared instances are fixtures in `test/conftest.py`.
- Tests must pass on Linux, macOS and Windows without platform guards; there is nothing POSIX-specific left to guard.

## Documentation

`docs/source/api_doc/` is generated by `make rst_auto` (`auto_rst.py` per module, `auto_rst_top_index.py` for `api_doc_en.rst` / `api_doc_zh.rst`) and committed, because `sphinx-multiversion` builds each tag from its own checkout. Regenerate after adding or removing a module, and delete the page of a removed module by hand. `index_en.rst` and `index_zh.rst` are hand-written and must stay in step with each other. `mds/` holds internal plan documents; they are not published.

Markdown paragraphs are written as single lines, not hard-wrapped at a column.

## Commit Message Style

- `type(scope): imperative summary`, lowercase type and scope, no trailing period: `feat(box): expose dual feasible function switch`, `fix(encode): default item copies_min to upstream's -1`, `ci(release): add s390x to the wheel matrix`.
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`. Scopes: `model`, `encode`, `solve`, `core`, `box`, `boxstacks`, `config`, `tests`, `docs`, `ci`, `packaging`, `cmake`, `upstream`. Omit the scope only when the change spans the whole repository.
- Non-trivial commits get a body: one overview sentence, then `-` bullets for concrete changes, tests, compatibility notes.
- Keep `Co-Authored-By:` trailers when applicable.

## Pull Request Workflow

Branch from `master`, open the pull request against `master`, and keep the body in English with three sections: `## Summary`, `## Changes` (bullets) and `## Validation` (the exact `make` targets run and the workflows that passed). A pull request that moves the upstream submodule pointer states the old and new upstream commits and links the upstream changes it picks up.
