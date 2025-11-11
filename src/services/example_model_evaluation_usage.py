"""
Example usage of Model Evaluation Service

Demonstrates how to:
- Evaluate regression models (venue popularity, ticket sales)
- Evaluate ranking models (recommendations)
- Split datasets for validation
- Compare model versions for A/B testing
- Generate performance reports with visualization data
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.services.model_evaluation_service import (
    ModelEvaluationService,
    DatasetSplitter,
    PerformanceVisualizer
)


def example_regression_evaluation():
    """Example: Evaluate a regression model (ticket sales prediction)"""
    print("\n=== Regression Model Evaluation Example ===\n")
    
    # Initialize evaluation service
    eval_service = ModelEvaluationService()
    
    # Simulate predictions and actuals for ticket sales
    np.random.seed(42)
    actuals = np.random.uniform(1000, 50000, 100)
    
    # Model v1.0 predictions (with some error)
    predictions_v1 = actuals + np.random.normal(0, 5000, 100)
    
    # Evaluate model v1.0
    metrics_v1 = eval_service.evaluate_regression_model(
        model_name='ticket_sales_predictor',
        model_version='v1.0',
        predictions=predictions_v1,
        actuals=actuals
    )
    
    print(f"Model: {metrics_v1.model_name} v{metrics_v1.model_version}")
    print(f"MAE: ${metrics_v1.mae:,.2f}")
    print(f"RMSE: ${metrics_v1.rmse:,.2f}")
    print(f"MAPE: {metrics_v1.mape:.2f}%")
    print(f"R²: {metrics_v1.r_squared:.3f}")
    print(f"Predictions: {metrics_v1.num_predictions}")
    
    return eval_service, actuals


def example_model_comparison():
    """Example: Compare two model versions"""
    print("\n=== Model Comparison Example ===\n")
    
    eval_service = ModelEvaluationService()
    
    # Simulate test data
    np.random.seed(42)
    actuals = np.random.uniform(1000, 50000, 100)
    
    # Baseline model (v1.0) - higher error
    baseline_predictions = actuals + np.random.normal(0, 5000, 100)
    
    # Challenger model (v2.0) - lower error (improved)
    challenger_predictions = actuals + np.random.normal(0, 3000, 100)
    
    # Compare models
    comparison = eval_service.compare_regression_models(
        model_name='ticket_sales_predictor',
        baseline_version='v1.0',
        challenger_version='v2.0',
        baseline_predictions=baseline_predictions,
        challenger_predictions=challenger_predictions,
        actuals=actuals
    )
    
    print(f"Comparison: {comparison.baseline_version} vs {comparison.challenger_version}")
    print(f"Winner: {comparison.winner} (confidence: {comparison.confidence:.2f})")
    print("\nMetric Improvements:")
    
    for metric, values in comparison.metric_comparisons.items():
        print(f"  {metric}:")
        print(f"    Baseline: {values['baseline']:.2f}")
        print(f"    Challenger: {values['challenger']:.2f}")
        print(f"    Improvement: {values['improvement_pct']:.2f}%")
    
    return comparison


def example_ranking_evaluation():
    """Example: Evaluate a ranking/recommendation model"""
    print("\n=== Ranking Model Evaluation Example ===\n")
    
    eval_service = ModelEvaluationService()
    
    # Simulate recommendations for 5 users
    recommendations = {
        'user1': ['concert1', 'concert2', 'concert3', 'concert4', 'concert5'],
        'user2': ['concert6', 'concert7', 'concert8', 'concert9', 'concert10'],
        'user3': ['concert11', 'concert12', 'concert13', 'concert14', 'concert15'],
        'user4': ['concert16', 'concert17', 'concert18', 'concert19', 'concert20'],
        'user5': ['concert21', 'concert22', 'concert23', 'concert24', 'concert25']
    }
    
    # Ground truth (relevant items)
    ground_truth = {
        'user1': ['concert1', 'concert3', 'concert7'],  # 2 out of 5 correct
        'user2': ['concert6', 'concert8', 'concert11'],  # 2 out of 5 correct
        'user3': ['concert12', 'concert13', 'concert14'],  # 3 out of 5 correct
        'user4': ['concert16', 'concert19', 'concert20'],  # 2 out of 5 correct
        'user5': ['concert21', 'concert25', 'concert30']  # 2 out of 5 correct
    }
    
    # Evaluate ranking model
    metrics = eval_service.evaluate_ranking_model(
        model_name='concert_recommender',
        model_version='v1.0',
        recommendations=recommendations,
        ground_truth=ground_truth,
        k_values=[3, 5, 10]
    )
    
    print(f"Model: {metrics.model_name} v{metrics.model_version}")
    print(f"Users evaluated: {metrics.num_users_evaluated}")
    print("\nPrecision@k:")
    for k, value in metrics.precision_at_k.items():
        print(f"  @{k}: {value:.3f}")
    
    print("\nRecall@k:")
    for k, value in metrics.recall_at_k.items():
        print(f"  @{k}: {value:.3f}")
    
    print("\nNDCG@k:")
    for k, value in metrics.ndcg_at_k.items():
        print(f"  @{k}: {value:.3f}")
    
    print(f"\nMAP: {metrics.map_score:.3f}")
    
    return metrics


def example_dataset_splitting():
    """Example: Split dataset for validation"""
    print("\n=== Dataset Splitting Example ===\n")
    
    # Create sample dataset
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    data = pd.DataFrame({
        'date': dates,
        'concert_id': [f'concert_{i}' for i in range(len(dates))],
        'sales': np.random.uniform(1000, 50000, len(dates)),
        'venue_type': np.random.choice(['arena', 'theater', 'club'], len(dates))
    })
    
    print(f"Total dataset size: {len(data)} records")
    
    # Temporal split (for time-series data)
    print("\n1. Temporal Split:")
    train, val, test = DatasetSplitter.temporal_split(
        data=data,
        date_column='date',
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    print(f"   Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    print(f"   Train dates: {train['date'].min()} to {train['date'].max()}")
    print(f"   Test dates: {test['date'].min()} to {test['date'].max()}")
    
    # Random split
    print("\n2. Random Split:")
    train, val, test = DatasetSplitter.random_split(
        data=data,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42
    )
    print(f"   Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    
    # Stratified split (maintain venue type distribution)
    print("\n3. Stratified Split (by venue_type):")
    train, val, test = DatasetSplitter.stratified_split(
        data=data,
        stratify_column='venue_type',
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42
    )
    print(f"   Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    print(f"   Train venue distribution:")
    print(f"   {train['venue_type'].value_counts(normalize=True)}")
    print(f"   Test venue distribution:")
    print(f"   {test['venue_type'].value_counts(normalize=True)}")


def example_performance_report():
    """Example: Generate performance report"""
    print("\n=== Performance Report Example ===\n")
    
    eval_service = ModelEvaluationService()
    
    # Run some evaluations
    np.random.seed(42)
    actuals = np.random.uniform(1000, 50000, 100)
    predictions = actuals + np.random.normal(0, 4000, 100)
    
    eval_service.evaluate_regression_model(
        model_name='venue_popularity',
        model_version='v1.0',
        predictions=predictions,
        actuals=actuals
    )
    
    # Generate report
    report = eval_service.generate_performance_report(
        model_name='venue_popularity',
        model_version='v1.0',
        output_format='dict'
    )
    
    print(f"Model: {report['model_name']} v{report['model_version']}")
    print(f"Number of evaluations: {report['num_evaluations']}")
    print(f"Report generated at: {report['report_generated_at']}")
    
    if report['evaluations']:
        latest = report['evaluations'][-1]
        print(f"\nLatest evaluation:")
        print(f"  MAE: {latest['mae']:.2f}")
        print(f"  RMSE: {latest['rmse']:.2f}")
        print(f"  R²: {latest['r_squared']:.3f}")


def example_visualization_data():
    """Example: Prepare data for visualization"""
    print("\n=== Visualization Data Example ===\n")
    
    eval_service = ModelEvaluationService()
    
    # Simulate multiple model versions
    np.random.seed(42)
    actuals = np.random.uniform(1000, 50000, 100)
    
    metrics_list = []
    for i, error_std in enumerate([5000, 4000, 3500], start=1):
        predictions = actuals + np.random.normal(0, error_std, 100)
        metrics = eval_service.evaluate_regression_model(
            model_name='ticket_sales_predictor',
            model_version=f'v{i}.0',
            predictions=predictions,
            actuals=actuals
        )
        metrics_list.append(metrics)
    
    # Prepare chart data
    chart_data = PerformanceVisualizer.prepare_regression_metrics_chart_data(metrics_list)
    
    print("Chart data prepared for visualization:")
    print(f"  Title: {chart_data['title']}")
    print(f"  Labels: {chart_data['labels']}")
    print(f"  Datasets: {len(chart_data['datasets'])} series")
    print(f"  MAE values: {chart_data['datasets'][0]['data']}")
    print(f"  R² values: {chart_data['datasets'][2]['data']}")
    
    print("\nThis data can be used with charting libraries like:")
    print("  - Chart.js (web)")
    print("  - Matplotlib (Python)")
    print("  - Recharts (React)")


def example_ranking_comparison():
    """Example: Compare two ranking model versions"""
    print("\n=== Ranking Model Comparison Example ===\n")
    
    eval_service = ModelEvaluationService()
    
    # Ground truth
    ground_truth = {
        'user1': ['concert1', 'concert3', 'concert7'],
        'user2': ['concert6', 'concert8', 'concert11'],
        'user3': ['concert12', 'concert13', 'concert14']
    }
    
    # Baseline recommendations (v1.0) - less accurate
    baseline_recs = {
        'user1': ['concert1', 'concert2', 'concert4', 'concert5', 'concert6'],
        'user2': ['concert6', 'concert7', 'concert9', 'concert10', 'concert11'],
        'user3': ['concert12', 'concert15', 'concert16', 'concert17', 'concert18']
    }
    
    # Challenger recommendations (v2.0) - more accurate
    challenger_recs = {
        'user1': ['concert1', 'concert3', 'concert7', 'concert2', 'concert4'],
        'user2': ['concert6', 'concert8', 'concert11', 'concert7', 'concert9'],
        'user3': ['concert12', 'concert13', 'concert14', 'concert15', 'concert16']
    }
    
    # Compare models
    comparison = eval_service.compare_ranking_models(
        model_name='concert_recommender',
        baseline_version='v1.0',
        challenger_version='v2.0',
        baseline_recommendations=baseline_recs,
        challenger_recommendations=challenger_recs,
        ground_truth=ground_truth,
        k_values=[3, 5, 10]
    )
    
    print(f"Comparison: {comparison.baseline_version} vs {comparison.challenger_version}")
    print(f"Winner: {comparison.winner} (confidence: {comparison.confidence:.2f})")
    print("\nMetric Improvements:")
    
    for metric, values in comparison.metric_comparisons.items():
        print(f"  {metric}:")
        print(f"    Baseline: {values['baseline']:.3f}")
        print(f"    Challenger: {values['challenger']:.3f}")
        print(f"    Improvement: {values['improvement_pct']:.2f}%")


def main():
    """Run all examples"""
    print("=" * 70)
    print("Model Evaluation Service - Usage Examples")
    print("=" * 70)
    
    # Run examples
    example_regression_evaluation()
    example_model_comparison()
    example_ranking_evaluation()
    example_dataset_splitting()
    example_performance_report()
    example_visualization_data()
    example_ranking_comparison()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
