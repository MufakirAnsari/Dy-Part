# tests/test_partitioner.py

import unittest
import networkx as nx
from vqe_framework.utils.graph_partitioner import partition_graph_greedy

class TestGraphPartitioner(unittest.TestCase):
    def setUp(self):
        """Create a simple 6-node graph for testing."""
        self.graph = nx.Graph()
        self.graph.add_edges_from([
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), # A 6-cycle
            (0, 3) # An extra chord
        ])
        # Total edges = 7
        
    def test_partition_into_twos(self):
        """Test partitioning into subgraphs of size 2."""
        subgraphs, num_cuts = partition_graph_greedy(self.graph, 2)
        self.assertEqual(len(subgraphs), 3)
        self.assertTrue(all(len(sg.nodes()) == 2 for sg in subgraphs))
        
        # Check if total nodes are conserved
        total_nodes = set()
        for sg in subgraphs:
            total_nodes.update(sg.nodes())
        self.assertEqual(total_nodes, set(range(6)))
        
        # Check cut calculation
        internal_edges = sum(len(sg.edges()) for sg in subgraphs)
        self.assertEqual(num_cuts, len(self.graph.edges()) - internal_edges)

if __name__ == '__main__':
    unittest.main()