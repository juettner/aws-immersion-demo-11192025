"""
ML Models API endpoints for Concert AI Platform.

Provides direct access to ML models for venue popularity, ticket sales prediction,
and recommendations.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import structlog

from src.services.venue_popularity_service import VenuePopularityService
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.services.recommendation_service import RecommendationService
from src.services.redshift_service import RedshiftService
from src.config.settings import Settings

logger = structlog.get_logger(__name__)


# Request/Response Models

class VenuePopularityRequest(BaseModel):
    """Request for venue popularity ranking."""
    top_n: int = Field(default=10, ge=1, le=100, description="Number of top venues to return")
    min_events: int = Field(default=5, ge=1, description="Minimum number of events for ranking")


class VenuePopularityResponse(BaseModel):
    """Response with venue popularity rankings."""
    venues: List[Dict[str, Any]]
    total_venues: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TicketSalesPredictionRequest(BaseModel):
    """Request for ticket sales prediction."""
    artist_id: str = Field(..., description="Artist identifier")
    venue_id: str = Field(..., description="Venue identifier")
    event_date: Optional[str] = Field(None, description="Event date (YYYY-MM-DD)")
    ticket_price: Optional[float] = Field(None, ge=0, description="Average ticket price")


class TicketSalesPredictionResponse(BaseModel):
    """Response with ticket sales prediction."""
    predicted_sales: float
    confidence: float = Field(ge=0.0, le=1.0)
    features_used: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RecommendationRequest(BaseModel):
    """Request for concert recommendations."""
    user_id: Optional[str] = Field(None, description="User identifier for personalized recommendations")
    artist_preferences: Optional[List[str]] = Field(None, description="Preferred artist genres")
    location: Optional[str] = Field(None, description="Preferred location")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations")


class RecommendationResponse(BaseModel):
    """Response with concert recommendations."""
    recommendations: List[Dict[str, Any]]
    total_recommendations: int
    recommendation_type: str  # "collaborative", "content_based", "hybrid"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Create router
router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# Initialize services (will be set by main app)
venue_service: Optional[VenuePopularityService] = None
ticket_service: Optional[TicketSalesPredictionService] = None
recommendation_service: Optional[RecommendationService] = None
redshift_service: Optional[RedshiftService] = None


def initialize_ml_services(settings: Settings):
    """
    Initialize ML services.
    
    Args:
        settings: Application settings
    """
    global venue_service, ticket_service, recommendation_service, redshift_service
    
    try:
        # Initialize Redshift service if configured
        if settings.aws.redshift_cluster_id:
            redshift_service = RedshiftService(
                cluster_id=settings.aws.redshift_cluster_id,
                database=settings.aws.redshift_database,
                region=settings.aws.region
            )
            logger.info("Redshift service initialized for ML API")
        
        # Initialize ML services
        # Note: These services may need Redshift client, handle gracefully
        try:
            venue_service = VenuePopularityService()
            logger.info("Venue popularity service initialized")
        except Exception as e:
            logger.warning("Venue popularity service initialization failed", error=str(e))
        
        try:
            ticket_service = TicketSalesPredictionService()
            logger.info("Ticket sales prediction service initialized")
        except Exception as e:
            logger.warning("Ticket sales prediction service initialization failed", error=str(e))
        
        try:
            recommendation_service = RecommendationService()
            logger.info("Recommendation service initialized")
        except Exception as e:
            logger.warning("Recommendation service initialization failed", error=str(e))
    
    except Exception as e:
        logger.error("Failed to initialize ML services", error=str(e))


# Endpoints

@router.get("/health")
async def ml_health_check():
    """Check ML services health."""
    return {
        "venue_popularity": "available" if venue_service else "unavailable",
        "ticket_prediction": "available" if ticket_service else "unavailable",
        "recommendations": "available" if recommendation_service else "unavailable",
        "redshift": "available" if redshift_service else "unavailable"
    }


@router.post("/venues/popularity", response_model=VenuePopularityResponse)
async def get_venue_popularity(request: VenuePopularityRequest):
    """
    Get venue popularity rankings.
    
    Args:
        request: Venue popularity request parameters
        
    Returns:
        Ranked list of popular venues
    """
    if not venue_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Venue popularity service not available"
        )
    
    try:
        # Get venue rankings
        venues = venue_service.get_top_venues(
            top_n=request.top_n,
            min_events=request.min_events
        )
        
        return VenuePopularityResponse(
            venues=venues,
            total_venues=len(venues)
        )
    
    except Exception as e:
        logger.error("Error getting venue popularity", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get venue popularity: {str(e)}"
        )


@router.post("/tickets/predict", response_model=TicketSalesPredictionResponse)
async def predict_ticket_sales(request: TicketSalesPredictionRequest):
    """
    Predict ticket sales for a concert.
    
    Args:
        request: Ticket sales prediction request
        
    Returns:
        Predicted ticket sales with confidence score
    """
    if not ticket_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket sales prediction service not available"
        )
    
    try:
        # Prepare features
        features = {
            "artist_id": request.artist_id,
            "venue_id": request.venue_id,
            "event_date": request.event_date,
            "ticket_price": request.ticket_price
        }
        
        # Get prediction
        prediction = ticket_service.predict_sales(
            artist_id=request.artist_id,
            venue_id=request.venue_id,
            event_date=request.event_date,
            ticket_price=request.ticket_price
        )
        
        return TicketSalesPredictionResponse(
            predicted_sales=prediction.get("predicted_sales", 0),
            confidence=prediction.get("confidence", 0.5),
            features_used=features
        )
    
    except Exception as e:
        logger.error("Error predicting ticket sales", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict ticket sales: {str(e)}"
        )


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get concert recommendations.
    
    Args:
        request: Recommendation request parameters
        
    Returns:
        List of recommended concerts
    """
    if not recommendation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service not available"
        )
    
    try:
        # Get recommendations
        recommendations = recommendation_service.get_recommendations(
            user_id=request.user_id,
            preferences={
                "genres": request.artist_preferences,
                "location": request.location
            },
            top_n=request.top_n
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            total_recommendations=len(recommendations),
            recommendation_type="hybrid"
        )
    
    except Exception as e:
        logger.error("Error getting recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/venues/{venue_id}")
