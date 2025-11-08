"""
Concert data model with validation schemas.
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import Field, validator
from .base import BaseEntity


class Concert(BaseEntity):
    """Concert entity linking artists and venues with event details."""
    concert_id: str = Field(..., description="Unique concert identifier")
    artist_id: str = Field(..., description="Reference to artist performing")
    venue_id: str = Field(..., description="Reference to venue hosting the concert")
    event_date: datetime = Field(..., description="Date and time of the concert")
    ticket_prices: Dict[str, float] = Field(
        default_factory=dict, 
        description="Ticket prices by tier (e.g., 'general': 50.0, 'vip': 150.0)"
    )
    total_attendance: Optional[int] = Field(
        None, 
        ge=0, 
        description="Actual attendance count"
    )
    revenue: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Total revenue generated"
    )
    status: str = Field(
        default="scheduled", 
        description="Concert status (scheduled, completed, cancelled)"
    )
    
    @validator('event_date')
    def validate_event_date(cls, v):
        """Ensure event date is not too far in the past or future."""
        now = datetime.utcnow()
        # Allow events up to 50 years in the past (historical data) and 5 years in the future
        if v.year < now.year - 50:
            raise ValueError('Event date is too far in the past')
        if v.year > now.year + 5:
            raise ValueError('Event date is too far in the future')
        return v
    
    @validator('ticket_prices')
    def validate_ticket_prices(cls, v):
        """Validate ticket price structure."""
        if not v:
            return v
        
        for tier, price in v.items():
            if not isinstance(price, (int, float)) or price < 0:
                raise ValueError(f'Invalid price for tier {tier}: must be non-negative number')
            if price > 10000:  # Reasonable upper limit
                raise ValueError(f'Price for tier {tier} seems unreasonably high')
        
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate concert status."""
        allowed_statuses = ['scheduled', 'completed', 'cancelled', 'postponed']
        if v.lower() not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v.lower()
    
    @validator('total_attendance')
    def validate_attendance(cls, v):
        """Validate attendance count."""
        if v is not None and v > 500000:  # Largest concerts in history
            raise ValueError('Attendance seems unreasonably large')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "concert_id": "con_001",
                "artist_id": "art_001",
                "venue_id": "ven_001",
                "event_date": "2024-07-15T20:00:00Z",
                "ticket_prices": {
                    "general": 75.0,
                    "premium": 125.0,
                    "vip": 250.0
                },
                "total_attendance": 18500,
                "revenue": 1875000.0,
                "status": "completed"
            }
        }