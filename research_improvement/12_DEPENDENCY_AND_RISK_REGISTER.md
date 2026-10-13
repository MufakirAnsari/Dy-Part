# Dependency and Risk Register

## 1. Action Dependency Graph

The following graph maps all 35 project actions across Phases 0 through 5, highlighting immediate prerequisites, downstream dependencies, and critical execution paths.

```
PHASE 0 (Parallel Setup & Environment):
  ACT-001 (requirements.txt) ──→ ACT-005 (SLURM scripts)
  ACT-002 (fix setup.py)     ──→ ACT-007 (Git init)
  ACT-003 (upgrade logging)  ──→ ACT-005 (SLURM scripts)
  ACT-004 (fix partitioner)  ──→ [no downstream; standalone fix]

  ACT-005 + ACT-003 ──→ ACT-006 (master submit script)

PHASE 1 (Sequential Core Algorithmic Fixes):
  ACT-008 (fix cost model)   ─┐
  ACT-009 (fix AR calc)      ─┤──→ ACT-012 (unit tests)
  ACT-010 (ternary search)   ─┘         │
  ACT-010 ──→ ACT-011 (exhaustive fallback)   │
                                         ├──→ ACT-013 (baseline reproduction)
  ACT-005 + ACT-006 ────────────────────┘

PHASE 2 (Empirical Benchmarking & Statistical Validation):
  ACT-012 + ACT-013 ──→ ACT-014 (hyperparameter grid search)
  ACT-014 ──→ ACT-015 (select hyperparams)
  [ACT-016 (METIS) can start anytime in Phase 2]
  [ACT-017 (random baseline) can start anytime in Phase 2]
  ACT-015 + ACT-016 + ACT-017 ──→ ACT-018 (full benchmark)
  ACT-018 ──→ ACT-019 (statistical analysis)
  ACT-010 ──→ ACT-020 (runtime measurement)

PHASE 3 (Ablation & Structural Optimizations - Optional / Parallel):
  ACT-021 (consolidate executors) — standalone
  ACT-008 + ACT-009 ──→ ACT-022 (empirical cost validation)
  ACT-010 + ACT-018 ──→ ACT-023 (ternary ablation)

PHASE 4 (Manuscript Revisions & Editorial Updates):
  ACT-024 (editorial fixes) — standalone, can start early
  ACT-008 + ACT-010 ──→ ACT-025 (update methodology)
  ACT-018 + ACT-019 ──→ ACT-026 (update results)
  ACT-018 ──→ ACT-027 (regenerate figures)
  ACT-028 (expand limitations) — standalone
  ACT-029 (VQE/QAOA justification) — standalone
  ACT-019 ──→ ACT-030 (update stats text)
  ACT-024 through ACT-030 ──→ ACT-031 (reviewer response)

PHASE 5 (Quality Assurance & Resubmission Package):
  ACT-031 ──→ ACT-032 (test suite)
  ACT-027 ──→ ACT-033 (figure cross-check)
  ACT-031 ──→ ACT-034 (rebuttal letter)
  ACT-034 ──→ ACT-035 (proofreading)
```

### Critical Path Analysis

The critical path determines the minimum completion schedule for the revision process:

```
[ACT-001/ACT-003] ──→ [ACT-005/ACT-006] ──→ [ACT-008/009/010] ──→ [ACT-012] 
       │                      │                      │                 │
     Days 1-2               Days 3-5               Days 6-8          Days 9-11
       ▼                      ▼                      ▼                 ▼
   [ACT-014]      ──→     [ACT-015]     ──→      [ACT-018]    ──→  [ACT-019/026/027]
       │                      │                      │                 │
    Week 2-3                Week 3                 Week 4            Week 4-5
       ▼                      ▼                      ▼                 ▼
   [ACT-031]      ──→     [ACT-034]     ──→      [ACT-035]
       │                      │                      │
     Week 5                 Week 5                 Week 5
```

- **Estimated Critical Path Duration:** **4–5 weeks** (dominated by high-performance compute queue and simulation wall-times for ACT-014 grid search and ACT-018 30-seed benchmark matrix across graph topologies and noise levels on OSC Pitzer).
- **Primary Bottlenecks:**
  1. Completion of ACT-008, ACT-009, ACT-010 code fixes before ACT-012 verification can validate baseline accuracy.
  2. OSC job queue throughput for ACT-014 (96 configurations) and ACT-018 (3,600 simulation runs).
  3. Regeneration of manuscript artifacts (ACT-026, ACT-027) upon completion of statistical verification (ACT-019).

---

## 2. Risk Register

