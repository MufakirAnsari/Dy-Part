#!/bin/bash
# slurm/launch_corrected_benchmark.sh — 1-Command Automated Pipeline for Full Benchmark (ACT-018)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

mkdir -p logs/phase2_benchmark results
# Preserves existing partition files to enable fast resumption of incomplete runs

echo "Submitting 30-worker array job for Full Multi-Scale Benchmark (4 methods x 5 sizes x 8 noise x 30 seeds = 4,800 runs)..."
ARRAY_JOB_ID=$(sbatch --parsable slurm/run_benchmark_array.sh)
echo "Submitted Array Job: ${ARRAY_JOB_ID}"

echo "Submitting automated merge & statistical analysis job with dependency afterok:${ARRAY_JOB_ID}..."
MERGE_JOB_ID=$(sbatch --parsable --dependency="afterok:${ARRAY_JOB_ID}" slurm/run_merge_benchmark.sh)
echo "Submitted Merge Job: ${MERGE_JOB_ID}"
echo ""
echo "================================================================"
echo " Full Benchmark Pipeline launched successfully on OSC!"
echo " 1. Workers running in parallel: Job ID ${ARRAY_JOB_ID}_[0-29]"
echo " 2. Estimated Wall-Clock Time: ~50-60 minutes"
echo " 3. Merge & Wilcoxon analysis will run automatically: Job ID ${MERGE_JOB_ID}"
echo " 4. Monitor with: squeue -u \$USER"
echo " 5. View logs with: tail -f logs/phase2_benchmark/slurm_bm_${ARRAY_JOB_ID}_*.out"
echo "================================================================"
