"""Build prompts from conversation history and knowledge base context."""

from sophion.store import Store
from sophion.tui.models import Conversation

SYSTEM_PROMPT = """\
You are Sophion, a personal knowledge base assistant. You help the user \
explore, understand, and build upon their knowledge base of research notes \
and articles.

You have access to a knowledge base of markdown articles. When answering \
questions, read relevant articles to provide thorough, well-sourced answers. \
Reference specific articles when citing information.

Be conversational and helpful. If the user asks about something not in the \
knowledge base, say so and offer to help them add it.\
"""


def build_prompt(conversation: Conversation, store: Store) -> str:
    """Build an LLM prompt from conversation history and wiki context."""
    parts = []

    # Knowledge base context
    index_path = store.wiki / "_index.md"
    if index_path.exists():
        index_content = index_path.read_text()
        parts.append(f"Knowledge base location: {store.wiki}")

        wiki_files = sorted(
            p.name for p in store.wiki.glob("*.md") if p.name != "_index.md"
        )
        if wiki_files:
            parts.append(f"Available articles: {', '.join(wiki_files)}")

        parts.append(f"Index:\n{index_content}")
    else:
        parts.append(f"Knowledge base location: {store.wiki}")
        parts.append("The knowledge base is currently empty.")

    # Conversation history
    if len(conversation.messages) > 1:
        parts.append("\nConversation history:")
        for msg in conversation.messages[:-1]:
            label = "User" if msg.role == "user" else "Assistant"
            parts.append(f"{label}: {msg.content}")

    # Current message
    latest = conversation.messages[-1]
    parts.append(f"\nUser: {latest.content}")

    parts.append(
        f"\nRead relevant articles from {store.wiki}/ if needed. "
        "Provide a thorough answer."
    )

    return "\n\n".join(parts)
