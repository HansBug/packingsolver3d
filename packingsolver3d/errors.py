"""
Overview:
    Exception hierarchy of :mod:`packingsolver3d`.

    Everything raised by this package derives from :class:`PackingSolverError`,
    so ``except PackingSolverError`` is enough to contain the whole binding.
"""

__all__ = [
    'PackingSolverError',
    'BinaryNotFoundError',
    'InvalidInstanceError',
    'UnsupportedFeatureError',
    'SolverFailedError',
    'SolverTimeoutError',
    'StackSemanticsError',
]


class PackingSolverError(Exception):
    """
    Base class of every error raised by :mod:`packingsolver3d`.
    """


class BinaryNotFoundError(PackingSolverError):
    """
    Raised when the precompiled executable for a problem type is missing.

    A wheel always ships the executables, so this normally means the package
    was installed from an sdist without building the upstream sources, or the
    ``bin`` directory was stripped after installation.
    """


class InvalidInstanceError(PackingSolverError, ValueError):
    """
    Raised when an :class:`~packingsolver3d.model.Instance` cannot be encoded.

    This covers structurally broken instances (no bin types, no item types,
    non-positive dimensions) and is raised before any process is spawned.
    """


class UnsupportedFeatureError(PackingSolverError, ValueError):
    """
    Raised when an instance uses a feature the chosen solver ignores.

    The ``box`` solver reads its instance CSV with an if/else chain that has no
    trailing error branch, so columns it does not know about are dropped in
    silence.  Rather than let stacking constraints vanish, we refuse the call.
    """


class StackSemanticsError(InvalidInstanceError):
    """
    Raised when ``boxstacks`` would build a stack upstream cannot represent.

    Upstream groups item types into stacks by ``(group_id, stackability_id)``
    alone and only discovers a footprint mismatch when the solution builder
    rejects the finished stack, which surfaces as an opaque non-zero exit.
    """


class SolverFailedError(PackingSolverError, RuntimeError):
    """
    Raised when the native executable exits non-zero or writes no output.

    :param message: Human readable summary.
    :param run: The :class:`~packingsolver3d.result.RunRecord` of the attempt,
        carrying ``argv``, the exit code and the captured streams.
    """

    def __init__(self, message, run=None):
        PackingSolverError.__init__(self, message)
        self.run = run


class SolverTimeoutError(SolverFailedError):
    """
    Raised when the native executable outruns its wall clock guard.

    PackingSolver honours ``--time-limit`` itself and normally exits cleanly
    with the best solution found so far; this error means it blew past even the
    grace period on top of that limit and had to be killed.
    """
