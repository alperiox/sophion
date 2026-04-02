"""Document ingestion — URLs and local files."""

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import frontmatter
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from sophion.store import Store
from sophion.utils import slugify


def ingest_url(url: str, store: Store) -> Path:
    """Fetch a URL, convert to markdown, and save to raw/."""
    headers = {"User-Agent": "Sophion/0.1.0 (knowledge-base ingester)"}
    response = httpx.get(url, follow_redirects=True, timeout=30.0, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    else:
        parsed = urlparse(url)
        title = f"{parsed.netloc}{parsed.path}".rstrip("/")

    markdown_content = markdownify(response.text, strip=["script", "style"])
    markdown_content = _clean_markdown(markdown_content)

    today = date.today().isoformat()
    slug = slugify(title)
    filename = f"{today}-{slug}.md"

    post = frontmatter.Post(
        markdown_content,
        title=title,
        source=url,
        ingested=today,
        compiled=False,
    )

    path = store.raw / filename
    path.write_text(frontmatter.dumps(post))
    return path


def ingest_file(file_path: str, store: Store) -> Path:
    """Copy a local markdown file to raw/ with ingestion metadata."""
    source = Path(file_path)
    content = source.read_text()

    try:
        post = frontmatter.loads(content)
    except Exception:
        post = frontmatter.Post(content)

    if "title" not in post.metadata:
        title = _extract_title(post.content) or source.stem
        post["title"] = title

    post["source"] = str(source)
    post["ingested"] = date.today().isoformat()
    post["compiled"] = False

    today = date.today().isoformat()
    slug = slugify(post["title"])
    filename = f"{today}-{slug}.md"

    path = store.raw / filename
    path.write_text(frontmatter.dumps(post))
    return path


def _extract_title(content: str) -> str | None:
    """Extract the first H1 heading from markdown content."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else None


def _clean_markdown(text: str) -> str:
    """Clean up markdown conversion artifacts."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
