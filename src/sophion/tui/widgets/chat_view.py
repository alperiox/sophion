"""Chat view widget — displays conversation messages with markdown rendering."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import Markdown, Static


class MessageBubble(Widget):
    """A single message in the conversation."""

    DEFAULT_CSS = """
    MessageBubble {
        width: 100%;
        padding: 1 2;
        margin: 0 0 1 0;
    }
    MessageBubble.user {
        background: $primary-background;
    }
    MessageBubble.assistant {
        background: $surface;
    }
    .message-role {
        text-style: bold;
        margin: 0 0 1 0;
    }
    """

    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.msg_content = content
        self.add_class(role)

    def compose(self) -> ComposeResult:
        label = "You" if self.role == "user" else "Sophion"
        yield Static(f"[bold]{label}[/bold]", classes="message-role", markup=True)
        yield Markdown(self.msg_content)


class ThinkingIndicator(Static):
    """Shown while waiting for LLM response."""

    DEFAULT_CSS = """
    ThinkingIndicator {
        color: $text-muted;
        padding: 1 2;
        text-style: italic;
    }
    """

    def __init__(self):
        super().__init__("Thinking...")


class ChatView(Widget):
    """Scrollable conversation view with message bubbles."""

    DEFAULT_CSS = """
    ChatView {
        width: 1fr;
        height: 1fr;
    }
    #messages {
        width: 100%;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(id="messages")

    def add_message(self, role: str, content: str) -> MessageBubble:
        """Add a message bubble and scroll to it."""
        container = self.query_one("#messages")
        bubble = MessageBubble(role, content)
        container.mount(bubble)
        bubble.scroll_visible()
        return bubble

    def show_thinking(self):
        """Show the thinking indicator."""
        container = self.query_one("#messages")
        container.mount(ThinkingIndicator())

    def hide_thinking(self):
        """Remove the thinking indicator."""
        for indicator in self.query(ThinkingIndicator):
            indicator.remove()

    def update_last_assistant(self, content: str):
        """Update the last assistant message content."""
        bubbles = list(self.query(MessageBubble))
        for bubble in reversed(bubbles):
            if bubble.role == "assistant":
                md = bubble.query_one(Markdown)
                md.update(content)
                bubble.scroll_visible()
                break

    def clear_messages(self):
        """Remove all messages from the view."""
        container = self.query_one("#messages")
        container.remove_children()

    def load_messages(self, messages: list[tuple[str, str]]):
        """Load a list of (role, content) messages."""
        self.clear_messages()
        for role, content in messages:
            self.add_message(role, content)
