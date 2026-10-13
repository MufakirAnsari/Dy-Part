# OSC SLURM Deployment & Logging Protocols

## 1. Environment Setup Script

```bash
#!/bin/bash
# slurm/env_setup.sh — Run once to set up the OSC conda environment
#SBATCH --job-name=dypart_env_setup
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/env_setup_%j.out
#SBATCH --error=logs/env_setup_%j.err

set -euo pipefail

echo "=== DY-PART ENVIRONMENT SETUP ==="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

module load miniconda3
conda create -n dypart python=3.10 -y
conda activate dypart

pip install qiskit==1.1.0
pip install qiskit-aer==0.14.0
pip install qiskit-algorithms==0.3.0
pip install numpy pandas matplotlib seaborn scipy networkx
pip install pymetis  # For METIS baseline

# Install our framework in editable mode
cd $HOME/dy-part/Dy-Part-main
pip install -e .

echo "=== ENVIRONMENT READY ==="
conda list
python -c "import qiskit; print(f'Qiskit version: {qiskit.__version__}')"
python -c "import vqe_framework; print('vqe_framework imported successfully')"
```

## 2. Master Submission Script

```bash
#!/bin/bash
# slurm/submit_all.sh — Submit the complete experimental pipeline from local terminal
# Usage: ssh user@pitzer.osc.edu "cd ~/dy-part && bash slurm/submit_all.sh"

set -euo pipefail

LOGDIR="$HOME/dy-part/logs"
mkdir -p $LOGDIR/{phase1_baseline,phase2_hyperparam,phase2_benchmark,phase3_ablation}

echo "=== DY-PART: SUBMITTING ALL EXPERIMENTS ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Phase 1: Baseline reproduction
JOB_BASELINE=$(sbatch --parsable slurm/run_baseline.sh)
echo "Submitted baseline reproduction: Job $JOB_BASELINE"

# Phase 2: Hyperparameter grid search (depends on Phase 1 completing)
JOB_HYPER=$(sbatch --parsable --dependency=afterok:$JOB_BASELINE slurm/run_hyperparam.sh)
echo "Submitted hyperparam search: Job $JOB_HYPER (after $JOB_BASELINE)"

# Phase 2: Full benchmark (depends on hyperparam search)
JOB_BENCH=$(sbatch --parsable --dependency=afterok:$JOB_HYPER slurm/run_benchmark.sh)
echo "Submitted full benchmark: Job $JOB_BENCH (after $JOB_HYPER)"

# Phase 3: Ablation studies (depends on benchmark)
JOB_ABLATION=$(sbatch --parsable --dependency=afterok:$JOB_BENCH slurm/run_ablation.sh)
echo "Submitted ablations: Job $JOB_ABLATION (after $JOB_BENCH)"

echo ""
echo "=== PIPELINE SUBMITTED ==="
echo "Dependency chain: $JOB_BASELINE → $JOB_HYPER → $JOB_BENCH → $JOB_ABLATION"
echo "Monitor: squeue -u $USER"
echo "Logs: $LOGDIR/"
```

## 3. Baseline Reproduction Script

```bash
#!/bin/bash
# slurm/run_baseline.sh — Phase 1: Reproduce original results
#SBATCH --job-name=dypart_baseline
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=16G
#SBATCH --output=logs/phase1_baseline/slurm_%j.out
#SBATCH --error=logs/phase1_baseline/slurm_%j.err

set -euo pipefail

echo "=== PHASE 1: BASELINE REPRODUCTION ==="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Working directory: $(pwd)"

module load miniconda3
conda activate dypart

export DYPART_LOG_DIR="$HOME/dy-part/logs/phase1_baseline"
export DYPART_LOG_LEVEL="DEBUG"

cd $HOME/dy-part/Dy-Part-main

echo "--- Running baseline reproduction ---"
python -u experiments/run_final_benchmark.py \
  2>&1 | tee ${DYPART_LOG_DIR}/baseline_${SLURM_JOB_ID}.log

echo "=== PHASE 1 COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Exit code: $?"
```

## 4. Hyperparameter Grid Search (Array Job)

```bash
#!/bin/bash
# slurm/run_hyperparam.sh — Phase 2a: Grid search over (α, β, γ)
#SBATCH --job-name=dypart_hyper
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=8G
#SBATCH --array=0-199%20
#SBATCH --output=logs/phase2_hyperparam/slurm_%A_%a.out
#SBATCH --error=logs/phase2_hyperparam/slurm_%A_%a.err

set -euo pipefail

echo "=== PHASE 2a: HYPERPARAM SEARCH ==="
echo "Job ID: ${SLURM_ARRAY_JOB_ID}, Task: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

module load miniconda3
conda activate dypart

export DYPART_LOG_DIR="$HOME/dy-part/logs/phase2_hyperparam"
export DYPART_LOG_LEVEL="INFO"

cd $HOME/dy-part/Dy-Part-main

# The Python script decodes SLURM_ARRAY_TASK_ID into (α, β, γ) tuple
python -u experiments/run_hyperparam_search.py \
  --task-id ${SLURM_ARRAY_TASK_ID} \
  --num-seeds 10 \
  --output-dir $HOME/dy-part/results \
  2>&1 | tee ${DYPART_LOG_DIR}/hyper_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log

echo "=== TASK ${SLURM_ARRAY_TASK_ID} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## 5. Full Benchmark (Array Job)

```bash
#!/bin/bash
# slurm/run_benchmark.sh — Phase 2b: Full corrected benchmark
#SBATCH --job-name=dypart_bench
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --mem=32G
#SBATCH --array=0-49%10
#SBATCH --output=logs/phase2_benchmark/slurm_%A_%a.out
#SBATCH --error=logs/phase2_benchmark/slurm_%A_%a.err

