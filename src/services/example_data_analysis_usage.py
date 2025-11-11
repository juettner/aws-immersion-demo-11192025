"""
Example usage of Data Analysis Service for Concert AI Chatbot.

This script demonstrates how to use the DataAnalysisService to:
- Analyze concert trends over time
- Compare artists and venues
- Generate statistical summaries
- Integrate with ML models for predictions
- Prepare visualization data
"""
from datetime import datetime, timedelta
from src.services.data_analysis_service import (
    DataAnalysisService,
    AnalysisType,
    ChartType
)
from src.services.redshift_service import RedshiftService
from src.services.venue_popularity_service import VenuePopularityService
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.services.recommendation_service import RecommendationService


def example_trend_analysis():
    """Example: Analyze concert trends over time."""
    print("=" * 80)
    print("Example 1: Concert Trend Analysis")
    print("=" * 80)
    
    # Initialize services (in production, these would be properly configured)
    redshift_service = RedshiftService()
    analysis_service = DataAnalysisService(redshift_service=redshift_service)
    
    # Analyze attendance trends by month
    result = analysis_service.analyze_concert_trends(
        time_period="last_year",
        metric="attendance",
        group_by="month"
    )
    
    print(f"\nTitle: {result.title}")
    print(f"Summary: {result.summary}")
    print("\nInsights:")
    for insight in result.insights:
        print(f"  • {insight}")
    
    print(f"\nVisualization: {result.visualization.get('chart_type', 'N/A')}")
    print(f"Data points: {result.metadata.get('record_count', 0)}")
    
    # Format for chatbot
    chatbot_response = analysis_service.format_for_chatbot(result)
    print("\nChatbot Response:")
    print(chatbot_response)


def example_comparison_analysis():
    """Example: Compare multiple artists."""
    print("\n" + "=" * 80)
    print("Example 2: Artist Comparison")
    print("=" * 80)
    
    redshift_service = RedshiftService()
    analysis_service = DataAnalysisService(redshift_service=redshift_service)
    
    # Compare three artists
    artist_ids = ["artist_001", "artist_002", "artist_003"]
    
    result = analysis_service.compare_entities(
        entity_type="artist",
        entity_ids=artist_ids,
        metrics=["total_concerts", "avg_attendance", "total_revenue"]
    )
    
    print(f"\nTitle: {result.title}")
    print(f"Summary: {result.summary}")
    print("\nInsights:")
    for insight in result.insights:
        print(f"  • {insight}")
    
    print(f"\nVisualization: {result.visualization.get('chart_type', 'N/A')}")


def example_statistical_summary():
    """Example: Generate statistical summary."""
    print("\n" + "=" * 80)
    print("Example 3: Statistical Summary")
    print("=" * 80)
    
    redshift_service = RedshiftService()
    analysis_service = DataAnalysisService(redshift_service=redshift_service)
    
    # Get concert statistics
    result = analysis_service.generate_statistical_summary(
        entity_type="concert"
    )
    
    print(f"\nTitle: {result.title}")
    print(f"Summary: {result.summary}")
    print("\nInsights:")
    for insight in result.insights:
        print(f"  • {insight}")
    
    if result.data.get("statistics"):
        print("\nDetailed Statistics:")
        for key, value in result.data["statistics"].items():
            print(f"  {key}: {value}")


def example_ml_prediction():
    """Example: Generate ML predictions."""
    print("\n" + "=" * 80)
    print("Example 4: ML Prediction Integration")
    print("=" * 80)
    
    # Initialize services
    redshift_service = RedshiftService()
    ticket_sales_service = TicketSalesPredictionService(
        redshift_client=redshift_service
    )
    
    analysis_service = DataAnalysisService(
        redshift_service=redshift_service,
        ticket_sales_service=ticket_sales_service
    )
    
    # Predict ticket sales for a concert
    input_data = {
        "concert_id": "concert_123",
        "artist_id": "artist_001",
        "venue_id": "venue_001",
        "event_date": datetime.now() + timedelta(days=60),
        "ticket_prices": {"general": 50.0, "vip": 150.0},
        "endpoint_name": "ticket-sales-endpoint"
    }
    
    result = analysis_service.predict_with_ml_models(
        prediction_type="ticket_sales",
        input_data=input_data
    )
    
    print(f"\nTitle: {result.title}")
    print(f"Summary: {result.summary}")
    print("\nInsights:")
    for insight in result.insights:
        print(f"  • {insight}")
    
    print(f"\nPrediction Data:")
    for key, value in result.data.items():
        print(f"  {key}: {value}")


