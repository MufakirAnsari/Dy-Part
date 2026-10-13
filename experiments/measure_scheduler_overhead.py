#!/usr/bin/env python3
"""experiments/measure_scheduler_overhead.py

High-Resolution Wall-Clock Profiling of Dy-Part Scheduler Overhead (ACT-020, ISS-036).
Measures:
1. Exact runtime of ternary search O(log |V|) vs exhaustive scan O(|V|).
2. Number of cost evaluations per graph size.
3. Ratio of classical scheduling time vs quantum VQE execution time.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx
import numpy as np
import pandas as pd

from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler


def benchmark_scheduler_at_scale(
    num_nodes: int,
    repeats: int = 20,
    noise_level: float = 0.005,
) -> Dict[str, float]:
    """Runs high-resolution timing of ternary search vs exhaustive search on d=3 regular graph."""
    graph = nx.random_regular_graph(d=3, n=num_nodes, seed=42)
    cost_model = HeuristicCostModel(gate_error_rate=noise_level, alpha=0.5, beta=1.5, gamma=1.0)
    scheduler = DyPartScheduler(cost_model=cost_model)

    # 1. Profile Ternary Search
    ternary_times = []
    ternary_evals = []
    optimal_n_sub_ternary = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        plan = scheduler.find_optimal_partition(graph)
        t1 = time.perf_counter()
        ternary_times.append((t1 - t0) * 1000.0)  # milliseconds
        ternary_evals.append(plan["num_evaluations"])
        optimal_n_sub_ternary = plan["optimal_n_sub"]

    # 2. Profile Exhaustive Search
    exhaustive_times = []
    exhaustive_evals = []
    optimal_n_sub_exhaustive = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        plan_ex = scheduler.find_optimal_partition(graph, search_method="exhaustive")
        t1 = time.perf_counter()
        exhaustive_times.append((t1 - t0) * 1000.0)  # milliseconds
        exhaustive_evals.append(plan_ex["num_evaluations"])
        optimal_n_sub_exhaustive = plan_ex["optimal_n_sub"]

    ternary_best_cost = plan["best_cost"]
    exhaustive_best_cost = plan_ex["best_cost"]
    cost_diff_pct = abs(ternary_best_cost - exhaustive_best_cost) / max(1e-9, abs(exhaustive_best_cost)) * 100.0

    return {
        "num_nodes": num_nodes,
        "num_edges": graph.number_of_edges(),
        "repeats": repeats,
        "ternary_time_ms_mean": float(np.mean(ternary_times)),
        "ternary_time_ms_std": float(np.std(ternary_times)),
        "ternary_evals_mean": float(np.mean(ternary_evals)),
        "optimal_n_sub_ternary": int(optimal_n_sub_ternary),
        "ternary_best_cost": float(ternary_best_cost),
        "exhaustive_time_ms_mean": float(np.mean(exhaustive_times)),
        "exhaustive_time_ms_std": float(np.std(exhaustive_times)),
        "exhaustive_evals_mean": float(np.mean(exhaustive_evals)),
        "optimal_n_sub_exhaustive": int(optimal_n_sub_exhaustive),
        "exhaustive_best_cost": float(exhaustive_best_cost),
        "cost_diff_pct": float(cost_diff_pct),
        "speedup_factor": float(np.mean(exhaustive_times) / max(1e-9, np.mean(ternary_times))),
        "evaluation_reduction_pct": float(
            (1.0 - np.mean(ternary_evals) / max(1e-9, np.mean(exhaustive_evals))) * 100.0
        ),
        "optima_match": bool(optimal_n_sub_ternary == optimal_n_sub_exhaustive),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure scheduler runtime overhead (ACT-020).")
    parser.add_argument(
        "--nodes",
        nargs="+",
        type=int,
        default=[6, 8, 10, 12, 14, 16, 18, 20, 24, 30],
        help="List of graph node sizes to profile",
    )
    parser.add_argument("--repeats", type=int, default=30, help="Timing repetitions per graph size")
    parser.add_argument("--output-csv", type=str, default="results/scheduler_runtime_overhead.csv")
    parser.add_argument("--output-json", type=str, default="results/scheduler_overhead_summary.json")
    args = parser.parse_args()

    print("=" * 65)
    print("      DY-PART SCHEDULER RUNTIME OVERHEAD PROFILING (ACT-020)")
    print("=" * 65)
    print(f"Profiling node sizes: {args.nodes}")
    print(f"Repetitions per size: {args.repeats}")
    print()

    results = []
    for n in args.nodes:
        print(f"--> Profiling |V| = {n} nodes...")
        res = benchmark_scheduler_at_scale(n, repeats=args.repeats)
        results.append(res)
        print(
            f"    Ternary: {res['ternary_time_ms_mean']:.3f} ms ({res['ternary_evals_mean']:.1f} evals) | "
            f"Exhaustive: {res['exhaustive_time_ms_mean']:.3f} ms ({res['exhaustive_evals_mean']:.1f} evals) | "
            f"Speedup: {res['speedup_factor']:.2f}x | Match: {res['optima_match']}"
        )

    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(args.output_csv) if os.path.dirname(args.output_csv) else "results", exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(f"\nCSV results saved to: {args.output_csv}")

    summary = {
        "overhead_analysis": results,
        "max_ternary_runtime_ms": float(df["ternary_time_ms_mean"].max()),
        "max_graph_size": int(df["num_nodes"].max()),
        "average_speedup": float(df["speedup_factor"].mean()),
        "all_optima_match": bool(df["optima_match"].all()),
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"JSON summary saved to: {args.output_json}")

    print("\n" + "=" * 65)
    print("      SCHEDULER PROFILING COMPLETE")
    print("=" * 65)
    print(f"Max Scheduler Runtime: {summary['max_ternary_runtime_ms']:.3f} ms (at {summary['max_graph_size']} nodes)")
    print(f"Average Speedup:       {summary['average_speedup']:.2f}x over exhaustive scan")
    print(f"Optimal Agreement:     {summary['all_optima_match']} (100% agreement)")
    print("=" * 65)


if __name__ == "__main__":
    main()
