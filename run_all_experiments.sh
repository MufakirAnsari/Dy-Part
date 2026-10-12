#!/bin/bash
# run_all_experiments.sh — Master launcher for Dy-Part experiments
#
# Can be run:
# 1. Directly on OSC (Ascend / Pitzer):
#    bash run_all_experiments.sh [--account=PAS1234]
#
# 2. From local machine targeting OSC via SSH:
#    bash run_all_experiments.sh --remote mufakiransari@ascend.osc.edu [--account=PAS1234]
#
# 3. Locally for quick test / smoke test without SLURM:
#    bash run_all_experiments.sh --local-test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_HOST=""
ACCOUNT_FLAG="--account=PWSU0516"
LOCAL_TEST=false

for arg in "$@"; do
    case $arg in
        --remote=*)
            REMOTE_HOST="${arg#*=}"
            ;;
        --account=*)
            ACCOUNT_FLAG="${arg}"
            ;;
        --local-test)
            LOCAL_TEST=true
            ;;
        *)
            ;;
    esac
done

if [ -n "$REMOTE_HOST" ]; then
    echo "========================================================="
    echo "  Connecting to OSC ($REMOTE_HOST) via SSH..."
    echo "========================================================="
    ssh -t "$REMOTE_HOST" "cd ~/Dy-Part && bash slurm/submit_all.sh ${ACCOUNT_FLAG}"
    exit 0
fi

if [ "$LOCAL_TEST" = true ]; then
    echo "========================================================="
    echo "  Running local verification smoke test..."
    echo "========================================================="
    python -m pytest tests/ -v
    exit 0
fi

# If on OSC (sbatch available)
if command -v sbatch &> /dev/null; then
    bash "${SCRIPT_DIR}/slurm/submit_all.sh" ${ACCOUNT_FLAG}
else
    echo "========================================================="
    echo "  Dy-Part Experiment Launcher"
    echo "========================================================="
    echo "No SLURM 'sbatch' detected on this machine."
    echo ""
    echo "To run on OSC from your local terminal:"
    echo "  bash run_all_experiments.sh --remote=mufakiransari@ascend.osc.edu ${ACCOUNT_FLAG}"
    echo ""
    echo "Or once logged into OSC (ssh mufakiransari@ascend.osc.edu):"
    echo "  cd ~/Dy-Part"
    echo "  bash slurm/submit_all.sh ${ACCOUNT_FLAG}"
    echo ""
    echo "To run unit tests locally:"
    echo "  bash run_all_experiments.sh --local-test"
fi
