"""
Example usage of Ticket Sales Prediction Service

This script demonstrates how to:
1. Extract features combining artist popularity, venue capacity, and historical sales
2. Train a regression model to predict ticket sales potential
3. Make predictions with confidence scoring and low-confidence flagging
"""
import logging
from datetime import datetime, timedelta
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_feature_extraction():
    """Example: Extract features for ticket sales prediction"""
    logger.info("=== Feature Extraction Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Extract features for a specific concert
    concert_id = "con_001"
    artist_id = "art_001"
    venue_id = "ven_001"
    event_date = datetime.now() + timedelta(days=60)
    ticket_prices = {
        'general': 75.0,
        'premium': 125.0,
        'vip': 250.0
    }
    
    features = service.extract_concert_features(
        concert_id=concert_id,
        artist_id=artist_id,
        venue_id=venue_id,
        event_date=event_date,
        ticket_prices=ticket_prices,
        lookback_days=730
    )
    
    if features:
        logger.info(f"Extracted features for concert {concert_id}:")
        logger.info(f"  Artist popularity: {features.artist_popularity_score}")
        logger.info(f"  Artist avg attendance: {features.artist_avg_attendance}")
        logger.info(f"  Venue capacity: {features.venue_capacity}")
        logger.info(f"  Venue attendance rate: {features.venue_avg_attendance_rate}")
        logger.info(f"  Historical avg sales: {features.historical_avg_sales}")
        logger.info(f"  Days until event: {features.days_until_event}")
        logger.info(f"  Average ticket price: ${features.avg_ticket_price:.2f}")
        logger.info(f"  Feature vector length: {len(features.to_feature_vector())}")
    else:
        logger.warning("Could not extract features")
    
    redshift_client.close()


def example_prepare_training_data():
    """Example: Prepare training data for model"""
    logger.info("\n=== Training Data Preparation Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Extract features for all completed concerts
    logger.info("Extracting features for all completed concerts...")
    features_df = service.extract_all_concert_features(lookback_days=730)
    
    if not features_df.empty:
        logger.info(f"Extracted features for {len(features_df)} concerts")
        logger.info(f"Feature columns: {list(features_df.columns)}")
        logger.info(f"\nSample statistics:")
        logger.info(f"  Avg actual sales: ${features_df['actual_sales'].mean():.2f}")
        logger.info(f"  Min actual sales: ${features_df['actual_sales'].min():.2f}")
        logger.info(f"  Max actual sales: ${features_df['actual_sales'].max():.2f}")
        
        # Prepare training data and save to S3
        try:
            output_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales"
            s3_path, num_records = service.prepare_training_data(
                output_path=output_path,
                lookback_days=730
            )
            logger.info(f"Training data saved to {s3_path}")
            logger.info(f"Total training records: {num_records}")
        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
    else:
        logger.warning("No training data available")
    
    redshift_client.close()


def example_train_model():
    """Example: Train SageMaker model for ticket sales prediction"""
    logger.info("\n=== Model Training Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Prepare training data
    training_data_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales"
    model_output_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales/output"
    
    try:
        logger.info("Starting model training...")
        result = service.train_sagemaker_model(
            training_data_path=training_data_path + "/training_data.csv",
            model_output_path=model_output_path,
            role_arn=settings.SAGEMAKER_ROLE_ARN,
            instance_type='ml.m5.xlarge'
        )
        
        logger.info(f"Training job completed: {result['job_name']}")
        logger.info(f"Model artifacts: {result['model_data']}")
        logger.info(f"Status: {result['status']}")
        
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
    
    redshift_client.close()


def example_deploy_model():
    """Example: Deploy trained model to SageMaker endpoint"""
    logger.info("\n=== Model Deployment Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Deploy model
    model_data_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales/output/model.tar.gz"
    
    try:
        logger.info("Deploying model to endpoint...")
        endpoint_name = service.deploy_model(
            model_data_path=model_data_path,
            role_arn=settings.SAGEMAKER_ROLE_ARN,
            endpoint_name="ticket-sales-prediction-demo",
            instance_type='ml.t2.medium'
        )
        
        logger.info(f"Model deployed to endpoint: {endpoint_name}")
        
    except Exception as e:
        logger.error(f"Error deploying model: {str(e)}")
    
    redshift_client.close()


def example_predict_ticket_sales():
    """Example: Predict ticket sales with confidence scoring"""
    logger.info("\n=== Ticket Sales Prediction Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Predict sales for an upcoming concert
    concert_id = "con_future_001"
    artist_id = "art_001"
    venue_id = "ven_001"
    event_date = datetime.now() + timedelta(days=60)
    ticket_prices = {
        'general': 75.0,
        'premium': 125.0,
        'vip': 250.0
    }
    endpoint_name = "ticket-sales-prediction-demo"
    
    try:
        logger.info(f"Predicting ticket sales for concert {concert_id}...")
        prediction = service.predict_ticket_sales(
            concert_id=concert_id,
            artist_id=artist_id,
            venue_id=venue_id,
            event_date=event_date,
            ticket_prices=ticket_prices,
            endpoint_name=endpoint_name
        )
        
        logger.info(f"\nPrediction Results:")
        logger.info(f"  Prediction ID: {prediction.prediction_id}")
        logger.info(f"  Concert ID: {prediction.concert_id}")
        logger.info(f"  Predicted Sales: ${prediction.predicted_sales:,.2f}")
        logger.info(f"  Confidence Score: {prediction.confidence_score:.3f}")
        logger.info(f"  Low Confidence Flag: {prediction.low_confidence_flag}")
        
        if prediction.low_confidence_flag:
            logger.warning(
                f"⚠️  Low confidence prediction detected! "
                f"Confidence score {prediction.confidence_score:.3f} is below threshold of 0.7"
            )
        else:
            logger.info(
                f"✓ High confidence prediction "
                f"(confidence score: {prediction.confidence_score:.3f})"
            )
        
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
    
    redshift_client.close()


def example_batch_predictions():
    """Example: Batch predict sales for multiple concerts"""
    logger.info("\n=== Batch Predictions Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Define multiple concerts to predict
    concerts = [
        {
            'concert_id': 'con_future_001',
            'artist_id': 'art_001',
            'venue_id': 'ven_001',
            'event_date': datetime.now() + timedelta(days=30),
            'ticket_prices': {'general': 50.0, 'vip': 150.0}
        },
        {
            'concert_id': 'con_future_002',
            'artist_id': 'art_002',
            'venue_id': 'ven_002',
            'event_date': datetime.now() + timedelta(days=60),
            'ticket_prices': {'general': 75.0, 'premium': 125.0, 'vip': 250.0}
        },
        {
            'concert_id': 'con_future_003',
            'artist_id': 'art_003',
            'venue_id': 'ven_001',
            'event_date': datetime.now() + timedelta(days=90),
            'ticket_prices': {'general': 100.0, 'vip': 300.0}
        }
    ]
    
    endpoint_name = "ticket-sales-prediction-demo"
    
    try:
        logger.info(f"Predicting sales for {len(concerts)} concerts...")
        predictions = service.batch_predict_sales(
            concerts=concerts,
            endpoint_name=endpoint_name
        )
        
        logger.info(f"\nBatch Prediction Results:")
        logger.info(f"Total predictions: {len(predictions)}")
        
        low_confidence_count = sum(1 for p in predictions if p.low_confidence_flag)
        logger.info(f"Low confidence predictions: {low_confidence_count}")
        
        for i, prediction in enumerate(predictions, 1):
            logger.info(f"\n  Prediction {i}:")
            logger.info(f"    Concert: {prediction.concert_id}")
            logger.info(f"    Predicted Sales: ${prediction.predicted_sales:,.2f}")
            logger.info(f"    Confidence: {prediction.confidence_score:.3f}")
            logger.info(f"    Low Confidence: {'⚠️ YES' if prediction.low_confidence_flag else '✓ NO'}")
        
    except Exception as e:
        logger.error(f"Error making batch predictions: {str(e)}")
    
    redshift_client.close()


def example_evaluate_model():
    """Example: Evaluate model performance on test data"""
    logger.info("\n=== Model Evaluation Example ===")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    endpoint_name = "ticket-sales-prediction-demo"
    
    try:
        logger.info("Evaluating model performance on recent concerts...")
        metrics = service.evaluate_model_performance(
            endpoint_name=endpoint_name,
            lookback_days=730
        )
        
        if 'error' in metrics:
            logger.error(f"Evaluation error: {metrics['error']}")
        else:
            logger.info(f"\nModel Performance Metrics:")
            logger.info(f"  Number of predictions: {metrics['num_predictions']}")
            logger.info(f"  Mean Absolute Error: ${metrics['mean_absolute_error']:,.2f}")
            logger.info(f"  Root Mean Squared Error: ${metrics['root_mean_squared_error']:,.2f}")
            logger.info(f"  Mean Absolute Percentage Error: {metrics['mean_absolute_percentage_error']:.2f}%")
            logger.info(f"  R-squared: {metrics['r_squared']:.4f}")
            logger.info(f"  Average Confidence Score: {metrics['avg_confidence_score']:.3f}")
            logger.info(f"  Low Confidence Count: {metrics['low_confidence_count']}")
            logger.info(f"  Low Confidence Percentage: {metrics['low_confidence_percentage']:.2f}%")
        
    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}")
    
    redshift_client.close()


def main():
    """Run all examples"""
    logger.info("Starting Ticket Sales Prediction Service Examples\n")
    
    try:
        # Example 1: Feature extraction
        example_feature_extraction()
        
        # Example 2: Prepare training data
        example_prepare_training_data()
        
        # Example 3: Train model (commented out - takes time)
        # example_train_model()
        
        # Example 4: Deploy model (commented out - requires trained model)
        # example_deploy_model()
        
        # Example 5: Single prediction with confidence scoring
        example_predict_ticket_sales()
        
        # Example 6: Batch predictions
        example_batch_predictions()
        
        # Example 7: Model evaluation
        example_evaluate_model()
        
        logger.info("\n=== All examples completed ===")
        
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}")


if __name__ == "__main__":
    main()
