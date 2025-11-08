"""
Validation script for Ticket Sales Prediction implementation

This script validates that the ticket sales prediction system meets all requirements:
- Features combining artist popularity, venue capacity, and historical sales
- Regression model training capability
- Confidence scoring and low-confidence flagging
"""
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_model_structure():
    """Validate ticket sales prediction model structure"""
    logger.info("Validating model structure...")
    
    try:
        from src.models.ticket_sales_prediction import (
            TicketSalesPrediction,
            TicketSalesFeatures
        )
        
        # Check TicketSalesPrediction model
        prediction_fields = TicketSalesPrediction.__dataclass_fields__
        required_prediction_fields = [
            'prediction_id', 'concert_id', 'artist_id', 'venue_id', 'event_date',
            'predicted_sales', 'confidence_score', 'low_confidence_flag',
            'prediction_timestamp', 'actual_sales'
        ]
        
        for field in required_prediction_fields:
            if field not in prediction_fields:
                logger.error(f"Missing field in TicketSalesPrediction: {field}")
                return False
        
        logger.info("✓ TicketSalesPrediction model has all required fields")
        
        # Check TicketSalesFeatures model
        features_fields = TicketSalesFeatures.__dataclass_fields__
        required_feature_categories = [
            'artist_popularity_score',  # Artist features
            'venue_capacity',  # Venue features
            'historical_avg_sales',  # Historical sales features
            'days_until_event',  # Temporal features
            'avg_ticket_price'  # Pricing features
        ]
        
        for field in required_feature_categories:
            if field not in features_fields:
                logger.error(f"Missing feature category in TicketSalesFeatures: {field}")
                return False
        
        logger.info("✓ TicketSalesFeatures model has all required feature categories")
        
        # Validate feature vector conversion
        feature_names = TicketSalesFeatures.get_feature_names()
        if len(feature_names) < 15:
            logger.error(f"Insufficient features: {len(feature_names)} (expected at least 15)")
            return False
        
        logger.info(f"✓ Feature vector has {len(feature_names)} features")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import models: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating model structure: {str(e)}")
        return False


def validate_service_structure():
    """Validate ticket sales prediction service structure"""
    logger.info("Validating service structure...")
    
    try:
        from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
        
        # Check required methods
        required_methods = [
            'extract_concert_features',
            'extract_all_concert_features',
            'prepare_training_data',
            'train_sagemaker_model',
            'deploy_model',
            'calculate_confidence_score',
            'predict_ticket_sales',
            'batch_predict_sales',
            'evaluate_model_performance'
        ]
        
        for method in required_methods:
            if not hasattr(TicketSalesPredictionService, method):
                logger.error(f"Missing method in TicketSalesPredictionService: {method}")
                return False
        
        logger.info("✓ TicketSalesPredictionService has all required methods")
        
        # Check confidence threshold constant
        if not hasattr(TicketSalesPredictionService, 'CONFIDENCE_THRESHOLD'):
            logger.error("Missing CONFIDENCE_THRESHOLD constant")
            return False
        
        if TicketSalesPredictionService.CONFIDENCE_THRESHOLD != 0.7:
            logger.error(f"CONFIDENCE_THRESHOLD should be 0.7, got {TicketSalesPredictionService.CONFIDENCE_THRESHOLD}")
            return False
        
        logger.info("✓ Confidence threshold set to 0.7")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import service: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating service structure: {str(e)}")
        return False


