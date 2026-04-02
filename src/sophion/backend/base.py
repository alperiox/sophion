"""LLM backend interface."""

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def query(self, prompt: str, system_prompt: str = "") -> str:
        """Send a prompt to the LLM and return the response text."""
        ...

    @property
    def has_file_access(self) -> bool:
        """Whether this backend can read files from the local filesystem.

        Claude Code can read files via its built-in tools.
        API-based backends cannot.
        """
        return False
