import pytest
from pathlib import Path

from sophion.config import Config
from sophion.store import Store


@pytest.fixture
def tmp_base(tmp_path):
    """Temporary base directory for sophion data."""
    return tmp_path / "sophion"


@pytest.fixture
def config(tmp_base):
    """Config pointing to temporary directory."""
    return Config(base_dir=tmp_base)


@pytest.fixture
def store(config):
    """Initialized store in temporary directory."""
    s = Store(config)
    s.initialize()
    return s
