#!/bin/bash
# slurm/launch_parallel_baseline.sh — 1-Command Automated Pipeline
# Submits 4 parallel workers on OSC, then automatically triggers the merger when all finish.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

mkdir -p logs/phase1_baseline results

echo "Submitting 4-worker array job for Seeds 10 to 29..."
ARRAY_JOB_ID=$(sbatch --parsable slurm/run_baseline_array.sh)
echo "Submitted Array Job: ${ARRAY_JOB_ID}"

echo "Submitting automated merge job with dependency afterok:${ARRAY_JOB_ID}..."
MERGE_JOB_ID=$(sbatch --parsable --dependency="afterok:${ARRAY_JOB_ID}" slurm/run_merge_baseline.sh)
echo "Submitted Merge Job: ${MERGE_JOB_ID}"
echo ""
echo "================================================================"
echo " Pipeline launched successfully on OSC!"
echo " 1. Workers running in parallel: Job ID ${ARRAY_JOB_ID}_[0-3]"
echo " 2. Merger will run automatically when all 4 finish: Job ID ${MERGE_JOB_ID}"
echo " 3. Monitor with: squeue -u \$USER"
echo " 4. View logs with: tail -f logs/phase1_baseline/slurm_arr_${ARRAY_JOB_ID}_*.out"
echo "================================================================"
