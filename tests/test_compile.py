from pathlib import Path
from unittest.mock import MagicMock

import frontmatter

from sophion.compile import compile_all, compile_document, update_index


def _make_raw_file(store, name: str = "test-article.md", content: str = "# Test\nSome content") -> Path:
    """Helper to create a raw file with frontmatter."""
    post = frontmatter.Post(
        content,
        title="Test Article",
        source="https://example.com",
        ingested="2026-04-03",
        compiled=False,
    )
    path = store.raw / name
    path.write_text(frontmatter.dumps(post))
    return path


def test_compile_document(store):
    raw_file = _make_raw_file(store)

    mock_backend = MagicMock()
    mock_backend.query.return_value = (
        "# Test Article\n\n"
        "## Summary\n\n"
        "This article covers testing concepts.\n\n"
        "## Key Concepts\n\n"
        "- Testing is important\n"
        "- [[unit-testing]] helps catch bugs\n"
    )

    wiki_path = compile_document(raw_file, store, mock_backend)

    assert wiki_path.exists()
    assert wiki_path.parent == store.wiki

    wiki_post = frontmatter.load(str(wiki_path))
    assert wiki_post["title"] == "Test Article"
    assert wiki_post["source_raw"] == "test-article.md"
    assert "testing concepts" in wiki_post.content

    raw_post = frontmatter.load(str(raw_file))
    assert raw_post["compiled"] is True


def test_compile_document_calls_backend_with_content(store):
    raw_file = _make_raw_file(store, content="# Deep Learning\nNeural networks are...")

    mock_backend = MagicMock()
    mock_backend.query.return_value = "# Deep Learning\n\nCompiled article."

    compile_document(raw_file, store, mock_backend)

    call_args = mock_backend.query.call_args
    prompt = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
    assert "Neural networks are" in prompt


def test_compile_all_processes_uncompiled(store):
    _make_raw_file(store, name="article-1.md")
    _make_raw_file(store, name="article-2.md")

    already_compiled = store.raw / "article-3.md"
    post = frontmatter.Post("Done", title="Done", compiled=True)
    already_compiled.write_text(frontmatter.dumps(post))

    mock_backend = MagicMock()
    mock_backend.query.return_value = "# Compiled\n\nContent."

    results = compile_all(store, mock_backend)
    assert len(results) == 2


def test_compile_all_empty(store):
    mock_backend = MagicMock()
    results = compile_all(store, mock_backend)
    assert results == []


def test_update_index(store):
    wiki_file = store.wiki / "test-article.md"
    post = frontmatter.Post(
        "# Test Article\n\nContent about testing.",
        title="Test Article",
        source_raw="test-article.md",
    )
    wiki_file.write_text(frontmatter.dumps(post))

    mock_backend = MagicMock()
    mock_backend.query.return_value = (
        "# Knowledge Base Index\n\n"
        "## Articles\n\n"
        "- [[test-article]] — An article about testing\n"
    )

    update_index(store, mock_backend)

    index_path = store.wiki / "_index.md"
    assert index_path.exists()
    assert "test-article" in index_path.read_text()
