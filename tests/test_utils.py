from sophion.utils import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_special_chars():
    assert slugify("Attention Is All You Need!") == "attention-is-all-you-need"


def test_slugify_extra_spaces():
    assert slugify("  lots   of   spaces  ") == "lots-of-spaces"


def test_slugify_underscores():
    assert slugify("some_thing_here") == "some-thing-here"


def test_slugify_consecutive_dashes():
    assert slugify("one---two") == "one-two"


def test_slugify_unicode():
    assert slugify("café latte") == "caf-latte"
