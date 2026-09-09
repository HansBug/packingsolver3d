import pytest

from packingsolver3d import (
    BinaryNotFoundError, InvalidInstanceError, PackingSolverError, SolverFailedError, SolverTimeoutError,
    StackSemanticsError, UnsupportedFeatureError,
)


@pytest.mark.unittest
class TestErrors:
    def test_hierarchy(self):
        assert issubclass(BinaryNotFoundError, PackingSolverError)
        assert issubclass(InvalidInstanceError, PackingSolverError)
        assert issubclass(InvalidInstanceError, ValueError)
        assert issubclass(UnsupportedFeatureError, ValueError)
        assert issubclass(StackSemanticsError, InvalidInstanceError)
        assert issubclass(SolverFailedError, RuntimeError)
        assert issubclass(SolverTimeoutError, SolverFailedError)

    def test_run_attribute(self):
        err = SolverFailedError('boom')
        assert err.run is None
        assert str(err) == 'boom'
        err = SolverTimeoutError('slow', run='marker')
        assert err.run == 'marker'
