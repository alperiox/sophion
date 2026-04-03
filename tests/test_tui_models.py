import json

from sophion.tui.models import Conversation, Message


def test_message_creation():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.timestamp is not None


def test_message_roundtrip():
    msg = Message(role="user", content="Hello")
    data = msg.to_dict()
    loaded = Message.from_dict(data)
    assert loaded.role == msg.role
    assert loaded.content == msg.content
    assert loaded.timestamp == msg.timestamp


def test_conversation_creation():
    convo = Conversation()
    assert convo.id is not None
    assert convo.name == "New Conversation"
    assert convo.messages == []


def test_conversation_add_message():
    convo = Conversation()
    msg = convo.add_message("user", "Hello")
    assert len(convo.messages) == 1
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_conversation_updates_timestamp():
    convo = Conversation()
    original = convo.updated_at
    convo.add_message("user", "Hello")
    assert convo.updated_at >= original


def test_conversation_roundtrip():
    convo = Conversation(name="Test Chat")
    convo.add_message("user", "Hello")
    convo.add_message("assistant", "Hi there!")

    data = convo.to_dict()
    loaded = Conversation.from_dict(data)

    assert loaded.id == convo.id
    assert loaded.name == convo.name
    assert len(loaded.messages) == 2
    assert loaded.messages[0].content == "Hello"
    assert loaded.messages[1].content == "Hi there!"


def test_conversation_save_load(tmp_path):
    convo = Conversation(name="Test Chat")
    convo.add_message("user", "Hello")
    convo.add_message("assistant", "Hi there!")

    convo.save(tmp_path)

    loaded = Conversation.load(tmp_path / f"{convo.id}.json")
    assert loaded.id == convo.id
    assert loaded.name == convo.name
    assert len(loaded.messages) == 2


def test_conversation_list_all(tmp_path):
    c1 = Conversation(name="Chat 1")
    c1.add_message("user", "First")
    c1.save(tmp_path)

    c2 = Conversation(name="Chat 2")
    c2.add_message("user", "Second")
    c2.save(tmp_path)

    convos = Conversation.list_all(tmp_path)
    assert len(convos) == 2


def test_conversation_list_all_empty(tmp_path):
    convos = Conversation.list_all(tmp_path)
    assert convos == []


def test_conversation_list_all_skips_invalid(tmp_path):
    (tmp_path / "bad.json").write_text("not json")

    c1 = Conversation(name="Valid")
    c1.save(tmp_path)

    convos = Conversation.list_all(tmp_path)
    assert len(convos) == 1


def test_conversation_generate_name():
    convo = Conversation()
    convo.add_message("user", "What is diffusion?")
    assert convo.generate_name() == "What is diffusion?"


def test_conversation_generate_name_truncates():
    convo = Conversation()
    convo.add_message("user", "A" * 100)
    name = convo.generate_name()
    assert len(name) <= 53
    assert name.endswith("...")


def test_conversation_generate_name_no_messages():
    convo = Conversation()
    assert convo.generate_name() == "New Conversation"
