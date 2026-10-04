from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.run_real_jev_choice_quality import render_report


def test_m12_report_marks_fallbacks_and_live_jev():
    result = {
        "summary": {
            "real-jev-random": {
                "runs": 1,
                "top1_rate": 0.5,
                "mean_rank": 2.0,
                "mean_regret": 1.0,
                "mean_normalized_regret": 0.5,
            }
        },
        "per_run": [{
            "mode": "real-jev-random",
            "decisions": 2.0,
            "jev_stats": {"calls": 2, "fallbacks": 1, "cost_usd": 0.01},
        }],
    }
    report = render_report(result)
    assert "Live JEV Destroy selector" in report
    assert "| Mode | Runs | Decisions | Top-1 rate | Mean rank | Mean regret | Normalized regret | JEV calls | Fallbacks | Cost USD |" in report
    assert "| real-jev-random | 1 | 2 | 0.500 | 2.00 | 1.000 | 0.500 | 2 | 1 | 0.010000 |" in report
