from sophion.latex_render import render_inline_math, render_math_in_text


def test_render_inline_basic_greek():
    result = render_inline_math(r"\alpha + \beta")
    assert "α" in result
    assert "β" in result


def test_render_inline_subscript():
    result = render_inline_math(r"x_0")
    assert "₀" in result


def test_render_inline_superscript():
    result = render_inline_math(r"x^2")
    assert "²" in result


def test_render_inline_sqrt():
    result = render_inline_math(r"\sqrt{x}")
    assert "√" in result


def test_render_inline_calligraphic():
    result = render_inline_math(r"\mathcal{N}")
    assert "𝒩" in result


def test_render_inline_nabla():
    result = render_inline_math(r"\nabla")
    assert "∇" in result


def test_render_inline_partial():
    result = render_inline_math(r"\partial")
    assert "∂" in result


def test_render_inline_sum():
    result = render_inline_math(r"\sum")
    assert "∑" in result


def test_render_math_in_text_inline():
    text = r"The variable $\alpha$ is important."
    result = render_math_in_text(text)
    assert "α" in result
    assert "$" not in result


def test_render_math_in_text_block():
    text = "Formula:\n$$\\alpha + \\beta = \\gamma$$\nDone."
    result = render_math_in_text(text)
    assert "α" in result
    assert "β" in result
    assert "γ" in result
    assert "$$" not in result


def test_render_math_in_text_no_math():
    text = "No math here, just plain text."
    result = render_math_in_text(text)
    assert result == text


def test_render_math_in_text_mixed():
    text = r"Given $x_0$ and the formula $$q(x_t | x_0) = \mathcal{N}(x_t)$$, we see..."
    result = render_math_in_text(text)
    assert "$" not in result
    assert "₀" in result
    assert "𝒩" in result


def test_render_math_in_text_preserves_non_math():
    text = r"Hello world. The value $\alpha$ is 5. Goodbye."
    result = render_math_in_text(text)
    assert result.startswith("Hello world.")
    assert result.endswith("Goodbye.")
    assert "α" in result
