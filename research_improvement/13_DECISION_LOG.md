# Decision Log

## DEC-001: Classical Cost Model Formula Selection
- **Status:** PENDING — Requires researcher input
- **Blocking:** ACT-008 (fix cost model), ACT-014 (hyperparameter search)
- **Context:** The current classical cost formula in `cost_model.py` line 64 is:
  ```python
  classical_cost = gamma * (normalized_cuts ** beta)
  ```
  where `normalized_cuts = num_cuts / total_edges ∈ [0,1]`. Because the base is <1, raising to higher β makes cost SMALLER. This is inverted from the paper's description.

- **Options:**

### Option A: Use Raw Count (Not Normalized)
```python
classical_cost = gamma * (num_cuts ** beta)
```
- **Pros:** Simple; higher β always increases cost
- **Cons:** Not scale-invariant across graph sizes; may need per-graph-size γ tuning
- **Risk:** Hyperparameters won't generalize

### Option B: Invert the Exponent (RECOMMENDED)
```python
classical_cost = gamma * (normalized_cuts ** (1.0 / beta))
```
- **Pros:** Scale-invariant; preserves [0,1] range; β>1 makes cost increase faster with cuts
- **Cons:** Slightly different mathematical meaning than paper implies
- **Risk:** Low — still monotonic and well-behaved

### Option C: Exponential Penalty
```python
classical_cost = gamma * (np.exp(beta * normalized_cuts) - 1.0) / (np.exp(beta) - 1.0)
```
- **Pros:** Theoretically motivated for circuit knitting overhead (exponential in cuts); normalized to [0,1]; β controls steepness elegantly
- **Cons:** Departs from paper's polynomial form; harder to interpret
- **Risk:** Medium — may require complete rewrite of methodology section

### Recommendation
Option B is recommended as the default because it:
1. Preserves the paper's polynomial form
2. Maintains scale invariance
3. Is the minimal change that fixes the inversion
4. Is easy to explain in a revision

However, Option C should be investigated in EXP-005 (cost model validation) as it has stronger theoretical motivation for quantum circuit overhead.

- **Decision:** DECIDED — Option A (Fix exponent: cost = γ * β * normalized_cuts or (normalized_cuts)^(1/β))
- **Decided by:** Researcher confirmation
- **Date:** 2026-10-12

---

## DEC-002: Maximum Graph Size for Experiments
- **Status:** PROPOSED — 20 nodes, pending memory feasibility test
- **Blocking:** ACT-018 (full benchmark)
- **Context:** Reviewers R2-C05 and R3-C04 request experiments on larger graphs ("at least 20 qubits"). Current experiments max out at 12 nodes.

- **Options:**

### Option A: Up to 16 Nodes
- **Pros:** Safe for statevector simulation (~64KB state); fast
- **Cons:** May not satisfy reviewers who said "20 qubits"

### Option B: Up to 20 Nodes (RECOMMENDED)
- **Pros:** Directly addresses reviewer request; 20-qubit state = 8MB, manageable
- **Cons:** Full 20-qubit simulation may be slow (but partitioning reduces subgraph size)
- **Note:** Since Dy-Part partitions into subgraphs (e.g., 4-5 qubits each for 20-node graph), the actual simulation cost per VQE call is small. The overhead is in the number of subgraph VQE calls.

### Option C: Up to 30 Nodes
- **Pros:** Strongest scalability demonstration
- **Cons:** Likely infeasible for exact simulation even with partitioning; would need approximate methods

- **Recommendation:** Option B (20 nodes) with a feasibility test: run one configuration at 20 nodes and measure memory/time before committing to full benchmark.
- **Decision:** [PROPOSED — needs feasibility test]
- **Decided by:** —
- **Date:** —

---

## DEC-003: Include METIS Baseline
- **Status:** DECIDED — Option A (pymetis)
- **Blocking:** ACT-016, ACT-018
- **Context:** R3-C03 explicitly asks for comparison to established partitioning methods. METIS is the standard graph partitioner in the literature.

- **Options:**

### Option A: Include METIS (RECOMMENDED)
- **Pros:** Directly addresses reviewer concern; establishes Dy-Part vs established method; shows noise-awareness advantage
- **Cons:** If METIS outperforms, it weakens the paper
- **Mitigation:** Emphasize noise-awareness as orthogonal advantage

### Option B: Skip METIS, Add Only Random Baseline
- **Pros:** Lower risk of unfavorable comparison
- **Cons:** May not satisfy R3; looks like dodging the comparison

- **Recommendation:** Include METIS. Even if METIS outperforms on partition quality, Dy-Part's noise-aware dynamic selection is a distinct contribution.
- **Decision:** DECIDED — Option A (pymetis)
- **Decided by:** Researcher confirmation
- **Date:** 2026-10-12

---

## DEC-004: VQE Optimizer Iterations for Larger Graphs
- **Status:** DEFAULT — 200 iterations (same as current)
- **Blocking:** ACT-018
- **Context:** Current experiments use COBYLA with maxiter=200. For 16-20 node graphs, may need more iterations to converge.

- **Options:**
  - 200 iterations (current default)
  - 300 iterations (50% increase)
  - 500 iterations (conservative)

- **Recommendation:** Start with 200; if convergence analysis shows insufficient, increase to 300.
- **Decision:** 200 (default; reassess after Phase 1 baseline)
- **Decided by:** Default
- **Date:** —

---

## DEC-005: Target Journal If QMI Rejects
- **Status:** CONTINGENCY — Only if needed
- **Blocking:** None currently
- **Context:** Paper is under major revision at Quantum Machine Intelligence (Springer Nature).

- **Options:**
  - IEEE Transactions on Quantum Engineering
  - Physical Review Research
  - Quantum Science and Technology (IOP)
  - arXiv preprint only (if all venues reject)

- **Decision:** [CONTINGENCY — Not needed yet]
- **Decided by:** —
- **Date:** —
