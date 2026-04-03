"""Shared utilities."""

import re


def slugify(text: str) -> str:
    """Convert text to a filename-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.ASCII)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
