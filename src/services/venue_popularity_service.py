"""
Venue Popularity Service - Feature engineering and model training for venue ranking
"""
import boto3
import sagemaker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging

from src.models.venue_popularity import VenueFeatures, VenuePopularity

logger = logging.getLogger(__name__)


class VenuePopularityService:
    """Service for venue popularity ranking and prediction"""
    
    def __init__(self, redshift_client, sagemaker_client=None):
        """
        Initialize venue popularity service
        
        Args:
            redshift_client: Client for querying Redshift data warehouse
            sagemaker_client: Optional SageMaker client for model operations
        """
        self.redshift_client = redshift_client
        self.sagemaker_client = sagemaker_client or boto3.client('sagemaker')
        self.sagemaker_runtime = boto3.client('sagemaker-runtime')
        
    def extract_venue_features(self, venue_id: str, lookback_days: int = 365) -> Optional[VenueFeatures]:
        """
        Extract features for a single venue from historical data
        
        Args:
            venue_id: Unique venue identifier
            lookback_days: Number of days to look back for historical data
            
        Returns:
            VenueFeatures object or None if insufficient data
        """
        query = f"""
        WITH venue_stats AS (
            SELECT 
                v.venue_id,
                v.capacity,
                v.venue_type,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.total_attendance) as avg_attendance,
                AVG(c.total_attendance::float / v.capacity) as avg_attendance_rate,
                SUM(c.revenue) as total_revenue,
                AVG(c.revenue) as avg_revenue_per_event,
                COUNT(DISTINCT c.artist_id) as unique_artists,
                COUNT(DISTINCT c.concert_id)::float / 
                    NULLIF(DATEDIFF(month, MIN(c.event_date), MAX(c.event_date)), 0) as booking_frequency
            FROM venues v
            LEFT JOIN concerts c ON v.venue_id = c.venue_id
            WHERE v.venue_id = '{venue_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                AND c.status = 'completed'
            GROUP BY v.venue_id, v.capacity, v.venue_type
        ),
        location_stats AS (
            SELECT 
                v.venue_id,
                AVG(other_v.total_concerts) as location_popularity
            FROM venues v
            CROSS JOIN (
                SELECT v2.venue_id, COUNT(c2.concert_id) as total_concerts
                FROM venues v2
                LEFT JOIN concerts c2 ON v2.venue_id = c2.venue_id
                WHERE c2.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                GROUP BY v2.venue_id
            ) other_v
            WHERE v.venue_id = '{venue_id}'
            GROUP BY v.venue_id
        ),
        repeat_bookings AS (
            SELECT
                v.venue_id,
                COUNT(DISTINCT artist_id)::float / NULLIF(COUNT(DISTINCT c.concert_id), 0) as repeat_rate
            FROM venues v
            LEFT JOIN concerts c ON v.venue_id = c.venue_id
            WHERE v.venue_id = '{venue_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
            GROUP BY v.venue_id
            HAVING COUNT(DISTINCT artist_id) > 1
        )
        SELECT 
            vs.*,
            COALESCE(ls.location_popularity, 0) as location_popularity,
            COALESCE(vs.unique_artists::float / NULLIF(vs.total_concerts, 0), 0) as artist_diversity_score,
            COALESCE(rb.repeat_rate, 0) as repeat_booking_rate
        FROM venue_stats vs
        LEFT JOIN location_stats ls ON vs.venue_id = ls.venue_id
        LEFT JOIN repeat_bookings rb ON vs.venue_id = rb.venue_id
        """
        
        try:
            result = self.redshift_client.execute_query(query)
            
            if not result or len(result) == 0:
                logger.warning(f"No data found for venue {venue_id}")
                return None
            
            row = result[0]
            
            return VenueFeatures(
                venue_id=row['venue_id'],
                total_concerts=row['total_concerts'] or 0,
                avg_attendance=row['avg_attendance'] or 0.0,
                avg_attendance_rate=row['avg_attendance_rate'] or 0.0,
                total_revenue=row['total_revenue'] or 0.0,
                avg_revenue_per_event=row['avg_revenue_per_event'] or 0.0,
                booking_frequency=row['booking_frequency'] or 0.0,
                capacity=row['capacity'],
                venue_type=row['venue_type'],
                location_popularity=row['location_popularity'] or 0.0,
                artist_diversity_score=row['artist_diversity_score'] or 0.0,
                repeat_booking_rate=row['repeat_booking_rate'] or 0.0
            )
            
        except Exception as e:
            logger.error(f"Error extracting features for venue {venue_id}: {str(e)}")
            return None

    def extract_all_venue_features(self, lookback_days: int = 365) -> pd.DataFrame:
        """
        Extract features for all venues in the system
        
        Args:
            lookback_days: Number of days to look back for historical data
            
        Returns:
            DataFrame with venue features
        """
        query = """
        SELECT DISTINCT venue_id FROM venues
        """
        
        try:
            venues = self.redshift_client.execute_query(query)
            venue_ids = [v['venue_id'] for v in venues]
            
            features_list = []
            for venue_id in venue_ids:
                features = self.extract_venue_features(venue_id, lookback_days)
                if features:
                    features_list.append(features)
            
            if not features_list:
                logger.warning("No venue features extracted")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for features in features_list:
                row = {
                    'venue_id': features.venue_id,
                    **dict(zip(VenueFeatures.get_feature_names(), features.to_feature_vector()))
                }
                data.append(row)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error extracting all venue features: {str(e)}")
            return pd.DataFrame()
    
    def calculate_popularity_scores(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate popularity scores based on weighted features
        
        Args:
            features_df: DataFrame with venue features
            
        Returns:
            DataFrame with popularity scores and rankings
        """
        if features_df.empty:
            return pd.DataFrame()
        
        # Normalize features to 0-1 scale
        feature_cols = VenueFeatures.get_feature_names()
        normalized_df = features_df.copy()
        
        for col in feature_cols:
            if col in normalized_df.columns:
                max_val = normalized_df[col].max()
                if max_val > 0:
                    normalized_df[col] = normalized_df[col] / max_val
        
        # Weighted popularity score
        weights = {
            'total_concerts': 0.15,
            'avg_attendance': 0.10,
            'avg_attendance_rate': 0.20,
            'total_revenue': 0.10,
            'avg_revenue_per_event': 0.15,
            'booking_frequency': 0.15,
            'capacity': 0.05,
            'venue_type_encoded': 0.02,
            'location_popularity': 0.03,
            'artist_diversity_score': 0.03,
            'repeat_booking_rate': 0.02
        }
        
        normalized_df['popularity_score'] = 0.0
        for col, weight in weights.items():
            if col in normalized_df.columns:
                normalized_df['popularity_score'] += normalized_df[col] * weight
        
        # Rank venues by popularity score
        normalized_df['popularity_rank'] = normalized_df['popularity_score'].rank(
            ascending=False, method='dense'
        ).astype(int)
        
        # Add original metrics back
        result_df = pd.DataFrame({
            'venue_id': features_df['venue_id'],
            'popularity_rank': normalized_df['popularity_rank'],
            'popularity_score': normalized_df['popularity_score'],
            'avg_attendance_rate': features_df['avg_attendance_rate'],
            'avg_revenue_per_event': features_df['avg_revenue_per_event'],
            'booking_frequency': features_df['booking_frequency']
        })
        
        return result_df.sort_values('popularity_rank')
    
    def get_venue_popularity_ranking(self, lookback_days: int = 365) -> List[VenuePopularity]:
        """
        Get complete venue popularity rankings
        
        Args:
            lookback_days: Number of days to look back for historical data
            
        Returns:
            List of VenuePopularity objects sorted by rank
        """
        features_df = self.extract_all_venue_features(lookback_days)
        
        if features_df.empty:
            logger.warning("No features available for ranking")
            return []
        
        rankings_df = self.calculate_popularity_scores(features_df)
        
        results = []
        calculated_at = datetime.now()
        
        for _, row in rankings_df.iterrows():
            results.append(VenuePopularity(
                venue_id=row['venue_id'],
                popularity_rank=int(row['popularity_rank']),
                avg_attendance_rate=float(row['avg_attendance_rate']),
                revenue_per_event=float(row['avg_revenue_per_event']),
                booking_frequency=float(row['booking_frequency']),
                calculated_at=calculated_at
            ))
        
        return results
    
    def prepare_training_data(self, output_path: str, lookback_days: int = 365) -> Tuple[str, int]:
        """
        Prepare training data for SageMaker model
        
        Args:
            output_path: S3 path to save training data
            lookback_days: Number of days to look back for historical data
            
        Returns:
            Tuple of (S3 path, number of records)
        """
        features_df = self.extract_all_venue_features(lookback_days)
        
        if features_df.empty:
            raise ValueError("No training data available")
        
        # Calculate target variable (popularity score)
        rankings_df = self.calculate_popularity_scores(features_df)
        
        # Merge features with target
        training_df = features_df.merge(
            rankings_df[['venue_id', 'popularity_score']], 
            on='venue_id'
        )
        
        # Prepare for SageMaker (target first, then features)
        feature_cols = VenueFeatures.get_feature_names()
        training_data = training_df[['popularity_score'] + feature_cols]
        
        # Save to S3
        s3_client = boto3.client('s3')
        bucket = output_path.split('/')[2]
        key = '/'.join(output_path.split('/')[3:]) + '/training_data.csv'
        
        csv_buffer = training_data.to_csv(index=False, header=False)
        s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer)
        
        full_path = f"s3://{bucket}/{key}"
        logger.info(f"Training data saved to {full_path}")
        
        return full_path, len(training_data)

    def train_sagemaker_model(
        self, 
        training_data_path: str,
        model_output_path: str,
        role_arn: str,
        instance_type: str = 'ml.m5.xlarge'
    ) -> Dict:
        """
        Train SageMaker model for venue popularity prediction
        
        Args:
            training_data_path: S3 path to training data
            model_output_path: S3 path for model artifacts
            role_arn: IAM role ARN for SageMaker
            instance_type: EC2 instance type for training
            
        Returns:
            Dictionary with training job details
        """
        from sagemaker import get_execution_role
        from sagemaker.estimator import Estimator
        from sagemaker.inputs import TrainingInput
        
        training_job_name = f"venue-popularity-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Use XGBoost algorithm for regression
        container = sagemaker.image_uris.retrieve(
            framework='xgboost',
            region=boto3.Session().region_name,
            version='1.5-1'
        )
        
        estimator = Estimator(
            image_uri=container,
            role=role_arn,
            instance_count=1,
            instance_type=instance_type,
            output_path=model_output_path,
            sagemaker_session=sagemaker.Session(),
            base_job_name='venue-popularity'
        )
        
        # Set hyperparameters for regression
        estimator.set_hyperparameters(
            objective='reg:squarederror',
            num_round=100,
            max_depth=5,
            eta=0.2,
            subsample=0.8,
            colsample_bytree=0.8
        )
        
        # Train the model
        training_input = TrainingInput(
            s3_data=training_data_path,
            content_type='text/csv'
        )
        
        logger.info(f"Starting training job: {training_job_name}")
        estimator.fit({'train': training_input}, job_name=training_job_name)
        
        return {
            'job_name': training_job_name,
            'model_data': estimator.model_data,
            'training_image': container,
            'status': 'completed'
        }
    
    def deploy_model(
        self,
        model_data_path: str,
        role_arn: str,
        endpoint_name: Optional[str] = None,
        instance_type: str = 'ml.t2.medium'
    ) -> str:
        """
        Deploy trained model to SageMaker endpoint
        
        Args:
            model_data_path: S3 path to model artifacts
            role_arn: IAM role ARN for SageMaker
            endpoint_name: Optional custom endpoint name
            instance_type: EC2 instance type for endpoint
            
        Returns:
            Endpoint name
        """
        from sagemaker.model import Model
        from sagemaker.predictor import Predictor
        
        if not endpoint_name:
            endpoint_name = f"venue-popularity-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Get XGBoost container
        container = sagemaker.image_uris.retrieve(
            framework='xgboost',
            region=boto3.Session().region_name,
            version='1.5-1'
        )
        
        # Create model
        model = Model(
            image_uri=container,
            model_data=model_data_path,
            role=role_arn,
            sagemaker_session=sagemaker.Session()
        )
        
        # Deploy to endpoint
        logger.info(f"Deploying model to endpoint: {endpoint_name}")
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type=instance_type,
            endpoint_name=endpoint_name
        )
        
        logger.info(f"Model deployed successfully to {endpoint_name}")
        return endpoint_name
    
    def predict_venue_popularity(
        self,
        venue_id: str,
        endpoint_name: str,
        lookback_days: int = 365
    ) -> Dict:
        """
        Predict venue popularity using deployed SageMaker endpoint
        
        Args:
            venue_id: Venue identifier
            endpoint_name: SageMaker endpoint name
            lookback_days: Number of days for feature extraction
            
        Returns:
            Dictionary with prediction results
        """
        # Extract features for the venue
        features = self.extract_venue_features(venue_id, lookback_days)
        
        if not features:
            raise ValueError(f"Could not extract features for venue {venue_id}")
        
        # Prepare input for prediction
        feature_vector = features.to_feature_vector()
        payload = ','.join(map(str, feature_vector))
        
        # Invoke endpoint
        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=payload
        )
        
        # Parse prediction
        result = json.loads(response['Body'].read().decode())
        predicted_score = float(result) if isinstance(result, (int, float)) else float(result[0])
        
        return {
            'venue_id': venue_id,
            'predicted_popularity_score': predicted_score,
            'features': features,
            'prediction_timestamp': datetime.now().isoformat()
        }
    
    def batch_predict_popularity(
        self,
        venue_ids: List[str],
        endpoint_name: str,
        lookback_days: int = 365
    ) -> List[Dict]:
        """
        Predict popularity for multiple venues
        
        Args:
            venue_ids: List of venue identifiers
            endpoint_name: SageMaker endpoint name
            lookback_days: Number of days for feature extraction
            
        Returns:
            List of prediction results
        """
        results = []
        
        for venue_id in venue_ids:
            try:
                prediction = self.predict_venue_popularity(
                    venue_id, endpoint_name, lookback_days
                )
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error predicting for venue {venue_id}: {str(e)}")
                results.append({
                    'venue_id': venue_id,
                    'error': str(e),
                    'prediction_timestamp': datetime.now().isoformat()
                })
        
        return results
