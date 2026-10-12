# experiments/analyze_hyperparameters.py
# This script analyzes the sensitivity of the Dy-Part scheduler to the alpha hyperparameter.


import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import logging
import time

# Import all framework components
from vqe_framework.logging_config import setup_logging
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.vqe_executor import PartitionedVQE
from vqe_framework.utils.hamiltonian_constructor import get_maxcut_hamiltonian
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from vqe_framework.qpu_interface import NoisyQPU 

logger = setup_logging()

# In experiments/in_depth_hyperparameter_analysis.py

def run_in_depth_analysis(graph: nx.Graph, noise_level: float, alpha_values: list, beta: float, gamma: float):
    """
    Performs a full analysis by running both the scheduler and the subsequent VQE
    for different alpha values.
    """
    
    all_analysis_results = []
    
    logger.info("="*60)
    logger.info("  Starting In-Depth Hyperparameter Sensitivity Analysis")
    logger.info("="*60)

    # First, get the true ground state energy
    exact_solver = NumPyMinimumEigensolver()
    full_hamiltonian = get_maxcut_hamiltonian(graph)
    true_min_energy = exact_solver.compute_minimum_eigenvalue(full_hamiltonian).eigenvalue.real

    for alpha in alpha_values:
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
        
        # *** USE OUR MAIN, PROVEN EXECUTOR ***
        vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer)
        vqe_result = vqe.run(partition_plan)
        
        final_energy = vqe_result['final_energy']
        approximation_ratio = vqe_result['approximation_ratio']
        
        logger.info(f"VQE with n_sub={chosen_n_sub} finished with AR = {approximation_ratio:.4f}")
        
        # --- 3. Store all relevant data ---
        all_analysis_results.append({
            "alpha": alpha,
            "chosen_n_sub": chosen_n_sub,
            "heuristic_cost": heuristic_cost,
            "final_ar": approximation_ratio,
            "search_results": partition_plan['search_results']
        })

    logger.info("="*60)
    return all_analysis_results

def plot_in_depth_results(results: list, graph_nodes: int, noise_level: float):
    """
    Generates the final, in-depth analysis plot.
    """
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # --- Primary Y-axis (ax1) for Heuristic Cost ---
    ax1.set_xlabel("Subgraph Size (n_sub)", fontsize=14)
    ax1.set_ylabel("Heuristic Cost (Scheduler's Objective)", fontsize=14, color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    colors = plt.cm.get_cmap('plasma', len(results) + 1)
    
    for i, res in enumerate(results):
        alpha = res['alpha']
        search_data = res['search_results']
        n_subs = [d['n_sub'] for d in search_data]
        total_costs = [d['total_cost'] for d in search_data]
        
        ax1.plot(n_subs, total_costs, 'o-', color=colors(i), alpha=0.7, 
                 label=f'Heuristic Cost (α = {alpha:.2f})')
        
        # Highlight the minimum found by the scheduler
        ax1.plot(res['chosen_n_sub'], res['heuristic_cost'], '*', markersize=20, 
                 markeredgecolor='black', color='gold', zorder=10)

    # --- Secondary Y-axis (ax2) for Actual Performance ---
    ax2 = ax1.twinx()
    ax2.set_ylabel("Final Approximation Ratio (Actual Performance)", fontsize=14, color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.axhline(y=1.0, color='red', linestyle=':', label='Ideal Solution (AR=1.0)')

    alphas = [res['alpha'] for res in results]
    final_ars = [res['final_ar'] for res in results]
    
    # Plot the final AR achieved for each alpha's chosen strategy
    # This is a bit tricky to visualize. Let's plot the AR for EACH n_sub choice.
    # We need to run a VQE for every possible n_sub to get the "true" performance curve.
    # This is too computationally expensive for the 20-day sprint.
    
    # A smarter visualization: Plot the final AR vs. Alpha.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    fig.suptitle(f"In-Depth Analysis for {graph_nodes}-Node Graph (Noise ε_gate = {noise_level:.1e})", fontsize=18)
    
    # --- Plot 1: The Scheduler's Decision Landscape ---
    for i, res in enumerate(results):
        search_data = res['search_results']
        n_subs = [d['n_sub'] for d in search_data]
        total_costs = [d['total_cost'] for d in search_data]
        ax1.plot(n_subs, total_costs, 'o-', label=f'Heuristic Cost (α = {res["alpha"]:.2f})')
        ax1.plot(res['chosen_n_sub'], res['heuristic_cost'], '*', markersize=15, markeredgecolor='k', color='gold')
    
    ax1.set_xlabel("Subgraph Size (n_sub)")
    ax1.set_ylabel("Heuristic Cost")
    ax1.set_title("Scheduler's Cost Model Landscape")
    ax1.legend()
    
    # --- Plot 2: The Final Performance Outcome ---
    ax2.plot(alphas, final_ars, 's-', color='crimson', label='Final VQE Performance')
    ax2.set_xlabel("Hyperparameter α")
    ax2.set_ylabel("Final Approximation Ratio")
    ax2.set_title("Actual Performance vs. Scheduler's Strategy (α)")
    ax2.axhline(y=1.0, color='red', linestyle=':', label='Ideal Solution (AR=1.0)')
    ax2.legend()

    # Find and highlight the best performing alpha
    best_idx = np.argmax(final_ars)
    best_alpha = alphas[best_idx]
    best_ar = final_ars[best_idx]
    ax2.plot(best_alpha, best_ar, 'v', markersize=15, color='gold', markeredgecolor='k', label=f'Best Performing α = {best_alpha:.2f}')
    ax2.legend()
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    output_path = "results/Figure_In_Depth_Analysis.png"
    plt.savefig(output_path, dpi=300)
    print(f"\nIn-depth analysis plot saved to: {output_path}")
    plt.show()

if __name__ == "__main__":
    # This is a long-running experiment
    GRAPH_NODES = 10 # Use a medium-sized graph
    problem_graph = nx.random_regular_graph(d=3, n=GRAPH_NODES, seed=42)

    FIXED_NOISE_LEVEL = 5e-3 # 0.5% gate error

    ALPHA_VALUES = [0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
    
    BETA = 1.5
    GAMMA = 0.1

    results = run_in_depth_analysis(
        graph=problem_graph,
        noise_level=FIXED_NOISE_LEVEL,
        alpha_values=ALPHA_VALUES,
        beta=BETA,
        gamma=GAMMA
    )
    
    plot_in_depth_results(results, graph_nodes=GRAPH_NODES, noise_level=FIXED_NOISE_LEVEL)