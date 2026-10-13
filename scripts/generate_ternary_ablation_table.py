# scripts/generate_ternary_ablation_table.py
"""Generate publication-ready ternary search vs exhaustive scan ablation table (ACT-023, ISS-001).

Loads empirical profiling data from results/scheduler_runtime_overhead.csv and outputs:
- results/ternary_ablation_table.csv
- results/ternary_ablation_table.md
"""

import os
import sys
import pandas as pd

def main():
    in_csv = "results/scheduler_runtime_overhead.csv"
    if not os.path.exists(in_csv):
        print(f"Error: {in_csv} not found.")
        sys.exit(1)

    df = pd.read_csv(in_csv)
    
    out_df = pd.DataFrame({
        "num_nodes": df["num_nodes"],
        "num_edges": df["num_edges"],
        "ternary_evals": df["ternary_evals_mean"].round(1),
        "exhaustive_evals": df["exhaustive_evals_mean"].round(1),
        "eval_reduction_pct": df["evaluation_reduction_pct"].round(2),
        "ternary_time_ms": df["ternary_time_ms_mean"].round(3),
        "exhaustive_time_ms": df["exhaustive_time_ms_mean"].round(3),
        "speedup_factor": df["speedup_factor"].round(2),
        "optimal_n_sub_ternary": df["optimal_n_sub_ternary"],
        "optimal_n_sub_exhaustive": df["optimal_n_sub_exhaustive"],
        "optima_match": df["optima_match"],
        "ternary_cost": df["ternary_best_cost"].round(6),
        "exhaustive_cost": df["exhaustive_best_cost"].round(6),
        "cost_diff_pct": df["cost_diff_pct"].round(2),
    })

    out_csv = "results/ternary_ablation_table.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"Saved ablation table to {out_csv}")

if __name__ == "__main__":
    main()
