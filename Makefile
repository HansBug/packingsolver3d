.PHONY: docs docs_en docs_zh pdocs test unittest build build_clean package clean rst_auto help

PYTHON := $(shell which python)

PROJ_DIR      := .
DOC_DIR       := ${PROJ_DIR}/docs
BUILD_DIR     := ${PROJ_DIR}/build
DIST_DIR      := ${PROJ_DIR}/dist
TEST_DIR      := ${PROJ_DIR}/test
TESTFILE_DIR  := ${TEST_DIR}/testfile
SRC_DIR       := ${PROJ_DIR}/packingsolver3d
UPSTREAM_DIR  := ${PROJ_DIR}/upstream/packingsolver
CMAKE_BUILD_DIR := ${BUILD_DIR}/cmake

RANGE_DIR      ?= .
RANGE_TEST_DIR := ${TEST_DIR}/${RANGE_DIR}
RANGE_SRC_DIR  := ${SRC_DIR}/${RANGE_DIR}

COV_TYPES ?= xml term-missing

# Native build knobs; JOBS defaults to every core, see setup.py.
JOBS ?=

# RST documentation generation variables
PYTHON_CODE_DIR   := ${SRC_DIR}
RST_DOC_DIR       := ${DOC_DIR}/source/api_doc
PYTHON_CODE_FILES := $(shell find ${PYTHON_CODE_DIR} -name "*.py" ! -name "__*.py" 2>/dev/null)
RST_DOC_FILES     := $(patsubst ${PYTHON_CODE_DIR}/%.py,${RST_DOC_DIR}/%.rst,${PYTHON_CODE_FILES})
PYTHON_NONM_FILES := $(shell find ${PYTHON_CODE_DIR} -name "__init__.py" 2>/dev/null)
RST_NONM_FILES    := $(foreach file,${PYTHON_NONM_FILES},$(patsubst %/__init__.py,%/index.rst,$(patsubst ${PYTHON_CODE_DIR}/%,${RST_DOC_DIR}/%,$(patsubst ${PYTHON_CODE_DIR}/__init__.py,${RST_DOC_DIR}/index.rst,${file}))))

# Help target
help:
	@echo "packingsolver3d Build System"
	@echo "============================"
	@echo ""
	@echo "Building and Packaging:"
	@echo "  make build        - Build the _core extension (upstream + pybind11 bridge) in place"
	@echo "                      Options: JOBS=<n>"
	@echo "  make build_clean  - Remove the CMake build tree and the built extension"
	@echo "  make package      - Build Python package (sdist and wheel)"
	@echo "  make clean        - Remove build artifacts"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests (alias for unittest)"
	@echo "  make unittest     - Run unit tests with pytest"
	@echo "                      Options: RANGE_DIR=<dir> COV_TYPES='xml term-missing'"
	@echo "                               MIN_COVERAGE=<percent> WORKERS=<n>"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Build documentation (auto-detects language)"
	@echo "  make docs_en      - Build English documentation"
	@echo "  make docs_zh      - Build Chinese documentation"
	@echo "  make pdocs        - Build production documentation with versioning"
	@echo "  make rst_auto     - Generate RST documentation from Python source"
	@echo "                      Options: RANGE_DIR=<dir>"
	@echo ""
	@echo "Common Variables:"
	@echo "  RANGE_DIR=<dir>   - Target specific directory (default: .)"
	@echo "  COV_TYPES=<types> - Coverage report types (default: xml term-missing)"
	@echo "  MIN_COVERAGE=<n>  - Minimum coverage percentage"
	@echo "  WORKERS=<n>       - Number of parallel test workers"
	@echo ""

build:
	$(if ${JOBS},CMAKE_BUILD_PARALLEL_LEVEL=${JOBS},) \
		PACKINGSOLVER3D_BUILD_DIR="${CMAKE_BUILD_DIR}" \
		$(PYTHON) setup.py build_ext --inplace

build_clean:
	rm -rf ${CMAKE_BUILD_DIR}
	rm -f ${SRC_DIR}/_core*.so ${SRC_DIR}/_core*.pyd

# The wheel is built from the source tree, not from the sdist, so the shared
# CMake tree in ${CMAKE_BUILD_DIR} is reused instead of rebuilding upstream.
package:
	rm -rf ${BUILD_DIR}/lib* ${BUILD_DIR}/bdist.* ${BUILD_DIR}/temp.*
	rm -f ${DIST_DIR}/*.whl ${DIST_DIR}/*.tar.gz
	$(PYTHON) -m build --sdist --outdir ${DIST_DIR}
	PACKINGSOLVER3D_BUILD_DIR="${CMAKE_BUILD_DIR}" $(PYTHON) -m build --wheel --outdir ${DIST_DIR}

clean:
	rm -rf ${DIST_DIR} ${BUILD_DIR} *.egg-info
	rm -f coverage.xml junit.xml .coverage

test: unittest

unittest:
	UNITTEST=1 \
		$(PYTHON) -m pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		--junitxml=junit.xml -o junit_family=legacy \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},) \
		$(if ${WORKERS},-n ${WORKERS},)

docs:
	$(MAKE) -C "${DOC_DIR}" build
docs_en:
	READTHEDOCS_LANGUAGE=en $(MAKE) -C "${DOC_DIR}" build
docs_zh:
	READTHEDOCS_LANGUAGE=zh-cn $(MAKE) -C "${DOC_DIR}" build
pdocs:
	$(MAKE) -C "${DOC_DIR}" prod

# RST documentation generation targets
rst_auto: ${RST_DOC_FILES} ${RST_NONM_FILES} auto_rst_top_index.py
	$(PYTHON) auto_rst_top_index.py -i ${PYTHON_CODE_DIR} -o ${DOC_DIR}/source

${RST_DOC_DIR}/%.rst: ${PYTHON_CODE_DIR}/%.py auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@

# A package index carries the toctree that auto_rst.py builds by listing the
# package directory, so it goes stale when a module or subpackage appears or is
# edited beside it -- not only when __init__.py itself changes.  The wildcards
# need the stem, which is why they are deferred to the second expansion.
.SECONDEXPANSION:

${RST_DOC_DIR}/%/index.rst: ${PYTHON_CODE_DIR}/%/__init__.py $$(wildcard ${PYTHON_CODE_DIR}/$$*/*.py) $$(wildcard ${PYTHON_CODE_DIR}/$$*/*/__init__.py) auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@

${RST_DOC_DIR}/index.rst: ${PYTHON_CODE_DIR}/__init__.py $(wildcard ${PYTHON_CODE_DIR}/*.py) $(wildcard ${PYTHON_CODE_DIR}/*/__init__.py) auto_rst.py Makefile
	@mkdir -p $(dir $@)
	$(PYTHON) auto_rst.py -i $< -o $@
