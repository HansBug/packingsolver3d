"""
Overview:
    Process boundary between :mod:`packingsolver3d` and the native solvers.

    The solvers run out of process on purpose.  PackingSolver is a research
    code base and several of its paths abort rather than raise: a null logger
    behind the ``FFOT_LOG`` macros, an out-of-bounds read in the axle-weight
    repair pass, a bare ``throw`` when no linear programming backend is
    compiled in.  In process, any of those takes the interpreter with it; out
    of process the worst case is a non-zero exit and a Python exception.

    The same boundary is where resource limits become real.  ``--memory-limit``
    is advisory -- the solver checks it at its own checkpoints -- so on POSIX
    we also set :data:`resource.RLIMIT_AS` in the child, which the allocator
    cannot talk its way past.
"""

import hashlib
import os
import signal
import stat
import subprocess
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

from .errors import BinaryNotFoundError, SolverFailedError, SolverTimeoutError
from .result import RunRecord

try:  # pragma: no cover
    import resource
except ImportError:  # pragma: no cover
    resource = None

__all__ = [
    'binary_path',
    'binary_sha256',
    'available_binaries',
    'run_solver',
]

#: Problem types this distribution ships executables for.
PROBLEM_TYPES = ('box', 'boxstacks')

#: Extra seconds allowed on top of ``--time-limit`` before the child is killed.
#:
#: PackingSolver polls its own timer between search nodes, so it overshoots by
#: however long the current node takes.  The grace period absorbs that plus
#: process start-up and the final certificate write.
DEFAULT_GRACE_SECONDS = 30.0

_SHA256_CACHE = {}  # type: Dict[str, str]


