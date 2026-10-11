#!/bin/bash
# slurm/env_setup.sh — One-time conda environment setup on OSC
# Usage: sbatch slurm/env_setup.sh
#SBATCH --job-name=dypart_env_setup
#SBATCH --account=<YOUR_OSC_PROJECT>
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/env_setup_%j.out
#SBATCH --error=logs/env_setup_%j.err
# #SBATCH --mail-type=END,FAIL
# #SBATCH --mail-user=<YOUR_EMAIL>

set -euo pipefail

echo "=== DY-PART ENVIRONMENT SETUP ==="
echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: $(hostname)"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Load conda
module load miniconda3/24.1.2-py310

# Create environment (skip if exists)
if conda info --envs | grep -q dypart; then
    echo "Environment 'dypart' already exists, updating..."
    source activate dypart
else
    echo "Creating new environment 'dypart'..."
    conda create -n dypart python=3.10 -y
    source activate dypart
fi

# Install dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install qiskit==1.1.0
pip install qiskit-aer==0.14.0
pip install qiskit-algorithms==0.3.0
pip install numpy pandas matplotlib seaborn scipy networkx
pip install pymetis  # METIS baseline
pip install pytest   # Testing

# Install Dy-Part framework in editable mode
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
echo "Installing dypart_framework from: $PROJECT_DIR"
cd "$PROJECT_DIR"
pip install -e .

echo ""
echo "=== ENVIRONMENT VALIDATION ==="
conda list
python -c "import qiskit; print(f'Qiskit version: {qiskit.__version__}')"
python -c "import qiskit_aer; print(f'Qiskit-Aer version: {qiskit_aer.__version__}')"
python -c "from vqe_framework.logging_config import setup_logging; print('vqe_framework OK')"
python -c "import pymetis; print('pymetis OK')"

echo ""
echo "=== ENVIRONMENT SETUP COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
