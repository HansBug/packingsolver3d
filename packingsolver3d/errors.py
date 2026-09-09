"""
Overview:
    Exception hierarchy of :mod:`packingsolver3d`.

    Everything raised by this package derives from :class:`PackingSolverError`,
    so ``except PackingSolverError`` is enough to contain the whole binding.

Example::

    >>> from packingsolver3d import (InvalidInstanceError, PackingSolverError, SolverFailedError,
    ...                              StackSemanticsError, UnsupportedFeatureError)
    >>> issubclass(StackSemanticsError, InvalidInstanceError)
    True
    >>> issubclass(InvalidInstanceError, ValueError) and issubclass(SolverFailedError, RuntimeError)
    True
    >>> all(issubclass(e, PackingSolverError)
    ...     for e in (InvalidInstanceError, UnsupportedFeatureError, SolverFailedError))
    True
    >>> SolverFailedError('upstream threw').run is None
    True
"""

__all__ = [
    'PackingSolverError',
    'InvalidInstanceError',
    'UnsupportedFeatureError',
    'SolverFailedError',
    'StackSemanticsError',
]


class PackingSolverError(Exception):
    """
    Base class of every error raised by :mod:`packingsolver3d`.
    """


class InvalidInstanceError(PackingSolverError, ValueError):
    """
    Raised when an :class:`~packingsolver3d.model.Instance` cannot be encoded.

    This covers structurally broken instances (no bin types, no item types,
    non-positive dimensions), raised before the native module is called, and
    the rejections of upstream's ``InstanceBuilder`` itself, re-raised with
    upstream's own message.
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
    rejects the finished stack, which surfaces as an opaque exception mid-solve.
    """


class SolverFailedError(PackingSolverError, RuntimeError):
    """
    Raised when upstream throws during the solve itself.

    :param message: Human readable summary, carrying upstream's own message.
    :param run: The :class:`~packingsolver3d.result.RunRecord` of the attempt,
        carrying the options handed to upstream and the wall time.
    """

    def __init__(self, message, run=None):
        PackingSolverError.__init__(self, message)
        self.run = run
