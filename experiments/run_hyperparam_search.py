#!/usr/bin/env python3
"""experiments/run_hyperparam_search.py

Hyperparameter Grid Search for Dy-Part Cost Model (EXP-002, ACT-014).
Systematically sweeps (alpha, beta, gamma) on 10-node 3-regular graphs to find
the optimal parameter operating regime for the corrected cost model (DEC-001).

Grid Specification:
- alpha: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95] (10 values)
- beta:  [1.0, 1.5, 2.0, 3.0]                                  (4 values)
- gamma: [0.1, 0.5, 1.0, 2.0, 5.0]                             (5 values)
Total Configurations = 10 x 4 x 5 = 200 configurations.
Total Runs = 200 configs x 10 seeds = 2,000 runs.
"""

from __future__ import annotations

import argparse
import itertools
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
    "config_id", "alpha", "beta", "gamma", "seed_id", "num_nodes", "noise_level",
    "chosen_n_sub", "num_cuts", "quantum_cost", "classical_cost", "total_cost",
    "final_energy", "true_energy", "approximation_ratio", "runtime_seconds"
]

ALPHA_GRID = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
BETA_GRID = [1.0, 1.5, 2.0, 3.0]
GAMMA_GRID = [0.1, 0.5, 1.0, 2.0, 5.0]


def get_all_configurations() -> List[Dict[str, float]]:
    """Generates the deterministic 200-configuration grid list."""
    configs = []
    for cfg_id, (a, b, g) in enumerate(itertools.product(ALPHA_GRID, BETA_GRID, GAMMA_GRID)):
        configs.append({
            "config_id": cfg_id,
            "alpha": round(a, 4),
            "beta": round(b, 4),
            "gamma": round(g, 4),
        })
    return configs


def run_single_hyperparam_run(
    config: Dict[str, Any],
    seed_id: int,
    num_nodes: int = 10,
    noise_level: float = 0.005,
) -> Dict[str, Any]:
    """Executes a single end-to-end Dy-Part run for a specific hyperparameter configuration."""
    start_time = time.time()
    cfg_id = config["config_id"]
    alpha = config["alpha"]
    beta = config["beta"]
    gamma = config["gamma"]

    logger.info(
        "--- Starting Run: Config=%d (α=%.2f, β=%.2f, γ=%.2f), Seed=%d, Noise=%.2e ---",
        cfg_id, alpha, beta, gamma, seed_id, noise_level
    )

    # 1. Generate graph with seed
    graph = nx.random_regular_graph(d=3, n=num_nodes, seed=42 + seed_id)

    # 2. Configure cost model and scheduler
    cost_model = HeuristicCostModel(gate_error_rate=noise_level, alpha=alpha, beta=beta, gamma=gamma)
    scheduler = DyPartScheduler(cost_model=cost_model)
    partition_plan = scheduler.find_optimal_partition(graph)

    optimal_n_sub = partition_plan["optimal_n_sub"]
    min_cost = partition_plan["min_cost"]

    # Retrieve cost breakdown for the chosen n_sub
    cost_breakdown = cost_model.evaluate_cost(graph, optimal_n_sub)
    q_cost = cost_breakdown["quantum_cost"]
    c_cost = cost_breakdown["classical_cost"]
    num_cuts = cost_breakdown["num_cuts"]

    # 3. Execute VQE
    from vqe_framework.qpu_interface import NoisyQPU
    from vqe_framework.vqe_executor import PartitionedVQE
    from qiskit_algorithms.optimizers import COBYLA

    qpu = NoisyQPU(n_qubits=num_nodes, gate_error_rate=noise_level, readout_error_rate=noise_level * 10)
    optimizer = COBYLA(maxiter=200)
    vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer, seed=123 + seed_id)
    result = vqe.run(partition_plan)

    final_energy = result["final_energy"]
    max_cut = result.get("max_cut", 1)
    approximation_ratio = result["approximation_ratio"]
    true_min_energy = -float(max_cut)

    runtime = time.time() - start_time

    logger.info(
        "--- Finished Run: Config=%d, n_sub=%d, AR=%.4f, Time=%.2fs ---",
        cfg_id, optimal_n_sub, approximation_ratio, runtime
    )

    return {
        "config_id": cfg_id,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "seed_id": seed_id,
        "num_nodes": num_nodes,
        "noise_level": noise_level,
        "chosen_n_sub": optimal_n_sub,
        "num_cuts": num_cuts,
        "quantum_cost": q_cost,
        "classical_cost": c_cost,
        "total_cost": min_cost,
        "final_energy": final_energy,
        "true_energy": true_min_energy,
        "approximation_ratio": approximation_ratio,
        "runtime_seconds": runtime,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dy-Part hyperparameter grid search runner (ACT-014).")
    parser.add_argument("--config-start", type=int, default=0, help="Starting config index (inclusive, 0..199)")
    parser.add_argument("--config-end", type=int, default=200, help="Ending config index (exclusive, 1..200)")
    parser.add_argument("--seeds", type=int, default=10, help="Number of random seeds per configuration (default: 10)")
    parser.add_argument("--nodes", type=int, default=10, help="Number of graph nodes (default: 10)")
    parser.add_argument("--noise", type=float, default=0.005, help="Gate error rate noise level (default: 0.005)")
    parser.add_argument("--output", type=str, default="results/hyperparam_grid_search.csv", help="Output CSV path")
    args = parser.parse_args()

    all_configs = get_all_configurations()
    total_available_configs = len(all_configs)

    config_start = max(0, min(args.config_start, total_available_configs))
    config_end = max(config_start, min(args.config_end, total_available_configs))
    active_configs = all_configs[config_start:config_end]
    num_seeds = args.seeds
    output_path = args.output

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "results", exist_ok=True)

    # Initialize CSV with header if file does not exist
    if not os.path.exists(output_path):
        pd.DataFrame(columns=COLUMNS).to_csv(output_path, index=False)

    logger.info("=" * 65)
    logger.info("      DY-PART HYPERPARAMETER GRID SEARCH (ACT-014)")
    logger.info("=" * 65)
    logger.info("Configs:   [%d, %d) (%d configs)", config_start, config_end, len(active_configs))
    logger.info("Seeds:     %d seeds per config", num_seeds)
    logger.info("Nodes:     %d", args.nodes)
    logger.info("Noise:     %.2e", args.noise)
    logger.info("Output:    %s", output_path)
    logger.info("=" * 65)

    all_results = []
    total_runs = len(active_configs) * num_seeds
    run_idx = 0

    for cfg in active_configs:
        cfg_id = cfg["config_id"]
        for seed_id in range(num_seeds):
            run_idx += 1
            logger.info(
                "Progress: Run %d/%d (Config %d/%d, Seed %d/%d)",
                run_idx, total_runs, cfg_id, total_available_configs - 1, seed_id, num_seeds - 1
            )
            try:
                res = run_single_hyperparam_run(cfg, seed_id, num_nodes=args.nodes, noise_level=args.noise)
                all_results.append(res)
                # Incremental flush to disk ensures zero data loss upon walltime limits
                pd.DataFrame([res])[COLUMNS].to_csv(output_path, mode="a", header=False, index=False)
            except Exception as exc:
                logger.error("Run failed for config %d, seed %d: %s", cfg_id, seed_id, exc)

    logger.info("Grid search completed successfully! Saved %d runs to %s", len(all_results), output_path)


if __name__ == "__main__":
    main()
