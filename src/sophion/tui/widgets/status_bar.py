"""Status bar widget — displays mode, conversation name, and article count."""

from textual.reactive import reactive
from textual.widget import Widget


class StatusBar(Widget):
    """Bottom status bar showing current mode and context."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    mode: reactive[str] = reactive("work")
    conversation_name: reactive[str] = reactive("New Conversation")
    article_count: reactive[int] = reactive(0)
    is_thinking: reactive[bool] = reactive(False)

    def render(self) -> str:
        mode_display = f"[{self.mode.upper()}]"
        thinking = " | thinking..." if self.is_thinking else ""
        return (
            f" {mode_display} | {self.conversation_name} "
            f"| {self.article_count} articles{thinking}"
        )
