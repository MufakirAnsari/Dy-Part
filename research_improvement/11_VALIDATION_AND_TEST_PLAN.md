# Validation and Test Plan

## 1. Unit Test Requirements

### TEST-001: Graph Partitioner Determinism (ACT-004, ISS-006)
- **Test file:** `tests/test_partitioner_determinism.py`
- **Setup:** Create 6, 8, 10, 12-node 3-regular graphs with fixed seed
- **Test cases:**
  - Same graph + `n_sub` produces identical partition across 100 invocations
  - Different `n_sub` values produce different partitions
  - All nodes assigned to exactly one subgraph
  - All subgraphs have size $\le n_{\text{sub}}$
- **Pass criteria:** 100% deterministic; no test failures in 100 runs

### TEST-002: Classical Cost Model Monotonicity (ACT-008, ISS-004)
- **Test file:** `tests/test_cost_model_corrected.py`
- **Setup:** Fixed graph (10 nodes); sweep $\beta$ from 0.5 to 5.0
- **Test cases:**
  - Higher $\beta \rightarrow$ higher classical cost for fixed `num_cuts` > 0
  - Cost = 0 when `num_cuts` = 0 regardless of $\beta$
  - Cost monotonically increases with `num_cuts` for fixed $\beta$
  - Total cost = $\alpha \times \text{quantum} + (1-\alpha) \times \text{classical}$
- **Pass criteria:** All monotonicity constraints hold

### TEST-003: AR Calculation Bounds (ACT-009, ISS-003)
- **Test file:** `tests/test_ar_calculation.py`
- **Setup:** Known small graphs (4, 6 nodes) with analytically computed MaxCut
- **Test cases:**
  - $\text{AR} \in [0, 1]$ for all noise levels ($10^{-4}$ to $10^{-1}$)
  - $\text{AR} = 1.0$ on noiseless 4-node graph (VQE should find optimal)
  - AR on 4-node known graph matches hand-computed value $\pm 0.01$
  - AR never exceeds 1.0 even with product-state approximation
- **Pass criteria:** No $\text{AR} > 1.0$ in any test configuration

### TEST-004: Ternary Search Correctness (ACT-010, ISS-001)
- **Test file:** `tests/test_ternary_search.py`
- **Setup:** 100 random 3-regular graphs (8–20 nodes)
- **Test cases:**
  - Ternary search returns same optimal $n_{\text{sub}}^*$ as exhaustive search
  - Number of cost evaluations $\le 2 \times \lceil\log_3(|V|)\rceil + 6$
  - Exhaustive fallback activates for small graphs (< 6 nodes)
  - Exhaustive fallback produces correct result
- **Pass criteria:** $\ge 95\%$ agreement between ternary and exhaustive; timing shows $\mathcal{O}(\log N)$

### TEST-005: Hamiltonian Convention Consistency (ISS-009)
- **Test file:** `tests/test_hamiltonian.py`
- **Setup:** 4-node complete graph, 4-node path graph
- **Test cases:**
  - Ground state energy matches brute-force computation
  - MaxCut value from energy matches known optimal cut
  - Convention documented in docstring
- **Pass criteria:** All energies match to machine precision

### TEST-006: VQE Executor Correctness (ISS-037)
- **Test file:** `tests/test_vqe_executor.py`
- **Setup:** 4-node graph, noiseless simulation
- **Test cases:**
  - Noiseless VQE achieves $\text{AR} \ge 0.95$ on known-optimal graph
  - `cut_aware=True` vs `cut_aware=False` produce different (but both valid) results
  - Executor handles single subgraph (no partition) correctly
  - Executor handles partition where $n_{\text{sub}} = |V|$ (each node separate) correctly
- **Pass criteria:** All assertions pass

### TEST-007: Logging System (ACT-003, ISS-038)
- **Test file:** `tests/test_logging.py`
- **Setup:** Temporary directory for log files
- **Test cases:**
  - `setup_logging()` creates log file in specified directory
  - Messages appear in both file and console
  - `SLURM_JOB_ID` environment variable is captured in filename
  - Log format includes timestamp, level, filename, line number