def validate_feature_engineering():
    """Validate feature engineering capabilities"""
    logger.info("Validating feature engineering...")
    
    try:
        from src.models.ticket_sales_prediction import TicketSalesFeatures
        from datetime import datetime
        
        # Create sample features
        features = TicketSalesFeatures(
            concert_id='test_001',
            artist_id='artist_001',
            venue_id='venue_001',
            event_date=datetime.now(),
            artist_popularity_score=85.5,
            artist_avg_attendance=15000.0,
            artist_total_concerts=50,
            artist_avg_revenue=500000.0,
            artist_genre_popularity=75.0,
            venue_capacity=20000,
            venue_avg_attendance_rate=0.85,
            venue_popularity_rank=5.0,
            venue_type_encoded=4.0,
            venue_location_popularity=100.0,
            historical_avg_sales=450000.0,
            historical_max_sales=750000.0,
            similar_concert_avg_sales=400000.0,
            days_until_event=60,
            is_weekend=True,
            month_of_year=7,
            season_encoded=3.0,
            avg_ticket_price=125.0,
            price_range=200.0,
            lowest_price=50.0,
            highest_price=250.0
        )
        
        # Test feature vector conversion
        feature_vector = features.to_feature_vector()
        
        if not isinstance(feature_vector, list):
            logger.error("Feature vector should be a list")
            return False
        
        if len(feature_vector) != len(TicketSalesFeatures.get_feature_names()):
            logger.error("Feature vector length doesn't match feature names")
            return False
        
        # Verify all values are numeric
        for i, value in enumerate(feature_vector):
            if not isinstance(value, (int, float)):
                logger.error(f"Feature {i} is not numeric: {type(value)}")
                return False
        
        logger.info(f"✓ Feature engineering works correctly ({len(feature_vector)} features)")
        
        # Validate feature categories
        feature_names = TicketSalesFeatures.get_feature_names()
        
        # Check for artist features
        artist_features = [f for f in feature_names if 'artist' in f]
        if len(artist_features) < 3:
            logger.error(f"Insufficient artist features: {len(artist_features)}")
            return False
        logger.info(f"✓ Artist features: {len(artist_features)}")
        
        # Check for venue features
        venue_features = [f for f in feature_names if 'venue' in f]
        if len(venue_features) < 3:
            logger.error(f"Insufficient venue features: {len(venue_features)}")
            return False
        logger.info(f"✓ Venue features: {len(venue_features)}")
        
        # Check for historical features
        historical_features = [f for f in feature_names if 'historical' in f or 'similar' in f]
        if len(historical_features) < 2:
            logger.error(f"Insufficient historical features: {len(historical_features)}")
            return False
        logger.info(f"✓ Historical sales features: {len(historical_features)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating feature engineering: {str(e)}")
        return False


def validate_confidence_scoring():
    """Validate confidence scoring implementation"""
    logger.info("Validating confidence scoring...")
    
    try:
        from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
        from src.models.ticket_sales_prediction import TicketSalesFeatures
        from datetime import datetime
        
        # Create mock service (without actual clients)
        class MockRedshiftClient:
            pass
        
        service = TicketSalesPredictionService(MockRedshiftClient())
        
        # Test confidence scoring with high-quality features
        high_quality_features = TicketSalesFeatures(
            concert_id='test_001',
            artist_id='artist_001',
            venue_id='venue_001',
            event_date=datetime.now(),
            artist_popularity_score=85.5,
            artist_avg_attendance=15000.0,
            artist_total_concerts=50,  # Good history
            artist_avg_revenue=500000.0,
            artist_genre_popularity=75.0,
            venue_capacity=20000,
            venue_avg_attendance_rate=0.85,  # Good venue performance
            venue_popularity_rank=5.0,
            venue_type_encoded=4.0,
            venue_location_popularity=100.0,
            historical_avg_sales=450000.0,  # Good historical data
            historical_max_sales=750000.0,
            similar_concert_avg_sales=400000.0,
            days_until_event=30,  # Near future
            is_weekend=True,
            month_of_year=7,
            season_encoded=3.0,
            avg_ticket_price=125.0,  # Has pricing
            price_range=200.0,
            lowest_price=50.0,
            highest_price=250.0
        )
        
        high_confidence = service.calculate_confidence_score(high_quality_features, 500000.0)
        
        if high_confidence < 0.7:
            logger.error(f"High quality features should have confidence >= 0.7, got {high_confidence}")
            return False
        
        logger.info(f"✓ High quality features confidence: {high_confidence:.3f}")
        
        # Test confidence scoring with low-quality features
        low_quality_features = TicketSalesFeatures(
            concert_id='test_002',
            artist_id='artist_002',
            venue_id='venue_002',
            event_date=datetime.now(),
            artist_popularity_score=30.0,
            artist_avg_attendance=0.0,
            artist_total_concerts=0,  # No history
            artist_avg_revenue=0.0,
            artist_genre_popularity=0.0,
            venue_capacity=5000,
            venue_avg_attendance_rate=0.0,  # No venue data
            venue_popularity_rank=999.0,
            venue_type_encoded=2.0,
            venue_location_popularity=0.0,
            historical_avg_sales=0.0,  # No historical data
            historical_max_sales=0.0,
            similar_concert_avg_sales=0.0,
            days_until_event=200,  # Far future
            is_weekend=False,
            month_of_year=2,
            season_encoded=1.0,
            avg_ticket_price=0.0,  # No pricing
            price_range=0.0,
            lowest_price=0.0,
            highest_price=0.0
        )
        
        low_confidence = service.calculate_confidence_score(low_quality_features, 100000.0)
        
        if low_confidence >= 0.7:
            logger.error(f"Low quality features should have confidence < 0.7, got {low_confidence}")
            return False
        
        logger.info(f"✓ Low quality features confidence: {low_confidence:.3f}")
        
        # Verify confidence is between 0 and 1
        if not (0 <= high_confidence <= 1) or not (0 <= low_confidence <= 1):
            logger.error("Confidence scores must be between 0 and 1")
            return False
        
        logger.info("✓ Confidence scoring works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating confidence scoring: {str(e)}")
        return False


