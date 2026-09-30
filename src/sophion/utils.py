"""Shared utilities."""

import re


def slugify(text: str) -> str:
    """Convert text to a filename-friendly slug.

    Never returns an empty string: a title with no ASCII word characters
    (e.g. "\u91cf\u5b50\u529b\u5b66") would otherwise produce a filename of ".md", a dotfile
    that distinct articles then collide on.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.ASCII)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "untitled"
