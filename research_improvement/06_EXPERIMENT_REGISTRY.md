# Experiment Registry

## EXP-001: Baseline Reproduction (Before Fixes)
- **Research question:** Can we reproduce the original results with the current code?
- **Hypothesis:** Results will match `final_benchmark_data_averaged.csv`
- **Why needed:** Establish ground truth before making code changes
- **Configuration:** 8,10,12 nodes; 8 noise levels; 5 seeds (fast subset)
- **Metrics:** AR, chosen n_sub, runtime
- **Statistical analysis:** Mean ± std
- **OSC resources:** 1 node, 4 cores, 4GB RAM, ~2h walltime
- **Script:** `experiments/run_final_benchmark.py` (unmodified)
- **Output:** `results/baseline_reproduction.csv`
- **Log:** `logs/phase1_baseline/exp001_*.log`
- **Dependencies:** ACT-001 through ACT-006
- **Status:** Not started

## EXP-002: Hyperparameter Grid Search (Corrected Code)
- **Research question:** What are the optimal (α, β, γ) for the corrected cost model?
- **Hypothesis:** The corrected cost model (with non-inverted β) will have a meaningfully different optimum than α=0.95
- **Why needed:** ISS-005 shows current tuning is at performance minimum
- **Configuration:**
  - α ∈ {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95}
  - β ∈ {1.0, 1.5, 2.0, 3.0}
  - γ ∈ {0.1, 0.5, 1.0, 2.0, 5.0}
  - Graph: 10-node 3-regular, seed=42
  - Noise: 5×10⁻³ (mid-range)
  - Seeds: 10 per config
  - Total configs: 10 × 4 × 5 = 200 × 10 seeds = 2000 runs
- **Metrics:** AR, chosen n_sub, cost components
- **Statistical analysis:** Mean AR per (α,β,γ); identify Pareto front
- **OSC resources:** Array job, 200 tasks × 10 seeds each; ~1 node/task, 2h each
- **Script:** New `experiments/run_hyperparam_search.py`
- **Output:** `results/hyperparam_grid_search.csv`
- **Log:** `logs/phase2_hyperparam/exp002_*.log`
- **Dependencies:** ACT-008,009,010 (corrected code)
- **Success criteria:** Clear optimum region identified; AR at optimum > AR at α=0.95
- **Status:** Not started

## EXP-003: Full Benchmark (Corrected Code + Tuned Params)
- **Research question:** Does corrected Dy-Part outperform static and METIS baselines?
- **Hypothesis:** Dy-Part with corrected cost model achieves higher AR than static n_sub=4 in high-noise regime
- **Why needed:** Central experimental evidence for the paper
- **Configuration:**
  - Methods: Dy-Part, Static(n_sub=4), METIS, Random-guess
  - Graph sizes: 8, 10, 12, 16, 20 nodes (3-regular)
  - Noise levels: 10 log-spaced from 10⁻⁴ to 10⁻¹
  - Seeds: 30 per config
  - Total: 4 methods × 5 sizes × 10 noise × 30 seeds = 6000 runs
- **Metrics:** AR, chosen n_sub, num_cuts, runtime (total + scheduler + VQE separately)
- **Statistical analysis:** Wilcoxon per noise point; ANOVA across noise sweep; effect sizes
- **OSC resources:** Array job; ~5 nodes; estimated 48h total walltime
- **Script:** New `experiments/run_corrected_benchmark.py`
- **Output:** `results/corrected_benchmark.csv`
- **Log:** `logs/phase2_benchmark/exp003_*.log`
- **Dependencies:** ACT-014,015,016,017
- **Success criteria:** Dy-Part AR > Static AR with p<0.05 in ≥3 noise points for ≥2 graph sizes
- **Failure criteria:** No noise point shows significant improvement → revise claims
- **Status:** Not started

## EXP-004: Ternary vs Exhaustive Ablation
- **Research question:** Does ternary search find the same optimum as exhaustive?
- **Hypothesis:** Ternary search agrees with exhaustive in ≥95% of cases (unimodal cost)
- **Why needed:** Validate the O(log|V|) claim
- **Configuration:** Graphs 8-40 nodes; 5 noise levels; 20 seeds
- **Metrics:** Agreement rate, divergence magnitude, wall-clock time
- **OSC resources:** 1 node, ~4h
- **Script:** New `experiments/run_ternary_ablation.py`
- **Output:** `results/ternary_vs_exhaustive.csv`
- **Log:** `logs/phase3_ablation/exp004_*.log`
- **Dependencies:** ACT-010,011
- **Status:** Not started

## EXP-005: Empirical Cost Model Validation
- **Research question:** Does the heuristic cost correlate with actual VQE performance?
- **Hypothesis:** Lower heuristic cost → higher AR, with meaningful correlation
- **Why needed:** ISS-004 / R3-C01 — validates the cost model empirically
- **Configuration:** 10,12-node graphs; sweep n_sub from 2 to |V|; 3 noise levels; 10 seeds
- **Metrics:** Heuristic cost vs actual AR; Pearson/Spearman correlation
- **OSC resources:** 1 node, ~8h
- **Script:** New `experiments/run_cost_validation.py`
- **Output:** `results/cost_model_validation.csv`
- **Log:** `logs/phase3_ablation/exp005_*.log`
- **Dependencies:** ACT-008,009
- **Status:** Not started

## EXP-006: Runtime Scaling Analysis
- **Research question:** How does scheduler + VQE runtime scale with graph size?
- **Hypothesis:** Scheduler overhead is negligible; VQE dominates
- **Why needed:** ISS-036 — runtime plot currently uses fabricated data
- **Configuration:** Graphs 8,10,12,16,20 nodes; 3 noise levels; 5 seeds; measure scheduler vs VQE time separately
- **Metrics:** Scheduler time, VQE time, total time
- **OSC resources:** 1 node, ~4h
- **Script:** New `experiments/run_runtime_analysis.py`
- **Output:** `results/runtime_scaling.csv`
- **Log:** `logs/phase3_ablation/exp006_*.log`
- **Dependencies:** ACT-010,018
- **Status:** Not started
