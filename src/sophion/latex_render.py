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


_MATH_SIGNAL = re.compile(r"[\\^_{]")


def _render_if_math(inner: str) -> str | None:
    """Render `inner` if it is unambiguously a math span, else None.

    Requires no whitespace against the delimiters (the usual Markdown-math
    rule) and at least one LaTeX signal character.
    """
    if not inner or inner[0].isspace() or inner[-1].isspace():
        return None
    if not _MATH_SIGNAL.search(inner):
        return None
    return render_inline_math(inner)


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

    # Then handle inline math ($...$).
    # "$" is ambiguous in prose, so a span only counts as math when it both
    # has no whitespace against the delimiters and carries a LaTeX signal.
    # This keeps "$5 and $10", "$HOME and $PATH" and "\\$5" intact.
    text = re.sub(
        r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)",
        lambda m: _render_if_math(m.group(1)) or m.group(0),
        text,
    )

    return text
