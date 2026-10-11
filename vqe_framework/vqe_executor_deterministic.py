# vqe_framework/vqe_executor_deterministic.py
# A new executor for the "cleaner result" experiment.

import numpy as np
import networkx as nx
from typing import Dict, Any

from qiskit.circuit.library import TwoLocal
from qiskit_algorithms.optimizers import COBYLA
from qiskit.quantum_info import SparsePauliOp

from .qpu_interface import NoisyQPU
from .utils.graph_partitioner import partition_graph_greedy
from .utils.hamiltonian_constructor import get_maxcut_hamiltonian

class PartitionedVQE_Deterministic:
    """
    An executor specifically for the verification experiment.
    It uses the "cut-aware" energy function but is configured to accept a deterministic
    optimizer like COBYLA and a specific number of shots for the Estimator.
    """
    def __init__(self, graph: nx.Graph, qpu: NoisyQPU, optimizer: COBYLA, shots: int = 4096):
        self.graph = graph
        self.qpu = qpu
        self.optimizer = optimizer
        self.shots = shots
        self.intermediate_results = {"iters": [], "vals": []}
        self.subgraphs = []
        self.cut_edges = []
        self.num_cuts = 0

    def _energy_evaluation_function(self, parameters: np.ndarray) -> float:
        # This logic is identical to our best "cut-aware" executor
        param_idx = 0
        circuits_batch, observables_batch, params_batch, node_maps = [], [], [], []

        for subg in self.subgraphs:
            num_subg_nodes = subg.number_of_nodes()
            node_maps.append({local_idx: global_idx for local_idx, global_idx in enumerate(subg.nodes())})
            subg_ansatz = TwoLocal(num_subg_nodes, "ry", "cz", reps=2, entanglement="linear")
            num_subg_params = subg_ansatz.num_parameters
            subg_params = parameters[param_idx : param_idx + num_subg_params]
            param_idx += num_subg_params

            if subg.number_of_edges() > 0:
                observables_batch.append(get_maxcut_hamiltonian(subg))
                circuits_batch.append(subg_ansatz)
                params_batch.append(subg_params)

            for local_idx in range(num_subg_nodes):
                pauli_op_str = ['I'] * num_subg_nodes
                pauli_op_str[local_idx] = 'Z'
                observables_batch.append(SparsePauliOp("".join(pauli_op_str)))
                circuits_batch.append(subg_ansatz)
                params_batch.append(subg_params)
        
        if not circuits_batch: return 0.0

        # Here we pass the shots to the estimator
        estimator = self.qpu.get_estimator(shots=self.shots) 
        all_exp_vals = estimator.run(circuits_batch, observables_batch, params_batch).result().values
        
        result_idx, internal_energy = 0, 0.0
        single_z_exp_vals = {}

        for i, subg in enumerate(self.subgraphs):
            if subg.number_of_edges() > 0:
                internal_energy += all_exp_vals[result_idx]
                result_idx += 1
            for local_idx in range(subg.number_of_nodes()):
                global_idx = node_maps[i][local_idx]
                single_z_exp_vals[global_idx] = all_exp_vals[result_idx]
                result_idx += 1
        
        cut_energy = sum(single_z_exp_vals[u] * single_z_exp_vals[v] for u, v in self.cut_edges)
        total_energy = internal_energy + cut_energy
        
        eval_count = len(self.intermediate_results["iters"]) + 1
        self.intermediate_results["iters"].append(eval_count)
        self.intermediate_results["vals"].append(total_energy)
        if eval_count % 5 == 0:
            print(f"  Executor Iteration {eval_count}: Current Energy = {total_energy:.4f}")
        
        return total_energy

    def run(self, partition_plan: Dict[str, Any]) -> Dict[str, Any]:
        n_sub = partition_plan['optimal_n_sub']
        self.subgraphs, self.num_cuts = partition_graph_greedy(self.graph, n_sub)
        
        original_edges = set(self.graph.edges())
        internal_edges = set().union(*(subg.edges() for subg in self.subgraphs))
        self.cut_edges = list(original_edges - internal_edges)
        
        total_params = sum(TwoLocal(sg.number_of_nodes(), "ry", "cz", reps=2).num_parameters for sg in self.subgraphs)
        
        initial_point = np.random.default_rng(42).random(total_params)
        self.intermediate_results = {"iters": [], "vals": []}
        
        opt_result = self.optimizer.minimize(fun=self._energy_evaluation_function, x0=initial_point)
        
        return {"final_energy": opt_result.fun, "convergence_data": self.intermediate_results}