set -euo pipefail

echo "=== PHASE 2b: FULL BENCHMARK ==="
echo "Job ID: ${SLURM_ARRAY_JOB_ID}, Task: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Available memory: $(free -h | head -2)"

module load miniconda3
conda activate dypart

export DYPART_LOG_DIR="$HOME/dy-part/logs/phase2_benchmark"
export DYPART_LOG_LEVEL="INFO"

cd $HOME/dy-part/Dy-Part-main

# Each task handles one (graph_size, noise_level) pair across all seeds & methods
python -u experiments/run_corrected_benchmark.py \
  --task-id ${SLURM_ARRAY_TASK_ID} \
  --num-seeds 30 \
  --output-dir $HOME/dy-part/results \
  2>&1 | tee ${DYPART_LOG_DIR}/bench_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log

echo "=== TASK ${SLURM_ARRAY_TASK_ID} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## 6. Local Terminal Workflow

```bash
# === ONE-TIME SETUP ===
# Set your OSC credentials
export OSC_USER="your_username"
export OSC_HOST="pitzer.osc.edu"

# Create remote directory structure
ssh ${OSC_USER}@${OSC_HOST} "mkdir -p ~/dy-part/{slurm,logs,results}"

# Sync project to OSC
rsync -avz --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' \
  ./Dy-Part-main/ ${OSC_USER}@${OSC_HOST}:~/dy-part/Dy-Part-main/

# Sync SLURM scripts
rsync -avz ./research_improvement/slurm/ ${OSC_USER}@${OSC_HOST}:~/dy-part/slurm/

# Setup environment (one-time)
ssh ${OSC_USER}@${OSC_HOST} "cd ~/dy-part && sbatch slurm/env_setup.sh"

# === EXPERIMENT EXECUTION ===
# Submit full pipeline
ssh ${OSC_USER}@${OSC_HOST} "cd ~/dy-part && bash slurm/submit_all.sh"

# Monitor jobs
ssh ${OSC_USER}@${OSC_HOST} "squeue -u ${OSC_USER} --format='%.18i %.9P %.30j %.8T %.10M %.6D %R'"

# Check specific job output
ssh ${OSC_USER}@${OSC_HOST} "tail -50 ~/dy-part/logs/phase2_benchmark/slurm_12345_0.out"

# === RESULTS RETRIEVAL ===
# Pull results and logs back to local
rsync -avz ${OSC_USER}@${OSC_HOST}:~/dy-part/results/ ./results_osc/
rsync -avz ${OSC_USER}@${OSC_HOST}:~/dy-part/logs/ ./logs_osc/

# Quick results check
ssh ${OSC_USER}@${OSC_HOST} "wc -l ~/dy-part/results/corrected_benchmark.csv"
ssh ${OSC_USER}@${OSC_HOST} "head -5 ~/dy-part/results/corrected_benchmark.csv"
```

## 7. Logging Specification

Every experiment logs the following to BOTH console (captured by SLURM) and a dedicated `.log` file:

### Startup metadata
```
=== EXPERIMENT START ===
Timestamp: 2026-10-12T14:00:00Z
SLURM Job ID: 12345
SLURM Array Task ID: 7
Hostname: p0042.ten.osc.edu
Python: 3.10.14
Qiskit: 1.1.0
Qiskit-Aer: 0.14.0
Working Directory: /users/PAS1234/user/dy-part/Dy-Part-main
Git Commit: abc1234 (if available)
```

### Per-experiment configuration
```
--- Experiment Config ---
Method: dypart
Graph: 12 nodes, 18 edges, 3-regular, seed=42
Noise: gate_error=5.00e-03, readout_error=5.00e-02
Cost Model: alpha=0.50, beta=1.50, gamma=1.00
Optimizer: COBYLA(maxiter=200)
VQE Seed: 123
Shots: 8192
```

### Per-iteration (DEBUG level)
```
[DEBUG] VQE Iteration 47: energy=-8.4321, params=[0.12, 0.45, ...]
```

### Per-run summary
```
--- Run Complete ---
Method: dypart
Chosen n_sub: 4
Num cuts: 6
Final energy: -8.2100
True energy: -10.0000
Cut value (VQE): 9.105
Cut value (exact): 10.000
Approximation Ratio: 0.9105
Scheduler time: 0.23s
VQE time: 45.67s
Total time: 45.90s
```

### Errors (full traceback)
```
[ERROR] Run failed: Method=dypart, Nodes=20, Noise=1e-02, Seed=15
Traceback (most recent call last):
  File "run_corrected_benchmark.py", line 89, in run_single
    result = vqe.run(partition_plan)
  ...
MemoryError: Unable to allocate 2.0 GiB for array
```

### Completion summary
```
=== EXPERIMENT COMPLETE ===
Total runs: 30
Successful: 29
Failed: 1
Output CSV: results/corrected_benchmark_task7.csv
Log file: logs/phase2_benchmark/bench_12345_7.log
End: 2026-10-12T16:30:00Z
Wall time: 2h 30m
```
