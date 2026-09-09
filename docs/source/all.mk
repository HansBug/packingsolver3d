PIP    := $(shell which pip)
PYTHON ?= $(shell which python)
PS     ?= $(shell ${PYTHON} -c "import os; print(os.pathsep)")

SOURCEDIR ?= $(shell readlink -f ${CURDIR})
BUILDDIR  ?= $(shell readlink -f ${CURDIR}/../build)

_CURRENT_PATH := ${PATH}
_PROJ_DIR     := $(shell readlink -f ${SOURCEDIR}/../..)

.EXPORT_ALL_VARIABLES:

PYTHONPATH = ${_PROJ_DIR}
PATH       = ${_CURRENT_PATH}

.PHONY: all build clean pip cleanplt

pip:
	@$(PIP) install -r ${_PROJ_DIR}/requirements.txt
	@$(PIP) install -r ${_PROJ_DIR}/requirements-doc.txt

# The API pages come from `make rst_auto` at the repository root; there are no
# generated diagrams, demos or notebooks in this documentation tree.
build:
	@true

all: build

clean:
	@true

cleanplt:
	@true
