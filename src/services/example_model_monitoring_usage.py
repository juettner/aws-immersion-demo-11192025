"""
Example usage of Model Monitoring and Drift Detection Service

Demonstrates:
- Prediction drift detection using PSI and KS test
- Feature drift detection across multiple features
- Performance monitoring for regression and ranking models
- CloudWatch metrics publishing
- Automated retraining triggers
- CloudWatch alarm creation
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

from src.services.model_monitoring_service import (
    ModelMonitoringService,
    DriftDetector,
    CloudWatchMetricsPublisher
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_prediction_drift_detection():
    """Example: Detect drift in model predictions"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Prediction Drift Detection")
    print("="*80)
    
    # Initialize monitoring service
    monitoring_service = ModelMonitoringService(
        cloudwatch_namespace='MLModels/Demo',
        thresholds={
            'drift_psi_threshold': 0.2,
            'drift_ks_pvalue': 0.05
        }
    )
    
    # Simulate baseline predictions (historical data)
    np.random.seed(42)
    baseline_predictions = np.random.normal(loc=5000, scale=1000, size=1000)
    
    # Simulate current predictions with drift (distribution shift)
    current_predictions = np.random.normal(loc=5500, scale=1200, size=500)
    
    print(f"\nBaseline predictions: mean={baseline_predictions.mean():.2f}, std={baseline_predictions.std():.2f}")
    print(f"Current predictions: mean={current_predictions.mean():.2f}, std={current_predictions.std():.2f}")
    
    # Detect drift using PSI
    print("\n--- PSI Method ---")
    drift_result_psi = monitoring_service.detect_prediction_drift(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        baseline_predictions=baseline_predictions,
        current_predictions=current_predictions,
        method='psi',
        baseline_period='last_30_days',
        current_period='last_7_days'
    )
    
    print(f"Drift detected: {drift_result_psi.drift_detected}")
    print(f"PSI score: {drift_result_psi.drift_score:.4f}")
    print(f"Threshold: {drift_result_psi.threshold}")
    
    # Detect drift using KS test
    print("\n--- KS Test Method ---")
    drift_result_ks = monitoring_service.detect_prediction_drift(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        baseline_predictions=baseline_predictions,
        current_predictions=current_predictions,
        method='ks_test',
        baseline_period='last_30_days',
        current_period='last_7_days'
    )
    
    print(f"Drift detected: {drift_result_ks.drift_detected}")
    print(f"KS statistic: {drift_result_ks.drift_score:.4f}")
    print(f"P-value: {drift_result_ks.p_value:.4f}")
    print(f"Threshold: {drift_result_ks.threshold}")
    
    # Check retraining triggers
    triggers = monitoring_service.get_retraining_triggers(
        model_name='ticket_sales_predictor'
    )
    
    if triggers:
        print(f"\n⚠️  Retraining triggers generated: {len(triggers)}")
        for trigger in triggers:
            print(f"  - {trigger['trigger_reason']} (severity: {trigger['severity']})")


