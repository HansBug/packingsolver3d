.PHONY: docs docs_en docs_zh pdocs test unittest doctest figures benchmarks build build_clean package clean rst_auto help

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
	@echo "                      Options: JOBS=<n> LINETRACE=1 (gcov-instrumented bridge)"
	@echo "  make build_clean  - Remove the CMake build tree and the built extension"
	@echo "  make package      - Build Python package (sdist and wheel)"
	@echo "  make clean        - Remove build artifacts"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests (alias for unittest)"
	@echo "  make unittest     - Run unit tests with pytest"
	@echo "                      Options: RANGE_DIR=<dir> COV_TYPES='xml term-missing'"
	@echo "                               MIN_COVERAGE=<percent> WORKERS=<n>"
	@echo "                      Runs the docstring examples as a second pass and folds"
	@echo "                      them into the same coverage.xml; after 'LINETRACE=1 make build'"
	@echo "                      that file also carries the gcov coverage of _core.cpp"
	@echo "  make doctest      - Run every >>> example under packingsolver3d/ (pytest --doctest-modules)"
	@echo "                      Options: DOCTEST_SCOPE=packingsolver3d/<module>.py DOCTEST_ARGS='-q'"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Build documentation (auto-detects language)"
	@echo "  make docs_en      - Build English documentation"
	@echo "  make docs_zh      - Build Chinese documentation"
	@echo "  make pdocs        - Build production documentation with versioning"
	@echo "  make rst_auto     - Generate RST documentation from Python source"
	@echo "                      Options: RANGE_DIR=<dir>"
	@echo "  make figures      - Regenerate the packing figures (HTML + PNG) under docs/source/_static/figures"
	@echo "                      Needs plotly and kaleido with a Chrome/Chromium binary; FIGURES_ARGS=--no-png skips PNG"
	@echo "  make benchmarks   - Solve the benchmark cases and regenerate the tables and figures of docs/source/benchmarks"
	@echo "                      (tools/make_benchmarks.py --solve --render); BENCHMARKS_ARGS=--no-png skips PNG"
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

# When the bridge was built instrumented (LINETRACE=1 make build), its gcov data
# lands next to the object file in the CMake tree; gcovr renders it as Cobertura
# and folds it into pytest-cov's coverage.xml, so one file carries both
# languages (gcovr reads coverage.py's Cobertura through --cobertura-add-tracefile).
# Compiler-generated exception and unreachable branches are left out, otherwise
# most pybind11 lines read as partially covered; codecov.yml additionally counts
# the remaining partial lines as hits so the dashboard matches the table below.
GCOV_DATA_DIR := ${CMAKE_BUILD_DIR}/CMakeFiles/_core.dir/packingsolver3d

# Docstring examples: every >>> block under the package is executed by pytest.
# The flags match sphinx.ext.doctest's defaults; pytest's own default is ELLIPSIS
# alone and setting the option replaces it, so the full set is always listed.
DOCTEST_SCOPE ?= ${SRC_DIR}
DOCTEST_FLAGS ?= ELLIPSIS IGNORE_EXCEPTION_DETAIL DONT_ACCEPT_TRUE_FOR_1

unittest:
	UNITTEST=1 \
		$(PYTHON) -m pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		--junitxml=junit.xml -o junit_family=legacy \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},) \
		$(if ${WORKERS},-n ${WORKERS},)
	UNITTEST=1 \
		$(PYTHON) -m pytest "${DOCTEST_SCOPE}" \
		--doctest-modules -p tools.doctest_plugin \
		-o doctest_optionflags="${DOCTEST_FLAGS}" \
		$(if $(filter xml,${COV_TYPES}),--cov="${RANGE_SRC_DIR}" --cov-append --cov-report=xml,)
	@if ls "${GCOV_DATA_DIR}"/*.gcda >/dev/null 2>&1 && [ -f coverage.xml ] \
		&& $(PYTHON) -m gcovr --help 2>/dev/null | grep -q -- --cobertura-add-tracefile; then \
		echo "Folding gcov coverage of packingsolver3d/_core.cpp into coverage.xml"; \
		$(PYTHON) -m gcovr --root "${PROJ_DIR}" --object-directory "${CMAKE_BUILD_DIR}" \
			--filter "packingsolver3d/_core\\.cpp" \
			--exclude-throw-branches --exclude-unreachable-branches \
			--cobertura .coverage-cpp.xml && \
		$(PYTHON) -m gcovr --root "${PROJ_DIR}" \
			--cobertura-add-tracefile coverage.xml --cobertura-add-tracefile .coverage-cpp.xml \
			--cobertura .coverage-merged.xml --txt=- --print-summary && \
		mv -f .coverage-merged.xml coverage.xml && rm -f .coverage-cpp.xml; \
	else \
		echo "C++ coverage not folded in: needs gcov data ('LINETRACE=1 make build') and gcovr >= 8"; \
	fi

# The gate alone, without coverage: a docstring is a published contract and an
# example that cannot run is a defect, never something to skip.
doctest:
	$(PYTHON) -m pytest "${DOCTEST_SCOPE}" \
		--doctest-modules -p tools.doctest_plugin \
		-o doctest_optionflags="${DOCTEST_FLAGS}" \
		$(DOCTEST_ARGS)

# The figures are committed: they are real solves rendered through
# packingsolver3d.visual, and the documentation build must not need the
# extension, plotly or a browser.
figures:
	$(PYTHON) -m tools.make_figures --output "${DOC_DIR}/source/_static/figures" $(FIGURES_ARGS)

benchmarks:
	$(PYTHON) -m tools.make_benchmarks --solve --render $(BENCHMARKS_ARGS)

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
