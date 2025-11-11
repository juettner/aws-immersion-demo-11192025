"""
Model Monitoring and Drift Detection Service

Provides comprehensive monitoring capabilities for ML models including:
- Prediction drift detection using statistical tests (KS test, PSI)
- CloudWatch custom metrics publishing for model performance
- Alerting logic for model degradation thresholds
- Automated model retraining triggers
"""
import boto3
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from scipy import stats
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DriftDetectionResult:
    """Results from drift detection analysis"""
    model_name: str
    model_version: str
    drift_type: str  # 'prediction', 'feature', 'target'
    drift_detected: bool
    drift_score: float
    statistical_test: str  # 'ks_test', 'psi', 'chi_square'
    p_value: Optional[float]
    threshold: float
    baseline_period: str
    current_period: str
    detection_timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['detection_timestamp'] = self.detection_timestamp.isoformat()
        # Convert numpy types to Python native types
        result['drift_detected'] = bool(result['drift_detected'])
        result['drift_score'] = float(result['drift_score'])
        if result['p_value'] is not None:
            result['p_value'] = float(result['p_value'])
        result['threshold'] = float(result['threshold'])
        return result


@dataclass
class ModelPerformanceMetrics:
    """Model performance metrics for monitoring"""
    model_name: str
    model_version: str
    metric_name: str
    metric_value: float
    threshold: Optional[float]
    threshold_breached: bool
    num_predictions: int
    time_period: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        # Convert numpy types to Python native types
        result['metric_value'] = float(result['metric_value'])
        if result['threshold'] is not None:
            result['threshold'] = float(result['threshold'])
        result['threshold_breached'] = bool(result['threshold_breached'])
        result['num_predictions'] = int(result['num_predictions'])
        return result


@dataclass
class RetrainingTrigger:
    """Trigger for automated model retraining"""
    trigger_id: str
    model_name: str
    model_version: str
    trigger_reason: str
    trigger_type: str  # 'drift', 'performance_degradation', 'scheduled'
    severity: str  # 'low', 'medium', 'high', 'critical'
    metrics: Dict[str, Any]
    triggered_at: datetime
    retraining_recommended: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['triggered_at'] = self.triggered_at.isoformat()
        return result


