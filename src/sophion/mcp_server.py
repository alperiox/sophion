"""Sophion MCP server — exposes knowledge base tools for Hermes Agent."""

import re
from datetime import datetime
from pathlib import Path

import frontmatter
from mcp.server.fastmcp import FastMCP

from sophion.config import Config
from sophion.gaps import GapTracker, StudySession
from sophion.ingest import ingest_file as _do_ingest_file
from sophion.ingest import ingest_url as _do_ingest_url
from sophion.latex_render import render_math_in_text
from sophion.store import Store
from sophion.utils import slugify

# --- Multi-base state management ---

_DEFAULT_BASES_DIR = Path.home() / ".sophion" / "bases"


class _ServerState:
    """Mutable server state supporting multiple knowledge bases."""

    def __init__(self, base_dir: Path | None = None):
        self.bases_dir = _DEFAULT_BASES_DIR
        if base_dir:
            config = Config(base_dir=base_dir)
        else:
            config = Config.load()
        self.store = Store(config)
        self.store.initialize()
        self.config = config
        self.current_base_name: str | None = None

    def switch_base(self, name: str) -> Store:
        """Switch to a named knowledge base under bases_dir."""
        base_path = self.bases_dir / name
        self.config = Config(base_dir=base_path)
        self.store = Store(self.config)
        self.store.initialize()
        self.current_base_name = name
        return self.store


_state = _ServerState()

mcp_app = FastMCP("sophion")


def _get_store() -> Store:
    return _state.store


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

    backend = get_backend(_state.config)
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


def _update_article(store: Store, name: str, content: str) -> str:
    """Create or overwrite a wiki article."""
    slug = slugify(name)
    path = store.wiki / f"{slug}.md"

    is_new = not path.exists()

    post = frontmatter.Post(
        content,
        title=name,
        updated_at=datetime.now().isoformat(),
    )
    if is_new:
        post["created_at"] = datetime.now().isoformat()

    path.write_text(frontmatter.dumps(post))

    action = "Created" if is_new else "Updated"
    return f"{action} article: {slug}.md"


def _lint_knowledge(store: Store) -> str:
    """Scan the wiki for health issues and improvement suggestions."""
    issues = []

    articles = {}
    for path in sorted(store.wiki.glob("*.md")):
        if path.name == "_index.md":
            continue
        content = path.read_text()
        post = frontmatter.load(str(path))
        title = post.get("title", path.stem)
        articles[path.stem] = {
            "title": title,
            "content": content,
            "path": path,
            "word_count": len(content.split()),
        }

    if not articles:
        return "Knowledge base is empty. Nothing to lint."

    # 1. Find broken wikilinks — [[referenced]] but no article exists
    all_slugs = set(articles.keys())
    for slug, info in articles.items():
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", info["content"])
        for link in wikilinks:
            link_slug = slugify(link)
            if link_slug and link_slug not in all_slugs:
                issues.append(
                    f"[broken-link] '{info['title']}' references [[{link}]] "
                    f"but no article '{link_slug}' exists"
                )

    # 2. Find thin articles (under 100 words of content)
    for slug, info in articles.items():
        if info["word_count"] < 100:
            issues.append(
                f"[thin-article] '{info['title']}' has only "
                f"{info['word_count']} words — consider expanding"
            )

    # 3. Find orphan articles (not referenced by any other article)
    referenced_slugs = set()
    for info in articles.values():
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", info["content"])
        for link in wikilinks:
            referenced_slugs.add(slugify(link))

    for slug in all_slugs:
        if slug not in referenced_slugs:
            issues.append(
                f"[orphan] '{articles[slug]['title']}' is not referenced "
                f"by any other article"
            )

    # 4. Check for missing index
    index_path = store.wiki / "_index.md"
    if not index_path.exists():
        issues.append("[missing-index] No _index.md found — run compile to generate")

    # 5. Check for uncompiled raw files
    uncompiled = store.uncompiled_files()
    if uncompiled:
        names = [p.name for p in uncompiled]
        issues.append(
            f"[uncompiled] {len(uncompiled)} raw file(s) not yet compiled: "
            f"{', '.join(names)}"
        )

    if not issues:
        return (
            f"Knowledge base is healthy. "
            f"{len(articles)} article(s), no issues found."
        )

    summary = f"Found {len(issues)} issue(s) across {len(articles)} article(s):\n"
    return summary + "\n".join(issues)


def _list_bases() -> str:
    """List all available knowledge bases."""
    bases_dir = _state.bases_dir
    if not bases_dir.exists():
        current = f"Using default base at {_state.store.base}"
        if _state.current_base_name:
            current = f"Current: {_state.current_base_name}"
        return f"No named bases found.\n{current}"

    bases = sorted(
        d.name for d in bases_dir.iterdir() if d.is_dir()
    )

    if not bases:
        return f"No named bases found.\nUsing default base at {_state.store.base}"

    lines = []
    for name in bases:
        store = Store(Config(base_dir=bases_dir / name))
        wiki_count = len([
            p for p in store.wiki.glob("*.md")
            if p.exists() and p.name != "_index.md"
        ]) if store.wiki.exists() else 0
        marker = " ← active" if name == _state.current_base_name else ""
        lines.append(f"- {name} ({wiki_count} articles){marker}")

    header = f"{len(bases)} knowledge base(s):\n"
    if not _state.current_base_name:
        header += f"(using default base at {_state.store.base})\n"
    return header + "\n".join(lines)