| Risk ID | Risk Description | Probability | Impact | Trigger Event | Mitigations | Contingency Plan | Owner | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-001** | Corrected Dy-Part Still Doesn't Beat Static | Medium (40%) | Critical | Completion and analysis of ACT-018 full benchmark matrix | **A:** Target and highlight operational regimes where dynamic advantages physically dominate (e.g., severe thermal/depolarizing noise, irregular dense topologies, high cross-cut communication costs).<br>**B:** Reposition manuscript contribution toward the dynamic scheduling framework, noise-adaptive decomposition methodology, and overhead trade-off boundaries rather than asserting universal dominance.<br>**C:** Test secondary cost formulations (Option B, Option C). | If zero noise/topology regimes demonstrate statistically significant advantage over static partitioning, reframe the manuscript as an exploratory analysis and benchmarking framework for dynamic quantum partitioning, demonstrating theoretical limits and overhead trade-offs for VQE MaxCut. | Lead Researcher | Unresolved |
| **RISK-002** | Ternary Search Doesn't Match Exhaustive Search | Low-Med (25%) | High | Completion of ACT-010 testing and TEST-004 verification | **A:** Empirically evaluate unimodality profiles across graph partition cost landscapes; implement automated fallback to bounded exhaustive search when convexity/unimodality is violated.<br>**B:** Honestly document the exact ternary agreement percentage; report ternary as an empirical heuristic yielding near-optimal solutions with sub-linear evaluation overhead. | If ternary agreement falls below 90% across benchmark topologies, default to exhaustive scan with early pruning heuristics and amend runtime complexity claims from $O(\log \|V\|)$ to $O(\|V\|)$ bounded. | Lead Researcher | Unresolved |
| **RISK-003** | OSC High-Performance Environment Setup Fails | Low (15%) | Medium | Execution of ACT-005 and automated environment configuration (`env_setup.sh`) | **A:** Validate exact conda virtual environment dependencies and Qiskit C-extensions on local development workstation first.<br>**B:** Export explicit conda lockfile (`conda env export --no-builds`) and portable wheels from a verified local build.<br>**C:** Package execution stack into an Apptainer/Singularity container for portable cluster deployment. | Transition benchmarking to local multicore workstation or scalable cloud compute (AWS ParallelCluster / GCP) while debugging OSC environment modules. | Lead Researcher | Unresolved |
| **RISK-004** | 20-Qubit Numerical Simulations Exceed Memory | Medium (35%) | Medium | Launch of ACT-018 benchmark jobs on 20-node instances | **A:** Retain statevector backend for $N \le 16$ qubits; configure Matrix Product State (MPS) or Clifford/Tensor Network simulator in Qiskit-Aer for $N=20$.<br>**B:** Request high-memory compute nodes on OSC Pitzer (`--mem=96GB` or `--mem=192GB`).<br>**C:** Limit sample shots and cap maximum classical optimizer steps (e.g., 200 iterations) for 20-qubit instances. | Bound empirical evaluation to $N \le 16$ qubits with comprehensive statistical depth (50 seeds), documenting 20-qubit simulation memory bounds as an architectural constraint for future tensor-network studies. | Lead Researcher | Unresolved |
| **RISK-005** | Statistical Tests Show No Significance ($p > 0.05$) | Medium (30%) | High | Execution of ACT-019 Wilcoxon and Mann-Whitney statistical tests | **A:** Increase sample seed count from 30 to 50 or 100 on contested topologies to boost statistical power.<br>**B:** Report Cohen's $d$ and Vargha-Delaney $A_{12}$ effect sizes alongside raw p-values to demonstrate systematic shifts.<br>**C:** Employ paired Wilcoxon signed-rank tests matching identical random graph seeds across algorithms. | Report all null and non-significant results transparently without selective filtering; frame findings as characterization of noise resilience boundaries where dynamic partitioning matches static performance. | Lead Researcher | Unresolved |
| **RISK-006** | METIS Baseline Outperforms Dy-Part Partitioning | Medium (35%) | High | Analysis of ACT-018 comparative benchmark results against METIS | **A:** Emphasize that Dy-Part is dynamic and noise-adaptive, whereas METIS minimizes edge cuts statically without awareness of qubit fidelity, gate error variation, or decoherence rates.<br>**B:** Emphasize high-noise and non-uniform noise topologies where edge cut minimization alone produces lower quantum circuit fidelity. | Position Dy-Part as complementary to structural graph partitioners like METIS; propose a hybrid METIS-initialized dynamic partitioning pipeline as a future research trajectory. | Lead Researcher | Unresolved |
| **RISK-007** | Cost Model Formulation Fundamentally Flawed | Low-Med (20%) | Critical | Analysis of EXP-005 empirical runtime vs. predicted cost correlations (ACT-022) | **A:** In the event of weak empirical correlation ($r < 0.50$), acknowledge linear additive modeling limits; document machine-learned cost modeling as next-generation work.<br>**B:** Evaluate alternative parameter weightings (DEC-001 Options B and C). | Reframe the cost function as a "heuristic scheduling guide" rather than an exact predictive cost model; update methodology equations and theoretical claims accordingly. | Lead Researcher | Unresolved |
| **RISK-008** | Reviewer Rejection Despite Full Re-implementation | Low (10%) | Medium | Receipt of editorial decision following resubmission package | **A:** Ensure the rebuttal response letter (ACT-034) is comprehensive, respectful, point-by-point, and accompanied by transparent data tables, reproducibility scripts, and open repository links. | Resubmit revised manuscript to alternative reputable venues (e.g., IEEE Transactions on Quantum Engineering, Quantum Science and Technology, or Physical Review Research). | Lead Researcher | Unresolved |

