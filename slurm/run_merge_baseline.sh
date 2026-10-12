#!/bin/bash
# slurm/run_merge_baseline.sh — Merges parallel baseline reproduction results on OSC
# Usage: sbatch slurm/run_merge_baseline.sh
#SBATCH --job-name=dypart_b_merge
#SBATCH --account=PWSU0516
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/phase1_baseline/slurm_merge_%j.out
#SBATCH --error=logs/phase1_baseline/slurm_merge_%j.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

echo "=== PHASE 1: MERGE & AUDIT REPRODUCTION DATA ==="
echo "Job ID:      ${SLURM_JOB_ID:-local}"
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

python -u scripts/merge_baseline_results.py \
    --base-file results/final_benchmark_data_averaged.csv \
    --part-files results/baseline_part_0.csv results/baseline_part_1.csv results/baseline_part_2.csv results/baseline_part_3.csv \
    --output-file results/final_benchmark_data_averaged.csv

echo ""
echo "=== MERGE & AUDIT COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