def _create_base(name: str) -> str:
    """Create a new named knowledge base."""
    base_path = _state.bases_dir / name
    if base_path.exists():
        return f"Base '{name}' already exists. Use switch_base to activate it."

    config = Config(base_dir=base_path)
    store = Store(config)
    store.initialize()
    return f"Created knowledge base '{name}' at {base_path}"


def _switch_base(name: str) -> str:
    """Switch to a named knowledge base."""
    base_path = _state.bases_dir / name
    if not base_path.exists():
        return f"Base '{name}' not found. Use create_base to create it first."

    store = _state.switch_base(name)

    wiki_count = len([
        p for p in store.wiki.glob("*.md") if p.name != "_index.md"
    ])
    gap_tracker = GapTracker(store.learner_state / "gaps.json")
    open_gaps = len(gap_tracker.list_open())

    return (
        f"Switched to '{name}' — "
        f"{wiki_count} article(s), {open_gaps} open gap(s)"
    )


def _toggle_study_mode(store: Store) -> str:
    """Toggle study mode on/off. Returns session summary when stopping."""
    session = StudySession(store.learner_state / "study_session.json")

    if session.is_active():
        # Stopping — generate summary
        started_at = session.stop()
        tracker = GapTracker(store.learner_state / "gaps.json")
        added, resolved = tracker.gaps_since(started_at)

        lines = ["Study session ended."]
        if added:
            lines.append(f"\nGaps surfaced ({len(added)}):")
            for gap in added:
                lines.append(f"  - ({gap.topic}) {gap.question}")
        if resolved:
            lines.append(f"\nGaps resolved ({len(resolved)}):")
            for gap in resolved:
                lines.append(f"  - ({gap.topic}) {gap.question}")
        if not added and not resolved:
            lines.append("No gaps were added or resolved during this session.")

        return "\n".join(lines)
    else:
        # Starting
        session.start()
        tracker = GapTracker(store.learner_state / "gaps.json")
        open_gaps = tracker.list_open()

        lines = ["Study mode activated. Challenger agent is now active."]
        if open_gaps:
            lines.append(f"\n{len(open_gaps)} open gap(s) to revisit:")
            for gap in open_gaps:
                lines.append(f"  - [{gap.id}] ({gap.topic}) {gap.question}")
        else:
            lines.append("No open gaps. What topic would you like to study?")

        return "\n".join(lines)


def _study_status(store: Store) -> str:
    """Check if study mode is active."""
    session = StudySession(store.learner_state / "study_session.json")
    if session.is_active():
        return f"Study mode is ACTIVE (since {session.started_at})"
    return "Study mode is OFF"


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


@mcp_app.tool()
def update_article(name: str, content: str) -> str:
    """Create or update a wiki article. Use this to file outputs back into the knowledge base.

    The article is saved with frontmatter (title, timestamps). If an article
    with this name already exists, it is overwritten.

    Args:
        name: Article title (will be slugified for the filename)
        content: Full markdown content of the article
    """
    return _update_article(_get_store(), name, content)


@mcp_app.tool()
def lint_knowledge() -> str:
    """Run health checks on the knowledge base and report issues.

    Checks for:
    - Broken wikilinks ([[referenced]] but no article exists)
    - Thin articles (under 100 words)
    - Orphan articles (not referenced by any other article)
    - Missing index file
    - Uncompiled raw documents

    Use the results to improve the wiki: create missing articles,
    expand thin ones, add cross-references, or compile raw documents.
    """
    return _lint_knowledge(_get_store())


@mcp_app.tool()
def toggle_study_mode() -> str:
    """Toggle study mode on or off.

    When activated: The challenger agent becomes active, surfacing knowledge gaps
    and testing your understanding. Shows any open gaps to revisit.

    When deactivated: Returns a session summary showing gaps surfaced and resolved
    during the session. The challenger agent stops challenging.
    """
    return _toggle_study_mode(_get_store())


@mcp_app.tool()
def study_status() -> str:
    """Check whether study mode is currently active or off."""
    return _study_status(_get_store())


@mcp_app.tool()
def list_bases() -> str:
    """List all available knowledge bases and show which one is active.

    Knowledge bases are separate wikis for different research topics.
    Each has its own articles, gaps, and conversation history.
    """
    return _list_bases()


@mcp_app.tool()
def create_base(name: str) -> str:
    """Create a new named knowledge base for a research topic.

    Args:
        name: Name for the knowledge base (e.g., 'diffusion', 'attention', 'rl')
    """
    return _create_base(name)


@mcp_app.tool()
def switch_base(name: str) -> str:
    """Switch to a different knowledge base. All subsequent operations will use this base.

    Args:
        name: Name of the knowledge base to switch to
    """
    return _switch_base(name)


def main():
    """Entry point for the sophion-mcp command."""
    mcp_app.run(transport="stdio")


if __name__ == "__main__":
    main()
