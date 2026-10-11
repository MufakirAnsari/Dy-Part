#!/bin/bash
# slurm/submit_all.sh — Submit the complete experimental pipeline
# Usage: ssh user@pitzer.osc.edu 'cd ~/dy-part/Dy-Part-main && bash slurm/submit_all.sh'
# Or locally: bash slurm/submit_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOGDIR="${PROJECT_DIR}/logs"
PIPELINE_LOG="${LOGDIR}/pipeline_submission.log"

# Create all log directories
mkdir -p "${LOGDIR}/"/{phase1_baseline,phase2_hyperparam,phase2_benchmark,phase3_ablation}

echo "=== DY-PART: SUBMITTING ALL EXPERIMENTS ===" | tee "$PIPELINE_LOG"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$PIPELINE_LOG"
echo "Project dir: $PROJECT_DIR" | tee -a "$PIPELINE_LOG"
echo "Log dir: $LOGDIR" | tee -a "$PIPELINE_LOG"
echo "" | tee -a "$PIPELINE_LOG"

# Pre-flight checks
echo "--- Pre-flight checks ---" | tee -a "$PIPELINE_LOG"
if ! command -v sbatch &> /dev/null; then
    echo "ERROR: sbatch not found. Are you on an OSC login node?" | tee -a "$PIPELINE_LOG"
    exit 1
fi

module load miniconda3/24.1.2-py310 2>/dev/null || true
if ! conda info --envs 2>/dev/null | grep -q dypart; then
    echo "ERROR: conda environment 'dypart' not found." | tee -a "$PIPELINE_LOG"
    echo "Run: sbatch slurm/env_setup.sh" | tee -a "$PIPELINE_LOG"
    exit 1
fi
echo "Pre-flight checks passed." | tee -a "$PIPELINE_LOG"
echo "" | tee -a "$PIPELINE_LOG"

# Phase 1: Baseline reproduction
echo "--- Submitting Phase 1: Baseline Reproduction ---" | tee -a "$PIPELINE_LOG"
JOB_BASELINE=$(sbatch --parsable "${SCRIPT_DIR}/run_baseline.sh")
echo "  Job ID: $JOB_BASELINE" | tee -a "$PIPELINE_LOG"

# Phase 2a: Hyperparameter grid search (depends on Phase 1)
echo "--- Submitting Phase 2a: Hyperparameter Search ---" | tee -a "$PIPELINE_LOG"
JOB_HYPER=$(sbatch --parsable --dependency=afterok:$JOB_BASELINE "${SCRIPT_DIR}/run_hyperparam.sh")
echo "  Job ID: $JOB_HYPER (after $JOB_BASELINE)" | tee -a "$PIPELINE_LOG"

# Phase 2b: Full benchmark (depends on hyperparam search)
echo "--- Submitting Phase 2b: Full Benchmark ---" | tee -a "$PIPELINE_LOG"
JOB_BENCH=$(sbatch --parsable --dependency=afterok:$JOB_HYPER "${SCRIPT_DIR}/run_benchmark.sh")
echo "  Job ID: $JOB_BENCH (after $JOB_HYPER)" | tee -a "$PIPELINE_LOG"

# Phase 3: Ablation studies (depends on benchmark)
echo "--- Submitting Phase 3: Ablation Studies ---" | tee -a "$PIPELINE_LOG"
JOB_ABLATION=$(sbatch --parsable --dependency=afterok:$JOB_BENCH "${SCRIPT_DIR}/run_ablation.sh")
echo "  Job ID: $JOB_ABLATION (after $JOB_BENCH)" | tee -a "$PIPELINE_LOG"

# Summary
echo "" | tee -a "$PIPELINE_LOG"
echo "=== PIPELINE SUBMITTED SUCCESSFULLY ===" | tee -a "$PIPELINE_LOG"
echo "Dependency chain:" | tee -a "$PIPELINE_LOG"
echo "  Phase 1 (Baseline):   $JOB_BASELINE" | tee -a "$PIPELINE_LOG"
echo "  Phase 2a (Hyper):     $JOB_HYPER -> after $JOB_BASELINE" | tee -a "$PIPELINE_LOG"
echo "  Phase 2b (Benchmark): $JOB_BENCH -> after $JOB_HYPER" | tee -a "$PIPELINE_LOG"
echo "  Phase 3 (Ablation):   $JOB_ABLATION -> after $JOB_BENCH" | tee -a "$PIPELINE_LOG"
echo "" | tee -a "$PIPELINE_LOG"
echo "Monitor:  squeue -u \$USER" | tee -a "$PIPELINE_LOG"
echo "Cancel:   scancel $JOB_BASELINE $JOB_HYPER $JOB_BENCH $JOB_ABLATION" | tee -a "$PIPELINE_LOG"
echo "Logs:     $LOGDIR/" | tee -a "$PIPELINE_LOG"
echo "Pipeline log: $PIPELINE_LOG" | tee -a "$PIPELINE_LOG"
