# vqe_framework/vqe_executor.py
"""Partitioned VQE executor with cut-aware energy reconstruction and bounded AR calculation.

Executes subgraphs independently on noisy QPU, reconstructs global MaxCut energy using
internal ZZ measurements and classical cut-edge product approximations, and computes
exact-bounded Approximation Ratio (ACT-009, ISS-003, ISS-009).
"""

from typing import Any, Dict, List, Optional
import networkx as nx
import numpy as np
import qiskit.circuit.library
if not hasattr(qiskit.circuit.library, "evolved_operator_ansatz"):
    if hasattr(qiskit.circuit.library, "EvolvedOperatorAnsatz"):
        setattr(qiskit.circuit.library, "evolved_operator_ansatz", qiskit.circuit.library.EvolvedOperatorAnsatz)

from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp

try:
    from qiskit_algorithms.optimizers import Optimizer
except (ImportError, AttributeError):
    Optimizer = Any  # type: ignore

from .logging_config import setup_logging
from .qpu_interface import NoisyQPU
from .utils.graph_partitioner import partition_graph_greedy
from .utils.hamiltonian_constructor import (
    calculate_approximation_ratio,
    get_exact_maxcut,
    get_maxcut_hamiltonian,
)

logger = setup_logging()


class PartitionedVQE:
    """Unified partitioned VQE executor for MaxCut across subgraphs (ACT-021, ISS-037).

    Supports:
    - Cut-aware energy reconstruction (reconstruct_cuts=True)
    - Blind energy evaluation (reconstruct_cuts=False)
    - Configurable estimator shots (shots=8192)
    - Multiple graph partitioners ('greedy', 'metis', 'random')
    - Deterministic random seed handling
    """

    def __init__(
        self,
        graph: nx.Graph,
        qpu: NoisyQPU,
        optimizer: Optimizer,
        seed: Optional[int] = None,
        shots: int = 8192,
        reconstruct_cuts: bool = True,
    ):
        self.graph = graph
        self.qpu = qpu
        self.optimizer = optimizer
        self.seed = seed
        self.shots = shots
        self.reconstruct_cuts = reconstruct_cuts
        self.intermediate_results: Dict[str, List] = {"iters": [], "vals": []}
        self.subgraphs: List[nx.Graph] = []
        self.cut_edges: List = []
        self.num_cuts: int = 0

    def _energy_evaluation_function(self, parameters: np.ndarray) -> float:
        param_idx = 0
        circuits_batch = []
        observables_batch = []
        params_batch = []
        node_maps = []

        for subg in self.subgraphs:
            num_subg_nodes = subg.number_of_nodes()
            subg_nodes = sorted(subg.nodes())
            node_maps.append({local_idx: global_idx for local_idx, global_idx in enumerate(subg_nodes)})

            subg_ansatz = TwoLocal(num_subg_nodes, "ry", "cz", reps=2, entanglement="linear")
            num_subg_params = subg_ansatz.num_parameters
            subg_params = parameters[param_idx : param_idx + num_subg_params]
            param_idx += num_subg_params

            if subg.number_of_edges() > 0:
                # Raw ZZ Hamiltonian for internal subgraph edges
                subg_hamiltonian = get_maxcut_hamiltonian(subg, standard_convention=False)
                circuits_batch.append(subg_ansatz)
                observables_batch.append(subg_hamiltonian)
                params_batch.append(subg_params)

            # Single Z measurements for product-state cut-edge reconstruction (if enabled)
            if self.reconstruct_cuts:
                for local_idx in range(num_subg_nodes):
                    pauli_op_str = ["I"] * num_subg_nodes
                    pauli_op_str[local_idx] = "Z"
                    z_observable = SparsePauliOp("".join(pauli_op_str))

                    circuits_batch.append(subg_ansatz)
                    observables_batch.append(z_observable)
                    params_batch.append(subg_params)

        if not circuits_batch:
            return 0.0

        estimator = self.qpu.get_estimator(shots=self.shots)
        job_result = estimator.run(
            circuits=circuits_batch,
            observables=observables_batch,
            parameter_values=params_batch,
        ).result()

        all_exp_vals = job_result.values
        result_idx = 0

        internal_energy = 0.0
        single_z_exp_vals = {}

        for i, subg in enumerate(self.subgraphs):
            if subg.number_of_edges() > 0:
                internal_energy += all_exp_vals[result_idx]
                result_idx += 1

            if self.reconstruct_cuts:
                for local_idx in range(subg.number_of_nodes()):
                    global_idx = node_maps[i][local_idx]
                    single_z_exp_vals[global_idx] = all_exp_vals[result_idx]
                    result_idx += 1

        cut_energy = 0.0
        if self.reconstruct_cuts:
            for u, v in self.cut_edges:
                cut_energy += single_z_exp_vals[u] * single_z_exp_vals[v]

        total_energy = float(internal_energy + cut_energy)

        eval_count = len(self.intermediate_results["iters"]) + 1
        self.intermediate_results["iters"].append(eval_count)
        self.intermediate_results["vals"].append(total_energy)
        if eval_count % 10 == 0:
            logger.info("  Executor Iteration %d: Current Energy = %.4f", eval_count, total_energy)

        return total_energy

    def run(self, partition_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Runs partitioned VQE using the optimal subgraph size from the partition plan."""
        partition_method = partition_plan.get("partition_method", "greedy")

        if "subgraphs" in partition_plan and "num_cuts" in partition_plan:
            self.subgraphs = partition_plan["subgraphs"]
            self.num_cuts = partition_plan["num_cuts"]
            n_sub = partition_plan.get("optimal_n_sub", max(s.number_of_nodes() for s in self.subgraphs) if self.subgraphs else 1)
        else:
            n_sub = partition_plan["optimal_n_sub"]
            if partition_method == "metis":
                from vqe_framework.utils.metis_partitioner import partition_graph_metis
                self.subgraphs, self.num_cuts = partition_graph_metis(self.graph, n_sub)
            elif partition_method == "random":
                from vqe_framework.utils.random_partitioner import partition_graph_random
                self.subgraphs, self.num_cuts = partition_graph_random(self.graph, n_sub, seed=self.seed)
            else:
                self.subgraphs, self.num_cuts = partition_graph_greedy(self.graph, n_sub)

        logger.info("--- VQE Executor: Starting run with method=%s, n_sub=%d ---", partition_method, n_sub)

        # Canonical edge sets to prevent tuple orientation bugs
        original_edges = {tuple(sorted(e)) for e in self.graph.edges()}
        internal_edges = {tuple(sorted(e)) for subg in self.subgraphs for e in subg.edges()}
        self.cut_edges = sorted(list(original_edges - internal_edges))

        logger.info(
            "Graph partitioned into %d subgraphs with %d cuts.",
            len(self.subgraphs),
            self.num_cuts,
        )

        total_params = 0
        for subg in self.subgraphs:
            ansatz = TwoLocal(subg.number_of_nodes(), "ry", "cz", reps=2)
            total_params += ansatz.num_parameters

        logger.info("Total variational parameters for all subgraphs: %d", total_params)

        rng = np.random.default_rng(self.seed)
        initial_point = rng.random(total_params)

        self.intermediate_results = {"iters": [], "vals": []}

        opt_result = self.optimizer.minimize(fun=self._energy_evaluation_function, x0=initial_point)
        final_energy = float(opt_result.fun)

        # Compute true expected cut and bounded Approximation Ratio
        total_edges = self.graph.number_of_edges()
        expected_cut = max(0.0, (total_edges - final_energy) / 2.0)
        max_cut = get_exact_maxcut(self.graph)
        ar = calculate_approximation_ratio(expected_cut, max_cut)

        logger.info("--- VQE Executor: Run complete ---")
        logger.info(
            "Final Energy: %.4f | Expected Cut: %.2f / %d | AR: %.4f",
            final_energy,
            expected_cut,
            max_cut,
            ar,
        )

        return {
            "final_energy": final_energy,
            "expected_cut": expected_cut,
            "max_cut": max_cut,
            "approximation_ratio": ar,
            "convergence_data": self.intermediate_results,
        }


class PartitionedVQE_Blind(PartitionedVQE):
    """Backwards-compatibility wrapper for blind partitioned VQE (ISS-037, ACT-021).

    Ignores inter-subgraph cut edges in energy evaluation.
    """

    def __init__(
        self,
        graph: nx.Graph,
        qpu: NoisyQPU,
        optimizer: Optimizer,
        seed: Optional[int] = 42,
        shots: int = 8192,
    ):
        super().__init__(
            graph=graph,
            qpu=qpu,
            optimizer=optimizer,
            seed=seed,
            shots=shots,
            reconstruct_cuts=False,
        )


class PartitionedVQE_Deterministic(PartitionedVQE):
    """Backwards-compatibility wrapper for deterministic partitioned VQE (ISS-037, ACT-021).

    Uses cut-aware energy reconstruction with deterministic seed and configurable shots.
    """

    def __init__(
        self,
        graph: nx.Graph,
        qpu: NoisyQPU,
        optimizer: Optimizer,
        shots: int = 4096,
        seed: Optional[int] = 42,
    ):
        super().__init__(
            graph=graph,
            qpu=qpu,
            optimizer=optimizer,
            seed=seed,
            shots=shots,
            reconstruct_cuts=True,
        )


class PartitionedVQE_Blind_Deterministic(PartitionedVQE):
    """Backwards-compatibility wrapper for deterministic blind partitioned VQE (ISS-037, ACT-021).

    Ignores inter-subgraph cut edges with deterministic seed and configurable shots.
    """

    def __init__(
        self,
        graph: nx.Graph,
        qpu: NoisyQPU,
        optimizer: Optimizer,
        shots: int = 4096,
        seed: Optional[int] = 42,
    ):
        super().__init__(
            graph=graph,
            qpu=qpu,
            optimizer=optimizer,
            seed=seed,
            shots=shots,
            reconstruct_cuts=False,
        )


__all__ = [
    "PartitionedVQE",
    "PartitionedVQE_Blind",
    "PartitionedVQE_Deterministic",
    "PartitionedVQE_Blind_Deterministic",
]