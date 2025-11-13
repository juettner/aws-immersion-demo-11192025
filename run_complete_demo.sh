#!/bin/bash
# Complete demo pipeline execution script
# Runs both data pipeline and model training in sequence

set -e  # Exit on error

echo "========================================================================"
echo "Concert Data Platform - Complete Demo Execution"
echo "========================================================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠ Warning: Virtual environment not activated"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

# Check if .env file exists
if [[ ! -f .env ]]; then
    echo "✗ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Parse command line arguments
SKIP_GENERATION=false
ARTISTS=1000
VENUES=500
CONCERTS=10000
SALES=50000
SEED=42

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-generation)
            SKIP_GENERATION=true
            shift
            ;;
        --artists)
            ARTISTS="$2"
            shift 2
            ;;
        --venues)
            VENUES="$2"
            shift 2
            ;;
        --concerts)
            CONCERTS="$2"
            shift 2
            ;;
        --sales)
            SALES="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-generation    Skip data generation, use existing S3 data"
            echo "  --artists N          Number of artists to generate (default: 1000)"
            echo "  --venues N           Number of venues to generate (default: 500)"
            echo "  --concerts N         Number of concerts to generate (default: 10000)"
            echo "  --sales N            Number of ticket sales to generate (default: 50000)"
            echo "  --seed N             Random seed for reproducibility (default: 42)"
            echo "  --help               Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --artists 500 --venues 250 --concerts 5000 --sales 25000"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Artists: $ARTISTS"
echo "  Venues: $VENUES"
echo "  Concerts: $CONCERTS"
echo "  Sales: $SALES"
echo "  Seed: $SEED"
echo "  Skip Generation: $SKIP_GENERATION"
echo ""

# Step 1: Validate implementation
echo "========================================================================"
echo "Step 1: Validating Implementation"
echo "========================================================================"
echo ""

python validate_demo_pipeline.py
if [[ $? -ne 0 ]]; then
    echo ""
    echo "✗ Validation failed. Please fix the issues before proceeding."
    exit 1
fi

echo ""
echo "✓ Validation passed!"
echo ""

# Step 2: Run data pipeline
echo "========================================================================"
echo "Step 2: Running Data Pipeline"
echo "========================================================================"
echo ""

PIPELINE_ARGS="--artists $ARTISTS --venues $VENUES --concerts $CONCERTS --sales $SALES --seed $SEED"

if [[ "$SKIP_GENERATION" == "true" ]]; then
    PIPELINE_ARGS="$PIPELINE_ARGS --skip-generation"
fi

python run_demo_pipeline.py $PIPELINE_ARGS
if [[ $? -ne 0 ]]; then
    echo ""
    echo "✗ Data pipeline failed. Check the logs above for details."
    exit 1
fi

echo ""
echo "✓ Data pipeline completed successfully!"
echo ""

# Step 3: Train ML models
echo "========================================================================"
echo "Step 3: Training ML Models"
echo "========================================================================"
echo ""

python train_demo_models.py --seed $SEED
if [[ $? -ne 0 ]]; then
    echo ""
    echo "✗ Model training failed. Check the logs above for details."
    exit 1
fi

echo ""
echo "✓ Model training completed successfully!"
echo ""

# Step 4: Summary
echo "========================================================================"
echo "Demo Execution Complete!"
echo "========================================================================"
echo ""
echo "Generated Reports:"
echo "  - pipeline_report_*.json (data pipeline execution)"
echo "  - model_training_report_*.json (model training results)"
echo ""
echo "Next Steps:"
echo "  1. Review the generated reports"
echo "  2. Query Redshift to explore the data"
echo "  3. Test the chatbot with the trained models"
echo "  4. View analytics in the web dashboard"
echo ""
echo "For more information, see:"
echo "  - docs/guides/DEMO_PIPELINE_GUIDE.md"
echo "  - docs/features/DEMO_PIPELINE_IMPLEMENTATION_SUMMARY.md"
echo ""
echo "========================================================================"

exit 0
