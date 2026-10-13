#!/bin/bash
# slurm/run_hyperparam_array.sh — 50-Worker Parallel Hyperparameter Grid Search on OSC (ACT-014)
# Usage: sbatch slurm/run_hyperparam_array.sh
#SBATCH --job-name=dypart_hp_arr
#SBATCH --account=PWSU0516
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --array=0-49
#SBATCH --output=logs/phase2_hyperparam/slurm_hp_%A_%a.out
#SBATCH --error=logs/phase2_hyperparam/slurm_hp_%A_%a.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

TASK_ID="${SLURM_ARRAY_TASK_ID:-0}"

# 50 workers over 200 configurations -> exactly 4 configurations per worker
CONFIGS_PER_TASK=4
START_CFG=$(( TASK_ID * CONFIGS_PER_TASK ))
END_CFG=$(( START_CFG + CONFIGS_PER_TASK ))
OUTPUT_CSV="results/hyperparam_part_${TASK_ID}.csv"

echo "=== PHASE 2: HYPERPARAMETER GRID SEARCH (50-WORKER HIGH-SPEED) ==="
echo "Array Job ID: ${SLURM_ARRAY_JOB_ID:-local}"
echo "Task ID:      ${TASK_ID}"
echo "Configs:      [${START_CFG}, ${END_CFG}) (4 configs x 10 seeds = 40 runs)"
echo "Output CSV:   ${OUTPUT_CSV}"
echo "Node:         $(hostname)"
echo "Start:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
export DYPART_LOG_LEVEL="DEBUG"
mkdir -p "$DYPART_LOG_DIR" results

# Ensure qiskit-algorithms (<0.4.0) compatibility with qiskit 1.1.0
pip install "qiskit-algorithms>=0.3.0,<0.4.0" 2>/dev/null || true

echo "--- Running Hyperparameter Worker ${TASK_ID} (Configs ${START_CFG} to ${END_CFG}) ---"
python -u experiments/run_hyperparam_search.py \
    --config-start "${START_CFG}" \
    --config-end "${END_CFG}" \
    --seeds 10 \
    --nodes 10 \
    --noise 0.005 \
    --output "${OUTPUT_CSV}" \
    2>&1 | tee "${DYPART_LOG_DIR}/hyperparam_part_${TASK_ID}_${SLURM_ARRAY_JOB_ID:-local}.log"

echo ""
echo "=== WORKER ${TASK_ID} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
