"""
Validation script for External Data Enrichment and Visualization services.
"""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def validate_imports():
    """Validate that all required modules can be imported."""
    print("Validating imports...")
    
    try:
        from services.external_data_enrichment_service import (
            ExternalDataEnrichmentService,
            EnrichmentResult,
            CachedData
        )
        print("✓ External data enrichment service imports successful")
    except ImportError as e:
        print(f"✗ Failed to import external data enrichment service: {e}")
        return False
    
    try:
        from services.data_visualization_service import (
            DataVisualizationService,
            VisualizationResult
        )
        print("✓ Data visualization service imports successful")
    except ImportError as e:
        print(f"✗ Failed to import data visualization service: {e}")
        return False
    
    return True


def validate_enrichment_service_structure():
    """Validate external data enrichment service structure."""
    print("\nValidating external data enrichment service structure...")
    
    from services.external_data_enrichment_service import ExternalDataEnrichmentService
    
    # Check required methods
    required_methods = [
        'from_settings',
        'enrich_artist_data',
        'enrich_venue_data',
        'enrich_concert_data',
        'clear_cache',
        'get_cache_stats',
        'close'
    ]
    
    for method in required_methods:
        if not hasattr(ExternalDataEnrichmentService, method):
            print(f"✗ Missing method: {method}")
            return False
        print(f"✓ Method exists: {method}")
    
    return True


def validate_visualization_service_structure():
    """Validate data visualization service structure."""
    print("\nValidating data visualization service structure...")
    
    from services.data_visualization_service import DataVisualizationService
    
    # Check required methods
    required_methods = [
        'create_bar_chart',
        'create_line_chart',
        'create_scatter_plot',
        'create_pie_chart',
        'create_heatmap',
        'create_venue_popularity_chart',
        'create_ticket_sales_forecast_chart',
        'create_artist_popularity_trend_chart',
        'create_genre_distribution_chart',
        'create_revenue_vs_attendance_chart'
    ]
    
    for method in required_methods:
        if not hasattr(DataVisualizationService, method):
            print(f"✗ Missing method: {method}")
            return False
        print(f"✓ Method exists: {method}")
    
    return True


async def test_enrichment_service():
    """Test external data enrichment service functionality."""
    print("\nTesting external data enrichment service...")
    
    from services.external_data_enrichment_service import ExternalDataEnrichmentService
    
    try:
        # Initialize service
        service = ExternalDataEnrichmentService()
        print("✓ Service initialized successfully")
        
        # Test cache operations
        stats = service.get_cache_stats()
        print(f"✓ Cache stats retrieved: {stats['size']} entries")
        
        # Test fallback behavior (without API credentials)
        result = await service.enrich_artist_data(artist_name="Test Artist")
        print(f"✓ Artist enrichment completed: source={result.source}, success={result.success}")
        
        result = await service.enrich_venue_data(venue_name="Test Venue", city="Test City")
        print(f"✓ Venue enrichment completed: source={result.source}, success={result.success}")
        
        result = await service.enrich_concert_data(artist_name="Test Artist", city="Test City")
        print(f"✓ Concert enrichment completed: source={result.source}, success={result.success}")
        
        # Test cache
        service.clear_cache()
        stats_after = service.get_cache_stats()
        print(f"✓ Cache cleared: {stats_after['size']} entries")
        
        # Cleanup
        await service.close()
        print("✓ Service closed successfully")
        
        return True
    
    except Exception as e:
        print(f"✗ Error testing enrichment service: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visualization_service():
    """Test data visualization service functionality."""
    print("\nTesting data visualization service...")
    
    from services.data_visualization_service import DataVisualizationService
    
    try:
        # Initialize service
        service = DataVisualizationService()
        print("✓ Service initialized successfully")
        
        # Test bar chart
        data = {"A": 10, "B": 20, "C": 15}
        result = service.create_bar_chart(
            data=data,
            title="Test Bar Chart",
            xlabel="Category",
            ylabel="Value"
        )
        print(f"✓ Bar chart created: success={result.success}")
        if result.success:
            print(f"  Image size: {len(result.image_base64)} characters")
        
        # Test line chart
        line_data = {"Series 1": [1, 2, 3, 4], "Series 2": [2, 3, 4, 5]}
        result = service.create_line_chart(
            data=line_data,
            title="Test Line Chart",
            xlabel="X",
            ylabel="Y"
        )
        print(f"✓ Line chart created: success={result.success}")
        
        # Test scatter plot
        result = service.create_scatter_plot(
            x_values=[1, 2, 3, 4],
            y_values=[2, 4, 6, 8],
            title="Test Scatter Plot",
            xlabel="X",
            ylabel="Y"
        )
        print(f"✓ Scatter plot created: success={result.success}")
        
        # Test pie chart
        pie_data = {"Category A": 30, "Category B": 40, "Category C": 30}
        result = service.create_pie_chart(
            data=pie_data,
            title="Test Pie Chart"
        )
        print(f"✓ Pie chart created: success={result.success}")
        
        # Test template methods
        venues = [
            {"name": "Venue 1", "popularity_rank": 1, "avg_attendance_rate": 0.9},
            {"name": "Venue 2", "popularity_rank": 2, "avg_attendance_rate": 0.8}
        ]
        result = service.create_venue_popularity_chart(venues)
        print(f"✓ Venue popularity chart created: success={result.success}")
        
        predictions = [
            {"concert_name": "Concert 1", "predicted_sales": 1000},
            {"concert_name": "Concert 2", "predicted_sales": 1500}
        ]
        result = service.create_ticket_sales_forecast_chart(predictions)
        print(f"✓ Ticket sales forecast chart created: success={result.success}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error testing visualization service: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("External Data & Visualization Services Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Validate imports
    if not validate_imports():
        print("\n✗ Import validation failed")
        return False
    
    # Validate service structures
    if not validate_enrichment_service_structure():
        print("\n✗ Enrichment service structure validation failed")
        all_passed = False
    
    if not validate_visualization_service_structure():
        print("\n✗ Visualization service structure validation failed")
        all_passed = False
    
    # Test enrichment service
    if not await test_enrichment_service():
        print("\n✗ Enrichment service tests failed")
        all_passed = False
    
    # Test visualization service
    if not test_visualization_service():
        print("\n✗ Visualization service tests failed")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All validation tests passed!")
    else:
        print("✗ Some validation tests failed")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
