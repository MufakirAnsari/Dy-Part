# experiments/in_depth_hyperparameter_analysis.py
# This script performs a deep dive, linking the scheduler's heuristic cost
# to the actual final performance of the VQE, and logs results to a CSV.

import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import logging
import time
import pandas as pd

# Import all framework components
from vqe_framework.logging_config import setup_logging
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.vqe_executor import PartitionedVQE
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA

logger = setup_logging()

def run_in_depth_analysis(graph: nx.Graph, noise_level: float, alpha_values: list, beta: float, gamma: float, output_csv_path: str):
    """
    Performs a full analysis by running both the scheduler and the subsequent VQE
    for different alpha values, saving results incrementally to a CSV.
    """
    
    logger.info("="*60)
    logger.info("  Starting In-Depth Hyperparameter Sensitivity Analysis")
    logger.info("="*60)

    # --- Setup CSV Logging ---
    results_file_exists = os.path.exists(output_csv_path)
    csv_header = "alpha,chosen_n_sub,heuristic_cost,final_ar,runtime_seconds\n"
    if not results_file_exists:
        with open(output_csv_path, 'w') as f:
            f.write(csv_header)

    # --- Get True Ground State Energy ---
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real

    for alpha in alpha_values:
        experiment_start_time = time.time()
        logger.info(f"--- Analyzing Alpha = {alpha:.2f} ---")
        
        # --- 1. Run the Scheduler to get the plan ---
        cost_model = HeuristicCostModel(gate_error_rate=noise_level, alpha=alpha, beta=beta, gamma=gamma)
        
        logging.getLogger("DyPart").setLevel(logging.WARNING)
        scheduler = DyPartScheduler(cost_model=cost_model)
        partition_plan = scheduler.find_optimal_partition(graph)
        logging.getLogger("DyPart").setLevel(logging.INFO)
        
        chosen_n_sub = partition_plan['optimal_n_sub']
        heuristic_cost = partition_plan['best_cost']
        logger.info(f"Scheduler chose n_sub = {chosen_n_sub} with heuristic cost {heuristic_cost:.4f}")

        # --- 2. Execute the VQE with the Scheduler's plan ---
        qpu = NoisyQPU(n_qubits=graph.number_of_nodes(), gate_error_rate=noise_level, readout_error_rate=noise_level * 10)
        optimizer = COBYLA(maxiter=200)
        
        vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer)
        vqe_result = vqe.run(partition_plan)
        
        final_energy = vqe_result['final_energy']
        approximation_ratio = vqe_result['approximation_ratio']
        
        experiment_runtime = time.time() - experiment_start_time
        logger.info(f"VQE with n_sub={chosen_n_sub} finished with AR = {approximation_ratio:.4f} in {experiment_runtime:.2f}s")
        
        # --- 3. Append result to CSV file ---
        with open(output_csv_path, 'a') as f:
            f.write(f"{alpha},{chosen_n_sub},{heuristic_cost},{approximation_ratio},{experiment_runtime}\n")

    logger.info("="*60)
    logger.info(f"In-depth analysis complete. All results saved to {output_csv_path}")

def plot_in_depth_results(results_df: pd.DataFrame, graph_nodes: int, noise_level: float):
    """
    Generates the final, in-depth analysis plot from the loaded DataFrame.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # --- Plot the Final Performance Outcome vs. Alpha ---
    sns.lineplot(data=results_df, x='alpha', y='final_ar', marker='s', markersize=10, 
                 color='crimson', label='Final VQE Performance (AR)', ax=ax)

    ax.set_xlabel("Hyperparameter α (Weight on Quantum Cost)", fontsize=14)
    ax.set_ylabel("Final Approximation Ratio", fontsize=14)
    ax.set_title(f"Actual Performance vs. Scheduler Strategy (α)\n"
                 f"({graph_nodes}-Node Graph, Noise ε_gate = {noise_level:.1e})", fontsize=16)
    
    ax.axhline(y=1.0, color='black', linestyle=':', label='Ideal Solution (AR=1.0)')
    
    # --- Find and highlight the best performing alpha ---
    best_idx = results_df['final_ar'].idxmax()
    best_alpha = results_df.loc[best_idx, 'alpha']
    best_ar = results_df.loc[best_idx, 'final_ar']
    best_n_sub = results_df.loc[best_idx, 'chosen_n_sub']
    
    ax.plot(best_alpha, best_ar, 'v', markersize=18, color='gold', markeredgecolor='k', 
            label=f'Best Performance (α={best_alpha:.2f})\nChosen n_sub={int(best_n_sub)}\nAR={best_ar:.3f}')
            
    ax.legend(fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=12)
    plt.tight_layout()
    
    output_path = "results/Figure_In_Depth_Analysis.png"
    plt.savefig(output_path, dpi=300)
    print(f"\nIn-depth analysis plot saved to: {output_path}")
    plt.show()

if __name__ == "__main__":
    # --- Configuration ---
    GRAPH_NODES = 10
    problem_graph = nx.random_regular_graph(d=3, n=GRAPH_NODES, seed=42)

    FIXED_NOISE_LEVEL = 5e-3 # 0.5% gate error
    ALPHA_VALUES = [0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
    
    BETA = 1.5
    GAMMA = 0.1
    
    OUTPUT_CSV = "results/in_depth_analysis_data.csv"

    # --- Run the Analysis ---
    run_in_depth_analysis(
        graph=problem_graph,
        noise_level=FIXED_NOISE_LEVEL,
        alpha_values=ALPHA_VALUES,
        beta=BETA,
        gamma=GAMMA,
        output_csv_path=OUTPUT_CSV
    )

    # --- Plot the Final Results from the CSV ---
    try:
        final_data_df = pd.read_csv(OUTPUT_CSV)
        plot_in_depth_results(final_data_df, graph_nodes=GRAPH_NODES, noise_level=FIXED_NOISE_LEVEL)
    except FileNotFoundError:
        logger.error(f"Could not find results file at {OUTPUT_CSV} to plot.")