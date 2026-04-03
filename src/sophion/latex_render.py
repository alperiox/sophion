"""LaTeX to Unicode rendering for terminal display."""

import re

import unicodeit


def render_inline_math(latex: str) -> str:
    """Convert a LaTeX math expression to Unicode.

    Uses unicodeit for symbol conversion with fallback to raw text.
    """
    try:
        return unicodeit.replace(latex)
    except Exception:
        return latex


def render_math_in_text(text: str) -> str:
    """Find and render all LaTeX math in a text string.

    Handles both inline ($...$) and block ($$...$$) math.
    Block math delimiters are replaced but the content stays inline
    (Unicode can't render display-mode layout).
    """
    # First handle block math ($$...$$) — must come before inline
    text = re.sub(
        r"\$\$(.+?)\$\$",
        lambda m: render_inline_math(m.group(1)),
        text,
        flags=re.DOTALL,
    )

    # Then handle inline math ($...$)
    # Avoid matching dollar signs that aren't math (e.g., "$5")
    text = re.sub(
        r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)",
        lambda m: render_inline_math(m.group(1)),
        text,
    )

    return text
