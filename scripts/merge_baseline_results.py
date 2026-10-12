#!/usr/bin/env python3
"""scripts/merge_baseline_results.py

Merges partitioned baseline reproduction runs (Seeds 10-29 across 4 parallel workers)
with the existing validated base results (Seeds 0-9) to produce the consolidated,
100% verified 30-seed dataset (1,440 runs).

Performs strict integrity checks:
1. Validates all expected seed IDs (0 to 29) are present without gaps or duplicates.
2. Validates exact run counts (48 runs per seed, 1,440 runs total).
3. Validates strict bounded AR in [0.0, 1.0] across all rows.
4. Validates matching column ordering.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Set
import pandas as pd

EXPECTED_COLUMNS = [
    "method", "num_nodes", "noise_level", "chosen_n_sub",
    "final_energy", "true_energy", "approximation_ratio", "runtime_seconds", "seed_id"
]

EXPECTED_RUNS_PER_SEED = 48
EXPECTED_TOTAL_SEEDS = 30
EXPECTED_TOTAL_RUNS = EXPECTED_TOTAL_SEEDS * EXPECTED_RUNS_PER_SEED  # 1,440


def validate_dataframe(df: pd.DataFrame, source_name: str, expected_seeds: Set[int] | None = None) -> None:
    """Validates schema, seed counts, and AR bounds of a benchmark DataFrame."""
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"[{source_name}] Schema mismatch.\nExpected: {EXPECTED_COLUMNS}\nGot: {list(df.columns)}"
        )

    if df.empty:
        raise ValueError(f"[{source_name}] DataFrame is empty.")

    # Null checks
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        raise ValueError(f"[{source_name}] Contains null values:\n{null_counts[null_counts > 0]}")

    # Seed checks
    seeds_found = set(df["seed_id"].astype(int).unique())
    if expected_seeds is not None and seeds_found != expected_seeds:
        missing = expected_seeds - seeds_found
        extra = seeds_found - expected_seeds
        raise ValueError(
            f"[{source_name}] Seed mismatch. Missing: {sorted(missing)}, Unexpected: {sorted(extra)}"
        )

    # Run counts per seed
    seed_counts = df["seed_id"].astype(int).value_counts()
    invalid_counts = seed_counts[seed_counts != EXPECTED_RUNS_PER_SEED]
    if not invalid_counts.empty:
        raise ValueError(
            f"[{source_name}] Invalid run count per seed (expected {EXPECTED_RUNS_PER_SEED}):\n{invalid_counts}"
        )

    # AR bounds check
    invalid_ar = df[(df["approximation_ratio"] < 0.0) | (df["approximation_ratio"] > 1.0)]
    if not invalid_ar.empty:
        raise ValueError(
            f"[{source_name}] Found {len(invalid_ar)} rows violating 0.0 <= AR <= 1.0:\n"
            f"{invalid_ar[['seed_id', 'method', 'num_nodes', 'noise_level', 'approximation_ratio']].head(10)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and audit partitioned baseline benchmark datasets.")
    parser.add_argument(
        "--base-file",
        type=str,
        default="results/final_benchmark_data_averaged.csv",
        help="Path to existing validated base CSV (contains seeds 0-9)",
    )
    parser.add_argument(
        "--part-files",
        nargs="+",
        default=[
            "results/baseline_part_0.csv",
            "results/baseline_part_1.csv",
            "results/baseline_part_2.csv",
            "results/baseline_part_3.csv",
        ],
        help="List of worker partition CSV files to merge",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="results/final_benchmark_data_averaged.csv",
        help="Path for the consolidated merged CSV",
    )
    parser.add_argument(
        "--delete-parts",
        action="store_true",
        help="Remove partition CSV files after successful merge",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("      DY-PART BASELINE REPRODUCTION: MERGE & AUDIT TOOL")
    print("=" * 65)
    print(f"Base file:   {args.base_file}")
    print(f"Part files:  {args.part_files}")
    print(f"Output file: {args.output_file}")
    print()

    # 1. Load and validate base file (Seeds 0-9)
    if not os.path.exists(args.base_file):
        raise FileNotFoundError(f"Base file not found: {args.base_file}")

    print(f"--> Loading base file: {args.base_file}...")
    base_df = pd.read_csv(args.base_file)
    expected_base_seeds = set(range(0, 10))
    validate_dataframe(base_df, "Base File", expected_seeds=expected_base_seeds)
    print(f"    Base file verified: {len(base_df)} runs, Seeds 0 to 9.")

    # 2. Load and validate each part file
    expected_ranges = [
        set(range(10, 15)),  # Part 0: Seeds 10-14
        set(range(15, 20)),  # Part 1: Seeds 15-19
        set(range(20, 25)),  # Part 2: Seeds 20-24
        set(range(25, 30)),  # Part 3: Seeds 25-29
    ]

    dfs_to_merge = [base_df]

    for idx, part_file in enumerate(args.part_files):
        if not os.path.exists(part_file):
            raise FileNotFoundError(f"Worker partition file not found: {part_file}")

        print(f"--> Loading worker part {idx}: {part_file}...")
        part_df = pd.read_csv(part_file)
        expected_part_seeds = expected_ranges[idx] if idx < len(expected_ranges) else None
        validate_dataframe(part_df, f"Part {idx} ({part_file})", expected_seeds=expected_part_seeds)
        print(f"    Part {idx} verified: {len(part_df)} runs, Seeds {min(expected_part_seeds)} to {max(expected_part_seeds)}.")
        dfs_to_merge.append(part_df)

    # 3. Concatenate and sort
    print("\n--> Merging all partitions...")
    merged_df = pd.concat(dfs_to_merge, ignore_index=True)
    merged_df["seed_id"] = merged_df["seed_id"].astype(int)
    merged_df.sort_values(by=["seed_id", "num_nodes", "noise_level", "method"], inplace=True)

    # 4. Final consolidated validation
    expected_all_seeds = set(range(0, EXPECTED_TOTAL_SEEDS))
    validate_dataframe(merged_df, "Consolidated Dataset", expected_seeds=expected_all_seeds)

    if len(merged_df) != EXPECTED_TOTAL_RUNS:
        raise ValueError(
            f"Consolidated dataset has {len(merged_df)} runs, expected exactly {EXPECTED_TOTAL_RUNS}."
        )

    # 5. Atomic write to output
    temp_output = args.output_file + ".tmp"
    merged_df[EXPECTED_COLUMNS].to_csv(temp_output, index=False)
    os.replace(temp_output, args.output_file)
    print(f"--> Consolidated dataset successfully saved to: {args.output_file}")

    # 6. Delete parts if requested
    if args.delete_parts:
        print("--> Cleaning up worker partition files...")
        for part_file in args.part_files:
            try:
                os.remove(part_file)
                print(f"    Removed {part_file}")
            except OSError as e:
                print(f"    Warning: Could not remove {part_file}: {e}")

    # 7. Print final summary statistics
    print("\n" + "=" * 65)
    print("      CONSOLIDATED BENCHMARK AUDIT COMPLETE: 100% SUCCESS")
    print("=" * 65)
    print(f"Total Seeds:       {EXPECTED_TOTAL_SEEDS} (Seeds 0 to 29)")
    print(f"Total Runs:        {len(merged_df)}")
    print(f"Min AR:            {merged_df['approximation_ratio'].min():.4f}")
    print(f"Max AR:            {merged_df['approximation_ratio'].max():.4f}")
    print(f"Mean AR (Dy-Part): {merged_df[merged_df['method'] == 'dypart']['approximation_ratio'].mean():.4f}")
    print(f"Mean AR (Static):  {merged_df[merged_df['method'] == 'static']['approximation_ratio'].mean():.4f}")
    print(f"AR in [0.0, 1.0]:  Strictly True (0 violations)")
    print("=" * 65)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[FATAL ERROR during merge]: {exc}", file=sys.stderr)
        sys.exit(1)
