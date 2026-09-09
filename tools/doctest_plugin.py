"""
Pytest plugin backing the docstring example gate.

Loaded with ``-p tools.doctest_plugin`` by the ``doctest`` Makefile target (and
by the doctest pass inside ``make unittest``) rather than living in a
``conftest.py``, so its behaviour stays scoped to the doctest run.

The gate itself is a plain ``pytest --doctest-modules`` invocation over
``packingsolver3d/``: every ``>>>`` example must run and produce the output its
docstring claims.  There is no known-failure list, and ``# doctest: +SKIP``
hides a problem rather than solving it.
"""

import pytest


@pytest.fixture(autouse=True)
def _doctest_workdir(tmp_path, monkeypatch):
    """
    Run each example in a throwaway working directory.

    Examples must stay copy-pasteable, so any file an example writes lands here
    instead of in the checkout.

    :param tmp_path: Per-test temporary directory fixture.
    :param monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.chdir(tmp_path)