async def get_venue_details(venue_id: str):
    """
    Get detailed venue information.
    
    Args:
        venue_id: Venue identifier
        
    Returns:
        Venue details including popularity metrics
    """
    if not redshift_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        # Query venue details from Redshift
        query = f"""
            SELECT 
                venue_id,
                name,
                city,
                state,
                capacity,
                venue_type
            FROM venues
            WHERE venue_id = '{venue_id}'
        """
        
        result = redshift_service.execute_query(query)
        
        if not result or not result.get("rows"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venue {venue_id} not found"
            )
        
        venue_data = result["rows"][0]
        
        return {
            "venue_id": venue_data.get("venue_id"),
            "name": venue_data.get("name"),
            "city": venue_data.get("city"),
            "state": venue_data.get("state"),
            "capacity": venue_data.get("capacity"),
            "venue_type": venue_data.get("venue_type")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting venue details", venue_id=venue_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get venue details: {str(e)}"
        )


@router.get("/artists/{artist_id}")
async def get_artist_details(artist_id: str):
    """
    Get detailed artist information.
    
    Args:
        artist_id: Artist identifier
        
    Returns:
        Artist details including performance history
    """
    if not redshift_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        # Query artist details from Redshift
        query = f"""
            SELECT 
                artist_id,
                name,
                genre,
                popularity_score
            FROM artists
            WHERE artist_id = '{artist_id}'
        """
        
        result = redshift_service.execute_query(query)
        
        if not result or not result.get("rows"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artist {artist_id} not found"
            )
        
        artist_data = result["rows"][0]
        
        return {
            "artist_id": artist_data.get("artist_id"),
            "name": artist_data.get("name"),
            "genre": artist_data.get("genre"),
            "popularity_score": artist_data.get("popularity_score")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting artist details", artist_id=artist_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get artist details: {str(e)}"
        )
