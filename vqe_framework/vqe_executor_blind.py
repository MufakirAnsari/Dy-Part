# vqe_framework/vqe_executor_blind.py
import numpy as np
import networkx as nx
from typing import Dict, Any

from qiskit.circuit.library import TwoLocal
from qiskit_algorithms.optimizers import SPSA
from qiskit.quantum_info import SparsePauliOp

from .qpu_interface import NoisyQPU
from .utils.graph_partitioner import partition_graph_greedy
from .utils.hamiltonian_constructor import get_maxcut_hamiltonian


class PartitionedVQE_Blind:
    def __init__(self, graph, qpu, optimizer):
        self.graph = graph
        self.qpu = qpu
        self.optimizer = optimizer
        self.intermediate_results = {"iters": [], "vals": []}

    def _energy_evaluation_function(self, parameters: np.ndarray) -> float:
        """
        This is the "BLIND" energy function. It only sums the expectation
        values of the subgraph Hamiltonians, ignoring the cut edges.
        """
        param_idx = 0
        
        circuits_batch = []
        observables_batch = []
        params_batch = []

        for subg in self.subgraphs:
            # This check is still necessary to avoid the QiskitError
            if subg.number_of_edges() == 0:
                ansatz = TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2)
                param_idx += ansatz.num_parameters
                continue
            
            num_subg_nodes = subg.number_of_nodes()
            subg_ansatz = TwoLocal(num_subg_nodes, "ry", "cz", reps=2, entanglement="linear")
            
            num_subg_params = subg_ansatz.num_parameters
            subg_params = parameters[param_idx : param_idx + num_subg_params]
            param_idx += num_subg_params
            
            subg_hamiltonian = get_maxcut_hamiltonian(subg)
            
            circuits_batch.append(subg_ansatz)
            observables_batch.append(subg_hamiltonian)
            params_batch.append(subg_params)
        
        total_energy = 0.0
        if circuits_batch:
            estimator = self.qpu.get_estimator()
            job_result = estimator.run(
                circuits=circuits_batch,
                observables=observables_batch,
                parameter_values=params_batch
            ).result()
            total_energy = np.sum(job_result.values)
        
        # Callback logic...
        eval_count = len(self.intermediate_results["iters"]) + 1
        self.intermediate_results["iters"].append(eval_count)
        self.intermediate_results["vals"].append(total_energy)
        # (No logging here for simplicity, but you could add it)
        
        return total_energy

    def run(self, partition_plan):
        n_sub = partition_plan['optimal_n_sub']
        self.subgraphs, self.num_cuts = partition_graph_greedy(self.graph, n_sub)
        
        total_params = 0
        for subg in self.subgraphs:
            ansatz = TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2)
            total_params += ansatz.num_parameters
        
        initial_point = np.random.default_rng(42).random(total_params)
        self.intermediate_results = {"iters": [], "vals": []}
        
        opt_result = self.optimizer.minimize(fun=self._energy_evaluation_function, x0=initial_point)
        
        return {
            "final_energy": opt_result.fun,
            "convergence_data": self.intermediate_results,
        }