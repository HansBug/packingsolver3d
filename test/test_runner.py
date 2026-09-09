import hashlib
import os
import shutil
import stat
import sys

import pytest

from packingsolver3d import BinaryNotFoundError, SolverFailedError, SolverTimeoutError, available_binaries, binary_path
from packingsolver3d import _runner
from packingsolver3d._csv import write_instance


def _fake_executable(directory, body_posix, body_windows):
    """Write a tiny stand-in solver; Windows runs .bat files straight from CreateProcess."""
    if sys.platform == 'win32':
        path = os.path.join(directory, 'fake.bat')
        with open(path, 'w') as f:
            f.write('@echo off\r\n' + body_windows + '\r\n')
    else:
        path = os.path.join(directory, 'fake.sh')
        with open(path, 'w') as f:
            f.write('#!/bin/sh\n' + body_posix + '\n')
        os.chmod(path, 0o755)
    return path


@pytest.mark.unittest
class TestBinaryPath:
    def test_known_types(self):
        for problem_type in _runner.PROBLEM_TYPES:
            path = binary_path(problem_type)
            assert os.path.isfile(path)
            assert os.path.basename(path).startswith('packingsolver_' + problem_type)

    def test_unknown_type(self):
        with pytest.raises(ValueError):
            binary_path('rectangle')

    def test_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_runner, '_bin_directory', lambda: str(tmp_path))
        with pytest.raises(BinaryNotFoundError) as exc_info:
            binary_path('box')
        assert 'tools/build_upstream.py' in str(exc_info.value)
        assert available_binaries() == {'box': None, 'boxstacks': None}

    def test_available(self):
        found = available_binaries()
        assert set(found) == {'box', 'boxstacks'}
        assert all(found.values())

    @pytest.mark.skipif(sys.platform == 'win32', reason='mode bits are a POSIX concept')
    def test_restores_executable_bit(self, tmp_path, monkeypatch):
        source = binary_path('box')
        target = tmp_path / os.path.basename(source)
        shutil.copyfile(source, str(target))
        os.chmod(str(target), stat.S_IRUSR | stat.S_IWUSR)
        monkeypatch.setattr(_runner, '_bin_directory', lambda: str(tmp_path))
        assert binary_path('box') == str(target)
        assert os.access(str(target), os.X_OK)


@pytest.mark.unittest
class TestSha256:
    def test_matches_hashlib(self):
        path = binary_path('box')
        with open(path, 'rb') as f:
            expected = hashlib.sha256(f.read()).hexdigest()
        assert _runner.binary_sha256(path) == expected
        assert _runner._SHA256_CACHE[path] == expected
        assert _runner.binary_sha256(path) is _runner._SHA256_CACHE[path]


@pytest.mark.unittest
class TestAddressSpaceLimiter:
    def test_shape(self):
        limiter = _runner._address_space_limiter(64)
        if _runner.resource is None:
            assert limiter is None
        else:
            assert callable(limiter)


@pytest.mark.unittest
class TestRunSolver:
    def _paths(self, instance, directory):
        paths = write_instance(instance, str(directory))
        paths['output'] = os.path.join(str(directory), 'output.json')
        paths['certificate'] = os.path.join(str(directory), 'certificate.csv')
        return paths

    def test_argv_and_record(self, box_instance, tmp_path):
        paths = self._paths(box_instance, tmp_path)
        record, argv = _runner.run_solver(
            'box', paths, options=['--verbosity-level', '0', '--linear-programming-solver', 'highs'],
            time_limit=2, memory_limit=4096,
        )
        assert argv[0] == binary_path('box')
        assert argv[1:9] == ['--items', paths['items'], '--bins', paths['bins'],
                             '--parameters', paths['parameters'], '--output', paths['output']]
        assert argv[9:11] == ['--certificate', paths['certificate']]
        assert argv[11:15] == ['--time-limit', '2.0', '--memory-limit', '4096']
        assert argv[-2:] == ['--linear-programming-solver', 'highs']
        assert record.argv == tuple(argv)
        assert record.returncode == 0
        assert not record.timed_out
        assert record.wall_time > 0
        assert record.binary_sha256 == _runner.binary_sha256(argv[0])
        assert os.path.isfile(paths['output'])
        assert os.path.isfile(paths['certificate'])

    def test_optional_paths(self, defect_instance, tmp_path):
        paths = write_instance(defect_instance, str(tmp_path))
        record, argv = _runner.run_solver(
            'boxstacks', paths, options=['--linear-programming-solver', 'highs'], time_limit=1,
        )
        assert '--defects' in argv
        assert '--output' not in argv
        assert '--certificate' not in argv
        assert record.returncode == 0

    def test_nonzero_exit(self, box_instance, tmp_path, monkeypatch):
        fake = _fake_executable(str(tmp_path), 'echo broken >&2; exit 3', 'echo broken 1>&2\r\nexit /b 3')
        monkeypatch.setattr(_runner, 'binary_path', lambda problem_type: fake)
        with pytest.raises(SolverFailedError) as exc_info:
            _runner.run_solver('box', self._paths(box_instance, tmp_path))
        assert exc_info.value.run.returncode == 3
        assert 'broken' in exc_info.value.run.stderr
        assert 'code 3' in str(exc_info.value)
        assert 'broken' in str(exc_info.value)

    def test_wall_clock_guard(self, box_instance, tmp_path, monkeypatch):
        fake = _fake_executable(str(tmp_path), 'sleep 10', 'ping -n 11 127.0.0.1 > nul')
        monkeypatch.setattr(_runner, 'binary_path', lambda problem_type: fake)
        with pytest.raises(SolverTimeoutError) as exc_info:
            _runner.run_solver('box', self._paths(box_instance, tmp_path), time_limit=0.1, grace_seconds=0.3)
        assert exc_info.value.run.timed_out
        assert exc_info.value.run.wall_time < 8

    def test_launch_failure(self, box_instance, tmp_path, monkeypatch):
        not_executable = tmp_path / 'plain.txt'
        not_executable.write_text('not a program')
        monkeypatch.setattr(_runner, 'binary_path', lambda problem_type: str(not_executable))
        with pytest.raises(SolverFailedError) as exc_info:
            _runner.run_solver('box', self._paths(box_instance, tmp_path))
        assert 'unable to launch' in str(exc_info.value)
        assert exc_info.value.run is None

    @pytest.mark.skipif(sys.platform != 'linux', reason='RLIMIT_AS is only enforced on Linux')
    def test_memory_limit_is_enforced(self, box_instance, tmp_path):
        with pytest.raises(SolverFailedError):
            _runner.run_solver(
                'box', self._paths(box_instance, tmp_path),
                options=['--linear-programming-solver', 'highs'], time_limit=2, memory_limit=8,
            )
