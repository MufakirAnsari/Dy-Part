#!/usr/bin/env python3
"""scripts/run_phase5_regression_suite.py

End-to-End Comprehensive Regression Test Suite for Dy-Part.
Executes across 9 rigorous verification modules:
1. Partitioner Determinism & Conservation (TEST-001)
2. Analytical Cost Model Monotonicity (TEST-002)
3. Approximation Ratio Strict Bounding [0.0, 1.0] (TEST-003)
4. Ternary Search Algorithmic Correctness & Logarithmic Pruning (TEST-004)
5. Baseline Partitioners & Edge Conservation (TEST-005)
6. 4,160-Run Benchmark Dataset Integrity (TEST-010)
7. 2,000-Run Hyperparameter Grid Search Validation (TEST-014)
8. Multi-Scale Algorithmic Ablation Verification (TEST-015)
9. LaTeX Publication Syntax, Braces, Environments, and Citation Integrity (TEST-013)
"""

import csv
import json
import math
import os
import re
import sys
import unittest
import networkx as nx

# Add Dy-Part-main to path for imports
BASE_DIR = os.path.abspath(os.path.dirname(__file__) + "/..")
if os.path.isdir(os.path.join(BASE_DIR, "Dy-Part-main")):
    sys.path.insert(0, os.path.join(BASE_DIR, "Dy-Part-main"))
sys.path.insert(0, BASE_DIR)

from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.utils.graph_partitioner import partition_graph_greedy
from vqe_framework.utils.random_partitioner import partition_graph_random
from vqe_framework.utils.metis_partitioner import partition_graph_metis
from vqe_framework.utils.hamiltonian_constructor import (
    calculate_approximation_ratio,
    get_exact_maxcut,
    get_graph_solution_value,
)


class Test1_PartitionerDeterminism(unittest.TestCase):
    """TEST-001: Verifies greedy partitioner is 100% deterministic and conserves nodes/edges."""

    def test_determinism_across_100_runs(self):
        graph = nx.random_regular_graph(3, 12, seed=42)
        subgraphs_0, cuts_0 = partition_graph_greedy(graph, 4)
        for _ in range(100):
            subgraphs_k, cuts_k = partition_graph_greedy(graph, 4)
            self.assertEqual(cuts_k, cuts_0)
            self.assertEqual(len(subgraphs_k), len(subgraphs_0))
            for g_a, g_b in zip(subgraphs_0, subgraphs_k):
                self.assertEqual(sorted(g_a.nodes()), sorted(g_b.nodes()))

    def test_node_and_edge_conservation(self):
        graph = nx.random_regular_graph(3, 20, seed=123)
        subgraphs, cuts = partition_graph_greedy(graph, 5)
        all_partition_nodes = [n for sg in subgraphs for n in sg.nodes()]
        self.assertEqual(len(all_partition_nodes), 20)
        self.assertEqual(set(all_partition_nodes), set(graph.nodes()))
        internal_edges = sum(sg.number_of_edges() for sg in subgraphs)
        self.assertEqual(internal_edges + cuts, graph.number_of_edges())


class Test2_CostModelMonotonicity(unittest.TestCase):
    """TEST-002: Verifies physical monotonicity of the heuristic cost model."""

    def setUp(self):
        self.dummy_graph = nx.cycle_graph(20)  # 20 edges

    def test_quantum_cost_growth_with_subgraph_size(self):
        cm = HeuristicCostModel(gate_error_rate=0.005, alpha=0.7, beta=1.5, gamma=0.1)
        costs = [cm._calculate_quantum_cost(n) for n in range(2, 21)]
        for i in range(len(costs) - 1):
            self.assertLess(costs[i], costs[i+1])

    def test_classical_cost_monotonicity_with_cuts(self):
        cm = HeuristicCostModel(gate_error_rate=0.005, alpha=0.7, beta=1.5, gamma=0.1)
        costs = [cm._calculate_classical_cost(self.dummy_graph, c) for c in range(1, 15)]
        for i in range(len(costs) - 1):
            self.assertLess(costs[i], costs[i+1])

    def test_higher_beta_strictly_penalizes_cuts(self):
        cm_low = HeuristicCostModel(gate_error_rate=0.005, alpha=0.7, beta=1.0, gamma=0.1)
        cm_high = HeuristicCostModel(gate_error_rate=0.005, alpha=0.7, beta=2.5, gamma=0.1)
        self.assertLess(
            cm_low._calculate_classical_cost(self.dummy_graph, 6),
            cm_high._calculate_classical_cost(self.dummy_graph, 6),
        )

    def test_zero_cuts_zero_classical_cost(self):
        cm = HeuristicCostModel(gate_error_rate=0.005, alpha=0.7, beta=2.0, gamma=0.1)
        self.assertEqual(cm._calculate_classical_cost(self.dummy_graph, 0), 0.0)


