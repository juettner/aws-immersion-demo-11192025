#!/usr/bin/env python3
"""
Validation script for demo pipeline implementation.

Checks that all required components are in place for task 8.2.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_file_structure():
    """Validate that all required files exist."""
    print("=" * 70)
    print("Validating Demo Pipeline File Structure")
    print("=" * 70)
    
    required_files = [
        'run_demo_pipeline.py',
        'train_demo_models.py',
        'docs/guides/DEMO_PIPELINE_GUIDE.md',
        'generate_synthetic_data.py',
        'src/services/synthetic_data_generator.py',
        'src/infrastructure/redshift_client.py',
        'src/infrastructure/redshift_data_loader.py',
        'src/infrastructure/glue_job_manager.py',
        'src/services/venue_popularity_service.py',
        'src/services/ticket_sales_prediction_service.py',
        'src/services/model_evaluation_service.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def validate_imports():
    """Validate that all required modules can be imported."""
    print("\n" + "=" * 70)
    print("Validating Python Imports")
    print("=" * 70)
    
    imports_to_test = [
        ('src.services.synthetic_data_generator', 'SyntheticDataGenerator'),
        ('src.infrastructure.redshift_client', 'RedshiftClient'),
        ('src.infrastructure.redshift_data_loader', 'RedshiftDataLoader'),
        ('src.infrastructure.glue_job_manager', 'GlueJobManager'),
        ('src.services.venue_popularity_service', 'VenuePopularityService'),
        ('src.services.ticket_sales_prediction_service', 'TicketSalesPredictionService'),
        ('src.services.model_evaluation_service', 'ModelEvaluationService'),
    ]
    
    all_imported = True
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except ImportError as e:
            print(f"✗ {module_name}.{class_name} - IMPORT ERROR: {e}")
            all_imported = False
        except AttributeError as e:
            print(f"✗ {module_name}.{class_name} - ATTRIBUTE ERROR: {e}")
            all_imported = False
    
    return all_imported


def validate_script_executability():
    """Validate that scripts are executable and have proper structure."""
    print("\n" + "=" * 70)
    print("Validating Script Structure")
    print("=" * 70)
    
    scripts = [
        'run_demo_pipeline.py',
        'train_demo_models.py'
    ]
    
    all_valid = True
    for script in scripts:
        path = Path(script)
        if not path.exists():
            print(f"✗ {script} - MISSING")
            all_valid = False
            continue
        
        content = path.read_text()
        
        # Check for shebang
        if not content.startswith('#!/usr/bin/env python3'):
            print(f"⚠ {script} - Missing shebang")
        
        # Check for main function
        if 'def main():' not in content:
            print(f"✗ {script} - Missing main() function")
            all_valid = False
        else:
            print(f"✓ {script} - Has main() function")
        
        # Check for argparse
        if 'argparse' in content:
            print(f"✓ {script} - Uses argparse for CLI")
        else:
            print(f"⚠ {script} - No argparse found")
        
        # Check for if __name__ == '__main__'
        if "if __name__ == '__main__':" in content:
            print(f"✓ {script} - Has proper entry point")
        else:
            print(f"✗ {script} - Missing entry point guard")
            all_valid = False
    
    return all_valid


def validate_pipeline_orchestrator():
    """Validate DemoPipelineOrchestrator class."""
    print("\n" + "=" * 70)
    print("Validating DemoPipelineOrchestrator")
    print("=" * 70)
    
    try:
        # Import the script as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_demo_pipeline", "run_demo_pipeline.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for DemoPipelineOrchestrator class
        if hasattr(module, 'DemoPipelineOrchestrator'):
            orchestrator_class = module.DemoPipelineOrchestrator
            print("✓ DemoPipelineOrchestrator class found")
            
            # Check for required methods
            required_methods = [
                'ensure_s3_buckets',
                'generate_and_upload_data',
                'run_glue_etl_jobs',
                'load_data_to_redshift',
                'verify_data_quality',
                'generate_summary_report',
                'run_pipeline'
            ]
            
            all_methods_present = True
            for method in required_methods:
                if hasattr(orchestrator_class, method):
                    print(f"  ✓ Method: {method}")
                else:
                    print(f"  ✗ Method: {method} - MISSING")
                    all_methods_present = False
            
            return all_methods_present
        else:
            print("✗ DemoPipelineOrchestrator class not found")
            return False
            
    except Exception as e:
        print(f"✗ Error validating orchestrator: {e}")
        return False


def validate_model_trainer():
    """Validate DemoModelTrainer class."""
    print("\n" + "=" * 70)
    print("Validating DemoModelTrainer")
    print("=" * 70)
    
    try:
        # Import the script as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location("train_demo_models", "train_demo_models.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for DemoModelTrainer class
        if hasattr(module, 'DemoModelTrainer'):
            trainer_class = module.DemoModelTrainer
            print("✓ DemoModelTrainer class found")
            
            # Check for required methods
            required_methods = [
                'extract_venue_training_data',
                'prepare_venue_features',
                'train_venue_popularity_model',
                'extract_ticket_sales_training_data',
                'prepare_ticket_sales_features',
                'train_ticket_sales_model',
                'generate_sample_predictions',
                'generate_training_report',
                'run_training_pipeline'
            ]
            
            all_methods_present = True
            for method in required_methods:
                if hasattr(trainer_class, method):
                    print(f"  ✓ Method: {method}")
                else:
                    print(f"  ✗ Method: {method} - MISSING")
                    all_methods_present = False
            
            return all_methods_present
        else:
            print("✗ DemoModelTrainer class not found")
            return False
            
    except Exception as e:
        print(f"✗ Error validating trainer: {e}")
        return False


def validate_documentation():
    """Validate documentation completeness."""
    print("\n" + "=" * 70)
    print("Validating Documentation")
    print("=" * 70)
    
    doc_path = Path('docs/guides/DEMO_PIPELINE_GUIDE.md')
    
    if not doc_path.exists():
        print("✗ DEMO_PIPELINE_GUIDE.md not found")
        return False
    
    content = doc_path.read_text()
    
    required_sections = [
        '## Overview',
        '## Prerequisites',
        '## Phase 1: Data Pipeline Execution',
        '## Phase 2: Model Training',
        '## Complete Workflow Example',
        '## Troubleshooting',
        '## Validation Queries'
    ]
    
    all_sections_present = True
    for section in required_sections:
        if section in content:
            print(f"✓ Section: {section}")
        else:
            print(f"✗ Section: {section} - MISSING")
            all_sections_present = False
    
    # Check for code examples
    if '```bash' in content:
        print("✓ Contains bash code examples")
    else:
        print("⚠ No bash code examples found")
    
    if '```sql' in content:
        print("✓ Contains SQL code examples")
    else:
        print("⚠ No SQL code examples found")
    
    return all_sections_present


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("Demo Pipeline Implementation Validation")
    print("Task 8.2: Execute end-to-end data pipeline with demo data")
    print("=" * 70 + "\n")
    
    results = {
        'File Structure': validate_file_structure(),
        'Python Imports': validate_imports(),
        'Script Structure': validate_script_executability(),
        'Pipeline Orchestrator': validate_pipeline_orchestrator(),
        'Model Trainer': validate_model_trainer(),
        'Documentation': validate_documentation()
    }
    
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All validation checks passed!")
        print("=" * 70)
        print("\nTask 8.2 implementation is complete and ready for execution.")
        print("\nNext steps:")
        print("1. Configure AWS credentials and Redshift connection in .env")
        print("2. Run: python run_demo_pipeline.py")
        print("3. Run: python train_demo_models.py")
        print("4. Review generated reports")
        return 0
    else:
        print("✗ Some validation checks failed")
        print("=" * 70)
        print("\nPlease review the errors above and fix the issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
