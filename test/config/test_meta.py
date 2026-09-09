import re

import pytest

from packingsolver3d.config.meta import (
    __AUTHOR__, __AUTHOR_EMAIL__, __DESCRIPTION__, __LP_SOLVER__, __TITLE__, __UPSTREAM_COMMIT__,
    __UPSTREAM_NAME__, __UPSTREAM_URL__, __VERSION__,
)


@pytest.mark.unittest
class TestConfigMeta:
    def test_title(self):
        assert __TITLE__ == 'packingsolver3d'

    def test_version(self):
        assert re.fullmatch(r'\d+\.\d+\.\d+([ab]\d+|rc\d+)?', __VERSION__)

    def test_description(self):
        assert isinstance(__DESCRIPTION__, str) and 'PackingSolver' in __DESCRIPTION__

    def test_author(self):
        assert __AUTHOR__ == 'HansBug'
        assert '@' in __AUTHOR_EMAIL__

    def test_upstream(self):
        assert __UPSTREAM_NAME__ == 'PackingSolver'
        assert __UPSTREAM_URL__.startswith('https://github.com/fontanf/')
        assert re.fullmatch(r'[0-9a-f]{40}', __UPSTREAM_COMMIT__)

    def test_lp_solver(self):
        assert __LP_SOLVER__ == 'highs'
