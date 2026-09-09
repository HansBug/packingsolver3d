#!/usr/bin/env bash
# Install an sdist from source inside a clean container and run the unit tests against the installed package.
#
# Usage: tools/try_sdist.sh <image> <sdist.tar.gz> [extra docker-run arguments...]
#
# The container gets only what a user's machine would have: a compiler, git and Python; pip builds the
# extension from the tarball (CMake and pybind11 come from the build requirements). The tests are copied
# out of the tarball into a scratch directory so the installed package, not the unpacked sources, is what
# gets imported -- the same arrangement cibuildwheel uses for the wheels.
set -euo pipefail

IMAGE=$1
SDIST=$(realpath "$2")
shift 2
ROOT=$(cd "$(dirname "$0")/.." && pwd)

case "$IMAGE" in
    *alpine*)
        SETUP='apk add --no-cache build-base linux-headers git' ;;
    ubuntu*|debian:*)
        SETUP='export DEBIAN_FRONTEND=noninteractive && apt-get update -qq && apt-get install -y -qq --no-install-recommends python3 python3-pip python3-dev python3-venv build-essential git ca-certificates && python3 -m venv /venv && export PATH=/venv/bin:$PATH' ;;
    *)  # the official python:* images are Debian based
        SETUP='apt-get update -qq && apt-get install -y -qq --no-install-recommends build-essential git ca-certificates' ;;
esac

exec docker run --rm "$@" \
    -v "$SDIST:/sdist/$(basename "$SDIST"):ro" \
    -v "$ROOT/requirements-test.txt:/requirements-test.txt:ro" \
    "$IMAGE" sh -euxc "
$SETUP
python -m pip install -U pip
python -m pip install /sdist/*.tar.gz
python -m pip install -r /requirements-test.txt
mkdir -p /src /scratch && tar xzf /sdist/*.tar.gz -C /src --no-same-owner
cp -r /src/*/test /src/*/pytest.ini /scratch/ && cd /scratch
python -c 'import packingsolver3d, os; print(packingsolver3d.__version__, os.path.dirname(packingsolver3d.__file__))'
pytest test -q -m unittest -p no:cacheprovider
"
