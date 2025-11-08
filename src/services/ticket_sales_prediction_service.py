"""
Ticket Sales Prediction Service - Feature engineering and model training for ticket sales forecasting
"""
import boto3
import sagemaker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging
import uuid

from src.models.ticket_sales_prediction import TicketSalesFeatures, TicketSalesPrediction

logger = logging.getLogger(__name__)


class TicketSalesPredictionService:
    """Service for ticket sales prediction and forecasting"""
    
    CONFIDENCE_THRESHOLD = 0.7  # Low confidence flag threshold
    
    def __init__(self, redshift_client, sagemaker_client=None):
        """
        Initialize ticket sales prediction service
        
        Args:
            redshift_client: Client for querying Redshift data warehouse
            sagemaker_client: Optional SageMaker client for model operations
        """
        self.redshift_client = redshift_client
        self.sagemaker_client = sagemaker_client or boto3.client('sagemaker')
        self.sagemaker_runtime = boto3.client('sagemaker-runtime')
        
    def extract_concert_features(
        self, 
        concert_id: str,
        artist_id: str,
        venue_id: str,
        event_date: datetime,
        ticket_prices: Dict[str, float],
        lookback_days: int = 730
    ) -> Optional[TicketSalesFeatures]:
        """
        Extract features for a concert from historical data
        
        Args:
            concert_id: Unique concert identifier
            artist_id: Artist performing at the concert
            venue_id: Venue hosting the concert
            event_date: Date and time of the concert
            ticket_prices: Dictionary of ticket prices by tier
            lookback_days: Number of days to look back for historical data
            
        Returns:
            TicketSalesFeatures object or None if insufficient data
        """
        query = f"""
        WITH artist_stats AS (
            SELECT 
                a.artist_id,
                a.popularity_score,
                AVG(c.total_attendance) as avg_attendance,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.revenue) as avg_revenue,
                AVG(genre_pop.popularity) as genre_popularity
            FROM artists a
            LEFT JOIN concerts c ON a.artist_id = c.artist_id
            LEFT JOIN (
                SELECT genre, AVG(popularity_score) as popularity
                FROM artists
                GROUP BY genre
            ) genre_pop ON a.genre = genre_pop.genre
            WHERE a.artist_id = '{artist_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                AND c.status = 'completed'
            GROUP BY a.artist_id, a.popularity_score
        ),
        venue_stats AS (
            SELECT 
                v.venue_id,
                v.capacity,
                v.venue_type,
                AVG(c.total_attendance::float / v.capacity) as avg_attendance_rate,
                AVG(location_concerts.total) as location_popularity
            FROM venues v
            LEFT JOIN concerts c ON v.venue_id = c.venue_id
            LEFT JOIN (
                SELECT v2.location, COUNT(c2.concert_id) as total
                FROM venues v2
                LEFT JOIN concerts c2 ON v2.venue_id = c2.venue_id
                WHERE c2.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                GROUP BY v2.location
            ) location_concerts ON v.location = location_concerts.location
            WHERE v.venue_id = '{venue_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                AND c.status = 'completed'
            GROUP BY v.venue_id, v.capacity, v.venue_type
        ),
        venue_ranking AS (
            SELECT 
                venue_id,
                ROW_NUMBER() OVER (ORDER BY AVG(total_attendance) DESC) as popularity_rank
            FROM concerts
            WHERE event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
                AND status = 'completed'
            GROUP BY venue_id
        ),
        historical_sales AS (
            SELECT 
                AVG(ts.quantity * ts.unit_price) as avg_sales,
                MAX(ts.quantity * ts.unit_price) as max_sales
            FROM ticket_sales ts
            JOIN concerts c ON ts.concert_id = c.concert_id
            WHERE c.artist_id = '{artist_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
        ),
        similar_concerts AS (
            SELECT 
                AVG(ts.quantity * ts.unit_price) as similar_avg_sales
            FROM ticket_sales ts
            JOIN concerts c ON ts.concert_id = c.concert_id
            WHERE c.venue_id = '{venue_id}'
                AND c.artist_id != '{artist_id}'
                AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
        )
        SELECT 
            ast.artist_id,
            ast.popularity_score as artist_popularity_score,
            COALESCE(ast.avg_attendance, 0) as artist_avg_attendance,
            COALESCE(ast.total_concerts, 0) as artist_total_concerts,
            COALESCE(ast.avg_revenue, 0) as artist_avg_revenue,
            COALESCE(ast.genre_popularity, 0) as artist_genre_popularity,
            vs.capacity as venue_capacity,
            COALESCE(vs.avg_attendance_rate, 0) as venue_avg_attendance_rate,
            COALESCE(vr.popularity_rank, 999) as venue_popularity_rank,
            vs.venue_type,
            COALESCE(vs.location_popularity, 0) as venue_location_popularity,
            COALESCE(hs.avg_sales, 0) as historical_avg_sales,
            COALESCE(hs.max_sales, 0) as historical_max_sales,
            COALESCE(sc.similar_avg_sales, 0) as similar_concert_avg_sales
        FROM artist_stats ast
        CROSS JOIN venue_stats vs
        LEFT JOIN venue_ranking vr ON vs.venue_id = vr.venue_id
        LEFT JOIN historical_sales hs ON 1=1
        LEFT JOIN similar_concerts sc ON 1=1
        """
        
        try:
            result = self.redshift_client.execute_query(query)
            
            if not result or len(result) == 0:
                logger.warning(f"No data found for concert {concert_id}")
                return None
            
            row = result[0]
            
            # Calculate temporal features
            now = datetime.now()
            days_until_event = (event_date - now).days if event_date > now else 0
            is_weekend = event_date.weekday() >= 5  # Saturday=5, Sunday=6
            month_of_year = event_date.month
            
            # Calculate season (1=winter, 2=spring, 3=summer, 4=fall)
            season_map = {12: 1, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 
                         6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 4}
            season_encoded = float(season_map.get(month_of_year, 1))
            
            # Calculate pricing features
            if ticket_prices:
                prices = list(ticket_prices.values())
                avg_ticket_price = sum(prices) / len(prices)
                lowest_price = min(prices)
                highest_price = max(prices)
                price_range = highest_price - lowest_price
            else:
                avg_ticket_price = 0.0
                lowest_price = 0.0
                highest_price = 0.0
                price_range = 0.0
            
            # Encode venue type
            venue_type_encoding = {
                'arena': 4,
                'stadium': 5,
                'theater': 3,
                'club': 2,
                'outdoor': 1,
                'amphitheater': 3
            }
            venue_type_encoded = float(venue_type_encoding.get(
                row['venue_type'].lower(), 0
            ))
            
            return TicketSalesFeatures(
                concert_id=concert_id,
                artist_id=artist_id,
                venue_id=venue_id,
                event_date=event_date,
                artist_popularity_score=float(row['artist_popularity_score'] or 0),
                artist_avg_attendance=float(row['artist_avg_attendance'] or 0),
                artist_total_concerts=int(row['artist_total_concerts'] or 0),
                artist_avg_revenue=float(row['artist_avg_revenue'] or 0),
                artist_genre_popularity=float(row['artist_genre_popularity'] or 0),
                venue_capacity=int(row['venue_capacity']),
                venue_avg_attendance_rate=float(row['venue_avg_attendance_rate'] or 0),
                venue_popularity_rank=float(row['venue_popularity_rank'] or 999),
                venue_type_encoded=venue_type_encoded,
                venue_location_popularity=float(row['venue_location_popularity'] or 0),
                historical_avg_sales=float(row['historical_avg_sales'] or 0),
                historical_max_sales=float(row['historical_max_sales'] or 0),
                similar_concert_avg_sales=float(row['similar_concert_avg_sales'] or 0),
                days_until_event=days_until_event,
                is_weekend=is_weekend,
                month_of_year=month_of_year,
                season_encoded=season_encoded,
                avg_ticket_price=avg_ticket_price,
                price_range=price_range,
                lowest_price=lowest_price,
                highest_price=highest_price
            )
            
        except Exception as e:
            logger.error(f"Error extracting features for concert {concert_id}: {str(e)}")
            return None

    def extract_all_concert_features(self, lookback_days: int = 730) -> pd.DataFrame:
        """
        Extract features for all completed concerts in the system
        
        Args:
            lookback_days: Number of days to look back for historical data
            
        Returns:
            DataFrame with concert features and actual sales
        """
        query = f"""
        SELECT 
            c.concert_id,
            c.artist_id,
            c.venue_id,
            c.event_date,
            c.ticket_prices,
            SUM(ts.quantity * ts.unit_price) as actual_sales
        FROM concerts c
        LEFT JOIN ticket_sales ts ON c.concert_id = ts.concert_id
        WHERE c.status = 'completed'
            AND c.event_date >= DATEADD(day, -{lookback_days}, CURRENT_DATE)
            AND c.event_date <= CURRENT_DATE
        GROUP BY c.concert_id, c.artist_id, c.venue_id, c.event_date, c.ticket_prices
        HAVING SUM(ts.quantity * ts.unit_price) > 0
        """
        
        try:
            concerts = self.redshift_client.execute_query(query)
            
            if not concerts:
                logger.warning("No completed concerts found for training")
                return pd.DataFrame()
            
            features_list = []
            for concert in concerts:
                # Parse ticket prices from JSON string if needed
                ticket_prices = concert['ticket_prices']
                if isinstance(ticket_prices, str):
                    ticket_prices = json.loads(ticket_prices)
                
                features = self.extract_concert_features(
                    concert_id=concert['concert_id'],
                    artist_id=concert['artist_id'],
                    venue_id=concert['venue_id'],
                    event_date=concert['event_date'],
                    ticket_prices=ticket_prices,
                    lookback_days=lookback_days
                )
                
                if features:
                    feature_dict = {
                        'concert_id': features.concert_id,
                        'actual_sales': float(concert['actual_sales']),
                        **dict(zip(
                            TicketSalesFeatures.get_feature_names(),
                            features.to_feature_vector()
                        ))
                    }
                    features_list.append(feature_dict)
            
            if not features_list:
                logger.warning("No concert features extracted")
                return pd.DataFrame()
            
            return pd.DataFrame(features_list)
            
        except Exception as e:
            logger.error(f"Error extracting all concert features: {str(e)}")
            return pd.DataFrame()
    
    def prepare_training_data(
        self, 
        output_path: str, 
        lookback_days: int = 730
    ) -> Tuple[str, int]:
        """
        Prepare training data for SageMaker model
        
        Args:
            output_path: S3 path to save training data
            lookback_days: Number of days to look back for historical data
            
        Returns:
            Tuple of (S3 path, number of records)
        """
        features_df = self.extract_all_concert_features(lookback_days)
        
        if features_df.empty:
            raise ValueError("No training data available")
        
        # Prepare for SageMaker (target first, then features)
        feature_cols = TicketSalesFeatures.get_feature_names()
        training_data = features_df[['actual_sales'] + feature_cols]
        
        # Remove any rows with NaN values
        training_data = training_data.dropna()
        
        if len(training_data) == 0:
            raise ValueError("No valid training data after cleaning")
        
        # Save to S3
        s3_client = boto3.client('s3')
        bucket = output_path.split('/')[2]
        key = '/'.join(output_path.split('/')[3:]) + '/training_data.csv'
        
        csv_buffer = training_data.to_csv(index=False, header=False)
        s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer)
        
        full_path = f"s3://{bucket}/{key}"
        logger.info(f"Training data saved to {full_path} ({len(training_data)} records)")
        
        return full_path, len(training_data)

    def train_sagemaker_model(
        self, 
        training_data_path: str,
        model_output_path: str,
        role_arn: str,
        instance_type: str = 'ml.m5.xlarge'
    ) -> Dict:
        """
        Train SageMaker model for ticket sales prediction
        
        Args:
            training_data_path: S3 path to training data
            model_output_path: S3 path for model artifacts
            role_arn: IAM role ARN for SageMaker
            instance_type: EC2 instance type for training
            
        Returns:
            Dictionary with training job details
        """
        from sagemaker.estimator import Estimator
        from sagemaker.inputs import TrainingInput
        
        training_job_name = f"ticket-sales-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
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
            base_job_name='ticket-sales-prediction'
        )
        
        # Set hyperparameters for regression
        estimator.set_hyperparameters(
            objective='reg:squarederror',
            num_round=150,
            max_depth=6,
            eta=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            alpha=0.1  # L1 regularization
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
        
        if not endpoint_name:
            endpoint_name = f"ticket-sales-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
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
    
    def calculate_confidence_score(
        self,
        features: TicketSalesFeatures,
        prediction: float
    ) -> float:
        """
        Calculate confidence score for a prediction based on feature quality
        
        Args:
            features: Feature set used for prediction
            prediction: Predicted sales value
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence_factors = []
        
        # Factor 1: Artist history (0-1)
        if features.artist_total_concerts > 0:
            artist_confidence = min(features.artist_total_concerts / 20.0, 1.0)
        else:
            artist_confidence = 0.3  # Low confidence for new artists
        confidence_factors.append(artist_confidence)
        
        # Factor 2: Historical sales data availability (0-1)
        if features.historical_avg_sales > 0:
            history_confidence = 1.0
        elif features.similar_concert_avg_sales > 0:
            history_confidence = 0.7
        else:
            history_confidence = 0.4
        confidence_factors.append(history_confidence)
        
        # Factor 3: Venue data quality (0-1)
        if features.venue_avg_attendance_rate > 0:
            venue_confidence = min(features.venue_avg_attendance_rate, 1.0)
        else:
            venue_confidence = 0.5
        confidence_factors.append(venue_confidence)
        
        # Factor 4: Time until event (0-1)
        if features.days_until_event > 180:
            time_confidence = 0.6  # Far future = less confident
        elif features.days_until_event > 90:
            time_confidence = 0.8
        elif features.days_until_event > 30:
            time_confidence = 0.9
        else:
            time_confidence = 1.0
        confidence_factors.append(time_confidence)
        
        # Factor 5: Pricing data (0-1)
        if features.avg_ticket_price > 0:
            price_confidence = 1.0
        else:
            price_confidence = 0.5
        confidence_factors.append(price_confidence)
        
        # Calculate weighted average
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]
        confidence_score = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return round(confidence_score, 3)
    
    def predict_ticket_sales(
        self,
        concert_id: str,
        artist_id: str,
        venue_id: str,
        event_date: datetime,
        ticket_prices: Dict[str, float],
        endpoint_name: str,
        lookback_days: int = 730
    ) -> TicketSalesPrediction:
        """
        Predict ticket sales for a concert using deployed SageMaker endpoint
        
        Args:
            concert_id: Concert identifier
            artist_id: Artist performing
            venue_id: Venue hosting
            event_date: Date and time of concert
            ticket_prices: Dictionary of ticket prices by tier
            endpoint_name: SageMaker endpoint name
            lookback_days: Number of days for feature extraction
            
        Returns:
            TicketSalesPrediction object with results
        """
        # Extract features for the concert
        features = self.extract_concert_features(
            concert_id=concert_id,
            artist_id=artist_id,
            venue_id=venue_id,
            event_date=event_date,
            ticket_prices=ticket_prices,
            lookback_days=lookback_days
        )
        
        if not features:
            raise ValueError(f"Could not extract features for concert {concert_id}")
        
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
        predicted_sales = float(result) if isinstance(result, (int, float)) else float(result[0])
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(features, predicted_sales)
        low_confidence_flag = confidence_score < self.CONFIDENCE_THRESHOLD
        
        prediction_id = str(uuid.uuid4())
        
        return TicketSalesPrediction(
            prediction_id=prediction_id,
            concert_id=concert_id,
            artist_id=artist_id,
            venue_id=venue_id,
            event_date=event_date,
            predicted_sales=predicted_sales,
            confidence_score=confidence_score,
            low_confidence_flag=low_confidence_flag,
            prediction_timestamp=datetime.now()
        )
    
    def batch_predict_sales(
        self,
        concerts: List[Dict],
        endpoint_name: str,
        lookback_days: int = 730
    ) -> List[TicketSalesPrediction]:
        """
        Predict sales for multiple concerts
        
        Args:
            concerts: List of concert dictionaries with required fields
            endpoint_name: SageMaker endpoint name
            lookback_days: Number of days for feature extraction
            
        Returns:
            List of TicketSalesPrediction objects
        """
        results = []
        
        for concert in concerts:
            try:
                prediction = self.predict_ticket_sales(
                    concert_id=concert['concert_id'],
                    artist_id=concert['artist_id'],
                    venue_id=concert['venue_id'],
                    event_date=concert['event_date'],
                    ticket_prices=concert.get('ticket_prices', {}),
                    endpoint_name=endpoint_name,
                    lookback_days=lookback_days
                )
                results.append(prediction)
                
                if prediction.low_confidence_flag:
                    logger.warning(
                        f"Low confidence prediction for concert {concert['concert_id']}: "
                        f"confidence={prediction.confidence_score}"
                    )
                    
            except Exception as e:
                logger.error(f"Error predicting for concert {concert['concert_id']}: {str(e)}")
        
        return results
    
    def evaluate_model_performance(
        self,
        endpoint_name: str,
        test_concerts: Optional[List[Dict]] = None,
        lookback_days: int = 730
    ) -> Dict:
        """
        Evaluate model performance on test data
        
        Args:
            endpoint_name: SageMaker endpoint name
            test_concerts: Optional list of test concerts, otherwise uses recent data
            lookback_days: Number of days for feature extraction
            
        Returns:
            Dictionary with performance metrics
        """
        if not test_concerts:
            # Get recent completed concerts for evaluation
            query = f"""
            SELECT 
                c.concert_id,
                c.artist_id,
                c.venue_id,
                c.event_date,
                c.ticket_prices,
                SUM(ts.quantity * ts.unit_price) as actual_sales
            FROM concerts c
            LEFT JOIN ticket_sales ts ON c.concert_id = ts.concert_id
            WHERE c.status = 'completed'
                AND c.event_date >= DATEADD(day, -90, CURRENT_DATE)
            GROUP BY c.concert_id, c.artist_id, c.venue_id, c.event_date, c.ticket_prices
            HAVING SUM(ts.quantity * ts.unit_price) > 0
            LIMIT 100
            """
            test_concerts = self.redshift_client.execute_query(query)
        
        predictions = []
        actuals = []
        confidence_scores = []
        
        for concert in test_concerts:
            try:
                ticket_prices = concert.get('ticket_prices', {})
                if isinstance(ticket_prices, str):
                    ticket_prices = json.loads(ticket_prices)
                
                prediction = self.predict_ticket_sales(
                    concert_id=concert['concert_id'],
                    artist_id=concert['artist_id'],
                    venue_id=concert['venue_id'],
                    event_date=concert['event_date'],
                    ticket_prices=ticket_prices,
                    endpoint_name=endpoint_name,
                    lookback_days=lookback_days
                )
                
                predictions.append(prediction.predicted_sales)
                actuals.append(float(concert['actual_sales']))
                confidence_scores.append(prediction.confidence_score)
                
            except Exception as e:
                logger.error(f"Error evaluating concert {concert['concert_id']}: {str(e)}")
        
        if not predictions:
            return {'error': 'No predictions generated for evaluation'}
        
        # Calculate metrics
        predictions_arr = np.array(predictions)
        actuals_arr = np.array(actuals)
        
        mae = np.mean(np.abs(predictions_arr - actuals_arr))
        rmse = np.sqrt(np.mean((predictions_arr - actuals_arr) ** 2))
        mape = np.mean(np.abs((actuals_arr - predictions_arr) / actuals_arr)) * 100
        
        # R-squared
        ss_res = np.sum((actuals_arr - predictions_arr) ** 2)
        ss_tot = np.sum((actuals_arr - np.mean(actuals_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'num_predictions': len(predictions),
            'mean_absolute_error': float(mae),
            'root_mean_squared_error': float(rmse),
            'mean_absolute_percentage_error': float(mape),
            'r_squared': float(r_squared),
            'avg_confidence_score': float(np.mean(confidence_scores)),
            'low_confidence_count': sum(1 for c in confidence_scores if c < self.CONFIDENCE_THRESHOLD),
            'low_confidence_percentage': (
                sum(1 for c in confidence_scores if c < self.CONFIDENCE_THRESHOLD) / len(confidence_scores) * 100
            )
        }
