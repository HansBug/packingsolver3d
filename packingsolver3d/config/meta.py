"""
Overview:
    Meta information for the ``packingsolver3d`` package.
"""

#: Title of this project (should be `packingsolver3d`).
__TITLE__ = 'packingsolver3d'

#: Version of this project.
__VERSION__ = '0.0.1'

#: Short description of the project, will be included in ``setup.py``.
__DESCRIPTION__ = 'Pythonic bindings for the 3D (box / boxstacks) solvers of PackingSolver, ' \
                  'shipped with precompiled native executables.'

#: Author of this project.
__AUTHOR__ = 'HansBug'

#: Email of the author.
__AUTHOR_EMAIL__ = 'hansbug@buaa.edu.cn'

#: Upstream project this distribution wraps.
__UPSTREAM_NAME__ = 'PackingSolver'

#: Upstream repository URL.
__UPSTREAM_URL__ = 'https://github.com/fontanf/packingsolver'

#: Upstream commit the bundled executables are built from.
#: Keep this in sync with the ``upstream/packingsolver`` submodule pointer.
__UPSTREAM_COMMIT__ = 'a7e533033d9c6ee3ff286513720afe6660b5989f'

#: Linear programming backend compiled into the bundled executables.
#:
#: PackingSolver's column generation asks ``columngenerationsolver`` for a
#: linear programming solver by name, and the default name is ``CLP``.  We
#: build with ``PACKINGSOLVER_USE_CLP=OFF PACKINGSOLVER_USE_HIGHS=ON``, so the
#: default name resolves to nothing and the factory throws.  Every command line
#: this package builds therefore passes ``--linear-programming-solver`` with
#: this value.
__LP_SOLVER__ = 'highs'
