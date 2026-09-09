import os
import re
import subprocess
import sys
from codecs import open

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py

try:
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:  # setuptools < 70.1 still keeps the command in the wheel package
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

_package_name = "packingsolver3d"

here = os.path.abspath(os.path.dirname(__file__))
meta = {}
with open(os.path.join(here, _package_name, 'config', 'meta.py'), 'r', 'utf-8') as f:
    exec(f.read(), meta)


def _load_req(file: str):
    with open(file, 'r', 'utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]


requirements = _load_req('requirements.txt')

_REQ_PATTERN = re.compile('^requirements-([a-zA-Z0-9_]+)\\.txt$')
group_requirements = {
    item.group(1): _load_req(item.group(0))
    for item in [_REQ_PATTERN.fullmatch(reqpath) for reqpath in os.listdir()] if item
}

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

_BIN_DIR = os.path.join(here, _package_name, 'bin')
_EXECUTABLES = ('packingsolver_box', 'packingsolver_boxstacks')
_EXE_SUFFIX = '.exe' if sys.platform == 'win32' else ''


def _executables_present():
    return all(
        os.path.isfile(os.path.join(_BIN_DIR, name + _EXE_SUFFIX))
        for name in _EXECUTABLES
    )


class build_py(_build_py):
    """
    Build the upstream executables first when nothing is staged yet.

    cibuildwheel stages them in ``before-all`` so wheel builds skip this; a
    source install (sdist) lands here and needs CMake plus a compiler.
    """

    def run(self):
        if not _executables_present() and not os.environ.get('PACKINGSOLVER3D_SKIP_NATIVE_BUILD'):
            subprocess.check_call([sys.executable, os.path.join(here, 'tools', 'build_upstream.py')])
            # package_data was scanned lazily before bin/ was populated; force a rescan.
            self.__dict__.pop('data_files', None)
        _build_py.run(self)


class bdist_wheel(_bdist_wheel):
    """The Python is pure but the executables are not: force a platform tag."""

    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False


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
    keywords='packingsolver bin-packing 3d box boxstacks knapsack container-loading',
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
    cmdclass=dict(build_py=build_py, bdist_wheel=bdist_wheel),
    zip_safe=False,
    package_data={
        '%s.bin' % _package_name: ['packingsolver_box', 'packingsolver_boxstacks', '*.exe'],
    },
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
