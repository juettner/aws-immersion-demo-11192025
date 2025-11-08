"""
Venue Popularity Model - Data models and feature engineering for venue ranking
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class VenuePopularity:
    """Model representing venue popularity metrics and ranking"""
    venue_id: str
    popularity_rank: int
    avg_attendance_rate: float
    revenue_per_event: float
    booking_frequency: float
    calculated_at: datetime


@dataclass
class VenueFeatures:
    """Feature set for venue popularity prediction"""
    venue_id: str
    total_concerts: int
    avg_attendance: float
    avg_attendance_rate: float
    total_revenue: float
    avg_revenue_per_event: float
    booking_frequency: float  # concerts per month
    capacity: int
    venue_type: str
    location_popularity: float
    artist_diversity_score: float  # unique artists / total concerts
    repeat_booking_rate: float  # artists that return
    
    def to_feature_vector(self) -> List[float]:
        """Convert features to numerical vector for ML model"""
        venue_type_encoding = {
            'arena': 4,
            'theater': 3,
            'club': 2,
            'outdoor': 1
        }
        
        return [
            float(self.total_concerts),
            self.avg_attendance,
            self.avg_attendance_rate,
            self.total_revenue,
            self.avg_revenue_per_event,
            self.booking_frequency,
            float(self.capacity),
            float(venue_type_encoding.get(self.venue_type.lower(), 0)),
            self.location_popularity,
            self.artist_diversity_score,
            self.repeat_booking_rate
        ]
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Get ordered list of feature names"""
        return [
            'total_concerts',
            'avg_attendance',
            'avg_attendance_rate',
            'total_revenue',
            'avg_revenue_per_event',
            'booking_frequency',
            'capacity',
            'venue_type_encoded',
            'location_popularity',
            'artist_diversity_score',
            'repeat_booking_rate'
        ]