- **Pass criteria:** All assertions pass; log file exists and contains expected content

---

## 2. Integration Test Requirements

### TEST-008: End-to-End Pipeline (Phase 1 gate)
- **Test file:** `tests/test_integration.py`
- **Setup:** 8-node 3-regular graph, noise = $5 \times 10^{-3}$, seed = 42
- **Test cases:**
  - Full pipeline runs without error: partition $\rightarrow$ VQE $\rightarrow$ AR calculation
  - $\text{AR} \in [0, 1]$
  - Chosen $n_{\text{sub}} \in [2, 8]$
  - Runtime < 300 seconds
  - Results CSV written correctly
- **Pass criteria:** Pipeline completes; outputs valid

### TEST-009: SLURM Script Syntax (ACT-005, ISS-039)
- **Test file:** Manual validation
- **Procedure:** `bash -n slurm/*.sh` (syntax check without execution)
- **Test cases:**
  - All SLURM scripts pass bash syntax check
  - All `#SBATCH` directives are valid
  - Environment activation works on OSC login node
- **Pass criteria:** No syntax errors; successful dry run on OSC

---

## 3. Data Validation Requirements

### TEST-010: Benchmark Output Validation
- **Script:** `tests/validate_benchmark_output.py`
- **Checks:**
  - All expected columns present in CSV
  - No NaN or Inf values in AR, energy, runtime
  - $\text{AR} \in [0, 1]$ for all rows
  - Every (method, graph_size, noise, seed) combination present
  - 30 seeds per configuration
  - Runtime > 0 for all runs
  - Scheduler time > 0 for Dy-Part runs

### TEST-011: Figure-Data Consistency
- **Script:** `tests/validate_figures.py`
- **Procedure:** For each figure, extract data from source CSV and verify plotted values match
- **Checks:**
  - Fig 4 data points match `corrected_benchmark.csv` means
  - Fig 5 error bands match $\pm 1\sigma$ from data
  - Fig 7 alpha sweep matches `hyperparam_grid_search.csv`
  - Runtime plot matches `runtime_scaling.csv`

---

## 4. Manuscript Validation Requirements

### TEST-012: Text-Data Consistency
- **Procedure:** Manual cross-check of every quantitative claim against source data
- **Checklist:**
  - [ ] Every AR value in text matches CSV to 3 decimal places
  - [ ] Every 'improvement' percentage matches computed values
  - [ ] No 'more than double' or similar claims without supporting data
  - [ ] All p-values match statistical test outputs
  - [ ] Noise range in text matches experimental configuration
  - [ ] Graph sizes in text match experimental configuration

### TEST-013: LaTeX Build Validation
- **Procedure:** `pdflatex sn-article.tex && bibtex sn-article && pdflatex sn-article.tex`
- **Checks:**
  - [ ] No undefined references
  - [ ] No multiply-defined labels
  - [ ] No missing citations
  - [ ] All figures render correctly
  - [ ] No overfull hboxes > 10pt

---

## 5. Phase Gates

### Phase 1 Gate (After Correctness Fixes)
- [ ] TEST-001 through TEST-005 pass
- [ ] TEST-008 passes
- [ ] AR never exceeds 1.0
- [ ] Ternary search agrees with exhaustive $\ge 95\%$

### Phase 2 Gate (After Experiments)
- [ ] TEST-010 passes on `corrected_benchmark.csv`
- [ ] Dy-Part AR > Static AR with $p < 0.05$ in at least one regime
- [ ] 16-node and 20-node results present in benchmark

### Phase 4 Gate (After Manuscript Revision)
- [ ] TEST-011 and TEST-012 pass
- [ ] TEST-013 passes
- [ ] All reviewer comments addressed in response document

### Phase 5 Gate (Submission Ready)
- [ ] All gates above passed
- [ ] Rebuttal letter complete
- [ ] All co-authors approve
