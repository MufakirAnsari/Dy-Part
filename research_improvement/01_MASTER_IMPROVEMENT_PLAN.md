# Master Improvement Plan — Dy-Part Research Project

## Executive Strategy

This project has **three P0-Critical issues** that must be resolved before any other work:
1. The scheduler does not implement ternary search (paper claims O(log|V|))
2. The actual experimental data shows Dy-Part does NOT beat the static baseline
3. The approximation ratio exceeds 1.0 in 9.4% of runs

These are not cosmetic problems. They mean the **core scientific contribution is currently unsupported by evidence**. The cost model has an inverted beta effect, the tuned hyperparameters are at the performance minimum, and the graph partitioner is non-deterministic.

The good news: the *idea* behind Dy-Part is sound. The framework architecture is correct. The problem is that the cost model math is broken and the hyperparameters were tuned to a broken model. Fixing the cost model, implementing the ternary search, and re-running experiments on OSC with proper logging should produce defensible results.

---

## Phased Implementation Roadmap

### Phase 0 — Baseline & Environment Setup (Prerequisite)
**Goal:** Establish reproducible environment, OSC integration, and comprehensive logging.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Create `requirements.txt` + `environment.yml` | ACT-001 | ISS-040 | Small | Not started |
| Fix `setup.py` location (move to root) | ACT-002 | ISS-040 | Very small | Not started |
| Upgrade `logging_config.py` for dual file+console logging | ACT-003 | ISS-038 | Small | Not started |
| Fix graph partitioner determinism (sort nodes) | ACT-004 | ISS-006 | Very small | Not started |
| Create SLURM batch submission framework for OSC | ACT-005 | ISS-039 | Medium | Not started |
| Create `run_all_experiments.sh` master script | ACT-006 | ISS-039 | Medium | Not started |
| Initialize Git repository | ACT-007 | — | Very small | Not started |

**Gate:** Environment installs on OSC; test job submits and runs successfully.

---

### Phase 1 — Critical Correctness Fixes (P0)
**Goal:** Fix the three fundamental correctness issues that invalidate the central claims.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Fix classical cost formula (ISS-004: inverted beta) | ACT-008 | ISS-004 | Small | Not started |
| Fix AR calculation (ISS-003: AR>1) | ACT-009 | ISS-003, ISS-009 | Medium | Not started |
| Implement ternary search in scheduler.py | ACT-010 | ISS-001 | Medium | Not started |
| Add exhaustive-search fallback for non-unimodal | ACT-011 | ISS-001 | Small | Not started |
| Add unit tests for all Phase 1 fixes | ACT-012 | ISS-001,3,4 | Small | Not started |
| Run baseline reproduction experiment (before changes) | ACT-013 | ISS-002 | Medium | Not started |

**Gate:** All unit tests pass. Ternary search matches exhaustive search optimum. AR ∈ [0,1].

---

### Phase 2 — Re-tuning & Core Experiments (P1)
**Goal:** With corrected code, find proper hyperparameters and generate defensible results.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Run hyperparameter grid search (α, β, γ) on OSC | ACT-014 | ISS-005 | Large (compute) | Not started |
| Select optimal hyperparameters from grid search | ACT-015 | ISS-005 | Small | Not started |
| Implement METIS baseline partitioner | ACT-016 | ISS-007 | Medium | Not started |
| Add random-guess baseline | ACT-017 | ISS-012 | Small | Not started |
| Run full benchmark: 8,10,12,16,20 nodes × corrected code | ACT-018 | ISS-002,8 | Large (OSC) | Not started |
| Run statistical analysis (Wilcoxon + ANOVA) | ACT-019 | ISS-010,35 | Medium | Not started |
| Measure actual scheduler runtime overhead | ACT-020 | ISS-036 | Small | Not started |

**Gate:** Dy-Part demonstrably outperforms static in at least one regime with p<0.05. Data for 16-20 nodes exists.

---

### Phase 3 — Research Enhancements (P2+)
**Goal:** Optional improvements that strengthen the paper.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Consolidate executor variants into single class | ACT-021 | ISS-037 | Medium | Not started |
| Empirical cost model validation (runtime vs cuts) | ACT-022 | ISS-004 | Medium | Not started |
| Additional ablation: ternary vs exhaustive performance | ACT-023 | ISS-001 | Small | Not started |

**Gate:** Each enhancement has supporting evidence.

---

