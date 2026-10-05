import json

from jev_vlns.container_stack.state import Container, ContainerStackState
from jev_vlns.evaluation.benchmark import (
    JEV_DESTROY_OBJECTIVE,
    JEV_DESTROY_QUESTION,
    _jev_destroy_candidate_context,
)
from jev_vlns.search.destroy import DestroyCandidate
from jev_vlns.jev.fake import FakeJevClient
from jev_vlns.selectors.jev import JevSelector


def test_destroy_candidate_context_is_state_aware():
    state = ContainerStackState(
        stacks=(("C1", "C2"), ("C3",)),
        containers=(
            Container("C1", "A", 1),
            Container("C2", "B", 2),
            Container("C3", "A", 3),
        ),
        stack_destinations=("B", "A"),
    )
    candidate = DestroyCandidate(
        id="stack:0",
        stack_indices=(0,),
        description="destroy top of stack 0",
    )

    context = json.loads(_jev_destroy_candidate_context(state, candidate))
    assert context == {
        "operation": "destroy_top",
        "affected_stacks": [
            {
                "index": 0,
                "destination": "B",
                "height_before": 2,
                "top": {"id": "C2", "destination": "B", "priority": 2},
                "exposed_after_destroy": {
                    "id": "C1", "destination": "A", "priority": 1
                },
            }
        ],
    }


def test_jev_selector_can_serialize_candidate_from_current_state():
    captured = {}

    class Client(FakeJevClient):
        def decide(self, state, question):
            captured["state"] = state
            captured["criteria"] = dict(question.candidates)
            captured["question"] = question.question
            captured["objective"] = question.objective
            return super().decide(state, question)

    class Candidate:
        def __init__(self, candidate_id, description):
            self.id = candidate_id
            self.description = description

    selector = JevSelector(
        Client(strategy="last"),
        lambda state, candidates: candidates[0],
        task="destroy",
        question=JEV_DESTROY_QUESTION,
        objective=JEV_DESTROY_OBJECTIVE,
        candidate_serializer=lambda state, candidate: f"{state['iteration']}:{candidate.id}",
    )
    candidates = [Candidate("stack:0", "destroy top of stack 0"), Candidate("stack:1", "destroy top of stack 1")]

    selected = selector.select({"iteration": 7}, candidates)

    assert selected.id == "stack:1"
    assert captured["criteria"] == {"stack:0": "7:stack:0", "stack:1": "7:stack:1"}
    assert "Choose exactly one legal destroy neighborhood" in captured["question"]
    assert "Oracle scores" in captured["question"]
    assert "Minimize final total container moves" in captured["objective"]


def test_real_destroy_prompt_contains_no_hidden_future_information():
    assert "future evaluations" in JEV_DESTROY_QUESTION
    assert "Oracle scores" in JEV_DESTROY_QUESTION
    assert "candidate rankings" in JEV_DESTROY_QUESTION
    assert "regret information" in JEV_DESTROY_QUESTION
