"""Behavior tests for the zero-dep interactive provider/model picker."""

from deepcloak.picker import ask_choice, candidates, pick_provider_and_model


def test_candidates_lists_only_credentialed_providers_in_order():
    env = {"OPENROUTER_API_KEY": "o", "ANTHROPIC_API_KEY": "b"}
    names = [s.name for s in candidates(env)]
    assert names == ["anthropic", "openrouter"]


def test_ask_choice_renders_numbered_menu_and_returns_value():
    inputs = iter(["2"])
    out = []

    val = ask_choice(
        "Pick one:",
        [("a", "Alpha"), ("b", "Beta")],
        input_fn=lambda prompt="": next(inputs),
        echo=out.append,
    )

    assert val == "b"
    text = "\n".join(out)
    assert "Pick one:" in text and "1. Alpha" in text and "2. Beta" in text


def test_ask_choice_eof_or_garbage_returns_none():
    def eof(prompt=""):
        raise EOFError

    echo = lambda s: None  # noqa: E731
    assert ask_choice("Pick:", [("a", "A")], input_fn=eof, echo=echo) is None
    assert ask_choice("Pick:", [("a", "A")], input_fn=lambda p="": "zz", echo=echo) is None


def test_pick_skipped_when_fewer_than_two_credentials():
    got = pick_provider_and_model(
        {"OPENAI_API_KEY": "x"}, input_fn=lambda p="": "1", echo=lambda s: None
    )
    assert got is None


def test_pick_provider_then_live_model_list():
    env = {"ANTHROPIC_API_KEY": "b", "OPENAI_API_KEY": "a"}
    answers = iter(["1", "2"])  # openai first, then its second listed model
    out = []

    def fake_fetch(url, headers):
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4.1"}]}

    got = pick_provider_and_model(
        env,
        input_fn=lambda prompt="": next(answers),
        echo=out.append,
        fetch=fake_fetch,
    )

    assert got == ("openai", "gpt-4.1")
    text = "\n".join(out)
    assert "openai — default gpt-4.1" in text
    assert "gpt-4o" in text and "gpt-4.1" in text


def test_pick_falls_back_to_default_when_listing_fails():
    env = {"ANTHROPIC_API_KEY": "b", "OPENAI_API_KEY": "a"}
    answers = iter(["2", ""])  # anthropic; accept default model on empty input

    def boom(url, headers):
        raise OSError("no network")

    got = pick_provider_and_model(
        env, input_fn=lambda prompt="": next(answers), echo=lambda s: None, fetch=boom
    )

    assert got == ("anthropic", "claude-sonnet-4-6")


def test_pick_manual_model_entry_when_server_has_no_directory():
    env = {"ANTHROPIC_API_KEY": "b", "GEMINI_API_KEY": "g"}
    answers = iter(["1", "my-custom-model"])

    def empty(url, headers):
        return {"data": []}

    got = pick_provider_and_model(
        env, input_fn=lambda prompt="": next(answers), echo=lambda s: None, fetch=empty
    )

    assert got == ("anthropic", "my-custom-model")
