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


def test_jev_repair_selector_scopes_candidates_by_container():
    from jev_vlns.selectors.jev import JevRepairSelector

    @dataclass(frozen=True)
    class RepairCandidate:
        id: str
        container_id: str
        description: str

    selector = JevRepairSelector(
        JevSelector(
            FakeJevClient(strategy="last"),
            fallback,
            task="repair",
            question="Choose placement",
        )
    )
    candidates = [
        RepairCandidate("a0", "c1", "c1 -> 0"),
        RepairCandidate("a1", "c1", "c1 -> 1"),
        RepairCandidate("b0", "c2", "c2 -> 0"),
    ]
    assert selector.select_for_container({}, candidates, "c1").id == "a1"


def test_jev_destroy_selector_chooses_neighborhood():
    from jev_vlns.selectors.jev import JevDestroySelector

    @dataclass(frozen=True)
    class DestroyCandidate:
        id: str
        description: str

    selector = JevDestroySelector(
        JevSelector(
            FakeJevClient(strategy="last"),
            fallback,
            task="destroy",
            question="Choose neighborhood",
        )
    )
    candidates = [
        DestroyCandidate("stack:0", "destroy stack 0"),
        DestroyCandidate("stacks:1,2", "destroy stacks 1 and 2"),
    ]
    assert selector.select({}, candidates).id == "stacks:1,2"