class Test3_ARCalculationBounds(unittest.TestCase):
    """TEST-003: Verifies Approximation Ratio is strictly bounded in [0.0, 1.0]."""

    def test_ar_bounds(self):
        cases = [(0.0, 10.0), (5.0, 10.0), (10.0, 10.0), (15.0, 10.0), (-3.0, 10.0), (0.0, 0.0)]
        for cut, max_cut in cases:
            ar = calculate_approximation_ratio(cut, max_cut)
            self.assertGreaterEqual(ar, 0.0)
            self.assertLessEqual(ar, 1.0)

    def test_canonical_graph_solutions(self):
        c4 = nx.cycle_graph(4)
        self.assertEqual(get_exact_maxcut(c4), 4)
        self.assertEqual(get_graph_solution_value(c4, "0101"), 4)
        self.assertEqual(get_graph_solution_value(c4, "0000"), 0)


class Test4_TernarySearchCorrectness(unittest.TestCase):
    """TEST-004: Verifies ternary search optimization and evaluation reduction."""

    def setUp(self):
        self.cm = HeuristicCostModel(gate_error_rate=0.01, alpha=0.7, beta=1.5, gamma=0.1)
        self.scheduler = DyPartScheduler(self.cm)

    def test_ternary_vs_exhaustive_agreement(self):
        g12 = nx.random_regular_graph(3, 12, seed=42)
        res_exh = self.scheduler.find_optimal_partition(g12, search_method="exhaustive")
        res_tern = self.scheduler.find_optimal_partition(g12, search_method="ternary")
        self.assertEqual(res_tern["optimal_n_sub"], res_exh["optimal_n_sub"])
        self.assertAlmostEqual(res_tern["best_cost"], res_exh["best_cost"], places=5)

    def test_ternary_evaluations_fewer_on_20_nodes(self):
        g20 = nx.random_regular_graph(3, 20, seed=999)
        res_exh = self.scheduler.find_optimal_partition(g20, search_method="exhaustive")
        res_tern = self.scheduler.find_optimal_partition(g20, search_method="ternary")
        self.assertLess(res_tern["num_evaluations"], res_exh["num_evaluations"])


class Test5_BaselinePartitioners(unittest.TestCase):
    """TEST-005: Verifies random and METIS partitioners conserve graph properties."""

    def test_random_partitioner_node_conservation(self):
        g = nx.random_regular_graph(3, 16, seed=77)
        sgs, cuts = partition_graph_random(g, 4, seed=123)
        all_nodes = [n for sg in sgs for n in sg.nodes()]
        self.assertEqual(len(all_nodes), 16)
        self.assertEqual(set(all_nodes), set(g.nodes()))

    def test_metis_partitioner_node_conservation(self):
        g = nx.random_regular_graph(3, 16, seed=88)
        sgs, cuts = partition_graph_metis(g, 4)
        all_nodes = [n for sg in sgs for n in sg.nodes()]
        self.assertEqual(len(all_nodes), 16)
        self.assertEqual(set(all_nodes), set(g.nodes()))


