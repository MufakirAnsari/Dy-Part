# experiments/demonstrate_scheduler.py
# --- VERSION 2: USING THE IMPROVED COST MODEL ---

import networkx as nx
import matplotlib.pyplot as plt
import os
import numpy as np

from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler

def run_demonstration(graph, noise_scenarios, alpha, beta, gamma):
    """
    Runs the scheduler for a given graph under different noise scenarios
    and generates a plot of the results.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(15, 9))
    
    # Use a color palette that is distinct
    colors = plt.cm.get_cmap('viridis', len(noise_scenarios))
    
    for i, (name, gate_error_rate) in enumerate(noise_scenarios.items()):
        cost_model = HeuristicCostModel(
            gate_error_rate=gate_error_rate,
            alpha=alpha,
            beta=beta,
            gamma=gamma
        )
        scheduler = DyPartScheduler(cost_model=cost_model)
        result = scheduler.find_optimal_partition(graph)
        
        # --- PLOTTING LOGIC ---
        n_subs = [res['n_sub'] for res in result['search_results']]
        total_costs = [res['total_cost'] for res in result['search_results']]
        
        # The main line for Total Cost for this scenario
        ax.plot(n_subs, total_costs, 'o-', color=colors(i), label=f'Total Cost ({name})', zorder=5, linewidth=2.5)
        
        optimal_n_sub = result['optimal_n_sub']
        best_cost = result['best_cost']
        ax.plot(optimal_n_sub, best_cost, '*', markersize=20, markeredgecolor='black', color='gold', 
                label=f'Optimal: n_sub={optimal_n_sub} ({name})', zorder=10)

    # --- ADD A SINGLE, GENERAL PLOT OF THE COMPONENTS ---
    # We only need to plot the components once to show their general shape.
    # Let's use the 'NISQ Prototype' data as a representative example.
    cost_model_rep = HeuristicCostModel(noise_scenarios["NISQ Prototype (ε=1e-3)"], alpha, beta, gamma)
    scheduler_rep = DyPartScheduler(cost_model_rep)
    result_rep = scheduler_rep.find_optimal_partition(graph, min_subgraph_size=2) # Rerun to get the data easily
    
    n_subs_rep = [res['n_sub'] for res in result_rep['search_results']]
    q_costs_rep = [res['quantum_cost'] * alpha for res in result_rep['search_results']]
    c_costs_rep = [res['classical_cost'] * (1-alpha) for res in result_rep['search_results']]
    
    # Plot the components in black to distinguish them
    ax.plot(n_subs_rep, q_costs_rep, '--', color='black', alpha=0.7, label='Quantum Cost Component (Shape)')
    ax.plot(n_subs_rep, c_costs_rep, ':', color='black', alpha=0.7, label='Classical Cost Component (Shape)')
    
    # --- Formatting and Final Legend ---
    ax.set_xlabel("Subgraph Size (n_sub)", fontsize=14)
    ax.set_ylabel("Heuristic Cost (Lower is Better)", fontsize=14)
    ax.set_title(f"Dy-Part Scheduler Decision Making for a {graph.number_of_nodes()}-Node Graph\n"
                 f"(alpha={alpha}, beta={beta}, gamma={gamma})", fontsize=16)
    
    # Now the legend will be much clearer
    ax.legend(fontsize=12, loc='upper right')
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_ylim(bottom=0) # Start y-axis at 0
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/day5_scheduler_demonstration_final.png", dpi=300, bbox_inches='tight')
    print("\nFinal, improved plot saved to 'results/day5_scheduler_demonstration_final.png'")
    plt.show()

if __name__ == "__main__":
    problem_graph = nx.random_regular_graph(d=3, n=16, seed=42)

    # Scenarios chosen to better highlight the transition
    noise_scenarios = {
        "Ideal QPU (ε=1e-5)": 1e-5,
        "NISQ Prototype (ε=1e-3)": 1e-3,
        "Noisy Device (ε=8e-3)": 8e-3
    }

    # *** >>> FINAL TUNED HYPERPARAMETERS <<< ***
    # We are now telling the scheduler to prioritize avoiding quantum noise above all else.
    ALPHA = 0.95 # Heavily weight quantum cost (95%)
    BETA = 1.5   # Keep this the same
    GAMMA = 0.1  # Drastically reduce the penalty for classical cuts
    
    run_demonstration(problem_graph, noise_scenarios, alpha=ALPHA, beta=BETA, gamma=GAMMA)