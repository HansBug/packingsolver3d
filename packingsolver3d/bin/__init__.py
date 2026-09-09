"""
Overview:
    Home of the precompiled PackingSolver executables.

    A wheel ships ``packingsolver_box`` and ``packingsolver_boxstacks`` here,
    built from the pinned upstream commit recorded in
    :data:`packingsolver3d.config.meta.__UPSTREAM_COMMIT__`.  An sdist ships
    this package empty, so importing :mod:`packingsolver3d` still works but any
    solve raises :class:`packingsolver3d.errors.BinaryNotFoundError` until the
    sources are built.
"""
