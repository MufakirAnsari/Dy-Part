# vqe_framework/scheduler.py
"""The core scheduler for the Dy-Part framework.

Orchestrates the dynamic qubit partitioning process using discrete ternary search
(O(log |V|)) over the unimodal cost landscape, with exhaustive fallback safeguards
(ACT-010, ACT-011, ISS-001).
"""

import logging
from typing import Any, Dict, List, Optional
import networkx as nx

from .cost_model import HeuristicCostModel
from .logging_config import setup_logging
from .utils.graph_partitioner import partition_graph_greedy

logger = setup_logging()


class DyPartScheduler:
    """The core scheduler for the Dy-Part framework.

    Explores candidate partition sizes for a given problem graph using
    logarithmic ternary search over the heuristic cost model.
    """

    def __init__(self, cost_model: HeuristicCostModel):
        """Initializes the scheduler with a given cost model.

        Args:
            cost_model: Instantiated HeuristicCostModel evaluating quantum infidelity
                        vs classical knitting/communication cost.
        """
        self.cost_model = cost_model

    def _evaluate_n_sub(
        self, graph: nx.Graph, n_sub: int, cache: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluates and caches the heuristic cost for a specific subgraph size."""
        if n_sub in cache:
            return cache[n_sub]

        _, num_cuts = partition_graph_greedy(graph, n_sub)
        cost_dict = self.cost_model.calculate_total_cost(
            graph=graph, n_sub=n_sub, num_cuts=num_cuts
        )
        cache[n_sub] = cost_dict

        logger.debug(
            "  - Evaluated n_sub = %2d: Cuts = %3d, Q_Cost = %.4f, C_Cost = %.4f, Total = %.4f",
            n_sub,
            num_cuts,
            cost_dict["quantum_cost"],
            cost_dict["classical_cost"],
            cost_dict["total_cost"],
        )
        return cost_dict

    def find_optimal_partition(
        self,
        graph: nx.Graph,
        min_subgraph_size: int = 2,
        search_method: str = "ternary",
        fallback_threshold: int = 5,
    ) -> Dict[str, Any]:
        """Finds the optimal subgraph size minimizing the heuristic cost.

        Uses discrete ternary search for O(log |V|) complexity when search_method='ternary'.
        Automatically uses exhaustive search for small graph domains (<= fallback_threshold)
        or when search_method='exhaustive'.

        Args:
            graph: The problem graph to be partitioned.
            min_subgraph_size: The minimum subgraph size to consider (default: 2).
            search_method: 'ternary' (O(log |V|)) or 'exhaustive' (O(|V|)).
            fallback_threshold: Domain width threshold below which exhaustive search
                                is used directly.

        Returns:
            Dictionary containing:
                - optimal_n_sub: Optimal subgraph size minimizing cost
                - best_cost: Minimum heuristic cost value
                - search_method_used: Method used ('ternary' or 'exhaustive')
                - num_evaluations: Number of distinct n_sub evaluated
                - search_results: List of evaluated cost dictionaries
        """
        max_subgraph_size = graph.number_of_nodes()
        if max_subgraph_size < min_subgraph_size:
            logger.warning(
                "Graph size (%d) < min_subgraph_size (%d). No partitioning.",
                max_subgraph_size,
                min_subgraph_size,
            )
            return {
                "optimal_n_sub": max_subgraph_size,
                "best_cost": 0.0,
                "search_method_used": "none",
                "num_evaluations": 1,
                "search_results": [
                    {
                        "total_cost": 0.0,
                        "quantum_cost": 0.0,
                        "classical_cost": 0.0,
                        "n_sub": max_subgraph_size,
                        "num_cuts": 0,
                    }
                ],
            }

        cache: Dict[int, Dict[str, Any]] = {}
        domain_width = max_subgraph_size - min_subgraph_size + 1

        logger.info("--- Dy-Part Scheduler: Starting search for optimal partition ---")
        logger.info("Graph: %d nodes, %d edges.", graph.number_of_nodes(), graph.number_of_edges())
        logger.info(
            "Cost Model: alpha=%.2f, beta=%.2f, gamma=%.2f, error=%.2e",
            self.cost_model.alpha,
            self.cost_model.beta,
            self.cost_model.gamma,
            self.cost_model.gate_error_rate,
        )

        method_used = search_method
        # For small search spaces, exhaustive scan is cheaper and guaranteed exact
        if search_method == "exhaustive" or domain_width <= fallback_threshold:
            method_used = "exhaustive"
            logger.debug("Using exhaustive search over domain [%d, %d]", min_subgraph_size, max_subgraph_size)
            for n in range(min_subgraph_size, max_subgraph_size + 1):
                self._evaluate_n_sub(graph, n, cache)
        else:
            # Discrete ternary search over [min_subgraph_size, max_subgraph_size]
            method_used = "ternary"
            logger.debug("Using ternary search over domain [%d, %d]", min_subgraph_size, max_subgraph_size)
            left = min_subgraph_size
            right = max_subgraph_size

            while (right - left) >= 3:
                third = (right - left) // 3
                m1 = left + third
                m2 = right - third

                c1 = self._evaluate_n_sub(graph, m1, cache)["total_cost"]
                c2 = self._evaluate_n_sub(graph, m2, cache)["total_cost"]

                if c1 <= c2:
                    right = m2 - 1
                else:
                    left = m1 + 1

            # Narrow search complete; evaluate remaining interval [left, right]
            for n in range(left, right + 1):
                self._evaluate_n_sub(graph, n, cache)

        search_results = list(cache.values())
        search_results.sort(key=lambda x: x["n_sub"])

        best_result = min(search_results, key=lambda x: x["total_cost"])
        optimal_n_sub = best_result["n_sub"]

        logger.info("--- Search Complete (%s, %d evaluations) ---", method_used, len(cache))
        logger.info("Optimal Subgraph Size (n_sub): %d", optimal_n_sub)
        logger.info("Minimum Heuristic Cost: %.4f", best_result["total_cost"])

        return {
            "optimal_n_sub": optimal_n_sub,
            "best_cost": best_result["total_cost"],
            "min_cost": best_result["total_cost"],
            "quantum_cost": best_result["quantum_cost"],
            "classical_cost": best_result["classical_cost"],
            "num_cuts": best_result["num_cuts"],
            "search_method_used": method_used,
            "num_evaluations": len(cache),
            "search_results": search_results,
        }