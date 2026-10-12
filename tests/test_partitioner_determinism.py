# tests/test_partitioner_determinism.py
"""Tests verifying that the graph partitioner is strictly deterministic (ACT-004, ISS-006, TEST-001)."""

import unittest
import networkx as nx
from vqe_framework.utils.graph_partitioner import partition_graph_greedy


class TestPartitionerDeterminism(unittest.TestCase):
    def setUp(self):
        # 10-node 3-regular graph with fixed seed
        self.graph10 = nx.random_regular_graph(3, 10, seed=42)
        # 12-node 3-regular graph with fixed seed
        self.graph12 = nx.random_regular_graph(3, 12, seed=123)

    def test_partition_determinism_100_runs(self):
        """Partitioning the exact same graph into subgraphs must yield identical results across 100 runs."""
        base_subgraphs, base_cuts = partition_graph_greedy(self.graph10, 4)
        base_nodes_list = [sorted(sg.nodes()) for sg in base_subgraphs]

        for run in range(100):
            subgraphs, cuts = partition_graph_greedy(self.graph10, 4)
            nodes_list = [sorted(sg.nodes()) for sg in subgraphs]

            self.assertEqual(cuts, base_cuts, f"Cut count differed on run {run}")
            self.assertEqual(nodes_list, base_nodes_list, f"Partition grouping differed on run {run}")

    def test_partition_conserves_nodes_and_edges(self):
        """Verify that all nodes are partitioned without loss or duplication and edge counts are exact."""
        for n_sub in [2, 3, 4, 5, 6]:
            subgraphs, cuts = partition_graph_greedy(self.graph12, n_sub)

            all_nodes = []
            for sg in subgraphs:
                self.assertLessEqual(len(sg.nodes()), n_sub)
                all_nodes.extend(sg.nodes())

            self.assertEqual(sorted(all_nodes), sorted(self.graph12.nodes()))
            self.assertEqual(len(all_nodes), len(set(all_nodes)))  # No duplicates

            internal_edges = sum(len(sg.edges()) for sg in subgraphs)
            self.assertEqual(cuts + internal_edges, len(self.graph12.edges()))


if __name__ == "__main__":
    unittest.main()
