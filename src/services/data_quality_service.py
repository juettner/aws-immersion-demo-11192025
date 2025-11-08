"""
Data quality monitoring and validation service for concert data.
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError
import structlog

from ..config.settings import settings
from ..infrastructure.glue_job_manager import GlueJobManager, DataQualityAlerting

logger = structlog.get_logger(__name__)


@dataclass
class QualityRule:
    """Data quality rule definition."""
    rule_id: str
    rule_name: str
    rule_type: str  # completeness, uniqueness, validity, consistency, accuracy
    column_name: str
    threshold: float
    severity: str  # critical, warning, info
    description: str
    validation_logic: str


@dataclass
class QualityResult:
    """Data quality validation result."""
    rule_id: str
    rule_name: str
    passed: bool
    score: float
    threshold: float
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class DataQualityService:
    """Service for monitoring and validating data quality across the concert data platform."""
    
    def __init__(self):
        self.s3_client = boto3.client('s3', **settings.get_aws_credentials())
        self.cloudwatch_client = boto3.client('cloudwatch', **settings.get_aws_credentials())
        self.glue_job_manager = GlueJobManager()
        self.quality_alerting = DataQualityAlerting()
        self.logger = structlog.get_logger("DataQualityService")
        
        # Define quality rules for each data type
        self.quality_rules = self._initialize_quality_rules()
    
    def _initialize_quality_rules(self) -> Dict[str, List[QualityRule]]:
        """Initialize data quality rules for each data type."""
        return {
            'artists': [
                QualityRule(
                    rule_id='artist_name_completeness',
                    rule_name='Artist Name Completeness',
                    rule_type='completeness',
                    column_name='name',
                    threshold=95.0,
                    severity='critical',
                    description='Artist name must be present for at least 95% of records',
                    validation_logic='not_null_and_not_empty'
                ),
                QualityRule(
                    rule_id='artist_id_uniqueness',
                    rule_name='Artist ID Uniqueness',
                    rule_type='uniqueness',
                    column_name='artist_id',
                    threshold=100.0,
                    severity='critical',
                    description='Artist IDs must be unique',
                    validation_logic='unique_values'
                ),
                QualityRule(
                    rule_id='popularity_score_validity',
                    rule_name='Popularity Score Validity',
                    rule_type='validity',
                    column_name='popularity_score',
                    threshold=90.0,
                    severity='warning',
                    description='Popularity scores should be between 0 and 100',
                    validation_logic='range_0_100'
                ),
                QualityRule(
                    rule_id='genre_completeness',
                    rule_name='Genre Completeness',
                    rule_type='completeness',
                    column_name='genre',
                    threshold=80.0,
                    severity='warning',
                    description='Genre information should be present for most artists',
                    validation_logic='not_null_and_not_empty'
                )
            ],
            'venues': [
                QualityRule(
                    rule_id='venue_name_completeness',
                    rule_name='Venue Name Completeness',
                    rule_type='completeness',
                    column_name='name',
                    threshold=95.0,
                    severity='critical',
                    description='Venue name must be present for at least 95% of records',
                    validation_logic='not_null_and_not_empty'
                ),
                QualityRule(
                    rule_id='venue_id_uniqueness',
                    rule_name='Venue ID Uniqueness',
                    rule_type='uniqueness',
                    column_name='venue_id',
                    threshold=100.0,
                    severity='critical',
                    description='Venue IDs must be unique',
                    validation_logic='unique_values'
                ),
                QualityRule(
                    rule_id='capacity_validity',
                    rule_name='Capacity Validity',
                    rule_type='validity',
                    column_name='capacity',
                    threshold=85.0,
                    severity='warning',
                    description='Venue capacity should be a positive number less than 200,000',
                    validation_logic='positive_number_max_200000'
                ),
                QualityRule(
                    rule_id='location_completeness',
                    rule_name='Location Completeness',
                    rule_type='completeness',
                    column_name='location.city',
                    threshold=90.0,
                    severity='warning',
                    description='City information should be present for most venues',
                    validation_logic='not_null_and_not_empty'
                ),
                QualityRule(
                    rule_id='coordinates_consistency',
                    rule_name='Coordinates Consistency',
                    rule_type='consistency',
                    column_name='location.latitude',
                    threshold=70.0,
                    severity='info',
                    description='Latitude and longitude should be provided together',
                    validation_logic='lat_lon_together'
                )
            ],
            'concerts': [
                QualityRule(
                    rule_id='concert_id_uniqueness',
                    rule_name='Concert ID Uniqueness',
                    rule_type='uniqueness',
                    column_name='concert_id',
                    threshold=100.0,
                    severity='critical',
                    description='Concert IDs must be unique',
                    validation_logic='unique_values'
                ),
                QualityRule(
                    rule_id='artist_venue_completeness',
                    rule_name='Artist and Venue Reference Completeness',
                    rule_type='completeness',
                    column_name='artist_id',
                    threshold=100.0,
                    severity='critical',
                    description='All concerts must have valid artist and venue references',
                    validation_logic='not_null_and_not_empty'
                ),
                QualityRule(
                    rule_id='event_date_validity',
                    rule_name='Event Date Validity',
                    rule_type='validity',
                    column_name='event_date',
                    threshold=95.0,
                    severity='critical',
                    description='Event dates should be valid and reasonable',
                    validation_logic='valid_date_range'
                ),
                QualityRule(
                    rule_id='attendance_validity',
                    rule_name='Attendance Validity',
                    rule_type='validity',
                    column_name='total_attendance',
                    threshold=80.0,
                    severity='warning',
                    description='Attendance should be positive and reasonable',
                    validation_logic='positive_number_max_500000'
                ),
                QualityRule(
                    rule_id='revenue_consistency',
                    rule_name='Revenue Consistency',
                    rule_type='consistency',
                    column_name='revenue',
                    threshold=75.0,
                    severity='info',
                    description='Revenue should be consistent with ticket prices and attendance',
                    validation_logic='revenue_attendance_consistency'
                )
            ]
        }
    
    def validate_data_quality(self, data_type: str, data_path: str) -> Dict[str, Any]:
        """Validate data quality for a specific data type."""
        if data_type not in self.quality_rules:
            raise ValueError(f"Unknown data type: {data_type}")
        
        self.logger.info(f"Starting data quality validation for {data_type}")
        
        try:
            # Load data from S3
            df = self._load_data_from_s3(data_path)
            if df is None or df.empty:
                return {
                    'data_type': data_type,
                    'status': 'failed',
                    'error': 'No data found or failed to load data',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Run quality rules
            results = []
            overall_score = 0.0
            critical_failures = 0
            
            for rule in self.quality_rules[data_type]:
                result = self._execute_quality_rule(df, rule)
                results.append(result)
                
                if result.severity == 'critical' and not result.passed:
                    critical_failures += 1
                
                # Weight scores by severity
                weight = {'critical': 3, 'warning': 2, 'info': 1}[result.severity]
                overall_score += result.score * weight
            
            # Calculate weighted average
            total_weight = sum({'critical': 3, 'warning': 2, 'info': 1}[r.severity] for r in results)
            overall_score = overall_score / total_weight if total_weight > 0 else 0
            
            # Determine overall status
            status = 'passed'
            if critical_failures > 0:
                status = 'failed'
            elif overall_score < 80:
                status = 'warning'
            
            # Generate summary
            summary = {
                'data_type': data_type,
                'status': status,
                'overall_score': round(overall_score, 2),
                'total_records': len(df),
                'rules_evaluated': len(results),
                'rules_passed': sum(1 for r in results if r.passed),
                'critical_failures': critical_failures,
                'timestamp': datetime.utcnow().isoformat(),
                'results': [self._quality_result_to_dict(r) for r in results]
            }
            
            # Send metrics to CloudWatch
            self._send_quality_metrics(data_type, summary)
            
            # Send alerts if needed
            if status in ['failed', 'warning']:
                self._send_quality_alert(data_type, summary)
            
            self.logger.info(f"Data quality validation completed for {data_type}", 
                           status=status, score=overall_score)
            
            return summary
            
        except Exception as e:
            error_msg = f"Data quality validation failed for {data_type}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'data_type': data_type,
                'status': 'error',
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _load_data_from_s3(self, s3_path: str) -> Optional[pd.DataFrame]:
        """Load data from S3 path."""
        try:
            # Parse S3 path
            if not s3_path.startswith('s3://'):
                raise ValueError("Invalid S3 path format")
            
            path_parts = s3_path[5:].split('/', 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ''
            
            # List objects in the path
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=key)
            
            if 'Contents' not in response:
                self.logger.warning(f"No objects found in S3 path: {s3_path}")
                return None
            
            # Load and combine data files
            dataframes = []
            for obj in response['Contents']:
                if obj['Key'].endswith(('.json', '.parquet', '.csv')):
                    try:
                        obj_response = self.s3_client.get_object(Bucket=bucket, Key=obj['Key'])
                        
                        if obj['Key'].endswith('.json'):
                            df = pd.read_json(obj_response['Body'])
                        elif obj['Key'].endswith('.parquet'):
                            df = pd.read_parquet(obj_response['Body'])
                        elif obj['Key'].endswith('.csv'):
                            df = pd.read_csv(obj_response['Body'])
                        
                        dataframes.append(df)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load file {obj['Key']}: {str(e)}")
            
            if not dataframes:
                return None
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Failed to load data from S3: {str(e)}")
            return None
    
    def _execute_quality_rule(self, df: pd.DataFrame, rule: QualityRule) -> QualityResult:
        """Execute a single data quality rule."""
        try:
            if rule.validation_logic == 'not_null_and_not_empty':
                score = self._check_completeness(df, rule.column_name)
            elif rule.validation_logic == 'unique_values':
                score = self._check_uniqueness(df, rule.column_name)
            elif rule.validation_logic == 'range_0_100':
                score = self._check_range(df, rule.column_name, 0, 100)
            elif rule.validation_logic == 'positive_number_max_200000':
                score = self._check_range(df, rule.column_name, 1, 200000)
            elif rule.validation_logic == 'positive_number_max_500000':
                score = self._check_range(df, rule.column_name, 1, 500000)
            elif rule.validation_logic == 'valid_date_range':
                score = self._check_date_range(df, rule.column_name)
            elif rule.validation_logic == 'lat_lon_together':
                score = self._check_coordinate_consistency(df)
            elif rule.validation_logic == 'revenue_attendance_consistency':
                score = self._check_revenue_consistency(df)
            else:
                score = 0.0
            
            passed = bool(score >= rule.threshold)
            
            return QualityResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                passed=passed,
                score=score,
                threshold=rule.threshold,
                severity=rule.severity,
                message=f"Rule {'passed' if passed else 'failed'}: {score:.1f}% (threshold: {rule.threshold}%)",
                details={'column': rule.column_name, 'validation_logic': rule.validation_logic},
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return QualityResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                passed=False,
                score=0.0,
                threshold=rule.threshold,
                severity=rule.severity,
                message=f"Rule execution failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow()
            )
    
    def _check_completeness(self, df: pd.DataFrame, column_name: str) -> float:
        """Check data completeness for a column."""
        if column_name not in df.columns:
            return 0.0
        
        total_rows = len(df)
        if total_rows == 0:
            return 100.0
        
        # Handle nested column names (e.g., 'location.city')
        if '.' in column_name:
            parts = column_name.split('.')
            series = df[parts[0]]
            for part in parts[1:]:
                if isinstance(series.iloc[0], dict):
                    series = series.apply(lambda x: x.get(part) if isinstance(x, dict) else None)
                else:
                    return 0.0
        else:
            series = df[column_name]
        
        non_null_count = series.notna().sum()
        non_empty_count = series.apply(lambda x: x != '' if isinstance(x, str) else True).sum()
        
        return (min(non_null_count, non_empty_count) / total_rows) * 100
    
    def _check_uniqueness(self, df: pd.DataFrame, column_name: str) -> float:
        """Check uniqueness for a column."""
        if column_name not in df.columns:
            return 0.0
        
        total_rows = len(df)
        if total_rows == 0:
            return 100.0
        
        unique_count = df[column_name].nunique()
        return (unique_count / total_rows) * 100
    
    def _check_range(self, df: pd.DataFrame, column_name: str, min_val: float, max_val: float) -> float:
        """Check if values are within a specified range."""
        if column_name not in df.columns:
            return 0.0
        
        series = df[column_name].dropna()
        if len(series) == 0:
            return 100.0
        
        # Convert to numeric if possible
        try:
            series = pd.to_numeric(series, errors='coerce').dropna()
        except:
            return 0.0
        
        if len(series) == 0:
            return 0.0
        
        valid_count = ((series >= min_val) & (series <= max_val)).sum()
        return (valid_count / len(series)) * 100
    
    def _check_date_range(self, df: pd.DataFrame, column_name: str) -> float:
        """Check if dates are within a reasonable range."""
        if column_name not in df.columns:
            return 0.0
        
        series = df[column_name].dropna()
        if len(series) == 0:
            return 100.0
        
        try:
            # Convert to datetime
            dates = pd.to_datetime(series, errors='coerce').dropna()
            
            if len(dates) == 0:
                return 0.0
            
            # Check reasonable date range (1950 to 5 years from now)
            min_date = pd.Timestamp('1950-01-01')
            max_date = pd.Timestamp.now() + pd.DateOffset(years=5)
            
            valid_count = ((dates >= min_date) & (dates <= max_date)).sum()
            return (valid_count / len(dates)) * 100
            
        except:
            return 0.0
    
    def _check_coordinate_consistency(self, df: pd.DataFrame) -> float:
        """Check if latitude and longitude are provided together."""
        lat_col = 'location.latitude'
        lon_col = 'location.longitude'
        
        # Extract nested values
        lat_values = df.apply(lambda row: row.get('location', {}).get('latitude') if isinstance(row.get('location'), dict) else None, axis=1)
        lon_values = df.apply(lambda row: row.get('location', {}).get('longitude') if isinstance(row.get('location'), dict) else None, axis=1)
        
        total_rows = len(df)
        if total_rows == 0:
            return 100.0
        
        # Count rows where both are present or both are absent
        both_present = ((lat_values.notna()) & (lon_values.notna())).sum()
        both_absent = ((lat_values.isna()) & (lon_values.isna())).sum()
        consistent_count = both_present + both_absent
        
        return (consistent_count / total_rows) * 100
    
    def _check_revenue_consistency(self, df: pd.DataFrame) -> float:
        """Check consistency between revenue, ticket prices, and attendance."""
        if not all(col in df.columns for col in ['revenue', 'total_attendance', 'ticket_prices']):
            return 0.0
        
        # This is a simplified consistency check
        # In practice, this would involve more complex business logic
        valid_records = df[
            (df['revenue'].notna()) & 
            (df['total_attendance'].notna()) & 
            (df['revenue'] > 0) & 
            (df['total_attendance'] > 0)
        ]
        
        if len(valid_records) == 0:
            return 100.0
        
        # Simple check: revenue per attendee should be reasonable ($10-$1000)
        revenue_per_attendee = valid_records['revenue'] / valid_records['total_attendance']
        reasonable_count = ((revenue_per_attendee >= 10) & (revenue_per_attendee <= 1000)).sum()
        
        return (reasonable_count / len(valid_records)) * 100
    
    def _quality_result_to_dict(self, result: QualityResult) -> Dict[str, Any]:
        """Convert QualityResult to dictionary."""
        return {
            'rule_id': result.rule_id,
            'rule_name': result.rule_name,
            'passed': result.passed,
            'score': result.score,
            'threshold': result.threshold,
            'severity': result.severity,
            'message': result.message,
            'details': result.details,
            'timestamp': result.timestamp.isoformat()
        }
    
    def _send_quality_metrics(self, data_type: str, summary: Dict[str, Any]):
        """Send quality metrics to CloudWatch."""
        try:
            metrics = [
                {
                    'MetricName': f'{data_type.title()}DataQualityScore',
                    'Value': summary['overall_score'],
                    'Unit': 'Percent',
                    'Dimensions': [{'Name': 'DataType', 'Value': data_type}]
                },
                {
                    'MetricName': f'{data_type.title()}RecordCount',
                    'Value': summary['total_records'],
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'DataType', 'Value': data_type}]
                },
                {
                    'MetricName': f'{data_type.title()}CriticalFailures',
                    'Value': summary['critical_failures'],
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'DataType', 'Value': data_type}]
                }
            ]
            
            self.cloudwatch_client.put_metric_data(
                Namespace='ConcertDataPlatform/DataQuality',
                MetricData=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send quality metrics: {str(e)}")
    
    def _send_quality_alert(self, data_type: str, summary: Dict[str, Any]):
        """Send quality alert if thresholds are breached."""
        try:
            # This would integrate with SNS or other alerting mechanisms
            alert_message = {
                'alert_type': 'data_quality',
                'data_type': data_type,
                'status': summary['status'],
                'overall_score': summary['overall_score'],
                'critical_failures': summary['critical_failures'],
                'timestamp': summary['timestamp']
            }
            
            self.logger.warning(f"Data quality alert for {data_type}", **alert_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send quality alert: {str(e)}")
    
    def run_quality_monitoring_pipeline(self, data_paths: Dict[str, str]) -> Dict[str, Any]:
        """Run quality monitoring for all data types."""
        results = {
            'pipeline_start_time': datetime.utcnow().isoformat(),
            'data_types': {},
            'overall_status': 'passed'
        }
        
        for data_type, path in data_paths.items():
            if data_type in self.quality_rules:
                result = self.validate_data_quality(data_type, path)
                results['data_types'][data_type] = result
                
                if result['status'] in ['failed', 'error']:
                    results['overall_status'] = 'failed'
                elif result['status'] == 'warning' and results['overall_status'] == 'passed':
                    results['overall_status'] = 'warning'
        
        results['pipeline_end_time'] = datetime.utcnow().isoformat()
        
        return results