"""
Example usage of Venue Popularity Service
Demonstrates feature engineering, model training, and prediction
"""
import os
from src.services.venue_popularity_service import VenuePopularityService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings


def example_calculate_rankings():
    """Example: Calculate venue popularity rankings from historical data"""
    print("=== Calculating Venue Popularity Rankings ===\n")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        cluster_identifier=settings.REDSHIFT_CLUSTER_ID,
        database=settings.REDSHIFT_DATABASE,
        db_user=settings.REDSHIFT_USER
    )
    
    service = VenuePopularityService(redshift_client)
    
    # Get rankings for past year
    rankings = service.get_venue_popularity_ranking(lookback_days=365)
    
    print(f"Found {len(rankings)} venues\n")
    print("Top 10 Most Popular Venues:")
    print("-" * 80)
    
    for venue in rankings[:10]:
        print(f"Rank {venue.popularity_rank}: {venue.venue_id}")
        print(f"  Attendance Rate: {venue.avg_attendance_rate:.2%}")
        print(f"  Revenue per Event: ${venue.revenue_per_event:,.2f}")
        print(f"  Booking Frequency: {venue.booking_frequency:.2f} concerts/month")
        print()


def example_train_model():
    """Example: Train SageMaker model for venue popularity prediction"""
    print("=== Training Venue Popularity Model ===\n")
    
    # Initialize clients
    settings = Settings()
    redshift_client = RedshiftClient(
        cluster_identifier=settings.REDSHIFT_CLUSTER_ID,
        database=settings.REDSHIFT_DATABASE,
        db_user=settings.REDSHIFT_USER
    )
    
    service = VenuePopularityService(redshift_client)
    
    # Prepare training data
    print("Extracting features and preparing training data...")
    training_path, num_records = service.prepare_training_data(
        output_path=f"s3://{settings.S3_BUCKET}/sagemaker/venue-popularity",
        lookback_days=365
    )
    
    print(f"Training data prepared: {num_records} records")
    print(f"Data location: {training_path}\n")
    
    # Train model
    print("Starting SageMaker training job...")
    training_result = service.train_sagemaker_model(
        training_data_path=training_path,
        model_output_path=f"s3://{settings.S3_BUCKET}/sagemaker/models",
        role_arn=settings.SAGEMAKER_ROLE_ARN,
        instance_type='ml.m5.xlarge'
    )
    
    print(f"Training job: {training_result['job_name']}")
    print(f"Status: {training_result['status']}")
    print(f"Model artifacts: {training_result['model_data']}\n")
    
    return training_result


def example_deploy_model(model_data_path: str):
    """Example: Deploy trained model to SageMaker endpoint"""
    print("=== Deploying Venue Popularity Model ===\n")
    
    settings = Settings()
    redshift_client = RedshiftClient(
        cluster_identifier=settings.REDSHIFT_CLUSTER_ID,
        database=settings.REDSHIFT_DATABASE,
        db_user=settings.REDSHIFT_USER
    )
    
    service = VenuePopularityService(redshift_client)
    
    # Deploy model
    print("Deploying model to SageMaker endpoint...")
    endpoint_name = service.deploy_model(
        model_data_path=model_data_path,
        role_arn=settings.SAGEMAKER_ROLE_ARN,
        instance_type='ml.t2.medium'
    )
    
    print(f"Model deployed to endpoint: {endpoint_name}\n")
    return endpoint_name


def example_predict_popularity(endpoint_name: str, venue_id: str):
    """Example: Predict venue popularity using deployed model"""
    print("=== Predicting Venue Popularity ===\n")
    
    settings = Settings()
    redshift_client = RedshiftClient(
        cluster_identifier=settings.REDSHIFT_CLUSTER_ID,
        database=settings.REDSHIFT_DATABASE,
        db_user=settings.REDSHIFT_USER
    )
    
    service = VenuePopularityService(redshift_client)
    
    # Make prediction
    print(f"Predicting popularity for venue: {venue_id}")
    result = service.predict_venue_popularity(
        venue_id=venue_id,
        endpoint_name=endpoint_name,
        lookback_days=365
    )
    
    print(f"\nPrediction Results:")
    print(f"  Venue ID: {result['venue_id']}")
    print(f"  Predicted Popularity Score: {result['predicted_popularity_score']:.4f}")
    print(f"  Timestamp: {result['prediction_timestamp']}")
    
    features = result['features']
    print(f"\nFeature Summary:")
    print(f"  Total Concerts: {features.total_concerts}")
    print(f"  Avg Attendance Rate: {features.avg_attendance_rate:.2%}")
    print(f"  Avg Revenue per Event: ${features.avg_revenue_per_event:,.2f}")
    print(f"  Booking Frequency: {features.booking_frequency:.2f} concerts/month")


def example_batch_predict(endpoint_name: str):
    """Example: Batch predict popularity for multiple venues"""
    print("=== Batch Predicting Venue Popularity ===\n")
    
    settings = Settings()
    redshift_client = RedshiftClient(
        cluster_identifier=settings.REDSHIFT_CLUSTER_ID,
        database=settings.REDSHIFT_DATABASE,
        db_user=settings.REDSHIFT_USER
    )
    
    service = VenuePopularityService(redshift_client)
    
    # Get sample venue IDs
    query = "SELECT venue_id FROM venues LIMIT 5"
    venues = redshift_client.execute_query(query)
    venue_ids = [v['venue_id'] for v in venues]
    
    print(f"Predicting popularity for {len(venue_ids)} venues...")
    results = service.batch_predict_popularity(
        venue_ids=venue_ids,
        endpoint_name=endpoint_name,
        lookback_days=365
    )
    
    print("\nBatch Prediction Results:")
    print("-" * 80)
    
    for result in results:
        if 'error' in result:
            print(f"Venue {result['venue_id']}: ERROR - {result['error']}")
        else:
            print(f"Venue {result['venue_id']}: Score = {result['predicted_popularity_score']:.4f}")


def main():
    """Run complete workflow example"""
    print("=" * 80)
    print("VENUE POPULARITY MODEL - COMPLETE WORKFLOW")
    print("=" * 80)
    print()
    
    # Step 1: Calculate rankings using rule-based approach
    example_calculate_rankings()
    
    # Step 2: Train ML model
    training_result = example_train_model()
    
    # Step 3: Deploy model
    endpoint_name = example_deploy_model(training_result['model_data'])
    
    # Step 4: Make predictions
    example_predict_popularity(endpoint_name, venue_id='venue_001')
    
    # Step 5: Batch predictions
    example_batch_predict(endpoint_name)
    
    print("\n" + "=" * 80)
    print("Workflow completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    # Run individual examples or complete workflow
    
    # Option 1: Calculate rankings only (no ML)
    # example_calculate_rankings()
    
    # Option 2: Complete ML workflow
    main()
