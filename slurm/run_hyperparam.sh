#!/bin/bash
# slurm/run_hyperparam.sh — Phase 2a: Grid search over (alpha, beta, gamma)
# Usage: sbatch slurm/run_hyperparam.sh
#SBATCH --job-name=dypart_hyper
#SBATCH --account=PWSU0516
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=8G
#SBATCH --array=0-199%20
#SBATCH --output=logs/phase2_hyperparam/slurm_%A_%a.out
#SBATCH --error=logs/phase2_hyperparam/slurm_%A_%a.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

echo "=== PHASE 2a: HYPERPARAM SEARCH ==="
echo "Job ID:      ${SLURM_ARRAY_JOB_ID:-local}, Task: ${SLURM_ARRAY_TASK_ID:-0}"
echo "Node:        $(hostname)"
echo "Start:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: ${PROJECT_DIR}"
echo ""

if [ -f /etc/profile.d/lmod.sh ]; then
    source /etc/profile.d/lmod.sh 2>/dev/null || true
fi
module load miniconda3/24.1.2-py310 2>/dev/null || module load miniconda3 2>/dev/null || true

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/apps/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/apps/miniconda3/etc/profile.d/conda.sh"
fi
source activate dypart 2>/dev/null || conda activate dypart 2>/dev/null || true
if [ -d "$HOME/.conda/envs/dypart/bin" ]; then
    export PATH="$HOME/.conda/envs/dypart/bin:$PATH"
fi

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase2_hyperparam"
export DYPART_LOG_LEVEL="INFO"
mkdir -p "$DYPART_LOG_DIR"
mkdir -p "${PROJECT_DIR}/results"

python -u experiments/run_hyperparam_search.py \
  --task-id ${SLURM_ARRAY_TASK_ID:-0} \
  --num-seeds 10 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/hyper_${SLURM_ARRAY_JOB_ID:-local}_${SLURM_ARRAY_TASK_ID:-0}.log"

echo ""
echo "=== TASK ${SLURM_ARRAY_TASK_ID:-0} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
