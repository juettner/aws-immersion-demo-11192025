"""
Artist data model with validation schemas.
"""
from datetime import date
from typing import List, Optional
from pydantic import Field, field_validator, ConfigDict
from .base import BaseEntity


class Artist(BaseEntity):
    """Artist entity with comprehensive metadata."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "artist_id": "art_001",
                "name": "The Rolling Stones",
                "genre": ["rock", "blues rock"],
                "popularity_score": 85.5,
                "formation_date": "1962-07-12",
                "members": ["Mick Jagger", "Keith Richards", "Charlie Watts", "Ronnie Wood"],
                "spotify_id": "22bE4uQ6baNwSHPVcDxLCe"
            }
        }
    )
    
    artist_id: str = Field(..., description="Unique artist identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Artist name")
    genre: List[str] = Field(default_factory=list, description="Musical genres")
    popularity_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0, 
        description="Popularity score (0-100)"
    )
    formation_date: Optional[date] = Field(None, description="Date when artist/band was formed")
    members: List[str] = Field(default_factory=list, description="Band members or solo artist")
    spotify_id: Optional[str] = Field(None, description="Spotify artist ID")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure artist name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Artist name cannot be empty')
        return v.strip()
    
    @field_validator('genre')
    @classmethod
    def validate_genre(cls, v):
        """Ensure genres are properly formatted."""
        return [genre.strip().lower() for genre in v if genre.strip()]
    
    @field_validator('members')
    @classmethod
    def validate_members(cls, v):
        """Ensure member names are properly formatted."""
        return [member.strip() for member in v if member.strip()]