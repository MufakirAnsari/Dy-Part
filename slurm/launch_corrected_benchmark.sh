#!/bin/bash
# slurm/launch_corrected_benchmark.sh — 1-Command Automated Pipeline for Full Benchmark (ACT-018)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

mkdir -p logs/phase2_benchmark results
rm -f results/benchmark_part_*.csv

echo "Submitting 10-worker array job for Full Multi-Scale Benchmark (4 methods x 5 sizes x 8 noise x 30 seeds)..."
ARRAY_JOB_ID=$(sbatch --parsable slurm/run_benchmark_array.sh)
echo "Submitted Array Job: ${ARRAY_JOB_ID}"

echo "Submitting automated merge job with dependency afterok:${ARRAY_JOB_ID}..."
MERGE_JOB_ID=$(sbatch --parsable --dependency="afterok:${ARRAY_JOB_ID}" slurm/run_merge_benchmark.sh)
echo "Submitted Merge Job: ${MERGE_JOB_ID}"
echo ""
echo "================================================================"
echo " Full Benchmark Pipeline launched successfully on OSC!"
echo " 1. Workers running in parallel: Job ID ${ARRAY_JOB_ID}_[0-9]"
echo " 2. Merge will run automatically when all 10 finish: Job ID ${MERGE_JOB_ID}"
echo " 3. Monitor with: squeue -u \$USER"
echo " 4. View logs with: tail -f logs/phase2_benchmark/slurm_bm_${ARRAY_JOB_ID}_*.out"
echo "================================================================"
