"""
Recommendation data models for concert recommendation engine.
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class UserInteraction(BaseModel):
    """User interaction with concerts (attendance, purchase, etc.)."""
    user_id: str = Field(..., description="User identifier")
    concert_id: str = Field(..., description="Concert identifier")
    interaction_type: str = Field(..., description="Type of interaction (attended, purchased, viewed)")
    interaction_strength: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Strength of interaction (0-1)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RecommendationScore(BaseModel):
    """Individual recommendation with score."""
    item_id: str = Field(..., description="ID of recommended item (concert, artist, venue)")
    item_type: str = Field(..., description="Type of item (concert, artist, venue)")
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    reasoning: Optional[str] = Field(None, description="Explanation for recommendation")
    metadata: Dict = Field(default_factory=dict, description="Additional item metadata")


class RecommendationResult(BaseModel):
    """Complete recommendation result for a user."""
    user_id: str = Field(..., description="User identifier")
    recommendations: List[RecommendationScore] = Field(
        default_factory=list,
        description="List of recommendations"
    )
    algorithm: str = Field(..., description="Algorithm used (collaborative, content-based, hybrid)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_candidates: int = Field(default=0, description="Total items considered")


class SimilarityScore(BaseModel):
    """Similarity score between two items or users."""
    id1: str = Field(..., description="First item/user ID")
    id2: str = Field(..., description="Second item/user ID")
    similarity: float = Field(..., ge=-1.0, le=1.0, description="Similarity score")
    method: str = Field(..., description="Similarity calculation method")
