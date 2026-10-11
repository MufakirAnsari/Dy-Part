# vqe_framework/scheduler.py

import networkx as nx
from typing import Dict, Any
import logging

# NEW: Import our centralized logging setup
from .logging_config import setup_logging
# Import the components we built on Day 3 and Day 4
from .cost_model import HeuristicCostModel
from .utils.graph_partitioner import partition_graph_greedy

# NEW: Instantiate the logger for this module
logger = setup_logging()

class DyPartScheduler:
    """
    The core scheduler for the Dy-Part framework.
    
    This class orchestrates the partitioning process. It explores various
    partitioning strategies for a given problem graph and uses a heuristic
    cost model to select the optimal strategy based on the hardware's
    noise characteristics.
    """
    def __init__(self, cost_model: HeuristicCostModel):
        """
        Initializes the scheduler.
        
        Args:
            cost_model: An instantiated HeuristicCostModel that will be used
                        to evaluate the cost of each potential partition.
        """
        self.cost_model = cost_model

    def find_optimal_partition(self, graph: nx.Graph, min_subgraph_size: int = 2) -> Dict[str, Any]:
        """
        Finds the optimal subgraph size for partitioning a given graph.
        
        This is the main decision-making function. It iterates through all
        sensible subgraph sizes, from min_subgraph_size up to the full graph size.
        For each size, it partitions the graph, calculates the heuristic cost,
        and identifies the partition size that minimizes this cost.
        
        Args:
            graph: The problem graph to be partitioned.
            min_subgraph_size: The smallest subgraph size to consider.
        
        Returns:
            A dictionary containing the results of the search, including the
            optimal subgraph size and the detailed cost breakdown for each
            evaluated option.
        """
        max_subgraph_size = graph.number_of_nodes()
        if max_subgraph_size < min_subgraph_size:
            logger.warning(f"Graph size ({max_subgraph_size}) is smaller than min_subgraph_size ({min_subgraph_size}). Not partitioning.")
            return {
                "optimal_n_sub": max_subgraph_size,
                "best_cost": 0.0,
                "search_results": [{
                    "total_cost": 0.0, "quantum_cost": 0.0, "classical_cost": 0.0,
                    "n_sub": max_subgraph_size, "num_cuts": 0
                }]
            }

        search_results = []
        
        # NEW: Replaced print statements with logger.info for high-level messages
        logger.info("--- Dy-Part Scheduler: Starting search for optimal partition ---")
        logger.info(f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")
        logger.info(f"Cost Model Params: alpha={self.cost_model.alpha}, beta={self.cost_model.beta}, "
                    f"gamma={self.cost_model.gamma}, gate_error={self.cost_model.gate_error_rate}")
        
        for n_sub in range(min_subgraph_size, max_subgraph_size + 1):
            # 1. Propose a partition using our greedy strategy
            _, num_cuts = partition_graph_greedy(graph, n_sub)
            
            # 2. Evaluate the cost of this partition strategy
            cost_dict = self.cost_model.calculate_total_cost(
                graph=graph,
                n_sub=n_sub,
                num_cuts=num_cuts
            )
            
            search_results.append(cost_dict)
            
            # NEW: Replaced iterative print with logger.debug for detailed progress.
            # This will only be shown if the logging level is set to DEBUG.
            logger.debug(f"  - Evaluated n_sub = {n_sub:2d}: "
                         f"Cuts = {num_cuts:3d}, "
                         f"Q_Cost = {cost_dict['quantum_cost']:.4f}, "
                         f"C_Cost = {cost_dict['classical_cost']:.4f}, "
                         f"Total Cost = {cost_dict['total_cost']:.4f}")

        # 3. Find the best result from the search
        if not search_results:
            logger.error("Scheduler search completed with no results.")
            raise RuntimeError("Scheduler search completed with no results.")
            
        best_result = min(search_results, key=lambda x: x['total_cost'])
        optimal_n_sub = best_result['n_sub']

        # NEW: Replaced print statements with logger.info for final results
        logger.info("--- Search Complete. Optimal partition size found. ---")
        logger.info(f"Optimal Subgraph Size (n_sub): {optimal_n_sub}")
        logger.info(f"Minimum Heuristic Cost: {best_result['total_cost']:.4f}")
        
        return {
            "optimal_n_sub": optimal_n_sub,
            "best_cost": best_result['total_cost'],
            "search_results": search_results
        }