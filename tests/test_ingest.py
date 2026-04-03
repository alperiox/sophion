from pathlib import Path
from unittest.mock import MagicMock, patch

import frontmatter

from sophion.ingest import _normalize_url, ingest_file, ingest_url


def test_ingest_url(store):
    mock_response = MagicMock()
    mock_response.text = (
        "<html><head><title>Test Article</title></head>"
        "<body><h1>Test</h1><p>Hello world</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    with patch("sophion.ingest.httpx.get", return_value=mock_response):
        path = ingest_url("https://example.com/article", store)

    assert path.exists()
    assert path.parent == store.raw

    post = frontmatter.load(str(path))
    assert post["title"] == "Test Article"
    assert post["source"] == "https://example.com/article"
    assert post["compiled"] is False
    assert "Hello world" in post.content


def test_ingest_url_no_title(store):
    mock_response = MagicMock()
    mock_response.text = "<html><body><p>No title page</p></body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("sophion.ingest.httpx.get", return_value=mock_response):
        path = ingest_url("https://example.com/page", store)

    post = frontmatter.load(str(path))
    assert post["title"] == "example.com/page"


def test_ingest_url_filename_includes_date(store):
    mock_response = MagicMock()
    mock_response.text = (
        "<html><head><title>My Article</title></head>"
        "<body><p>Content</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    with patch("sophion.ingest.httpx.get", return_value=mock_response):
        path = ingest_url("https://example.com/my-article", store)

    assert path.name.startswith("20")
    assert "my-article" in path.name


def test_ingest_file(store, tmp_path):
    source = tmp_path / "notes.md"
    source.write_text("# My Notes\n\nSome personal notes here.")

    path = ingest_file(str(source), store)

    assert path.exists()
    assert path.parent == store.raw

    post = frontmatter.load(str(path))
    assert post["title"] == "My Notes"
    assert post["source"] == str(source)
    assert post["compiled"] is False
    assert "Some personal notes here." in post.content


def test_ingest_file_no_heading(store, tmp_path):
    source = tmp_path / "plain.md"
    source.write_text("Just some text without a heading.")

    path = ingest_file(str(source), store)

    post = frontmatter.load(str(path))
    assert post["title"] == "plain"


def test_ingest_file_preserves_existing_frontmatter(store, tmp_path):
    source = tmp_path / "with-meta.md"
    post = frontmatter.Post("Content here", title="Original Title", author="Alper")
    source.write_text(frontmatter.dumps(post))

    path = ingest_file(str(source), store)

    loaded = frontmatter.load(str(path))
    assert loaded["title"] == "Original Title"
    assert loaded["author"] == "Alper"
    assert loaded["compiled"] is False


# --- URL normalization tests ---


def test_normalize_arxiv_abs():
    result = _normalize_url("https://arxiv.org/abs/2106.09685")
    assert result == "https://ar5iv.labs.arxiv.org/html/2106.09685"


def test_normalize_arxiv_pdf():
    result = _normalize_url("https://arxiv.org/pdf/2106.09685")
    assert result == "https://ar5iv.labs.arxiv.org/html/2106.09685"


def test_normalize_arxiv_pdf_with_extension():
    result = _normalize_url("https://arxiv.org/pdf/2106.09685.pdf")
    assert result == "https://ar5iv.labs.arxiv.org/html/2106.09685"


def test_normalize_non_arxiv_unchanged():
    url = "https://example.com/article"
    assert _normalize_url(url) == url


def test_normalize_ar5iv_unchanged():
    url = "https://ar5iv.labs.arxiv.org/html/2106.09685"
    assert _normalize_url(url) == url