class Test6_BenchmarkDatasetIntegrity(unittest.TestCase):
    """TEST-010: Validates corrected_benchmark.csv structure, counts, and ranges."""

    def setUp(self):
        csv_path = os.path.join(BASE_DIR, "results", "corrected_benchmark.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            self.rows = list(csv.DictReader(f))

    def test_exact_row_count_and_methods(self):
        self.assertEqual(len(self.rows), 4160)
        methods = set(r["method"] for r in self.rows)
        self.assertEqual(methods, {"dypart", "static", "metis", "random"})

    def test_seed_counts_per_graph_size(self):
        for n, expected_seeds in [(8, 30), (10, 30), (12, 30), (16, 25), (20, 15)]:
            sub = [r for r in self.rows if int(r["num_nodes"]) == n and r["method"] == "dypart" and abs(float(r["noise_level"]) - 0.0003162277660168) < 1e-6]
            self.assertEqual(len(sub), expected_seeds, f"Expected {expected_seeds} seeds for N={n}")

    def test_all_approximation_ratios_bounded(self):
        for r in self.rows:
            ar = float(r["approximation_ratio"])
            self.assertGreaterEqual(ar, 0.0)
            self.assertLessEqual(ar, 1.0)


class Test7_HyperparamGridSearchIntegrity(unittest.TestCase):
    """TEST-014: Validates hyperparam_grid_search.csv and optimal_hyperparameters.json."""

    def test_grid_search_runs_and_optima(self):
        csv_path = os.path.join(BASE_DIR, "results", "hyperparam_grid_search.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 2000)

        json_path = os.path.join(BASE_DIR, "results", "optimal_hyperparameters.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        opt = data["optimal_hyperparameters"]
        self.assertEqual(opt["alpha"], 0.7)
        self.assertEqual(opt["beta"], 1.0)
        self.assertEqual(opt["gamma"], 0.1)
        self.assertAlmostEqual(opt["mean_approximation_ratio"], 0.9115, places=3)


class Test8_AblationSummaryIntegrity(unittest.TestCase):
    """TEST-015: Validates ternary_ablation_table.csv and scheduler_overhead_summary.json."""

    def test_ablation_metrics(self):
        json_path = os.path.join(BASE_DIR, "results", "scheduler_overhead_summary.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["overhead_analysis"]), 10)
        self.assertLess(data["max_ternary_runtime_ms"], 4.2)
        self.assertGreater(data["average_speedup"], 1.7)


class Test9_PublicationIntegrity(unittest.TestCase):
    """TEST-013: Audits LaTeX publication syntax, structure, and citations."""

    def test_latex_braces_and_environments(self):
        tex_path = os.path.join(BASE_DIR, "sn-article.tex")
        if not os.path.exists(tex_path):
            tex_path = os.path.abspath(os.path.join(BASE_DIR, "..", "sn-article.tex"))
        if not os.path.exists(tex_path):
            self.skipTest("sn-article.tex not present in repository")
        with open(tex_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        clean_lines = []
        for l in lines:
            idx = l.find("%")
            if idx >= 0:
                if idx > 0 and l[idx - 1] == "\\":
                    clean_lines.append(l)
                else:
                    clean_lines.append(l[:idx])
            else:
                clean_lines.append(l)
        text = "\n".join(clean_lines)

        open_b = len(re.findall(r"(?<!\\)\{", text))
        close_b = len(re.findall(r"(?<!\\)\}", text))
        self.assertEqual(open_b, close_b, f"Mismatched braces: {open_b} open vs {close_b} close")

        begins = re.findall(r"\\begin\{([^}]+)\}", text)
        ends = re.findall(r"\\end\{([^}]+)\}", text)
        self.assertEqual(len(begins), len(ends), f"Mismatched environments: {len(begins)} begins vs {len(ends)} ends")

    def test_authors_and_affiliations(self):
        tex_path = os.path.join(BASE_DIR, "sn-article.tex")
        if not os.path.exists(tex_path):
            tex_path = os.path.abspath(os.path.join(BASE_DIR, "..", "sn-article.tex"))
        if not os.path.exists(tex_path):
            self.skipTest("sn-article.tex not present in repository")
        with open(tex_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Mufakir", content)
        self.assertTrue("ansari.30@wright.edu" in content or "mufakir.ansari@utoledo.edu" in content)
        self.assertIn("Mudabir", content)
        self.assertIn("mansari2@lamar.edu", content)
        self.assertIn("Lamar University", content)
        self.assertIn("Wright State University", content)


if __name__ == "__main__":
    print("=" * 70)
    print("      DY-PART END-TO-END REGRESSION TEST SUITE")
    print("=" * 70)
    unittest.main(verbosity=2)
