import pytest
from pathlib import Path

from sophion.config import Config


@pytest.fixture
def tmp_base(tmp_path):
    """Temporary base directory for sophion data."""
    return tmp_path / "sophion"


@pytest.fixture
def config(tmp_base):
    """Config pointing to temporary directory."""
    return Config(base_dir=tmp_base)
