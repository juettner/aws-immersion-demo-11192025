#!/bin/bash
# Run Chatbot API Server
# This script sets up the proper Python path and runs the chatbot service

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "Starting Chatbot API Server..."
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

# Run the chatbot API
python src/api/chatbot_api.py