def example_recommendation_analysis():
    """Example: Generate recommendations with analysis."""
    print("\n" + "=" * 80)
    print("Example 5: Recommendation Analysis")
    print("=" * 80)
    
    recommendation_service = RecommendationService()
    analysis_service = DataAnalysisService(
        recommendation_service=recommendation_service
    )
    
    # Generate concert recommendations
    user_preferences = {
        "preferred_artist_ids": ["artist_001", "artist_002"],
        "preferred_venue_ids": ["venue_001"],
        "exclude_concert_ids": set()
    }
    
    result = analysis_service.generate_recommendations_analysis(
        user_id="user_123",
        recommendation_type="concert",
        top_k=10,
        user_preferences=user_preferences
    )
    
    print(f"\nTitle: {result.title}")
    print(f"Summary: {result.summary}")
    print("\nInsights:")
    for insight in result.insights:
        print(f"  • {insight}")
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(result.data.get("recommendations", [])[:5], 1):
        print(f"  {i}. {rec['item_id']} (score: {rec['score']:.3f})")


def example_visualization_preparation():
    """Example: Prepare visualization data."""
    print("\n" + "=" * 80)
    print("Example 6: Visualization Data Preparation")
    print("=" * 80)
    
    redshift_service = RedshiftService()
    analysis_service = DataAnalysisService(redshift_service=redshift_service)
    
    # Analyze trends
    result = analysis_service.analyze_concert_trends(
        time_period="last_quarter",
        metric="revenue",
        group_by="month"
    )
    
    # Prepare visualization data
    viz_data = analysis_service.prepare_visualization_data(
        analysis_result=result,
        chart_type=ChartType.LINE
    )
    
    print(f"\nVisualization Configuration:")
    print(f"  Chart Type: {viz_data.get('chart_type')}")
    print(f"  Title: {viz_data.get('title', result.title)}")
    
    if "data" in viz_data:
        data = viz_data["data"]
        if "labels" in data:
            print(f"  Labels: {len(data['labels'])} data points")
        if "datasets" in data:
            print(f"  Datasets: {len(data['datasets'])} series")


def example_chatbot_integration():
    """Example: Full chatbot integration workflow."""
    print("\n" + "=" * 80)
    print("Example 7: Chatbot Integration Workflow")
    print("=" * 80)
    
    redshift_service = RedshiftService()
    analysis_service = DataAnalysisService(redshift_service=redshift_service)
    
    # Simulate chatbot query: "Show me concert trends this year"
    print("\nUser Query: 'Show me concert trends this year'")
    
    # Perform analysis
    result = analysis_service.analyze_concert_trends(
        time_period="last_year",
        metric="attendance",
        group_by="month"
    )
    
    # Format for chatbot
    chatbot_response = analysis_service.format_for_chatbot(result)
    
    # Prepare visualization
    viz_data = analysis_service.prepare_visualization_data(result)
    
    print("\nChatbot Response:")
    print(chatbot_response)
    
    print("\nVisualization Ready:")
    print(f"  Type: {viz_data.get('chart_type')}")
    print(f"  Can be rendered in UI: Yes")


if __name__ == "__main__":
    print("Data Analysis Service - Example Usage")
    print("=" * 80)
    print("\nNote: These examples require configured AWS services and data.")
    print("Some examples may fail if services are not available.\n")
    
    try:
        example_trend_analysis()
    except Exception as e:
        print(f"Trend analysis example failed: {e}")
    
    try:
        example_comparison_analysis()
    except Exception as e:
        print(f"Comparison analysis example failed: {e}")
    
    try:
        example_statistical_summary()
    except Exception as e:
        print(f"Statistical summary example failed: {e}")
    
    try:
        example_ml_prediction()
    except Exception as e:
        print(f"ML prediction example failed: {e}")
    
    try:
        example_recommendation_analysis()
    except Exception as e:
        print(f"Recommendation analysis example failed: {e}")
    
    try:
        example_visualization_preparation()
    except Exception as e:
        print(f"Visualization preparation example failed: {e}")
    
    try:
        example_chatbot_integration()
    except Exception as e:
        print(f"Chatbot integration example failed: {e}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
