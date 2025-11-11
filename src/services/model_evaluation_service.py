"""
Model Performance Evaluation Service

Provides comprehensive evaluation capabilities for all ML models including:
- Regression metrics (MAE, RMSE) for venue popularity and ticket sales
- Ranking metrics (precision@k, recall@k) for recommendation systems
- Validation dataset splitting utilities
- Model comparison framework for A/B testing
- Performance reporting with visualization support
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class RegressionMetrics:
    """Metrics for regression models (venue popularity, ticket sales)"""
    model_name: str
    model_version: str
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Squared Error
    mape: float  # Mean Absolute Percentage Error
    r_squared: float  # R-squared coefficient
    num_predictions: int
    evaluation_timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['evaluation_timestamp'] = self.evaluation_timestamp.isoformat()
        return result


@dataclass
class RankingMetrics:
    """Metrics for ranking/recommendation models"""
    model_name: str
    model_version: str
    precision_at_k: Dict[int, float]  # Precision at different k values
    recall_at_k: Dict[int, float]  # Recall at different k values
    ndcg_at_k: Dict[int, float]  # Normalized Discounted Cumulative Gain
    map_score: float  # Mean Average Precision
    num_users_evaluated: int
    evaluation_timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['evaluation_timestamp'] = self.evaluation_timestamp.isoformat()
        return result


@dataclass
class ModelComparison:
    """Comparison results between two model versions"""
    model_name: str
    baseline_version: str
    challenger_version: str
    metric_comparisons: Dict[str, Dict[str, float]]  # metric -> {baseline, challenger, improvement}
    winner: str  # 'baseline', 'challenger', or 'tie'
    confidence: float  # Statistical confidence in the comparison
    comparison_timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['comparison_timestamp'] = self.comparison_timestamp.isoformat()
        return result


class DatasetSplitter:
    """Utilities for splitting datasets into train/validation/test sets"""
    
    @staticmethod
    def temporal_split(
        data: pd.DataFrame,
        date_column: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data temporally (chronologically) for time-series data
        
        Args:
            data: DataFrame to split
            date_column: Name of the date column
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Ratios must sum to 1.0")
        
        # Sort by date
        sorted_data = data.sort_values(date_column).reset_index(drop=True)
        
        n = len(sorted_data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train_df = sorted_data.iloc[:train_end]
        val_df = sorted_data.iloc[train_end:val_end]
        test_df = sorted_data.iloc[val_end:]
        
        logger.info(
            f"Temporal split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}"
        )
        
        return train_df, val_df, test_df
    
    @staticmethod
    def random_split(
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data randomly for non-temporal data
        
        Args:
            data: DataFrame to split
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Ratios must sum to 1.0")
        
        # Shuffle data
        shuffled_data = data.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        n = len(shuffled_data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train_df = shuffled_data.iloc[:train_end]
        val_df = shuffled_data.iloc[train_end:val_end]
        test_df = shuffled_data.iloc[val_end:]
        
        logger.info(
            f"Random split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}"
        )
        
        return train_df, val_df, test_df
    
    @staticmethod
    def stratified_split(
        data: pd.DataFrame,
        stratify_column: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data with stratification to maintain class distribution
        
        Args:
            data: DataFrame to split
            stratify_column: Column to stratify on
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Ratios must sum to 1.0")
        
        train_dfs = []
        val_dfs = []
        test_dfs = []
        
        # Split each stratum separately
        for stratum_value in data[stratify_column].unique():
            stratum_data = data[data[stratify_column] == stratum_value]
            
            n = len(stratum_data)
            train_end = int(n * train_ratio)
            val_end = int(n * (train_ratio + val_ratio))
            
            shuffled = stratum_data.sample(frac=1, random_state=random_state)
            
            train_dfs.append(shuffled.iloc[:train_end])
            val_dfs.append(shuffled.iloc[train_end:val_end])
            test_dfs.append(shuffled.iloc[val_end:])
        
        train_df = pd.concat(train_dfs, ignore_index=True)
        val_df = pd.concat(val_dfs, ignore_index=True)
        test_df = pd.concat(test_dfs, ignore_index=True)
        
        logger.info(
            f"Stratified split on '{stratify_column}': "
            f"train={len(train_df)}, val={len(val_df)}, test={len(test_df)}"
        )
        
        return train_df, val_df, test_df


class ModelEvaluationService:
    """Service for evaluating ML model performance"""
    
    def __init__(self):
        """Initialize the evaluation service"""
        self.evaluation_history: List[Dict] = []
        self.comparison_history: List[ModelComparison] = []
    
    def evaluate_regression_model(
        self,
        model_name: str,
        model_version: str,
        predictions: np.ndarray,
        actuals: np.ndarray
    ) -> RegressionMetrics:
        """
        Evaluate regression model performance (for venue popularity, ticket sales)
        
        Args:
            model_name: Name of the model
            model_version: Version identifier
            predictions: Array of predicted values
            actuals: Array of actual values
            
        Returns:
            RegressionMetrics object with calculated metrics
        """
        if len(predictions) != len(actuals):
            raise ValueError("Predictions and actuals must have same length")
        
        if len(predictions) == 0:
            raise ValueError("Cannot evaluate with empty arrays")
        
        # Convert to numpy arrays
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Calculate MAE (Mean Absolute Error)
        mae = np.mean(np.abs(predictions - actuals))
        
        # Calculate RMSE (Root Mean Squared Error)
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        # Avoid division by zero
        non_zero_mask = actuals != 0
        if np.any(non_zero_mask):
            mape = np.mean(np.abs((actuals[non_zero_mask] - predictions[non_zero_mask]) / actuals[non_zero_mask])) * 100
        else:
            mape = float('inf')
        
        # Calculate R-squared
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        metrics = RegressionMetrics(
            model_name=model_name,
            model_version=model_version,
            mae=float(mae),
            rmse=float(rmse),
            mape=float(mape),
            r_squared=float(r_squared),
            num_predictions=len(predictions),
            evaluation_timestamp=datetime.now()
        )
        
        # Store in history
        self.evaluation_history.append({
            'type': 'regression',
            'metrics': metrics.to_dict()
        })
        
        logger.info(
            f"Regression evaluation for {model_name} v{model_version}: "
            f"MAE={mae:.2f}, RMSE={rmse:.2f}, R²={r_squared:.3f}"
        )
        
        return metrics

    def evaluate_ranking_model(
        self,
        model_name: str,
        model_version: str,
        recommendations: Dict[str, List[str]],
        ground_truth: Dict[str, List[str]],
        k_values: List[int] = [5, 10, 20]
    ) -> RankingMetrics:
        """
        Evaluate ranking/recommendation model performance
        
        Args:
            model_name: Name of the model
            model_version: Version identifier
            recommendations: Dict mapping user_id to list of recommended item_ids (ordered by score)
            ground_truth: Dict mapping user_id to list of relevant item_ids
            k_values: List of k values for precision@k and recall@k
            
        Returns:
            RankingMetrics object with calculated metrics
        """
        if not recommendations or not ground_truth:
            raise ValueError("Recommendations and ground truth cannot be empty")
        
        # Calculate metrics for each user
        precision_at_k = {k: [] for k in k_values}
        recall_at_k = {k: [] for k in k_values}
        ndcg_at_k = {k: [] for k in k_values}
        average_precisions = []
        
        num_users = 0
        
        for user_id in recommendations.keys():
            if user_id not in ground_truth:
                continue
            
            recommended = recommendations[user_id]
            relevant = set(ground_truth[user_id])
            
            if len(relevant) == 0:
                continue
            
            num_users += 1
            
            # Calculate precision@k and recall@k for each k
            for k in k_values:
                top_k = recommended[:k]
                relevant_in_top_k = len([item for item in top_k if item in relevant])
                
                # Precision@k
                precision = relevant_in_top_k / k if k > 0 else 0.0
                precision_at_k[k].append(precision)
                
                # Recall@k
                recall = relevant_in_top_k / len(relevant) if len(relevant) > 0 else 0.0
                recall_at_k[k].append(recall)
                
                # NDCG@k (Normalized Discounted Cumulative Gain)
                dcg = sum([1.0 / np.log2(i + 2) if top_k[i] in relevant else 0.0 
                          for i in range(min(k, len(top_k)))])
                
                # Ideal DCG (all relevant items at top)
                ideal_dcg = sum([1.0 / np.log2(i + 2) 
                                for i in range(min(k, len(relevant)))])
                
                ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0.0
                ndcg_at_k[k].append(ndcg)
            
            # Calculate Average Precision for MAP
            num_relevant_seen = 0
            precision_sum = 0.0
            
            for i, item in enumerate(recommended):
                if item in relevant:
                    num_relevant_seen += 1
                    precision_at_i = num_relevant_seen / (i + 1)
                    precision_sum += precision_at_i
            
            avg_precision = precision_sum / len(relevant) if len(relevant) > 0 else 0.0
            average_precisions.append(avg_precision)
        
        # Calculate mean metrics
        mean_precision_at_k = {k: np.mean(precision_at_k[k]) if precision_at_k[k] else 0.0 
                               for k in k_values}
        mean_recall_at_k = {k: np.mean(recall_at_k[k]) if recall_at_k[k] else 0.0 
                           for k in k_values}
        mean_ndcg_at_k = {k: np.mean(ndcg_at_k[k]) if ndcg_at_k[k] else 0.0 
                         for k in k_values}
        map_score = np.mean(average_precisions) if average_precisions else 0.0
        
        metrics = RankingMetrics(
            model_name=model_name,
            model_version=model_version,
            precision_at_k=mean_precision_at_k,
            recall_at_k=mean_recall_at_k,
            ndcg_at_k=mean_ndcg_at_k,
            map_score=float(map_score),
            num_users_evaluated=num_users,
            evaluation_timestamp=datetime.now()
        )
        
        # Store in history
        self.evaluation_history.append({
            'type': 'ranking',
            'metrics': metrics.to_dict()
        })
        
        logger.info(
            f"Ranking evaluation for {model_name} v{model_version}: "
            f"P@10={mean_precision_at_k.get(10, 0):.3f}, "
            f"R@10={mean_recall_at_k.get(10, 0):.3f}, "
            f"MAP={map_score:.3f}"
        )
        
        return metrics
    
    def compare_regression_models(
        self,
        model_name: str,
        baseline_version: str,
        challenger_version: str,
        baseline_predictions: np.ndarray,
        challenger_predictions: np.ndarray,
        actuals: np.ndarray,
        significance_threshold: float = 0.05
    ) -> ModelComparison:
        """
        Compare two regression model versions for A/B testing
        
        Args:
            model_name: Name of the model
            baseline_version: Version identifier for baseline
            challenger_version: Version identifier for challenger
            baseline_predictions: Predictions from baseline model
            challenger_predictions: Predictions from challenger model
            actuals: Actual values
            significance_threshold: Threshold for statistical significance
            
        Returns:
            ModelComparison object with comparison results
        """
        # Evaluate both models
        baseline_metrics = self.evaluate_regression_model(
            model_name=model_name,
            model_version=baseline_version,
            predictions=baseline_predictions,
            actuals=actuals
        )
        
        challenger_metrics = self.evaluate_regression_model(
            model_name=model_name,
            model_version=challenger_version,
            predictions=challenger_predictions,
            actuals=actuals
        )
        
        # Compare metrics
        metric_comparisons = {}
        
        for metric_name in ['mae', 'rmse', 'mape', 'r_squared']:
            baseline_value = getattr(baseline_metrics, metric_name)
            challenger_value = getattr(challenger_metrics, metric_name)
            
            # For MAE, RMSE, MAPE: lower is better
            # For R-squared: higher is better
            if metric_name == 'r_squared':
                improvement = ((challenger_value - baseline_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
            else:
                improvement = ((baseline_value - challenger_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
            
            metric_comparisons[metric_name] = {
                'baseline': baseline_value,
                'challenger': challenger_value,
                'improvement_pct': improvement
            }
        
        # Determine winner based on primary metrics (MAE and R-squared)
        mae_improvement = metric_comparisons['mae']['improvement_pct']
        r2_improvement = metric_comparisons['r_squared']['improvement_pct']
        
        # Simple voting: if both improve, challenger wins; if both worse, baseline wins
        improvements = [mae_improvement > 0, r2_improvement > 0]
        
        if sum(improvements) >= 2:
            winner = 'challenger'
            confidence = 0.8
        elif sum(improvements) == 0:
            winner = 'baseline'
            confidence = 0.8
        else:
            # Mixed results - use MAE as tiebreaker
            if mae_improvement > 0:
                winner = 'challenger'
            else:
                winner = 'baseline'
            confidence = 0.6
        
        comparison = ModelComparison(
            model_name=model_name,
            baseline_version=baseline_version,
            challenger_version=challenger_version,
            metric_comparisons=metric_comparisons,
            winner=winner,
            confidence=confidence,
            comparison_timestamp=datetime.now()
        )
        
        self.comparison_history.append(comparison)
        
        logger.info(
            f"Model comparison: {baseline_version} vs {challenger_version} - "
            f"Winner: {winner} (confidence: {confidence:.2f})"
        )
        
        return comparison
    
    def compare_ranking_models(
        self,
        model_name: str,
        baseline_version: str,
        challenger_version: str,
        baseline_recommendations: Dict[str, List[str]],
        challenger_recommendations: Dict[str, List[str]],
        ground_truth: Dict[str, List[str]],
        k_values: List[int] = [5, 10, 20]
    ) -> ModelComparison:
        """
        Compare two ranking model versions for A/B testing
        
        Args:
            model_name: Name of the model
            baseline_version: Version identifier for baseline
            challenger_version: Version identifier for challenger
            baseline_recommendations: Recommendations from baseline model
            challenger_recommendations: Recommendations from challenger model
            ground_truth: Ground truth relevant items
            k_values: List of k values for evaluation
            
        Returns:
            ModelComparison object with comparison results
        """
        # Evaluate both models
        baseline_metrics = self.evaluate_ranking_model(
            model_name=model_name,
            model_version=baseline_version,
            recommendations=baseline_recommendations,
            ground_truth=ground_truth,
            k_values=k_values
        )
        
        challenger_metrics = self.evaluate_ranking_model(
            model_name=model_name,
            model_version=challenger_version,
            recommendations=challenger_recommendations,
            ground_truth=ground_truth,
            k_values=k_values
        )
        
        # Compare metrics
        metric_comparisons = {}
        
        # Compare precision@10, recall@10, and MAP
        for metric_name, k in [('precision_at_10', 10), ('recall_at_10', 10)]:
            if k == 10:
                baseline_value = baseline_metrics.precision_at_k.get(10, 0) if 'precision' in metric_name else baseline_metrics.recall_at_k.get(10, 0)
                challenger_value = challenger_metrics.precision_at_k.get(10, 0) if 'precision' in metric_name else challenger_metrics.recall_at_k.get(10, 0)
            
            improvement = ((challenger_value - baseline_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
            
            metric_comparisons[metric_name] = {
                'baseline': baseline_value,
                'challenger': challenger_value,
                'improvement_pct': improvement
            }
        
        # Compare MAP
        baseline_map = baseline_metrics.map_score
        challenger_map = challenger_metrics.map_score
        map_improvement = ((challenger_map - baseline_map) / abs(baseline_map)) * 100 if baseline_map != 0 else 0
        
        metric_comparisons['map'] = {
            'baseline': baseline_map,
            'challenger': challenger_map,
            'improvement_pct': map_improvement
        }
        
        # Determine winner
        improvements = [
            metric_comparisons['precision_at_10']['improvement_pct'] > 0,
            metric_comparisons['recall_at_10']['improvement_pct'] > 0,
            metric_comparisons['map']['improvement_pct'] > 0
        ]
        
        if sum(improvements) >= 2:
            winner = 'challenger'
            confidence = 0.8
        elif sum(improvements) <= 1:
            winner = 'baseline'
            confidence = 0.8
        else:
            winner = 'tie'
            confidence = 0.5
        
        comparison = ModelComparison(
            model_name=model_name,
            baseline_version=baseline_version,
            challenger_version=challenger_version,
            metric_comparisons=metric_comparisons,
            winner=winner,
            confidence=confidence,
            comparison_timestamp=datetime.now()
        )
        
        self.comparison_history.append(comparison)
        
        logger.info(
            f"Ranking model comparison: {baseline_version} vs {challenger_version} - "
            f"Winner: {winner} (confidence: {confidence:.2f})"
        )
        
        return comparison
    
    def generate_performance_report(
        self,
        model_name: str,
        model_version: str,
        output_format: str = 'dict'
    ) -> Dict:
        """
        Generate comprehensive performance report for a model
        
        Args:
            model_name: Name of the model
            model_version: Version identifier
            output_format: Output format ('dict', 'json')
            
        Returns:
            Performance report as dictionary or JSON string
        """
        # Find all evaluations for this model version
        evaluations = [
            e for e in self.evaluation_history
            if e['metrics']['model_name'] == model_name 
            and e['metrics']['model_version'] == model_version
        ]
        
        if not evaluations:
            return {
                'error': f'No evaluations found for {model_name} v{model_version}'
            }
        
        # Find comparisons involving this model version
        comparisons = [
            c for c in self.comparison_history
            if c.model_name == model_name 
            and (c.baseline_version == model_version or c.challenger_version == model_version)
        ]
        
        report = {
            'model_name': model_name,
            'model_version': model_version,
            'num_evaluations': len(evaluations),
            'evaluations': [e['metrics'] for e in evaluations],
            'comparisons': [c.to_dict() for c in comparisons],
            'report_generated_at': datetime.now().isoformat()
        }
        
        if output_format == 'json':
            return json.dumps(report, indent=2)
        
        return report
    
    def get_evaluation_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get evaluation history, optionally filtered by model name
        
        Args:
            model_name: Optional model name to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of evaluation records
        """
        history = self.evaluation_history
        
        if model_name:
            history = [
                e for e in history
                if e['metrics']['model_name'] == model_name
            ]
        
        return history[-limit:]
    
    def get_comparison_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get comparison history, optionally filtered by model name
        
        Args:
            model_name: Optional model name to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of comparison records
        """
        history = self.comparison_history
        
        if model_name:
            history = [
                c for c in history
                if c.model_name == model_name
            ]
        
        return [c.to_dict() for c in history[-limit:]]
    
    def clear_history(self):
        """Clear all evaluation and comparison history"""
        self.evaluation_history.clear()
        self.comparison_history.clear()
        logger.info("Cleared evaluation and comparison history")


class PerformanceVisualizer:
    """Utilities for visualizing model performance metrics"""
    
    @staticmethod
    def prepare_regression_metrics_chart_data(
        metrics_list: List[RegressionMetrics]
    ) -> Dict:
        """
        Prepare data for regression metrics visualization
        
        Args:
            metrics_list: List of regression metrics
            
        Returns:
            Dictionary with chart data
        """
        if not metrics_list:
            return {'error': 'No metrics provided'}
        
        chart_data = {
            'labels': [f"{m.model_version}" for m in metrics_list],
            'datasets': [
                {
                    'label': 'MAE',
                    'data': [m.mae for m in metrics_list],
                    'type': 'bar'
                },
                {
                    'label': 'RMSE',
                    'data': [m.rmse for m in metrics_list],
                    'type': 'bar'
                },
                {
                    'label': 'R²',
                    'data': [m.r_squared for m in metrics_list],
                    'type': 'line'
                }
            ],
            'title': f'Regression Metrics - {metrics_list[0].model_name}',
            'x_axis_label': 'Model Version',
            'y_axis_label': 'Metric Value'
        }
        
        return chart_data
    
    @staticmethod
    def prepare_ranking_metrics_chart_data(
        metrics_list: List[RankingMetrics],
        k: int = 10
    ) -> Dict:
        """
        Prepare data for ranking metrics visualization
        
        Args:
            metrics_list: List of ranking metrics
            k: K value to visualize
            
        Returns:
            Dictionary with chart data
        """
        if not metrics_list:
            return {'error': 'No metrics provided'}
        
        chart_data = {
            'labels': [f"{m.model_version}" for m in metrics_list],
            'datasets': [
                {
                    'label': f'Precision@{k}',
                    'data': [m.precision_at_k.get(k, 0) for m in metrics_list],
                    'type': 'bar'
                },
                {
                    'label': f'Recall@{k}',
                    'data': [m.recall_at_k.get(k, 0) for m in metrics_list],
                    'type': 'bar'
                },
                {
                    'label': 'MAP',
                    'data': [m.map_score for m in metrics_list],
                    'type': 'line'
                }
            ],
            'title': f'Ranking Metrics - {metrics_list[0].model_name}',
            'x_axis_label': 'Model Version',
            'y_axis_label': 'Metric Value'
        }
        
        return chart_data
    
    @staticmethod
    def prepare_comparison_chart_data(
        comparison: ModelComparison
    ) -> Dict:
        """
        Prepare data for model comparison visualization
        
        Args:
            comparison: Model comparison object
            
        Returns:
            Dictionary with chart data
        """
        metrics = list(comparison.metric_comparisons.keys())
        baseline_values = [comparison.metric_comparisons[m]['baseline'] for m in metrics]
        challenger_values = [comparison.metric_comparisons[m]['challenger'] for m in metrics]
        
        chart_data = {
            'labels': metrics,
            'datasets': [
                {
                    'label': f'Baseline ({comparison.baseline_version})',
                    'data': baseline_values,
                    'type': 'bar'
                },
                {
                    'label': f'Challenger ({comparison.challenger_version})',
                    'data': challenger_values,
                    'type': 'bar'
                }
            ],
            'title': f'Model Comparison - {comparison.model_name}',
            'x_axis_label': 'Metric',
            'y_axis_label': 'Value',
            'winner': comparison.winner,
            'confidence': comparison.confidence
        }
        
        return chart_data
