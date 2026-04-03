import pytest

from sophion.config import Config
from sophion.store import Store
from sophion.tui.app import SophionApp
from sophion.tui.widgets.chat_view import ChatView
from sophion.tui.widgets.message_input import MessageInput
from sophion.tui.widgets.sidebar import Sidebar
from sophion.tui.widgets.status_bar import StatusBar


@pytest.fixture
def app(tmp_base):
    config = Config(base_dir=tmp_base)
    store = Store(config)
    store.initialize()
    return SophionApp(config=config, store=store)


@pytest.mark.asyncio
async def test_app_mounts(app):
    async with app.run_test() as pilot:
        assert app.query_one(ChatView) is not None
        assert app.query_one(MessageInput) is not None
        assert app.query_one(Sidebar) is not None
        assert app.query_one(StatusBar) is not None


@pytest.mark.asyncio
async def test_app_creates_initial_conversation(app):
    async with app.run_test() as pilot:
        assert app.conversation is not None
        assert app.conversation.name == "New Conversation"


@pytest.mark.asyncio
async def test_app_toggle_sidebar(app):
    async with app.run_test() as pilot:
        assert app.sidebar_visible is True
        await pilot.press("ctrl+b")
        assert app.sidebar_visible is False
        await pilot.press("ctrl+b")
        assert app.sidebar_visible is True


@pytest.mark.asyncio
async def test_app_new_conversation(app):
    async with app.run_test() as pilot:
        first_id = app.conversation.id
        await pilot.press("ctrl+n")
        assert app.conversation.id != first_id
