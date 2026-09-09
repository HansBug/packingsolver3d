#!/usr/bin/env bash
# cibuildwheel before-all for Linux.  Runs once per job inside the manylinux
# container, before any per-Python wheel build, and stages the executables into
# packingsolver3d/bin so every wheel of the job reuses one native build.
set -euo pipefail

PACKAGE="${1:?usage: linux_before_all.sh <package-dir>}"

# Any container CPython is fine for running the build script.
PY="$(ls -d /opt/python/cp3*/bin/python | sort -V | tail -n 1)"

# PackingSolver needs CMake >= 3.28 and older pinned manylinux images ship less;
# the PyPI wheel is the one source available on every architecture.
"$PY" -m venv /tmp/ps3d-tools
/tmp/ps3d-tools/bin/pip install --disable-pip-version-check "cmake>=3.28"
export PATH="/tmp/ps3d-tools/bin:$PATH"
cmake --version

exec "$PY" "$PACKAGE/tools/build_upstream.py" --jobs "$(nproc)"
