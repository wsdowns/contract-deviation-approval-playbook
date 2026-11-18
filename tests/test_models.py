"""A cut-off or empty model answer is refused, never used as if it were complete."""
import pytest

import models

CFG = {"backend": "openai-compatible", "name": "m", "base_url": "http://x/v1", "api_key_env": "", "max_tokens": 10, "timeout_seconds": 5}


def reply(content, finish="stop"):
    return {"choices": [{"message": {"content": content}, "finish_reason": finish}]}


def test_a_complete_answer_is_returned(monkeypatch):
    monkeypatch.setattr(models, "_post", lambda *a: reply("  Done.  "))
    assert models.ask("p", CFG) == "Done."


@pytest.mark.parametrize("out", [reply(None, "length"), reply("partial text", "length"), reply("", "stop"), reply(None)])
def test_cut_off_or_empty_answers_are_refused(monkeypatch, out):
    monkeypatch.setattr(models, "_post", lambda *a: out)
    with pytest.raises(RuntimeError, match="ran out of room"):
        models.ask("p", CFG)


def test_anthropic_cut_off_is_refused(monkeypatch):
    monkeypatch.setattr(models, "_post", lambda *a: {"content": [{"text": "half"}], "stop_reason": "max_tokens"})
    monkeypatch.setenv("K", "k")
    with pytest.raises(RuntimeError, match="ran out of room"):
        models.ask("p", {**CFG, "backend": "anthropic-api", "api_key_env": "K"})


@pytest.mark.parametrize("effort,sent", [("", None), ("low", {"effort": "low"}), ("off", {"enabled": False})])
def test_reasoning_effort_is_sent_only_when_set(monkeypatch, effort, sent):
    seen = {}
    monkeypatch.setattr(models, "_post", lambda url, headers, body, t: seen.update(body) or reply("ok"))
    models.ask("p", {**CFG, "reasoning_effort": effort})
    assert seen.get("reasoning") == sent
