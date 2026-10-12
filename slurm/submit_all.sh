#!/bin/bash
# slurm/submit_all.sh — Submit the complete experimental pipeline
# Usage:
#   bash slurm/submit_all.sh
#   bash slurm/submit_all.sh --account=PAS1234
# Or via SSH from local machine:
#   ssh mufakiransari@ascend.osc.edu "cd ~/Dy-Part && bash slurm/submit_all.sh"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${DYPART_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"
LOGDIR="${PROJECT_DIR}/logs"
PIPELINE_LOG="${LOGDIR}/pipeline_submission.log"

mkdir -p "${LOGDIR}/"{phase1_baseline,phase2_hyperparam,phase2_benchmark,phase3_ablation}

# Parse optional arguments
SBATCH_EXTRA_ARGS=""
for arg in "$@"; do
    case $arg in
        --account=*)
            SBATCH_EXTRA_ARGS="${SBATCH_EXTRA_ARGS} ${arg}"
            shift
            ;;
        *)
            ;;
    esac
done

if [ -n "${SLURM_ACCOUNT:-}" ] && [[ "$SBATCH_EXTRA_ARGS" != *"--account="* ]]; then
    SBATCH_EXTRA_ARGS="${SBATCH_EXTRA_ARGS} --account=${SLURM_ACCOUNT}"
fi

echo "======================================================" | tee "$PIPELINE_LOG"
echo "  DY-PART: SUBMITTING ALL EXPERIMENTAL JOBS           " | tee -a "$PIPELINE_LOG"
echo "======================================================" | tee -a "$PIPELINE_LOG"
echo "Timestamp:    $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$PIPELINE_LOG"
echo "Project dir:  ${PROJECT_DIR}" | tee -a "$PIPELINE_LOG"
echo "Log dir:      ${LOGDIR}" | tee -a "$PIPELINE_LOG"
if [ -n "$SBATCH_EXTRA_ARGS" ]; then
    echo "Extra args:  ${SBATCH_EXTRA_ARGS}" | tee -a "$PIPELINE_LOG"
fi
echo "" | tee -a "$PIPELINE_LOG"

# Pre-flight checks
echo "--- Pre-flight checks ---" | tee -a "$PIPELINE_LOG"
if ! command -v sbatch &> /dev/null; then
    echo "ERROR: 'sbatch' command not found." | tee -a "$PIPELINE_LOG"
    echo "This script must be executed on an OSC cluster (Ascend, Pitzer, Owens)." | tee -a "$PIPELINE_LOG"
    exit 1
fi

if [ -f /etc/profile.d/lmod.sh ]; then
    source /etc/profile.d/lmod.sh 2>/dev/null || true
fi
module load miniconda3 2>/dev/null || module load miniconda3/24.1.2-py310 2>/dev/null || true

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

if ! conda info --envs 2>/dev/null | grep -q '\bdypart\b'; then
    echo "WARNING: Conda environment 'dypart' not found yet." | tee -a "$PIPELINE_LOG"
    echo "Submitting environment setup job first..." | tee -a "$PIPELINE_LOG"
    JOB_ENV=$(sbatch --parsable ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/env_setup.sh")
    echo "Submitted env_setup: Job ID ${JOB_ENV}" | tee -a "$PIPELINE_LOG"
    ENV_DEP="--dependency=afterok:${JOB_ENV}"
else
    echo "Conda environment 'dypart' verified." | tee -a "$PIPELINE_LOG"
    ENV_DEP=""
fi

echo "Pre-flight checks passed." | tee -a "$PIPELINE_LOG"
echo "" | tee -a "$PIPELINE_LOG"

# Phase 1: Baseline reproduction
echo "--- Submitting Phase 1: Baseline Reproduction ---" | tee -a "$PIPELINE_LOG"
if [ -n "${ENV_DEP}" ]; then
    JOB_BASELINE=$(sbatch --parsable ${ENV_DEP} ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/run_baseline.sh")
else
    JOB_BASELINE=$(sbatch --parsable ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/run_baseline.sh")
fi
echo "  Job ID: ${JOB_BASELINE}" | tee -a "$PIPELINE_LOG"

# Phase 2a: Hyperparameter grid search (depends on Phase 1)
echo "--- Submitting Phase 2a: Hyperparameter Search ---" | tee -a "$PIPELINE_LOG"
JOB_HYPER=$(sbatch --parsable --dependency=afterok:${JOB_BASELINE} ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/run_hyperparam.sh")
echo "  Job ID: ${JOB_HYPER} (after ${JOB_BASELINE})" | tee -a "$PIPELINE_LOG"

# Phase 2b: Full benchmark (depends on hyperparam search)
echo "--- Submitting Phase 2b: Full Benchmark ---" | tee -a "$PIPELINE_LOG"
JOB_BENCH=$(sbatch --parsable --dependency=afterok:${JOB_HYPER} ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/run_benchmark.sh")
echo "  Job ID: ${JOB_BENCH} (after ${JOB_HYPER})" | tee -a "$PIPELINE_LOG"

# Phase 3: Ablation studies (depends on benchmark)
echo "--- Submitting Phase 3: Ablation Studies ---" | tee -a "$PIPELINE_LOG"
JOB_ABLATION=$(sbatch --parsable --dependency=afterok:${JOB_BENCH} ${SBATCH_EXTRA_ARGS} "${SCRIPT_DIR}/run_ablation.sh")
echo "  Job ID: ${JOB_ABLATION} (after ${JOB_BENCH})" | tee -a "$PIPELINE_LOG"

# Summary
echo "" | tee -a "$PIPELINE_LOG"
echo "======================================================" | tee -a "$PIPELINE_LOG"
echo "  PIPELINE SUBMITTED SUCCESSFULLY                     " | tee -a "$PIPELINE_LOG"
echo "======================================================" | tee -a "$PIPELINE_LOG"
echo "Dependency chain:" | tee -a "$PIPELINE_LOG"
echo "  Phase 1 (Baseline):   ${JOB_BASELINE}" | tee -a "$PIPELINE_LOG"
echo "  Phase 2a (Hyper):     ${JOB_HYPER} -> after ${JOB_BASELINE}" | tee -a "$PIPELINE_LOG"
echo "  Phase 2b (Benchmark): ${JOB_BENCH} -> after ${JOB_HYPER}" | tee -a "$PIPELINE_LOG"
echo "  Phase 3 (Ablation):   ${JOB_ABLATION} -> after ${JOB_BENCH}" | tee -a "$PIPELINE_LOG"
echo "" | tee -a "$PIPELINE_LOG"
echo "Monitor queue:  squeue -u \$USER" | tee -a "$PIPELINE_LOG"
echo "Cancel all:     scancel ${JOB_BASELINE} ${JOB_HYPER} ${JOB_BENCH} ${JOB_ABLATION}" | tee -a "$PIPELINE_LOG"
echo "Logs root:      ${LOGDIR}/" | tee -a "$PIPELINE_LOG"
echo "Pipeline log:   ${PIPELINE_LOG}" | tee -a "$PIPELINE_LOG"
