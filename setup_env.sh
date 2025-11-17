#!/bin/bash
# Setup Environment for Concert Data Platform
# Source this file to set up your environment: source setup_env.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Create helpful aliases
alias run-chatbot='PYTHONPATH=. python src/api/chatbot_api.py'
alias run-ml-api='PYTHONPATH=. python src/api/ml_api.py'
alias run-demo='PYTHONPATH=. python demo_test_queries.py'
alias validate-system='PYTHONPATH=. python quick_system_validation.py'

echo "✅ Environment configured!"
echo ""
echo "PYTHONPATH set to: ${PYTHONPATH}"
echo ""
echo "Available aliases:"
echo "  run-chatbot      - Start chatbot API"
echo "  run-ml-api       - Start ML API"
echo "  run-demo         - Run demo test queries"
echo "  validate-system  - Quick system validation"
echo ""
echo "Or run any Python script with: PYTHONPATH=. python path/to/script.py"
