# Cover Letter for Revised Manuscript Submission

**Date:** October 14, 2026  
**To:** The Editorial Board and Handling Editor  
**Journal:** *Springer Nature Journal of Supercomputing* / *Quantum Information Processing*  
**Manuscript Title:** **Dy-Part: A Dynamic, Noise-Aware Scheduler for Optimizing Hybrid Quantum-Classical Algorithms**  
**Authors:**  
- **Mufakir Qamar Ansari** (Corresponding Author), Department of Computer Science and Engineering, Wright State University, Dayton, OH 45435, USA. Email: `ansari.30@wright.edu`  
- **Mudabir Qamar Ansari**, Department of Information Systems, Lamar University, Beaumont, TX 77705, USA. Email: `mansari2@lamar.edu`  

**Manuscript Category:** Research Article  
**Submission Type:** Revised Submission (Major Revision)  
**Public Code & Data Repository:** [https://github.com/MufakirAnsari/Dy-Part](https://github.com/MufakirAnsari/Dy-Part)  

---

Dear Editor and Reviewers,

We are pleased to resubmit our revised manuscript entitled **"Dy-Part: A Dynamic, Noise-Aware Scheduler for Optimizing Hybrid Quantum-Classical Algorithms"** for consideration for publication as an original research article.

We express our sincere gratitude to the Handling Editor and the five Reviewers for their generous time, thoughtful evaluations, and exceptionally constructive suggestions. The reviewers' insightful critiques have challenged us to conduct a substantially deeper investigation into the physics, statistics, and algorithmic complexity of dynamic workload partitioning on Noisy Intermediate-Scale Quantum (NISQ) architectures.

In response, we undertook a thorough and exhaustive revision campaign. We have substantially extended our empirical evaluations, integrated two new state-of-the-art baselines, conducted rigorous statistical validation of our theoretical cost model, provided formal algorithmic ablation of the ternary search scheduler, and ensured 100% mathematical precision and reproducibility across all data.

The primary enhancements and scientific contributions included in this revised manuscript are summarized below:

1. **Comprehensive 4,160-Run Benchmark Expansion Across Scales and Noise Regimes:**  
   In direct response to Reviewer 2 (REV-R2-05) and Reviewer 3 (REV-R3-04), we expanded our benchmark campaign beyond 12-node prototypes to include 16-node and 20-node 3-regular graphs across eight logarithmically spaced two-qubit gate error rates ($\epsilon_{\text{gate}} \in [3.16 \times 10^{-4}, 3.16 \times 10^{-2}]$) and proportional readout noise ($\epsilon_{\text{readout}} = 10 \cdot \epsilon_{\text{gate}}$). Multi-seed cluster executions encompass 4,160 complete hybrid VQE runs, demonstrating statistically validated advantages for Dy-Part that amplify with problem scale (up to $+4.90\%$ higher approximation ratio on 20 nodes, $p = 6.10 \times 10^{-5}$, Cohen's $d = 1.30$, and up to $d = 1.75$ in severe noise).

2. **Empirical Validation of the Heuristic Cost Model ($R^2 = 0.8227$, $p < 10^{-12}$):**  
   Addressing Reviewer 3 (REV-R3-01), we conducted an exhaustive statistical validation of the theoretical cost formulation across our 1,040 Dy-Part benchmark executions and 2,000 hyperparameter grid-search runs. The composite heuristic cost objective achieves a Pearson correlation of $r = -0.9071$ ($R^2 = 0.8227$, $p < 10^{-12}$) against empirical Max-Cut approximation ratios, confirming that the model captures $82.3\%$ of the variance in physical execution quality. Furthermore, the classical penalty formulation demonstrates near-perfect monotonic rank alignment with physical cut edges ($\rho = 0.9486$).

3. **Inclusion of State-of-the-Art and Industry Baselines (METIS & Random):**  
   In response to Reviewer 3 (REV-R3-03) and Reviewer 5 (REV-R5-02), we implemented and benchmarked the industry-standard multilevel graph partitioning library METIS as well as an unbiased random partitioning baseline across all 4,160 runs. Dy-Part achieves the highest overall mean AR ($0.8489$), outperforming METIS ($0.8448$, $p < 0.05$ in 17/40 configurations), Static ($0.8434$, $p < 0.05$ in 15/40 configurations), and Random ($0.8398$, $p < 0.05$ in 19/40 configurations), with multi-factor ANOVA confirming a statistically significant main effect ($F(3, 4117) = 12.37, p < 10^{-7}$).

4. **Algorithmic Complexity Proofs and Runtime Ablation of Ternary Search:**  
   Responding to Reviewer 3 (REV-R3-02), we proved that the ternary search scheduling algorithm reduces evaluation rounds geometrically to $O(\log |V|)$ trisections, establishing a total worst-case scheduling complexity of $O(\log |V| \cdot (|V| + |E|))$ with partition memoization. In head-to-head empirical ablation across 10 problem dimensions ($|V|=6$ to $30$), ternary search reduces graph evaluations by up to $65.52\%$ with a $1.77\times$ speedup, completing execution within $4.16\text{ ms}$ (mean $1.74\text{ ms}$).

5. **Refactored Energy Normalization and Strict Bound Verification ($\text{AR} \le 1.0$):**  
   In response to Reviewer 2 (REV-R2-04) and Reviewer 3 (REV-R3-05), we completely refactored the VQE energy evaluation pipeline, aligning Hamiltonian sign conventions and ground-state normalization via exact diagonalization. Across all 4,160 experimental runs in our benchmark dataset, all approximation ratios are strictly bounded in $[0.0, 1.0]$ (maximum observed AR $= 0.9936$, with zero instances exceeding 1.0).

6. **High-Performance Computing Rigor (Ohio Supercomputer Center):**  
   All large-scale benchmark simulations and grid-search arrays were executed on the Ohio Supercomputer Center (OSC) Ascend cluster under Project Allocation PWSU0516 (dual AMD EPYC 7763 64-core processors, 128 physical cores per node, 512 GB RAM, SLURM parallel job arrays), guaranteeing complete hardware consistency and reproducibility.

Accompanying this revised manuscript is a comprehensive point-by-point **Response to Reviewers** document addressing every individual query in full detail, cross-referenced with exact section and line numbers in the revised text.

In accordance with open-science principles, the complete source code of Dy-Part, automated test suites, and all benchmark datasets (including the 4,160-run benchmark and 2,000-run hyperparameter grid search) are publicly accessible on GitHub:  
`https://github.com/MufakirAnsari/Dy-Part`

We confirm that this manuscript is original, has not been published previously, is not under consideration for publication elsewhere, and has been approved for resubmission by both authors. There are no competing financial or non-financial conflicts of interest.

We believe the manuscript is now in its strongest possible form and provides a timely, rigorous, and impactful contribution to the hybrid quantum-classical algorithms community. Thank you for your continued editorial guidance.

Sincerely,

**Mufakir Qamar Ansari**, Corresponding Author  
Ph.D. Researcher, Department of Computer Science and Engineering  
Wright State University, Dayton, OH 45435, USA  
Email: `ansari.30@wright.edu`  

**Mudabir Qamar Ansari**, Co-Author  
Department of Information Systems  
Lamar University, Beaumont, TX 77705, USA  
Email: `mansari2@lamar.edu`  
