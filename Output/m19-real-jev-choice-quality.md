# M12 — Real JEV Choice Quality

Live JEV Destroy selector with Random Repair, evaluated with the same local Oracle landscape used by M11.

| Mode | Runs | Decisions | Top-1 rate | Mean rank | Mean regret | Normalized regret | JEV calls | Fallbacks | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| real-jev-random | 5 | 250 | 0.004 | 9.84 | 1.720 | 0.972 | 250 | 0 | 0.029216 |

## Method

- Same seeds and iteration budget as M11.
- Random Repair is fixed; only Destroy selection is live JEV.
- Legal candidates are generated locally before JEV is called.
- Oracle downstream scores are computed only after the decision and are never sent to JEV.
- JEV may only select one of the locally generated candidate IDs.
- Fallbacks are reported separately and must not be described as successful JEV decisions.

## Interpretation

Compare this result with the M11 random-random, heuristic-random and oracle-random controls. M12 measures local choice quality; it does not by itself establish better end-to-end VLNS performance.
