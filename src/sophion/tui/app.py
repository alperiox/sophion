"""Sophion TUI — main application."""

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static

from sophion.backend import get_backend
from sophion.config import Config
from sophion.store import Store
from sophion.tui.async_backend import AsyncBackendWrapper
from sophion.tui.models import Conversation
from sophion.tui.prompt_builder import SYSTEM_PROMPT, build_prompt
from sophion.tui.widgets.chat_view import ChatView
from sophion.tui.widgets.message_input import MessageInput
from sophion.tui.widgets.sidebar import Sidebar
from sophion.tui.widgets.status_bar import StatusBar


class DocumentViewer(ModalScreen):
    """Modal overlay for viewing knowledge base documents."""

    BINDINGS = [("escape", "dismiss", "Close")]

    DEFAULT_CSS = """
    DocumentViewer {
        align: center middle;
    }
    #doc-container {
        width: 80%;
        height: 80%;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    #doc-title {
        text-style: bold;
        margin: 0 0 1 0;
    }
    #doc-content {
        height: 1fr;
    }
    """

    def __init__(self, title: str, content: str):
        super().__init__()
        self.doc_title = title
        self.doc_content = content

    def compose(self) -> ComposeResult:
        with Vertical(id="doc-container"):
            yield Static(
                f"[bold]{self.doc_title}[/bold]  (Esc to close)",
                id="doc-title",
                markup=True,
            )
            yield ScrollableContainer(Markdown(self.doc_content), id="doc-content")


class SophionApp(App):
    """Sophion interactive TUI."""

    CSS_PATH = "styles.tcss"

    TITLE = "Sophion"

    BINDINGS = [
        Binding("ctrl+n", "new_conversation", "New Chat", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    sidebar_visible: reactive[bool] = reactive(True)

    def __init__(self, config: Config, store: Store):
        super().__init__()
        self.config = config
        self.store = store
        self.backend = AsyncBackendWrapper(get_backend(config))
        self.conversation: Conversation | None = None
        self.conversations: list[Conversation] = []

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Sidebar(id="sidebar"),
            Vertical(
                ChatView(id="chat-view"),
                MessageInput(id="message-input"),
                id="main-panel",
            ),
            id="app-grid",
        )
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """Initialize the app state on startup."""
        self.store.initialize()
        self._refresh_conversations()
        self._refresh_knowledge()

        if self.conversations:
            self._switch_conversation(self.conversations[0].id)
        else:
            self._create_new_conversation()

        self.query_one(MessageInput).focus()

    def _refresh_conversations(self):
        """Reload conversation list from disk."""
        self.conversations = Conversation.list_all(self.store.conversations)
        sidebar = self.query_one(Sidebar)
        sidebar.update_conversations(
            [{"id": c.id, "name": c.name} for c in self.conversations]
        )

    def _refresh_knowledge(self):
        """Reload knowledge base file list."""
        sidebar = self.query_one(Sidebar)
        sidebar.update_knowledge_files(self.store.wiki, self.store.raw)

        wiki_count = len(
            [p for p in self.store.wiki.glob("*.md") if p.name != "_index.md"]
        )
        self.query_one(StatusBar).article_count = wiki_count

    def _switch_conversation(self, conversation_id: str):
        """Load and display a conversation (always reloads from disk)."""
        path = self.store.conversations / f"{conversation_id}.json"
        if not path.exists():
            return

        self.conversation = Conversation.load(path)

        # Update in-memory list with fresh data
        for i, convo in enumerate(self.conversations):
            if convo.id == conversation_id:
                self.conversations[i] = self.conversation
                break

        chat_view = self.query_one(ChatView)
        chat_view.load_messages(
            [(m.role, m.content) for m in self.conversation.messages]
        )

        sidebar = self.query_one(Sidebar)
        sidebar.highlight_conversation(conversation_id)

        status = self.query_one(StatusBar)
        status.conversation_name = self.conversation.name

    def _create_new_conversation(self):
        """Create a new conversation and switch to it."""
        convo = Conversation()
        convo.save(self.store.conversations)
        self.conversations.insert(0, convo)
        self._refresh_conversations()
        self._switch_conversation(convo.id)

    def on_sidebar_conversation_selected(
        self, event: Sidebar.ConversationSelected
    ) -> None:
        """Handle conversation selection from sidebar."""
        self._switch_conversation(event.conversation_id)

    def on_message_input_submitted(self, event: MessageInput.Submitted) -> None:
        """Handle message submission from input."""
        if not self.conversation:
            self._create_new_conversation()

        self.conversation.add_message("user", event.text)

        if self.conversation.name == "New Conversation":
            self.conversation.name = self.conversation.generate_name()
            self._refresh_conversations()
            self.query_one(StatusBar).conversation_name = self.conversation.name

        chat_view = self.query_one(ChatView)
        chat_view.add_message("user", event.text)

        self.conversation.save(self.store.conversations)

        self._send_to_backend(event.text)

    @work(exclusive=True)
    async def _send_to_backend(self, user_text: str) -> None:
        """Send the conversation to the LLM backend, streaming the response."""
        chat_view = self.query_one(ChatView)
        status = self.query_one(StatusBar)

        chat_view.show_thinking()
        status.is_thinking = True

        try:
            prompt = build_prompt(self.conversation, self.store)

            # Replace thinking indicator with empty assistant bubble for streaming
            chat_view.hide_thinking()
            chat_view.add_message("assistant", "")

            full_response = ""
            async for text in self.backend.stream_query(
                prompt, system_prompt=SYSTEM_PROMPT
            ):
                full_response = text
                chat_view.update_last_assistant(full_response)

            # Fallback if streaming yielded nothing
            if not full_response:
                full_response = await self.backend.query(
                    prompt, system_prompt=SYSTEM_PROMPT
                )
                chat_view.update_last_assistant(full_response)

            self.conversation.add_message("assistant", full_response)
            self.conversation.save(self.store.conversations)
        except Exception as e:
            chat_view.hide_thinking()
            chat_view.add_message("assistant", f"Error: {e}")
        finally:
            status.is_thinking = False

    def action_new_conversation(self) -> None:
        """Create a new conversation."""
        self._create_new_conversation()
        self.query_one(MessageInput).focus()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one(Sidebar)
        self.sidebar_visible = not self.sidebar_visible
        sidebar.set_class(not self.sidebar_visible, "hidden")

    def on_sidebar_knowledge_item_selected(
        self, event: Sidebar.KnowledgeItemSelected
    ) -> None:
        """Handle knowledge base file selection — open document viewer."""
        prefix, filename = event.file_ref.split(":", 1)
        if prefix == "wiki":
            path = self.store.wiki / filename
        else:
            path = self.store.raw / filename

        if path.exists():
            content = path.read_text()
            self.push_screen(DocumentViewer(filename, content))

    def watch_sidebar_visible(self, visible: bool) -> None:
        """React to sidebar visibility change."""
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.set_class(not visible, "hidden")
        except Exception:
            pass
