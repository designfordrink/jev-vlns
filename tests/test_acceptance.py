from jev_vlns.core.evaluator import Evaluation
from jev_vlns.search.acceptance import strict_improvement


def test_feasible_lower_objective_is_accepted():
    assert strict_improvement(
        Evaluation(True, 10), Evaluation(True, 9)
    )


def test_equal_objective_is_rejected():
    assert not strict_improvement(
        Evaluation(True, 10), Evaluation(True, 10)
    )


def test_infeasible_candidate_is_rejected():
    assert not strict_improvement(
        Evaluation(True, 10), Evaluation(False, 1)
    )


def test_feasible_candidate_beats_infeasible_current():
    assert strict_improvement(
        Evaluation(False, 100), Evaluation(True, 20)
    )
