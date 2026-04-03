"""Async wrapper around the synchronous LLM backend for TUI use."""

import asyncio

from sophion.backend.base import LLMBackend


class AsyncBackendWrapper:
    """Runs blocking LLMBackend.query() in a thread so the TUI stays responsive."""

    def __init__(self, backend: LLMBackend):
        self.backend = backend

    async def query(self, prompt: str, system_prompt: str = "") -> str:
        """Run the blocking query in a background thread."""
        return await asyncio.to_thread(self.backend.query, prompt, system_prompt)

    @property
    def has_file_access(self) -> bool:
        return self.backend.has_file_access
