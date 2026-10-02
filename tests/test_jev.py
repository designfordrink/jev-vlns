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



def test_jev_selector_stats_track_acceptance_and_fallback():
    from jev_vlns.jev.fake import FakeJevClient
    from jev_vlns.selectors.jev import JevSelector

    client = FakeJevClient(strategy="last", confidence=0.9)
    selector = JevSelector(
        client,
        lambda state, candidates: candidates[0],
        task="destroy",
        question="Choose",
    )
    candidates = [type("C", (), {"id": "a", "description": "A"})(), type("C", (), {"id": "b", "description": "B"})()]
    assert selector.select({}, candidates).id == "b"
    assert selector.stats.decisions == 1
    assert selector.stats.accepted == 1
    assert selector.stats.fallbacks == 0


def test_jev_client_parses_current_typesafe_response(monkeypatch):
    import json
    from jev_vlns.jev.client import JevClient
    from jev_vlns.jev.config import JevConfig
    from jev_vlns.jev.types import DecisionQuestion

    captured = {}

    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({
                "model": "jev-1.13.0",
                "answers": {
                    "choice": {
                        "type": "choice",
                        "choice": "d2",
                        "confidence": 0.87,
                        "probabilities": {"d1": 0.13, "d2": 0.87},
                    }
                },
                "usage": {"input_tokens": 123, "output_tokens": 12},
            }).encode()

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = JevClient(JevConfig(api_key="test"))
    result = client.decide(
        {"stacks": [["C1"]]},
        DecisionQuestion(
            task="destroy",
            question="Choose",
            candidates={"d1": "first", "d2": "second"},
        ),
    )
    assert result.choice == "d2"
    assert result.confidence == 0.87
    assert client.stats.calls == 1
    assert client.stats.successes == 1
    assert client.stats.total_input_tokens == 123
    assert result.cost_usd == 0.000123
    assert client.stats.total_cost_usd == 0.000123
    assert captured["body"]["questions"]["choice"]["type"] == "choice"
    assert captured["body"]["questions"]["choice"]["criteria"] == {
        "d1": "first",
        "d2": "second",
    }


def test_real_jev_benchmark_requires_key(monkeypatch):
    from jev_vlns.evaluation.benchmark import run_real_jev_destroy_benchmark
    from jev_vlns.jev.config import JevConfig

    try:
        run_real_jev_destroy_benchmark(
            seed=1,
            iterations=1,
            config=JevConfig(api_key=None),
        )
    except RuntimeError as exc:
        assert "requires JEV_API_KEY" in str(exc)
    else:
        raise AssertionError("expected real JEV benchmark to require a key")
