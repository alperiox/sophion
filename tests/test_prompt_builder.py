from sophion.tui.models import Conversation
from sophion.tui.prompt_builder import build_prompt, SYSTEM_PROMPT

import frontmatter


def test_build_prompt_includes_question(store):
    convo = Conversation()
    convo.add_message("user", "What is attention?")

    prompt = build_prompt(convo, store)
    assert "What is attention?" in prompt


def test_build_prompt_includes_history(store):
    convo = Conversation()
    convo.add_message("user", "What is diffusion?")
    convo.add_message("assistant", "Diffusion is a process...")
    convo.add_message("user", "Tell me more")

    prompt = build_prompt(convo, store)
    assert "What is diffusion?" in prompt
    assert "Diffusion is a process..." in prompt
    assert "Tell me more" in prompt


def test_build_prompt_includes_wiki_index(store):
    index_post = frontmatter.Post("# Index\n\n- [[article-one]]")
    (store.wiki / "_index.md").write_text(frontmatter.dumps(index_post))

    convo = Conversation()
    convo.add_message("user", "What do we have?")

    prompt = build_prompt(convo, store)
    assert "article-one" in prompt


def test_build_prompt_includes_wiki_location(store):
    convo = Conversation()
    convo.add_message("user", "Hi")

    prompt = build_prompt(convo, store)
    assert str(store.wiki) in prompt


def test_build_prompt_handles_empty_wiki(store):
    convo = Conversation()
    convo.add_message("user", "Hi")

    prompt = build_prompt(convo, store)
    assert "Hi" in prompt


def test_system_prompt_exists():
    assert len(SYSTEM_PROMPT) > 0
    assert "knowledge base" in SYSTEM_PROMPT.lower()
