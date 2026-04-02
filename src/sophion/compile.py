"""Knowledge compilation — transform raw documents into wiki articles."""

from datetime import datetime
from pathlib import Path

import frontmatter

from sophion.backend.base import LLMBackend
from sophion.store import Store
from sophion.utils import slugify

COMPILE_SYSTEM_PROMPT = """\
You are a knowledge compiler for a personal wiki. Your job is to transform \
raw source material into well-structured, interconnected wiki articles.

Given a raw document, produce a clean wiki article in markdown that:

1. Starts with a clear, descriptive title (# heading)
2. Has a brief summary paragraph (2-3 sentences)
3. Organizes key concepts under ## headings
4. Uses [[wikilink]] syntax to reference related concepts
5. Preserves important technical details, formulas, and code snippets
6. Is written in clear, educational prose

Output ONLY the markdown article content. Do not include YAML frontmatter.\
"""

INDEX_SYSTEM_PROMPT = """\
You maintain the index for a personal knowledge base wiki. \
Given a list of articles with their titles, generate a well-organized index that:

1. Groups articles under meaningful topic headings (## level)
2. Provides a one-line description for each article
3. Uses [[wikilink]] syntax for cross-references
4. Highlights connections between articles

Output ONLY the markdown content. Do not include YAML frontmatter. \
Start with a # Knowledge Base Index heading.\
"""


def compile_document(raw_path: Path, store: Store, backend: LLMBackend) -> Path:
    """Compile a single raw document into a wiki article."""
    raw_post = frontmatter.load(str(raw_path))
    title = raw_post.get("title", raw_path.stem)
    source = raw_post.get("source", "unknown")

    prompt = (
        f"Compile this raw document into a wiki article:\n\n"
        f"Title: {title}\n"
        f"Source: {source}\n\n"
        f"Content:\n{raw_post.content}"
    )

    result = backend.query(prompt, system_prompt=COMPILE_SYSTEM_PROMPT)

    slug = slugify(title)
    wiki_path = store.wiki / f"{slug}.md"

    wiki_post = frontmatter.Post(
        result,
        title=title,
        source_raw=raw_path.name,
        compiled_at=datetime.now().isoformat(),
    )
    wiki_path.write_text(frontmatter.dumps(wiki_post))

    raw_post["compiled"] = True
    raw_path.write_text(frontmatter.dumps(raw_post))

    return wiki_path


def compile_all(store: Store, backend: LLMBackend) -> list[Path]:
    """Compile all uncompiled raw documents."""
    uncompiled = store.uncompiled_files()
    results = []
    for raw_path in uncompiled:
        wiki_path = compile_document(raw_path, store, backend)
        results.append(wiki_path)

    if results:
        update_index(store, backend)

    return results


def update_index(store: Store, backend: LLMBackend):
    """Regenerate the wiki index from all wiki articles."""
    articles = sorted(
        p for p in store.wiki.glob("*.md") if p.name != "_index.md"
    )

    if not articles:
        return

    article_list = ""
    for article_path in articles:
        post = frontmatter.load(str(article_path))
        title = post.get("title", article_path.stem)
        article_list += f"- {article_path.stem}: {title}\n"

    prompt = (
        f"Generate an index for these wiki articles:\n\n{article_list}"
    )

    result = backend.query(prompt, system_prompt=INDEX_SYSTEM_PROMPT)

    index_path = store.wiki / "_index.md"
    index_post = frontmatter.Post(
        result,
        last_updated=datetime.now().isoformat(),
    )
    index_path.write_text(frontmatter.dumps(index_post))
