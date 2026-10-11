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
# #SBATCH --mail-type=END,FAIL
# #SBATCH --mail-user=<YOUR_EMAIL>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== PHASE 2b: FULL BENCHMARK ==="
echo "Job ID: ${SLURM_ARRAY_JOB_ID:-local}, Task: ${SLURM_ARRAY_TASK_ID:-0}"
echo "Node: $(hostname)"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: $PROJECT_DIR"
echo "Available memory: $(free -h 2>/dev/null | head -2 || echo 'N/A')"
echo ""

module load miniconda3/24.1.2-py310
source activate dypart

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase2_benchmark"
export DYPART_LOG_LEVEL="INFO"
mkdir -p "$DYPART_LOG_DIR"

cd "$PROJECT_DIR"

python -u experiments/run_corrected_benchmark.py \
  --task-id ${SLURM_ARRAY_TASK_ID:-0} \
  --num-seeds 30 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/bench_${SLURM_ARRAY_JOB_ID:-local}_${SLURM_ARRAY_TASK_ID:-0}.log"

echo ""
echo "=== TASK ${SLURM_ARRAY_TASK_ID:-0} COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
