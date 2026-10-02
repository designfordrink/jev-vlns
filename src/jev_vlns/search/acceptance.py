from jev_vlns.core.evaluator import Evaluation


def strict_improvement(
    current: Evaluation, candidate: Evaluation
) -> bool:
    """MVP VLNS acceptance: accept only a strictly better feasible solution."""

    return (
        candidate.feasible
        and (not current.feasible or candidate.objective < current.objective)
    )
