#!/usr/bin/env bash
# cibuildwheel before-all for Windows, run through Git Bash.  The default
# Visual Studio generator finds MSVC without vcvars, and upstream already pins
# the static CRT (CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded), so the executables
# do not need a redistributable.
set -euo pipefail

PACKAGE="$(cygpath -u "${1:?usage: windows_before_all.sh <package-dir>}")"
cmake --version

exec python "$PACKAGE/tools/build_upstream.py" --jobs "${NUMBER_OF_PROCESSORS:-2}"
