#!/bin/bash
# slurm/run_benchmark.sh — Phase 2b: Full corrected benchmark
# Usage: sbatch slurm/run_benchmark.sh
#SBATCH --job-name=dypart_bench
#SBATCH --account=PWSU0516
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --mem=32G
#SBATCH --array=0-49%10
#SBATCH --output=logs/phase2_benchmark/slurm_%A_%a.out
#SBATCH --error=logs/phase2_benchmark/slurm_%A_%a.err

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${DYPART_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"

echo "=== PHASE 2b: FULL BENCHMARK ==="
echo "Job ID:      ${SLURM_ARRAY_JOB_ID:-local}, Task: ${SLURM_ARRAY_TASK_ID:-0}"
echo "Node:        $(hostname)"
echo "Start:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: ${PROJECT_DIR}"
echo "Memory info: $(free -h 2>/dev/null | head -2 || echo 'N/A')"
echo ""

if [ -f /etc/profile.d/lmod.sh ]; then
    source /etc/profile.d/lmod.sh 2>/dev/null || true
fi
module load miniconda3 2>/dev/null || module load miniconda3/24.1.2-py310 2>/dev/null || true

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi
conda activate dypart 2>/dev/null || source activate dypart 2>/dev/null || true

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase2_benchmark"
export DYPART_LOG_LEVEL="INFO"
mkdir -p "$DYPART_LOG_DIR"
mkdir -p "${PROJECT_DIR}/results"

cd "$PROJECT_DIR"

python -u experiments/run_corrected_benchmark.py \
  --task-id ${SLURM_ARRAY_TASK_ID:-0} \
  --num-seeds 30 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/bench_${SLURM_ARRAY_JOB_ID:-local}_${SLURM_ARRAY_TASK_ID:-0}.log"

echo ""
echo "=== TASK ${SLURM_ARRAY_TASK_ID:-0} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
