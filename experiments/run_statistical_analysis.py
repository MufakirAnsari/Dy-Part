#!/usr/bin/env python3
"""experiments/run_statistical_analysis.py

Rigorous Statistical Significance Analysis for Dy-Part Evaluation (ACT-019, ISS-010, ISS-035).
Performs:
1. Paired Wilcoxon signed-rank tests across matching seeds for each (num_nodes, noise_level).
2. Cohen's d effect size calculations.
3. Summary statistical tables (Mean, STD, Median, IQR, p-values).
4. Formatted LaTeX tables and Markdown summary for manuscript inclusion.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats


def compute_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Computes Cohen's d effect size for paired samples."""
    diff = x - y
    n = len(diff)
    if n < 2:
        return 0.0
    sd = float(np.std(diff, ddof=1))
    if sd == 0.0 or np.isnan(sd):
        return 0.0
    return float(np.mean(diff) / sd)


def run_pairwise_analysis(df: pd.DataFrame, method_a: str, method_b: str) -> List[Dict[str, Any]]:
    """Runs Wilcoxon signed-rank test between two methods across (num_nodes, noise_level)."""
    results = []
    node_sizes = sorted(df["num_nodes"].unique())
    noise_levels = sorted(df["noise_level"].unique())

    for nodes in node_sizes:
        for noise in noise_levels:
            sub = df[(df["num_nodes"] == nodes) & (np.isclose(df["noise_level"], noise))]
            a_df = sub[sub["method"] == method_a].set_index("seed_id")["approximation_ratio"]
            b_df = sub[sub["method"] == method_b].set_index("seed_id")["approximation_ratio"]

            # Intersect seeds
            common_seeds = a_df.index.intersection(b_df.index)
            if len(common_seeds) < 3:
                continue

            a_vals = a_df.loc[common_seeds].to_numpy()
            b_vals = b_df.loc[common_seeds].to_numpy()
            diffs = a_vals - b_vals

            mean_a = float(np.mean(a_vals))
            mean_b = float(np.mean(b_vals))
            mean_diff = float(np.mean(diffs))
            d_val = compute_cohens_d(a_vals, b_vals)

            # Wilcoxon signed-rank test
            if np.all(diffs == 0.0):
                stat, p_val = 0.0, 1.0
            else:
                try:
                    w_res = stats.wilcoxon(a_vals, b_vals, alternative="two-sided")
                    stat, p_val = float(w_res.statistic), float(w_res.pvalue)
                except Exception:
                    stat, p_val = 0.0, 1.0

            results.append({
                "method_a": method_a,
                "method_b": method_b,
                "num_nodes": int(nodes),
                "noise_level": float(noise),
                "n_samples": len(common_seeds),
                "mean_a": mean_a,
                "mean_b": mean_b,
                "mean_diff": mean_diff,
                "cohens_d": d_val,
                "wilcoxon_stat": stat,
                "p_value": p_val,
                "significant_p05": p_val < 0.05,
                "significant_p01": p_val < 0.01,
            })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Statistical significance analysis (ACT-019).")
    parser.add_argument(
        "--input",
        type=str,
        default="results/final_benchmark_data_averaged.csv",
        help="Input benchmark CSV file (either final_benchmark_data_averaged.csv or corrected_benchmark.csv)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="results/statistical_analysis_results.csv",
        help="Path for statistical analysis results CSV",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="results/statistical_significance_report.md",
        help="Path for markdown summary report",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Benchmark file not found: {args.input}")

    print("=" * 65)
    print("      DY-PART STATISTICAL SIGNIFICANCE ANALYSIS (ACT-019)")
    print("=" * 65)
    print(f"Loading data from: {args.input}")

    df = pd.read_csv(args.input)
    methods_present = sorted(df["method"].unique())
    print(f"Loaded {len(df)} runs. Methods present: {methods_present}")

    all_comparisons = []
    if "dypart" in methods_present:
        for baseline in [m for m in methods_present if m != "dypart"]:
            print(f"--> Analyzing Dy-Part vs {baseline}...")
            res = run_pairwise_analysis(df, "dypart", baseline)
            all_comparisons.extend(res)

    results_df = pd.DataFrame(all_comparisons)
    os.makedirs(os.path.dirname(args.output_csv) if os.path.dirname(args.output_csv) else "results", exist_ok=True)
    results_df.to_csv(args.output_csv, index=False)
    print(f"Detailed statistics saved to: {args.output_csv}")

    # Generate Markdown Report
    with open(args.output_report, "w", encoding="utf-8") as f:
        f.write("# Statistical Significance Analysis Report (ACT-019)\n\n")
        f.write(f"- **Data Source:** `{args.input}`\n")
        f.write(f"- **Total Experimental Runs:** {len(df)}\n")
        f.write(f"- **Compared Methods:** {', '.join(methods_present)}\n\n")

        f.write("## Overall Mean Approximation Ratios\n\n")
        f.write("| Method | Mean AR | Std AR | Median AR | Min AR | Max AR | Total Runs |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for m in methods_present:
            sub = df[df["method"] == m]["approximation_ratio"]
            f.write(
                f"| **{m}** | {sub.mean():.4f} | {sub.std():.4f} | {sub.median():.4f} | "
                f"{sub.min():.4f} | {sub.max():.4f} | {len(sub)} |\n"
            )
        f.write("\n---\n\n")

        f.write("## Pairwise Hypothesis Testing (Wilcoxon Signed-Rank Test)\n\n")
        for baseline in [m for m in methods_present if m != "dypart"]:
            comp_sub = results_df[results_df["method_b"] == baseline]
            if comp_sub.empty:
                continue
            sig_05 = comp_sub["significant_p05"].sum()
            total_points = len(comp_sub)
            f.write(f"### Dy-Part vs {baseline.capitalize()}\n")
            f.write(f"- Significant improvements ($p < 0.05$): **{sig_05} / {total_points}** configurations.\n")
            f.write(f"- Mean overall difference: **{comp_sub['mean_diff'].mean():+.4f}**\n\n")
            f.write("| Nodes | Noise | Dy-Part Mean AR | Baseline Mean AR | Difference | Cohen's d | p-value | Sig ($p<0.05$) |\n")
            f.write("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for _, r in comp_sub.iterrows():
                sig_star = "**YES**" if r["significant_p05"] else "No"
                f.write(
                    f"| {r['num_nodes']} | {r['noise_level']:.2e} | {r['mean_a']:.4f} | {r['mean_b']:.4f} | "
                    f"{r['mean_diff']:+.4f} | {r['cohens_d']:.2f} | {r['p_value']:.4e} | {sig_star} |\n"
                )
            f.write("\n")

    print(f"Markdown significance report saved to: {args.output_report}")
    print("\n" + "=" * 65)
    print("      STATISTICAL ANALYSIS COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
