import frontmatter

from sophion.store import Store


def test_store_initialize(config):
    store = Store(config)
    store.initialize()

    assert store.raw.is_dir()
    assert store.wiki.is_dir()
    assert store.gaps.is_dir()
    assert store.conversations.is_dir()
    assert store.learner_state.is_dir()


def test_store_initialize_is_idempotent(config):
    store = Store(config)
    store.initialize()
    store.initialize()
    assert store.raw.is_dir()


def test_store_paths(config):
    store = Store(config)
    assert store.raw == config.base_dir / "knowledge" / "raw"
    assert store.wiki == config.base_dir / "knowledge" / "wiki"
    assert store.gaps == config.base_dir / "knowledge" / "gaps"
    assert store.conversations == config.base_dir / "conversations"
    assert store.learner_state == config.base_dir / "learner_state"


def test_uncompiled_files_empty(store):
    assert store.uncompiled_files() == []


def test_uncompiled_files_finds_uncompiled(store):
    raw_file = store.raw / "test-article.md"
    post = frontmatter.Post(
        "# Test\nSome content",
        title="Test Article",
        compiled=False,
    )
    raw_file.write_text(frontmatter.dumps(post))

    result = store.uncompiled_files()
    assert len(result) == 1
    assert result[0] == raw_file


def test_uncompiled_files_skips_compiled(store):
    compiled_file = store.raw / "done-article.md"
    post = frontmatter.Post(
        "# Done\nAlready compiled",
        title="Done Article",
        compiled=True,
    )
    compiled_file.write_text(frontmatter.dumps(post))

    assert store.uncompiled_files() == []


def test_uncompiled_files_mixed(store):
    uncompiled = store.raw / "new.md"
    post1 = frontmatter.Post("New content", title="New", compiled=False)
    uncompiled.write_text(frontmatter.dumps(post1))

    compiled = store.raw / "old.md"
    post2 = frontmatter.Post("Old content", title="Old", compiled=True)
    compiled.write_text(frontmatter.dumps(post2))

    result = store.uncompiled_files()
    assert len(result) == 1
    assert result[0] == uncompiled
