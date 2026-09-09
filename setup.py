import os
import re
import shlex
import shutil
import subprocess
import sys
from codecs import open

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

_package_name = "packingsolver3d"

here = os.path.abspath(os.path.dirname(__file__))
meta = {}
with open(os.path.join(here, _package_name, 'config', 'meta.py'), 'r', 'utf-8') as f:
    exec(f.read(), meta)


def _load_req(file: str):
    with open(file, 'r', 'utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]


requirements = _load_req(os.path.join(here, 'requirements.txt'))

_REQ_PATTERN = re.compile('^requirements-([a-zA-Z0-9_]+)\\.txt$')
group_requirements = {
    item.group(1): _load_req(os.path.join(here, item.group(0)))
    for item in [_REQ_PATTERN.fullmatch(reqpath) for reqpath in os.listdir(here)] if item
}

with open(os.path.join(here, 'README.md'), 'r', 'utf-8') as f:
    readme = f.read()


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


# FindPython (Python_*, _Python*), pybind11 (pybind11_*, PYBIND11_*) and
# pybind11's legacy module-extension cache (PYTHON_MODULE_EXTENSION and friends,
# which would otherwise name a module built against another interpreter).
_PYTHON_CACHE_PREFIXES = (
    'Python_', '_Python', 'pybind11_', 'PYBIND11_', 'PYTHON_',
    'FIND_PACKAGE_MESSAGE_DETAILS_Python', 'FIND_PACKAGE_MESSAGE_DETAILS_pybind11',
)


def _prepare_build_dir(build_dir, sourcedir):
    """
    Make an existing CMake tree safe to reconfigure from this checkout.

    A tree configured from another source directory (a restored cache in a
    different workspace, an unpacked sdist) cannot be reused and is removed;
    one configured from this checkout only loses its interpreter-specific
    cache entries.
    """
    cache = os.path.join(build_dir, 'CMakeCache.txt')
    if not os.path.isfile(cache):
        return
    with open(cache, 'r', 'utf-8') as f:
        for line in f:
            if line.startswith('CMAKE_HOME_DIRECTORY:INTERNAL='):
                home = line.split('=', 1)[1].strip()
                if os.path.normcase(os.path.realpath(home)) != os.path.normcase(os.path.realpath(sourcedir)):
                    print('discarding CMake tree configured from', home, flush=True)
                    shutil.rmtree(build_dir)
                    return
                break
    _forget_python_cache(build_dir)


def _forget_python_cache(build_dir):
    """
    Drop the interpreter-specific entries from an existing CMake cache.

    The tree is shared between interpreters.  FindPython keeps the previous
    interpreter's include directory and SOABI in the cache and then fails to
    find ``Development.Module`` for the next one, and ``cmake -U`` cannot be
    combined with the ``-D`` that names the new executable on one command line
    (the glob would remove it again), so the cache file is edited directly.
    """
    cache = os.path.join(build_dir, 'CMakeCache.txt')
    if not os.path.isfile(cache):
        return
    with open(cache, 'r', 'utf-8') as f:
        lines = f.readlines()

    # An entry is "NAME:TYPE=VALUE" preceded by its "//" help lines; both go
    # together, otherwise CMake trips over a help block with no entry after it.
    kept, help_lines, dropped = [], [], 0
    for line in lines:
        if line.startswith('//'):
            help_lines.append(line)
            continue
        is_entry = bool(line.strip()) and not line.startswith('#') and ':' in line and '=' in line
        if is_entry and line.startswith(_PYTHON_CACHE_PREFIXES):
            help_lines = []
            dropped += 1
            continue
        kept.extend(help_lines)
        help_lines = []
        kept.append(line)
    kept.extend(help_lines)

    if dropped:
        with open(cache, 'w', 'utf-8') as f:
            f.writelines(kept)


class CMakeBuild(build_ext):
    """
    Drive the top-level CMakeLists.txt, which compiles upstream PackingSolver
    and the pybind11 bridge into one extension module.

    The build directory is fixed (``build/cmake`` unless
    ``PACKINGSOLVER3D_BUILD_DIR`` says otherwise) rather than setuptools'
    per-interpreter ``build_temp``: upstream's objects do not depend on the
    Python version, so reconfiguring the same tree for the next interpreter
    only rebuilds the bridge.  cibuildwheel relies on this to build eight
    wheels per job in little more than the time of one.
    """

    def run(self):
        try:
            subprocess.check_output([self._cmake(), '--version'])
        except OSError:
            raise RuntimeError('CMake >= 3.28 must be installed to build ' +
                               ', '.join(e.name for e in self.extensions))
        for ext in self.extensions:
            self.build_extension(ext)

    @staticmethod
    def _cmake():
        return os.environ.get('CMAKE') or shutil.which('cmake') or 'cmake'

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cfg = 'Debug' if self.debug else 'Release'
        build_dir = os.environ.get('PACKINGSOLVER3D_BUILD_DIR') or os.path.join(here, 'build', 'cmake')
        os.makedirs(build_dir, exist_ok=True)

        _prepare_build_dir(build_dir, ext.sourcedir)
        os.makedirs(build_dir, exist_ok=True)
        cmake_args = [
            '-S', ext.sourcedir,
            '-B', build_dir,
            '-DCMAKE_BUILD_TYPE=' + cfg,
            '-DPython_EXECUTABLE=' + sys.executable,
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_' + cfg.upper() + '=' + extdir,
        ]
        try:
            import pybind11
        except ImportError:  # CMake may still find a system-wide pybind11
            pass
        else:
            cmake_args.append('-Dpybind11_DIR=' + pybind11.get_cmake_dir())
        # LINETRACE is the house convention for coverage-instrumented builds.
        coverage = 'ON' if os.environ.get('LINETRACE') else 'OFF'
        cmake_args.append('-DPS3D_COVERAGE=' + coverage)
        generator = os.environ.get('CMAKE_GENERATOR')
        if generator:
            cmake_args.extend(['-G', generator])
        extra = os.environ.get('PACKINGSOLVER3D_CMAKE_ARGS')
        if extra:
            cmake_args.extend(shlex.split(extra))

        build_args = ['--build', build_dir, '--config', cfg, '--target', '_core']
        if not os.environ.get('CMAKE_BUILD_PARALLEL_LEVEL'):
            build_args.extend(['--parallel', str(os.cpu_count() or 2)])

        print('cmake', ' '.join(cmake_args), flush=True)
        subprocess.check_call([self._cmake()] + cmake_args)
        print('cmake', ' '.join(build_args), flush=True)
        subprocess.check_call([self._cmake()] + build_args)


setup(
    # information
    name=meta['__TITLE__'],
    version=meta['__VERSION__'],
    packages=find_packages(
        include=(_package_name, "%s.*" % _package_name)
    ),
    description=meta['__DESCRIPTION__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=meta['__AUTHOR__'],
    author_email=meta['__AUTHOR_EMAIL__'],
    license='MIT',
    keywords='packingsolver bin-packing 3d box boxstacks knapsack container-loading pybind11',
    url='https://github.com/HansBug/packingsolver3d',
    project_urls={
        'Homepage': 'https://github.com/HansBug/packingsolver3d',
        'Documentation': 'https://packingsolver3d.readthedocs.io/en/latest/',
        'Source': 'https://github.com/HansBug/packingsolver3d',
        'Tracker': 'https://github.com/HansBug/packingsolver3d/issues',
        'Issues': 'https://github.com/HansBug/packingsolver3d/issues',
        'CI': 'https://github.com/HansBug/packingsolver3d/actions',
        'Download': 'https://pypi.org/project/packingsolver3d/#files',
        'Upstream': meta['__UPSTREAM_URL__'],
    },

    # environment
    python_requires=">=3.7",
    ext_modules=[
        CMakeExtension('%s._core' % _package_name),
    ],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
    install_requires=requirements,
    extras_require=group_requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: C++',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
