from jev_vlns.evaluation.choice_quality import choice_metrics, summarize_choice_metrics

def _trace(selected, scores):
    return [{
        "selected_destroy": selected,
        "selected_destroy_score": scores[selected],
        "destroy_scores": scores,
    }]

def test_choice_quality_top1_and_regret():
    metrics = choice_metrics(_trace("a", {"a": 2.0, "b": 2.0, "c": 4.0}))
    assert metrics["top1_rate"] == 1.0
    assert metrics["mean_rank"] == 1.0
    assert metrics["mean_regret"] == 0.0

    metrics = choice_metrics(_trace("c", {"a": 2.0, "b": 3.0, "c": 4.0}))
    assert metrics["top1_rate"] == 0.0
    assert metrics["mean_rank"] == 3.0
    assert metrics["mean_regret"] == 2.0
    assert metrics["mean_normalized_regret"] == 1.0

def test_choice_quality_summary_groups_modes():
    docs = [
        {"mode": "random-random", "seed": 1, "trace": _trace("a", {"a": 1, "b": 2})},
        {"mode": "random-random", "seed": 2, "trace": _trace("b", {"a": 1, "b": 2})},
    ]
    result = summarize_choice_metrics(docs)
    assert result["summary"]["random-random"]["runs"] == 2
    assert result["summary"]["random-random"]["top1_rate"] == 0.5
