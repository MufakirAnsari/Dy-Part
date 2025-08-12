# vqe_framework/cost_model.py
# --- VERSION 2: IMPROVED AND MORE SENSITIVE ---

import networkx as nx
import numpy as np

class HeuristicCostModel:
    def __init__(self, gate_error_rate: float, alpha: float = 0.5, beta: float = 2.0, gamma: float = 1.0):
        """
        Initializes the cost model.
        
        Args:
            gate_error_rate: The 2-qubit gate error rate.
            alpha: Balances quantum vs. classical costs.
            beta: Exponent for classical complexity based on cuts.
            gamma: *** NEW: A scaling factor to amplify the classical cost. ***
                   Higher gamma makes the model more averse to partitioning.
        """
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0.0 and 1.0")
        if beta < 1.0:
            raise ValueError("beta must be >= 1.0")
        
        self.gate_error_rate = gate_error_rate
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma # New hyperparameter

    def _estimate_num_two_qubit_gates(self, n_sub: int, reps: int = 2) -> int:
        """
        *** IMPROVED HEURISTIC ***
        A more realistic heuristic for the number of two-qubit gates.
        For a TwoLocal ansatz with linear entanglement, each rep has (n_sub - 1) CZ gates.
        """
        if n_sub <= 1:
            return 0
        return reps * (n_sub - 1)

    def _calculate_quantum_cost(self, n_sub: int) -> float:
        """
        Calculates quantum cost (infidelity).
        Cost = 1 - Fidelity = 1 - (1 - error_rate)^num_noisy_gates
        """
        num_noisy_gates = self._estimate_num_two_qubit_gates(n_sub)
        if num_noisy_gates == 0:
            return 0.0
        
        fidelity = (1.0 - self.gate_error_rate)**num_noisy_gates
        return 1.0 - fidelity

    def _calculate_classical_cost(self, graph: nx.Graph, num_cuts: int) -> float:
        """
        Calculates classical cost.
        *** NOW INCLUDES GAMMA SCALING ***
        Cost = gamma * (num_cuts / total_edges)^beta
        """
        total_edges = graph.number_of_edges()
        if total_edges == 0 or num_cuts == 0:
            return 0.0
        
        normalized_cuts = num_cuts / total_edges
        
        # Apply the polynomial model and the new scaling factor
        return self.gamma * (normalized_cuts**self.beta)

    def calculate_total_cost(self, graph: nx.Graph, n_sub: int, num_cuts: int) -> dict:
        """Calculates the total heuristic cost for a partitioning scheme."""
        quantum_cost = self._calculate_quantum_cost(n_sub)
        classical_cost = self._calculate_classical_cost(graph, num_cuts)
        
        total_cost = (self.alpha * quantum_cost) + ((1 - self.alpha) * classical_cost)
        
        return {
            "total_cost": total_cost,
            "quantum_cost": quantum_cost,
            "classical_cost": classical_cost,
            "n_sub": n_sub,
            "num_cuts": num_cuts
        }