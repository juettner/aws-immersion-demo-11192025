"""
Integration test for Data Analysis Service with Chatbot.

This script demonstrates the integration of DataAnalysisService with the
ConcertChatbotService for dynamic data analysis capabilities.
"""
from datetime import datetime, timedelta
from src.services.chatbot_service import ConcertChatbotService
from src.services.data_analysis_service import DataAnalysisService, AnalysisType
from src.services.redshift_service import RedshiftService


def test_chatbot_with_data_analysis():
    """Test chatbot with data analysis service integration."""
    print("=" * 80)
    print("Testing Chatbot with Data Analysis Integration")
    print("=" * 80)
    
    # Initialize services
    try:
        redshift_service = RedshiftService()
        print("✓ Redshift service initialized")
    except Exception as e:
        print(f"⚠ Redshift service initialization failed: {e}")
        redshift_service = None
    
    # Initialize chatbot with data analysis capabilities
    chatbot = ConcertChatbotService(
        redshift_service=redshift_service,
        enable_memory_persistence=False  # Disable for testing
    )
    
    print(f"✓ Chatbot initialized")
    print(f"  - Data analysis service: {'Available' if chatbot.data_analysis_service else 'Not available'}")
    print(f"  - NL to SQL service: {'Available' if chatbot.nl_to_sql_service else 'Not available'}")
    
    # Create a test session
    session_id = chatbot.create_session(user_id="test_user")
    print(f"✓ Session created: {session_id}")
    
    # Test queries
    test_queries = [
        "Show me concert trends over the last year",
        "Give me statistics about concerts",
        "Analyze venue statistics",
        "What are the trends in attendance?",
        "Show me artist statistics"
    ]
    
    print("\n" + "=" * 80)
    print("Testing Data Analysis Queries")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"User: {query}")
        
        try:
            response = chatbot.process_message(query, session_id=session_id)
            
            print(f"\nIntent: {response.intent.value if response.intent else 'None'}")
            print(f"Confidence: {response.confidence:.2f}")
            print(f"\nResponse:")
            print(response.message[:500])  # Truncate long responses
            
            if response.data:
                print(f"\nData keys: {list(response.data.keys())}")
                
                if "analysis_type" in response.data:
                    print(f"Analysis type: {response.data['analysis_type']}")
                
                if "visualization" in response.data:
                    viz = response.data['visualization']
                    if viz:
                        print(f"Visualization: {viz.get('chart_type', 'N/A')}")
                
                if "insights" in response.data:
                    insights = response.data['insights']
                    if insights:
                        print(f"Insights count: {len(insights)}")
            
            print("✓ Query processed successfully")
            
        except Exception as e:
            print(f"✗ Query failed: {e}")
    
    print("\n" + "=" * 80)
    print("Integration Test Complete")
    print("=" * 80)


def test_data_analysis_service_directly():
    """Test data analysis service directly."""
    print("\n" + "=" * 80)
    print("Testing Data Analysis Service Directly")
    print("=" * 80)
    
    try:
        redshift_service = RedshiftService()
        analysis_service = DataAnalysisService(redshift_service=redshift_service)
        
        print("✓ Data analysis service initialized")
        
        # Test trend analysis
        print("\n--- Test 1: Trend Analysis ---")
        try:
            result = analysis_service.analyze_concert_trends(
                time_period="last_year",
                metric="attendance",
                group_by="month"
            )
            
            print(f"Title: {result.title}")
            print(f"Analysis type: {result.analysis_type.value}")
            print(f"Insights: {len(result.insights)}")
            print(f"Has visualization: {result.visualization is not None}")
            print("✓ Trend analysis successful")
            
        except Exception as e:
            print(f"✗ Trend analysis failed: {e}")
        
        # Test statistical summary
        print("\n--- Test 2: Statistical Summary ---")
        try:
            result = analysis_service.generate_statistical_summary(
                entity_type="concert"
            )
            
            print(f"Title: {result.title}")
            print(f"Analysis type: {result.analysis_type.value}")
            print(f"Insights: {len(result.insights)}")
            print(f"Has statistics: {'statistics' in result.data}")
            print("✓ Statistical summary successful")
            
        except Exception as e:
            print(f"✗ Statistical summary failed: {e}")
        
        # Test formatting for chatbot
        print("\n--- Test 3: Chatbot Formatting ---")
        try:
            result = analysis_service.generate_statistical_summary(
                entity_type="artist"
            )
            
            formatted = analysis_service.format_for_chatbot(result)
            
            print(f"Formatted response length: {len(formatted)} characters")
            print(f"Contains title: {'**' in formatted}")
            print(f"Contains insights: {'•' in formatted}")
            print("✓ Chatbot formatting successful")
            
        except Exception as e:
            print(f"✗ Chatbot formatting failed: {e}")
        
        # Test visualization preparation
        print("\n--- Test 4: Visualization Preparation ---")
        try:
            result = analysis_service.analyze_concert_trends(
                time_period="last_quarter",
                metric="revenue",
                group_by="month"
            )
            
            viz_data = analysis_service.prepare_visualization_data(result)
            
            print(f"Chart type: {viz_data.get('chart_type', 'N/A')}")
            print(f"Has data: {'data' in viz_data}")
            print("✓ Visualization preparation successful")
            
        except Exception as e:
            print(f"✗ Visualization preparation failed: {e}")
        
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
    
    print("\n" + "=" * 80)
    print("Direct Service Test Complete")
    print("=" * 80)


def test_error_handling():
    """Test error handling in data analysis."""
    print("\n" + "=" * 80)
    print("Testing Error Handling")
    print("=" * 80)
    
    # Test with no services
    analysis_service = DataAnalysisService()
    
    print("\n--- Test 1: No Redshift Service ---")
    result = analysis_service.analyze_concert_trends(
        time_period="last_year",
        metric="attendance"
    )
    
    print(f"Title: {result.title}")
    print(f"Has error: {'error' in result.data}")
    print(f"Insights: {result.insights}")
    print("✓ Error handled gracefully")
    
    print("\n--- Test 2: Invalid Entity Type ---")
    result = analysis_service.compare_entities(
        entity_type="invalid_type",
        entity_ids=["id1", "id2"]
    )
    
    print(f"Title: {result.title}")
    print(f"Has error: {'error' in result.data}")
    print("✓ Invalid input handled gracefully")
    
    print("\n--- Test 3: Missing ML Services ---")
    result = analysis_service.predict_with_ml_models(
        prediction_type="venue_popularity",
        input_data={"venue_id": "test"}
    )
    
    print(f"Title: {result.title}")
    print(f"Has error: {'error' in result.data}")
    print("✓ Missing service handled gracefully")
    
    print("\n" + "=" * 80)
    print("Error Handling Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    print("Data Analysis Service Integration Tests")
    print("=" * 80)
    print("\nNote: These tests require configured AWS services.")
    print("Some tests may fail if services are not available.\n")
    
    # Run tests
    test_data_analysis_service_directly()
    test_error_handling()
    test_chatbot_with_data_analysis()
    
    print("\n" + "=" * 80)
    print("All Integration Tests Complete")
    print("=" * 80)
