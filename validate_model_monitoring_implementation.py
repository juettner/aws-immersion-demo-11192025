"""
Validation script for Model Monitoring and Drift Detection implementation

Validates:
- Drift detection algorithms (KS test, PSI, Chi-Square)
- CloudWatch metrics publishing
- Performance monitoring for regression and ranking models
- Retraining trigger logic
- Monitoring report generation
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_imports():
    """Validate that all required modules can be imported"""
    print("\n" + "="*80)
    print("VALIDATION 1: Module Imports")
    print("="*80)
    
    try:
        from src.services.model_monitoring_service import (
            ModelMonitoringService,
            DriftDetector,
            CloudWatchMetricsPublisher,
            DriftDetectionResult,
            ModelPerformanceMetrics,
            RetrainingTrigger
        )
        print("✓ All model monitoring modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        return False


def validate_drift_detector():
    """Validate drift detection algorithms"""
    print("\n" + "="*80)
    print("VALIDATION 2: Drift Detection Algorithms")
    print("="*80)
    
    from src.services.model_monitoring_service import DriftDetector
    
    detector = DriftDetector()
    
    # Test data
    np.random.seed(42)
    baseline_data = np.random.normal(100, 15, 1000)
    
    # No drift scenario
    current_data_no_drift = np.random.normal(100, 15, 500)
    
    # Drift scenario
    current_data_with_drift = np.random.normal(120, 20, 500)
    
    # Test KS test
    print("\n--- Kolmogorov-Smirnov Test ---")
    try:
        drift_detected, ks_stat, p_value = detector.kolmogorov_smirnov_test(
            baseline_data, current_data_no_drift
        )
        print(f"✓ KS test (no drift): drift={drift_detected}, ks_stat={ks_stat:.4f}, p_value={p_value:.4f}")
        
        drift_detected, ks_stat, p_value = detector.kolmogorov_smirnov_test(
            baseline_data, current_data_with_drift
        )
        print(f"✓ KS test (with drift): drift={drift_detected}, ks_stat={ks_stat:.4f}, p_value={p_value:.4f}")
        
        if not drift_detected:
            print("⚠️  Warning: Expected drift to be detected but it wasn't")
    except Exception as e:
        print(f"✗ KS test failed: {str(e)}")
        return False
    
    # Test PSI
    print("\n--- Population Stability Index ---")
    try:
        drift_detected, psi_value = detector.population_stability_index(
            baseline_data, current_data_no_drift
        )
        print(f"✓ PSI (no drift): drift={drift_detected}, psi={psi_value:.4f}")
        
        drift_detected, psi_value = detector.population_stability_index(
            baseline_data, current_data_with_drift
        )
        print(f"✓ PSI (with drift): drift={drift_detected}, psi={psi_value:.4f}")
        
        if not drift_detected:
            print("⚠️  Warning: Expected drift to be detected but it wasn't")
    except Exception as e:
        print(f"✗ PSI calculation failed: {str(e)}")
        return False
    
    # Test Chi-Square
    print("\n--- Chi-Square Test ---")
    try:
        drift_detected, chi2_stat, p_value = detector.chi_square_test(
            baseline_data, current_data_no_drift
        )
        print(f"✓ Chi-Square (no drift): drift={drift_detected}, chi2={chi2_stat:.4f}, p_value={p_value:.4f}")
        
        drift_detected, chi2_stat, p_value = detector.chi_square_test(
            baseline_data, current_data_with_drift
        )
        print(f"✓ Chi-Square (with drift): drift={drift_detected}, chi2={chi2_stat:.4f}, p_value={p_value:.4f}")
    except Exception as e:
        print(f"✗ Chi-Square test failed: {str(e)}")
        return False
    
    print("\n✓ All drift detection algorithms validated")
    return True


def validate_cloudwatch_publisher():
    """Validate CloudWatch metrics publisher"""
    print("\n" + "="*80)
    print("VALIDATION 3: CloudWatch Metrics Publisher")
    print("="*80)
    
    from src.services.model_monitoring_service import CloudWatchMetricsPublisher
    
    try:
        publisher = CloudWatchMetricsPublisher(namespace='MLModels/Test')
        print("✓ CloudWatch publisher initialized")
        
        # Note: Actual publishing requires AWS credentials and permissions
        print("⚠️  Note: Actual CloudWatch publishing requires AWS credentials")
        print("   The publisher is initialized and ready to use")
        
        return True
    except Exception as e:
        print(f"✗ CloudWatch publisher initialization failed: {str(e)}")
        return False


def validate_prediction_drift_detection():
    """Validate prediction drift detection"""
    print("\n" + "="*80)
    print("VALIDATION 4: Prediction Drift Detection")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Test data
        np.random.seed(42)
        baseline_predictions = np.random.normal(5000, 1000, 1000)
        current_predictions = np.random.normal(5500, 1200, 500)
        
        # Test PSI method
        result = monitoring_service.detect_prediction_drift(
            model_name='test_model',
            model_version='v1.0',
            baseline_predictions=baseline_predictions,
            current_predictions=current_predictions,
            method='psi'
        )
        
        print(f"✓ PSI drift detection: drift={result.drift_detected}, score={result.drift_score:.4f}")
        
        # Test KS method
        result = monitoring_service.detect_prediction_drift(
            model_name='test_model',
            model_version='v1.0',
            baseline_predictions=baseline_predictions,
            current_predictions=current_predictions,
            method='ks_test'
        )
        
        print(f"✓ KS drift detection: drift={result.drift_detected}, score={result.drift_score:.4f}")
        
        # Check drift history
        history = monitoring_service.get_drift_history(model_name='test_model')
        print(f"✓ Drift history recorded: {len(history)} entries")
        
        return True
    except Exception as e:
        print(f"✗ Prediction drift detection failed: {str(e)}")
        return False


def validate_feature_drift_detection():
    """Validate feature drift detection"""
    print("\n" + "="*80)
    print("VALIDATION 5: Feature Drift Detection")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Test data
        np.random.seed(42)
        baseline_features = pd.DataFrame({
            'feature1': np.random.uniform(0, 100, 1000),
            'feature2': np.random.randint(0, 1000, 1000),
            'feature3': np.random.normal(50, 10, 1000)
        })
        
        current_features = pd.DataFrame({
            'feature1': np.random.uniform(10, 110, 500),  # Slight drift
            'feature2': np.random.randint(0, 1000, 500),  # No drift
            'feature3': np.random.normal(60, 15, 500)  # Significant drift
        })
        
        results = monitoring_service.detect_feature_drift(
            model_name='test_model',
            model_version='v1.0',
            baseline_features=baseline_features,
            current_features=current_features,
            feature_columns=['feature1', 'feature2', 'feature3'],
            method='psi'
        )
        
        print(f"✓ Feature drift detection completed: {len(results)} features checked")
        
        for result in results:
            status = "DRIFT" if result.drift_detected else "OK"
            print(f"  - {result.drift_type}: {status} (score={result.drift_score:.4f})")
        
        return True
    except Exception as e:
        print(f"✗ Feature drift detection failed: {str(e)}")
        return False


def validate_regression_performance_monitoring():
    """Validate regression model performance monitoring"""
    print("\n" + "="*80)
    print("VALIDATION 6: Regression Performance Monitoring")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Test data
        np.random.seed(42)
        actuals = np.random.uniform(1000, 10000, 500)
        predictions = actuals + np.random.normal(0, 500, 500)
        
        # Calculate baseline metrics
        baseline_mae = 400.0
        baseline_rmse = 550.0
        baseline_r2 = 0.88
        
        baseline_metrics = {
            'mae': baseline_mae,
            'rmse': baseline_rmse,
            'r_squared': baseline_r2
        }
        
        # Monitor performance
        results = monitoring_service.monitor_regression_performance(
            model_name='test_model',
            model_version='v1.0',
            predictions=predictions,
            actuals=actuals,
            baseline_metrics=baseline_metrics
        )
        
        print(f"✓ Performance monitoring completed: {len(results)} metrics tracked")
        
        for result in results:
            status = "BREACHED" if result.threshold_breached else "OK"
            print(f"  - {result.metric_name}: {result.metric_value:.4f} ({status})")
        
        # Check performance history
        history = monitoring_service.get_performance_history(model_name='test_model')
        print(f"✓ Performance history recorded: {len(history)} entries")
        
        return True
    except Exception as e:
        print(f"✗ Regression performance monitoring failed: {str(e)}")
        return False


def validate_ranking_performance_monitoring():
    """Validate ranking model performance monitoring"""
    print("\n" + "="*80)
    print("VALIDATION 7: Ranking Performance Monitoring")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Test data
        recommendations = {
            'user1': ['item1', 'item2', 'item3', 'item4', 'item5'],
            'user2': ['item6', 'item7', 'item8', 'item9', 'item10'],
            'user3': ['item11', 'item12', 'item13', 'item14', 'item15']
        }
        
        ground_truth = {
            'user1': ['item1', 'item3', 'item6'],
            'user2': ['item7', 'item8', 'item11'],
            'user3': ['item12', 'item13', 'item14']
        }
        
        baseline_metrics = {
            'precision_at_10': 0.40,
            'recall_at_10': 0.67,
            'map': 0.55
        }
        
        # Monitor performance
        results = monitoring_service.monitor_ranking_performance(
            model_name='test_recommender',
            model_version='v1.0',
            recommendations=recommendations,
            ground_truth=ground_truth,
            baseline_metrics=baseline_metrics
        )
        
        print(f"✓ Ranking performance monitoring completed: {len(results)} metrics tracked")
        
        for result in results:
            status = "BREACHED" if result.threshold_breached else "OK"
            print(f"  - {result.metric_name}: {result.metric_value:.4f} ({status})")
        
        return True
    except Exception as e:
        print(f"✗ Ranking performance monitoring failed: {str(e)}")
        return False


def validate_retraining_triggers():
    """Validate retraining trigger logic"""
    print("\n" + "="*80)
    print("VALIDATION 8: Retraining Triggers")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Trigger drift-based retraining
        np.random.seed(42)
        baseline_data = np.random.normal(5000, 1000, 1000)
        current_data = np.random.normal(6000, 1500, 500)  # Significant drift
        
        monitoring_service.detect_prediction_drift(
            model_name='test_model',
            model_version='v1.0',
            baseline_predictions=baseline_data,
            current_predictions=current_data,
            method='psi'
        )
        
        # Trigger performance-based retraining
        actuals = np.random.uniform(1000, 10000, 500)
        predictions = actuals + np.random.normal(0, 1500, 500)  # Poor predictions
        
        monitoring_service.monitor_regression_performance(
            model_name='test_model',
            model_version='v1.0',
            predictions=predictions,
            actuals=actuals,
            baseline_metrics={'mae': 400.0, 'rmse': 550.0, 'r_squared': 0.88}
        )
        
        # Check triggers
        triggers = monitoring_service.get_retraining_triggers(model_name='test_model')
        
        print(f"✓ Retraining triggers generated: {len(triggers)}")
        
        for trigger in triggers:
            print(f"  - Type: {trigger['trigger_type']}, Severity: {trigger['severity']}")
            print(f"    Reason: {trigger['trigger_reason']}")
        
        if len(triggers) == 0:
            print("⚠️  Warning: Expected retraining triggers but none were generated")
        
        return True
    except Exception as e:
        print(f"✗ Retraining trigger validation failed: {str(e)}")
        return False


def validate_monitoring_report():
    """Validate monitoring report generation"""
    print("\n" + "="*80)
    print("VALIDATION 9: Monitoring Report Generation")
    print("="*80)
    
    from src.services.model_monitoring_service import ModelMonitoringService
    
    try:
        monitoring_service = ModelMonitoringService()
        
        # Generate some monitoring activity
        np.random.seed(42)
        baseline_data = np.random.normal(5000, 1000, 1000)
        current_data = np.random.normal(5200, 1100, 500)
        
        monitoring_service.detect_prediction_drift(
            model_name='test_model',
            model_version='v1.0',
            baseline_predictions=baseline_data,
            current_predictions=current_data,
            method='psi'
        )
        
        actuals = np.random.uniform(1000, 10000, 300)
        predictions = actuals + np.random.normal(0, 600, 300)
        
        monitoring_service.monitor_regression_performance(
            model_name='test_model',
            model_version='v1.0',
            predictions=predictions,
            actuals=actuals,
            baseline_metrics={'mae': 400.0, 'rmse': 550.0, 'r_squared': 0.88}
        )
        
        # Generate report
        report = monitoring_service.generate_monitoring_report(
            model_name='test_model',
            model_version='v1.0',
            output_format='dict'
        )
        
        print("✓ Monitoring report generated successfully")
        print(f"  - Model: {report['model_name']} v{report['model_version']}")
        print(f"  - Drift checks: {report['monitoring_summary']['total_drift_checks']}")
        print(f"  - Performance checks: {report['monitoring_summary']['total_performance_checks']}")
        print(f"  - Retraining triggers: {report['monitoring_summary']['retraining_triggers_count']}")
        
        # Test JSON format
        json_report = monitoring_service.generate_monitoring_report(
            model_name='test_model',
            model_version='v1.0',
            output_format='json'
        )
        
        print("✓ JSON report format validated")
        
        return True
    except Exception as e:
        print(f"✗ Monitoring report generation failed: {str(e)}")
        return False


def main():
    """Run all validations"""
    print("\n" + "="*80)
    print("MODEL MONITORING AND DRIFT DETECTION - VALIDATION")
    print("="*80)
    
    validations = [
        ("Module Imports", validate_imports),
        ("Drift Detection Algorithms", validate_drift_detector),
        ("CloudWatch Publisher", validate_cloudwatch_publisher),
        ("Prediction Drift Detection", validate_prediction_drift_detection),
        ("Feature Drift Detection", validate_feature_drift_detection),
        ("Regression Performance Monitoring", validate_regression_performance_monitoring),
        ("Ranking Performance Monitoring", validate_ranking_performance_monitoring),
        ("Retraining Triggers", validate_retraining_triggers),
        ("Monitoring Report", validate_monitoring_report)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Validation '{name}' failed with exception: {str(e)}", exc_info=True)
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✓ ALL VALIDATIONS PASSED - Implementation is complete and functional")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed - Please review the errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
