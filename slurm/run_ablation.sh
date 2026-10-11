#!/bin/bash
# slurm/run_ablation.sh — Phase 3: Ablation studies and supplementary experiments
#SBATCH --job-name=dypart_ablation
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=16G
#SBATCH --output=logs/phase3_ablation/slurm_%j.out
#SBATCH --error=logs/phase3_ablation/slurm_%j.err
# #SBATCH --mail-type=END,FAIL
# #SBATCH --mail-user=<YOUR_EMAIL>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== PHASE 3: ABLATION STUDIES ==="
echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: $(hostname)"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: $PROJECT_DIR"
echo "Python: $(python --version 2>&1)"
echo ""

module load miniconda3/24.1.2-py310
source activate dypart

export DYPART_LOG_DIR="${PROJECT_DIR}/logs/phase3_ablation"
export DYPART_LOG_LEVEL="DEBUG"
mkdir -p "$DYPART_LOG_DIR"

cd "$PROJECT_DIR"

# --- Ablation 1: Ternary vs Exhaustive Search Comparison ---
echo ""
echo "--- Ablation 1: Ternary vs Exhaustive Search ---"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
python -u experiments/run_ternary_vs_exhaustive.py \
  --graph-sizes 8 10 12 16 20 24 28 32 36 40 \
  --num-seeds 30 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/ablation_ternary_${SLURM_JOB_ID:-local}.log"
echo "Ablation 1 complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Ablation 2: Empirical Cost Model Validation ---
echo ""
echo "--- Ablation 2: Cost Model Validation ---"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
python -u experiments/run_cost_model_validation.py \
  --graph-sizes 8 10 12 16 \
  --noise-levels 1e-4 5e-4 1e-3 5e-3 1e-2 5e-2 \
  --num-seeds 20 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/ablation_cost_model_${SLURM_JOB_ID:-local}.log"
echo "Ablation 2 complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Ablation 3: Runtime Overhead Measurement ---
echo ""
echo "--- Ablation 3: Runtime Overhead Measurement ---"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
python -u experiments/run_runtime_measurement.py \
  --graph-sizes 8 10 12 16 20 \
  --noise-levels 1e-4 1e-3 1e-2 \
  --num-seeds 10 \
  --output-dir "${PROJECT_DIR}/results" \
  2>&1 | tee "${DYPART_LOG_DIR}/ablation_runtime_${SLURM_JOB_ID:-local}.log"
echo "Ablation 3 complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Summary ---
echo ""
echo "=== PHASE 3 COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Output files:"
ls -la "${PROJECT_DIR}/results/"ablation_*.csv 2>/dev/null || echo "  (no ablation CSVs found)"
ls -la "${PROJECT_DIR}/results/"runtime_*.csv 2>/dev/null || echo "  (no runtime CSVs found)"
ls -la "${PROJECT_DIR}/results/"cost_model_*.csv 2>/dev/null || echo "  (no cost model CSVs found)"
