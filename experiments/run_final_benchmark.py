# experiments/run_final_benchmark.py
# VERSION 2: Includes statistical averaging over multiple random seeds.

import qiskit.circuit.library
if not hasattr(qiskit.circuit.library, "evolved_operator_ansatz"):
    if hasattr(qiskit.circuit.library, "EvolvedOperatorAnsatz"):
        setattr(qiskit.circuit.library, "evolved_operator_ansatz", qiskit.circuit.library.EvolvedOperatorAnsatz)

import networkx as nx
import numpy as np
import pandas as pd
import os
import time
import logging

# Import all framework components
from vqe_framework.logging_config import setup_logging
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.vqe_executor import PartitionedVQE
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms.optimizers import COBYLA

# Setup logger for this experiment
logger = setup_logging()

def run_single_experiment(graph: nx.Graph, noise_level: float, method: str, vqe_seed: int):
    """
    Runs a single, complete VQE experiment for a given method and seed.
    """
    start_time = time.time()
    logger.info(f"--- Starting Exp: Method={method}, Nodes={graph.number_of_nodes()}, Noise={noise_level:.2e}, Seed={vqe_seed} ---")

    # Determine Partition Plan
    if method == 'dypart':
        cost_model = HeuristicCostModel(gate_error_rate=noise_level, alpha=0.95, beta=1.5, gamma=0.1)
        scheduler = DyPartScheduler(cost_model=cost_model)
        partition_plan = scheduler.find_optimal_partition(graph)
    elif method == 'static':
        partition_plan = {"optimal_n_sub": 4}
    else:
        raise ValueError(f"Unknown method: {method}")

    optimal_n_sub = partition_plan['optimal_n_sub']
    
    # Execute VQE
    # Pass the seed to the QPU and the VQE executor
    qpu = NoisyQPU(n_qubits=graph.number_of_nodes(), gate_error_rate=noise_level, readout_error_rate=noise_level * 10)
    optimizer = COBYLA(maxiter=200)
    
    # Pass the seed to the VQE executor for reproducible initial parameters
    vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer, seed=vqe_seed)
    result = vqe.run(partition_plan)
    
    final_energy = result['final_energy']
    expected_cut = result.get('expected_cut', 0.0)
    max_cut = result.get('max_cut', 1)
    approximation_ratio = result['approximation_ratio']
    true_min_energy = -float(max_cut)
    
    end_time = time.time()
    runtime = end_time - start_time
    
    logger.info(f"--- Finished Exp: Cut={expected_cut:.2f}/{max_cut}, AR={approximation_ratio:.4f}, Time={runtime:.2f}s ---")
    
    return {
        "method": method,
        "num_nodes": graph.number_of_nodes(),
        "noise_level": noise_level,
        "chosen_n_sub": optimal_n_sub,
        "final_energy": final_energy,
        "true_energy": true_min_energy,
        "approximation_ratio": approximation_ratio,
        "runtime_seconds": runtime,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dy-Part final benchmark reproduction runner.")
    parser.add_argument("--start-seed", type=int, default=0, help="Starting seed ID (inclusive, default: 0)")
    parser.add_argument("--end-seed", type=int, default=30, help="Ending seed ID (exclusive, default: 30)")
    parser.add_argument("--output", type=str, default="results/final_benchmark_data_averaged.csv", help="Path to output CSV")
    args = parser.parse_args()

    # --- EXPERIMENT CONFIGURATION ---
    NODE_SIZES = [8, 10, 12]
    NOISE_LEVELS = np.logspace(-3.5, -1.5, 8)
    
    start_seed = args.start_seed
    end_seed = args.end_seed
    output_path = args.output
    
    COLUMNS = [
        "method", "num_nodes", "noise_level", "chosen_n_sub",
        "final_energy", "true_energy", "approximation_ratio", "runtime_seconds", "seed_id"
    ]

    all_results = []
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "results", exist_ok=True)
    
    # Initialize CSV with header if file does not exist
    if not os.path.exists(output_path):
        pd.DataFrame(columns=COLUMNS).to_csv(output_path, index=False)
    
    logger.info(f"=== Benchmark Starting: Seeds {start_seed} to {end_seed} -> {output_path} ===")

    # --- Outer loop for statistical averaging ---
    for seed_id in range(start_seed, end_seed):
        logger.info(f"\n{'='*20} RUNNING SEED {seed_id} (Range [{start_seed}, {end_seed})) {'='*20}\n")
        
        for nodes in NODE_SIZES:
            # Generate a reproducible random graph for each seed
            graph = nx.random_regular_graph(d=3, n=nodes, seed=42 + seed_id)
            
            for noise in NOISE_LEVELS:
                # Add seed_id to the results dictionary
                base_info = {"seed_id": seed_id}

                # Run Dy-Part
                try:
                    dypart_result = run_single_experiment(graph, noise, 'dypart', vqe_seed=123 + seed_id)
                    dypart_result.update(base_info)
                    all_results.append(dypart_result)
                    pd.DataFrame([dypart_result])[COLUMNS].to_csv(output_path, mode='a', header=False, index=False)
                except Exception as e:
                    logger.error(f"Dy-Part failed for seed {seed_id}, {nodes} nodes, noise {noise:.2e}: {e}")

                # Run Static Baseline
                try:
                    static_result = run_single_experiment(graph, noise, 'static', vqe_seed=123 + seed_id)
                    static_result.update(base_info)
                    all_results.append(static_result)
                    pd.DataFrame([static_result])[COLUMNS].to_csv(output_path, mode='a', header=False, index=False)
                except Exception as e:
                    logger.error(f"Static failed for seed {seed_id}, {nodes} nodes, noise {noise:.2e}: {e}")
    
    # --- Final summary ---
    results_df = pd.DataFrame(all_results)
    
    print("\n\n" + "="*50)
    print("      FINAL AVERAGED BENCHMARK COMPLETE")
    print("="*50)
    print(f"All data saved incrementally to: {output_path} (Total runs: {len(results_df)})")
    if not results_df.empty:
        print("\nFinal Averaged Results DataFrame (head):")
        print(results_df[COLUMNS].head())