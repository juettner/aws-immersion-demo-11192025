#!/usr/bin/env python3
"""
Quick System Validation Script

Performs rapid validation checks that don't require all services running.
Useful for pre-demo verification and quick health checks.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if file exists"""
    if Path(filepath).exists():
        return True, f"✓ {filepath}"
    else:
        return False, f"✗ {filepath} - NOT FOUND"

def check_directory_exists(dirpath: str) -> Tuple[bool, str]:
    """Check if directory exists"""
    if Path(dirpath).is_dir():
        file_count = len(list(Path(dirpath).rglob("*")))
        return True, f"✓ {dirpath} ({file_count} files)"
    else:
        return False, f"✗ {dirpath} - NOT FOUND"

def check_python_import(module_name: str) -> Tuple[bool, str]:
    """Check if Python module can be imported"""
    try:
        __import__(module_name)
        return True, f"✓ {module_name}"
    except ImportError as e:
        return False, f"✗ {module_name} - {str(e)}"

def check_env_variable(var_name: str) -> Tuple[bool, str]:
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        masked_value = value[:4] + "..." if len(value) > 4 else "***"
        return True, f"✓ {var_name} = {masked_value}"
    else:
        return False, f"✗ {var_name} - NOT SET"

def main():
    """Run quick validation checks"""
    print_header("Quick System Validation")
    
    all_passed = True
    
    # Check 1: Core Python Files
    print_header("1. Core Python Files")
    
    core_files = [
        "src/config/settings.py",
        "src/services/chatbot_service.py",
        "src/services/venue_popularity_service.py",
        "src/services/ticket_sales_prediction_service.py",
        "src/services/recommendation_service.py",
        "src/infrastructure/redshift_client.py",
        "src/infrastructure/kinesis_client.py",
        "src/api/chatbot_api.py",
        "generate_synthetic_data.py",
        "train_demo_models.py"
    ]
    
    for filepath in core_files:
        passed, message = check_file_exists(filepath)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 2: Data Directories
    print_header("2. Data Directories")
    
    data_dirs = [
        "src/models",
        "src/services",
        "src/infrastructure",
        "src/api",
        "docs",
        "infrastructure"
    ]
    
    for dirpath in data_dirs:
        passed, message = check_directory_exists(dirpath)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 3: Web Application Files
    print_header("3. Web Application Files")
    
    web_files = [
        "web/package.json",
        "web/src/App.tsx",
        "web/src/pages/ChatbotPage.tsx",
        "web/src/pages/DashboardPage.tsx",
        "web/src/services/chatbot.ts",
        "web/src/services/analytics.ts"
    ]
    
    for filepath in web_files:
        passed, message = check_file_exists(filepath)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 4: Python Dependencies
    print_header("4. Python Dependencies")
    
    python_modules = [
        "boto3",
        "pydantic",
        "pandas",
        "numpy",
        "requests",
        "fastapi",
        "uvicorn"
    ]
    
    for module in python_modules:
        passed, message = check_python_import(module)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 5: Environment Variables
    print_header("5. Environment Variables")
    
    env_vars = [
        "AWS_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "REDSHIFT_HOST",
        "REDSHIFT_DATABASE",
        "BEDROCK_AGENT_ID"
    ]
    
    for var in env_vars:
        passed, message = check_env_variable(var)
        print(message)
        if not passed:
            print(f"  Note: {var} may be optional depending on configuration")
    
    # Check 6: Documentation Files
    print_header("6. Documentation Files")
    
    doc_files = [
        "README.md",
        "QUICKSTART.md",
        "DEPLOYMENT.md",
        "DEMO_EXECUTION_GUIDE.md",
        "docs/guides/DEMO_SCENARIOS.md",
        "docs/DOCUMENTATION_INDEX.md",
        ".kiro/specs/data-readiness-ai-demo/requirements.md",
        ".kiro/specs/data-readiness-ai-demo/design.md",
        ".kiro/specs/data-readiness-ai-demo/tasks.md"
    ]
    
    for filepath in doc_files:
        passed, message = check_file_exists(filepath)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 7: Validation Scripts
    print_header("7. Validation Scripts")
    
    validation_scripts = [
        "validate_redshift_implementation.py",
        "validate_chatbot_service.py",
        "validate_recommendation_engine.py",
        "validate_demo_pipeline.py",
        "validate_end_to_end_system.py",
        "demo_test_queries.py"
    ]
    
    for filepath in validation_scripts:
        passed, message = check_file_exists(filepath)
        print(message)
        if not passed:
            all_passed = False
    
    # Check 8: Infrastructure Files
    print_header("8. Infrastructure Files")
    
    infra_files = [
        "infrastructure/cloudformation/01-networking.yaml",
        "infrastructure/cloudformation/02-storage-processing.yaml",
        "infrastructure/cloudformation/03-compute-application.yaml",
        "infrastructure/cloudformation/04-chatbot-infrastructure.yaml",
        "infrastructure/cloudformation/05-monitoring-observability.yaml",
        "infrastructure/cloudformation/06-tracing-logging.yaml",
        "infrastructure/setup_api_gateway.py",
        "infrastructure/deploy_web_app.py"
    ]
    
    for filepath in infra_files:
        passed, message = check_file_exists(filepath)
        print(message)
        if not passed:
            all_passed = False
    
    # Summary
    print_header("Validation Summary")
    
    if all_passed:
        print("✓ All critical files and dependencies are present")
        print("✓ System is ready for demo execution")
        print("\nNext Steps:")
        print("  1. Generate demo data: python generate_synthetic_data.py")
        print("  2. Run data pipeline: ./run_complete_demo.sh")
        print("  3. Train ML models: python train_demo_models.py")
        print("  4. Start chatbot: python src/api/chatbot_api.py")
        print("  5. Start web app: cd web && npm run dev")
        print("  6. Run full validation: python validate_end_to_end_system.py")
        return 0
    else:
        print("✗ Some files or dependencies are missing")
        print("✗ Please review the errors above and install missing components")
        print("\nCommon Fixes:")
        print("  - Install Python dependencies: pip install -r requirements.txt")
        print("  - Install web dependencies: cd web && npm install")
        print("  - Set environment variables in .env file")
        print("  - Verify AWS credentials are configured")
        return 1

if __name__ == "__main__":
    sys.exit(main())
