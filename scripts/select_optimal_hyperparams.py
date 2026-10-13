#!/usr/bin/env python3
"""scripts/select_optimal_hyperparams.py

Analyzes hyperparameter grid search data (ACT-014) to select optimal (alpha, beta, gamma)
for the corrected cost model (ACT-015, ISS-005).

Calculates:
1. Mean and standard deviation of AR for all 200 configurations.
2. Identifies the global optimum (alpha*, beta*, gamma*).
3. Compares performance against the legacy setting (alpha=0.95, beta=1.5, gamma=0.1).
4. Exports optimal_hyperparameters.json and hyperparam_summary.csv.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import pandas as pd
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze grid search results and select optimal hyperparameters (ACT-015).")
    parser.add_argument(
        "--input",
        type=str,
        default="results/hyperparam_grid_search.csv",
        help="Path to consolidated grid search CSV",
    )
    parser.add_argument(
        "--output-summary",
        type=str,
        default="results/hyperparam_summary.csv",
        help="Path for per-configuration summary CSV",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="results/optimal_hyperparameters.json",
        help="Path for optimal hyperparameters JSON",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    print("=" * 65)
    print("      DY-PART HYPERPARAMETER SELECTION (ACT-015)")
    print("=" * 65)
    print(f"Loading: {args.input}...")

    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} total runs across {df['config_id'].nunique()} configurations.")

    # Group by configuration
    grouped = df.groupby(["config_id", "alpha", "beta", "gamma"]).agg(
        mean_ar=("approximation_ratio", "mean"),
        std_ar=("approximation_ratio", "std"),
        min_ar=("approximation_ratio", "min"),
        max_ar=("approximation_ratio", "max"),
        mean_n_sub=("chosen_n_sub", "mean"),
        mean_cuts=("num_cuts", "mean"),
        mean_runtime=("runtime_seconds", "mean"),
        sample_size=("approximation_ratio", "count"),
    ).reset_index()

    # Sort by mean AR descending, then std ascending
    grouped.sort_values(by=["mean_ar", "std_ar"], ascending=[False, True], inplace=True)
    grouped.to_csv(args.output_summary, index=False)
    print(f"Summary table saved to: {args.output_summary}")

    # Identify optimal configuration
    best = grouped.iloc[0]
    best_config = {
        "config_id": int(best["config_id"]),
        "alpha": float(best["alpha"]),
        "beta": float(best["beta"]),
        "gamma": float(best["gamma"]),
        "mean_approximation_ratio": float(best["mean_ar"]),
        "std_approximation_ratio": float(best["std_ar"]) if not np.isnan(best["std_ar"]) else 0.0,
        "mean_chosen_n_sub": float(best["mean_n_sub"]),
        "mean_num_cuts": float(best["mean_cuts"]),
        "mean_runtime_seconds": float(best["mean_runtime"]),
        "sample_size": int(best["sample_size"]),
    }

    # Locate legacy setting (alpha=0.95, beta=1.5, gamma=0.1)
    legacy_row = grouped[
        (np.isclose(grouped["alpha"], 0.95)) &
        (np.isclose(grouped["beta"], 1.5)) &
        (np.isclose(grouped["gamma"], 0.1))
    ]

    legacy_info = {}
    if not legacy_row.empty:
        l = legacy_row.iloc[0]
        legacy_info = {
            "alpha": 0.95,
            "beta": 1.5,
            "gamma": 0.1,
            "mean_ar": float(l["mean_ar"]),
            "std_ar": float(l["std_ar"]) if not np.isnan(l["std_ar"]) else 0.0,
            "ar_difference": float(best["mean_ar"] - l["mean_ar"]),
        }

    output_data = {
        "optimal_hyperparameters": best_config,
        "legacy_comparison": legacy_info,
        "top_5_configurations": grouped.head(5).to_dict(orient="records"),
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Optimal parameters saved to: {args.output_json}")

    print("\n" + "=" * 65)
    print("      OPTIMAL HYPERPARAMETER SELECTION RESULTS")
    print("=" * 65)
    print(f"Optimal alpha*:  {best_config['alpha']}")
    print(f"Optimal beta*:   {best_config['beta']}")
    print(f"Optimal gamma*:  {best_config['gamma']}")
    print(f"Mean AR at opt:  {best_config['mean_approximation_ratio']:.4f} ± {best_config['std_approximation_ratio']:.4f}")
    if legacy_info:
        print(f"Mean AR legacy:  {legacy_info['mean_ar']:.4f} ± {legacy_info['std_ar']:.4f}")
        print(f"Improvement:     +{legacy_info['ar_difference']:.4f} ({(legacy_info['ar_difference']/legacy_info['mean_ar'])*100:.2f}%)")
    print("=" * 65)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[FATAL ERROR]: {exc}", file=sys.stderr)
        sys.exit(1)
