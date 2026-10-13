"""tests/test_baselines_partitioners.py

Unit tests for METIS and Random graph partitioner baselines (ACT-016, ACT-017).
Validates node conservation, cut conservation, size bounds, and deterministic seeding.
"""

import unittest
import networkx as nx
from vqe_framework.utils.metis_partitioner import partition_graph_metis
from vqe_framework.utils.random_partitioner import partition_graph_random


class TestRandomPartitioner(unittest.TestCase):
    """Tests for partition_graph_random (ACT-017)."""

    def setUp(self):
        self.graph = nx.random_regular_graph(d=3, n=12, seed=42)

    def test_node_conservation(self):
        subgraphs, num_cuts = partition_graph_random(self.graph, n_sub=4, seed=123)
        partitioned_nodes = []
        for subg in subgraphs:
            partitioned_nodes.extend(list(subg.nodes()))

        self.assertEqual(sorted(partitioned_nodes), sorted(list(self.graph.nodes())))
        self.assertEqual(len(partitioned_nodes), self.graph.number_of_nodes())

    def test_subgraph_size_bound(self):
        subgraphs, num_cuts = partition_graph_random(self.graph, n_sub=4, seed=123)
        for subg in subgraphs:
            self.assertLessEqual(subg.number_of_nodes(), 4)

    def test_cut_conservation(self):
        subgraphs, num_cuts = partition_graph_random(self.graph, n_sub=4, seed=123)
        internal_edges = sum(subg.number_of_edges() for subg in subgraphs)
        total_edges = self.graph.number_of_edges()
        self.assertEqual(internal_edges + num_cuts, total_edges)

    def test_determinism_with_same_seed(self):
        subgraphs1, cuts1 = partition_graph_random(self.graph, n_sub=3, seed=999)
        subgraphs2, cuts2 = partition_graph_random(self.graph, n_sub=3, seed=999)

        self.assertEqual(cuts1, cuts2)
        nodes1 = [sorted(s.nodes()) for s in subgraphs1]
        nodes2 = [sorted(s.nodes()) for s in subgraphs2]
        self.assertEqual(nodes1, nodes2)

    def test_trivial_full_graph(self):
        subgraphs, num_cuts = partition_graph_random(self.graph, n_sub=20, seed=42)
        self.assertEqual(len(subgraphs), 1)
        self.assertEqual(num_cuts, 0)
        self.assertEqual(subgraphs[0].number_of_nodes(), self.graph.number_of_nodes())


class TestMetisPartitioner(unittest.TestCase):
    """Tests for partition_graph_metis (ACT-016)."""

    def setUp(self):
        self.graph = nx.random_regular_graph(d=3, n=12, seed=42)

    def test_node_conservation(self):
        subgraphs, num_cuts = partition_graph_metis(self.graph, n_sub=4)
        partitioned_nodes = []
        for subg in subgraphs:
            partitioned_nodes.extend(list(subg.nodes()))

        self.assertEqual(sorted(partitioned_nodes), sorted(list(self.graph.nodes())))
        self.assertEqual(len(partitioned_nodes), self.graph.number_of_nodes())

    def test_cut_conservation(self):
        subgraphs, num_cuts = partition_graph_metis(self.graph, n_sub=4)
        internal_edges = sum(subg.number_of_edges() for subg in subgraphs)
        total_edges = self.graph.number_of_edges()
        self.assertEqual(internal_edges + num_cuts, total_edges)

    def test_determinism(self):
        subgraphs1, cuts1 = partition_graph_metis(self.graph, n_sub=3)
        subgraphs2, cuts2 = partition_graph_metis(self.graph, n_sub=3)

        self.assertEqual(cuts1, cuts2)
        nodes1 = [sorted(s.nodes()) for s in subgraphs1]
        nodes2 = [sorted(s.nodes()) for s in subgraphs2]
        self.assertEqual(nodes1, nodes2)

    def test_trivial_full_graph(self):
        subgraphs, num_cuts = partition_graph_metis(self.graph, n_sub=20)
        self.assertEqual(len(subgraphs), 1)
        self.assertEqual(num_cuts, 0)
        self.assertEqual(subgraphs[0].number_of_nodes(), self.graph.number_of_nodes())


if __name__ == "__main__":
    unittest.main()
