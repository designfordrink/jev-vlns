"""Compare offline VLNS neighborhood sizes under a matched protocol.

This experiment isolates the effect of the Destroy neighborhood family.
It does not use real JEV and it reports the existing projected-search
objective, not a physical reconfiguration cost.
"""
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.vlns import random_vlns

def run(seeds, iterations, max_k, adjacent_only):
    rows=[]
    for seed in seeds:
        initial=make_seeded_state(seed)
        for k in range(1,max_k+1):
            result=random_vlns(initial,seed=seed,iterations=iterations,
                destroy_min_stacks=1,destroy_max_stacks=k,
                destroy_include_non_adjacent=not adjacent_only)
            rows.append({"seed":seed,"k":k,"adjacent_only":adjacent_only,
                "iterations":int(result.iterations),"requested_iterations":iterations,"moves":int(result.evaluation.moves),
                "projected_objective":float(result.best_projected_objective),
                "feasible":bool(result.evaluation.feasible),
                "mean_destroy_candidates":float(result.mean_destroy_candidates)})
    summary=[]
    for k in range(1,max_k+1):
        group=[r for r in rows if r["k"]==k]
        moves=[r["moves"] for r in group]
        summary.append({"k":k,"n":len(group),
            "feasible_rate":sum(r["feasible"] for r in group)/len(group),
            "mean_moves":statistics.mean(moves),"median_moves":statistics.median(moves),
            "stdev_moves":statistics.stdev(moves) if len(moves)>1 else 0.0,
            "mean_destroy_candidates":statistics.mean(r["mean_destroy_candidates"] for r in group)})
    paired=[]
    by_seed={seed:{} for seed in seeds}
    for row in rows: by_seed[row["seed"]][row["k"]]=row
    for seed,values in sorted(by_seed.items()):
        baseline=values[1]["moves"]
        for k in range(2,max_k+1):
            paired.append({"seed":seed,"k":k,"baseline_k1_moves":baseline,
                "moves":values[k]["moves"],"delta_vs_k1":values[k]["moves"]-baseline})
    return {"seeds":seeds,"iterations":iterations,"max_k":max_k,
        "adjacent_only":adjacent_only,"results":rows,"summary":summary,"paired_deltas":paired}

def render(payload):
    lines=["# Offline VLNS neighborhood comparison","",
        f"Seeds: {payload['seeds']}",f"Iterations: {payload['iterations']}",
        f"Adjacent only: {payload['adjacent_only']}","",
        "## Summary","",
        "| K | N | Feasible | Mean moves | Median | Stdev | Mean candidates |",
        "|---:|---:|---:|---:|---:|---:|---:|"]
    for r in payload["summary"]:
        lines.append(f"| {r['k']} | {r['n']} | {r['feasible_rate']:.0%} | {r['mean_moves']:.2f} | {r['median_moves']:.2f} | {r['stdev_moves']:.2f} | {r['mean_destroy_candidates']:.2f} |")
    lines += ["","## Paired deltas","",
        "delta = moves(K) - moves(K=1); negative is better.","",
        "| Seed | K | K=1 | K | Delta |","|---:|---:|---:|---:|---:|"]
    for r in payload["paired_deltas"]:
        lines.append(f"| {r['seed']} | {r['k']} | {r['baseline_k1_moves']} | {r['moves']} | {r['delta_vs_k1']:+d} |")
    lines += ["","## Interpretation boundary","",
        "- Offline Random Destroy + Random Repair control only.",
        "- Seeds, initial states, iteration budget, Repair, and acceptance are matched.",
        "- Only the Destroy neighborhood family changes.",
        "- The current projected-search semantics are used; this is not physical reconfiguration evidence.",
        "- A useful neighborhood should improve paired outcomes, not merely increase candidate count."]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",nargs="+",type=int,default=[1,2,3,4,5])
    p.add_argument("--iterations",type=int,default=50)
    p.add_argument("--max-k",type=int,default=3)
    p.add_argument("--adjacent-only",action="store_true")
    p.add_argument("--output",type=Path)
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    if a.iterations<0 or a.max_k<1: p.error("iterations must be >= 0 and max-k must be >= 1")
    payload=run(a.seeds,a.iterations,a.max_k,a.adjacent_only)
    print(render(payload))
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(render(payload)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__": raise SystemExit(main())
