"""
Overview:
    Package metadata, re-exported from :mod:`packingsolver3d.config.meta`.

Example::

    >>> from packingsolver3d.config import __VERSION__
    >>> isinstance(__VERSION__, str) and __VERSION__.count('.') >= 2
    True
"""

from .meta import __AUTHOR__, __AUTHOR_EMAIL__, __DESCRIPTION__, __LP_SOLVER__, __TITLE__, \
    __UPSTREAM_COMMIT__, __UPSTREAM_NAME__, __UPSTREAM_URL__, __VERSION__

__all__ = [
    '__AUTHOR__',
    '__AUTHOR_EMAIL__',
    '__DESCRIPTION__',
    '__LP_SOLVER__',
    '__TITLE__',
    '__UPSTREAM_COMMIT__',
    '__UPSTREAM_NAME__',
    '__UPSTREAM_URL__',
    '__VERSION__',
]