def _bin_directory() -> str:
    """
    Locate the directory holding the bundled executables.

    :return: Absolute path of the ``bin`` directory inside the installed
        package.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')


def binary_path(problem_type: str) -> str:
    """
    Resolve the executable for a problem type.

    :param problem_type: One of :data:`PROBLEM_TYPES`.
    :return: Absolute path of the executable.
    :raise BinaryNotFoundError: When the executable is absent, which normally
        means the package was installed from an sdist without building the
        upstream sources.

    Example::

        >>> import os
        >>> from packingsolver3d._runner import binary_path
        >>> os.path.basename(binary_path('box')).startswith('packingsolver_box')
        True
    """
    if problem_type not in PROBLEM_TYPES:
        raise ValueError(
            'unknown problem type {problem_type!r}, expected one of {expected!r}'.format(
                problem_type=problem_type, expected=PROBLEM_TYPES,
            )
        )

    suffix = '.exe' if sys.platform == 'win32' else ''
    path = os.path.join(_bin_directory(), 'packingsolver_' + problem_type + suffix)
    if not os.path.isfile(path):
        raise BinaryNotFoundError(
            'no executable for problem type {problem_type!r} at {path!r}; '
            'install a wheel, or build the upstream sources with '
            '"python tools/build_upstream.py"'.format(
                problem_type=problem_type, path=path,
            )
        )
    if sys.platform != 'win32' and not os.access(path, os.X_OK):
        # Some archive tools drop the mode bits when unpacking a wheel.
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def available_binaries() -> Dict[str, Optional[str]]:
    """
    Report which executables this installation actually has.

    :return: A mapping from problem type to executable path, with ``None`` for
        the ones that are missing.

    Example::

        >>> from packingsolver3d._runner import available_binaries
        >>> sorted(available_binaries())
        ['box', 'boxstacks']
    """
    result = {}
    for problem_type in PROBLEM_TYPES:
        try:
            result[problem_type] = binary_path(problem_type)
        except BinaryNotFoundError:
            result[problem_type] = None
    return result


def binary_sha256(path: str) -> str:
    """
    Digest an executable, so a result can be pinned to the build that made it.

    The digest is cached per path because it is taken on every solve and the
    file does not change under a running interpreter.

    :param path: Path of the executable.
    :return: Lowercase hex SHA-256 digest.
    """
    cached = _SHA256_CACHE.get(path)
    if cached is not None:
        return cached

    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            digest.update(chunk)
    _SHA256_CACHE[path] = digest.hexdigest()
    return _SHA256_CACHE[path]


def _address_space_limiter(megabytes: int):
    """
    Build a ``preexec_fn`` that caps the child's address space.

    :param megabytes: Limit in mebibytes.
    :return: A callable for ``subprocess``, or ``None`` where
        :mod:`resource` is unavailable (Windows).
    """
    if resource is None:
        return None

    limit = int(megabytes) * 1024 * 1024

    def _limit():  # pragma: no cover - runs in the forked child
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        ceiling = limit if hard == resource.RLIM_INFINITY else min(limit, hard)
        resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))

    return _limit


def _kill_tree(process: 'subprocess.Popen') -> None:
    """
    Kill a child and everything it spawned.

    :param process: The child started by :func:`run_solver`.
    """
    if sys.platform == 'win32':
        subprocess.call(
            ['taskkill', '/F', '/T', '/PID', str(process.pid)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:  # the group already died on its own
            pass
    process.kill()


def run_solver(
        problem_type: str,
        paths: Dict[str, str],
        options: Sequence[str] = (),
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        grace_seconds: float = DEFAULT_GRACE_SECONDS,
) -> Tuple[RunRecord, List[str]]:
    """
    Invoke a native solver once and capture everything it produced.

    :param problem_type: One of :data:`PROBLEM_TYPES`.
    :param paths: Instance file paths as returned by
        :func:`packingsolver3d._csv.write_instance`, plus ``output`` and
        ``certificate`` destinations.
    :param options: Extra command line arguments, already rendered.
    :param time_limit: Value for ``--time-limit``, in seconds.
    :param memory_limit: Value for ``--memory-limit``, in mebibytes.  Also
        applied as a hard :data:`resource.RLIMIT_AS` on POSIX.
    :param grace_seconds: Seconds allowed beyond ``time_limit`` before the
        child is killed.  See :data:`DEFAULT_GRACE_SECONDS`.
    :return: The :class:`~packingsolver3d.result.RunRecord` and the argv used.
    :raise SolverTimeoutError: When the child outran the grace period.
    :raise SolverFailedError: When the child exited non-zero.
    """
    executable = binary_path(problem_type)

    argv = [executable, '--items', paths['items'], '--bins', paths['bins']]
    for key in ('defects', 'parameters'):
        if key in paths:
            argv.extend(['--' + key, paths[key]])
    if 'output' in paths:
        argv.extend(['--output', paths['output']])
    if 'certificate' in paths:
        argv.extend(['--certificate', paths['certificate']])
    if time_limit is not None:
        argv.extend(['--time-limit', repr(float(time_limit))])
    if memory_limit is not None:
        argv.extend(['--memory-limit', str(int(memory_limit))])
    argv.extend(options)

    wall_limit = None
    if time_limit is not None:
        wall_limit = float(time_limit) + max(grace_seconds, 0.0)

    started = time.time()
    timed_out = False
    try:
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=None if memory_limit is None else _address_space_limiter(memory_limit),
            cwd=os.path.dirname(paths['items']) or None,
            # Own process group, so the wall clock guard can kill any child the
            # solver spawned; an orphan holding the pipes would block communicate().
            start_new_session=(sys.platform != 'win32'),
        )
    except OSError as err:
        raise SolverFailedError(
            'unable to launch {executable!r}: {err}'.format(executable=executable, err=err)
        )

    try:
        raw_out, raw_err = process.communicate(timeout=wall_limit)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(process)
        raw_out, raw_err = process.communicate()

    record = RunRecord(
        argv=tuple(argv),
        returncode=process.returncode,
        stdout=(raw_out or b'').decode('utf-8', 'replace'),
        stderr=(raw_err or b'').decode('utf-8', 'replace'),
        wall_time=time.time() - started,
        binary_sha256=binary_sha256(executable),
        timed_out=timed_out,
    )

    if timed_out:
        raise SolverTimeoutError(
            '{problem_type} solver exceeded its wall clock guard of '
            '{wall_limit}s'.format(problem_type=problem_type, wall_limit=wall_limit),
            run=record,
        )
    if record.returncode != 0:
        raise SolverFailedError(
            '{problem_type} solver exited with code {code}: {message}'.format(
                problem_type=problem_type,
                code=record.returncode,
                message=(record.stderr.strip() or record.stdout.strip() or
                         'no diagnostic on either stream'),
            ),
            run=record,
        )

    return record, argv
