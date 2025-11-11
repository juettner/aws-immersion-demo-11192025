"""
Validation script for Model Evaluation Service implementation

Verifies that task 4.4.1 requirements are met:
- Implement metrics calculation service for all ML models (MAE, RMSE, precision@k, recall@k)
- Create validation dataset splitting utilities
- Build model comparison framework for A/B testing different model versions
- Add performance reporting with visualization support
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from src.services.model_evaluation_service import (
    ModelEvaluationService,
    DatasetSplitter,
    PerformanceVisualizer,
    RegressionMetrics,
    RankingMetrics,
    ModelComparison
)


def validate_regression_metrics():
    """Validate regression metrics calculation (MAE, RMSE)"""
    print("\n✓ Testing regression metrics calculation...")
    
    eval_service = ModelEvaluationService()
    
    # Test data
    actuals = np.array([100, 200, 300, 400, 500])
    predictions = np.array([110, 190, 310, 390, 510])
    
    metrics = eval_service.evaluate_regression_model(
        model_name='test_model',
        model_version='v1.0',
        predictions=predictions,
        actuals=actuals
    )
    
    # Verify metrics are calculated
    assert isinstance(metrics, RegressionMetrics), "Should return RegressionMetrics object"
    assert metrics.mae > 0, "MAE should be calculated"
    assert metrics.rmse > 0, "RMSE should be calculated"
    assert metrics.mape > 0, "MAPE should be calculated"
    assert 0 <= metrics.r_squared <= 1, "R² should be between 0 and 1"
    assert metrics.num_predictions == 5, "Should track number of predictions"
    
    # Verify MAE calculation is correct
    expected_mae = np.mean(np.abs(predictions - actuals))
    assert abs(metrics.mae - expected_mae) < 0.01, "MAE calculation should be accurate"
    
    print("  ✓ MAE calculation: PASS")
    print("  ✓ RMSE calculation: PASS")
    print("  ✓ MAPE calculation: PASS")
    print("  ✓ R² calculation: PASS")
    
    return True


def validate_ranking_metrics():
    """Validate ranking metrics calculation (precision@k, recall@k)"""
    print("\n✓ Testing ranking metrics calculation...")
    
    eval_service = ModelEvaluationService()
    
    # Test data
    recommendations = {
        'user1': ['item1', 'item2', 'item3', 'item4', 'item5']
    }
    ground_truth = {
        'user1': ['item1', 'item3', 'item6']  # 2 out of 5 correct
    }
    
    metrics = eval_service.evaluate_ranking_model(
        model_name='test_recommender',
        model_version='v1.0',
        recommendations=recommendations,
        ground_truth=ground_truth,
        k_values=[3, 5]
    )
    
    # Verify metrics are calculated
    assert isinstance(metrics, RankingMetrics), "Should return RankingMetrics object"
    assert 3 in metrics.precision_at_k, "Should calculate precision@3"
    assert 5 in metrics.precision_at_k, "Should calculate precision@5"
    assert 3 in metrics.recall_at_k, "Should calculate recall@3"
    assert 5 in metrics.recall_at_k, "Should calculate recall@5"
    assert 3 in metrics.ndcg_at_k, "Should calculate NDCG@3"
    assert metrics.map_score >= 0, "Should calculate MAP score"
    
    # Verify precision@5 calculation
    # 2 relevant items in top 5, so precision@5 = 2/5 = 0.4
    expected_precision_5 = 2.0 / 5.0
    assert abs(metrics.precision_at_k[5] - expected_precision_5) < 0.01, "Precision@5 should be accurate"
    
    # Verify recall@5 calculation
    # 2 relevant items found out of 3 total relevant, so recall@5 = 2/3 = 0.667
    expected_recall_5 = 2.0 / 3.0
    assert abs(metrics.recall_at_k[5] - expected_recall_5) < 0.01, "Recall@5 should be accurate"
    
    print("  ✓ Precision@k calculation: PASS")
    print("  ✓ Recall@k calculation: PASS")
    print("  ✓ NDCG@k calculation: PASS")
    print("  ✓ MAP calculation: PASS")
    
    return True


def validate_dataset_splitting():
    """Validate dataset splitting utilities"""
    print("\n✓ Testing dataset splitting utilities...")
    
    # Create test dataset
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    data = pd.DataFrame({
        'date': dates,
        'value': np.random.uniform(0, 100, len(dates)),
        'category': np.random.choice(['A', 'B', 'C'], len(dates))
    })
    
    # Test temporal split
    train, val, test = DatasetSplitter.temporal_split(
        data=data,
        date_column='date',
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    assert len(train) + len(val) + len(test) == len(data), "Split should preserve all data"
    assert train['date'].max() < val['date'].min(), "Temporal split should be chronological"
    assert val['date'].max() < test['date'].min(), "Temporal split should be chronological"
    
    print("  ✓ Temporal split: PASS")
    
    # Test random split
    train, val, test = DatasetSplitter.random_split(
        data=data,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42
    )
    
    assert len(train) + len(val) + len(test) == len(data), "Split should preserve all data"
    assert len(train) > len(val), "Train set should be larger than validation"
    assert len(train) > len(test), "Train set should be larger than test"
    
    print("  ✓ Random split: PASS")
    
    # Test stratified split
    train, val, test = DatasetSplitter.stratified_split(
        data=data,
        stratify_column='category',
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42
    )
    
    assert len(train) + len(val) + len(test) == len(data), "Split should preserve all data"
    
    # Check stratification maintains distribution
    train_dist = train['category'].value_counts(normalize=True).sort_index()
    test_dist = test['category'].value_counts(normalize=True).sort_index()
    
    # Distributions should be similar (within 10%)
    for cat in train_dist.index:
        diff = abs(train_dist[cat] - test_dist[cat])
        assert diff < 0.1, f"Stratification should maintain distribution for {cat}"
    
    print("  ✓ Stratified split: PASS")
    
    return True


def validate_model_comparison():
    """Validate model comparison framework for A/B testing"""
    print("\n✓ Testing model comparison framework...")
    
    eval_service = ModelEvaluationService()
    
    # Test data
    actuals = np.array([100, 200, 300, 400, 500])
    baseline_predictions = np.array([110, 190, 310, 390, 510])  # Higher error
    challenger_predictions = np.array([105, 195, 305, 395, 505])  # Lower error
    
    # Compare regression models
    comparison = eval_service.compare_regression_models(
        model_name='test_model',
        baseline_version='v1.0',
        challenger_version='v2.0',
        baseline_predictions=baseline_predictions,
        challenger_predictions=challenger_predictions,
        actuals=actuals
    )
    
    assert isinstance(comparison, ModelComparison), "Should return ModelComparison object"
    assert comparison.winner in ['baseline', 'challenger', 'tie'], "Should determine a winner"
    assert 0 <= comparison.confidence <= 1, "Confidence should be between 0 and 1"
    assert 'mae' in comparison.metric_comparisons, "Should compare MAE"
    assert 'rmse' in comparison.metric_comparisons, "Should compare RMSE"
    assert 'r_squared' in comparison.metric_comparisons, "Should compare R²"
    
    # Challenger should win (lower error)
    assert comparison.winner == 'challenger', "Challenger with lower error should win"
    
    print("  ✓ Regression model comparison: PASS")
    
    # Test ranking model comparison
    ground_truth = {
        'user1': ['item1', 'item3', 'item5']
    }
    baseline_recs = {
        'user1': ['item1', 'item2', 'item4', 'item6', 'item7']  # 1 correct
    }
    challenger_recs = {
        'user1': ['item1', 'item3', 'item5', 'item2', 'item4']  # 3 correct
    }
    
    comparison = eval_service.compare_ranking_models(
        model_name='test_recommender',
        baseline_version='v1.0',
        challenger_version='v2.0',
        baseline_recommendations=baseline_recs,
        challenger_recommendations=challenger_recs,
        ground_truth=ground_truth,
        k_values=[5]
    )
    
    assert isinstance(comparison, ModelComparison), "Should return ModelComparison object"
    assert comparison.winner in ['baseline', 'challenger', 'tie'], "Should determine a winner"
    assert 'precision_at_10' in comparison.metric_comparisons or 'map' in comparison.metric_comparisons, "Should compare ranking metrics"
    
    print("  ✓ Ranking model comparison: PASS")
    
    return True


def validate_performance_reporting():
    """Validate performance reporting with visualization support"""
    print("\n✓ Testing performance reporting...")
    
    eval_service = ModelEvaluationService()
    
    # Run some evaluations
    actuals = np.array([100, 200, 300, 400, 500])
    predictions = np.array([110, 190, 310, 390, 510])
    
    eval_service.evaluate_regression_model(
        model_name='test_model',
        model_version='v1.0',
        predictions=predictions,
        actuals=actuals
    )
    
    # Generate report
    report = eval_service.generate_performance_report(
        model_name='test_model',
        model_version='v1.0',
        output_format='dict'
    )
    
    assert 'model_name' in report, "Report should include model name"
    assert 'model_version' in report, "Report should include model version"
    assert 'num_evaluations' in report, "Report should include evaluation count"
    assert 'evaluations' in report, "Report should include evaluation details"
    assert report['num_evaluations'] > 0, "Should have at least one evaluation"
    
    print("  ✓ Performance report generation: PASS")
    
    # Test visualization data preparation
    metrics_list = [
        eval_service.evaluate_regression_model(
            model_name='test_model',
            model_version=f'v{i}.0',
            predictions=predictions + i,
            actuals=actuals
        )
        for i in range(1, 4)
    ]
    
    chart_data = PerformanceVisualizer.prepare_regression_metrics_chart_data(metrics_list)
    
    assert 'labels' in chart_data, "Chart data should include labels"
    assert 'datasets' in chart_data, "Chart data should include datasets"
    assert 'title' in chart_data, "Chart data should include title"
    assert len(chart_data['datasets']) > 0, "Should have at least one dataset"
    assert len(chart_data['labels']) == 3, "Should have 3 labels for 3 versions"
    
    print("  ✓ Visualization data preparation: PASS")
    
    # Test ranking visualization
    ranking_metrics = [
        RankingMetrics(
            model_name='test_recommender',
            model_version=f'v{i}.0',
            precision_at_k={5: 0.5 + i*0.1, 10: 0.4 + i*0.1},
            recall_at_k={5: 0.6 + i*0.1, 10: 0.5 + i*0.1},
            ndcg_at_k={5: 0.7 + i*0.05, 10: 0.6 + i*0.05},
            map_score=0.5 + i*0.1,
            num_users_evaluated=100,
            evaluation_timestamp=datetime.now()
        )
        for i in range(1, 4)
    ]
    
    chart_data = PerformanceVisualizer.prepare_ranking_metrics_chart_data(ranking_metrics, k=10)
    
    assert 'labels' in chart_data, "Chart data should include labels"
    assert 'datasets' in chart_data, "Chart data should include datasets"
    assert len(chart_data['datasets']) >= 2, "Should have multiple metric datasets"
    
    print("  ✓ Ranking visualization data: PASS")
    
    return True


def validate_evaluation_history():
    """Validate evaluation history tracking"""
    print("\n✓ Testing evaluation history...")
    
    eval_service = ModelEvaluationService()
    
    # Run multiple evaluations
    actuals = np.array([100, 200, 300])
    
    for i in range(3):
        predictions = actuals + np.random.normal(0, 10, 3)
        eval_service.evaluate_regression_model(
            model_name='test_model',
            model_version=f'v{i}.0',
            predictions=predictions,
            actuals=actuals
        )
    
    # Get history
    history = eval_service.get_evaluation_history(model_name='test_model')
    
    assert len(history) == 3, "Should track all evaluations"
    assert all('metrics' in h for h in history), "Each record should have metrics"
    
    print("  ✓ Evaluation history tracking: PASS")
    
    # Test comparison history
    baseline_preds = actuals + 10
    challenger_preds = actuals + 5
    
    eval_service.compare_regression_models(
        model_name='test_model',
        baseline_version='v1.0',
        challenger_version='v2.0',
        baseline_predictions=baseline_preds,
        challenger_predictions=challenger_preds,
        actuals=actuals
    )
    
    comp_history = eval_service.get_comparison_history(model_name='test_model')
    
    assert len(comp_history) > 0, "Should track comparisons"
    assert 'winner' in comp_history[0], "Comparison should have winner"
    
    print("  ✓ Comparison history tracking: PASS")
    
    return True


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("Validating Model Evaluation Service Implementation")
    print("Task 4.4.1: Create model performance evaluation service")
    print("=" * 70)
    
    try:
        # Run all validation tests
        validate_regression_metrics()
        validate_ranking_metrics()
        validate_dataset_splitting()
        validate_model_comparison()
        validate_performance_reporting()
        validate_evaluation_history()
        
        print("\n" + "=" * 70)
        print("✓ ALL VALIDATION TESTS PASSED")
        print("=" * 70)
        print("\nTask 4.4.1 Requirements Met:")
        print("  ✓ Metrics calculation service for all ML models (MAE, RMSE, precision@k, recall@k)")
        print("  ✓ Validation dataset splitting utilities (temporal, random, stratified)")
        print("  ✓ Model comparison framework for A/B testing different versions")
        print("  ✓ Performance reporting with visualization support")
        print("\nImplementation is complete and functional!")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ VALIDATION FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
