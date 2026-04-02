import pytest
from unittest.mock import MagicMock, patch

import frontmatter
from click.testing import CliRunner

from sophion.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_init_command(runner, tmp_base):
    result = runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])
    assert result.exit_code == 0
    assert "Initialized" in result.output
    assert (tmp_base / "knowledge" / "raw").is_dir()
    assert (tmp_base / "knowledge" / "wiki").is_dir()


def test_init_command_already_initialized(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])
    result = runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])
    assert result.exit_code == 0


def test_ingest_url(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    mock_response = MagicMock()
    mock_response.text = (
        "<html><head><title>Test</title></head>"
        "<body><p>Content</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    with patch("sophion.ingest.httpx.get", return_value=mock_response):
        result = runner.invoke(
            cli,
            ["--base-dir", str(tmp_base), "ingest", "https://example.com/test"],
        )

    assert result.exit_code == 0
    assert "Ingested" in result.output


def test_ingest_file(runner, tmp_base, tmp_path):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    source = tmp_path / "notes.md"
    source.write_text("# Notes\nSome notes.")

    result = runner.invoke(
        cli,
        ["--base-dir", str(tmp_base), "ingest", str(source)],
    )

    assert result.exit_code == 0
    assert "Ingested" in result.output


def test_compile_command(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    raw_dir = tmp_base / "knowledge" / "raw"
    post = frontmatter.Post("# Test\nContent", title="Test", compiled=False)
    (raw_dir / "test.md").write_text(frontmatter.dumps(post))

    mock_backend = MagicMock()
    mock_backend.query.return_value = "# Test\n\nCompiled content."

    with patch("sophion.cli.get_backend", return_value=mock_backend):
        result = runner.invoke(
            cli,
            ["--base-dir", str(tmp_base), "compile"],
        )

    assert result.exit_code == 0
    assert "Compiled 1" in result.output


def test_compile_command_nothing_to_compile(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    mock_backend = MagicMock()
    with patch("sophion.cli.get_backend", return_value=mock_backend):
        result = runner.invoke(
            cli,
            ["--base-dir", str(tmp_base), "compile"],
        )

    assert result.exit_code == 0
    assert "Nothing to compile" in result.output


def test_query_command(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    wiki_dir = tmp_base / "knowledge" / "wiki"
    index_post = frontmatter.Post("# Index\n\n- [[test-article]]")
    (wiki_dir / "_index.md").write_text(frontmatter.dumps(index_post))

    mock_backend = MagicMock()
    mock_backend.has_file_access = True
    mock_backend.query.return_value = "The answer is 42."

    with patch("sophion.cli.get_backend", return_value=mock_backend):
        result = runner.invoke(
            cli,
            ["--base-dir", str(tmp_base), "query", "What is the answer?"],
        )

    assert result.exit_code == 0
    assert "42" in result.output


def test_query_empty_wiki(runner, tmp_base):
    runner.invoke(cli, ["--base-dir", str(tmp_base), "init"])

    mock_backend = MagicMock()
    with patch("sophion.cli.get_backend", return_value=mock_backend):
        result = runner.invoke(
            cli,
            ["--base-dir", str(tmp_base), "query", "anything"],
        )

    assert result.exit_code == 0
    assert "empty" in result.output.lower()
