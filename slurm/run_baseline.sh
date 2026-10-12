#!/bin/bash
# slurm/run_baseline.sh — Phase 1: Reproduce original results
# Usage: sbatch slurm/run_baseline.sh
#SBATCH --job-name=dypart_baseline
# #SBATCH --account=<YOUR_OSC_PROJECT>  # Uncomment and set if required by your OSC project
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=16G
#SBATCH --output=logs/phase1_baseline/slurm_%j.out
#SBATCH --error=logs/phase1_baseline/slurm_%j.err

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${DYPART_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"

echo "=== PHASE 1: BASELINE REPRODUCTION ==="
echo "Job ID:      ${SLURM_JOB_ID:-local}"
echo "Node:        $(hostname)"
echo "Start:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: ${PROJECT_DIR}"
echo ""

if [ -f /etc/profile.d/lmod.sh ]; then
    source /etc/profile.d/lmod.sh 2>/dev/null || true
fi
module load miniconda3 2>/dev/null || module load miniconda3/24.1.2-py310 2>/dev/null || true

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi
conda activate dypart 2>/dev/null || source activate dypart 2>/dev/null || true

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase1_baseline"
export DYPART_LOG_LEVEL="DEBUG"
mkdir -p "$DYPART_LOG_DIR"

cd "$PROJECT_DIR"

echo "--- Running baseline reproduction experiment ---"
python -u experiments/run_final_benchmark.py \
  2>&1 | tee "${DYPART_LOG_DIR}/baseline_${SLURM_JOB_ID:-local}.log"

echo ""
echo "=== PHASE 1 COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
