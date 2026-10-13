#!/bin/bash
# slurm/run_merge_hyperparam.sh — Merges and selects optimal hyperparameters on OSC (ACT-014, ACT-015)
# Usage: sbatch slurm/run_merge_hyperparam.sh
#SBATCH --job-name=dypart_hp_merge
#SBATCH --account=PWSU0516
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/phase2_hyperparam/slurm_hp_merge_%j.out
#SBATCH --error=logs/phase2_hyperparam/slurm_hp_merge_%j.err

set -euo pipefail

PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"

echo "=== PHASE 2: MERGE HYPERPARAMETERS & SELECT OPTIMUM ==="
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

echo "--> Step 1: Merging all hyperparameter partitions..."
python -u scripts/merge_hyperparam_results.py \
    --pattern "results/hyperparam_part_*.csv" \
    --output-file results/hyperparam_grid_search.csv

echo ""
echo "--> Step 2: Selecting optimal hyperparameters..."
python -u scripts/select_optimal_hyperparams.py \
    --input results/hyperparam_grid_search.csv \
    --output-summary results/hyperparam_summary.csv \
    --output-json results/optimal_hyperparameters.json

echo ""
echo "=== HYPERPARAMETER PIPELINE COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
