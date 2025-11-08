"""
Unified recommendation service API for concert recommendations.

This service provides a high-level API that combines collaborative filtering
and content-based filtering to generate personalized concert, artist, and
venue recommendations.
"""
from typing import List, Dict, Optional, Set
from enum import Enum

from src.models.artist import Artist
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.recommendation import (
    UserInteraction,
    RecommendationScore,
    RecommendationResult
)
from src.services.collaborative_filtering_service import CollaborativeFilteringService
from src.services.content_based_filtering_service import ContentBasedFilteringService


class RecommendationStrategy(str, Enum):
    """Recommendation algorithm strategy."""
    COLLABORATIVE_USER = "collaborative_user"
    COLLABORATIVE_ITEM = "collaborative_item"
    CONTENT_ARTIST = "content_artist"
    CONTENT_VENUE = "content_venue"
    CONTENT_HYBRID = "content_hybrid"
    HYBRID_ALL = "hybrid_all"


class RecommendationService:
    """
    Unified recommendation service for generating personalized recommendations.
    
    Provides methods for:
    - Concert recommendations
    - Artist recommendations
    - Venue recommendations
    - Batch recommendations for multiple users
    """
    
    def __init__(self):
        """Initialize the recommendation service."""
        self.collaborative_service = CollaborativeFilteringService()
        self.content_service = ContentBasedFilteringService()
        
    def add_interaction(self, interaction: UserInteraction) -> None:
        """
        Add a user interaction to the collaborative filtering system.
        
        Args:
            interaction: User interaction data
        """
        self.collaborative_service.add_interaction(interaction)
    
    def add_interactions_batch(self, interactions: List[UserInteraction]) -> None:
        """
        Add multiple user interactions in batch.
        
        Args:
            interactions: List of user interactions
        """
        self.collaborative_service.build_interaction_matrix(interactions)
    
    def add_artist(self, artist: Artist) -> None:
        """
        Add an artist to the content-based system.
        
        Args:
            artist: Artist data
        """
        self.content_service.add_artist(artist)
    
    def add_venue(self, venue: Venue) -> None:
        """
        Add a venue to the content-based system.
        
        Args:
            venue: Venue data
        """
        self.content_service.add_venue(venue)
    
    def add_concert(self, concert: Concert) -> None:
        """
        Add a concert to the content-based system.
        
        Args:
            concert: Concert data
        """
        self.content_service.add_concert(concert)
    
    def recommend_concerts(
        self,
        user_id: str,
        strategy: RecommendationStrategy = RecommendationStrategy.HYBRID_ALL,
        top_k: int = 10,
        user_preferences: Optional[Dict] = None
    ) -> RecommendationResult:
        """
        Generate concert recommendations for a user.
        
        Args:
            user_id: User identifier
            strategy: Recommendation strategy to use
            top_k: Number of recommendations to return
            user_preferences: Optional user preferences (preferred artists, venues)
            
        Returns:
            Recommendation result with scored concerts
        """
        if user_preferences is None:
            user_preferences = {}
        
        if strategy == RecommendationStrategy.COLLABORATIVE_USER:
            return self.collaborative_service.recommend_concerts_user_based(
                user_id=user_id,
                top_k=top_k
            )
        
        elif strategy == RecommendationStrategy.COLLABORATIVE_ITEM:
            return self.collaborative_service.recommend_concerts_item_based(
                user_id=user_id,
                top_k=top_k
            )
        
        elif strategy == RecommendationStrategy.CONTENT_ARTIST:
            preferred_artists = user_preferences.get("preferred_artist_ids", [])
            exclude_concerts = user_preferences.get("exclude_concert_ids", set())
            return self.content_service.recommend_concerts_by_artist_preference(
                preferred_artist_ids=preferred_artists,
                top_k=top_k,
                exclude_concert_ids=exclude_concerts
            )
        
        elif strategy == RecommendationStrategy.CONTENT_VENUE:
            preferred_venues = user_preferences.get("preferred_venue_ids", [])
            exclude_concerts = user_preferences.get("exclude_concert_ids", set())
            return self.content_service.recommend_concerts_by_venue_preference(
                preferred_venue_ids=preferred_venues,
                top_k=top_k,
                exclude_concert_ids=exclude_concerts
            )
        
        elif strategy == RecommendationStrategy.CONTENT_HYBRID:
            preferred_artists = user_preferences.get("preferred_artist_ids", [])
            preferred_venues = user_preferences.get("preferred_venue_ids", [])
            exclude_concerts = user_preferences.get("exclude_concert_ids", set())
            return self.content_service.recommend_concerts_hybrid(
                preferred_artist_ids=preferred_artists,
                preferred_venue_ids=preferred_venues,
                top_k=top_k,
                exclude_concert_ids=exclude_concerts
            )
        
        elif strategy == RecommendationStrategy.HYBRID_ALL:
            return self._recommend_concerts_hybrid_all(
                user_id=user_id,
                top_k=top_k,
                user_preferences=user_preferences
            )
        
        else:
            raise ValueError(f"Unknown recommendation strategy: {strategy}")
    
    def _recommend_concerts_hybrid_all(
        self,
        user_id: str,
        top_k: int,
        user_preferences: Dict
    ) -> RecommendationResult:
        """
        Generate recommendations using all available methods and combine them.
        
        Args:
            user_id: User identifier
            top_k: Number of recommendations to return
            user_preferences: User preferences
            
        Returns:
            Combined recommendation result
        """
        all_recommendations: Dict[str, RecommendationScore] = {}
        
        # Try collaborative filtering (user-based)
        try:
            collab_user_recs = self.collaborative_service.recommend_concerts_user_based(
                user_id=user_id,
                top_k=top_k * 2
            )
            for rec in collab_user_recs.recommendations:
                if rec.item_id not in all_recommendations:
                    all_recommendations[rec.item_id] = rec
                else:
                    # Combine scores
                    existing = all_recommendations[rec.item_id]
                    all_recommendations[rec.item_id] = RecommendationScore(
                        item_id=rec.item_id,
                        item_type=rec.item_type,
                        score=(existing.score + rec.score) / 2,
                        confidence=max(existing.confidence, rec.confidence),
                        reasoning="Hybrid: collaborative + content",
                        metadata=rec.metadata
                    )
        except Exception:
            pass  # Collaborative filtering may fail if no data
        
        # Try content-based filtering if preferences available
        preferred_artists = user_preferences.get("preferred_artist_ids", [])
        preferred_venues = user_preferences.get("preferred_venue_ids", [])
        exclude_concerts = user_preferences.get("exclude_concert_ids", set())
        
        if preferred_artists or preferred_venues:
            try:
                content_recs = self.content_service.recommend_concerts_hybrid(
                    preferred_artist_ids=preferred_artists,
                    preferred_venue_ids=preferred_venues,
                    top_k=top_k * 2,
                    exclude_concert_ids=exclude_concerts
                )
                for rec in content_recs.recommendations:
                    if rec.item_id not in all_recommendations:
                        all_recommendations[rec.item_id] = rec
                    else:
                        # Combine scores
                        existing = all_recommendations[rec.item_id]
                        all_recommendations[rec.item_id] = RecommendationScore(
                            item_id=rec.item_id,
                            item_type=rec.item_type,
                            score=(existing.score + rec.score) / 2,
                            confidence=max(existing.confidence, rec.confidence),
                            reasoning="Hybrid: collaborative + content",
                            metadata=rec.metadata
                        )
            except Exception:
                pass
        
        # Sort and return top k
        recommendations = sorted(
            all_recommendations.values(),
            key=lambda x: x.score,
            reverse=True
        )[:top_k]
        
        return RecommendationResult(
            user_id=user_id,
            recommendations=recommendations,
            algorithm="hybrid_all",
            total_candidates=len(all_recommendations)
        )
    
    def recommend_artists(
        self,
        preferred_artist_ids: List[str],
        top_k: int = 10
    ) -> List[RecommendationScore]:
        """
        Recommend artists based on user's preferred artists.
        
        Args:
            preferred_artist_ids: List of artist IDs the user likes
            top_k: Number of artist recommendations to return
            
        Returns:
            List of recommended artists with scores
        """
        similar_artists: Dict[str, float] = {}
        
        for artist_id in preferred_artist_ids:
            similar = self.content_service.find_similar_artists(
                artist_id=artist_id,
                top_k=top_k * 2
            )
            
            for sim in similar:
                other_artist_id = sim.id2
                if other_artist_id not in similar_artists:
                    similar_artists[other_artist_id] = 0.0
                # Take maximum similarity across all preferred artists
                similar_artists[other_artist_id] = max(
                    similar_artists[other_artist_id],
                    sim.similarity
                )
        
        # Create recommendations
        recommendations = []
        for artist_id, score in similar_artists.items():
            artist = self.content_service.artists.get(artist_id)
            reasoning = "Similar artist"
            metadata = {}
            
            if artist:
                reasoning = f"Similar genres: {', '.join(artist.genre[:2])}"
                metadata = {
                    "name": artist.name,
                    "genres": artist.genre,
                    "popularity": artist.popularity_score
                }
            
            recommendations.append(
                RecommendationScore(
                    item_id=artist_id,
                    item_type="artist",
                    score=score,
                    confidence=min(len(preferred_artist_ids) / 5.0, 1.0),
                    reasoning=reasoning,
                    metadata=metadata
                )
            )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_k]
    
    def recommend_venues(
        self,
        preferred_venue_ids: List[str],
        top_k: int = 10
    ) -> List[RecommendationScore]:
        """
        Recommend venues based on user's preferred venues.
        
        Args:
            preferred_venue_ids: List of venue IDs the user likes
            top_k: Number of venue recommendations to return
            
        Returns:
            List of recommended venues with scores
        """
        similar_venues: Dict[str, float] = {}
        
        for venue_id in preferred_venue_ids:
            similar = self.content_service.find_similar_venues(
                venue_id=venue_id,
                top_k=top_k * 2
            )
            
            for sim in similar:
                other_venue_id = sim.id2
                if other_venue_id not in similar_venues:
                    similar_venues[other_venue_id] = 0.0
                # Take maximum similarity across all preferred venues
                similar_venues[other_venue_id] = max(
                    similar_venues[other_venue_id],
                    sim.similarity
                )
        
        # Create recommendations
        recommendations = []
        for venue_id, score in similar_venues.items():
            venue = self.content_service.venues.get(venue_id)
            reasoning = "Similar venue"
            metadata = {}
            
            if venue:
                reasoning = f"Similar venue: {venue.venue_type} in {venue.location.city}"
                metadata = {
                    "name": venue.name,
                    "type": venue.venue_type,
                    "capacity": venue.capacity,
                    "location": {
                        "city": venue.location.city,
                        "state": venue.location.state
                    }
                }
            
            recommendations.append(
                RecommendationScore(
                    item_id=venue_id,
                    item_type="venue",
                    score=score,
                    confidence=min(len(preferred_venue_ids) / 5.0, 1.0),
                    reasoning=reasoning,
                    metadata=metadata
                )
            )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_k]
    
    def recommend_batch(
        self,
        user_ids: List[str],
        strategy: RecommendationStrategy = RecommendationStrategy.HYBRID_ALL,
        top_k: int = 10,
        user_preferences_map: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, RecommendationResult]:
        """
        Generate recommendations for multiple users in batch.
        
        Args:
            user_ids: List of user identifiers
            strategy: Recommendation strategy to use
            top_k: Number of recommendations per user
            user_preferences_map: Map of user_id to preferences
            
        Returns:
            Dictionary mapping user_id to recommendation results
        """
        if user_preferences_map is None:
            user_preferences_map = {}
        
        results = {}
        
        for user_id in user_ids:
            user_prefs = user_preferences_map.get(user_id, {})
            try:
                results[user_id] = self.recommend_concerts(
                    user_id=user_id,
                    strategy=strategy,
                    top_k=top_k,
                    user_preferences=user_prefs
                )
            except Exception as e:
                # Return empty result on error
                results[user_id] = RecommendationResult(
                    user_id=user_id,
                    recommendations=[],
                    algorithm=strategy.value,
                    total_candidates=0
                )
        
        return results
    
    def get_system_statistics(self) -> Dict:
        """
        Get statistics about the recommendation system.
        
        Returns:
            Dictionary with system statistics
        """
        collab_stats = self.collaborative_service.get_matrix_statistics()
        
        return {
            "collaborative_filtering": collab_stats,
            "content_based": {
                "total_artists": len(self.content_service.artists),
                "total_venues": len(self.content_service.venues),
                "total_concerts": len(self.content_service.concerts)
            }
        }
