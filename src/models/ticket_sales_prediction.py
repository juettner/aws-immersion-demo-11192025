"""
Ticket Sales Prediction Model - Data models and feature engineering for ticket sales forecasting
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TicketSalesPrediction:
    """Model representing ticket sales prediction results"""
    prediction_id: str
    concert_id: str
    artist_id: str
    venue_id: str
    event_date: datetime
    predicted_sales: float
    confidence_score: float
    low_confidence_flag: bool  # True if confidence < 0.7
    prediction_timestamp: datetime
    actual_sales: Optional[float] = None


@dataclass
class TicketSalesFeatures:
    """Feature set for ticket sales prediction"""
    concert_id: str
    artist_id: str
    venue_id: str
    event_date: datetime
    
    # Artist features
    artist_popularity_score: float
    artist_avg_attendance: float
    artist_total_concerts: int
    artist_avg_revenue: float
    artist_genre_popularity: float
    
    # Venue features
    venue_capacity: int
    venue_avg_attendance_rate: float
    venue_popularity_rank: float
    venue_type_encoded: float
    venue_location_popularity: float
    
    # Historical sales features
    historical_avg_sales: float
    historical_max_sales: float
    similar_concert_avg_sales: float
    
    # Temporal features
    days_until_event: int
    is_weekend: bool
    month_of_year: int
    season_encoded: float  # 1=winter, 2=spring, 3=summer, 4=fall
    
    # Pricing features
    avg_ticket_price: float
    price_range: float
    lowest_price: float
    highest_price: float
    
    def to_feature_vector(self) -> List[float]:
        """Convert features to numerical vector for ML model"""
        return [
            self.artist_popularity_score,
            self.artist_avg_attendance,
            float(self.artist_total_concerts),
            self.artist_avg_revenue,
            self.artist_genre_popularity,
            float(self.venue_capacity),
            self.venue_avg_attendance_rate,
            self.venue_popularity_rank,
            self.venue_type_encoded,
            self.venue_location_popularity,
            self.historical_avg_sales,
            self.historical_max_sales,
            self.similar_concert_avg_sales,
            float(self.days_until_event),
            float(self.is_weekend),
            float(self.month_of_year),
            self.season_encoded,
            self.avg_ticket_price,
            self.price_range,
            self.lowest_price,
            self.highest_price
        ]
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Get ordered list of feature names"""
        return [
            'artist_popularity_score',
            'artist_avg_attendance',
            'artist_total_concerts',
            'artist_avg_revenue',
            'artist_genre_popularity',
            'venue_capacity',
            'venue_avg_attendance_rate',
            'venue_popularity_rank',
            'venue_type_encoded',
            'venue_location_popularity',
            'historical_avg_sales',
            'historical_max_sales',
            'similar_concert_avg_sales',
            'days_until_event',
            'is_weekend',
            'month_of_year',
            'season_encoded',
            'avg_ticket_price',
            'price_range',
            'lowest_price',
            'highest_price'
        ]
