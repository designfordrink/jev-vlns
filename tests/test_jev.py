import os

from jev_vlns.jev.config import JevConfig
from jev_vlns.jev.fake import FakeJevClient
from jev_vlns.jev.types import DecisionQuestion


def test_fake_jev_is_deterministic():
    client = FakeJevClient(strategy="last", confidence=0.9)
    question = DecisionQuestion(
        task="repair",
        question="Choose",
        candidates={"r1": "A", "r2": "B"},
    )

    first = client.decide({}, question)
    second = client.decide({}, question)

    assert first.choice == "r2"
    assert second.choice == "r2"
    assert client.calls == 2


def test_fake_jev_scripted():
    client = FakeJevClient(strategy="scripted", scripted_choices=["r2", "r1"])
    question = DecisionQuestion(
        task="repair",
        question="Choose",
        candidates={"r1": "A", "r2": "B"},
    )

    assert client.decide({}, question).choice == "r2"
    assert client.decide({}, question).choice == "r1"


def test_config_does_not_require_secrets(monkeypatch):
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    config = JevConfig.from_environment()
    assert config.api_key is None
    assert config.model == "jev-latest"
