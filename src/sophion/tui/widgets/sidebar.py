"""Sidebar widget — conversation list and knowledge base file browser."""

from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


class Sidebar(Widget):
    """Left sidebar with conversation list and knowledge browser."""

    DEFAULT_CSS = """
    Sidebar {
        width: 30;
        height: 100%;
        dock: left;
        border-right: solid $border;
        overflow-y: auto;
    }
    .section-header {
        text-style: bold;
        padding: 1 1 0 1;
        color: $text-muted;
    }
    #conversation-list {
        height: auto;
        max-height: 50%;
        margin: 0 1;
    }
    #knowledge-list {
        height: auto;
        margin: 0 1;
    }
    """

    class ConversationSelected(Message):
        """Posted when a conversation is selected."""

        def __init__(self, conversation_id: str) -> None:
            super().__init__()
            self.conversation_id = conversation_id

    class KnowledgeItemSelected(Message):
        """Posted when a knowledge base file is selected."""

        def __init__(self, file_ref: str) -> None:
            super().__init__()
            self.file_ref = file_ref  # "wiki:filename.md" or "raw:filename.md"

    def compose(self) -> ComposeResult:
        yield Static("Conversations", classes="section-header")
        yield OptionList(id="conversation-list")
        yield Static("Knowledge Base", classes="section-header")
        yield OptionList(id="knowledge-list")

    def update_conversations(self, conversations: list[dict]):
        """Update the conversation list. Each dict has 'id' and 'name'."""
        option_list = self.query_one("#conversation-list", OptionList)
        option_list.clear_options()
        for convo in conversations:
            option_list.add_option(Option(convo["name"], id=convo["id"]))

    def update_knowledge_files(self, wiki_dir: Path, raw_dir: Path):
        """Update the knowledge base file list."""
        option_list = self.query_one("#knowledge-list", OptionList)
        option_list.clear_options()

        wiki_files = sorted(wiki_dir.glob("*.md"))
        if wiki_files:
            option_list.add_option(Option("── wiki ──", disabled=True))
            for f in wiki_files:
                if f.name != "_index.md":
                    option_list.add_option(Option(f"  {f.stem}", id=f"wiki:{f.name}"))

        raw_files = sorted(raw_dir.glob("*.md"))
        if raw_files:
            option_list.add_option(Option("── raw ──", disabled=True))
            for f in raw_files:
                option_list.add_option(Option(f"  {f.stem}", id=f"raw:{f.name}"))

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle selection of conversations or knowledge base items."""
        option_id = event.option.id
        if not option_id:
            return
        if option_id.startswith(("wiki:", "raw:")):
            self.post_message(self.KnowledgeItemSelected(option_id))
        else:
            self.post_message(self.ConversationSelected(option_id))

    def highlight_conversation(self, conversation_id: str):
        """Highlight the active conversation in the list."""
        option_list = self.query_one("#conversation-list", OptionList)
        for idx, option in enumerate(option_list._options):
            if option.id == conversation_id:
                option_list.highlighted = idx
                break
