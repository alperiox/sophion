from unittest.mock import MagicMock, patch

from sophion.backend.base import LLMBackend
from sophion.backend.claude_code import ClaudeCodeBackend


def test_claude_code_implements_backend():
    backend = ClaudeCodeBackend()
    assert isinstance(backend, LLMBackend)


def test_claude_code_has_file_access():
    backend = ClaudeCodeBackend()
    assert backend.has_file_access is True


def test_claude_code_builds_basic_command():
    backend = ClaudeCodeBackend()
    cmd = backend._build_command("hello world")
    assert cmd == ["claude", "-p", "--output-format", "text", "hello world"]


def test_claude_code_builds_command_with_system_prompt():
    backend = ClaudeCodeBackend()
    cmd = backend._build_command("hello", system_prompt="be helpful")
    assert cmd == [
        "claude", "-p", "--output-format", "text",
        "--system-prompt", "be helpful",
        "hello",
    ]


def test_claude_code_query():
    backend = ClaudeCodeBackend()
    mock_result = MagicMock()
    mock_result.stdout = "This is the response\n"
    mock_result.returncode = 0

    with patch("sophion.backend.claude_code.subprocess.run", return_value=mock_result) as mock_run:
        result = backend.query("test prompt", system_prompt="be concise")

    assert result == "This is the response"
    mock_run.assert_called_once_with(
        [
            "claude", "-p", "--output-format", "text",
            "--system-prompt", "be concise",
            "test prompt",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_claude_code_query_no_system_prompt():
    backend = ClaudeCodeBackend()
    mock_result = MagicMock()
    mock_result.stdout = "response\n"
    mock_result.returncode = 0

    with patch("sophion.backend.claude_code.subprocess.run", return_value=mock_result) as mock_run:
        result = backend.query("just a question")

    assert result == "response"
    mock_run.assert_called_once_with(
        ["claude", "-p", "--output-format", "text", "just a question"],
        capture_output=True,
        text=True,
        check=True,
    )