class DriftDetector:
    """Statistical drift detection utilities"""
    
    @staticmethod
    def kolmogorov_smirnov_test(
        baseline_data: np.ndarray,
        current_data: np.ndarray,
        significance_level: float = 0.05
    ) -> Tuple[bool, float, float]:
        """
        Perform Kolmogorov-Smirnov test for distribution drift
        
        Args:
            baseline_data: Historical baseline data
            current_data: Current data to compare
            significance_level: Significance level for hypothesis test
            
        Returns:
            Tuple of (drift_detected, ks_statistic, p_value)
        """
        if len(baseline_data) == 0 or len(current_data) == 0:
            raise ValueError("Cannot perform KS test with empty data")
        
        # Perform two-sample KS test
        ks_statistic, p_value = stats.ks_2samp(baseline_data, current_data)
        
        # Drift detected if p-value < significance level
        drift_detected = p_value < significance_level
        
        return drift_detected, float(ks_statistic), float(p_value)
    
    @staticmethod
    def population_stability_index(
        baseline_data: np.ndarray,
        current_data: np.ndarray,
        num_bins: int = 10
    ) -> Tuple[bool, float]:
        """
        Calculate Population Stability Index (PSI) for drift detection
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change (drift detected)
        
        Args:
            baseline_data: Historical baseline data
            current_data: Current data to compare
            num_bins: Number of bins for discretization
            
        Returns:
            Tuple of (drift_detected, psi_value)
        """
        if len(baseline_data) == 0 or len(current_data) == 0:
            raise ValueError("Cannot calculate PSI with empty data")
        
        # Create bins based on baseline data
        min_val = min(baseline_data.min(), current_data.min())
        max_val = max(baseline_data.max(), current_data.max())
        bins = np.linspace(min_val, max_val, num_bins + 1)
        
        # Calculate distributions
        baseline_counts, _ = np.histogram(baseline_data, bins=bins)
        current_counts, _ = np.histogram(current_data, bins=bins)
        
        # Convert to proportions (add small epsilon to avoid division by zero)
        epsilon = 1e-10
        baseline_props = (baseline_counts + epsilon) / (len(baseline_data) + epsilon * num_bins)
        current_props = (current_counts + epsilon) / (len(current_data) + epsilon * num_bins)
        
        # Calculate PSI
        psi = np.sum((current_props - baseline_props) * np.log(current_props / baseline_props))
        
        # Drift detected if PSI >= 0.2
        drift_detected = psi >= 0.2
        
        return drift_detected, float(psi)
    
    @staticmethod
    def chi_square_test(
        baseline_data: np.ndarray,
        current_data: np.ndarray,
        num_bins: int = 10,
        significance_level: float = 0.05
    ) -> Tuple[bool, float, float]:
        """
        Perform Chi-Square test for categorical drift detection
        
        Args:
            baseline_data: Historical baseline data
            current_data: Current data to compare
            num_bins: Number of bins for discretization
            significance_level: Significance level for hypothesis test
            
        Returns:
            Tuple of (drift_detected, chi_square_statistic, p_value)
        """
        if len(baseline_data) == 0 or len(current_data) == 0:
            raise ValueError("Cannot perform Chi-Square test with empty data")
        
        # Create bins
        min_val = min(baseline_data.min(), current_data.min())
        max_val = max(baseline_data.max(), current_data.max())
        bins = np.linspace(min_val, max_val, num_bins + 1)
        
        # Calculate observed frequencies
        baseline_counts, _ = np.histogram(baseline_data, bins=bins)
        current_counts, _ = np.histogram(current_data, bins=bins)
        
        # Normalize to same total for chi-square test
        baseline_total = np.sum(baseline_counts)
        current_total = np.sum(current_counts)
        
        # Scale expected frequencies to match observed total
        expected_counts = (baseline_counts / baseline_total) * current_total
        
        # Add small epsilon to avoid zero frequencies
        epsilon = 1e-10
        expected_counts = expected_counts + epsilon
        current_counts_adj = current_counts + epsilon
        
        # Perform chi-square test
        chi2_statistic, p_value = stats.chisquare(
            f_obs=current_counts_adj,
            f_exp=expected_counts
        )
        
        # Drift detected if p-value < significance level
        drift_detected = p_value < significance_level
        
        return drift_detected, float(chi2_statistic), float(p_value)


