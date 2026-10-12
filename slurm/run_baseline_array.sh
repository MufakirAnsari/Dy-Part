#!/bin/bash
# slurm/run_baseline_array.sh — Parallel Phase 1 Baseline Reproduction on OSC
# Usage: sbatch slurm/run_baseline_array.sh
#SBATCH --job-name=dypart_b_arr
#SBATCH --account=PWSU0516
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=16G
#SBATCH --array=0-3
#SBATCH --output=logs/phase1_baseline/slurm_arr_%A_%a.out
#SBATCH --error=logs/phase1_baseline/slurm_arr_%A_%a.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

TASK_ID="${SLURM_ARRAY_TASK_ID:-0}"

# Worker 0: Seeds 10 to 15 (exclusive) -> 10, 11, 12, 13, 14
# Worker 1: Seeds 15 to 20 (exclusive) -> 15, 16, 17, 18, 19
# Worker 2: Seeds 20 to 25 (exclusive) -> 20, 21, 22, 23, 24
# Worker 3: Seeds 25 to 30 (exclusive) -> 25, 26, 27, 28, 29
START_SEED=$(( 10 + TASK_ID * 5 ))
END_SEED=$(( START_SEED + 5 ))
OUTPUT_CSV="results/baseline_part_${TASK_ID}.csv"

echo "=== PHASE 1: PARALLEL BASELINE REPRODUCTION ==="
echo "Array Job ID: ${SLURM_ARRAY_JOB_ID:-local}"
echo "Task ID:      ${TASK_ID}"
echo "Seeds:        [${START_SEED}, ${END_SEED})"
echo "Output CSV:   ${OUTPUT_CSV}"
echo "Node:         $(hostname)"
echo "Start:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir:  ${PROJECT_DIR}"
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

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase1_baseline"
export DYPART_LOG_LEVEL="DEBUG"
mkdir -p "$DYPART_LOG_DIR" results

# Ensure qiskit-algorithms (<0.4.0) compatibility with qiskit 1.1.0
pip install "qiskit-algorithms>=0.3.0,<0.4.0" 2>/dev/null || true

echo "--- Running parallel worker ${TASK_ID} (Seeds ${START_SEED} to ${END_SEED}) ---"
python -u experiments/run_final_benchmark.py \
    --start-seed "${START_SEED}" \
    --end-seed "${END_SEED}" \
    --output "${OUTPUT_CSV}" \
    2>&1 | tee "${DYPART_LOG_DIR}/baseline_part_${TASK_ID}_${SLURM_ARRAY_JOB_ID:-local}_${TASK_ID}.log"

echo ""
echo "=== WORKER ${TASK_ID} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
