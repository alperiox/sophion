"""Claude Code CLI backend using `claude -p`."""

import subprocess

from sophion.backend.base import LLMBackend


class ClaudeCodeBackend(LLMBackend):
    """LLM backend that uses the Claude Code CLI in print mode."""

    @property
    def has_file_access(self) -> bool:
        return True

    def _build_command(self, prompt: str, system_prompt: str = "") -> list[str]:
        cmd = ["claude", "-p", "--output-format", "text"]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        cmd.append(prompt)
        return cmd

    def query(self, prompt: str, system_prompt: str = "") -> str:
        cmd = self._build_command(prompt, system_prompt)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