def example_feature_drift_detection():
    """Example: Detect drift in input features"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Feature Drift Detection")
    print("="*80)
    
    monitoring_service = ModelMonitoringService()
    
    # Simulate baseline features
    np.random.seed(42)
    baseline_features = pd.DataFrame({
        'artist_popularity': np.random.uniform(0, 100, 1000),
        'venue_capacity': np.random.randint(100, 10000, 1000),
        'ticket_price': np.random.uniform(20, 200, 1000),
        'days_until_event': np.random.randint(1, 365, 1000)
    })
    
    # Simulate current features with drift in some features
    current_features = pd.DataFrame({
        'artist_popularity': np.random.uniform(10, 110, 500),  # Slight shift
        'venue_capacity': np.random.randint(100, 10000, 500),  # No drift
        'ticket_price': np.random.uniform(50, 250, 500),  # Significant shift
        'days_until_event': np.random.randint(1, 365, 500)  # No drift
    })
    
    print("\nBaseline feature statistics:")
    print(baseline_features.describe())
    
    print("\nCurrent feature statistics:")
    print(current_features.describe())
    
    # Detect feature drift
    drift_results = monitoring_service.detect_feature_drift(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        baseline_features=baseline_features,
        current_features=current_features,
        feature_columns=['artist_popularity', 'venue_capacity', 'ticket_price', 'days_until_event'],
        method='psi'
    )
    
    print(f"\n--- Feature Drift Results ---")
    for result in drift_results:
        status = "⚠️  DRIFT DETECTED" if result.drift_detected else "✓ No drift"
        print(f"{result.drift_type}: {status} (PSI={result.drift_score:.4f})")


def example_regression_performance_monitoring():
    """Example: Monitor regression model performance"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Regression Model Performance Monitoring")
    print("="*80)
    
    monitoring_service = ModelMonitoringService(
        thresholds={
            'mae_increase_pct': 15.0,
            'rmse_increase_pct': 15.0,
            'r_squared_decrease_pct': 10.0
        }
    )
    
    # Simulate baseline performance
    np.random.seed(42)
    baseline_actuals = np.random.uniform(1000, 10000, 500)
    baseline_predictions = baseline_actuals + np.random.normal(0, 500, 500)
    
    # Calculate baseline metrics
    baseline_mae = np.mean(np.abs(baseline_predictions - baseline_actuals))
    baseline_rmse = np.sqrt(np.mean((baseline_predictions - baseline_actuals) ** 2))
    ss_res = np.sum((baseline_actuals - baseline_predictions) ** 2)
    ss_tot = np.sum((baseline_actuals - np.mean(baseline_actuals)) ** 2)
    baseline_r2 = 1 - (ss_res / ss_tot)
    
    baseline_metrics = {
        'mae': baseline_mae,
        'rmse': baseline_rmse,
        'r_squared': baseline_r2
    }
    
    print(f"\nBaseline metrics:")
    print(f"  MAE: {baseline_mae:.2f}")
    print(f"  RMSE: {baseline_rmse:.2f}")
    print(f"  R²: {baseline_r2:.4f}")
    
    # Simulate current performance with degradation
    current_actuals = np.random.uniform(1000, 10000, 300)
    current_predictions = current_actuals + np.random.normal(0, 800, 300)  # Worse predictions
    
    print(f"\n--- Monitoring Current Performance ---")
    performance_results = monitoring_service.monitor_regression_performance(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        predictions=current_predictions,
        actuals=current_actuals,
        baseline_metrics=baseline_metrics,
        time_period='last_7_days'
    )
    
    print(f"\nPerformance monitoring results:")
    for result in performance_results:
        status = "⚠️  THRESHOLD BREACHED" if result.threshold_breached else "✓ Within threshold"
        print(f"  {result.metric_name.upper()}: {result.metric_value:.4f} - {status}")
    
    # Check retraining triggers
    triggers = monitoring_service.get_retraining_triggers(
        model_name='ticket_sales_predictor',
        severity='high'
    )
    
    if triggers:
        print(f"\n⚠️  High severity retraining triggers: {len(triggers)}")
        for trigger in triggers:
            print(f"  - {trigger['trigger_reason']}")


