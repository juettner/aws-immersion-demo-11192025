#!/bin/bash
# Run ML API Server
# This script sets up the proper Python path and runs the ML API service

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "Starting ML API Server..."
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

# Run the ML API
python src/api/ml_api.py
