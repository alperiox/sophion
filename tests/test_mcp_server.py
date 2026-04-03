import re

import frontmatter

from sophion.mcp_server import (
    _ServerState,
    _add_gap,
    _compile_knowledge,
    _create_base,
    _ingest_file,
    _lint_knowledge,
    _list_articles,
    _list_bases,
    _list_gaps,
    _read_article,
    _render_math,
    _resolve_gap,
    _search_articles,
    _state,
    _study_status,
    _switch_base,
    _toggle_study_mode,
    _update_article,
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


# --- update_article tests ---


def test_update_article_creates_new(store):
    result = _update_article(store, "Score Matching", "# Score Matching\n\nContent here.")
    assert "created" in result.lower()
    assert (store.wiki / "score-matching.md").exists()

    post = frontmatter.load(str(store.wiki / "score-matching.md"))
    assert post["title"] == "Score Matching"
    assert "Content here." in post.content


def test_update_article_overwrites_existing(store):
    # Create initial
    _update_article(store, "Test Article", "# V1\nFirst version.")
    # Overwrite
    result = _update_article(store, "Test Article", "# V2\nSecond version.")
    assert "updated" in result.lower()

    post = frontmatter.load(str(store.wiki / "test-article.md"))
    assert "Second version." in post.content
    assert "First version." not in post.content


def test_update_article_readable(store):
    _update_article(store, "My Article", "# My Article\n\nSome content.")
    result = _read_article(store, "my-article")
    assert "My Article" in result


# --- lint_knowledge tests ---


def test_lint_empty_kb(store):
    result = _lint_knowledge(store)
    assert "empty" in result.lower()


def test_lint_healthy_kb(store):
    # Two articles referencing each other — no issues
    post1 = frontmatter.Post(
        "# Attention\n\nRelated to [[diffusion]].\n\n" + ("word " * 100),
        title="Attention",
    )
    (store.wiki / "attention.md").write_text(frontmatter.dumps(post1))

    post2 = frontmatter.Post(
        "# Diffusion\n\nRelated to [[attention]].\n\n" + ("word " * 100),
        title="Diffusion",
    )
    (store.wiki / "diffusion.md").write_text(frontmatter.dumps(post2))

    # Add index so it doesn't flag missing
    (store.wiki / "_index.md").write_text("# Index\n")

    result = _lint_knowledge(store)
    assert "healthy" in result.lower()


def test_lint_finds_broken_wikilinks(store):
    post = frontmatter.Post(
        "# Article\n\nSee [[nonexistent-topic]] for more.\n\n" + ("word " * 100),
        title="Article",
    )
    (store.wiki / "article.md").write_text(frontmatter.dumps(post))
    (store.wiki / "_index.md").write_text("# Index\n")

    result = _lint_knowledge(store)
    assert "broken-link" in result
    assert "nonexistent-topic" in result


def test_lint_finds_thin_articles(store):
    post = frontmatter.Post("# Thin\n\nShort.", title="Thin")
    (store.wiki / "thin.md").write_text(frontmatter.dumps(post))
    (store.wiki / "_index.md").write_text("# Index\n")

    result = _lint_knowledge(store)
    assert "thin-article" in result


def test_lint_finds_orphans(store):
    # Two articles, neither references the other
    post1 = frontmatter.Post(
        "# Standalone A\n\n" + ("word " * 100), title="Standalone A"
    )
    (store.wiki / "standalone-a.md").write_text(frontmatter.dumps(post1))

    post2 = frontmatter.Post(
        "# Standalone B\n\n" + ("word " * 100), title="Standalone B"
    )
    (store.wiki / "standalone-b.md").write_text(frontmatter.dumps(post2))
    (store.wiki / "_index.md").write_text("# Index\n")

    result = _lint_knowledge(store)
    assert "orphan" in result


def test_lint_finds_uncompiled(store):
    post = frontmatter.Post(
        "# Article\n\n" + ("word " * 100), title="Article"
    )
    (store.wiki / "article.md").write_text(frontmatter.dumps(post))
    (store.wiki / "_index.md").write_text("# Index\n")

    # Add an uncompiled raw file
    raw_post = frontmatter.Post("Raw content", title="Raw", compiled=False)
    (store.raw / "raw-doc.md").write_text(frontmatter.dumps(raw_post))

    result = _lint_knowledge(store)
    assert "uncompiled" in result
    assert "raw-doc.md" in result


# --- Multi-base management tests ---


# --- Study mode toggle tests ---


def test_toggle_study_mode_on(store):
    result = _toggle_study_mode(store)
    assert "activated" in result.lower()
    assert _study_status(store) == f"Study mode is ACTIVE (since {result.split('since ')[-1].rstrip(')')}" or "ACTIVE" in _study_status(store)


def test_toggle_study_mode_off(store):
    _toggle_study_mode(store)  # on
    result = _toggle_study_mode(store)  # off
    assert "ended" in result.lower()
    assert "OFF" in _study_status(store)


def test_toggle_study_mode_shows_gaps(store):
    _add_gap(store, "diffusion", "What is ELBO?")
    result = _toggle_study_mode(store)  # on
    assert "diffusion" in result
    assert "ELBO" in result


def test_toggle_study_mode_summary(store):
    _toggle_study_mode(store)  # on
    _add_gap(store, "attention", "How does masking work?")
    result = _toggle_study_mode(store)  # off
    assert "ended" in result.lower()
    assert "attention" in result
    assert "masking" in result.lower()


def test_study_status_off(store):
    result = _study_status(store)
    assert "OFF" in result


# --- Multi-base management tests ---


def test_list_bases_none(tmp_path):
    state = _ServerState(base_dir=tmp_path / "default")
    state.bases_dir = tmp_path / "bases"  # doesn't exist
    old_state_bases = _state.bases_dir
    _state.bases_dir = state.bases_dir
    try:
        result = _list_bases()
        assert "no named bases" in result.lower()
    finally:
        _state.bases_dir = old_state_bases


def test_create_base(tmp_path):
    old_bases = _state.bases_dir
    old_store = _state.store
    old_name = _state.current_base_name
    _state.bases_dir = tmp_path / "bases"
    try:
        result = _create_base("diffusion")
        assert "created" in result.lower()
        assert "switched" in result.lower()
        assert (tmp_path / "bases" / "diffusion" / "knowledge" / "wiki").is_dir()
        assert _state.current_base_name == "diffusion"
    finally:
        _state.bases_dir = old_bases
        _state.store = old_store
        _state.current_base_name = old_name


def test_create_base_already_exists(tmp_path):
    old_bases = _state.bases_dir
    old_store = _state.store
    old_name = _state.current_base_name
    _state.bases_dir = tmp_path / "bases"
    try:
        _create_base("diffusion")
        result = _create_base("diffusion")
        assert "already exists" in result.lower()
    finally:
        _state.bases_dir = old_bases
        _state.store = old_store
        _state.current_base_name = old_name


def test_switch_base(tmp_path):
    old_bases = _state.bases_dir
    old_store = _state.store
    old_name = _state.current_base_name
    _state.bases_dir = tmp_path / "bases"
    try:
        _create_base("attention")
        result = _switch_base("attention")
        assert "switched" in result.lower()
        assert "attention" in result.lower()
        assert _state.current_base_name == "attention"
        assert _state.store.base == tmp_path / "bases" / "attention"
    finally:
        _state.bases_dir = old_bases
        _state.store = old_store
        _state.current_base_name = old_name


def test_switch_base_not_found(tmp_path):
    old_bases = _state.bases_dir
    _state.bases_dir = tmp_path / "bases"
    try:
        result = _switch_base("nonexistent")
        assert "not found" in result.lower()
    finally:
        _state.bases_dir = old_bases


def test_list_bases_shows_created(tmp_path):
    old_bases = _state.bases_dir
    old_store = _state.store
    old_name = _state.current_base_name
    _state.bases_dir = tmp_path / "bases"
    try:
        _create_base("diffusion")
        _create_base("attention")
        result = _list_bases()
        assert "2 knowledge base" in result
        assert "diffusion" in result
        assert "attention" in result
    finally:
        _state.bases_dir = old_bases
        _state.store = old_store
        _state.current_base_name = old_name


def test_switch_base_isolates_articles(tmp_path):
    old_bases = _state.bases_dir
    old_store = _state.store
    old_name = _state.current_base_name
    _state.bases_dir = tmp_path / "bases"
    try:
        # Create two bases with different articles
        _create_base("base-a")
        _switch_base("base-a")
        _update_article(_state.store, "Article A", "Content for A")

        _create_base("base-b")
        _switch_base("base-b")
        _update_article(_state.store, "Article B", "Content for B")

        # base-b should only have Article B
        result_b = _list_articles(_state.store)
        assert "Article B" in result_b
        assert "Article A" not in result_b

        # Switch back to base-a — should only have Article A
        _switch_base("base-a")
        result_a = _list_articles(_state.store)
        assert "Article A" in result_a
        assert "Article B" not in result_a
    finally:
        _state.bases_dir = old_bases
        _state.store = old_store
        _state.current_base_name = old_name
