# Data Analysis Service

## Overview

The Data Analysis Service provides dynamic analytical capabilities for the Concert AI Chatbot, enabling:
- Trend analysis over time
- Entity comparisons (artists, venues)
- Statistical summaries
- ML model predictions
- Recommendation analysis
- Visualization data preparation

## Quick Start

```python
from src.services.data_analysis_service import DataAnalysisService
from src.services.redshift_service import RedshiftService

# Initialize with dependencies
redshift_service = RedshiftService()
analysis_service = DataAnalysisService(redshift_service=redshift_service)

# Analyze trends
result = analysis_service.analyze_concert_trends(
    time_period="last_year",
    metric="attendance",
    group_by="month"
)

# Format for chatbot
response = analysis_service.format_for_chatbot(result)
print(response)

# Prepare visualization
viz_data = analysis_service.prepare_visualization_data(result)
```

## Analysis Types

### 1. Trend Analysis

Analyze how metrics change over time:

```python
result = analysis_service.analyze_concert_trends(
    time_period="last_year",  # last_week, last_month, last_quarter, last_year
    metric="attendance",       # attendance, revenue, ticket_sales
    group_by="month"          # month, genre, or None
)
```

**Returns:**
- Title and summary
- List of insights
- Visualization data (line or bar chart)
- Raw data for further processing

### 2. Entity Comparison

Compare multiple artists or venues:

```python
result = analysis_service.compare_entities(
    entity_type="artist",  # artist or venue
    entity_ids=["artist_001", "artist_002", "artist_003"],
    metrics=["total_concerts", "avg_attendance", "total_revenue"]
)
```

**Returns:**
- Comparison insights (top performers)
- Visualization data (bar chart)
- Detailed comparison data

### 3. Statistical Summary

Generate statistical overviews:

```python
result = analysis_service.generate_statistical_summary(
    entity_type="concert"  # concert, artist, or venue
)
```

**Returns:**
- Key statistics (mean, stddev, min, max, percentiles)
- Statistical insights
- Visualization data (table)

### 4. ML Predictions

Integrate with ML models:

```python
# Venue popularity prediction
result = analysis_service.predict_with_ml_models(
    prediction_type="venue_popularity",
    input_data={
        "venue_id": "venue_001",
        "endpoint_name": "venue-popularity-endpoint"
    }
)

# Ticket sales prediction
result = analysis_service.predict_with_ml_models(
    prediction_type="ticket_sales",
    input_data={
        "concert_id": "concert_123",
        "artist_id": "artist_001",
        "venue_id": "venue_001",
        "event_date": datetime.now() + timedelta(days=60),
        "ticket_prices": {"general": 50.0, "vip": 150.0},
        "endpoint_name": "ticket-sales-endpoint"
    }
)
```

**Returns:**
- Prediction value
- Confidence score
- Low confidence flag (if applicable)
- Visualization data

### 5. Recommendation Analysis

Generate recommendations with analysis:

```python
result = analysis_service.generate_recommendations_analysis(
    user_id="user_123",
    recommendation_type="concert",  # concert, artist, or venue
    top_k=10,
    user_preferences={
        "preferred_artist_ids": ["artist_001", "artist_002"],
        "preferred_venue_ids": ["venue_001"]
    }
)
```

**Returns:**
- List of recommendations with scores
- Reasoning for each recommendation
- Visualization data (bar chart)

## Chatbot Integration

The service is automatically integrated with the chatbot:

```python
from src.services.chatbot_service import ConcertChatbotService

chatbot = ConcertChatbotService(
    redshift_service=redshift_service,
    venue_popularity_service=venue_service,
    ticket_sales_service=sales_service,
    recommendation_service=rec_service
)

# User queries are automatically routed to data analysis
response = chatbot.process_message(
    "Show me concert trends this year",
    session_id=session_id
)
```

**Supported Query Patterns:**
- Trends: "show trends", "analyze over time", "growth in attendance"
- Comparisons: "compare artists", "venue vs venue", "difference between"
- Statistics: "show statistics", "give me stats", "summary of concerts"

## Visualization Data Format

All analysis results include visualization data in a standardized format:

```python
{
    "chart_type": "line",  # line, bar, pie, scatter, heatmap, table
    "data": {
        "labels": ["Jan", "Feb", "Mar"],
        "datasets": [
            {
                "label": "Total Concerts",
                "values": [45, 52, 48]
            }
        ]
    },
    "title": "Concert Trends - Last Year"
}
```

This format can be directly consumed by charting libraries like Recharts, Chart.js, or D3.js.

## Result Structure

All analysis methods return an `AnalysisResult` object:

```python
class AnalysisResult:
    analysis_type: AnalysisType      # Type of analysis performed
    title: str                        # Human-readable title
    summary: str                      # Brief summary
    insights: List[str]               # Key insights as bullet points
    data: Dict[str, Any]             # Raw data and results
    visualization: Dict[str, Any]     # Visualization configuration
    metadata: Dict[str, Any]         # Additional metadata
    timestamp: datetime               # When analysis was performed
```

## Error Handling

The service handles errors gracefully:

```python
# Missing service
result = analysis_service.analyze_concert_trends(...)
if "error" in result.data:
    print(f"Error: {result.data['error']}")

# Invalid input
result = analysis_service.compare_entities(
    entity_type="invalid_type",
    entity_ids=["id1"]
)
# Returns error result with helpful message
```

## Helper Methods

### Format for Chatbot

Convert analysis results to chatbot-friendly text:

```python
formatted_text = analysis_service.format_for_chatbot(result)
# Returns markdown-formatted string with title, summary, and insights
```

### Prepare Visualization

Prepare visualization data with optional chart type override:

```python
from src.services.data_analysis_service import ChartType

viz_data = analysis_service.prepare_visualization_data(
    analysis_result=result,
    chart_type=ChartType.BAR  # Optional override
)
```

## Examples

See `src/services/example_data_analysis_usage.py` for comprehensive examples of:
- Trend analysis
- Comparison analysis
- Statistical summaries
- ML predictions
- Recommendation analysis
- Visualization preparation
- Chatbot integration workflow

## Testing

Run the integration tests:

```bash
python src/services/test_data_analysis_integration.py
```

Run the validation script:

```bash
python validate_data_analysis_service.py
```

## Dependencies

- `src.services.redshift_service` - For data queries
- `src.services.venue_popularity_service` - For venue predictions
- `src.services.ticket_sales_prediction_service` - For sales predictions
- `src.services.recommendation_service` - For recommendations

All dependencies are optional - the service will gracefully handle missing services.

## Best Practices

1. **Initialize with services**: Provide as many service dependencies as possible for full functionality
2. **Check for errors**: Always check `result.data` for error keys
3. **Use insights**: The `insights` list provides human-readable takeaways
4. **Leverage visualization**: Use the `visualization` data for UI rendering
5. **Format for users**: Use `format_for_chatbot()` for user-facing text

## Future Enhancements

Potential improvements:
- Advanced entity extraction for comparison queries
- Caching for frequently requested analyses
- More sophisticated trend detection algorithms
- Additional chart types and visualization options
- Real-time streaming analysis
- Anomaly detection in trends
- Predictive forecasting beyond ML models
