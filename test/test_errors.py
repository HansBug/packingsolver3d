import pytest

from packingsolver3d import (
    InvalidInstanceError, PackingSolverError, SolverFailedError, StackSemanticsError, UnsupportedFeatureError,
)


@pytest.mark.unittest
class TestErrors:
    def test_hierarchy(self):
        assert issubclass(InvalidInstanceError, PackingSolverError)
        assert issubclass(InvalidInstanceError, ValueError)
        assert issubclass(UnsupportedFeatureError, ValueError)
        assert issubclass(StackSemanticsError, InvalidInstanceError)
        assert issubclass(SolverFailedError, RuntimeError)

    def test_run_attribute(self):
        err = SolverFailedError('boom')
        assert err.run is None
        assert str(err) == 'boom'
        err = SolverFailedError('slow', run='marker')
        assert err.run == 'marker'
