"""
Venue data model with validation schemas.
"""
from typing import List, Optional
from pydantic import Field, validator
from .base import BaseEntity, Location


class Venue(BaseEntity):
    """Venue entity with location and capacity information."""
    venue_id: str = Field(..., description="Unique venue identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Venue name")
    location: Location = Field(..., description="Venue location details")
    capacity: int = Field(..., gt=0, description="Maximum venue capacity")
    venue_type: str = Field(..., description="Type of venue (arena, theater, club, outdoor)")
    amenities: List[str] = Field(default_factory=list, description="Available amenities")
    ticketmaster_id: Optional[str] = Field(None, description="Ticketmaster venue ID")
    
    @validator('name')
    def validate_name(cls, v):
        """Ensure venue name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Venue name cannot be empty')
        return v.strip()
    
    @validator('venue_type')
    def validate_venue_type(cls, v):
        """Validate venue type against allowed values."""
        allowed_types = ['arena', 'theater', 'club', 'outdoor', 'stadium', 'amphitheater']
        if v.lower() not in allowed_types:
            raise ValueError(f'Venue type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    @validator('amenities')
    def validate_amenities(cls, v):
        """Ensure amenities are properly formatted."""
        return [amenity.strip().lower() for amenity in v if amenity.strip()]
    
    @validator('capacity')
    def validate_capacity(cls, v):
        """Ensure capacity is reasonable."""
        if v > 200000:  # Largest venues in the world
            raise ValueError('Capacity seems unreasonably large')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "venue_id": "ven_001",
                "name": "Madison Square Garden",
                "location": {
                    "address": "4 Pennsylvania Plaza",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "postal_code": "10001",
                    "latitude": 40.7505,
                    "longitude": -73.9934
                },
                "capacity": 20789,
                "venue_type": "arena",
                "amenities": ["parking", "concessions", "merchandise", "vip_boxes"],
                "ticketmaster_id": "KovZpZAEkJ7A"
            }
        }