def validate_example_usage():
    """Validate example usage file exists and is complete"""
    logger.info("Validating example usage file...")
    
    example_file = Path("src/services/example_ticket_sales_prediction_usage.py")
    
    if not example_file.exists():
        logger.error("Example usage file not found")
        return False
    
    content = example_file.read_text()
    
    required_examples = [
        'example_feature_extraction',
        'example_prepare_training_data',
        'example_train_model',
        'example_deploy_model',
        'example_predict_ticket_sales',
        'example_batch_predictions',
        'example_evaluate_model'
    ]
    
    for example in required_examples:
        if example not in content:
            logger.error(f"Missing example function: {example}")
            return False
    
    logger.info("✓ Example usage file is complete")
    
    return True


def validate_requirements_coverage():
    """Validate that implementation covers all requirements"""
    logger.info("Validating requirements coverage...")
    
    try:
        from src.models.ticket_sales_prediction import TicketSalesFeatures
        from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
        
        # Requirement 3.2: Features combining artist popularity, venue capacity, and historical sales
        feature_names = TicketSalesFeatures.get_feature_names()
        
        has_artist_popularity = any('artist' in f and 'popularity' in f for f in feature_names)
        has_venue_capacity = 'venue_capacity' in feature_names
        has_historical_sales = any('historical' in f and 'sales' in f for f in feature_names)
        
        if not (has_artist_popularity and has_venue_capacity and has_historical_sales):
            logger.error("Missing required feature categories")
            return False
        
        logger.info("✓ Requirement 3.2: Features combine artist popularity, venue capacity, and historical sales")
        
        # Requirement 3.2: Train regression model
        if not hasattr(TicketSalesPredictionService, 'train_sagemaker_model'):
            logger.error("Missing model training capability")
            return False
        
        logger.info("✓ Requirement 3.2: Regression model training implemented")
        
        # Requirement 3.5: Confidence scoring and low-confidence flagging
        if not hasattr(TicketSalesPredictionService, 'calculate_confidence_score'):
            logger.error("Missing confidence scoring")
            return False
        
        if TicketSalesPredictionService.CONFIDENCE_THRESHOLD != 0.7:
            logger.error("Confidence threshold not set to 0.7")
            return False
        
        logger.info("✓ Requirement 3.5: Confidence scoring with 0.7 threshold implemented")
        
        # Check that predictions include low_confidence_flag
        from src.models.ticket_sales_prediction import TicketSalesPrediction
        if 'low_confidence_flag' not in TicketSalesPrediction.__dataclass_fields__:
            logger.error("Missing low_confidence_flag in predictions")
            return False
        
        logger.info("✓ Requirement 3.5: Low-confidence flagging implemented")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating requirements coverage: {str(e)}")
        return False


def main():
    """Run all validation checks"""
    logger.info("=" * 60)
    logger.info("Ticket Sales Prediction Implementation Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Model Structure", validate_model_structure),
        ("Service Structure", validate_service_structure),
        ("Feature Engineering", validate_feature_engineering),
        ("Confidence Scoring", validate_confidence_scoring),
        ("Example Usage", validate_example_usage),
        ("Requirements Coverage", validate_requirements_coverage)
    ]
    
    results = []
    for check_name, check_func in checks:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Running: {check_name}")
        logger.info(f"{'=' * 60}")
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("VALIDATION SUMMARY")
    logger.info(f"{'=' * 60}")
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        logger.info(f"\n{'=' * 60}")
        logger.info("✓ ALL VALIDATIONS PASSED")
        logger.info(f"{'=' * 60}")
        logger.info("\nImplementation Summary:")
        logger.info("- Features combining artist popularity, venue capacity, and historical sales ✓")
        logger.info("- Regression model training for ticket sales prediction ✓")
        logger.info("- Confidence scoring with 0.7 threshold ✓")
        logger.info("- Low-confidence flagging for predictions below threshold ✓")
        return 0
    else:
        logger.error(f"\n{'=' * 60}")
        logger.error("✗ SOME VALIDATIONS FAILED")
        logger.error(f"{'=' * 60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
