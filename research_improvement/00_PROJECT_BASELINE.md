# Project Baseline — Verified 2026-10-11

## 1. Manuscript
- **File:** `sn-article.tex` (root directory)
- **Journal:** Quantum Machine Intelligence (Springer Nature)
- **Title:** *Dy-Part: A Dynamic, Noise-Aware Scheduler for Optimizing Hybrid Quantum-Classical Algorithms*
- **Author:** Mufakir Qamar Ansari
- **Status:** Under review — Major Revision requested

## 2. Implementation
- **Location:** `Dy-Part-main/`
- **Core framework:** `vqe_framework/` — 8 Python source files + 2 `__init__.py`
- **Experiments:** `experiments/` — 17 Python scripts (many are dev-stage duplicates)
- **Tests:** `tests/` — 3 unit test files
- **No Git repository detected** — no `.git/` directory present

## 3. Review Status
- **5 reviewers** across 6 files in `Review/`
- **R1:** Positive — no issues (accepted prior revisions)
- **R2:** PDF attachment — 5 substantive issues (VQE vs QAOA, shots, SWAP gates, AR>1, scale)
- **R3:** Heaviest review — 11 major + 12 minor = **23 comments total**
- **R4:** 3 improvement requests (SWAP gates, alpha outlier, duplicated text)
- **R5:** 5 specific issues requiring correction before further consideration
- **Total verified reviewer comments:** 37 (32 from TXT + ~5 from R2 PDF)
- **Previous review_analysis captured:** 22 comments. **~10 were missed.**

## 4. Critical Findings from Code & Data Audit

### FINDING-A: Ternary Search Does NOT Exist (P0-Critical)
- **Paper claims:** O(log|V|) ternary search (Algorithm 1, Section 3.2)
- **Code reality:** `scheduler.py` line 73 — exhaustive linear loop `for n_sub in range(...)`
- **Diagram file** (`digraph DyPart Workflow.dot`) describes ternary search with midpoints m1/m2
- **Result:** O(log|V|) claim is completely unsupported

### FINDING-B: Dy-Part Does NOT Beat Static Baseline (P0-Critical)
- **Paper claims:** Dy-Part outperforms static, "more than double" AR in high noise
- **Data reality (final_benchmark_data_averaged.csv):**
  - 8 nodes: Static AR=0.748 vs Dy-Part AR=0.716 → **Static wins**
  - 10 nodes: Static AR=0.706 vs Dy-Part AR=0.689 → **Static wins**
  - 12 nodes: Static AR=0.668 vs Dy-Part AR=0.668 → **Tied**
- **Root cause:** α=0.95 causes scheduler to collapse to n_sub=2 in **89.3%** of all runs

### FINDING-C: AR > 1.0 Occurs in 136/1440 Data Points (P0-Critical)
- Cut-aware reconstruction: ⟨Z_u⟩⟨Z_v⟩ ≠ ⟨Z_uZ_v⟩
- Product approximation violates variational bound
- Max observed AR = 1.347

### FINDING-D: Classical Cost Beta Effect Is Inverted (P1-Major)
- `cost_model.py` line 64: `gamma * (normalized_cuts ** beta)`
- Because `normalized_cuts = num_cuts / total_edges ∈ [0,1]`, raising to higher β makes cost SMALLER
- The test suite (`test_beta_exponent_effect`) explicitly validates this counter-intuitive behavior
- Paper describes β as penalizing complexity — code does the opposite

### FINDING-E: Alpha=0.95 Produces WORST Performance (P1-Major)
- `in_depth_analysis_data.csv`: α=0.95 → AR=0.507 (worst); α=0.2 → AR=0.722 (best)
- The "tuned" operating point is actually the minimum of the performance curve

### FINDING-F: Graph Partitioner Is Non-Deterministic (P1-Major)
- `graph_partitioner.py` line 36: `seed_node = nodes_to_assign.pop()` from a Python `set`
- Python set iteration order is not guaranteed across processes
- Same graph+n_sub can yield different partitions and different num_cuts

### FINDING-G: Runtime Plot Uses Fabricated Data (P2-Important)
- `plot_runtime_breakdown.py` line 16-18: hardcodes `scheduler_time = 0.5s`
- Never actually measured scheduler overhead

### FINDING-H: Hamiltonian Missing Constant Offset (P2-Important)
- Code implements H = Σ Z_uZ_v (raw ZZ sum)
- Standard MaxCut: C = Σ (I - Z_uZ_v)/2
- The -1/2 prefactor and |E|/2 offset are missing
- This doesn't affect optimization (constant shift), but affects AR calculation

## 5. Existing Experimental Evidence
- `results/final_benchmark_data_averaged.csv` — 1440 rows (30 seeds × 3 sizes × 8 noise × 2 methods)
- `results/in_depth_analysis_data.csv` — 6 rows (α sweep)
- `results/in_depth_beta_gamma_data.csv` — 9 rows (β/γ grid)
- Multiple PNG plots in `results/`

## 6. Compute Environment
- **Target:** Ohio Supercomputer Center (OSC)
- **Submission:** SLURM batch scripts, submitted from local terminal
- **Requirements:** All experiments must log comprehensively to files
- **Current logging:** Console-only via `logging_config.py` → stdout

## 7. Missing Resources
- No Git version control
- No requirements.txt or environment.yml
- No SLURM scripts
- No file-based logging
- `setup.py` is in wrong directory (`experiments/` instead of root)
- No comprehensive test coverage for VQE executor or scheduler

## 8. Risks & Blockers
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dy-Part doesn't outperform static | Invalidates central claim | Fix cost model, retune hyperparameters, proper experiments |
| No ternary search in code | O(log\|V\|) claim false | Implement ternary search or correct paper |
| AR>1 anomaly | Mathematical impossibility | Fix AR calculation or clamp |
| Non-deterministic partitioner | Irreproducible results | Sort nodes before partitioning |
| OSC environment untested | Experiments may fail | Create comprehensive SLURM scripts with proper error handling |