### Phase 4 — Manuscript Revision (All Priorities)
**Goal:** Synchronize manuscript with verified code and data.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Fix all P3 editorial issues | ACT-024 | ISS-022–033,041 | Small | Not started |
| Update Section 3 methodology (cost model, ternary search) | ACT-025 | ISS-001,4 | Medium | Not started |
| Update Section 5 results with new data | ACT-026 | ISS-002,11 | Medium | Not started |
| Regenerate all figures with corrected data | ACT-027 | ISS-003,20,42 | Medium | Not started |
| Expand limitations discussion | ACT-028 | ISS-013,14,16,17,18,34 | Small | Not started |
| Add VQE/QAOA justification, gradient optimizers | ACT-029 | ISS-019,30 | Small | Not started |
| Update statistical analysis text | ACT-030 | ISS-010,35 | Small | Not started |
| Prepare reviewer response document | ACT-031 | All | Medium | Not started |

**Gate:** Every quantitative claim matches verified data. No text-plot mismatches.

---

### Phase 5 — Final QA & Submission
**Goal:** Everything is consistent, reproducible, and ready.

| Action | ID | Issues | Effort | Status |
|--------|-----|--------|--------|--------|
| Run full test suite | ACT-032 | All | Small | Not started |
| Cross-check every figure against data CSV | ACT-033 | All | Small | Not started |
| Build complete rebuttal letter | ACT-034 | All | Medium | Not started |
| Final proofreading pass | ACT-035 | All | Small | Not started |

---

## Dependency Graph (Critical Path)

```
ACT-001,002,003,004 (Environment) ──→ ACT-007 (Git init)
                                    ──→ ACT-005,006 (SLURM)
                                    ──→ ACT-008 (Fix cost model)
                                    ──→ ACT-009 (Fix AR calc)
                                    ──→ ACT-010,011 (Ternary search)
                                         │
                                         ▼
                                    ACT-012 (Unit tests)
                                    ACT-013 (Baseline repro)
                                         │
                                         ▼
                                    ACT-014 (Hyperparameter search on OSC)
                                         │
                                         ▼
                                    ACT-015 (Select hyperparams)
                                    ACT-016 (METIS baseline)
                                    ACT-017 (Random baseline)
                                         │
                                         ▼
                                    ACT-018 (Full benchmark on OSC)
                                         │
                                         ▼
                                    ACT-019 (Statistical analysis)
                                    ACT-020 (Runtime measurement)
                                         │
                                         ▼
                                    ACT-024-030 (Manuscript revision)
                                         │
                                         ▼
                                    ACT-031-035 (Final QA & rebuttal)
```

## OSC Deployment Strategy

### Directory Structure on OSC
```
$HOME/dy-part/
├── Dy-Part-main/           # Code (rsync'd from local)
├── logs/                    # All experiment logs (timestamped)
│   ├── phase0_env_test/
│   ├── phase1_baseline/
│   ├── phase2_hyperparam/
│   ├── phase2_benchmark/
│   └── phase3_ablation/
├── results/                 # Output CSVs and plots
├── slurm/                   # SLURM batch scripts
│   ├── submit_all.sh        # Master submission script
│   ├── env_setup.sh         # Environment/conda setup
│   ├── run_baseline.sh      # Phase 1 baseline reproduction
│   ├── run_hyperparam.sh    # Phase 2 grid search
│   ├── run_benchmark.sh     # Phase 2 full benchmark
│   └── run_ablation.sh      # Phase 3 ablations
├── conda_env.yml
└── requirements.txt
```

### Submission From Local Terminal
```bash
# Sync code to OSC
rsync -avz ./Dy-Part-main/ $OSC_USER@pitzer.osc.edu:~/dy-part/Dy-Part-main/

# Submit all experiments
ssh $OSC_USER@pitzer.osc.edu "cd ~/dy-part && sbatch slurm/submit_all.sh"

# Monitor jobs
ssh $OSC_USER@pitzer.osc.edu "squeue -u $OSC_USER"

# Pull results back
rsync -avz $OSC_USER@pitzer.osc.edu:~/dy-part/results/ ./results/
rsync -avz $OSC_USER@pitzer.osc.edu:~/dy-part/logs/ ./logs/
```

### Logging Strategy
Every experiment will log:
1. **SLURM job metadata:** job ID, node, start/end time, exit code
2. **Environment:** Python version, package versions, conda env name
3. **Experiment config:** all hyperparameters, graph sizes, noise levels, seeds
4. **Per-iteration:** optimizer step, energy, parameters (if DEBUG)
5. **Per-run:** AR, energy, n_sub chosen, runtime, num_cuts
6. **Aggregated:** mean/std/min/max across seeds
7. **Errors:** full tracebacks with context

All logs go to both:
- **File:** `logs/<phase>/<experiment>_<SLURM_JOB_ID>_<timestamp>.log`
- **Console:** captured by SLURM to `slurm-<job_id>.out`
