# vqe_framework/vqe_executor.py
# --- VERSION 4: ADDED SEED FOR REPRODUCIBILITY (FINAL VERSION) ---

import numpy as np
import networkx as nx
from typing import Dict, Any

from qiskit.circuit.library import TwoLocal
# The optimizer type hint can be more general
from qiskit_algorithms.optimizers.optimizer import Optimizer
from qiskit.quantum_info import SparsePauliOp

# Now importing logging_config
from .logging_config import setup_logging
from .qpu_interface import NoisyQPU
from .utils.graph_partitioner import partition_graph_greedy
from .utils.hamiltonian_constructor import get_maxcut_hamiltonian

# Instantiate logger
logger = setup_logging()

class PartitionedVQE:
    # *** CHANGE 1: Add 'seed=None' to the __init__ signature ***
    def __init__(self, graph: nx.Graph, qpu: NoisyQPU, optimizer: Optimizer, seed=None):
        self.graph = graph
        self.qpu = qpu
        self.optimizer = optimizer
        self.intermediate_results = {"iters": [], "vals": []}
        # *** CHANGE 2: Store the seed ***
        self.seed = seed
        # Initialize these attributes to avoid potential errors
        self.subgraphs = []
        self.cut_edges = []
        self.num_cuts = 0

    def _energy_evaluation_function(self, parameters: np.ndarray) -> float:
        param_idx = 0
        
        circuits_batch = []
        observables_batch = []
        params_batch = []
        node_maps = []

        for subg in self.subgraphs:
            num_subg_nodes = subg.number_of_nodes()
            subg_nodes = list(subg.nodes())
            node_maps.append({local_idx: global_idx for local_idx, global_idx in enumerate(subg_nodes)})
            
            subg_ansatz = TwoLocal(num_subg_nodes, "ry", "cz", reps=2, entanglement="linear")
            
            num_subg_params = subg_ansatz.num_parameters
            subg_params = parameters[param_idx : param_idx + num_subg_params]
            param_idx += num_subg_params

            if subg.number_of_edges() > 0:
                subg_hamiltonian = get_maxcut_hamiltonian(subg)
                circuits_batch.append(subg_ansatz)
                observables_batch.append(subg_hamiltonian)
                params_batch.append(subg_params)

            for local_idx in range(num_subg_nodes):
                pauli_op_str = ['I'] * num_subg_nodes
                pauli_op_str[local_idx] = 'Z'
                z_observable = SparsePauliOp("".join(pauli_op_str))
                
                circuits_batch.append(subg_ansatz)
                observables_batch.append(z_observable)
                params_batch.append(subg_params)
        
        if not circuits_batch:
            return 0.0

        estimator = self.qpu.get_estimator(shots=8192) # Keep high shots for accuracy
        job_result = estimator.run(
            circuits=circuits_batch,
            observables=observables_batch,
            parameter_values=params_batch
        ).result()
        
        all_exp_vals = job_result.values
        result_idx = 0
        
        internal_energy = 0.0
        single_z_exp_vals = {}

        for i, subg in enumerate(self.subgraphs):
            if subg.number_of_edges() > 0:
                internal_energy += all_exp_vals[result_idx]
                result_idx += 1
            
            for local_idx in range(subg.number_of_nodes()):
                global_idx = node_maps[i][local_idx]
                single_z_exp_vals[global_idx] = all_exp_vals[result_idx]
                result_idx += 1
        
        cut_energy = 0.0
        for u, v in self.cut_edges:
            cut_energy += single_z_exp_vals[u] * single_z_exp_vals[v]
            
        total_energy = internal_energy + cut_energy
        
        eval_count = len(self.intermediate_results["iters"]) + 1
        self.intermediate_results["iters"].append(eval_count)
        self.intermediate_results["vals"].append(total_energy)
        if eval_count % 10 == 0:
            logger.info(f"  Executor Iteration {eval_count}: Current Energy = {total_energy:.4f}")
        
        return total_energy

    def run(self, partition_plan: Dict[str, Any]) -> Dict[str, Any]:
        n_sub = partition_plan['optimal_n_sub']
        logger.info(f"--- VQE Executor: Starting run with partition size n_sub = {n_sub} ---")
        
        self.subgraphs, self.num_cuts = partition_graph_greedy(self.graph, n_sub)
        
        original_edges = set(self.graph.edges())
        internal_edges = set().union(*(subg.edges() for subg in self.subgraphs))
        self.cut_edges = list(original_edges - internal_edges)
        
        logger.info(f"Graph partitioned into {len(self.subgraphs)} subgraphs with {self.num_cuts} cuts.")

        total_params = 0
        for subg in self.subgraphs:
            ansatz = TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2)
            total_params += ansatz.num_parameters
        
        logger.info(f"Total variational parameters for all subgraphs: {total_params}")
        
        # *** CHANGE 3: Use the stored seed to create a reproducible initial point ***
        rng = np.random.default_rng(self.seed)
        initial_point = rng.random(total_params)
        
        self.intermediate_results = {"iters": [], "vals": []}
        
        opt_result = self.optimizer.minimize(fun=self._energy_evaluation_function, x0=initial_point)
        
        final_energy = opt_result.fun
        
        logger.info(f"--- VQE Executor: Run complete ---")
        logger.info(f"Final minimized energy (Internal + Cut): {final_energy:.4f}")
        
        return {
            "final_energy": final_energy,
            "convergence_data": self.intermediate_results
        }