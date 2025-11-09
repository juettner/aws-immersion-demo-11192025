"""
Venue data model with validation schemas.
"""
from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from .base import BaseEntity


class Venue(BaseEntity):
    """Venue entity with location and capacity information."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "venue_id": "ven_001",
                "name": "Madison Square Garden",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "capacity": 20789,
                "venue_type": "arena",
                "address": "4 Pennsylvania Plaza",
                "postal_code": "10001"
            }
        }
    )
    
    venue_id: str = Field(..., description="Unique venue identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Venue name")
    city: str = Field(..., min_length=1, max_length=100, description="City location")
    state: Optional[str] = Field(None, max_length=50, description="State/province")
    country: str = Field(..., min_length=2, max_length=100, description="Country")
    capacity: int = Field(..., gt=0, description="Maximum venue capacity")
    venue_type: str = Field(..., description="Type of venue (arena, stadium, theater, etc.)")
    address: Optional[str] = Field(None, max_length=300, description="Street address")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    
    @field_validator('name', 'city', 'country')
    @classmethod
    def validate_text_fields(cls, v):
        """Ensure text fields are properly formatted."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @field_validator('venue_type')
    @classmethod
    def validate_venue_type(cls, v):
        """Validate venue type."""
        allowed_types = ['arena', 'stadium', 'theater', 'club', 'amphitheater', 'hall', 'other']
        if v.lower() not in allowed_types:
            raise ValueError(f'Venue type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    @field_validator('capacity')
    @classmethod
    def validate_capacity(cls, v):
        """Validate capacity is reasonable."""
        if v > 200000:  # Largest venues in the world
            raise ValueError('Capacity seems unreasonably large')
        return v
    
    @field_validator('state', 'address', 'postal_code')
    @classmethod
    def validate_optional_text(cls, v):
        """Ensure optional text fields are properly formatted."""
        if v:
            return v.strip()
        return v