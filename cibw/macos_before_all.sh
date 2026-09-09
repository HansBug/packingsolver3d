#!/usr/bin/env bash
# cibuildwheel before-all for macOS.  The runner architecture is the wheel
# architecture (asserted by the workflow), so a plain native build suffices.
set -euo pipefail

PACKAGE="${1:?usage: macos_before_all.sh <package-dir>}"

# CMake reads this from the environment; keep one floor for every wheel.
export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}"
cmake --version

exec python "$PACKAGE/tools/build_upstream.py" --jobs "$(sysctl -n hw.ncpu)"
