from dataclasses import dataclass

from jev_vlns.jev.fake import FakeJevClient
from jev_vlns.selectors.jev import JevSelector


@dataclass(frozen=True)
class Candidate:
    id: str
    description: str


def fallback(_state, candidates):
    return candidates[0]


def test_jev_selector_chooses_candidate():
    selector = JevSelector(
        FakeJevClient(strategy="last", confidence=0.9),
        fallback,
        task="repair",
        question="Choose a repair",
        min_confidence=0.5,
    )
    candidates = [Candidate("r1", "first"), Candidate("r2", "second")]
    assert selector.select({"iteration": 1}, candidates).id == "r2"


def test_jev_selector_falls_back_on_unknown_choice():
    selector = JevSelector(
        FakeJevClient(strategy="scripted", scripted_choices=["unknown"]),
        fallback,
        task="repair",
        question="Choose a repair",
    )
    candidates = [Candidate("r1", "first"), Candidate("r2", "second")]
    assert selector.select({}, candidates).id == "r1"


def test_jev_selector_falls_back_on_low_confidence():
    selector = JevSelector(
        FakeJevClient(strategy="last", confidence=0.2),
        fallback,
        task="repair",
        question="Choose a repair",
        min_confidence=0.8,
    )
    candidates = [Candidate("r1", "first"), Candidate("r2", "second")]
    assert selector.select({}, candidates).id == "r1"


def test_jev_selector_rejects_duplicate_ids():
    selector = JevSelector(FakeJevClient(), fallback, task="repair", question="Choose")
    candidates = [Candidate("r1", "first"), Candidate("r1", "duplicate")]
    try:
        selector.select({}, candidates)
    except ValueError as exc:
        assert "duplicate candidate id" in str(exc)
    else:
        raise AssertionError("expected duplicate candidate IDs to fail")
