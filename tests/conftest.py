import pytest
from pathlib import Path


@pytest.fixture
def tmp_base(tmp_path):
    """Temporary base directory for sophion data."""
    return tmp_path / "sophion"
