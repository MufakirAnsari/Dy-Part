#!/usr/bin/env python3
"""scripts/merge_corrected_benchmark_results.py

Merges and audits partitioned corrected multi-scale benchmark datasets (ACT-018).
Ensures all 4 methods, graph sizes, and seeds are cleanly merged with zero AR violations.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import pandas as pd

from experiments.run_corrected_benchmark import COLUMNS


def validate_benchmark_dataframe(df: pd.DataFrame, source_name: str) -> None:
    """Validates schema, nulls, and AR bounds for a benchmark DataFrame."""
    if list(df.columns) != COLUMNS:
        raise ValueError(
            f"[{source_name}] Schema mismatch.\nExpected: {COLUMNS}\nGot: {list(df.columns)}"
        )

    if df.empty:
        raise ValueError(f"[{source_name}] DataFrame is empty.")

    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        raise ValueError(f"[{source_name}] Contains null values:\n{null_counts[null_counts > 0]}")

    invalid_ar = df[(df["approximation_ratio"] < 0.0) | (df["approximation_ratio"] > 1.0)]
    if not invalid_ar.empty:
        raise ValueError(
            f"[{source_name}] Found {len(invalid_ar)} rows violating 0.0 <= AR <= 1.0:\n"
            f"{invalid_ar[['method', 'num_nodes', 'noise_level', 'approximation_ratio']].head(10)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and audit partitioned multi-scale benchmark datasets.")
    parser.add_argument(
        "--part-files",
        nargs="+",
        default=None,
        help="List of worker partition CSV files (or auto-discovered via pattern if omitted)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="results/benchmark_part_*.csv",
        help="Glob pattern to find partition files when --part-files is not explicitly passed",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="results/corrected_benchmark.csv",
        help="Path for the consolidated merged CSV",
    )
    parser.add_argument(
        "--delete-parts",
        action="store_true",
        help="Remove partition CSV files after successful merge",
    )
    args = parser.parse_args()

    part_files = args.part_files
    if not part_files:
        part_files = sorted(glob.glob(args.pattern))

    if not part_files:
        raise FileNotFoundError(f"No partition files found matching pattern: {args.pattern}")

    print("=" * 65)
    print("      DY-PART FULL BENCHMARK MERGE & AUDIT TOOL (ACT-018)")
    print("=" * 65)
    print(f"Found {len(part_files)} partition files.")
    print(f"Output file: {args.output_file}")
    print()

    dfs = []
    for part in part_files:
        print(f"--> Loading {part}...")
        df = pd.read_csv(part)
        validate_benchmark_dataframe(df, part)
        print(f"    Verified {len(df)} runs.")
        dfs.append(df)

    merged = pd.concat(dfs, ignore_index=True)
    merged["seed_id"] = merged["seed_id"].astype(int)
    merged["num_nodes"] = merged["num_nodes"].astype(int)

    # Deduplicate in case of overlapping runs
    initial_len = len(merged)
    merged.drop_duplicates(subset=["method", "num_nodes", "noise_level", "seed_id"], keep="last", inplace=True)
    if len(merged) < initial_len:
        print(f"--> Deduplicated {initial_len - len(merged)} duplicate rows.")

    merged.sort_values(by=["seed_id", "num_nodes", "noise_level", "method"], inplace=True)
    validate_benchmark_dataframe(merged, "Consolidated Dataset")

    # Atomic write to output
    temp_output = args.output_file + ".tmp"
    merged[COLUMNS].to_csv(temp_output, index=False)
    os.replace(temp_output, args.output_file)
    print(f"\n--> Successfully saved {len(merged)} runs to {args.output_file}")

    if args.delete_parts:
        print("--> Cleaning up partition files...")
        for p in part_files:
            try:
                os.remove(p)
                print(f"    Removed {p}")
            except OSError as err:
                print(f"    Warning: Could not remove {p}: {err}")

    print("\n" + "=" * 65)
    print("      BENCHMARK AUDIT SUMMARY")
    print("=" * 65)
    print(f"Total Runs:       {len(merged)}")
    print(f"Methods:          {sorted(merged['method'].unique())}")
    print(f"Node Sizes:       {sorted(merged['num_nodes'].unique())}")
    print(f"Seeds:            {merged['seed_id'].nunique()}")
    print(f"Min AR:           {merged['approximation_ratio'].min():.4f}")
    print(f"Max AR:           {merged['approximation_ratio'].max():.4f}")
    for m in sorted(merged["method"].unique()):
        sub = merged[merged["method"] == m]
        print(f"Mean AR ({m:7s}): {sub['approximation_ratio'].mean():.4f} (N={len(sub)})")
    print(f"AR in [0.0, 1.0]: Strictly True (0 violations)")
    print("=" * 65)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[FATAL ERROR during merge]: {exc}", file=sys.stderr)
        sys.exit(1)
