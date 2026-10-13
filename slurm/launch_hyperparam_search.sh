#!/bin/bash
# slurm/launch_hyperparam_search.sh — 1-Command Automated Pipeline for Hyperparameter Grid Search (ACT-014, ACT-015)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

mkdir -p logs/phase2_hyperparam results

echo "Submitting 10-worker array job for Hyperparameter Grid Search (200 configs x 10 seeds = 2000 runs)..."
ARRAY_JOB_ID=$(sbatch --parsable slurm/run_hyperparam_array.sh)
echo "Submitted Array Job: ${ARRAY_JOB_ID}"

echo "Submitting automated merge & parameter selection job with dependency afterok:${ARRAY_JOB_ID}..."
MERGE_JOB_ID=$(sbatch --parsable --dependency="afterok:${ARRAY_JOB_ID}" slurm/run_merge_hyperparam.sh)
echo "Submitted Merge Job: ${MERGE_JOB_ID}"
echo ""
echo "================================================================"
echo " Hyperparameter Pipeline launched successfully on OSC!"
echo " 1. Workers running in parallel: Job ID ${ARRAY_JOB_ID}_[0-9]"
echo " 2. Merge & selection will run automatically: Job ID ${MERGE_JOB_ID}"
echo " 3. Monitor with: squeue -u \$USER"
echo " 4. View logs with: tail -f logs/phase2_hyperparam/slurm_hp_${ARRAY_JOB_ID}_*.out"
echo "================================================================"
