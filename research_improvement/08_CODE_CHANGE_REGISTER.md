# Code Change Register

## COD-001: Fix Graph Partitioner Determinism
- **File:** `vqe_framework/utils/graph_partitioner.py`
- **Issue:** ISS-006
- **Current behavior:** `set.pop()` gives arbitrary node order
- **Desired behavior:** Deterministic partitioning
- **Change:**
  - Line 30: `nodes_to_assign = set(graph.nodes())` → `nodes_to_assign = sorted(graph.nodes())`
  - Line 36: `seed_node = nodes_to_assign.pop()` → use `nodes_to_assign.pop(0)` (list pop from front)
  - Change the `while` loop to operate on a list instead of a set
- **Side effects:** May change partition results compared to old runs (different seed node selection)
- **Tests:** Same graph + n_sub → same partition across 100 runs
- **Rollback:** Revert to `set()`

## COD-002: Fix Classical Cost Formula (Inverted Beta)
- **File:** `vqe_framework/cost_model.py`
- **Issue:** ISS-004
- **Current behavior (L61-64):**
  ```python
  normalized_cuts = num_cuts / total_edges
  return self.gamma * (normalized_cuts ** self.beta)
  ```
  With `normalized_cuts ∈ [0,1]`, higher β → lower cost (inverted)
- **Desired behavior:** Higher β should penalize more cuts more severely
- **Proposed fix option A:** Use raw count, not normalized:
  ```python
  return self.gamma * (num_cuts ** self.beta)
  ```
  Problem: not scale-invariant across graph sizes.
- **Proposed fix option B (RECOMMENDED):** Keep normalization but invert the exponent meaning:
  ```python
  return self.gamma * (normalized_cuts ** (1.0 / self.beta))
  ```
  Now β>1 makes cost increase faster with cuts.
- **Proposed fix option C:** Entirely different formulation matching paper intent:
  ```python
  # Exponential penalty (theoretically motivated for circuit knitting)
  return self.gamma * (np.exp(self.beta * normalized_cuts) - 1.0) / (np.exp(self.beta) - 1.0)
  ```
  Normalized to [0,1] range. Higher β → steeper exponential penalty.
- **Decision required:** DEC-001 — Which formula? Need researcher input.
- **Tests:** `test_beta_exponent_effect` must be INVERTED to check higher β → higher cost
- **Rollback:** Revert formula

## COD-003: Fix AR Calculation
- **File:** `experiments/run_final_benchmark.py` (and all experiment scripts)
- **Issue:** ISS-003, ISS-009
- **Current behavior (L58):**
  ```python
  approximation_ratio = final_energy / true_min_energy
  ```
  Both negative; if final_energy < true_min_energy → AR > 1.0
- **Desired behavior:** AR ∈ [0,1] using standard MaxCut convention
- **Proposed fix:**
  ```python
  # Convert ZZ energy to cut value: C = (|E| - E)/2
  total_edges = graph.number_of_edges()
  cut_value_vqe = (total_edges - final_energy) / 2.0
  cut_value_exact = (total_edges - true_min_energy) / 2.0
  approximation_ratio = cut_value_vqe / cut_value_exact
  # Clamp for safety (noise can still cause slight violations)
  approximation_ratio = min(approximation_ratio, 1.0)
  ```
- **Tests:** AR on noiseless 4-node graph matches hand-computed value; AR ≤ 1.0 always
- **Rollback:** Revert formula

## COD-004: Implement Ternary Search in Scheduler
- **File:** `vqe_framework/scheduler.py`
- **Issue:** ISS-001
- **Current behavior:** Linear loop L73
- **Desired behavior:** O(log|V|) ternary search when cost is unimodal; exhaustive fallback
- **Proposed implementation:**
  ```python
  def find_optimal_partition(self, graph, min_subgraph_size=2, force_exhaustive=False):
      if force_exhaustive or graph.number_of_nodes() <= 6:
          return self._exhaustive_search(graph, min_subgraph_size)
      
      # Ternary search
      lo = min_subgraph_size
      hi = graph.number_of_nodes()
      while hi - lo > 2:
          m1 = lo + (hi - lo) // 3
          m2 = hi - (hi - lo) // 3
          cost_m1 = self._evaluate_cost(graph, m1)
          cost_m2 = self._evaluate_cost(graph, m2)
          if cost_m1 < cost_m2:
              hi = m2
          else:
              lo = m1
      # Final linear scan on small interval
      return self._exhaustive_search_range(graph, lo, hi)
  ```
- **Tests:** Ternary search agrees with exhaustive on 100 random graphs; wall-clock time scales O(log N)
- **Rollback:** `force_exhaustive=True`

## COD-005: Upgrade Logging for OSC
- **File:** `vqe_framework/logging_config.py`
- **Issue:** ISS-038
- **Current behavior:** Console-only StreamHandler
- **Desired behavior:** Dual file + console logging; configurable via env vars
- **Proposed implementation:**
  ```python
  import os, logging, sys
  from datetime import datetime

  def setup_logging(level=None, log_dir=None):
      logger = logging.getLogger("DyPart")
      if logger.handlers:
          return logger
      
      level = level or os.environ.get("DYPART_LOG_LEVEL", "INFO")
      log_dir = log_dir or os.environ.get("DYPART_LOG_DIR", "logs")
      
      logger.setLevel(getattr(logging, level.upper()))
      formatter = logging.Formatter(
          '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
          datefmt='%Y-%m-%d %H:%M:%S'
      )
      
      # Console handler
      console = logging.StreamHandler(sys.stdout)
      console.setFormatter(formatter)
      logger.addHandler(console)
      
      # File handler
      os.makedirs(log_dir, exist_ok=True)
      job_id = os.environ.get("SLURM_JOB_ID", "local")
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_file = os.path.join(log_dir, f"dypart_{job_id}_{timestamp}.log")
      file_handler = logging.FileHandler(log_file)
      file_handler.setFormatter(formatter)
      logger.addHandler(file_handler)
      
      logger.info(f"Logging initialized: {log_file}")
      return logger
  ```
- **Tests:** Log file is created; both console and file receive messages
- **Rollback:** Revert to original

## COD-006: Create Comprehensive Experiment Runner
- **File:** NEW `experiments/run_corrected_benchmark.py`
- **Issue:** ISS-002, ISS-008
- **Design principles:**
  - Accept all parameters via command-line args (for SLURM array jobs)
  - Log every single measurement to both CSV and log file
  - Separate scheduler timing from VQE timing
  - Support Dy-Part, Static, METIS, and Random baselines
  - Handle errors gracefully with full traceback logging
  - Write incremental results (crash-safe)
- **See 07_EXPERIMENT_PROTOCOLS.md for full specification**

## COD-007: Create Hyperparameter Grid Search Script
- **File:** NEW `experiments/run_hyperparam_search.py`
- **Issue:** ISS-005
- **Design:** Accept (α, β, γ) as CLI args; log all results; OSC array-job compatible

## COD-008: Implement METIS Baseline
- **File:** NEW `vqe_framework/utils/metis_partitioner.py`
- **Issue:** ISS-007
- **Design:** Wrapper around `pymetis` or `networkx.algorithms.community`
- **Dependencies:** May need `python-metis` package in environment

## COD-009: Fix qpu_interface Print Statement
- **File:** `vqe_framework/qpu_interface.py`
- **Issue:** Engineering quality
- **Current (L58):** `print(f"Noise Model Created: ...")` — bare print
- **Fix:** Replace with `logger.info(...)`