class CloudWatchMetricsPublisher:
    """Publisher for CloudWatch custom metrics"""
    
    def __init__(self, namespace: str = 'MLModels/Performance'):
        """
        Initialize CloudWatch metrics publisher
        
        Args:
            namespace: CloudWatch namespace for metrics
        """
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
    
    def publish_model_metric(
        self,
        model_name: str,
        model_version: str,
        metric_name: str,
        metric_value: float,
        unit: str = 'None',
        dimensions: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish a single model metric to CloudWatch
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            metric_name: Name of the metric
            metric_value: Value of the metric
            unit: CloudWatch unit (None, Count, Percent, etc.)
            dimensions: Additional dimensions for the metric
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metric_dimensions = [
                {'Name': 'ModelName', 'Value': model_name},
                {'Name': 'ModelVersion', 'Value': model_version}
            ]
            
            if dimensions:
                for key, value in dimensions.items():
                    metric_dimensions.append({'Name': key, 'Value': value})
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': metric_value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': metric_dimensions
                    }
                ]
            )
            
            logger.info(
                f"Published metric {metric_name}={metric_value} for "
                f"{model_name} v{model_version} to CloudWatch"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error publishing metric to CloudWatch: {str(e)}")
            return False
    
    def publish_batch_metrics(
        self,
        model_name: str,
        model_version: str,
        metrics: Dict[str, float],
        unit: str = 'None'
    ) -> int:
        """
        Publish multiple metrics in batch
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            metrics: Dictionary of metric_name -> metric_value
            unit: CloudWatch unit for all metrics
            
        Returns:
            Number of successfully published metrics
        """
        success_count = 0
        
        for metric_name, metric_value in metrics.items():
            if self.publish_model_metric(
                model_name=model_name,
                model_version=model_version,
                metric_name=metric_name,
                metric_value=metric_value,
                unit=unit
            ):
                success_count += 1
        
        return success_count
    
    def publish_drift_metric(
        self,
        model_name: str,
        model_version: str,
        drift_score: float,
        drift_detected: bool
    ) -> bool:
        """
        Publish drift detection metrics
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            drift_score: Drift score value
            drift_detected: Whether drift was detected
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Publish drift score
        success &= self.publish_model_metric(
            model_name=model_name,
            model_version=model_version,
            metric_name='DriftScore',
            metric_value=drift_score,
            unit='None'
        )
        
        # Publish drift detection flag
        success &= self.publish_model_metric(
            model_name=model_name,
            model_version=model_version,
            metric_name='DriftDetected',
            metric_value=1.0 if drift_detected else 0.0,
            unit='Count'
        )
        
        return success


class ModelMonitoringService:
    """Service for comprehensive model monitoring and drift detection"""
    
    # Default thresholds for performance degradation
    DEFAULT_THRESHOLDS = {
        'mae_increase_pct': 20.0,  # 20% increase in MAE triggers alert
        'rmse_increase_pct': 20.0,
        'r_squared_decrease_pct': 10.0,  # 10% decrease in R² triggers alert
        'precision_decrease_pct': 15.0,
        'recall_decrease_pct': 15.0,
        'map_decrease_pct': 15.0,
        'drift_psi_threshold': 0.2,
        'drift_ks_pvalue': 0.05
    }
    
    def __init__(
        self,
        cloudwatch_namespace: str = 'MLModels/Performance',
        thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize model monitoring service
        
        Args:
            cloudwatch_namespace: CloudWatch namespace for metrics
            thresholds: Custom thresholds for alerting
        """
        self.drift_detector = DriftDetector()
        self.metrics_publisher = CloudWatchMetricsPublisher(cloudwatch_namespace)
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.drift_history: List[DriftDetectionResult] = []
        self.performance_history: List[ModelPerformanceMetrics] = []
        self.retraining_triggers: List[RetrainingTrigger] = []
    
    def detect_prediction_drift(
        self,
        model_name: str,
        model_version: str,
        baseline_predictions: np.ndarray,
        current_predictions: np.ndarray,
        method: str = 'psi',
        baseline_period: str = 'last_30_days',
        current_period: str = 'last_7_days'
    ) -> DriftDetectionResult:
        """
        Detect drift in model predictions
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            baseline_predictions: Historical baseline predictions
            current_predictions: Current predictions to compare
            method: Detection method ('psi', 'ks_test', 'chi_square')
            baseline_period: Description of baseline period
            current_period: Description of current period
            
        Returns:
            DriftDetectionResult object
        """
        if method == 'psi':
            drift_detected, drift_score = self.drift_detector.population_stability_index(
                baseline_predictions, current_predictions
            )
            p_value = None
            statistical_test = 'psi'
            threshold = self.thresholds['drift_psi_threshold']
            
        elif method == 'ks_test':
            drift_detected, drift_score, p_value = self.drift_detector.kolmogorov_smirnov_test(
                baseline_predictions, current_predictions
            )
            statistical_test = 'ks_test'
            threshold = self.thresholds['drift_ks_pvalue']
            
        elif method == 'chi_square':
            drift_detected, drift_score, p_value = self.drift_detector.chi_square_test(
                baseline_predictions, current_predictions
            )
            statistical_test = 'chi_square'
            threshold = self.thresholds['drift_ks_pvalue']
            
        else:
            raise ValueError(f"Unknown drift detection method: {method}")
        
        result = DriftDetectionResult(
            model_name=model_name,
            model_version=model_version,
            drift_type='prediction',
            drift_detected=drift_detected,
            drift_score=drift_score,
            statistical_test=statistical_test,
            p_value=p_value,
            threshold=threshold,
            baseline_period=baseline_period,
            current_period=current_period,
            detection_timestamp=datetime.now()
        )
        
        # Store in history
        self.drift_history.append(result)
        
        # Publish to CloudWatch
        self.metrics_publisher.publish_drift_metric(
            model_name=model_name,
            model_version=model_version,
            drift_score=drift_score,
            drift_detected=drift_detected
        )
        
        logger.info(
            f"Prediction drift detection for {model_name} v{model_version}: "
            f"drift_detected={drift_detected}, score={drift_score:.4f}"
        )
        
        # Check if retraining should be triggered
        if drift_detected:
            self._trigger_retraining_alert(
                model_name=model_name,
                model_version=model_version,
                trigger_reason=f"Prediction drift detected (score={drift_score:.4f})",
                trigger_type='drift',
                severity='high',
                metrics={'drift_score': drift_score, 'method': method}
            )
        
        return result
    
    def detect_feature_drift(
        self,
        model_name: str,
        model_version: str,
        baseline_features: pd.DataFrame,
        current_features: pd.DataFrame,
        feature_columns: List[str],
        method: str = 'psi'
    ) -> List[DriftDetectionResult]:
        """
        Detect drift in input features
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            baseline_features: Historical baseline features
            current_features: Current features to compare
            feature_columns: List of feature column names to check
            method: Detection method ('psi', 'ks_test')
            
        Returns:
            List of DriftDetectionResult objects (one per feature)
        """
        results = []
        
        for feature_col in feature_columns:
            if feature_col not in baseline_features.columns or feature_col not in current_features.columns:
                logger.warning(f"Feature {feature_col} not found in data, skipping")
                continue
            
            baseline_data = baseline_features[feature_col].dropna().values
            current_data = current_features[feature_col].dropna().values
            
            if len(baseline_data) == 0 or len(current_data) == 0:
                logger.warning(f"Empty data for feature {feature_col}, skipping")
                continue
            
            try:
                if method == 'psi':
                    drift_detected, drift_score = self.drift_detector.population_stability_index(
                        baseline_data, current_data
                    )
                    p_value = None
                    statistical_test = 'psi'
                    threshold = self.thresholds['drift_psi_threshold']
                    
                elif method == 'ks_test':
                    drift_detected, drift_score, p_value = self.drift_detector.kolmogorov_smirnov_test(
                        baseline_data, current_data
                    )
                    statistical_test = 'ks_test'
                    threshold = self.thresholds['drift_ks_pvalue']
                    
                else:
                    raise ValueError(f"Unknown drift detection method: {method}")
                
                result = DriftDetectionResult(
                    model_name=model_name,
                    model_version=model_version,
                    drift_type=f'feature_{feature_col}',
                    drift_detected=drift_detected,
                    drift_score=drift_score,
                    statistical_test=statistical_test,
                    p_value=p_value,
                    threshold=threshold,
                    baseline_period='baseline',
                    current_period='current',
                    detection_timestamp=datetime.now()
                )
                
                results.append(result)
                self.drift_history.append(result)
                
                # Publish to CloudWatch
                self.metrics_publisher.publish_model_metric(
                    model_name=model_name,
                    model_version=model_version,
                    metric_name=f'FeatureDrift_{feature_col}',
                    metric_value=drift_score,
                    unit='None'
                )
                
                if drift_detected:
                    logger.warning(
                        f"Feature drift detected for {feature_col} in {model_name}: "
                        f"score={drift_score:.4f}"
                    )
                    
            except Exception as e:
                logger.error(f"Error detecting drift for feature {feature_col}: {str(e)}")
        
        # Check if multiple features have drift
        drift_count = sum(1 for r in results if r.drift_detected)
        if drift_count >= len(feature_columns) * 0.3:  # 30% of features have drift
            self._trigger_retraining_alert(
                model_name=model_name,
                model_version=model_version,
                trigger_reason=f"Feature drift detected in {drift_count}/{len(feature_columns)} features",
                trigger_type='drift',
                severity='high',
                metrics={'drift_feature_count': drift_count, 'total_features': len(feature_columns)}
            )
        
        return results

    def monitor_regression_performance(
        self,
        model_name: str,
        model_version: str,
        predictions: np.ndarray,
        actuals: np.ndarray,
        baseline_metrics: Optional[Dict[str, float]] = None,
        time_period: str = 'current'
    ) -> List[ModelPerformanceMetrics]:
        """
        Monitor regression model performance and check for degradation
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            predictions: Model predictions
            actuals: Actual values
            baseline_metrics: Optional baseline metrics for comparison
            time_period: Description of time period
            
        Returns:
            List of ModelPerformanceMetrics objects
        """
        # Calculate current metrics
        mae = np.mean(np.abs(predictions - actuals))
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        # Calculate MAPE
        non_zero_mask = actuals != 0
        if np.any(non_zero_mask):
            mape = np.mean(np.abs((actuals[non_zero_mask] - predictions[non_zero_mask]) / actuals[non_zero_mask])) * 100
        else:
            mape = float('inf')
        
        # Calculate R-squared
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        current_metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'r_squared': float(r_squared)
        }
        
        # Publish to CloudWatch
        self.metrics_publisher.publish_batch_metrics(
            model_name=model_name,
            model_version=model_version,
            metrics={
                'MAE': current_metrics['mae'],
                'RMSE': current_metrics['rmse'],
                'MAPE': current_metrics['mape'],
                'R_Squared': current_metrics['r_squared']
            },
            unit='None'
        )
        
        # Check for performance degradation
        performance_results = []
        degradation_detected = False
        degradation_reasons = []
        
        if baseline_metrics:
            for metric_name, current_value in current_metrics.items():
                baseline_value = baseline_metrics.get(metric_name)
                
                if baseline_value is None:
                    continue
                
                # Calculate percentage change
                if metric_name == 'r_squared':
                    # For R², lower is worse
                    pct_change = ((baseline_value - current_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
                    threshold = self.thresholds.get('r_squared_decrease_pct', 10.0)
                    threshold_breached = pct_change > threshold
                else:
                    # For MAE, RMSE, MAPE: higher is worse
                    pct_change = ((current_value - baseline_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
                    threshold = self.thresholds.get(f'{metric_name}_increase_pct', 20.0)
                    threshold_breached = pct_change > threshold
                
                metric_result = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_version=model_version,
                    metric_name=metric_name,
                    metric_value=current_value,
                    threshold=threshold,
                    threshold_breached=threshold_breached,
                    num_predictions=len(predictions),
                    time_period=time_period,
                    timestamp=datetime.now()
                )
                
                performance_results.append(metric_result)
                self.performance_history.append(metric_result)
                
                if threshold_breached:
                    degradation_detected = True
                    degradation_reasons.append(
                        f"{metric_name.upper()} degraded by {pct_change:.1f}% "
                        f"(baseline={baseline_value:.4f}, current={current_value:.4f})"
                    )
                    
                    logger.warning(
                        f"Performance degradation detected for {model_name}: {degradation_reasons[-1]}"
                    )
        else:
            # No baseline, just record current metrics
            for metric_name, current_value in current_metrics.items():
                metric_result = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_version=model_version,
                    metric_name=metric_name,
                    metric_value=current_value,
                    threshold=None,
                    threshold_breached=False,
                    num_predictions=len(predictions),
                    time_period=time_period,
                    timestamp=datetime.now()
                )
                performance_results.append(metric_result)
                self.performance_history.append(metric_result)
        
        # Trigger retraining if degradation detected
        if degradation_detected:
            self._trigger_retraining_alert(
                model_name=model_name,
                model_version=model_version,
                trigger_reason='; '.join(degradation_reasons),
                trigger_type='performance_degradation',
                severity='high',
                metrics=current_metrics
            )
        
        return performance_results
    
    def monitor_ranking_performance(
        self,
        model_name: str,
        model_version: str,
        recommendations: Dict[str, List[str]],
        ground_truth: Dict[str, List[str]],
        baseline_metrics: Optional[Dict[str, float]] = None,
        k_values: List[int] = [5, 10, 20],
        time_period: str = 'current'
    ) -> List[ModelPerformanceMetrics]:
        """
        Monitor ranking/recommendation model performance
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            recommendations: Dict mapping user_id to recommended item_ids
            ground_truth: Dict mapping user_id to relevant item_ids
            baseline_metrics: Optional baseline metrics for comparison
            k_values: List of k values for evaluation
            time_period: Description of time period
            
        Returns:
            List of ModelPerformanceMetrics objects
        """
        # Calculate current metrics
        precision_at_k = {k: [] for k in k_values}
        recall_at_k = {k: [] for k in k_values}
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
            
            # Calculate precision@k and recall@k
            for k in k_values:
                top_k = recommended[:k]
                relevant_in_top_k = len([item for item in top_k if item in relevant])
                
                precision = relevant_in_top_k / k if k > 0 else 0.0
                precision_at_k[k].append(precision)
                
                recall = relevant_in_top_k / len(relevant) if len(relevant) > 0 else 0.0
                recall_at_k[k].append(recall)
            
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
        current_metrics = {
            'precision_at_10': float(np.mean(precision_at_k[10])) if precision_at_k[10] else 0.0,
            'recall_at_10': float(np.mean(recall_at_k[10])) if recall_at_k[10] else 0.0,
            'map': float(np.mean(average_precisions)) if average_precisions else 0.0
        }
        
        # Publish to CloudWatch
        self.metrics_publisher.publish_batch_metrics(
            model_name=model_name,
            model_version=model_version,
            metrics={
                'Precision_at_10': current_metrics['precision_at_10'],
                'Recall_at_10': current_metrics['recall_at_10'],
                'MAP': current_metrics['map']
            },
            unit='None'
        )
        
        # Check for performance degradation
        performance_results = []
        degradation_detected = False
        degradation_reasons = []
        
        if baseline_metrics:
            for metric_name, current_value in current_metrics.items():
                baseline_value = baseline_metrics.get(metric_name)
                
                if baseline_value is None:
                    continue
                
                # For ranking metrics, lower is worse
                pct_change = ((baseline_value - current_value) / abs(baseline_value)) * 100 if baseline_value != 0 else 0
                threshold = self.thresholds.get(f'{metric_name}_decrease_pct', 15.0)
                threshold_breached = pct_change > threshold
                
                metric_result = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_version=model_version,
                    metric_name=metric_name,
                    metric_value=current_value,
                    threshold=threshold,
                    threshold_breached=threshold_breached,
                    num_predictions=num_users,
                    time_period=time_period,
                    timestamp=datetime.now()
                )
                
                performance_results.append(metric_result)
                self.performance_history.append(metric_result)
                
                if threshold_breached:
                    degradation_detected = True
                    degradation_reasons.append(
                        f"{metric_name.upper()} degraded by {pct_change:.1f}% "
                        f"(baseline={baseline_value:.4f}, current={current_value:.4f})"
                    )
                    
                    logger.warning(
                        f"Performance degradation detected for {model_name}: {degradation_reasons[-1]}"
                    )
        else:
            # No baseline, just record current metrics
            for metric_name, current_value in current_metrics.items():
                metric_result = ModelPerformanceMetrics(
                    model_name=model_name,
                    model_version=model_version,
                    metric_name=metric_name,
                    metric_value=current_value,
                    threshold=None,
                    threshold_breached=False,
                    num_predictions=num_users,
                    time_period=time_period,
                    timestamp=datetime.now()
                )
                performance_results.append(metric_result)
                self.performance_history.append(metric_result)
        
        # Trigger retraining if degradation detected
        if degradation_detected:
            self._trigger_retraining_alert(
                model_name=model_name,
                model_version=model_version,
                trigger_reason='; '.join(degradation_reasons),
                trigger_type='performance_degradation',
                severity='high',
                metrics=current_metrics
            )
        
        return performance_results
    
    def _trigger_retraining_alert(
        self,
        model_name: str,
        model_version: str,
        trigger_reason: str,
        trigger_type: str,
        severity: str,
        metrics: Dict[str, Any]
    ):
        """
        Internal method to trigger retraining alert
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            trigger_reason: Reason for triggering
            trigger_type: Type of trigger
            severity: Severity level
            metrics: Associated metrics
        """
        import uuid
        
        trigger = RetrainingTrigger(
            trigger_id=str(uuid.uuid4()),
            model_name=model_name,
            model_version=model_version,
            trigger_reason=trigger_reason,
            trigger_type=trigger_type,
            severity=severity,
            metrics=metrics,
            triggered_at=datetime.now(),
            retraining_recommended=True
        )
        
        self.retraining_triggers.append(trigger)
        
        # Publish retraining trigger metric to CloudWatch
        self.metrics_publisher.publish_model_metric(
            model_name=model_name,
            model_version=model_version,
            metric_name='RetrainingTriggered',
            metric_value=1.0,
            unit='Count',
            dimensions={'TriggerType': trigger_type, 'Severity': severity}
        )
        
        logger.warning(
            f"Retraining trigger created for {model_name} v{model_version}: "
            f"{trigger_reason} (severity={severity})"
        )
    
    def create_cloudwatch_alarms(
        self,
        model_name: str,
        model_version: str,
        sns_topic_arn: str,
        alarm_prefix: str = 'MLModel'
    ) -> List[str]:
        """
        Create CloudWatch alarms for model monitoring
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            sns_topic_arn: SNS topic ARN for alarm notifications
            alarm_prefix: Prefix for alarm names
            
        Returns:
            List of created alarm names
        """
        cloudwatch = boto3.client('cloudwatch')
        alarm_names = []
        
        # Alarm for drift detection
        drift_alarm_name = f"{alarm_prefix}-{model_name}-{model_version}-DriftDetected"
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=drift_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='DriftDetected',
                Namespace=self.metrics_publisher.namespace,
                Period=300,  # 5 minutes
                Statistic='Sum',
                Threshold=0.5,  # Trigger if drift detected
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn],
                AlarmDescription=f'Drift detected for {model_name} v{model_version}',
                Dimensions=[
                    {'Name': 'ModelName', 'Value': model_name},
                    {'Name': 'ModelVersion', 'Value': model_version}
                ]
            )
            alarm_names.append(drift_alarm_name)
            logger.info(f"Created CloudWatch alarm: {drift_alarm_name}")
        except Exception as e:
            logger.error(f"Error creating drift alarm: {str(e)}")
        
        # Alarm for MAE increase
        mae_alarm_name = f"{alarm_prefix}-{model_name}-{model_version}-MAE-High"
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=mae_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='MAE',
                Namespace=self.metrics_publisher.namespace,
                Period=3600,  # 1 hour
                Statistic='Average',
                Threshold=1000.0,  # Adjust based on your model
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn],
                AlarmDescription=f'High MAE for {model_name} v{model_version}',
                Dimensions=[
                    {'Name': 'ModelName', 'Value': model_name},
                    {'Name': 'ModelVersion', 'Value': model_version}
                ]
            )
            alarm_names.append(mae_alarm_name)
            logger.info(f"Created CloudWatch alarm: {mae_alarm_name}")
        except Exception as e:
            logger.error(f"Error creating MAE alarm: {str(e)}")
        
        # Alarm for retraining trigger
        retraining_alarm_name = f"{alarm_prefix}-{model_name}-{model_version}-RetrainingNeeded"
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=retraining_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='RetrainingTriggered',
                Namespace=self.metrics_publisher.namespace,
                Period=300,  # 5 minutes
                Statistic='Sum',
                Threshold=0.5,
                ActionsEnabled=True,
                AlarmActions=[sns_topic_arn],
                AlarmDescription=f'Retraining needed for {model_name} v{model_version}',
                Dimensions=[
                    {'Name': 'ModelName', 'Value': model_name},
                    {'Name': 'ModelVersion', 'Value': model_version}
                ]
            )
            alarm_names.append(retraining_alarm_name)
            logger.info(f"Created CloudWatch alarm: {retraining_alarm_name}")
        except Exception as e:
            logger.error(f"Error creating retraining alarm: {str(e)}")
        
        return alarm_names
    
    def get_drift_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get drift detection history
        
        Args:
            model_name: Optional model name to filter by
            limit: Maximum number of results
            
        Returns:
            List of drift detection results
        """
        history = self.drift_history
        
        if model_name:
            history = [d for d in history if d.model_name == model_name]
        
        return [d.to_dict() for d in history[-limit:]]
    
    def get_performance_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get performance monitoring history
        
        Args:
            model_name: Optional model name to filter by
            limit: Maximum number of results
            
        Returns:
            List of performance metrics
        """
        history = self.performance_history
        
        if model_name:
            history = [p for p in history if p.model_name == model_name]
        
        return [p.to_dict() for p in history[-limit:]]
    
    def get_retraining_triggers(
        self,
        model_name: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get retraining triggers
        
        Args:
            model_name: Optional model name to filter by
            severity: Optional severity level to filter by
            limit: Maximum number of results
            
        Returns:
            List of retraining triggers
        """
        triggers = self.retraining_triggers
        
        if model_name:
            triggers = [t for t in triggers if t.model_name == model_name]
        
        if severity:
            triggers = [t for t in triggers if t.severity == severity]
        
        return [t.to_dict() for t in triggers[-limit:]]
    
    def generate_monitoring_report(
        self,
        model_name: str,
        model_version: str,
        output_format: str = 'dict'
    ) -> Dict:
        """
        Generate comprehensive monitoring report
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            output_format: Output format ('dict', 'json')
            
        Returns:
            Monitoring report
        """
        # Get relevant history
        drift_results = [
            d for d in self.drift_history
            if d.model_name == model_name and d.model_version == model_version
        ]
        
        performance_results = [
            p for p in self.performance_history
            if p.model_name == model_name and p.model_version == model_version
        ]
        
        retraining_triggers = [
            t for t in self.retraining_triggers
            if t.model_name == model_name and t.model_version == model_version
        ]
        
        # Calculate summary statistics
        drift_detected_count = sum(1 for d in drift_results if d.drift_detected)
        performance_issues_count = sum(1 for p in performance_results if p.threshold_breached)
        
        report = {
            'model_name': model_name,
            'model_version': model_version,
            'monitoring_summary': {
                'total_drift_checks': len(drift_results),
                'drift_detected_count': drift_detected_count,
                'drift_detection_rate': drift_detected_count / len(drift_results) if drift_results else 0,
                'total_performance_checks': len(performance_results),
                'performance_issues_count': performance_issues_count,
                'retraining_triggers_count': len(retraining_triggers)
            },
            'recent_drift_detections': [d.to_dict() for d in drift_results[-10:]],
            'recent_performance_metrics': [p.to_dict() for p in performance_results[-10:]],
            'retraining_triggers': [t.to_dict() for t in retraining_triggers],
            'report_generated_at': datetime.now().isoformat()
        }
        
        if output_format == 'json':
            return json.dumps(report, indent=2)
        
        return report
    
    def clear_history(self):
        """Clear all monitoring history"""
        self.drift_history.clear()
        self.performance_history.clear()
        self.retraining_triggers.clear()
        logger.info("Cleared monitoring history")
