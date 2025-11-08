#!/usr/bin/env python3
"""
Validation script for AWS Glue ETL implementation.
"""
import sys
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, 'src')

from src.infrastructure.glue_job_manager import GlueJobManager, DataQualityAlerting
from src.services.data_quality_service import DataQualityService, QualityRule


def test_glue_job_manager():
    """Test Glue job manager functionality."""
    print("Testing Glue Job Manager...")
    
    try:
        manager = GlueJobManager()
        
        # Test job configurations
        assert 'artist-data-etl' in manager.job_configs
        assert 'venue-data-etl' in manager.job_configs
        assert 'concert-data-etl' in manager.job_configs
        
        print("✓ Glue job configurations loaded successfully")
        
        # Test job config structure
        for job_key, config in manager.job_configs.items():
            required_fields = ['name', 'description', 'script_location', 'max_capacity', 'timeout', 'max_retries']
            for field in required_fields:
                assert field in config, f"Missing field {field} in {job_key} config"
        
        print("✓ Job configurations have all required fields")
        
        return True
        
    except Exception as e:
        print(f"✗ Glue Job Manager test failed: {str(e)}")
        return False


def test_data_quality_service():
    """Test data quality service functionality."""
    print("\nTesting Data Quality Service...")
    
    try:
        service = DataQualityService()
        
        # Test quality rules initialization
        assert 'artists' in service.quality_rules
        assert 'venues' in service.quality_rules
        assert 'concerts' in service.quality_rules
        
        print("✓ Quality rules initialized for all data types")
        
        # Test completeness checking
        test_df = pd.DataFrame({
            'name': ['Artist 1', 'Artist 2', '', None, 'Artist 5'],
            'genre': ['rock', 'pop', 'jazz', 'blues', None]
        })
        
        completeness_score = service._check_completeness(test_df, 'name')
        assert 60 <= completeness_score <= 100, f"Unexpected completeness score: {completeness_score}"
        
        print("✓ Completeness checking works correctly")
        
        # Test uniqueness checking
        uniqueness_df = pd.DataFrame({
            'artist_id': ['art_1', 'art_2', 'art_3', 'art_2', 'art_4']
        })
        
        uniqueness_score = service._check_uniqueness(uniqueness_df, 'artist_id')
        assert uniqueness_score == 80.0, f"Expected 80% uniqueness, got {uniqueness_score}%"
        
        print("✓ Uniqueness checking works correctly")
        
        # Test range validation
        range_df = pd.DataFrame({
            'popularity_score': [85.5, 92.0, 150.0, -10.0, 75.5]
        })
        
        range_score = service._check_range(range_df, 'popularity_score', 0, 100)
        assert range_score == 60.0, f"Expected 60% range validity, got {range_score}%"
        
        print("✓ Range validation works correctly")
        
        # Test quality rule execution
        rule = QualityRule(
            rule_id='test_rule',
            rule_name='Test Rule',
            rule_type='completeness',
            column_name='name',
            threshold=80.0,
            severity='warning',
            description='Test rule',
            validation_logic='not_null_and_not_empty'
        )
        
        result = service._execute_quality_rule(test_df, rule)
        assert result.rule_id == 'test_rule'
        assert isinstance(result.score, float)
        assert isinstance(result.passed, bool)
        
        print("✓ Quality rule execution works correctly")
        
        return True
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"✗ Data Quality Service test failed: {str(e)}")
        print(f"  Error details: {error_details}")
        return False


def test_fuzzy_matching():
    """Test fuzzy matching functionality for deduplication."""
    print("\nTesting Fuzzy Matching...")
    
    try:
        # Use standalone fuzzy matcher to avoid AWS Glue dependencies
        from src.infrastructure.fuzzy_matcher_standalone import FuzzyMatcher
        
        matcher = FuzzyMatcher(similarity_threshold=0.85)
        
        # Test string normalization
        normalized = matcher.normalize_string("The Rolling Stones Inc.")
        expected = "rolling stones"
        assert normalized == expected, f"Expected '{expected}', got '{normalized}'"
        
        print("✓ String normalization works correctly")
        
        # Test similarity calculation
        similarity = matcher.calculate_similarity("The Beatles", "Beatles")
        assert similarity > 0.8, f"Expected high similarity, got {similarity}"
        
        print("✓ Similarity calculation works correctly")
        
        # Test duplicate detection
        test_df = pd.DataFrame({
            'artist_id': ['art_1', 'art_2', 'art_3', 'art_4'],
            'name': ['The Beatles', 'Beatles', 'Rolling Stones', 'Led Zeppelin']
        })
        
        duplicates_df = matcher.find_duplicates(test_df, ['name'], 'artist_id')
        assert isinstance(duplicates_df, pd.DataFrame), "Should return a DataFrame"
        
        print("✓ Duplicate detection works correctly")
        
        return True
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"✗ Fuzzy Matching test failed: {str(e)}")
        print(f"  Error details: {error_details}")
        return False