---

## 3. Decision Register Dependencies

The following table records architectural and experimental decisions that directly gate downstream execution stages.

| Decision ID | Description | Impacted / Blocking Actions | Decision Deadline | Status | Recommended Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEC-001** | Classical cost formula formulation selection: Option A ($T_{\text{classical}} = k \cdot 2^{N_i}$), Option B ($T_{\text{classical}} = k \cdot 1.442^{N_i}$), or Option C ($T_{\text{classical}} = \alpha \cdot N_i + \beta$). | ACT-008, ACT-014 | Prior to Phase 1 implementation | Pending Researcher Confirmation | Adopt Option A as primary baseline for exact exponential MaxCut solvers; benchmark Option B as an alternate branch during ACT-022. |
| **DEC-002** | Maximum benchmark graph size ($N=16$ vs. $N=20$ nodes). | ACT-018 | Prior to launching Phase 2 benchmark matrix | Pending (Depends on RISK-004) | Target $N=16$ with 30 seeds across all noise models; execute $N=20$ on a targeted subset using OSC high-memory nodes (96GB). |
| **DEC-003** | Baseline partitioner inclusion criteria (Include METIS graph partitioning baseline or retain Random baseline only). | ACT-016, ACT-018 | Prior to Phase 2 benchmark launch | Pending Researcher Confirmation | Include both METIS (`pymetis`) and uniform Random partitioning to satisfy reviewer demands for comprehensive classical comparison. |
| **DEC-004** | Maximum iterations for classical VQE optimizer (COBYLA/SPSA) on large graph instances ($N \ge 12$). | ACT-018 | Prior to Phase 2 benchmark launch | Default: 200 iterations | Maintain default 200 iterations for convergence parity; apply early-stopping threshold ($\Delta E < 10^{-4}$) to prevent queue timeouts. |
| **DEC-005** | Contingency target journal selection in case Quantum Machine Intelligence resubmission is declined. | ACT-034 | Post-decision (Only if rejected) | Pending Editorial Decision | Primary alternative: *IEEE Transactions on Quantum Engineering*; Secondary: *Quantum Science and Technology* (IOP). |

---

## 4. External Dependencies

| Dependency | Purpose / Required For | Source / Provider | Operational Status | Risk Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **OSC Account Access** | Cluster compute resources for high-throughput batch experiments (ACT-014, ACT-018) | Ohio Supercomputer Center (Pitzer Cluster) | Assumed Available | Local workstation fallback for $N \le 12$; cloud compute reservation. |
| **Qiskit 1.1.0+** | Core quantum circuit representation, primitives, and transpile pipeline | PyPI / Conda-forge | Available | Pin exact minor and patch versions in `requirements.txt`. |
| **Qiskit-Aer 0.14.0+** | Noisy quantum circuit simulation with custom noise models | PyPI / Conda-forge | Available | Test wheel compatibility with OSC GLIBC and C++ runtime modules. |
| **pymetis 2023.1+** | METIS graph partitioning baseline implementation (ACT-016) | PyPI | Available | Provide pure-networkx edge-cut fallback if native C++ build fails. |
| **SLURM Workload Manager** | Batch scheduling, array submission, and node allocation on cluster | OSC Pitzer Environment | Available | Master submission script (`run_all.sh`) with robust dependency arrays. |
| **Python 3.10** | Execution runtime environment | OSC Modules (`python/3.10-2023.09`) | Available | Automated initialization script checks module availability. |
| **Conda / Miniconda** | Virtual environment isolation and package management | OSC Modules (`miniconda3`) | Available | Fallback to Python standard `venv` + `pip` if conda solver hangs. |
| **SciPy 1.12+ / NumPy 1.26+** | Scientific computing, optimization, and statistical testing (ACT-019) | PyPI / Conda-forge | Available | Standard scientific stack dependencies pinned in `requirements.txt`. |
