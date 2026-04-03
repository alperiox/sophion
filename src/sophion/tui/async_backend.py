"""Async wrapper around the synchronous LLM backend for TUI use."""

import asyncio
import json
from collections.abc import AsyncIterator

from sophion.backend.base import LLMBackend


class AsyncBackendWrapper:
    """Runs blocking LLMBackend.query() in a thread so the TUI stays responsive."""

    def __init__(self, backend: LLMBackend):
        self.backend = backend

    async def query(self, prompt: str, system_prompt: str = "") -> str:
        """Run the blocking query in a background thread."""
        return await asyncio.to_thread(self.backend.query, prompt, system_prompt)

    async def stream_query(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[str]:
        """Stream a query response using claude -p --output-format stream-json.

        Yields the accumulated response text as it arrives. Each yield
        contains the full text so far (not just the delta).
        Falls back to blocking query if streaming fails.
        """
        cmd = [
            "claude",
            "-p",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
        ]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        cmd.append(prompt)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        last_text = ""
        async for line_bytes in process.stdout:
            line = line_bytes.decode().strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type == "assistant":
                content_blocks = data.get("message", {}).get("content", [])
                text_parts = []
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                if text_parts:
                    current_text = "\n".join(text_parts)
                    if current_text != last_text:
                        last_text = current_text
                        yield current_text
            elif msg_type == "result":
                result_text = data.get("result", "")
                if result_text and result_text != last_text:
                    yield result_text

        await process.wait()

    @property
    def has_file_access(self) -> bool:
        return self.backend.has_file_access