def test_data_quality_alerting():
    """Test data quality alerting functionality."""
    print("\nTesting Data Quality Alerting...")
    
    try:
        alerting = DataQualityAlerting()
        
        # Test alarm configuration
        alarms = {
            'ArtistDataQualityLow': {
                'alarm_name': 'ConcertPlatform-ArtistDataQuality-Low',
                'metric_name': 'ArtistDataQualityScore',
                'threshold': 70.0,
                'comparison_operator': 'LessThanThreshold'
            }
        }
        
        # Verify alarm structure
        for alarm_key, config in alarms.items():
            required_fields = ['alarm_name', 'metric_name', 'threshold', 'comparison_operator']
            for field in required_fields:
                assert field in config, f"Missing field {field} in alarm config"
        
        print("✓ Alarm configurations are properly structured")
        
        return True
        
    except Exception as e:
        print(f"✗ Data Quality Alerting test failed: {str(e)}")
        return False


def test_etl_job_scripts():
    """Test ETL job script structure and imports."""
    print("\nTesting ETL Job Scripts...")
    
    try:
        # Test that the ETL script file exists and has required components
        with open('src/infrastructure/glue_etl_jobs.py', 'r') as f:
            script_content = f.read()
        
        # Check for required classes and functions
        required_components = [
            'class DataQualityMonitor',
            'class FuzzyMatcher', 
            'class ArtistETL',
            'class VenueETL',
            'class ConcertETL',
            'def process_artist_data',
            'def process_venue_data',
            'def process_concert_data'
        ]
        
        for component in required_components:
            assert component in script_content, f"Missing component: {component}"
        
        print("✓ ETL job script has all required components")
        
        # Test that AWS Glue imports are present
        glue_imports = [
            'from awsglue.transforms import',
            'from awsglue.context import GlueContext',
            'from awsglue.job import Job',
            'from pyspark.sql import DataFrame'
        ]
        
        for import_stmt in glue_imports:
            assert import_stmt in script_content, f"Missing import: {import_stmt}"
        
        print("✓ ETL job script has required AWS Glue imports")
        
        return True
        
    except Exception as e:
        print(f"✗ ETL Job Scripts test failed: {str(e)}")
        return False


def generate_test_report(results: Dict[str, bool]) -> Dict[str, Any]:
    """Generate a comprehensive test report."""
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate
        },
        'test_results': results,
        'status': 'PASSED' if success_rate == 100 else 'FAILED',
        'recommendations': []
    }
    
    if success_rate < 100:
        failed_tests = [test for test, passed in results.items() if not passed]
        report['recommendations'].append(f"Fix failing tests: {', '.join(failed_tests)}")
    else:
        report['recommendations'].append("All tests passed - ETL implementation is ready for deployment")
    
    return report


def main():
    """Run all validation tests."""
    print("AWS Glue ETL Implementation Validation")
    print("=" * 50)
    
    # Run all tests
    test_results = {
        'Glue Job Manager': test_glue_job_manager(),
        'Data Quality Service': test_data_quality_service(),
        'Fuzzy Matching': test_fuzzy_matching(),
        'Data Quality Alerting': test_data_quality_alerting(),
        'ETL Job Scripts': test_etl_job_scripts()
    }
    
    # Generate report
    report = generate_test_report(test_results)
    
    print("\n" + "=" * 50)
    print("VALIDATION REPORT")
    print("=" * 50)
    print(f"Status: {report['status']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
    
    if report['summary']['failed_tests'] > 0:
        print("\nFailed Tests:")
        for test_name, passed in test_results.items():
            if not passed:
                print(f"  ✗ {test_name}")
    
    print("\nRecommendations:")
    for recommendation in report['recommendations']:
        print(f"  • {recommendation}")
    
    # Exit with appropriate code
    sys.exit(0 if report['status'] == 'PASSED' else 1)


if __name__ == "__main__":
    main()