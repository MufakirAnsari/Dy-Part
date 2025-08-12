# vqe_framework/vqe_executor_blind_deterministic.py

import numpy as np
from qiskit.circuit.library import TwoLocal
from qiskit_algorithms.optimizers import COBYLA

from .qpu_interface import NoisyQPU
from .utils.graph_partitioner import partition_graph_greedy
from .utils.hamiltonian_constructor import get_maxcut_hamiltonian

class PartitionedVQE_Blind_Deterministic:
    def __init__(self, graph, qpu, optimizer, shots=4096):
        self.graph = graph
        self.qpu = qpu
        self.optimizer = optimizer
        self.shots = shots
        self.intermediate_results = {"iters": [], "vals": []}
        self.subgraphs = []

    def _energy_evaluation_function(self, parameters: np.ndarray) -> float:
        # "BLIND" energy function - identical to the one in vqe_executor_blind.py
        param_idx = 0
        circuits_batch, observables_batch, params_batch = [], [], []

        for subg in self.subgraphs:
            if subg.number_of_edges() == 0:
                param_idx += TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2).num_parameters
                continue
            
            subg_ansatz = TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2)
            num_subg_params = subg_ansatz.num_parameters
            subg_params = parameters[param_idx : param_idx + num_subg_params]
            param_idx += num_subg_params
            
            observables_batch.append(get_maxcut_hamiltonian(subg))
            circuits_batch.append(subg_ansatz)
            params_batch.append(subg_params)
        
        total_energy = 0.0
        if circuits_batch:
            estimator = self.qpu.get_estimator(shots=self.shots)
            job_result = estimator.run(circuits_batch, observables_batch, params_batch).result()
            total_energy = np.sum(job_result.values)
        
        eval_count = len(self.intermediate_results["iters"]) + 1
        self.intermediate_results["iters"].append(eval_count)
        self.intermediate_results["vals"].append(total_energy)
        if eval_count % 5 == 0:
            print(f"  Blind Executor Iteration {eval_count}: Internal Energy = {total_energy:.4f}")
        
        return total_energy

    def run(self, partition_plan):
        n_sub = partition_plan['optimal_n_sub']
        self.subgraphs, _ = partition_graph_greedy(self.graph, n_sub)
        
        total_params = sum(TwoLocal(sg.number_of_nodes(), "ry", "cz", reps=2).num_parameters for sg in self.subgraphs)
        initial_point = np.random.default_rng(42).random(total_params)
        self.intermediate_results = {"iters": [], "vals": []}
        
        opt_result = self.optimizer.minimize(fun=self._energy_evaluation_function, x0=initial_point)
        
        return {"final_energy": opt_result.fun, "convergence_data": self.intermediate_results}