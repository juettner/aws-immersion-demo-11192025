"""
Validation script for Data Analysis Service implementation.

This script validates that the DataAnalysisService is properly implemented
according to task 5.2.2 requirements.
"""
import sys
from pathlib import Path


def validate_imports():
    """Validate that all required imports work."""
    print("Validating imports...")
    
    try:
        from src.services.data_analysis_service import (
            DataAnalysisService,
            AnalysisType,
            ChartType,
            AnalysisResult
        )
        print("✓ Core imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def validate_class_structure():
    """Validate that the DataAnalysisService class has required methods."""
    print("\nValidating class structure...")
    
    try:
        from src.services.data_analysis_service import DataAnalysisService
        
        required_methods = [
            "analyze_concert_trends",
            "compare_entities",
            "generate_statistical_summary",
            "predict_with_ml_models",
            "generate_recommendations_analysis",
            "format_for_chatbot",
            "prepare_visualization_data"
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(DataAnalysisService, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"✗ Missing methods: {', '.join(missing_methods)}")
            return False
        
        print(f"✓ All {len(required_methods)} required methods present")
        return True
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def validate_enums():
    """Validate that required enums are defined."""
    print("\nValidating enums...")
    
    try:
        from src.services.data_analysis_service import AnalysisType, ChartType
        
        # Check AnalysisType values
        required_analysis_types = [
            "TREND_ANALYSIS",
            "COMPARISON",
            "AGGREGATION",
            "PREDICTION",
            "RECOMMENDATION",
            "STATISTICAL_SUMMARY"
        ]
        
        for analysis_type in required_analysis_types:
            if not hasattr(AnalysisType, analysis_type):
                print(f"✗ Missing AnalysisType: {analysis_type}")
                return False
        
        # Check ChartType values
        required_chart_types = [
            "LINE",
            "BAR",
            "PIE",
            "SCATTER",
            "HEATMAP",
            "TABLE"
        ]
        
        for chart_type in required_chart_types:
            if not hasattr(ChartType, chart_type):
                print(f"✗ Missing ChartType: {chart_type}")
                return False
        
        print("✓ All required enum values present")
        return True
        
    except Exception as e:
        print(f"✗ Enum validation failed: {e}")
        return False


def validate_models():
    """Validate that AnalysisResult model is properly defined."""
    print("\nValidating data models...")
    
    try:
        from src.services.data_analysis_service import AnalysisResult, AnalysisType
        
        # Create a test instance
        result = AnalysisResult(
            analysis_type=AnalysisType.TREND_ANALYSIS,
            title="Test Analysis",
            summary="Test summary",
            insights=["Insight 1", "Insight 2"],
            data={"test": "data"}
        )
        
        # Validate required fields
        assert result.analysis_type == AnalysisType.TREND_ANALYSIS
        assert result.title == "Test Analysis"
        assert result.summary == "Test summary"
        assert len(result.insights) == 2
        assert result.data == {"test": "data"}
        assert result.timestamp is not None
        
        print("✓ AnalysisResult model validated")
        return True
        
    except Exception as e:
        print(f"✗ Model validation failed: {e}")
        return False


def validate_service_initialization():
    """Validate that the service can be initialized."""
    print("\nValidating service initialization...")
    
    try:
        from src.services.data_analysis_service import DataAnalysisService
        
        # Test initialization without dependencies
        service = DataAnalysisService()
        assert service is not None
        print("✓ Service initialized without dependencies")
        
        # Test initialization with None dependencies
        service = DataAnalysisService(
            redshift_service=None,
            venue_popularity_service=None,
            ticket_sales_service=None,
            recommendation_service=None
        )
        assert service is not None
        print("✓ Service initialized with explicit None dependencies")
        
        return True
        
    except Exception as e:
        print(f"✗ Initialization validation failed: {e}")
        return False


def validate_method_signatures():
    """Validate that methods have correct signatures."""
    print("\nValidating method signatures...")
    
    try:
        from src.services.data_analysis_service import DataAnalysisService
        import inspect
        
        service = DataAnalysisService()
        
        # Check analyze_concert_trends signature
        sig = inspect.signature(service.analyze_concert_trends)
        params = list(sig.parameters.keys())
        assert "time_period" in params
        assert "metric" in params
        assert "group_by" in params
        print("✓ analyze_concert_trends signature correct")
        
        # Check compare_entities signature
        sig = inspect.signature(service.compare_entities)
        params = list(sig.parameters.keys())
        assert "entity_type" in params
        assert "entity_ids" in params
        assert "metrics" in params
        print("✓ compare_entities signature correct")
        
        # Check predict_with_ml_models signature
        sig = inspect.signature(service.predict_with_ml_models)
        params = list(sig.parameters.keys())
        assert "prediction_type" in params
        assert "input_data" in params
        print("✓ predict_with_ml_models signature correct")
        
        # Check format_for_chatbot signature
        sig = inspect.signature(service.format_for_chatbot)
        params = list(sig.parameters.keys())
        assert "analysis_result" in params
        print("✓ format_for_chatbot signature correct")
        
        # Check prepare_visualization_data signature
        sig = inspect.signature(service.prepare_visualization_data)
        params = list(sig.parameters.keys())
        assert "analysis_result" in params
        assert "chart_type" in params
        print("✓ prepare_visualization_data signature correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Method signature validation failed: {e}")
        return False


def validate_example_file():
    """Validate that example usage file exists."""
    print("\nValidating example file...")
    
    example_file = Path("src/services/example_data_analysis_usage.py")
    
    if not example_file.exists():
        print(f"✗ Example file not found: {example_file}")
        return False
    
    print(f"✓ Example file exists: {example_file}")
    
    # Try to import it
    try:
        import src.services.example_data_analysis_usage
        print("✓ Example file imports successfully")
        return True
    except Exception as e:
        print(f"✗ Example file import failed: {e}")
        return False


def validate_integration_points():
    """Validate integration with other services."""
    print("\nValidating integration points...")
    
    try:
        from src.services.data_analysis_service import DataAnalysisService
        from src.services.redshift_service import RedshiftService
        from src.services.venue_popularity_service import VenuePopularityService
        from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
        from src.services.recommendation_service import RecommendationService
        
        # Test that service accepts all integration services
        service = DataAnalysisService(
            redshift_service=RedshiftService(),
            venue_popularity_service=VenuePopularityService(redshift_client=None),
            ticket_sales_service=TicketSalesPredictionService(redshift_client=None),
            recommendation_service=RecommendationService()
        )
        
        assert service.redshift_service is not None
        assert service.venue_popularity_service is not None
        assert service.ticket_sales_service is not None
        assert service.recommendation_service is not None
        
        print("✓ All service integrations validated")
        return True
        
    except Exception as e:
        print(f"✗ Integration validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 80)
    print("Data Analysis Service Validation")
    print("=" * 80)
    
    validations = [
        ("Imports", validate_imports),
        ("Class Structure", validate_class_structure),
        ("Enums", validate_enums),
        ("Data Models", validate_models),
        ("Service Initialization", validate_service_initialization),
        ("Method Signatures", validate_method_signatures),
        ("Example File", validate_example_file),
        ("Integration Points", validate_integration_points)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} validation crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✓ All validations passed! Implementation is complete.")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
