# Research Enhancement Backlog

## Priority Legend
- **High**: Directly strengthens a reviewer response or fixes a scientific weakness
- **Medium**: Improves paper quality but not strictly required
- **Low**: Nice-to-have for journal-quality polish

---

## Enhancement List

### ENH-001: Implement METIS Baseline Comparison (High)
- **Motivation:** R3-C03 explicitly asks for comparison to established partitioning methods. METIS is the gold standard for graph partitioning.
- **Scientific benefit:** Positions Dy-Part against an accepted benchmark, making results more meaningful to reviewers and readers.
- **Implementation:** Create `metis_partitioner.py` wrapper; add METIS as a method in `run_corrected_benchmark.py`.
- **Related issues:** ISS-007
- **Effort:** Medium (2-3 days)
- **Risk:** If METIS outperforms Dy-Part, this weakens the paper. Mitigate by emphasizing Dy-Part's noise-awareness as an orthogonal advantage.

### ENH-002: Random-Guess Baseline for AR Floor (High)
- **Motivation:** R3-C06 notes AR drops below 0.5 (random guessing). Adding a random baseline line makes this comparison explicit.
- **Scientific benefit:** Shows at which noise level VQE becomes worse than random; this is an honest and important data point.
- **Implementation:** Add random MaxCut solver (random bitstring evaluation); plot as horizontal line at AR≈0.5.
- **Related issues:** ISS-012
- **Effort:** Small (hours)
- **Risk:** None.

### ENH-003: Empirical Cost Model Validation (High)
- **Motivation:** R3-C01 questions whether the heuristic cost model actually predicts VQE performance.
- **Scientific benefit:** If correlation is high, this validates the cost model. If low, it motivates improvements.
- **Implementation:** Run EXP-005; compute Pearson/Spearman correlation between heuristic cost and actual AR across partition sizes.
- **Related issues:** ISS-004
- **Effort:** Medium (1 compute day + analysis)
- **Risk:** Low correlation would require acknowledging the cost model is approximate.

### ENH-004: Extended Scale Experiments (16-20 Qubits) (High)
- **Motivation:** Both R2-C05 and R3-C04 demand larger experiments. 12 qubits is classically trivial.
- **Scientific benefit:** Demonstrates scalability and the regime where partitioning becomes essential.
- **Implementation:** Add 16 and 20-node 3-regular graphs to benchmark configuration.
- **Related issues:** ISS-008
- **Effort:** Large (compute-bound on OSC)
- **Risk:** Simulation of 20-qubit subcircuits may require significant memory.

### ENH-005: Proper Statistical Testing Framework (High)
- **Motivation:** R3-C08 and R5-C04 both flag inadequate statistical analysis.
- **Scientific benefit:** Proper Wilcoxon signed-rank tests per noise point + ANOVA across noise sweep provide defensible claims.
- **Implementation:** Post-process benchmark CSV with scipy.stats; generate p-value table.
- **Related issues:** ISS-010, ISS-035
- **Effort:** Medium (1 day)
- **Risk:** Statistical tests may show no significance → must temper claims accordingly.

### ENH-006: Ternary vs Exhaustive Ablation Study (Medium)
- **Motivation:** After implementing ternary search, verify it finds the same optimum and measure speedup.
- **Scientific benefit:** Validates O(log|V|) claim with empirical evidence; shows when unimodality assumption holds.
- **Implementation:** Run EXP-004 on graphs up to 40 nodes.
- **Related issues:** ISS-001
- **Effort:** Small (hours of compute + analysis)
- **Risk:** If unimodality fails frequently, must adjust claims about ternary search reliability.

### ENH-007: Executor Consolidation (Medium)
- **Motivation:** 4 near-identical executor files create maintenance burden and risk of inconsistent behavior.
- **Scientific benefit:** Cleaner codebase improves reproducibility and reduces bugs.
- **Implementation:** Refactor into single `PartitionedVQE` class with flags for `cut_aware` (bool) and `seed` (optional int).
- **Related issues:** ISS-037
- **Effort:** Medium (1-2 days)
- **Risk:** Must ensure refactored executor produces identical results to originals.

### ENH-008: Measured Runtime Breakdown (Medium)
- **Motivation:** Current runtime plot uses fabricated data (hardcoded scheduler_time=0.5s).
- **Scientific benefit:** Honest runtime data; shows scheduler overhead is negligible.
- **Implementation:** Instrument scheduler and VQE executor with `time.perf_counter()`. Run EXP-006.
- **Related issues:** ISS-036
- **Effort:** Small (hours)
- **Risk:** None.

### ENH-009: Hardware Topology Discussion (Medium)
- **Motivation:** R2-C03 and R4-C01 both flag missing SWAP gate discussion.
- **Scientific benefit:** Acknowledging the limitation positions it as future work and shows awareness.
- **Implementation:** Expand Section 6.3 with explicit discussion of topology-aware cost modeling.
- **Related issues:** ISS-013, ISS-028
- **Effort:** Very small (text only)
- **Risk:** None.

### ENH-010: Quantum/Classical Boundary Analysis (Medium)
- **Motivation:** R3-C10 raises fundamental concern: n_sub=2 makes subproblems classically simulatable.
- **Scientific benefit:** Honest discussion of when partitioning helps vs when it removes quantum advantage.
- **Implementation:** Add analysis paragraph identifying the crossover point where subgraph size is too small for quantum benefit.
- **Related issues:** ISS-017
- **Effort:** Small (analysis + text)
- **Risk:** None.

### ENH-011: VQE vs QAOA Justification (Low)
- **Motivation:** R2-C01 asks why VQE not QAOA.
- **Scientific benefit:** Strengthens methodology section.
- **Implementation:** Add paragraph explaining VQE chosen because the partitioning framework is ansatz-agnostic; QAOA is a special case.
- **Related issues:** ISS-019
- **Effort:** Very small (text only)
- **Risk:** None.

### ENH-012: Comprehensive Test Suite (Low)
- **Motivation:** Only 3 test files exist; critical paths untested.
- **Scientific benefit:** Increases confidence in implementation correctness.
- **Implementation:** Add tests for scheduler, AR calculation, cost model, VQE executor.
- **Related issues:** ISS-006
- **Effort:** Medium (1-2 days)
- **Risk:** None.

---

## Resource Estimates
| Priority | Count | Total Effort |
|----------|-------|--------------|
| High     | 5     | ~2 weeks (mostly compute) |
| Medium   | 5     | ~1 week |
| Low      | 2     | ~2 days |
