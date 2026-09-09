# Notice

`packingsolver3d` is an **unofficial** Python distribution of two solvers from [PackingSolver](https://github.com/fontanf/packingsolver) by Florian Fontan. It is not affiliated with or endorsed by the upstream project; please report solver behaviour to upstream only after reproducing it with the upstream command-line executables.

## What is redistributed

Every wheel ships two unmodified upstream executables, `packingsolver_box` and `packingsolver_boxstacks`, compiled from the upstream commit recorded in `packingsolver3d/config/meta.py` (`__UPSTREAM_COMMIT__`). The upstream source is vendored as the git submodule `upstream/packingsolver` and is never patched in this repository; a required fix is sent upstream as a pull request instead.

## Build configuration

The executables are built by `tools/build_upstream.py` with exactly these CMake options: `-DCMAKE_BUILD_TYPE=Release -DPACKINGSOLVER_USE_CLP=OFF -DPACKINGSOLVER_USE_HIGHS=ON -DPACKINGSOLVER_USE_KNITRO=OFF -DPACKINGSOLVER_BUILD_MAIN=ON -DPACKINGSOLVER_BUILD_TEST=OFF`. HiGHS is the only linear-programming backend compiled in, which is why every invocation made by this package passes `--linear-programming-solver highs`. The solver libraries that upstream pulls in through CMake `FetchContent` (Boost, HiGHS, optimizationtools, treesearchsolver, columngenerationsolver, knapsacksolver, multiplechoicesubsetsumsolver, shape, mathoptsolverscmake) are statically linked into the executables.

## Licenses

This repository is released under the MIT License (`LICENSE`). PackingSolver is released under the MIT License, reproduced verbatim in `LICENSE-packingsolver`. The statically linked third-party libraries keep their own licenses; see the corresponding upstream repositories referenced from `upstream/packingsolver/extern/CMakeLists.txt`.
