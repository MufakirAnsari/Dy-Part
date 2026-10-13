#!/bin/bash
# slurm/run_merge_benchmark.sh — Merges and audits full benchmark on OSC (ACT-018)
# Usage: sbatch slurm/run_merge_benchmark.sh
#SBATCH --job-name=dypart_bm_merge
#SBATCH --account=PWSU0516
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/phase2_benchmark/slurm_bm_merge_%j.out
#SBATCH --error=logs/phase2_benchmark/slurm_bm_merge_%j.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

echo "=== PHASE 2: MERGE FULL BENCHMARK DATA ==="
echo "Job ID:      ${SLURM_JOB_ID:-local}"
echo "Start:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"

python -u scripts/merge_corrected_benchmark_results.py \
    --pattern "results/benchmark_part_*.csv" \
    --output-file results/corrected_benchmark.csv

echo ""
echo "=== BENCHMARK MERGE COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
