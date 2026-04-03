"""LLM backend package."""

from sophion.backend.base import LLMBackend
from sophion.backend.claude_code import ClaudeCodeBackend
from sophion.config import Config


def get_backend(config: Config) -> LLMBackend:
    """Create the appropriate LLM backend from config."""
    if config.backend.primary == "claude-code":
        return ClaudeCodeBackend()
    raise ValueError(f"Unknown backend: {config.backend.primary}")
