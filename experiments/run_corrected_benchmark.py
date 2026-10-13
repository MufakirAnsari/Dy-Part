#!/usr/bin/env python3
"""experiments/run_corrected_benchmark.py

Full Multi-Scale Corrected Benchmark across Graph Scales (EXP-003, ACT-018).
Compares 4 partitioning paradigms:
1. 'dypart': Noise-adaptive dynamic partitioning with ternary search (tuned alpha, beta, gamma).
2. 'static': Fixed subgraph size baseline (n_sub = 4).
3. 'metis': Classical graph partitioning baseline via METIS (ACT-016).
4. 'random': Random-guess partitioning sanity lower bound (ACT-017).

Graph scales: 8, 10, 12, 16, 20 nodes (3-regular).
Noise levels: 8 log-spaced levels from 10^-3.5 to 10^-1.5.
Seeds: Up to 30 seeds per configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, List

import networkx as nx
import numpy as np
import pandas as pd

from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.logging_config import setup_logging
from vqe_framework.scheduler import DyPartScheduler

logger = setup_logging()

COLUMNS = [
    "method", "num_nodes", "noise_level", "chosen_n_sub", "num_cuts",
    "final_energy", "true_energy", "approximation_ratio", "runtime_seconds", "seed_id"
]


def load_optimal_hyperparams(json_path: str = "results/optimal_hyperparameters.json") -> Dict[str, float]:
    """Loads tuned hyperparameters from ACT-015 if available, else uses defaults."""
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            opt = data.get("optimal_hyperparameters", {})
            return {
                "alpha": float(opt.get("alpha", 0.5)),
                "beta": float(opt.get("beta", 1.5)),
                "gamma": float(opt.get("gamma", 1.0)),
            }
        except Exception as exc:
            logger.warning("Failed to load %s (%s); using defaults.", json_path, exc)
    return {"alpha": 0.5, "beta": 1.5, "gamma": 1.0}


def run_single_benchmark_experiment(
    graph: nx.Graph,
    noise_level: float,
    method: str,
    vqe_seed: int,
    hyperparams: Dict[str, float],
) -> Dict[str, Any]:
    """Executes a single benchmark run for a specific method, graph, noise, and seed."""
    start_time = time.time()
    num_nodes = graph.number_of_nodes()
    logger.info("--- Starting Exp: Method=%s, Nodes=%d, Noise=%.2e, Seed=%d ---", method, num_nodes, noise_level, vqe_seed)

    # 1. Determine Partition Plan
    if method == "dypart":
        cost_model = HeuristicCostModel(
            gate_error_rate=noise_level,
            alpha=hyperparams["alpha"],
            beta=hyperparams["beta"],
            gamma=hyperparams["gamma"],
        )
        scheduler = DyPartScheduler(cost_model=cost_model)
        partition_plan = scheduler.find_optimal_partition(graph)
        partition_plan["partition_method"] = "greedy"
    elif method == "static":
        partition_plan = {"optimal_n_sub": 4, "partition_method": "greedy"}
    elif method == "metis":
        partition_plan = {"optimal_n_sub": 4, "partition_method": "metis"}
    elif method == "random":
        partition_plan = {"optimal_n_sub": 4, "partition_method": "random"}
    else:
        raise ValueError(f"Unknown benchmarking method: {method}")

    # 2. Lazy imports for quantum simulation
    from vqe_framework.qpu_interface import NoisyQPU
    from vqe_framework.vqe_executor import PartitionedVQE
    from qiskit_algorithms.optimizers import COBYLA

    qpu = NoisyQPU(n_qubits=num_nodes, gate_error_rate=noise_level, readout_error_rate=noise_level * 10)
    optimizer = COBYLA(maxiter=200)
    vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer, seed=vqe_seed)
    result = vqe.run(partition_plan)

    final_energy = result["final_energy"]
    max_cut = result.get("max_cut", 1)
    approximation_ratio = result["approximation_ratio"]
    true_min_energy = -float(max_cut)
    optimal_n_sub = partition_plan.get("optimal_n_sub", 4)
    num_cuts = getattr(vqe, "num_cuts", 0)

    runtime = time.time() - start_time
    logger.info(
        "--- Finished Exp: Method=%s, n_sub=%d, Cuts=%d, AR=%.4f, Time=%.2fs ---",
        method, optimal_n_sub, num_cuts, approximation_ratio, runtime
    )

    return {
        "method": method,
        "num_nodes": num_nodes,
        "noise_level": noise_level,
        "chosen_n_sub": optimal_n_sub,
        "num_cuts": num_cuts,
        "final_energy": final_energy,
        "true_energy": true_min_energy,
        "approximation_ratio": approximation_ratio,
        "runtime_seconds": runtime,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-scale corrected benchmark runner (EXP-003, ACT-018).")
    parser.add_argument("--start-seed", type=int, default=0, help="Starting seed ID (inclusive, default: 0)")
    parser.add_argument("--end-seed", type=int, default=30, help="Ending seed ID (exclusive, default: 30)")
    parser.add_argument("--nodes", nargs="+", type=int, default=[8, 10, 12, 16, 20], help="List of node sizes to benchmark")
    parser.add_argument("--methods", nargs="+", default=["dypart", "static", "metis", "random"], help="Methods to compare")
    parser.add_argument("--output", type=str, default="results/corrected_benchmark.csv", help="Output CSV path")
    parser.add_argument("--hyperparams-json", type=str, default="results/optimal_hyperparameters.json", help="Path to optimal hyperparams JSON")
    args = parser.parse_args()

    node_sizes = args.nodes
    methods = args.methods
    noise_levels = np.logspace(-3.5, -1.5, 8)
    start_seed = args.start_seed
    end_seed = args.end_seed
    output_path = args.output

    hyperparams = load_optimal_hyperparams(args.hyperparams_json)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "results", exist_ok=True)

    existing_runs = set()
    all_results = []
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            for _, r in existing_df.iterrows():
                key = (str(r["method"]), int(r["num_nodes"]), round(float(r["noise_level"]), 6), int(r["seed_id"]))
                existing_runs.add(key)
                all_results.append(r.to_dict())
            logger.info("Found %d already completed runs in %s; resuming remaining.", len(existing_runs), output_path)
        except Exception as exc:
            logger.warning("Could not read existing file %s: %s", output_path, exc)
            pd.DataFrame(columns=COLUMNS).to_csv(output_path, index=False)
    else:
        pd.DataFrame(columns=COLUMNS).to_csv(output_path, index=False)

    logger.info("=" * 65)
    logger.info("      DY-PART MULTI-SCALE BENCHMARK (ACT-018)")
    logger.info("=" * 65)
    logger.info("Methods:      %s", methods)
    logger.info("Node sizes:   %s", node_sizes)
    logger.info("Seeds:        [%d, %d)", start_seed, end_seed)
    logger.info("Hyperparams:  %s", hyperparams)
    logger.info("Output:       %s", output_path)
    logger.info("=" * 65)

    for seed_id in range(start_seed, end_seed):
        logger.info("\n%s RUNNING SEED %d [%d, %d) %s\n", "=" * 20, seed_id, start_seed, end_seed, "=" * 20)
        for nodes in node_sizes:
            graph = nx.random_regular_graph(d=3, n=nodes, seed=42 + seed_id)
            for noise in noise_levels:
                for method in methods:
                    run_key = (str(method), int(nodes), round(float(noise), 6), int(seed_id))
                    if run_key in existing_runs:
                        continue
                    base_info = {"seed_id": seed_id}
                    try:
                        res = run_single_benchmark_experiment(
                            graph=graph,
                            noise_level=float(noise),
                            method=method,
                            vqe_seed=123 + seed_id,
                            hyperparams=hyperparams,
                        )
                        res.update(base_info)
                        all_results.append(res)
                        existing_runs.add(run_key)
                        # Incremental write
                        pd.DataFrame([res])[COLUMNS].to_csv(output_path, mode="a", header=False, index=False)
                    except Exception as exc:
                        logger.error("Failed for method=%s, nodes=%d, noise=%.2e, seed=%d: %s", method, nodes, noise, seed_id, exc)
                        raise exc

    expected_runs = (end_seed - start_seed) * len(node_sizes) * len(noise_levels) * len(methods)
    if len(all_results) < expected_runs:
        raise RuntimeError(f"Expected {expected_runs} benchmark runs, but only completed {len(all_results)}.")

    logger.info("Benchmark complete! Saved %d runs to %s", len(all_results), output_path)


if __name__ == "__main__":
    main()
