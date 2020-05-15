import os
import pytest


def test_build_info(app):
    # if not os.environ.get("CI"):
    #     pytest.skip("Not in Circle CI")
    assert os.environ["GIT_SHA"] is not None
    assert app.config["GIT_SHA"] is not None
