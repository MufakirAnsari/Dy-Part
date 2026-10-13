# Final Acceptance Checklist

This checklist must be fully satisfied before submission.

## A. P0-Critical Issues Resolved
- [ ] **ISS-001:** Ternary search implemented in `scheduler.py`; O(log|V|) claim verified by TEST-004
- [ ] **ISS-002:** Dy-Part outperforms static baseline in corrected benchmark with p<0.05
- [ ] **ISS-003:** AR ∈ [0,1] for ALL data points in corrected benchmark; verified by TEST-003

## B. P1-Major Issues Resolved
- [ ] **ISS-004:** Classical cost formula corrected; higher β → higher cost; verified by TEST-002
- [ ] **ISS-005:** Hyperparameters re-tuned with corrected cost model; selected α,β,γ documented
- [ ] **ISS-006:** Graph partitioner is fully deterministic; verified by TEST-001
- [ ] **ISS-007:** At least one literature baseline (METIS) included in experiments
- [ ] **ISS-008:** Experiments include 16-node and 20-node graphs
- [ ] **ISS-010:** All statistical significance claims supported by actual test results
- [ ] **ISS-011:** Every text claim matches plotted/tabulated data
- [ ] **ISS-035:** Cumulative advantage tested with global statistical test (ANOVA or similar)
- [ ] **ISS-039:** SLURM scripts created and tested on OSC

## C. P2-Important Issues Resolved
- [ ] **ISS-009:** Hamiltonian convention documented; AR calculation consistent
- [ ] **ISS-012:** AR < 0.5 cases explained or resolved in text
- [ ] **ISS-013:** SWAP gate limitation discussed in manuscript
- [ ] **ISS-014:** Shot overhead acknowledged in manuscript
- [ ] **ISS-015:** Algorithm 1 explained in prose
- [ ] **ISS-016:** Overclaiming removed; claims qualified to tested instances
- [ ] **ISS-017:** Quantum/classical boundary discussed
- [ ] **ISS-018:** VQE runtime claim corrected
- [ ] **ISS-019:** VQE vs QAOA choice justified
- [ ] **ISS-020:** Figure 4 has error bars
- [ ] **ISS-021:** α=0.9 outlier explained
- [ ] **ISS-034:** SPSA/ansatz limitation retained
- [ ] **ISS-036:** Runtime breakdown uses measured data
- [ ] **ISS-037:** Executor variants consolidated (optional but recommended)
- [ ] **ISS-038:** Dual file+console logging implemented
- [ ] **ISS-040:** requirements.txt and environment.yml created

## D. P3-Minor Issues Resolved
- [ ] **ISS-022:** Noise range in text matches experiments
- [ ] **ISS-023:** Missing citation added
- [ ] **ISS-024:** |V| defined before first use
- [ ] **ISS-025:** Spaces before citations fixed
- [ ] **ISS-026:** Quantum advantage overclaim removed
- [ ] **ISS-027:** Error types specified in abstract
- [ ] **ISS-028:** Hardware claims qualified
- [ ] **ISS-029:** All hyperrefs/cross-refs working
- [ ] **ISS-030:** Gradient-based optimizers mentioned
- [ ] **ISS-031:** Repeated sentences removed
- [ ] **ISS-032:** Classical optimizer named (COBYLA)
- [ ] **ISS-033:** Classical baseline correctly labeled
- [ ] **ISS-041:** |V+E| → (|V| + |E|) notation fixed
- [ ] **ISS-042:** Figure 6 regenerated with wider range

## E. Code Quality
- [ ] All unit tests pass (TEST-001 through TEST-007)
- [ ] Integration test passes (TEST-008)
- [ ] No Python warnings or deprecation notices
- [ ] All print() statements replaced with logger calls
- [ ] setup.py in correct location (project root)
- [ ] Git repository initialized with clean commit history

## F. Experiment Quality
- [ ] Benchmark output validated (TEST-010)
- [ ] All figures match source data (TEST-011)
- [ ] All text claims match data (TEST-012)
- [ ] 30 seeds per configuration (statistical power)
- [ ] All experiments logged to files on OSC

## G. Manuscript Quality
- [ ] LaTeX builds without errors (TEST-013)
- [ ] No undefined references
- [ ] No broken cross-references
- [ ] All figures high-quality and readable
- [ ] Bibliography complete and correctly formatted
- [ ] Reviewer response document complete
- [ ] Rebuttal letter addresses all 37 reviewer comments

## H. Submission Package
- [ ] Revised manuscript PDF
- [ ] Point-by-point reviewer response document
- [ ] Supplementary materials (if any)
- [ ] Source code archive (if required by journal)
- [ ] Cover letter to editor
