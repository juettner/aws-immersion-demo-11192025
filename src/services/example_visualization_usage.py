"""
Example usage of Data Visualization Service.
"""
from data_visualization_service import DataVisualizationService


def main():
    """Demonstrate data visualization capabilities."""
    print("=== Data Visualization Service Demo ===\n")
    
    # Initialize service
    service = DataVisualizationService()
    
    # Example 1: Bar chart for venue popularity
    print("1. Creating venue popularity bar chart...")
    venues = [
        {"name": "Madison Square Garden", "popularity_rank": 1, "avg_attendance_rate": 0.95},
        {"name": "Staples Center", "popularity_rank": 2, "avg_attendance_rate": 0.92},
        {"name": "Red Rocks", "popularity_rank": 3, "avg_attendance_rate": 0.88},
        {"name": "Hollywood Bowl", "popularity_rank": 4, "avg_attendance_rate": 0.85},
        {"name": "Fenway Park", "popularity_rank": 5, "avg_attendance_rate": 0.82}
    ]
    result = service.create_venue_popularity_chart(venues, top_n=5)
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    if result.success:
        print(f"   Image size: {len(result.image_base64)} characters (base64)")
        print(f"   Metadata: {result.metadata}")
    print()
    
    # Example 2: Line chart for artist popularity trends
    print("2. Creating artist popularity trend line chart...")
    artist_trends = {
        "Taylor Swift": [85, 87, 90, 92, 95],
        "Ed Sheeran": [78, 80, 82, 84, 86],
        "Metallica": [70, 72, 71, 73, 75]
    }
    result = service.create_artist_popularity_trend_chart(artist_trends)
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    if result.success:
        print(f"   Series count: {result.metadata.get('series_count')}")
    print()
    
    # Example 3: Scatter plot for revenue vs attendance
    print("3. Creating revenue vs attendance scatter plot...")
    concerts = [
        {"name": "Concert A", "total_attendance": 15000, "revenue": 750000},
        {"name": "Concert B", "total_attendance": 20000, "revenue": 1200000},
        {"name": "Concert C", "total_attendance": 8000, "revenue": 400000},
        {"name": "Concert D", "total_attendance": 12000, "revenue": 600000},
        {"name": "Concert E", "total_attendance": 18000, "revenue": 950000}
    ]
    result = service.create_revenue_vs_attendance_chart(concerts)
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    if result.success:
        print(f"   Data points: {result.metadata.get('data_points')}")
    print()
    
    # Example 4: Pie chart for genre distribution
    print("4. Creating genre distribution pie chart...")
    genre_counts = {
        "Rock": 45,
        "Pop": 30,
        "Hip-Hop": 15,
        "Country": 10
    }
    result = service.create_genre_distribution_chart(genre_counts)
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    if result.success:
        print(f"   Categories: {result.metadata.get('categories')}")
    print()
    
    # Example 5: Ticket sales forecast
    print("5. Creating ticket sales forecast chart...")
    predictions = [
        {"concert_name": "Taylor Swift - LA", "predicted_sales": 18500},
        {"concert_name": "Metallica - NYC", "predicted_sales": 15200},
        {"concert_name": "Ed Sheeran - Chicago", "predicted_sales": 12800},
        {"concert_name": "Beyoncé - Miami", "predicted_sales": 19000}
    ]
    result = service.create_ticket_sales_forecast_chart(predictions)
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    if result.success:
        print(f"   Data points: {result.metadata.get('data_points')}")
    print()
    
    # Example 6: Custom bar chart
    print("6. Creating custom bar chart...")
    custom_data = {
        "Jan": 120,
        "Feb": 135,
        "Mar": 150,
        "Apr": 145,
        "May": 160
    }
    result = service.create_bar_chart(
        data=custom_data,
        title="Monthly Concert Bookings",
        xlabel="Month",
        ylabel="Number of Concerts",
        color="#ff7f0e"
    )
    print(f"   Success: {result.success}")
    print(f"   Chart type: {result.chart_type}")
    print()
    
    # Example 7: Heatmap (if numpy available)
    print("7. Creating heatmap...")
    try:
        heatmap_data = [
            [10, 20, 30, 40],
            [15, 25, 35, 45],
            [20, 30, 40, 50],
            [25, 35, 45, 55]
        ]
        row_labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
        col_labels = ["Mon", "Tue", "Wed", "Thu"]
        
        result = service.create_heatmap(
            data=heatmap_data,
            title="Concert Attendance Heatmap",
            row_labels=row_labels,
            col_labels=col_labels
        )
        print(f"   Success: {result.success}")
        print(f"   Chart type: {result.chart_type}")
        if result.success:
            print(f"   Dimensions: {result.metadata.get('rows')}x{result.metadata.get('cols')}")
    except ImportError as e:
        print(f"   Skipped (numpy not available): {e}")
    print()
    
    print("All visualization examples completed!")
    print("\nNote: Images are encoded as base64 strings and can be embedded in chatbot responses.")
    print("Example usage in chatbot: <img src='data:image/png;base64,{image_base64}' />")


if __name__ == "__main__":
    main()
