from dataclasses import dataclass

import pytest

from jev_vlns.core.action import Action
from jev_vlns.core.evaluator import Evaluation
from jev_vlns.core.selector import Selector
from jev_vlns.core.state import State
from jev_vlns.jev.types import DecisionQuestion, DecisionResult


def test_state_is_immutable():
    state = State(data={"value": 1})
    with pytest.raises(AttributeError):
        state.data = {"value": 2}


def test_action_is_typed_and_immutable():
    action = Action(id="a1", kind="move", payload={"from": 0, "to": 1})
    assert action.id == "a1"
    with pytest.raises(AttributeError):
        action.id = "a2"


def test_evaluation_is_typed():
    evaluation = Evaluation(feasible=True, objective=7, metrics={"moves": 7})
    assert evaluation.feasible
    assert evaluation.objective == 7


def test_protocols_are_runtime_independent():
    @dataclass(frozen=True)
    class ExampleState(State):
        pass

    class ExampleSelector:
        def select(self, state, candidates):
            return candidates[0]

    selector: Selector = ExampleSelector()
    assert selector.select(ExampleState(), [Action("a1", "x")]).id == "a1"


def test_decision_question_and_result():
    question = DecisionQuestion(
        task="repair",
        question="Choose the best candidate",
        candidates={"r1": "move C1 to stack 0", "r2": "move C1 to stack 1"},
    )
    result = DecisionResult(choice="r2", confidence=0.81)
    assert question.candidates[result.choice].startswith("move")
