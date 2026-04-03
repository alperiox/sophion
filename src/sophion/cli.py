"""Sophion CLI — knowledge base management commands."""

from pathlib import Path

import click
from rich.console import Console

from sophion.backend import get_backend
from sophion.compile import compile_all
from sophion.config import Config
from sophion.ingest import ingest_file, ingest_url
from sophion.store import Store

console = Console()


@click.group()
@click.option(
    "--base-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Base directory for sophion data (default: ~/.sophion)",
)
@click.pass_context
def cli(ctx, base_dir: Path | None):
    """Sophion — personal knowledge engine."""
    ctx.ensure_object(dict)
    config = Config.load(base_dir=base_dir)
    store = Store(config)
    ctx.obj["config"] = config
    ctx.obj["store"] = store


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the sophion knowledge base directory."""
    store: Store = ctx.obj["store"]
    store.initialize()
    console.print(f"Initialized sophion at [bold]{store.base}[/bold]")


@cli.command()
@click.argument("source")
@click.pass_context
def ingest(ctx, source: str):
    """Ingest a URL or local file into the knowledge base."""
    store: Store = ctx.obj["store"]
    store.initialize()

    if source.startswith("http://") or source.startswith("https://"):
        path = ingest_url(source, store)
    else:
        path = ingest_file(source, store)

    console.print(f"Ingested: [bold]{path.name}[/bold]")


@cli.command(name="compile")
@click.pass_context
def compile_cmd(ctx):
    """Compile raw documents into wiki articles."""
    store: Store = ctx.obj["store"]
    config: Config = ctx.obj["config"]
    backend = get_backend(config)

    results = compile_all(store, backend)

    if results:
        console.print(f"Compiled {len(results)} document(s).")
        for path in results:
            console.print(f"  → [bold]{path.name}[/bold]")
    else:
        console.print("Nothing to compile — all documents are up to date.")


@cli.command()
@click.argument("question")
@click.pass_context
def query(ctx, question: str):
    """Ask a question against the knowledge base."""
    store: Store = ctx.obj["store"]
    config: Config = ctx.obj["config"]

    index_path = store.wiki / "_index.md"
    if not index_path.exists():
        console.print("Knowledge base is empty. Run [bold]sophion compile[/bold] first.")
        return

    backend = get_backend(config)
    index_content = index_path.read_text()

    wiki_files = sorted(
        p.name for p in store.wiki.glob("*.md") if p.name != "_index.md"
    )

    if backend.has_file_access:
        prompt = (
            f"You are answering questions against a personal knowledge base.\n\n"
            f"Knowledge base location: {store.wiki}\n"
            f"Available articles: {', '.join(wiki_files)}\n\n"
            f"Index:\n{index_content}\n\n"
            f"Question: {question}\n\n"
            f"Read the relevant articles from {store.wiki}/ and provide "
            f"a thorough answer. Reference specific articles when citing information."
        )
    else:
        file_contents = ""
        for wiki_file in store.wiki.glob("*.md"):
            if wiki_file.name == "_index.md":
                continue
            file_contents += f"\n--- {wiki_file.name} ---\n{wiki_file.read_text()}\n"

        prompt = (
            f"You are answering questions against a personal knowledge base.\n\n"
            f"Index:\n{index_content}\n\n"
            f"Articles:\n{file_contents}\n\n"
            f"Question: {question}\n\n"
            f"Provide a thorough answer. Reference specific articles when citing information."
        )

    system_prompt = (
        "You are a knowledgeable research assistant. Answer questions "
        "based on the provided knowledge base. Be thorough and cite sources."
    )

    answer = backend.query(prompt, system_prompt=system_prompt)
    console.print(answer)
