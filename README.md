# Dy-Part: A Dynamic, Noise-Aware Scheduler for Optimizing Hybrid Quantum-Classical Algorithms

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 1.0+](https://img.shields.io/badge/Qiskit-1.0%2B-613394.svg)](https://qiskit.org/)
[![Regression Suite](https://img.shields.io/badge/regression%20tests-19%2F19%20passing-success.svg)](scripts/run_phase5_regression_suite.py)
[![Unit Tests](https://img.shields.io/badge/unit%20tests-21%2F21%20passing-success.svg)](tests/)
[![HPC Validated](https://img.shields.io/badge/HPC-OSC%20Ascend%20(AMD%20EPYC%207763)-orange.svg)](slurm/)
[![Empirical Validation](https://img.shields.io/badge/Cost%20Model%20R%5E2-0.8227-brightgreen.svg)](results/Figure_Cost_Model_Empirical_Validation.png)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](README.md)

**Dy-Part** is an automated, noise-aware graph partitioning framework for distributed Variational Quantum Eigensolver (VQE) architectures targeting combinatorial optimization problems—such as Max-Cut—on Noisy Intermediate-Scale Quantum (NISQ) devices.

Conventional quantum workload partitioning strategies rely on static, topology-only graph decomposition that remains completely indifferent to physical device calibration. Under low noise, static partitioners over-fragment graphs and accumulate unnecessary classical recombination penalties; under moderate-to-high noise, unpartitioned or under-partitioned circuits collapse toward the maximally mixed state due to multi-qubit depolarizing decoherence.

**Dy-Part solves this fundamental trade-off.** By formulating workload decomposition as a pre-execution optimization problem, Dy-Part analytically balances **quantum circuit infidelity** against **classical recombination penalties**. It identifies the optimal subgraph size $n_{\text{sub}}^*$ using a discrete $O(\log |V| \cdot (|V| + |E|))$ ternary search scheduler with partition memoization, executing in sub-4.2 millisecond latency.

---

## Table of Contents

- [1. Mainframe Findings & Empirical Plots](#1-mainframe-findings--empirical-plots)
  - [1.1 Multi-Scale Benchmark Performance (4,160 Runs)](#11-multi-scale-benchmark-performance-4160-runs)
  - [1.2 Empirical Cost Model Validation ($R^2 = 0.8227$)](#12-empirical-cost-model-validation-r2--08227)
  - [1.3 Static Oracle Comparison & Pareto Frontier](#13-static-oracle-comparison--pareto-frontier)
  - [1.4 Autonomous Scheduler Decision Dynamics](#14-autonomous-scheduler-decision-dynamics)
  - [1.5 Algorithmic Ternary Search Ablation](#15-algorithmic-ternary-search-ablation)
- [2. System Architecture](#2-system-architecture)
- [3. Mathematical & Algorithmic Formulation](#3-mathematical--algorithmic-formulation)
  - [3.1 Joint Heuristic Cost Model](#31-joint-heuristic-cost-model)
  - [3.2 Discrete Ternary Search Algorithm](#32-discrete-ternary-search-algorithm)
  - [3.3 Cut-Aware Partitioned VQE Execution](#33-cut-aware-partitioned-vqe-execution)
  - [3.4 Standard Max-Cut Hamiltonian & Bounded AR](#34-standard-max-cut-hamiltonian--bounded-ar)
- [4. Quantitative Benchmark Summary](#4-quantitative-benchmark-summary)
  - [4.1 Multi-Factor ANOVA & Wilcoxon Significance](#41-multi-factor-anova--wilcoxon-significance)
  - [4.2 Scalability & Evaluation Reduction Table](#42-scalability--evaluation-reduction-table)
- [5. Repository Structure](#5-repository-structure)
- [6. Installation & Environment Setup](#6-installation--environment-setup)
  - [6.1 Local Workstation (Conda / Pip)](#61-local-workstation-conda--pip)
  - [6.2 Supercomputing Environment (Ohio Supercomputer Center)](#62-supercomputing-environment-ohio-supercomputer-center)
- [7. Quick Start & Python API Tutorial](#7-quick-start--python-api-tutorial)
- [8. HPC SLURM Automation Pipeline](#8-hpc-slurm-automation-pipeline)
- [9. Verification & Automated Test Suites](#9-verification--automated-test-suites)
  - [9.1 End-to-End Regression Test Suite (19 Tests)](#91-end-to-end-regression-test-suite-19-tests)
  - [9.2 Unit Test Suite (21 Tests)](#92-unit-test-suite-21-tests)
- [10. Citation, License & Acknowledgments](#10-citation-license--acknowledgments)

---

## 1. Mainframe Findings & Empirical Plots

### 1.1 Multi-Scale Benchmark Performance (4,160 Runs)

Dy-Part was evaluated across a massive **4,160-run experimental campaign** on 3-regular graphs across 5 scales ($|V| \in \{8, 10, 12, 16, 20\}$) and 8 logarithmically spaced two-qubit gate error rates ($\epsilon_{\text{gate}} \in [3.16 \times 10^{-4}, 3.16 \times 10^{-2}]$) with proportional readout noise ($\epsilon_{\text{readout}} = 10 \cdot \epsilon_{\text{gate}}$), benchmarked head-to-head against Static ($n_{\text{sub}}=4$), METIS multilevel graph partitioner, and Random baselines.

<p align="center">
  <img src="results/Figure_Performance_Comparison_Averaged.png" alt="Multi-Scale Performance Comparison" width="95%"/>
</p>

> **Figure 1:** Multi-scale Max-Cut Approximation Ratio ($\text{AR} \in [0.0, 1.0]$) across gate noise rates. Shaded bands represent $\pm 1\sigma$ standard deviations across independent topology and parameter seeds. Dy-Part achieves statistically superior performance over all baselines in moderate-to-high noise regimes, preventing the catastrophic fidelity collapse observed in fixed-topology algorithms.

- **Overall Mean AR:** Dy-Part ($0.8489$) > METIS ($0.8448$) > Static ($0.8434$) > Random ($0.8398$).
- **Statistical Significance:** Paired Wilcoxon signed-rank tests confirm statistically significant advantages for Dy-Part in **15 of 40** configurations against Static ($p < 0.05$), **15 of 40** against METIS ($p < 0.05$), and **19 of 40** against Random ($p < 0.05$).
- **Scale Advantage:** On 16-node graphs at $\epsilon_{\text{gate}} = 4.39 \times 10^{-3}$, Dy-Part delivers $+3.71\%$ higher AR over Static ($p = 1.62 \times 10^{-4}$, Cohen's $d = 0.76$). On 20-node graphs at $\epsilon_{\text{gate}} = 2.28 \times 10^{-3}$, Dy-Part achieves $+4.90\%$ higher AR over Random ($p = 6.10 \times 10^{-5}$, Cohen's $d = 1.30$, and up to $d = 1.75$ in severe noise).

---

### 1.2 Empirical Cost Model Validation ($R^2 = 0.8227$)

To demonstrate that our theoretical formulation directly reflects physical quantum execution, the heuristic cost function was validated across 1,040 benchmark runs and 2,000 hyperparameter grid-search executions:

<p align="center">
  <img src="results/Figure_Cost_Model_Empirical_Validation.png" alt="Empirical Cost Model Validation" width="95%"/>
</p>

> **Figure 2:** Four-panel empirical validation of the Dy-Part heuristic cost model. (a) Total heuristic cost versus empirical Approximation Ratio ($R^2 = 0.8227$, Pearson $r = -0.9071$, Spearman $\rho = -0.8150$, $p < 10^{-12}$). (b) Quantum cost versus VQE wall-clock runtime ($r = 0.9163$, $R^2 = 0.8396$). (c) Classical knitting penalty versus physical cut edges ($\rho = 0.9486$). (d) Empirical AR versus physical cut count ($r = -0.5877$).

The results confirm that the theoretical cost objective explains **$82.3\%$ of the variance** in empirical Max-Cut solution quality across all graph dimensions ($N=8: r=-0.9514; N=10: r=-0.9068; N=12: r=-0.9227; N=16: r=-0.9163; N=20: r=-0.9104$).

---

### 1.3 Static Oracle Comparison & Pareto Frontier

We compared Dy-Part against an exhaustive **Static Oracle** on 10-node graphs, constructed by executing VQE across every allowable static partition size ($n_{\text{sub}} \in \{2, 3, \dots, 10\}$) at each noise level:

<p align="center">
  <img src="results/Figure_Oracle_Comparison_Detailed_10_nodes.png" alt="Static Oracle Comparison" width="90%"/>
</p>

> **Figure 3:** (Top) Mean approximation ratio comparison including the Static Oracle Pareto frontier. (Bottom) Optimality gap relative to the oracle ($\text{AR}_{\text{Oracle}} - \text{AR}$). Dy-Part closely tracks the empirical upper bound across all noise rates, maintaining an optimality gap below $0.03$.

---

### 1.4 Autonomous Scheduler Decision Dynamics

Figure 4 illustrates the mean optimal partition size ($n_{\text{sub}}^*$) selected by Dy-Part as hardware noise increases:

<p align="center">
  <img src="results/Figure_Scheduler_Decisions_Averaged.png" alt="Scheduler Partition Size Decisions" width="85%"/>
</p>

> **Figure 4:** Optimal partition size ($n_{\text{sub}}^*$) chosen by the scheduler as a function of 2-qubit gate error rate. At low noise ($\epsilon_{\text{gate}} \le 10^{-3}$), the scheduler selects larger partitions ($n_{\text{sub}} = 4\text{--}6$) to minimize boundary cuts. As noise increases beyond $2 \times 10^{-3}$, Dy-Part automatically downscales subgraphs to $n_{\text{sub}} = 2\text{--}3$, shielding the quantum state from multi-gate depolarizing decoherence.

---

### 1.5 Algorithmic Ternary Search Ablation

We conducted a head-to-head runtime and query complexity ablation comparing our $O(\log |V| \cdot (|V| + |E|))$ ternary search scheduler against an exhaustive linear scan across graphs from 6 to 30 nodes:

<p align="center">
  <img src="results/Figure_Ternary_Search_Ablation.png" alt="Ternary Search Ablation" width="90%"/>
</p>

> **Figure 5:** Algorithmic ablation comparing ternary search against exhaustive linear scan across 10 problem dimensions ($|V| \in [6, 30]$). (Top) Number of partition cost evaluations; ternary search achieves up to a $65.52\%$ reduction at 30 nodes. (Bottom) Scheduling execution latency; ternary search delivers a $1.77\times$ speedup while keeping total scheduling latency strictly under $4.16\text{ ms}$ (mean $1.74\text{ ms}$).

---

## 2. System Architecture

```
                       Input Graph G = (V, E)
                   + Hardware Noise Calibration (ε_gate, ε_readout)
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │   DyPartScheduler     │  ◄── Memoization Cache 𝒞
                      │  O(log |V|) Trisection│
                      └───────────┬───────────┘
                                  │ Evaluates Candidate Partition Costs
                                  ▼
                      ┌───────────────────────┐
                      │  HeuristicCostModel   │
                      │  α·C_quant + (1-α)·C_c│  ◄── Validated R² = 0.8227
                      └───────────┬───────────┘
                                  │ Optimal Partition Plan n_sub*
                                  ▼
                      ┌───────────────────────┐
                      │ GraphPartitioner      │
                      │ (Deterministic Greedy)│  ◄── O(|V| + |E|) BFS Queue
                      └───────────┬───────────┘
                                  │ Subgraphs {G_k} + Inter-Subgraph Cuts E_cut
                                  ▼
                      ┌───────────────────────┐
                      │   PartitionedVQE      │
                      │  (Cut-Aware Executor) │  ◄── Parallel/Decoupled QPU Execution
                      └───────────┬───────────┘
                                  │ Internal ZZ + Product Boundary Recombination
                                  ▼
                Global Reconstructed Energy & Bounded AR ∈ [0.0, 1.0]
```

The Dy-Part pipeline operates through four modular phases:
1. **Device Calibration Ingestion:** Receives physical hardware noise metrics ($\epsilon_{\text{gate}}$, $\epsilon_{\text{readout}}$) from QPU backend calibration data.
2. **Pre-Execution Scheduling:** Employs ternary search over allowable partition sizes $n_{\text{sub}} \in [2, |V|]$ using the heuristic cost objective.
3. **Deterministic Partitioning:** Decomposes the problem graph into localized subgraphs while tracking severed boundary edges.
4. **Cut-Aware VQE Execution:** Maps subgraphs to independent quantum registers, computes expectation values, and reconstructs the global cut energy via product marginals.

---

## 3. Mathematical & Algorithmic Formulation

### 3.1 Joint Heuristic Cost Model

For an input graph $G = (V, E)$ and candidate partition size $n_{\text{sub}}$, the total objective $C(n_{\text{sub}})$ balances expected quantum infidelity against classical reconstruction penalty:

$$C(n_{\text{sub}}) = \alpha \cdot C_{\text{quantum}}(n_{\text{sub}}, \epsilon_{\text{gate}}) + (1 - \alpha) \cdot C_{\text{classical}}(|E_{\text{cut}}|)$$

where $\alpha \in [0, 1]$ is the fidelity priority weight (empirically optimized at $\alpha^* = 0.70$ via grid search; default $\alpha = 0.95$).

#### Quantum Infidelity Formulation:
Assuming a hardware-efficient `TwoLocal` ansatz with linear CZ entanglement ($2 \cdot n_{\text{sub}}$ entangling gates per subgraph), the probability of at least one two-qubit gate error across the partition is:

$$C_{\text{quantum}}(n_{\text{sub}}, \epsilon_{\text{gate}}) = 1 - (1 - \epsilon_{\text{gate}})^{2 n_{\text{sub}}}$$

#### Classical Recombination Penalty:
Severed boundary edges $E_{\text{cut}}$ must be reconstructed classically via product-state marginals $\langle Z_u Z_v \rangle \approx \langle Z_u \rangle \langle Z_v \rangle$, discarding quantum entanglement across partitions. The penalty scales superlinearly with cut fraction:

$$C_{\text{classical}}(|E_{\text{cut}}|) = \gamma \cdot \left(\frac{|E_{\text{cut}}|}{|E|}\right)^{1 / \beta}$$

where $\gamma = 0.1$ is a scaling prefactor, and $\beta = 1.5$ is the superlinear cut penalty exponent.

---

### 3.2 Discrete Ternary Search Algorithm

Rather than exhaustive $O(|V|)$ scans, Dy-Part exploits the unimodal characteristics of $C(n_{\text{sub}})$ via a discrete ternary search algorithm:

```
Algorithm 1: Discrete Ternary Search for Optimal Partition Size
Input : Graph G = (V, E), Noise-Aware Cost Model C(·), Search Domain [low, high]
Output: Optimal subgraph size n_sub*

1: Initialize memoization cache 𝒞 ← ∅
2: while (high - low) >= 3 do
3:     m1 ← low + floor((high - low) / 3)
4:     m2 ← high - floor((high - low) / 3)
5:     cost1 ← EvaluateCost(m1, G, C, 𝒞)
6:     cost2 ← EvaluateCost(m2, G, C, 𝒞)
7:     if cost1 < cost2 then
8:         high ← m2 - 1
9:     else
10:        low ← m1 + 1
11: return argmin_{n ∈ [low, high]} EvaluateCost(n, G, C, 𝒞)
```

**Complexity Analysis:** In each round, the search interval contracts by approximately $33\%$, requiring $\lceil \log_{3/2}(|V|) \rceil = O(\log |V|)$ trisection rounds. Each evaluation runs the greedy BFS graph partitioner in $O(|V| + |E|)$ time. With memoization, each distinct candidate is evaluated at most once, establishing total worst-case scheduling complexity as:

$$\mathcal{T}_{\text{schedule}} = O(\log |V| \cdot (|V| + |E|))$$

---

### 3.3 Cut-Aware Partitioned VQE Execution

Each subgraph $G_k$ executes on a dedicated quantum register of size $n_k \le n_{\text{sub}}$ using a `TwoLocal(reps=2, rotation="ry", entanglement="cz")` ansatz. Global expectation values are reconstructed by decomposing edge terms:
1. **Internal Subgraph Edges:** Measured directly via joint $Z_u Z_v$ Pauli observables on the localized quantum register.
2. **Boundary Cut Edges $(u, v) \in E_{\text{cut}}$:** Reconstructed via single-qubit expectation values using product-state approximation:
   $$\langle Z_u Z_v \rangle \approx \langle Z_u \rangle \cdot \langle Z_v \rangle$$

Total reconstructed energy:
$$E_{\text{total}}(\vec{\theta}) = \sum_{k} \langle H_{G_k} \rangle_{\vec{\theta}_k} + \sum_{(u, v) \in E_{\text{cut}}} \frac{\langle Z_u \rangle \langle Z_v \rangle - 1}{2}$$

---

### 3.4 Standard Max-Cut Hamiltonian & Bounded AR

Dy-Part adopts the standard Max-Cut cost Hamiltonian:

$$H_{\text{cost}} = \sum_{(u, v) \in E} \frac{Z_u Z_v - I}{2} = \frac{1}{2} \sum_{(u, v) \in E} Z_u Z_v - \frac{|E|}{2} I$$

The exact ground-state energy $E_{\text{exact}}$ is computed via exact diagonalization (`NumPyMinimumEigensolver`). The **Approximation Ratio (AR)** is strictly bounded in $[0.0, 1.0]$:

$$\text{AR} = \min\left(1.0, \frac{|E_{\text{VQE}}|}{|E_{\text{exact}}|}\right) \in [0.0, 1.0]$$

Across all 4,160 experimental runs in our benchmark dataset, the maximum observed AR is strictly **0.9936**, with **0 instances** exceeding 1.0.

---

## 4. Quantitative Benchmark Summary

### 4.1 Multi-Factor ANOVA & Wilcoxon Significance

- **Multi-Factor ANOVA:** Controlling for graph dimension and noise regime confirms a statistically significant main effect of partitioning method on approximation ratio:
  $$F(3, 4117) = 12.37, \quad p = 4.88 \times 10^{-8}$$
- **Randomized Complete Block Design:** Blocking across graph instances confirms robust superiority:
  $$F(3, 3117) = 14.35, \quad p = 2.45 \times 10^{-9}$$
- **Paired Wilcoxon Signed-Rank Tests Across 40 Noise-Scale Configurations:**
  - Dy-Part vs. Static ($n_{\text{sub}}=4$): Statistically significant in **15 of 40** configurations ($p < 0.05$).
  - Dy-Part vs. METIS: Statistically significant in **15 of 40** configurations ($p < 0.05$).
  - Dy-Part vs. Random: Statistically significant in **19 of 40** configurations ($p < 0.05$).

### 4.2 Scalability & Evaluation Reduction Table

Head-to-head ablation between ternary search and exhaustive scan across 10 graph dimensions:

| Graph Scale (N) | Exhaustive Evals | Ternary Evals | Reduction (%) | Exhaustive Time (ms) | Ternary Time (ms) | Speedup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 6 | 5 | 5 | 0.00% | 0.98 | 0.97 | 1.01× |
| 8 | 7 | 5 | 28.57% | 1.34 | 1.03 | 1.30× |
| 10 | 9 | 5 | 44.44% | 1.83 | 1.15 | 1.59× |
| 12 | 11 | 6 | 45.45% | 2.37 | 1.48 | 1.60× |
| 14 | 13 | 7 | 46.15% | 3.01 | 1.72 | 1.75× |
| 16 | 15 | 7 | 53.33% | 3.75 | 1.95 | 1.92× |
| 18 | 17 | 8 | 52.94% | 4.62 | 2.31 | 2.00× |
| 20 | 19 | 8 | 57.89% | 5.58 | 2.62 | 2.13× |
| 25 | 24 | 9 | 62.50% | 8.35 | 3.40 | 2.46× |
| 30 | 29 | 10 | **65.52%** | 11.82 | **4.16** | **2.84×** |

---

## 5. Repository Structure

```
Dy-Part/
├── vqe_framework/                     # Core Framework Package
│   ├── __init__.py                   # Package exports & Qiskit 1.0+ compatibility
│   ├── cost_model.py                 # HeuristicCostModel with validated monotonic beta
│   ├── scheduler.py                  # DyPartScheduler with O(log |V|) ternary search & cache
│   ├── qpu_interface.py              # NoisyQPU with Aer Estimator, gate depolarizing & readout noise
│   ├── vqe_executor.py               # PartitionedVQE cut-aware energy & bounded AR executor
│   ├── logging_config.py             # Dual console + rotating file logging with Slurm Job ID
│   └── utils/
│       ├── graph_partitioner.py      # Deterministic greedy BFS graph partitioner
│       ├── metis_partitioner.py      # Industry-standard METIS multilevel partitioner wrapper
│       ├── random_partitioner.py     # Uniform random assignment baseline partitioner
│       └── hamiltonian_constructor.py# Standard Max-Cut Hamiltonian & exact brute-force AR
├── experiments/                      # Benchmark & Analysis Scripts
│   ├── run_final_benchmark.py        # Multi-seed baseline reproduction benchmark
│   ├── run_hyperparam_search.py      # Multi-dimensional grid search over (α, β, γ)
│   ├── run_corrected_benchmark.py    # Multi-scale 4,160-run benchmark (8, 10, 12, 16, 20 nodes)
│   ├── generate_final_plots.py       # Publication-ready vector figures with error bands
│   └── plot_runtime_breakdown.py     # Execution time vs scheduler overhead breakdown
├── slurm/                            # HPC Batch Job Scripts (Ohio Supercomputer Center)
│   ├── env_setup.sh                  # Conda environment bootstrap & package installation
│   ├── run_baseline.sh               # Phase 1: Baseline reproduction runner
│   ├── run_hyperparam.sh             # Phase 2a: Slurm job array for hyperparameter sweep (2,000 runs)
│   ├── run_benchmark.sh              # Phase 2b: Slurm job array for multi-scale benchmark (4,160 runs)
│   ├── run_ablation.sh               # Phase 3: Ablation study runner (ternary vs exhaustive)
│   └── submit_all.sh                 # Dependency-chained pipeline orchestrator
├── scripts/                          # Automated Auditing & QA Test Runners
│   ├── run_phase5_regression_suite.py# Comprehensive 19-test end-to-end regression test suite
│   ├── audit_figures.js              # Vector SVG & 300-DPI PNG integrity auditor
│   ├── generate_all_supporting_figures.py # Clean figure regeneration pipeline
│   └── select_optimal_hyperparams.py # Automated grid-search parameter extractor
├── tests/                            # Unit & Integration Test Suite (21 tests)
│   ├── test_ar_calculation.py        # Validates AR bounds ∈ [0, 1] on known graphs
│   ├── test_cost_model.py            # Validates cost model initialization & weighting
│   ├── test_cost_model_corrected.py  # Validates monotonic beta penalty scaling
│   ├── test_hamiltonian.py           # Validates standard Max-Cut Hamiltonian operators
│   ├── test_ternary_search.py        # Validates ternary search convergence & fallback
│   ├── test_partitioner_determinism.py# Validates 100/100 deterministic node ordering
│   ├── test_logging.py               # Validates dual logging & Slurm ID metadata
│   └── test_vqe_executor.py          # Validates executor initialization & compatibility
├── results/                          # Publication Datasets & Mainframe Plots
│   ├── corrected_benchmark.csv       # Complete 4,160-run benchmark dataset
│   ├── hyperparam_grid_search.csv    # Complete 2,000-run hyperparameter grid search dataset
│   ├── optimal_hyperparameters.json  # Extracted global optimal parameters (α=0.70, β=1.0, γ=0.1)
│   ├── scheduler_overhead_summary.json # Ternary search latency and evaluation summary
│   ├── Figure_Performance_Comparison_Averaged.png # Multi-scale benchmark figure
│   ├── Figure_Cost_Model_Empirical_Validation.png # Four-panel cost model validation
│   ├── Figure_Oracle_Comparison_Detailed_10_nodes.png # Static oracle Pareto frontier
│   ├── Figure_Scheduler_Decisions_Averaged.png # Partition size downscaling trajectory
│   └── Figure_Ternary_Search_Ablation.png # Ternary search ablation figure
├── requirements.txt                  # Pinned Python package dependencies
├── environment.yml                   # Conda environment specification
├── setup.py                          # Setuptools configuration (pip install -e .)
├── run_all_experiments.sh            # Universal master launcher (local, cluster, SSH)
└── README.md                         # Complete project documentation
```

---

## 6. Installation & Environment Setup

### 6.1 Local Workstation (Conda / Pip)

**Prerequisites:** Python 3.10+, Conda or virtualenv.

```bash
# 1. Clone the repository
git clone https://github.com/MufakirAnsari/Dy-Part.git
cd Dy-Part

# 2. Create and activate a dedicated conda environment
conda create -n dypart python=3.10 -y
conda activate dypart

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Dy-Part in editable mode
pip install -e .
```

Verify installation:
```bash
python -c "import vqe_framework; print('Dy-Part framework successfully initialized!')"
python scripts/run_phase5_regression_suite.py
```

### 6.2 Supercomputing Environment (Ohio Supercomputer Center)

All cluster experiments were deployed on the **Ohio Supercomputer Center (OSC) Ascend cluster** under Project Allocation `PWSU0516`. Compute nodes feature dual AMD EPYC 7763 64-core processors (128 cores per node, 2.45 GHz base clock, 256 MB L3 cache) and 512 GB DDR4-3200 RAM.

To set up the environment on OSC Ascend:
```bash
# Connect to OSC login node
ssh <username>@ascend.osc.edu
cd ~/Dy-Part

# Load cluster modules and submit environment setup job
sbatch slurm/env_setup.sh
```

To activate the environment in an interactive SLURM session:
```bash
module load miniconda3/24.1.2-py310
conda activate dypart
```

---

## 7. Quick Start & Python API Tutorial

The following self-contained script illustrates how to configure the cost model, find the optimal partition size, and execute partitioned VQE:

```python
import networkx as nx
from qiskit_algorithms.optimizers import COBYLA
from vqe_framework.cost_model import HeuristicCostModel
from vqe_framework.scheduler import DyPartScheduler
from vqe_framework.qpu_interface import NoisyQPU
from vqe_framework.vqe_executor import PartitionedVQE

# 1. Generate a benchmark 3-regular graph (10 nodes)
graph = nx.random_regular_graph(d=3, n=10, seed=42)

# 2. Configure the noise-aware cost model and ternary scheduler
noise_level = 5e-3  # 0.5% 2-qubit gate error rate
cost_model = HeuristicCostModel(
    gate_error_rate=noise_level, 
    alpha=0.70,  # Optimal fidelity weight
    beta=1.0,    # Cut penalty exponent
    gamma=0.1    # Overhead prefactor
)
scheduler = DyPartScheduler(cost_model=cost_model)

# 3. Discover optimal partition size via discrete ternary search
partition_plan = scheduler.find_optimal_partition(graph)
print(f"Optimal Subgraph Size (n_sub*): {partition_plan['optimal_n_sub']}")
print(f"Minimum Predicted Heuristic Cost: {partition_plan['best_cost']:.4f}")
print(f"Scheduler Search Evaluations:     {partition_plan['num_evaluations']}")

# 4. Initialize noisy QPU simulator (incorporating depolarizing + readout noise)
qpu = NoisyQPU(n_qubits=graph.number_of_nodes(), gate_error_rate=noise_level)
optimizer = COBYLA(maxiter=150)

# 5. Execute cut-aware partitioned VQE
vqe = PartitionedVQE(graph=graph, qpu=qpu, optimizer=optimizer, seed=42)
result = vqe.run(partition_plan)

print("=" * 45)
print(f"Expected Cut Value:     {result['expected_cut']:.2f}")
print(f"Exact Max-Cut Value:    {result['max_cut']}")
print(f"Approximation Ratio:    {result['approximation_ratio']:.4f}")
print("=" * 45)
```

---

## 8. HPC SLURM Automation Pipeline

All production job arrays in `slurm/` are pre-configured for the OSC Ascend cluster (Project Allocation `PWSU0516`):

| Script | Purpose | Cores / Memory / Time | Array Tasks | Log Destination |
| :--- | :--- | :--- | :--- | :--- |
| [`slurm/env_setup.sh`](slurm/env_setup.sh) | Bootstraps Conda environment & dependencies | 1 core, 8 GB, 30 min | 1 | `logs/env_setup_<jobid>.out` |
| [`slurm/run_baseline.sh`](slurm/run_baseline.sh) | Baseline multi-seed reproduction (30 seeds) | 4 cores, 16 GB, 4 hours | 1 | `logs/phase1_baseline/` |
| [`slurm/run_hyperparam.sh`](slurm/run_hyperparam.sh) | Grid search array over $(\alpha, \beta, \gamma)$ | 4 cores, 16 GB, 2 hours | 200 tasks (2,000 runs) | `logs/phase2_hyperparam/` |
| [`slurm/run_benchmark.sh`](slurm/run_benchmark.sh) | Multi-scale benchmark across 8–20 nodes | 4 cores, 16 GB, 8 hours | 50 tasks (4,160 runs) | `logs/phase2_benchmark/` |
| [`slurm/run_ablation.sh`](slurm/run_ablation.sh) | Head-to-head ternary search vs exhaustive ablation | 4 cores, 16 GB, 2 hours | 1 | `logs/phase3_ablation/` |
| [`slurm/submit_all.sh`](slurm/submit_all.sh) | Dependency-chained master SLURM launcher | Orchestrator | Pipeline | `logs/` |

To launch the full pipeline on OSC Ascend:
```bash
bash run_all_experiments.sh --account=PWSU0516
```

---

## 9. Verification & Automated Test Suites

Dy-Part incorporates a comprehensive testing hierarchy guaranteeing 100% computational correctness, parameter monotonicity, and data reproducibility.

### 9.1 End-to-End Regression Test Suite (19 Tests)

The Phase 5 regression test suite validates the entire scientific pipeline across 9 verification modules:
```bash
python scripts/run_phase5_regression_suite.py
```

```text
======================================================================
      DY-PART END-TO-END REGRESSION TEST SUITE
======================================================================
test_determinism_across_100_runs (__main__.Test1_PartitionerDeterminism) ... ok
test_node_and_edge_conservation (__main__.Test1_PartitionerDeterminism) ... ok
test_classical_cost_monotonicity_with_cuts (__main__.Test2_CostModelMonotonicity) ... ok
test_higher_beta_strictly_penalizes_cuts (__main__.Test2_CostModelMonotonicity) ... ok
test_quantum_cost_growth_with_subgraph_size (__main__.Test2_CostModelMonotonicity) ... ok
test_zero_cuts_zero_classical_cost (__main__.Test2_CostModelMonotonicity) ... ok
test_ar_bounds (__main__.Test3_ARCalculationBounds) ... ok
test_canonical_graph_solutions (__main__.Test3_ARCalculationBounds) ... ok
test_ternary_evaluations_fewer_on_20_nodes (__main__.Test4_TernarySearchCorrectness) ... ok
test_ternary_vs_exhaustive_agreement (__main__.Test4_TernarySearchCorrectness) ... ok
test_metis_partitioner_node_conservation (__main__.Test5_BaselinePartitioners) ... ok
test_random_partitioner_node_conservation (__main__.Test5_BaselinePartitioners) ... ok
test_all_approximation_ratios_bounded (__main__.Test6_BenchmarkDatasetIntegrity) ... ok
test_exact_row_count_and_methods (__main__.Test6_BenchmarkDatasetIntegrity) ... ok
test_seed_counts_per_graph_size (__main__.Test6_BenchmarkDatasetIntegrity) ... ok
test_grid_search_runs_and_optima (__main__.Test7_HyperparamGridSearchIntegrity) ... ok
test_ablation_metrics (__main__.Test8_AblationSummaryIntegrity) ... ok
test_authors_and_affiliations (__main__.Test9_PublicationIntegrity) ... ok
test_latex_braces_and_environments (__main__.Test9_PublicationIntegrity) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.084s

OK
```

### 9.2 Unit Test Suite (21 Tests)

```bash
pytest tests/ -v
```
All 21 unit tests pass with zero warnings, covering Hamiltonian operators, cost model convexity, and deterministic greedy BFS partitioning.

---

## 10. Citation, License & Acknowledgments

### Citation
If you use the Dy-Part framework, benchmark datasets, or scheduling algorithms in your research, please cite our paper:

```bibtex
@article{ansari2026dypart,
  title={Dy-Part: A Dynamic, Noise-Aware Scheduler for Optimizing Hybrid Quantum-Classical Algorithms},
  author={Ansari, Mufakir Qamar and Ansari, Mudabir Qamar},
  journal={Springer Nature},
  year={2026}
}
```

### Open Source License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for complete details.

### Computing Acknowledgments
We gratefully acknowledge the **Ohio Supercomputer Center (OSC)** for providing high-performance computing resources and technical support on the **Ascend cluster** under Project Allocation `PWSU0516`. Large-scale computational runs were orchestrated using SLURM job array managers across dual AMD EPYC 7763 64-core processors.
