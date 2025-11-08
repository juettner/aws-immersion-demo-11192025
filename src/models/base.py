"""
Base models and common types for the concert data platform.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Base class for all entities with common fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # Allow validation of datetime objects
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Location(BaseModel):
    """Geographic location information."""
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    country: str = Field(..., description="Country name")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")