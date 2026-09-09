"""
Configure, build, and stage the two PackingSolver executables this package ships.

The script is the single native-build entry point shared by ``make build``,
``setup.py`` (for source installs) and the cibuildwheel ``before-all`` hooks, so
that every wheel is produced with exactly the options recorded in
:mod:`packingsolver3d.config.meta`.

Example::

    python tools/build_upstream.py --jobs 8
"""

import argparse
import glob
import os
import platform
import shutil
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_SOURCE = os.path.join(ROOT, 'upstream', 'packingsolver')
DEFAULT_BUILD_DIR = os.path.join(ROOT, 'build', 'upstream')
DEFAULT_OUTPUT_DIR = os.path.join(ROOT, 'packingsolver3d', 'bin')

#: CMake target per problem type, from ``src/<type>/CMakeLists.txt`` upstream.
TARGETS = {
    'box': 'PackingSolver_box_main',
    'boxstacks': 'PackingSolver_boxstacks_main',
}

#: Executable suffix of the current platform.
EXE_SUFFIX = '.exe' if platform.system() == 'Windows' else ''

#: The one supported configuration.  HiGHS is bundled by upstream's FetchContent;
#: CLP is off because it drags in COIN-OR and LAPACK, and the two are redundant.
#: Never disable both -- the column-generation code throws at runtime otherwise.
CMAKE_OPTIONS = (
    '-DCMAKE_BUILD_TYPE=Release',
    '-DPACKINGSOLVER_USE_CLP=OFF',
    '-DPACKINGSOLVER_USE_HIGHS=ON',
    '-DPACKINGSOLVER_USE_KNITRO=OFF',
    '-DPACKINGSOLVER_BUILD_MAIN=ON',
    '-DPACKINGSOLVER_BUILD_TEST=OFF',
)


def cmake_executable():
    """
    Locate CMake, honouring ``$CMAKE`` first.

    :return: Path or bare command name.
    """
    return os.environ.get('CMAKE') or shutil.which('cmake') or 'cmake'


def configure(source, build_dir, generator=None, extra=()):
    """
    Run the CMake configure step.

    :param source: Upstream source tree.
    :param build_dir: Out-of-tree build directory, created if missing.
    :param generator: Optional ``-G`` generator name.
    :param extra: Additional ``-D`` style arguments appended verbatim.
    """
    argv = [cmake_executable(), '-S', source, '-B', build_dir]
    argv.extend(CMAKE_OPTIONS)
    argv.extend(extra)
    if generator:
        argv.extend(['-G', generator])
    print('+', ' '.join(argv), flush=True)
    subprocess.check_call(argv)


def build(build_dir, jobs=None):
    """
    Build only the two executables we ship.

    :param build_dir: Configured build directory.
    :param jobs: Parallel jobs; ``None`` lets CMake pick.
    """
    argv = [cmake_executable(), '--build', build_dir, '--config', 'Release', '--target']
    argv.extend(TARGETS.values())
    if jobs:
        argv.extend(['--parallel', str(jobs)])
    print('+', ' '.join(argv), flush=True)
    subprocess.check_call(argv)


def stage(build_dir, output_dir):
    """
    Copy the built executables into the package's ``bin`` directory.

    Multi-config generators (MSVC) nest a ``Release`` directory, hence the
    recursive glob rather than a fixed path.

    :param build_dir: Configured build directory.
    :param output_dir: Destination directory.
    :return: Paths of the staged executables.
    :raises FileNotFoundError: If a target produced no executable.
    """
    os.makedirs(output_dir, exist_ok=True)
    staged = []
    for name in TARGETS:
        filename = 'packingsolver_{name}{suffix}'.format(name=name, suffix=EXE_SUFFIX)
        pattern = os.path.join(build_dir, 'src', name, '**', filename)
        matches = sorted(glob.glob(pattern, recursive=True))
        if not matches:
            raise FileNotFoundError('no {filename} under {build_dir}'.format(
                filename=filename, build_dir=build_dir))
        destination = os.path.join(output_dir, filename)
        shutil.copy2(matches[-1], destination)
        mode = os.stat(destination).st_mode
        os.chmod(destination, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print('staged', destination, os.path.getsize(destination), 'bytes', flush=True)
        staged.append(destination)
    return staged


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--source', default=DEFAULT_SOURCE, help='upstream source tree')
    parser.add_argument('--build-dir', default=DEFAULT_BUILD_DIR, help='CMake build directory')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR, help='where to stage the executables')
    parser.add_argument('--jobs', type=int, default=os.cpu_count(), help='parallel build jobs')
    parser.add_argument('--generator', default=os.environ.get('CMAKE_GENERATOR'), help='CMake generator')
    parser.add_argument('--cmake-arg', action='append', default=[], help='extra argument for the configure step')
    parser.add_argument('--no-configure', action='store_true', help='reuse an already configured build directory')
    args = parser.parse_args(argv)

    if not os.path.isfile(os.path.join(args.source, 'CMakeLists.txt')):
        parser.error('no CMakeLists.txt in {source!r}; run "git submodule update --init"'.format(
            source=args.source))
    if not args.no_configure:
        configure(args.source, args.build_dir, args.generator, args.cmake_arg)
    build(args.build_dir, args.jobs)
    stage(args.build_dir, args.output_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
