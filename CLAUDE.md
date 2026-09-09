# CLAUDE.md

`AGENTS.md` and `CLAUDE.md` are the same file via symlink. Edit only one of them and avoid duplicate changes.

## Project Identity

`packingsolver3d` is an unofficial Python distribution of two solvers from [PackingSolver](https://github.com/fontanf/packingsolver) by Florian Fontan: `box` (plain three-dimensional bin packing) and `boxstacks` (three-dimensional packing with stacks, nesting, weight-above, stack density, defects and unloading constraints). Every wheel ships the two upstream executables precompiled; the Python layer is a value-in / value-out façade that writes instance files, runs one subprocess per solve, and parses what comes back.

The package name is deliberate: it names the upstream project, so credit stays with it, and it says `3d` so nobody expects the rectangle, guillotine, one-dimensional or irregular solvers. Adding a fifth problem type is a scope change that needs an explicit decision, not an incremental commit.

The design charter, including the reasoning behind every rule below, lives in `mds/DESIGN_CHARTER.md`. Read it before changing the architecture.

## Hard Boundary: The Upstream Submodule

`upstream/packingsolver/` is a git submodule pinned to the commit recorded as `__UPSTREAM_COMMIT__` in `packingsolver3d/config/meta.py`. It is never patched in this repository. The only permitted change to it is moving the version pointer, and every such move must update `__UPSTREAM_COMMIT__` in the same commit. A fix upstream needs goes to `fontanf/packingsolver` as a pull request; until it lands, adapt the wrapper or document the limitation in the docstring of the affected function.

The readers upstream uses for CSV input match known column labels and ignore unknown ones without a diagnostic. This is why `packingsolver3d.box.validate` refuses instances that carry stacking fields, defects or an unloading constraint instead of letting the `box` executable silently solve a different problem.

## Non-Negotiable Rules

1. **No Python object owns C++ memory.** The only artifacts crossing the process boundary are files and exit statuses. No handle, pointer, buffer view or reference into solver memory is ever exposed.
2. **Value in, value out.** Public models are frozen dataclasses. There is no mutable session, live solver handle or partial-result callback.
3. **Every solve is auditable.** A `Result` always carries its `RunRecord`: argv, exit code, stdout, stderr, wall time, the executable's SHA-256 and whether the wall-clock guard fired. Never drop these to make a result smaller.
4. **A solver-reported bound is never relabelled as proven optimal.** `Status.OPTIMAL` requires a bound reported for the requested objective and an achieved value meeting it. Heuristic incumbent, reported bound and proof are three distinct things; keep them distinct in code, tests and docs.
5. **Never build or ship with both LP backends disabled.** The bundled executables are built with `PACKINGSOLVER_USE_CLP=OFF PACKINGSOLVER_USE_HIGHS=ON`, recorded in `tools/build_upstream.py`, `config/meta.py` (`__LP_SOLVER__`) and `NOTICE.md`. Because upstream defaults the solver name to `CLP` and throws when no matching backend was compiled in, `--linear-programming-solver highs` is passed on every invocation.
6. **Refusals are typed.** Structural problems raise `InvalidInstanceError`, features the chosen solver would drop raise `UnsupportedFeatureError`, a non-zero exit raises `SolverFailedError` with the `RunRecord` attached, and an outrun wall clock raises `SolverTimeoutError`. Nothing returns an empty solution where an error is due.
7. **Resource limits are real.** `time_limit` is forwarded and backed by a wall-clock guard (`time_limit + grace_seconds`); `memory_limit` is forwarded and, on POSIX, enforced as `RLIMIT_AS` on the child through `preexec_fn`.
8. **No broad `except Exception:`.** Name every expected exception class and justify it inline.
9. Code, comments, docstrings, commit messages, issue and pull-request bodies are in English.
10. Python must run on CPython 3.7 through 3.14 on Linux, macOS and Windows.

## Upstream File Contract

These are the columns and sentinels the façade emits; they were verified against the upstream readers at the pinned commit and against live runs. Keep `packingsolver3d/_csv.py` and this table in step.

| File | Columns |
|---|---|
| items | `X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN` plus `ROTATION_XYZ ... ROTATION_ZXY` when any item sets rotations, plus `GROUP_ID,STACKABILITY_ID,NESTING_HEIGHT,MAXIMUM_STACKABILITY,MAXIMUM_WEIGHT_ABOVE` when any item sets one of them |
| bins | `X,Y,Z,COST,COPIES,COPIES_MIN` plus `MAXIMUM_WEIGHT` and `MAXIMUM_STACK_DENSITY` when set |
| defects | `BIN,X,Y,LX,LY` (`boxstacks` only) |
| parameters | `NAME,VALUE`; `box` honours `objective`, `boxstacks` also honours `unloading-constraint` |
| box certificate | `TYPE,ID,COPIES,BIN,X,Y,Z,LX,LY,LZ,ROTATION` |
| boxstacks certificate | `TYPE,ID,COPIES,BIN,STACK,X,Y,Z,LX,LY,LZ,GROUP_ID,ROTATION`, rows end with a trailing comma |

Sentinels that matter: `PROFIT=-1` means "derive from volume", `COST=-1` means "derive from footprint", item `COPIES_MIN=-1` means "all copies mandatory, or none under knapsack" (the reason `ItemType.copies_min` defaults to `None`), `MAXIMUM_STACKABILITY=2147483647` because `ItemPos` is `int32_t` and a 64-bit value wraps negative, and `inf` for unlimited weights because the reader uses `std::stod`.

## Repository Structure

```text
.
|- AGENTS.md -> CLAUDE.md            # symlink; never edit the two separately
|- CLAUDE.md                         # this file
|- README.md                         # unofficial-distribution notice, install, quick start
|- LICENSE                           # this repository, MIT
|- LICENSE-packingsolver             # verbatim upstream MIT
|- NOTICE.md                         # attribution, pinned commit, build options
|- pyproject.toml                    # build-system + [tool.cibuildwheel]
|- setup.py                          # metadata from config/meta.py; platform-tagged wheels; source-install build hook
|- Makefile                          # unified local build / test / package / docs entrypoint
|- pytest.ini
|- requirements.txt                  # runtime: empty on purpose, the package is stdlib-only
|- requirements-build.txt            # setuptools, wheel, build, cmake
|- requirements-test.txt
|- requirements-doc.txt
|- codecov.yml
|- .readthedocs.yaml
|- .gitmodules
|- upstream/packingsolver/           # git submodule -> fontanf/packingsolver, pinned; NEVER patched
|- cibw/                             # cibuildwheel before-all hooks, one per OS
|- tools/build_upstream.py           # CMake configure, build and stage the two executables
|- mds/                              # internal design and plan docs
|- packingsolver3d/
|  |- __init__.py                    # public re-exports
|  |- config/meta.py                 # __VERSION__, __UPSTREAM_COMMIT__, __LP_SOLVER__
|  |- bin/                           # staged executables; build products, gitignored
|  |- model.py                       # Objective, Rotation, ItemType, BinType, Defect, Instance
|  |- result.py                      # Status, Placement, Stack, PackedBin, RunRecord, Result
|  |- errors.py
|  |- _csv.py                        # instance writer + certificate reader
|  |- _runner.py                     # subprocess runner: argv, rlimit, wall clock, RunRecord
|  |- _solve.py                      # shared pipeline: encode, run, decode, classify
|  |- box.py                         # validate() + solve() for packingsolver_box
|  `- boxstacks.py                   # solve() for packingsolver_boxstacks
|- test/                             # pytest; mirrors the package layout; testfile/ holds fixtures
|- docs/                             # sphinx; source/api_doc is generated by `make rst_auto` and committed
`- .github/workflows/
   |- test.yaml                      # native build once per OS, pytest on 3.7-3.14, wheel smoke
   |- release_test.yaml              # full cibuildwheel matrix, no publishing
   |- release.yaml                   # full cibuildwheel matrix + PyPI publish on release
   `- badge.yaml
```

## Where Changes Belong

- A new solver option goes into the keyword arguments of `box.solve` or `boxstacks.solve`, is rendered into argv there, and gets a test asserting the rendered pair.
- A new instance field goes into `model.py`, into the column tables of `_csv.py` with its upstream default as the sentinel, into `box.validate` if `box` would ignore it, and into `test/test_csv.py`.
- Anything about how the executables are located, launched or limited belongs in `_runner.py`.
- Anything about status classification belongs in `_solve._classify` and must keep rule 4.
- Anything about the native build belongs in `tools/build_upstream.py`; the cibw scripts and `setup.py` only call it.

## Local Development

Required tooling: CPython 3.7 to 3.14 (3.12 recommended for development), CMake >= 3.28, a C++14 compiler (GCC 10+, Clang, or MSVC 2022), GNU make, git with submodule support. `pip install -r requirements-build.txt` provides a recent CMake on every platform.

```shell
git clone --recursive https://github.com/HansBug/packingsolver3d.git
cd packingsolver3d
pip install -r requirements-test.txt -r requirements-build.txt -r requirements-doc.txt
make build        # configure + build upstream, stage executables into packingsolver3d/bin
make unittest     # pytest -m unittest with coverage (RANGE_DIR=<subdir> narrows it)
make rst_auto     # regenerate docs/source/api_doc from the package
make docs         # sphinx html into docs/build
make package      # sdist + wheel into dist/
```

`make help` lists every target and variable. `RANGE_DIR`, `COV_TYPES`, `MIN_COVERAGE`, `WORKERS` and `JOBS` are the supported knobs; do not add targets for tooling this repository does not have (there is no logo, no CLI, no PyInstaller build).

Native build notes: the first configure fetches Boost 1.84, HiGHS and six solver libraries through CMake `FetchContent` and needs network access; the build takes several minutes on a workstation. `tools/build_upstream.py` builds only the two `*_main` targets, never the upstream unit tests. The staged executables are gitignored; `make build_clean` removes them and the build tree.

## Packaging and Release

Wheels are built with cibuildwheel from `[tool.cibuildwheel]` in `pyproject.toml`. The executables do not depend on the Python version, so `before-all` builds them once per job and every per-Python wheel of that job reuses them. `setup.py` forces `root_is_pure = False` so wheels carry the platform tag they need, and its `build_py` hook only builds the natives when `packingsolver3d/bin` is empty (a source install) unless `PACKINGSOLVER3D_SKIP_NATIVE_BUILD` is set. The sdist grafts `upstream/packingsolver` minus `data/`, `test/` and `.git` so a source install can build.

Release and Release Test share one matrix: `ubuntu-22.04` (x86_64 native; aarch64, ppc64le, s390x through QEMU), `windows-2022` (AMD64), `macos-14` (arm64), `macos-15-intel` (x86_64), for CPython 3.7 through 3.14, minus 3.7 on macOS. The Python 3.7 jobs deliberately install the last cibuildwheel line that still targets cp37; keep `pip install cibuildwheel` unpinned so each interpreter resolves the line it can run. Runner images are the lowest version still offered, to maximise artifact compatibility. Architectures left out are commented in the matrix with the reason; keep it that way rather than deleting the line.

Tests inside cibuildwheel copy `test/` into a scratch directory before running pytest so the installed wheel, not the source tree, is what gets imported.

## Engineering Expectations

- Preserve upstream terminology: objective tokens, rotation names, option names and column labels are upstream's, verbatim.
- Prefer thin wrappers over opinionated abstractions. If upstream exposes a capability on the command line, expose it faithfully as a keyword argument.
- When behaviour is inherited from upstream rather than decided here, say so in the docstring or test, with the upstream file and function when it is not obvious.
- Do not assume Linux. Paths go through `os.path`, subprocess behaviour and encodings are explicit, `.exe` is appended on Windows, mode bits are restored on POSIX, and `resource` is optional.
- Every published number about solver behaviour must be reproducible from a `RunRecord`; do not report measurements without one.

## Python Code Style

- Compatible with CPython 3.7 through 3.14. No `list[str]` or `X | None` annotations, no `match`, no walrus, no `functools.cached_property`, no `dataclasses(slots=True)`, no `typing.Literal`, no `tomllib`. Use `typing.List`, `Optional`, `Tuple`, `Dict`, `Sequence`.
- `UPPER_SNAKE_CASE` constants, `CapWords` classes, `snake_case` everything else. Module-private helpers start with one underscore; private modules do too (`_csv.py`, `_runner.py`, `_solve.py`).
- Public functions and classes have type annotations and reST docstrings with `:param:`, `:return:`, `:raise:` and, where a short one exists, an `Example::` block that doctest could run.
- Standard library first. The runtime has no third-party dependency and should stay that way. Test code may use `hbutils` (`hbutils.testing.TextAligner` is already a fixture); check `hbutils` before writing a generic helper under `test/`.
- Never `except Exception:`; catch the class you expect and say why.
- Frozen dataclasses for public models; keep `__post_init__` to normalisation such as turning sequences into tuples.

## Testing Rules

- Tests live under `test/`, mirror the package layout, and are marked `@pytest.mark.unittest`. `make unittest` runs only that marker.
- New or changed behaviour comes with tests. A rendered command line option is asserted as an `(option, value)` pair in `RunRecord.argv`; a new column is asserted against the exact header line.
- Tests that run the executables use instances that solve to proven optimality in well under a second; `pytest.ini` sets a 60 s timeout per test. Fixtures for shared instances live in `test/conftest.py`, fixture files in `test/testfile/`.
- Tests must pass on Linux, macOS and Windows. Anything POSIX-only (`RLIMIT_AS`, mode bits) is `skipif`-guarded with the reason.

## Documentation

`docs/source/api_doc/` is generated by `make rst_auto` (`auto_rst.py` per module, `auto_rst_top_index.py` for `api_doc_en.rst` / `api_doc_zh.rst`) and committed, because `sphinx-multiversion` builds each tag from its own checkout. Regenerate after adding or removing a module. `index_en.rst` and `index_zh.rst` are hand-written and must stay in step with each other. `mds/` holds internal plan documents; they are not published.

Markdown paragraphs are written as single lines, not hard-wrapped at a column.

## Commit Message Style

- `type(scope): imperative summary`, lowercase type and scope, no trailing period: `feat(box): expose dual feasible function switch`, `fix(csv): default item copies_min to upstream's -1`, `ci(release): add s390x to the wheel matrix`.
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`. Scopes: `model`, `csv`, `runner`, `solve`, `box`, `boxstacks`, `config`, `tests`, `docs`, `ci`, `packaging`, `upstream`. Omit the scope only when the change spans the whole repository.
- Non-trivial commits get a body: one overview sentence, then `-` bullets for concrete changes, tests, compatibility notes.
- Keep `Co-Authored-By:` trailers when applicable.

## Pull Request Workflow

Branch from `master`, open the pull request against `master`, and keep the body in English with three sections: `## Summary`, `## Changes` (bullets) and `## Validation` (the exact `make` targets run and the workflows that passed). A pull request that moves the upstream submodule pointer states the old and new upstream commits and links the upstream changes it picks up.
