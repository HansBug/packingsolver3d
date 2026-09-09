# Notice

`packingsolver3d` is an **unofficial** Python distribution of two solvers from [PackingSolver](https://github.com/fontanf/packingsolver) by Florian Fontan. It is not affiliated with or endorsed by the upstream project; please report solver behaviour to upstream only after reproducing it with the upstream command-line executables.

## What is redistributed

Every wheel ships one extension module, `packingsolver3d._core`, into which the unmodified upstream libraries `PackingSolver::box` and `PackingSolver::boxstacks` are statically linked together with a thin pybind11 bridge (`packingsolver3d/_core.cpp`). The upstream commit is recorded in `packingsolver3d/config/meta.py` (`__UPSTREAM_COMMIT__`) and vendored as the git submodule `upstream/packingsolver`; it is never patched in this repository, and a required fix is sent upstream as a pull request instead.

## Build configuration

The top-level `CMakeLists.txt` adds the upstream tree with exactly these options: `PACKINGSOLVER_USE_CLP=OFF PACKINGSOLVER_USE_HIGHS=ON PACKINGSOLVER_USE_KNITRO=OFF PACKINGSOLVER_BUILD_MAIN=OFF PACKINGSOLVER_BUILD_TEST=OFF`, in a `Release` configuration with position-independent code. HiGHS is the only linear-programming backend compiled in, which is why every call made by this package sets upstream's `linear_programming_solver_name` to HiGHS. On Windows the upstream targets are switched from the static to the DLL MSVC runtime so the module links against the runtime CPython uses. The solver libraries that upstream pulls in through CMake `FetchContent` (Boost, HiGHS, nlohmann/json, optimizationtools, treesearchsolver, columngenerationsolver, knapsacksolver, multiplechoicesubsetsumsolver, shape, mathoptsolverscmake) are statically linked into the module.

## Licenses

This repository is released under the MIT License (`LICENSE`). PackingSolver is released under the MIT License, reproduced verbatim in `LICENSE-packingsolver`. pybind11 is released under a BSD-style license. The statically linked third-party libraries keep their own licenses; see the corresponding upstream repositories referenced from `upstream/packingsolver/extern/CMakeLists.txt`.
