"""
Data Analysis Service for Concert AI Chatbot.

This service provides dynamic data analysis capabilities including:
- Analytical insights generation from concert data
- Result parsing and formatting for chatbot responses
- Integration with ML models for predictions
- Visualization data preparation for chart generation
"""
import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np

from src.services.redshift_service import RedshiftService
from src.services.venue_popularity_service import VenuePopularityService
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.services.recommendation_service import RecommendationService


class AnalysisType(str, Enum):
    """Types of data analysis."""
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"
    STATISTICAL_SUMMARY = "statistical_summary"


class ChartType(str, Enum):
    """Types of charts for visualization."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    TABLE = "table"


class AnalysisResult(BaseModel):
    """Result from data analysis."""
    analysis_type: AnalysisType
    title: str
    summary: str
    insights: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    visualization: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DataAnalysisService:
    """
    Data Analysis Service for generating insights and visualizations.
    
    Provides:
    - Trend analysis for concert data
    - Comparative analysis across artists, venues, and time periods
    - Statistical summaries and aggregations
    - Integration with ML prediction models
    - Visualization data preparation
    """
    
    def __init__(
        self,
        redshift_service: Optional[RedshiftService] = None,
        venue_popularity_service: Optional[VenuePopularityService] = None,
        ticket_sales_service: Optional[TicketSalesPredictionService] = None,
        recommendation_service: Optional[RecommendationService] = None
    ):
        """
        Initialize data analysis service.
        
        Args:
            redshift_service: Service for querying data warehouse
            venue_popularity_service: Service for venue popularity predictions
            ticket_sales_service: Service for ticket sales predictions
            recommendation_service: Service for recommendations
        """
        self.redshift_service = redshift_service
        self.venue_popularity_service = venue_popularity_service
        self.ticket_sales_service = ticket_sales_service
        self.recommendation_service = recommendation_service
    
    def analyze_concert_trends(
        self,
        time_period: str = "last_year",
        metric: str = "attendance",
        group_by: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze trends in concert data over time.
        
        Args:
            time_period: Time period for analysis (last_month, last_quarter, last_year)
            metric: Metric to analyze (attendance, revenue, ticket_sales)
            group_by: Optional grouping (artist, venue, genre, month)
            
        Returns:
            Analysis result with trend data and insights
        """
        # Determine date range
        days_back = self._get_days_from_period(time_period)
        
        # Build query based on metric and grouping
        if group_by == "month":
            query = f"""
            SELECT 
                DATE_TRUNC('month', event_date) as period,
                COUNT(DISTINCT concert_id) as total_concerts,
                AVG(total_attendance) as avg_attendance,
                SUM(revenue) as total_revenue,
                SUM(total_attendance) as total_attendance
            FROM concert_dw.concerts
            WHERE event_date >= DATEADD(day, -{days_back}, CURRENT_DATE)
                AND status = 'completed'
            GROUP BY DATE_TRUNC('month', event_date)
            ORDER BY period
            """
        elif group_by == "genre":
            query = f"""
            SELECT 
                a.genre,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.total_attendance) as avg_attendance,
                SUM(c.revenue) as total_revenue
            FROM concert_dw.concerts c
            JOIN concert_dw.artists a ON c.artist_id = a.artist_id
            WHERE c.event_date >= DATEADD(day, -{days_back}, CURRENT_DATE)
                AND c.status = 'completed'
            GROUP BY a.genre
            ORDER BY total_concerts DESC
            LIMIT 10
            """
        else:
            query = f"""
            SELECT 
                event_date,
                total_attendance,
                revenue
            FROM concert_dw.concerts
            WHERE event_date >= DATEADD(day, -{days_back}, CURRENT_DATE)
                AND status = 'completed'
            ORDER BY event_date
            """
        
        if not self.redshift_service:
            return self._create_error_result("Redshift service not available")
        
        try:
            data = self.redshift_service.execute_custom_query(query)
            
            if not data:
                return self._create_empty_result("No data found for the specified period")
            
            # Generate insights
            insights = self._generate_trend_insights(data, metric, group_by)
            
            # Prepare visualization data
            viz_data = self._prepare_trend_visualization(data, metric, group_by)
            
            return AnalysisResult(
                analysis_type=AnalysisType.TREND_ANALYSIS,
                title=f"{metric.title()} Trends - {time_period.replace('_', ' ').title()}",
                summary=f"Analysis of {metric} trends over {time_period.replace('_', ' ')}",
                insights=insights,
                data={"raw_data": data, "metric": metric, "period": time_period},
                visualization=viz_data,
                metadata={"group_by": group_by, "record_count": len(data)}
            )
            
        except Exception as e:
            return self._create_error_result(f"Trend analysis failed: {str(e)}")
    
    def compare_entities(
        self,
        entity_type: str,
        entity_ids: List[str],
        metrics: List[str] = None
    ) -> AnalysisResult:
        """
        Compare multiple entities (artists, venues) across various metrics.
        
        Args:
            entity_type: Type of entity (artist, venue)
            entity_ids: List of entity IDs to compare
            metrics: List of metrics to compare (attendance, revenue, popularity)
            
        Returns:
            Analysis result with comparison data
        """
        if metrics is None:
            metrics = ["total_concerts", "avg_attendance", "total_revenue"]
        
        if entity_type == "artist":
            query = f"""
            SELECT 
                a.artist_id,
                a.name,
                a.popularity_score,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.total_attendance) as avg_attendance,
                SUM(c.revenue) as total_revenue,
                MAX(c.total_attendance) as max_attendance
            FROM concert_dw.artists a
            LEFT JOIN concert_dw.concerts c ON a.artist_id = c.artist_id
            WHERE a.artist_id IN ({','.join(f"'{id}'" for id in entity_ids)})
                AND c.status = 'completed'
            GROUP BY a.artist_id, a.name, a.popularity_score
            """
        elif entity_type == "venue":
            query = f"""
            SELECT 
                v.venue_id,
                v.name,
                v.capacity,
                v.venue_type,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.total_attendance) as avg_attendance,
                SUM(c.revenue) as total_revenue,
                AVG(c.total_attendance::float / v.capacity) as avg_attendance_rate
            FROM concert_dw.venues v
            LEFT JOIN concert_dw.concerts c ON v.venue_id = c.venue_id
            WHERE v.venue_id IN ({','.join(f"'{id}'" for id in entity_ids)})
                AND c.status = 'completed'
            GROUP BY v.venue_id, v.name, v.capacity, v.venue_type
            """
        else:
            return self._create_error_result(f"Unsupported entity type: {entity_type}")
        
        if not self.redshift_service:
            return self._create_error_result("Redshift service not available")
        
        try:
            data = self.redshift_service.execute_custom_query(query)
            
            if not data:
                return self._create_empty_result("No data found for comparison")
            
            # Generate comparison insights
            insights = self._generate_comparison_insights(data, entity_type, metrics)
            
            # Prepare visualization data
            viz_data = self._prepare_comparison_visualization(data, entity_type, metrics)
            
            return AnalysisResult(
                analysis_type=AnalysisType.COMPARISON,
                title=f"{entity_type.title()} Comparison",
                summary=f"Comparative analysis of {len(entity_ids)} {entity_type}s",
                insights=insights,
                data={"comparison_data": data, "entity_type": entity_type},
                visualization=viz_data,
                metadata={"entity_count": len(data), "metrics": metrics}
            )
            
        except Exception as e:
            return self._create_error_result(f"Comparison analysis failed: {str(e)}")
    
    def generate_statistical_summary(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Generate statistical summary for concert data.
        
        Args:
            entity_type: Type of entity (concert, artist, venue)
            filters: Optional filters to apply
            
        Returns:
            Analysis result with statistical summary
        """
        if entity_type == "concert":
            query = """
            SELECT 
                COUNT(DISTINCT concert_id) as total_concerts,
                COUNT(DISTINCT artist_id) as unique_artists,
                COUNT(DISTINCT venue_id) as unique_venues,
                AVG(total_attendance) as avg_attendance,
                STDDEV(total_attendance) as stddev_attendance,
                MIN(total_attendance) as min_attendance,
                MAX(total_attendance) as max_attendance,
                AVG(revenue) as avg_revenue,
                SUM(revenue) as total_revenue,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_attendance) as median_attendance
            FROM concert_dw.concerts
            WHERE status = 'completed'
            """
        elif entity_type == "artist":
            query = """
            SELECT 
                COUNT(DISTINCT artist_id) as total_artists,
                AVG(popularity_score) as avg_popularity,
                STDDEV(popularity_score) as stddev_popularity,
                MIN(popularity_score) as min_popularity,
                MAX(popularity_score) as max_popularity,
                COUNT(DISTINCT genre) as unique_genres
            FROM concert_dw.artists
            """
        elif entity_type == "venue":
            query = """
            SELECT 
                COUNT(DISTINCT venue_id) as total_venues,
                AVG(capacity) as avg_capacity,
                STDDEV(capacity) as stddev_capacity,
                MIN(capacity) as min_capacity,
                MAX(capacity) as max_capacity,
                COUNT(DISTINCT venue_type) as unique_types,
                COUNT(DISTINCT city) as unique_cities
            FROM concert_dw.venues
            """
        else:
            return self._create_error_result(f"Unsupported entity type: {entity_type}")
        
        if not self.redshift_service:
            return self._create_error_result("Redshift service not available")
        
        try:
            data = self.redshift_service.execute_custom_query(query)
            
            if not data or len(data) == 0:
                return self._create_empty_result("No data found for summary")
            
            stats = data[0]
            
            # Generate insights from statistics
            insights = self._generate_statistical_insights(stats, entity_type)
            
            # Prepare visualization data
            viz_data = self._prepare_summary_visualization(stats, entity_type)
            
            return AnalysisResult(
                analysis_type=AnalysisType.STATISTICAL_SUMMARY,
                title=f"{entity_type.title()} Statistical Summary",
                summary=f"Statistical overview of {entity_type} data",
                insights=insights,
                data={"statistics": stats},
                visualization=viz_data,
                metadata={"entity_type": entity_type}
            )
            
        except Exception as e:
            return self._create_error_result(f"Statistical summary failed: {str(e)}")
    
    def predict_with_ml_models(
        self,
        prediction_type: str,
        input_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Generate predictions using ML models.
        
        Args:
            prediction_type: Type of prediction (venue_popularity, ticket_sales)
            input_data: Input data for prediction
            
        Returns:
            Analysis result with prediction data
        """
        if prediction_type == "venue_popularity":
            if not self.venue_popularity_service:
                return self._create_error_result("Venue popularity service not available")
            
            try:
                venue_id = input_data.get("venue_id")
                endpoint_name = input_data.get("endpoint_name")
                
                if not venue_id or not endpoint_name:
                    return self._create_error_result("Missing required parameters: venue_id, endpoint_name")
                
                prediction = self.venue_popularity_service.predict_venue_popularity(
                    venue_id=venue_id,
                    endpoint_name=endpoint_name
                )
                
                insights = [
                    f"Predicted popularity score: {prediction['predicted_popularity_score']:.3f}",
                    f"Venue: {venue_id}",
                    f"Prediction generated at: {prediction['prediction_timestamp']}"
                ]
                
                viz_data = {
                    "chart_type": ChartType.BAR.value,
                    "data": {
                        "labels": ["Predicted Score"],
                        "values": [prediction['predicted_popularity_score']]
                    }
                }
                
                return AnalysisResult(
                    analysis_type=AnalysisType.PREDICTION,
                    title="Venue Popularity Prediction",
                    summary=f"ML-based popularity prediction for venue {venue_id}",
                    insights=insights,
                    data=prediction,
                    visualization=viz_data,
                    metadata={"prediction_type": prediction_type}
                )
                
            except Exception as e:
                return self._create_error_result(f"Venue popularity prediction failed: {str(e)}")
        
        elif prediction_type == "ticket_sales":
            if not self.ticket_sales_service:
                return self._create_error_result("Ticket sales service not available")
            
            try:
                required_fields = ["concert_id", "artist_id", "venue_id", "event_date", "endpoint_name"]
                missing = [f for f in required_fields if f not in input_data]
                
                if missing:
                    return self._create_error_result(f"Missing required parameters: {', '.join(missing)}")
                
                prediction = self.ticket_sales_service.predict_ticket_sales(
                    concert_id=input_data["concert_id"],
                    artist_id=input_data["artist_id"],
                    venue_id=input_data["venue_id"],
                    event_date=input_data["event_date"],
                    ticket_prices=input_data.get("ticket_prices", {}),
                    endpoint_name=input_data["endpoint_name"]
                )
                
                insights = [
                    f"Predicted ticket sales: ${prediction.predicted_sales:,.2f}",
                    f"Confidence score: {prediction.confidence_score:.2%}",
                    f"Low confidence: {'Yes' if prediction.low_confidence_flag else 'No'}",
                    f"Concert: {prediction.concert_id}"
                ]
                
                if prediction.low_confidence_flag:
                    insights.append("⚠️ This prediction has low confidence and should be used with caution")
                
                viz_data = {
                    "chart_type": ChartType.BAR.value,
                    "data": {
                        "labels": ["Predicted Sales", "Confidence"],
                        "values": [prediction.predicted_sales, prediction.confidence_score * 100]
                    }
                }
                
                return AnalysisResult(
                    analysis_type=AnalysisType.PREDICTION,
                    title="Ticket Sales Prediction",
                    summary=f"ML-based sales forecast for concert {prediction.concert_id}",
                    insights=insights,
                    data={
                        "prediction_id": prediction.prediction_id,
                        "predicted_sales": prediction.predicted_sales,
                        "confidence_score": prediction.confidence_score,
                        "low_confidence_flag": prediction.low_confidence_flag
                    },
                    visualization=viz_data,
                    metadata={"prediction_type": prediction_type}
                )
                
            except Exception as e:
                return self._create_error_result(f"Ticket sales prediction failed: {str(e)}")
        
        else:
            return self._create_error_result(f"Unsupported prediction type: {prediction_type}")
    
    def generate_recommendations_analysis(
        self,
        user_id: str,
        recommendation_type: str = "concert",
        top_k: int = 10,
        user_preferences: Optional[Dict] = None
    ) -> AnalysisResult:
        """
        Generate recommendations with analysis.
        
        Args:
            user_id: User identifier
            recommendation_type: Type of recommendation (concert, artist, venue)
            top_k: Number of recommendations
            user_preferences: Optional user preferences
            
        Returns:
            Analysis result with recommendations
        """
        if not self.recommendation_service:
            return self._create_error_result("Recommendation service not available")
        
        try:
            if recommendation_type == "concert":
                from src.services.recommendation_service import RecommendationStrategy
                
                result = self.recommendation_service.recommend_concerts(
                    user_id=user_id,
                    strategy=RecommendationStrategy.HYBRID_ALL,
                    top_k=top_k,
                    user_preferences=user_preferences or {}
                )
                
                insights = [
                    f"Generated {len(result.recommendations)} concert recommendations",
                    f"Algorithm: {result.algorithm}",
                    f"Total candidates evaluated: {result.total_candidates}"
                ]
                
                # Add top recommendations to insights
                for i, rec in enumerate(result.recommendations[:3], 1):
                    insights.append(f"{i}. {rec.item_id} (score: {rec.score:.3f})")
                
                viz_data = self._prepare_recommendation_visualization(result.recommendations)
                
                return AnalysisResult(
                    analysis_type=AnalysisType.RECOMMENDATION,
                    title="Concert Recommendations",
                    summary=f"Personalized concert recommendations for user {user_id}",
                    insights=insights,
                    data={
                        "recommendations": [
                            {
                                "item_id": r.item_id,
                                "score": r.score,
                                "confidence": r.confidence,
                                "reasoning": r.reasoning
                            }
                            for r in result.recommendations
                        ]
                    },
                    visualization=viz_data,
                    metadata={"user_id": user_id, "algorithm": result.algorithm}
                )
                
            elif recommendation_type == "artist":
                preferred_artists = user_preferences.get("preferred_artist_ids", []) if user_preferences else []
                
                if not preferred_artists:
                    return self._create_error_result("No preferred artists provided for recommendations")
                
                recommendations = self.recommendation_service.recommend_artists(
                    preferred_artist_ids=preferred_artists,
                    top_k=top_k
                )
                
                insights = [
                    f"Generated {len(recommendations)} artist recommendations",
                    f"Based on {len(preferred_artists)} preferred artists"
                ]
                
                for i, rec in enumerate(recommendations[:3], 1):
                    insights.append(f"{i}. {rec.item_id} (score: {rec.score:.3f})")
                
                viz_data = self._prepare_recommendation_visualization(recommendations)
                
                return AnalysisResult(
                    analysis_type=AnalysisType.RECOMMENDATION,
                    title="Artist Recommendations",
                    summary=f"Similar artists based on preferences",
                    insights=insights,
                    data={
                        "recommendations": [
                            {
                                "item_id": r.item_id,
                                "score": r.score,
                                "reasoning": r.reasoning
                            }
                            for r in recommendations
                        ]
                    },
                    visualization=viz_data,
                    metadata={"user_id": user_id}
                )
                
            else:
                return self._create_error_result(f"Unsupported recommendation type: {recommendation_type}")
                
        except Exception as e:
            return self._create_error_result(f"Recommendation analysis failed: {str(e)}")
    
    def format_for_chatbot(self, analysis_result: AnalysisResult) -> str:
        """
        Format analysis result for chatbot response.
        
        Args:
            analysis_result: Analysis result to format
            
        Returns:
            Formatted string for chatbot
        """
        response = f"**{analysis_result.title}**\n\n"
        response += f"{analysis_result.summary}\n\n"
        
        if analysis_result.insights:
            response += "**Key Insights:**\n"
            for insight in analysis_result.insights:
                response += f"• {insight}\n"
        
        if analysis_result.visualization:
            response += f"\n📊 Visualization available: {analysis_result.visualization.get('chart_type', 'chart')}\n"
        
        return response
    
    def prepare_visualization_data(
        self,
        analysis_result: AnalysisResult,
        chart_type: Optional[ChartType] = None
    ) -> Dict[str, Any]:
        """
        Prepare data for visualization generation.
        
        Args:
            analysis_result: Analysis result
            chart_type: Optional chart type override
            
        Returns:
            Dictionary with visualization configuration
        """
        if analysis_result.visualization:
            viz = analysis_result.visualization.copy()
            if chart_type:
                viz["chart_type"] = chart_type.value
            return viz
        
        # Generate default visualization based on analysis type
        return {
            "chart_type": chart_type.value if chart_type else ChartType.TABLE.value,
            "title": analysis_result.title,
            "data": analysis_result.data
        }
    
    # Helper methods
    
    def _get_days_from_period(self, period: str) -> int:
        """Convert period string to number of days."""
        period_map = {
            "last_week": 7,
            "last_month": 30,
            "last_quarter": 90,
            "last_year": 365,
            "last_2_years": 730
        }
        return period_map.get(period, 365)
    
    def _generate_trend_insights(
        self,
        data: List[Dict],
        metric: str,
        group_by: Optional[str]
    ) -> List[str]:
        """Generate insights from trend data."""
        insights = []
        
        if not data:
            return ["No data available for analysis"]
        
        insights.append(f"Analyzed {len(data)} data points")
        
        # Calculate growth if time-series data
        if group_by == "month" and len(data) >= 2:
            first_value = data[0].get("total_concerts", 0)
            last_value = data[-1].get("total_concerts", 0)
            
            if first_value > 0:
                growth = ((last_value - first_value) / first_value) * 100
                insights.append(f"Concert volume {'increased' if growth > 0 else 'decreased'} by {abs(growth):.1f}%")
        
        # Find peak values
        if metric == "attendance" and "avg_attendance" in data[0]:
            max_item = max(data, key=lambda x: x.get("avg_attendance", 0))
            insights.append(f"Highest average attendance: {max_item.get('avg_attendance', 0):.0f}")
        
        if "total_revenue" in data[0]:
            total_rev = sum(item.get("total_revenue", 0) for item in data)
            insights.append(f"Total revenue: ${total_rev:,.2f}")
        
        return insights
    
    def _generate_comparison_insights(
        self,
        data: List[Dict],
        entity_type: str,
        metrics: List[str]
    ) -> List[str]:
        """Generate insights from comparison data."""
        insights = []
        
        if not data:
            return ["No data available for comparison"]
        
        # Find top performer for each metric
        if "total_concerts" in data[0]:
            top_concerts = max(data, key=lambda x: x.get("total_concerts", 0))
            insights.append(f"Most active: {top_concerts.get('name', 'Unknown')} with {top_concerts.get('total_concerts', 0)} concerts")
        
        if "total_revenue" in data[0]:
            top_revenue = max(data, key=lambda x: x.get("total_revenue", 0))
            insights.append(f"Highest revenue: {top_revenue.get('name', 'Unknown')} with ${top_revenue.get('total_revenue', 0):,.2f}")
        
        if "avg_attendance" in data[0]:
            top_attendance = max(data, key=lambda x: x.get("avg_attendance", 0))
            insights.append(f"Best attendance: {top_attendance.get('name', 'Unknown')} with {top_attendance.get('avg_attendance', 0):.0f} avg")
        
        return insights
    
    def _generate_statistical_insights(
        self,
        stats: Dict[str, Any],
        entity_type: str
    ) -> List[str]:
        """Generate insights from statistical summary."""
        insights = []
        
        if entity_type == "concert":
            insights.append(f"Total concerts: {stats.get('total_concerts', 0):,}")
            insights.append(f"Average attendance: {stats.get('avg_attendance', 0):.0f}")
            insights.append(f"Total revenue: ${stats.get('total_revenue', 0):,.2f}")
            
            if stats.get('stddev_attendance'):
                insights.append(f"Attendance variability: ±{stats.get('stddev_attendance', 0):.0f}")
        
        elif entity_type == "artist":
            insights.append(f"Total artists: {stats.get('total_artists', 0):,}")
            insights.append(f"Average popularity: {stats.get('avg_popularity', 0):.2f}")
            insights.append(f"Unique genres: {stats.get('unique_genres', 0)}")
        
        elif entity_type == "venue":
            insights.append(f"Total venues: {stats.get('total_venues', 0):,}")
            insights.append(f"Average capacity: {stats.get('avg_capacity', 0):.0f}")
            insights.append(f"Unique cities: {stats.get('unique_cities', 0)}")
        
        return insights
    
    def _prepare_trend_visualization(
        self,
        data: List[Dict],
        metric: str,
        group_by: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare visualization data for trends."""
        if group_by == "month":
            return {
                "chart_type": ChartType.LINE.value,
                "data": {
                    "labels": [str(item.get("period", "")) for item in data],
                    "datasets": [
                        {
                            "label": "Total Concerts",
                            "values": [item.get("total_concerts", 0) for item in data]
                        }
                    ]
                }
            }
        elif group_by == "genre":
            return {
                "chart_type": ChartType.BAR.value,
                "data": {
                    "labels": [item.get("genre", "Unknown") for item in data],
                    "values": [item.get("total_concerts", 0) for item in data]
                }
            }
        else:
            return {
                "chart_type": ChartType.LINE.value,
                "data": {
                    "labels": [str(item.get("event_date", "")) for item in data],
                    "values": [item.get(metric, 0) for item in data]
                }
            }
    
    def _prepare_comparison_visualization(
        self,
        data: List[Dict],
        entity_type: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Prepare visualization data for comparisons."""
        return {
            "chart_type": ChartType.BAR.value,
            "data": {
                "labels": [item.get("name", "Unknown") for item in data],
                "datasets": [
                    {
                        "label": metric.replace("_", " ").title(),
                        "values": [item.get(metric, 0) for item in data]
                    }
                    for metric in metrics if metric in data[0]
                ]
            }
        }
    
    def _prepare_summary_visualization(
        self,
        stats: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """Prepare visualization data for statistical summary."""
        return {
            "chart_type": ChartType.TABLE.value,
            "data": {
                "headers": ["Metric", "Value"],
                "rows": [[k.replace("_", " ").title(), str(v)] for k, v in stats.items()]
            }
        }
    
    def _prepare_recommendation_visualization(
        self,
        recommendations: List
    ) -> Dict[str, Any]:
        """Prepare visualization data for recommendations."""
        return {
            "chart_type": ChartType.BAR.value,
            "data": {
                "labels": [rec.item_id[:20] for rec in recommendations[:10]],
                "values": [rec.score for rec in recommendations[:10]]
            }
        }
    
    def _create_error_result(self, error_message: str) -> AnalysisResult:
        """Create an error analysis result."""
        return AnalysisResult(
            analysis_type=AnalysisType.STATISTICAL_SUMMARY,
            title="Analysis Error",
            summary=error_message,
            insights=[f"Error: {error_message}"],
            data={"error": error_message}
        )
    
    def _create_empty_result(self, message: str) -> AnalysisResult:
        """Create an empty analysis result."""
        return AnalysisResult(
            analysis_type=AnalysisType.STATISTICAL_SUMMARY,
            title="No Data",
            summary=message,
            insights=[message],
            data={}
        )
