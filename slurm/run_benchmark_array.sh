#!/bin/bash
# slurm/run_benchmark_array.sh — Multi-Scale Corrected Benchmark on OSC (ACT-018)
# Usage: sbatch slurm/run_benchmark_array.sh
#SBATCH --job-name=dypart_bm_arr
#SBATCH --account=PWSU0516
#SBATCH --time=02:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --array=0-29
#SBATCH --output=logs/phase2_benchmark/slurm_bm_%A_%a.out
#SBATCH --error=logs/phase2_benchmark/slurm_bm_%A_%a.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

TASK_ID="${SLURM_ARRAY_TASK_ID:-0}"

# 30 workers over 30 seeds -> exactly 1 seed per worker
START_SEED=${TASK_ID}
END_SEED=$(( TASK_ID + 1 ))
OUTPUT_CSV="results/benchmark_part_${TASK_ID}.csv"

echo "=== PHASE 2: FULL CORRECTED BENCHMARK (ACT-018) ==="
echo "Array Job ID: ${SLURM_ARRAY_JOB_ID:-local}"
echo "Task ID:      ${TASK_ID}"
echo "Seeds:        [${START_SEED}, ${END_SEED})"
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

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase2_benchmark"
export DYPART_LOG_LEVEL="DEBUG"
mkdir -p "$DYPART_LOG_DIR" results

# Ensure qiskit-algorithms (<0.4.0) compatibility with qiskit 1.1.0
pip install "qiskit-algorithms>=0.3.0,<0.4.0" 2>/dev/null || true

echo "--- Running Benchmark Worker ${TASK_ID} (Seeds ${START_SEED} to ${END_SEED}) ---"
python -u experiments/run_corrected_benchmark.py \
    --start-seed "${START_SEED}" \
    --end-seed "${END_SEED}" \
    --nodes 8 10 12 16 20 \
    --methods dypart static metis random \
    --output "${OUTPUT_CSV}" \
    --hyperparams-json results/optimal_hyperparameters.json \
    2>&1 | tee "${DYPART_LOG_DIR}/benchmark_part_${TASK_ID}_${SLURM_ARRAY_JOB_ID:-local}.log"

echo ""
echo "=== WORKER ${TASK_ID} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
