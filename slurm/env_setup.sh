#!/bin/bash
# slurm/env_setup.sh — One-time conda environment setup on OSC (Ascend / Pitzer)
# Usage: sbatch slurm/env_setup.sh
#SBATCH --job-name=dypart_env_setup
#SBATCH --account=PWSU0516
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --output=logs/env_setup_%j.out
#SBATCH --error=logs/env_setup_%j.err

set -euo pipefail

# In SLURM, SLURM_SUBMIT_DIR is the directory where sbatch was executed
PROJECT_DIR="${DYPART_PROJECT_DIR:-${SLURM_SUBMIT_DIR:-$HOME/Dy-Part}}"
cd "${PROJECT_DIR}"
mkdir -p "${PROJECT_DIR}/logs"

echo "=== DY-PART ENVIRONMENT SETUP ==="
echo "Job ID:      ${SLURM_JOB_ID:-local}"
echo "Node:        $(hostname)"
echo "Date:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Project dir: ${PROJECT_DIR}"
echo ""

# Load conda module on OSC
if [ -f /etc/profile.d/lmod.sh ]; then
    source /etc/profile.d/lmod.sh 2>/dev/null || true
fi
module load miniconda3/24.1.2-py310 2>/dev/null || module load miniconda3 2>/dev/null || true

# Initialize conda in subshell
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/apps/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/apps/miniconda3/etc/profile.d/conda.sh"
fi

# Create environment (skip if exists)
if conda info --envs 2>/dev/null | grep -q '\bdypart\b'; then
    echo "Environment 'dypart' already exists, updating dependencies..."
    source activate dypart || conda activate dypart
else
    echo "Creating new environment 'dypart' with Python 3.10..."
    conda create -n dypart python=3.10 -y
    source activate dypart || conda activate dypart
fi

# Install dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install qiskit==1.1.0
pip install "qiskit-aer>=0.14.0,<0.15.0"
pip install "qiskit-algorithms>=0.3.0"
pip install "numpy>=1.24" "pandas>=2.0" "scipy>=1.10" "networkx>=3.0"
pip install "matplotlib>=3.7" "seaborn>=0.12"
pip install "pymetis>=2023.1"
pip install "pytest>=7.0"

# Install Dy-Part framework in editable mode
echo "Installing dypart_framework from: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"
pip install -e .

echo ""
echo "=== ENVIRONMENT VALIDATION ==="
conda list | grep -E "(qiskit|numpy|pandas|scipy|pymetis|dypart)"
python -c "import qiskit; print(f'Qiskit version: {qiskit.__version__}')"
python -c "import qiskit_aer; print(f'Qiskit-Aer version: {qiskit_aer.__version__}')"
python -c "from vqe_framework.logging_config import setup_logging; print('vqe_framework: OK')"
python -c "import pymetis; print('pymetis: OK')"

echo ""
echo "=== ENVIRONMENT SETUP COMPLETE ==="
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