def example_ranking_performance_monitoring():
    """Example: Monitor ranking/recommendation model performance"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Ranking Model Performance Monitoring")
    print("="*80)
    
    monitoring_service = ModelMonitoringService(
        thresholds={
            'precision_decrease_pct': 10.0,
            'recall_decrease_pct': 10.0,
            'map_decrease_pct': 10.0
        }
    )
    
    # Simulate baseline recommendations
    baseline_recommendations = {
        'user1': ['item1', 'item2', 'item3', 'item4', 'item5'],
        'user2': ['item6', 'item7', 'item8', 'item9', 'item10'],
        'user3': ['item11', 'item12', 'item13', 'item14', 'item15']
    }
    
    ground_truth = {
        'user1': ['item1', 'item3', 'item6'],
        'user2': ['item7', 'item8', 'item11'],
        'user3': ['item12', 'item13', 'item14']
    }
    
    # Calculate baseline metrics (simplified)
    baseline_metrics = {
        'precision_at_10': 0.40,
        'recall_at_10': 0.67,
        'map': 0.55
    }
    
    print(f"\nBaseline metrics:")
    print(f"  Precision@10: {baseline_metrics['precision_at_10']:.4f}")
    print(f"  Recall@10: {baseline_metrics['recall_at_10']:.4f}")
    print(f"  MAP: {baseline_metrics['map']:.4f}")
    
    # Simulate current recommendations with degradation
    current_recommendations = {
        'user1': ['item2', 'item4', 'item5', 'item7', 'item8'],  # Worse recommendations
        'user2': ['item6', 'item9', 'item10', 'item11', 'item12'],
        'user3': ['item11', 'item15', 'item16', 'item17', 'item18']
    }
    
    print(f"\n--- Monitoring Current Performance ---")
    performance_results = monitoring_service.monitor_ranking_performance(
        model_name='concert_recommender',
        model_version='v1.0',
        recommendations=current_recommendations,
        ground_truth=ground_truth,
        baseline_metrics=baseline_metrics,
        time_period='last_7_days'
    )
    
    print(f"\nPerformance monitoring results:")
    for result in performance_results:
        status = "⚠️  THRESHOLD BREACHED" if result.threshold_breached else "✓ Within threshold"
        print(f"  {result.metric_name.upper()}: {result.metric_value:.4f} - {status}")


def example_cloudwatch_integration():
    """Example: CloudWatch metrics publishing and alarm creation"""
    print("\n" + "="*80)
    print("EXAMPLE 5: CloudWatch Integration")
    print("="*80)
    
    # Initialize metrics publisher
    metrics_publisher = CloudWatchMetricsPublisher(
        namespace='MLModels/Demo'
    )
    
    print("\n--- Publishing Metrics to CloudWatch ---")
    
    # Publish single metric
    success = metrics_publisher.publish_model_metric(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        metric_name='MAE',
        metric_value=450.25,
        unit='None'
    )
    print(f"Single metric published: {success}")
    
    # Publish batch metrics
    metrics = {
        'MAE': 450.25,
        'RMSE': 625.50,
        'R_Squared': 0.85,
        'MAPE': 12.5
    }
    
    success_count = metrics_publisher.publish_batch_metrics(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        metrics=metrics,
        unit='None'
    )
    print(f"Batch metrics published: {success_count}/{len(metrics)}")
    
    # Publish drift metrics
    success = metrics_publisher.publish_drift_metric(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        drift_score=0.25,
        drift_detected=True
    )
    print(f"Drift metrics published: {success}")
    
    # Note: Creating alarms requires SNS topic ARN
    print("\n--- CloudWatch Alarm Creation ---")
    print("To create CloudWatch alarms, you need:")
    print("1. An SNS topic ARN for notifications")
    print("2. Appropriate IAM permissions")
    print("\nExample code:")
    print("""
    monitoring_service = ModelMonitoringService()
    alarm_names = monitoring_service.create_cloudwatch_alarms(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        sns_topic_arn='arn:aws:sns:us-east-1:123456789012:model-alerts',
        alarm_prefix='MLModel'
    )
    print(f"Created alarms: {alarm_names}")
    """)


def example_monitoring_report():
    """Example: Generate comprehensive monitoring report"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Monitoring Report Generation")
    print("="*80)
    
    monitoring_service = ModelMonitoringService()
    
    # Simulate some monitoring activity
    np.random.seed(42)
    
    # Add drift detection results
    baseline_data = np.random.normal(5000, 1000, 1000)
    current_data = np.random.normal(5200, 1100, 500)
    
    monitoring_service.detect_prediction_drift(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        baseline_predictions=baseline_data,
        current_predictions=current_data,
        method='psi'
    )
    
    # Add performance monitoring results
    actuals = np.random.uniform(1000, 10000, 300)
    predictions = actuals + np.random.normal(0, 600, 300)
    
    monitoring_service.monitor_regression_performance(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        predictions=predictions,
        actuals=actuals,
        baseline_metrics={'mae': 400.0, 'rmse': 550.0, 'r_squared': 0.88}
    )
    
    # Generate report
    report = monitoring_service.generate_monitoring_report(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        output_format='dict'
    )
    
    print("\n--- Monitoring Report ---")
    print(f"Model: {report['model_name']} v{report['model_version']}")
    print(f"\nSummary:")
    summary = report['monitoring_summary']
    print(f"  Total drift checks: {summary['total_drift_checks']}")
    print(f"  Drift detected: {summary['drift_detected_count']}")
    print(f"  Drift detection rate: {summary['drift_detection_rate']:.2%}")
    print(f"  Performance checks: {summary['total_performance_checks']}")
    print(f"  Performance issues: {summary['performance_issues_count']}")
    print(f"  Retraining triggers: {summary['retraining_triggers_count']}")
    
    if report['retraining_triggers']:
        print(f"\n⚠️  Retraining Triggers:")
        for trigger in report['retraining_triggers']:
            print(f"  - {trigger['trigger_reason']} ({trigger['severity']})")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MODEL MONITORING AND DRIFT DETECTION SERVICE - EXAMPLES")
    print("="*80)
    
    try:
        example_prediction_drift_detection()
        example_feature_drift_detection()
        example_regression_performance_monitoring()
        example_ranking_performance_monitoring()
        example_cloudwatch_integration()
        example_monitoring_report()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
