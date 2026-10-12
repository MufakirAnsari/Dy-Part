# experiments/in_depth_beta_gamma_analysis.py
# This script performs an in-depth analysis of the scheduler's sensitivity
# to beta and gamma, linking their values to the final VQE performance.

import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import logging
import pandas as pd
import time

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

def run_in_depth_beta_gamma_analysis(graph: nx.Graph, noise_level: float, alpha: float, 
                                     beta_values: list, gamma_values: list, output_csv_path: str):
    """
    Runs a full scheduler->VQE pipeline for different beta and gamma values.
    """
    logger.info("="*60)
    logger.info("  Starting In-Depth Beta/Gamma Sensitivity Analysis")
    logger.info("="*60)
    
    # Setup CSV Logging
    if not os.path.exists(output_csv_path):
        with open(output_csv_path, 'w') as f:
            f.write("beta,gamma,chosen_n_sub,final_ar,runtime_seconds\n")

    # Get True Ground State Energy
    exact_solver = NumPyMinimumEigensolver()
    true_min_energy = exact_solver.compute_minimum_eigenvalue(get_maxcut_hamiltonian(graph)).eigenvalue.real

    for beta in beta_values:
        for gamma in gamma_values:
            exp_start_time = time.time()
            logger.info(f"--- Analyzing Beta={beta:.2f}, Gamma={gamma:.2f} ---")
            
            # --- 1. Run Scheduler ---
            cost_model = HeuristicCostModel(gate_error_rate=noise_level, alpha=alpha, beta=beta, gamma=gamma)
            
            logging.getLogger("DyPart").setLevel(logging.WARNING)
            scheduler = DyPartScheduler(cost_model=cost_model)
            partition_plan = scheduler.find_optimal_partition(graph)
            logging.getLogger("DyPart").setLevel(logging.INFO)
            
            chosen_n_sub = partition_plan['optimal_n_sub']
            logger.info(f"Scheduler chose n_sub = {chosen_n_sub}")

            # --- 2. Run VQE with the chosen plan ---
            qpu = NoisyQPU(n_qubits=graph.number_of_nodes(), gate_error_rate=noise_level, readout_error_rate=noise_level * 10)
            optimizer = COBYLA(maxiter=200)
            
            vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer)
            vqe_result = vqe.run(partition_plan)
            
            final_energy = vqe_result['final_energy']
            approximation_ratio = vqe_result['approximation_ratio']
            runtime = time.time() - exp_start_time
            
            logger.info(f"VQE finished with AR = {approximation_ratio:.4f} in {runtime:.2f}s")
            
            # --- 3. Append to CSV ---
            with open(output_csv_path, 'a') as f:
                f.write(f"{beta},{gamma},{chosen_n_sub},{approximation_ratio},{runtime}\n")

    logger.info("="*60)
    logger.info(f"Analysis complete. All results saved to {output_csv_path}")

def plot_in_depth_beta_gamma(results_df: pd.DataFrame):
    """
    Generates a sophisticated two-panel heatmap plot.
    """
    sns.set_theme(style="white")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle("Scheduler Sensitivity to Classical Cost Hyperparameters", fontsize=20, weight='bold')

    # --- Plot 1: Heatmap of Scheduler's Decision (chosen_n_sub) ---
    heatmap_decision = results_df.pivot(index="gamma", columns="beta", values="chosen_n_sub")
    sns.heatmap(heatmap_decision, ax=ax1, annot=True, fmt="d", cmap="viridis_r",
                linewidths=.5, cbar_kws={'label': 'Chosen Partition Size ($n_{sub}^*$)'})
    ax1.set_title("Scheduler's Decision", fontsize=16)
    ax1.set_xlabel("Classical Complexity Exponent (β)", fontsize=12)
    ax1.set_ylabel("Classical Cost Scaling Factor (γ)", fontsize=12)

    # --- Plot 2: Heatmap of Final Performance (final_ar) ---
    heatmap_performance = results_df.pivot(index="gamma", columns="beta", values="final_ar")
    sns.heatmap(heatmap_performance, ax=ax2, annot=True, fmt=".3f", cmap="magma",
                linewidths=.5, cbar_kws={'label': 'Final Approximation Ratio (AR)'})
    ax2.set_title("Resulting VQE Performance", fontsize=16)
    ax2.set_xlabel("Classical Complexity Exponent (β)", fontsize=12)
    ax2.set_ylabel("") # Hide y-label for clarity

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    output_path = "results/Figure_In_Depth_Beta_Gamma_Analysis.png"
    plt.savefig(output_path, dpi=300)
    print(f"\nIn-depth analysis plot saved to: {output_path}")
    plt.show()

if __name__ == "__main__":
    # --- Configuration ---
    # This is a VERY long-running experiment.
    GRAPH_NODES = 10 # Use a 10-node graph as a compromise
    problem_graph = nx.random_regular_graph(d=3, n=GRAPH_NODES, seed=42)
    
    FIXED_NOISE_LEVEL = 5e-3
    FIXED_ALPHA = 0.95
    
    BETA_VALUES = [1.2, 1.5, 2.0]
    GAMMA_VALUES = [0.1, 0.5, 1.0]
    
    OUTPUT_CSV = "results/in_depth_beta_gamma_data.csv"

    # --- Run Analysis ---
    run_in_depth_beta_gamma_analysis(
        graph=problem_graph,
        noise_level=FIXED_NOISE_LEVEL,
        alpha=FIXED_ALPHA,
        beta_values=BETA_VALUES,
        gamma_values=GAMMA_VALUES,
        output_csv_path=OUTPUT_CSV
    )

    # --- Plot Results ---
    try:
        final_data_df = pd.read_csv(OUTPUT_CSV)
        plot_in_depth_beta_gamma(final_data_df)
    except FileNotFoundError:
        logger.error(f"Could not find results file at {OUTPUT_CSV} to plot.")