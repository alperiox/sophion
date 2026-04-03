"""Message input widget — multi-line text input with Ctrl+D to send."""

from textual.binding import Binding
from textual.message import Message
from textual.widgets import TextArea


class MessageInput(TextArea):
    """Multi-line input for composing messages. Ctrl+D to send."""

    BINDINGS = [
        Binding("ctrl+d", "submit", "Send", show=True),
    ]

    DEFAULT_CSS = """
    MessageInput {
        height: auto;
        min-height: 3;
        max-height: 10;
        border: solid $accent;
        margin: 0 0 0 0;
    }
    MessageInput:focus {
        border: solid $accent;
    }
    """

    class Submitted(Message):
        """Posted when the user submits their message."""

        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def action_submit(self) -> None:
        """Send the current text content."""
        text = self.text.strip()
        if text:
            self.post_message(self.Submitted(text))
            self.clear()

    def on_mount(self) -> None:
        """Set placeholder text."""
        self.show_line_numbers = False
