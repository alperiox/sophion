"""Sophion MCP server — exposes knowledge base tools for Hermes Agent."""

import frontmatter
from mcp.server.fastmcp import FastMCP

from sophion.config import Config
from sophion.gaps import GapTracker
from sophion.ingest import ingest_file as _do_ingest_file
from sophion.ingest import ingest_url as _do_ingest_url
from sophion.latex_render import render_math_in_text
from sophion.store import Store

# Initialize global state
_config = Config.load()
_store = Store(_config)
_store.initialize()

mcp_app = FastMCP("sophion")


def _get_store() -> Store:
    return _store


def _get_tracker() -> GapTracker:
    return GapTracker(_store.learner_state / "gaps.json")


# --- Internal functions (testable without MCP) ---


def _list_articles(store: Store) -> str:
    articles = []
    for path in sorted(store.wiki.glob("*.md")):
        if path.name == "_index.md":
            continue
        post = frontmatter.load(str(path))
        title = post.get("title", path.stem)
        articles.append(f"- {path.stem}: {title}")

    if not articles:
        return "No articles in the knowledge base."
    return "\n".join(articles)


def _read_article(store: Store, name: str) -> str:
    path = store.wiki / f"{name}.md"
    if not path.exists():
        matches = list(store.wiki.glob(f"{name}*"))
        if matches:
            path = matches[0]
        else:
            return f"Article '{name}' not found."

    content = path.read_text()
    return render_math_in_text(content)


def _search_articles(store: Store, query: str) -> str:
    query_lower = query.lower()
    results = []

    for path in sorted(store.wiki.glob("*.md")):
        if path.name == "_index.md":
            continue
        content = path.read_text().lower()
        if query_lower in content:
            post = frontmatter.load(str(path))
            title = post.get("title", path.stem)
            for line in path.read_text().split("\n"):
                if query_lower in line.lower():
                    snippet = line.strip()[:100]
                    results.append(f"- **{title}** ({path.stem}): ...{snippet}...")
                    break

    if not results:
        return f"No articles found matching '{query}'."
    return f"Found {len(results)} result(s):\n" + "\n".join(results)


def _ingest_file(store: Store, file_path: str) -> str:
    path = _do_ingest_file(file_path, store)
    return f"Ingested: {path.name}"


def _render_math(text: str) -> str:
    return render_math_in_text(text)


def _compile_knowledge(store: Store) -> str:
    from sophion.backend import get_backend
    from sophion.compile import compile_all

    backend = get_backend(_config)
    results = compile_all(store, backend)

    if results:
        names = [p.name for p in results]
        return f"Compiled {len(results)} document(s): {', '.join(names)}"
    return "Nothing to compile — all documents are up to date."


def _list_gaps(store: Store) -> str:
    tracker = GapTracker(store.learner_state / "gaps.json")
    gaps = tracker.list_open()
    if not gaps:
        return "No open learning gaps."
    lines = []
    for gap in gaps:
        lines.append(f"- [{gap.id}] ({gap.topic}) {gap.question}")
    return f"{len(gaps)} open gap(s):\n" + "\n".join(lines)


def _add_gap(store: Store, topic: str, question: str) -> str:
    tracker = GapTracker(store.learner_state / "gaps.json")
    gap = tracker.add(topic, question)
    return f"Gap added [{gap.id}] ({topic}): {question}"


def _resolve_gap(store: Store, gap_id: str, resolution: str) -> str:
    tracker = GapTracker(store.learner_state / "gaps.json")
    gap = tracker.resolve(gap_id, resolution)
    if gap:
        return f"Gap resolved [{gap.id}]: {resolution}"
    return f"Gap '{gap_id}' not found."


# --- MCP Tool Definitions ---


@mcp_app.tool()
def list_articles() -> str:
    """List all articles in the Sophion knowledge base wiki with their titles."""
    return _list_articles(_get_store())


@mcp_app.tool()
def read_article(name: str) -> str:
    """Read a specific wiki article by name. LaTeX math is automatically converted to Unicode.

    Args:
        name: Article filename without extension (e.g., 'diffusion-models')
    """
    return _read_article(_get_store(), name)


@mcp_app.tool()
def search_articles(query: str) -> str:
    """Full-text search across all wiki articles. Returns matching articles with context snippets.

    Args:
        query: Text to search for (case-insensitive)
    """
    return _search_articles(_get_store(), query)


@mcp_app.tool()
def ingest_url(url: str) -> str:
    """Fetch a web page, convert to markdown, and add to the knowledge base raw/ directory.

    Args:
        url: The URL to fetch and ingest
    """
    store = _get_store()
    path = _do_ingest_url(url, store)
    return f"Ingested: {path.name}"


@mcp_app.tool()
def ingest_file(file_path: str) -> str:
    """Ingest a local markdown file into the knowledge base raw/ directory.

    Args:
        file_path: Absolute path to the file to ingest
    """
    return _ingest_file(_get_store(), file_path)


@mcp_app.tool()
def compile_knowledge() -> str:
    """Compile all unprocessed raw documents into wiki articles using the LLM.
    This creates structured wiki articles from raw ingested material.
    """
    return _compile_knowledge(_get_store())


@mcp_app.tool()
def render_math(text: str) -> str:
    """Convert LaTeX math notation ($..$ and $$..$$) to readable Unicode characters.

    Args:
        text: Text containing LaTeX math expressions
    """
    return _render_math(text)


@mcp_app.tool()
def list_gaps() -> str:
    """List all open learning gaps — topics you've accepted without fully understanding."""
    return _list_gaps(_get_store())


@mcp_app.tool()
def add_gap(topic: str, question: str) -> str:
    """Record a new learning gap — something you noticed you don't fully understand.

    Args:
        topic: The broad topic area (e.g., 'diffusion', 'attention')
        question: The specific question or gap in understanding
    """
    return _add_gap(_get_store(), topic, question)


@mcp_app.tool()
def resolve_gap(gap_id: str, resolution: str) -> str:
    """Mark a learning gap as resolved with your explanation of understanding.

    Args:
        gap_id: The gap ID (8-character hex string)
        resolution: Your explanation of how you now understand this
    """
    return _resolve_gap(_get_store(), gap_id, resolution)


def main():
    """Entry point for the sophion-mcp command."""
    mcp_app.run(transport="stdio")


if __name__ == "__main__":
    main()
