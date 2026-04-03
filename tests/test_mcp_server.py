import re

import frontmatter

from sophion.mcp_server import (
    _add_gap,
    _compile_knowledge,
    _ingest_file,
    _list_articles,
    _list_gaps,
    _read_article,
    _render_math,
    _resolve_gap,
    _search_articles,
)


def test_list_articles_empty(store):
    articles = _list_articles(store)
    assert articles == "No articles in the knowledge base."


def test_list_articles_with_files(store):
    post = frontmatter.Post("# Test\nContent", title="Test Article")
    (store.wiki / "test-article.md").write_text(frontmatter.dumps(post))

    result = _list_articles(store)
    assert "test-article" in result
    assert "Test Article" in result


def test_list_articles_skips_index(store):
    (store.wiki / "_index.md").write_text("# Index")
    post = frontmatter.Post("Content", title="Real Article")
    (store.wiki / "real.md").write_text(frontmatter.dumps(post))

    result = _list_articles(store)
    assert "_index" not in result
    assert "Real Article" in result


def test_read_article(store):
    post = frontmatter.Post(
        r"# Diffusion" + "\n" + r"The variable $\alpha$ controls noise.",
        title="Diffusion Models",
    )
    (store.wiki / "diffusion.md").write_text(frontmatter.dumps(post))

    result = _read_article(store, "diffusion")
    assert "Diffusion" in result
    assert "α" in result
    assert "$" not in result


def test_read_article_not_found(store):
    result = _read_article(store, "nonexistent")
    assert "not found" in result.lower()


def test_search_articles(store):
    post1 = frontmatter.Post("# Attention\nSelf-attention is key.", title="Attention")
    (store.wiki / "attention.md").write_text(frontmatter.dumps(post1))

    post2 = frontmatter.Post("# Diffusion\nNoise schedule.", title="Diffusion")
    (store.wiki / "diffusion.md").write_text(frontmatter.dumps(post2))

    result = _search_articles(store, "attention")
    assert "attention" in result.lower()


def test_search_articles_no_results(store):
    result = _search_articles(store, "quantum computing")
    assert "no articles" in result.lower() or "no results" in result.lower()


def test_render_math():
    result = _render_math(r"The formula $\alpha + \beta$ is important.")
    assert "α" in result
    assert "β" in result
    assert "$" not in result


def test_ingest_file_tool(store, tmp_path):
    source = tmp_path / "notes.md"
    source.write_text("# My Notes\nSome content here.")

    result = _ingest_file(store, str(source))
    assert "ingested" in result.lower() or "my-notes" in result.lower()

    raw_files = list(store.raw.glob("*.md"))
    assert len(raw_files) == 1


def test_list_gaps(store):
    result = _list_gaps(store)
    assert "no open" in result.lower() or "no gaps" in result.lower()


def test_add_gap(store):
    result = _add_gap(store, "diffusion", "Why does noise schedule matter?")
    assert "added" in result.lower() or "diffusion" in result.lower()

    result2 = _list_gaps(store)
    assert "diffusion" in result2


def test_resolve_gap(store):
    add_result = _add_gap(store, "attention", "How does masking work?")
    match = re.search(r"[a-f0-9]{8}", add_result)
    if match:
        gap_id = match.group(0)
        result = _resolve_gap(store, gap_id, "Masking prevents attention to future tokens")
        assert "resolved" in result.lower()
