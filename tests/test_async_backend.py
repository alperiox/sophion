import asyncio
from unittest.mock import MagicMock

from sophion.tui.async_backend import AsyncBackendWrapper


def test_async_wrapper_query():
    mock_backend = MagicMock()
    mock_backend.query.return_value = "response text"

    wrapper = AsyncBackendWrapper(mock_backend)
    result = asyncio.run(wrapper.query("test prompt", system_prompt="be helpful"))

    assert result == "response text"
    mock_backend.query.assert_called_once_with("test prompt", "be helpful")


def test_async_wrapper_query_no_system_prompt():
    mock_backend = MagicMock()
    mock_backend.query.return_value = "hello"

    wrapper = AsyncBackendWrapper(mock_backend)
    result = asyncio.run(wrapper.query("hi"))

    assert result == "hello"
    mock_backend.query.assert_called_once_with("hi", "")


def test_async_wrapper_has_file_access_true():
    mock_backend = MagicMock()
    mock_backend.has_file_access = True

    wrapper = AsyncBackendWrapper(mock_backend)
    assert wrapper.has_file_access is True


def test_async_wrapper_has_file_access_false():
    mock_backend = MagicMock()
    mock_backend.has_file_access = False

    wrapper = AsyncBackendWrapper(mock_backend)
    assert wrapper.has_file_access is False
