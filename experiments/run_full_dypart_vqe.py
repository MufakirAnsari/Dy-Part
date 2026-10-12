# experiments/run_full_dypart_vqe.py

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import os
import time

# Import all our framework components
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.vqe_executor import PartitionedVQE
from vqe_framework.utils.hamiltonian_constructor import get_graph_solution_value, get_maxcut_hamiltonian
from qiskit_algorithms.optimizers import SPSA

def analyze_and_reconstruct_solution(result: dict, full_graph: nx.Graph) -> str:
    """
    Takes the result from the PartitionedVQE and reconstructs the full solution bitstring.
    """
    optimal_params = result['optimal_parameters']
    subgraphs = result['subgraphs']
    
    full_solution_map = {}
    param_idx = 0
    
    # This is a placeholder for sampling. A full implementation would sample each
    # subgraph's final circuit. For now, we will assume the VQE result gives us
    # a good classical representation. This is a simplification for the 20-day sprint.
    # Let's focus on the energy value, which is the key metric.
    
    # A simple placeholder for now.
    # In a full run, we would build each sub-circuit, run a Sampler, find the most
    # likely bitstring for each, and stitch them together.
    # Let's defer this complex part to focus on the energy convergence.
    print("\nNote: Full bitstring reconstruction is a complex task deferred for future work.")
    print("We will focus on the final energy as the primary metric of success.")
    return "NotImplemented"

if __name__ == '__main__':
    start_time = time.time()
    
    # --- 1. Define the Problem and Hardware ---
    print("--- MILESTONE 1: End-to-End Dy-Part VQE Run ---")
    problem_graph = nx.random_regular_graph(d=3, n=8, seed=42)
    
    # Let's choose a moderately noisy QPU
    GATE_ERROR_RATE = 1e-3
    READOUT_ERROR_RATE = 1e-2
    
    # --- 2. Run the Dy-Part Scheduler ---
    # The scheduler makes the decision BEFORE the VQE run.
    cost_model = HeuristicCostModel(gate_error_rate=GATE_ERROR_RATE, alpha=0.95, beta=1.5, gamma=0.1)
    scheduler = DyPartScheduler(cost_model=cost_model)
    partition_plan = scheduler.find_optimal_partition(problem_graph)
    
    # --- 3. Execute the VQE based on the Scheduler's Plan ---
    qpu = NoisyQPU(
        n_qubits=problem_graph.number_of_nodes(), # Max qubits needed
        gate_error_rate=GATE_ERROR_RATE,
        readout_error_rate=READOUT_ERROR_RATE
    )
    
    optimizer = SPSA(maxiter=50) # Use fewer iterations for a quicker test run
    
    partitioned_vqe = PartitionedVQE(graph=problem_graph, qpu=qpu, optimizer=optimizer)
    result = partitioned_vqe.run(partition_plan)
    
    # --- 4. Analyze and Report Results ---
    final_energy = result['final_energy']
    expected_cut = result.get('expected_cut', 0.0)
    max_cut = result.get('max_cut', 1)
    approximation_ratio = result['approximation_ratio']
    true_min_energy = -float(max_cut)
    
    print("\n--- FINAL RESULTS ---")
    print(f"Problem Graph: {problem_graph.number_of_nodes()} nodes, {problem_graph.number_of_edges()} edges")
    print(f"Scheduler's Optimal Partition Size: {partition_plan['optimal_n_sub']}")
    print(f"MaxCut Ground Truth (Exact): {max_cut}")
    print(f"Expected Cut Achieved: {expected_cut:.2f}")
    print(f"Dy-Part VQE Final Energy: {final_energy:.4f}")
    print(f"Bounded Approximation Ratio: {approximation_ratio:.4f}")
    
    end_time = time.time()
    print(f"\nTotal End-to-End Runtime: {end_time - start_time:.2f} seconds.")

    # --- 5. Plot Convergence ---
    plt.figure(figsize=(12, 7))
    conv_data = result['convergence_data']
    plt.plot(conv_data['iters'], conv_data['vals'], 'o-', label=f"Dy-Part VQE (n_sub={partition_plan['optimal_n_sub']})")
    plt.axhline(y=true_min_energy, color='red', linestyle='--', label='True Ground State Energy')
    plt.xlabel("Optimizer Iteration")
    plt.ylabel("Total Energy")
    plt.title(f"End-to-End VQE Convergence for 8-Node Graph (Noise: {GATE_ERROR_RATE:.1e})")
    plt.legend()
    plt.grid(True)
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/day7_full_run_convergence.png", dpi=300)
    print("\nConvergence plot saved to 'results/day7_full_run_convergence.png'")
    plt.show()