"""
Content-based filtering recommendation service for concerts.

This service implements content-based recommendations using artist features
(genre, popularity, style) and venue features (location, capacity, type).
"""
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
import math

from src.models.artist import Artist
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.recommendation import RecommendationScore, RecommendationResult, SimilarityScore


class ContentBasedFilteringService:
    """
    Content-based recommendation engine for concerts.
    
    Recommends concerts based on artist and venue features using
    similarity scoring and weighted combinations.
    """
    
    def __init__(self):
        """Initialize the content-based filtering service."""
        self.artists: Dict[str, Artist] = {}
        self.venues: Dict[str, Venue] = {}
        self.concerts: Dict[str, Concert] = {}
        
    def add_artist(self, artist: Artist) -> None:
        """Add an artist to the recommendation system."""
        self.artists[artist.artist_id] = artist
    
    def add_venue(self, venue: Venue) -> None:
        """Add a venue to the recommendation system."""
        self.venues[venue.venue_id] = venue
    
    def add_concert(self, concert: Concert) -> None:
        """Add a concert to the recommendation system."""
        self.concerts[concert.concert_id] = concert
    
    def calculate_genre_similarity(self, genres1: List[str], genres2: List[str]) -> float:
        """
        Calculate similarity between two genre lists using Jaccard similarity.
        
        Args:
            genres1: First list of genres
            genres2: Second list of genres
            
        Returns:
            Jaccard similarity score (0-1)
        """
        if not genres1 or not genres2:
            return 0.0
        
        set1 = set(g.lower() for g in genres1)
        set2 = set(g.lower() for g in genres2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_popularity_similarity(self, pop1: float, pop2: float) -> float:
        """
        Calculate similarity between two popularity scores.
        
        Uses normalized difference to compute similarity.
        
        Args:
            pop1: First popularity score (0-100)
            pop2: Second popularity score (0-100)
            
        Returns:
            Similarity score (0-1)
        """
        # Normalize to 0-1 range
        diff = abs(pop1 - pop2) / 100.0
        # Convert difference to similarity (closer = more similar)
        return 1.0 - diff
    
    def calculate_artist_similarity(
        self,
        artist1_id: str,
        artist2_id: str,
        genre_weight: float = 0.6,
        popularity_weight: float = 0.4
    ) -> float:
        """
        Calculate overall similarity between two artists.
        
        Combines genre similarity and popularity similarity with weights.
        
        Args:
            artist1_id: First artist ID
            artist2_id: Second artist ID
            genre_weight: Weight for genre similarity
            popularity_weight: Weight for popularity similarity
            
        Returns:
            Overall similarity score (0-1)
        """
        if artist1_id not in self.artists or artist2_id not in self.artists:
            return 0.0
        
        artist1 = self.artists[artist1_id]
        artist2 = self.artists[artist2_id]
        
        # Calculate component similarities
        genre_sim = self.calculate_genre_similarity(artist1.genre, artist2.genre)
        popularity_sim = self.calculate_popularity_similarity(
            artist1.popularity_score,
            artist2.popularity_score
        )
        
        # Weighted combination
        total_weight = genre_weight + popularity_weight
        similarity = (
            genre_weight * genre_sim +
            popularity_weight * popularity_sim
        ) / total_weight
        
        return similarity
    
    def find_similar_artists(
        self,
        artist_id: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[SimilarityScore]:
        """
        Find artists similar to the given artist.
        
        Args:
            artist_id: Target artist ID
            top_k: Number of similar artists to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar artists with scores
        """
        if artist_id not in self.artists:
            return []
        
        similarities = []
        
        for other_artist_id in self.artists:
            if other_artist_id == artist_id:
                continue
            
            similarity = self.calculate_artist_similarity(artist_id, other_artist_id)
            
            if similarity >= min_similarity:
                similarities.append(
                    SimilarityScore(
                        id1=artist_id,
                        id2=other_artist_id,
                        similarity=similarity,
                        method="content_based_artist"
                    )
                )
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_k]
    
    def calculate_location_distance(
        self,
        lat1: Optional[float],
        lon1: Optional[float],
        lat2: Optional[float],
        lon2: Optional[float]
    ) -> Optional[float]:
        """
        Calculate distance between two locations using Haversine formula.
        
        Args:
            lat1, lon1: First location coordinates
            lat2, lon2: Second location coordinates
            
        Returns:
            Distance in kilometers, or None if coordinates missing
        """
        if None in (lat1, lon1, lat2, lon2):
            return None
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        radius = 6371.0
        
        return radius * c
    
    def calculate_capacity_similarity(self, cap1: int, cap2: int) -> float:
        """
        Calculate similarity between two venue capacities.
        
        Args:
            cap1: First venue capacity
            cap2: Second venue capacity
            
        Returns:
            Similarity score (0-1)
        """
        # Use log scale for capacity comparison
        log_cap1 = math.log10(max(cap1, 1))
        log_cap2 = math.log10(max(cap2, 1))
        
        # Maximum reasonable log capacity difference (e.g., 100 vs 100,000)
        max_log_diff = 3.0
        
        log_diff = abs(log_cap1 - log_cap2)
        similarity = max(0.0, 1.0 - (log_diff / max_log_diff))
        
        return similarity
    
    def calculate_venue_similarity(
        self,
        venue1_id: str,
        venue2_id: str,
        location_weight: float = 0.4,
        capacity_weight: float = 0.3,
        type_weight: float = 0.3,
        max_distance_km: float = 100.0
    ) -> float:
        """
        Calculate overall similarity between two venues.
        
        Args:
            venue1_id: First venue ID
            venue2_id: Second venue ID
            location_weight: Weight for location similarity
            capacity_weight: Weight for capacity similarity
            type_weight: Weight for venue type similarity
            max_distance_km: Maximum distance for location similarity
            
        Returns:
            Overall similarity score (0-1)
        """
        if venue1_id not in self.venues or venue2_id not in self.venues:
            return 0.0
        
        venue1 = self.venues[venue1_id]
        venue2 = self.venues[venue2_id]
        
        # Location similarity
        distance = self.calculate_location_distance(
            venue1.location.latitude,
            venue1.location.longitude,
            venue2.location.latitude,
            venue2.location.longitude
        )
        
        if distance is not None:
            # Closer venues are more similar
            location_sim = max(0.0, 1.0 - (distance / max_distance_km))
        else:
            # If no coordinates, use city/state matching
            location_sim = 1.0 if (
                venue1.location.city.lower() == venue2.location.city.lower() and
                venue1.location.state.lower() == venue2.location.state.lower()
            ) else 0.0
        
        # Capacity similarity
        capacity_sim = self.calculate_capacity_similarity(venue1.capacity, venue2.capacity)
        
        # Type similarity
        type_sim = 1.0 if venue1.venue_type == venue2.venue_type else 0.0
        
        # Weighted combination
        total_weight = location_weight + capacity_weight + type_weight
        similarity = (
            location_weight * location_sim +
            capacity_weight * capacity_sim +
            type_weight * type_sim
        ) / total_weight
        
        return similarity
    
    def find_similar_venues(
        self,
        venue_id: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[SimilarityScore]:
        """
        Find venues similar to the given venue.
        
        Args:
            venue_id: Target venue ID
            top_k: Number of similar venues to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar venues with scores
        """
        if venue_id not in self.venues:
            return []
        
        similarities = []
        
        for other_venue_id in self.venues:
            if other_venue_id == venue_id:
                continue
            
            similarity = self.calculate_venue_similarity(venue_id, other_venue_id)
            
            if similarity >= min_similarity:
                similarities.append(
                    SimilarityScore(
                        id1=venue_id,
                        id2=other_venue_id,
                        similarity=similarity,
                        method="content_based_venue"
                    )
                )
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_k]
    
    def recommend_concerts_by_artist_preference(
        self,
        preferred_artist_ids: List[str],
        top_k: int = 10,
        exclude_concert_ids: Optional[Set[str]] = None
    ) -> RecommendationResult:
        """
        Recommend concerts based on artist preferences.
        
        Finds concerts featuring artists similar to the user's preferred artists.
        
        Args:
            preferred_artist_ids: List of artist IDs the user likes
            top_k: Number of recommendations to return
            exclude_concert_ids: Concert IDs to exclude from recommendations
            
        Returns:
            Recommendation result with scored concerts
        """
        if exclude_concert_ids is None:
            exclude_concert_ids = set()
        
        # Find similar artists for each preferred artist
        similar_artists: Dict[str, float] = {}
        
        for artist_id in preferred_artist_ids:
            similar = self.find_similar_artists(artist_id, top_k=20)
            for sim in similar:
                other_artist_id = sim.id2
                # Accumulate similarity scores
                if other_artist_id not in similar_artists:
                    similar_artists[other_artist_id] = 0.0
                similar_artists[other_artist_id] = max(
                    similar_artists[other_artist_id],
                    sim.similarity
                )
        
        # Also include the preferred artists themselves
        for artist_id in preferred_artist_ids:
            if artist_id in self.artists:
                similar_artists[artist_id] = 1.0
        
        # Find concerts featuring these artists
        concert_scores: Dict[str, float] = {}
        
        for concert_id, concert in self.concerts.items():
            if concert_id in exclude_concert_ids:
                continue
            
            if concert.artist_id in similar_artists:
                artist_similarity = similar_artists[concert.artist_id]
                concert_scores[concert_id] = artist_similarity
        
        # Create recommendations
        recommendations = []
        for concert_id, score in concert_scores.items():
            concert = self.concerts[concert_id]
            artist = self.artists.get(concert.artist_id)
            
            reasoning = f"Artist match"
            if artist:
                reasoning = f"Similar to your preferred artists (genre: {', '.join(artist.genre[:2])})"
            
            recommendations.append(
                RecommendationScore(
                    item_id=concert_id,
                    item_type="concert",
                    score=score,
                    confidence=min(len(preferred_artist_ids) / 5.0, 1.0),
                    reasoning=reasoning,
                    metadata={
                        "artist_id": concert.artist_id,
                        "venue_id": concert.venue_id
                    }
                )
            )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return RecommendationResult(
            user_id="content_based",
            recommendations=recommendations[:top_k],
            algorithm="content_based_artist",
            total_candidates=len(concert_scores)
        )
    
    def recommend_concerts_by_venue_preference(
        self,
        preferred_venue_ids: List[str],
        top_k: int = 10,
        exclude_concert_ids: Optional[Set[str]] = None
    ) -> RecommendationResult:
        """
        Recommend concerts based on venue preferences.
        
        Finds concerts at venues similar to the user's preferred venues.
        
        Args:
            preferred_venue_ids: List of venue IDs the user likes
            top_k: Number of recommendations to return
            exclude_concert_ids: Concert IDs to exclude from recommendations
            
        Returns:
            Recommendation result with scored concerts
        """
        if exclude_concert_ids is None:
            exclude_concert_ids = set()
        
        # Find similar venues for each preferred venue
        similar_venues: Dict[str, float] = {}
        
        for venue_id in preferred_venue_ids:
            similar = self.find_similar_venues(venue_id, top_k=20)
            for sim in similar:
                other_venue_id = sim.id2
                # Accumulate similarity scores
                if other_venue_id not in similar_venues:
                    similar_venues[other_venue_id] = 0.0
                similar_venues[other_venue_id] = max(
                    similar_venues[other_venue_id],
                    sim.similarity
                )
        
        # Also include the preferred venues themselves
        for venue_id in preferred_venue_ids:
            if venue_id in self.venues:
                similar_venues[venue_id] = 1.0
        
        # Find concerts at these venues
        concert_scores: Dict[str, float] = {}
        
        for concert_id, concert in self.concerts.items():
            if concert_id in exclude_concert_ids:
                continue
            
            if concert.venue_id in similar_venues:
                venue_similarity = similar_venues[concert.venue_id]
                concert_scores[concert_id] = venue_similarity
        
        # Create recommendations
        recommendations = []
        for concert_id, score in concert_scores.items():
            concert = self.concerts[concert_id]
            venue = self.venues.get(concert.venue_id)
            
            reasoning = "Venue match"
            if venue:
                reasoning = f"Similar venue ({venue.venue_type}, {venue.location.city})"
            
            recommendations.append(
                RecommendationScore(
                    item_id=concert_id,
                    item_type="concert",
                    score=score,
                    confidence=min(len(preferred_venue_ids) / 5.0, 1.0),
                    reasoning=reasoning,
                    metadata={
                        "artist_id": concert.artist_id,
                        "venue_id": concert.venue_id
                    }
                )
            )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return RecommendationResult(
            user_id="content_based",
            recommendations=recommendations[:top_k],
            algorithm="content_based_venue",
            total_candidates=len(concert_scores)
        )
    
    def recommend_concerts_hybrid(
        self,
        preferred_artist_ids: List[str],
        preferred_venue_ids: List[str],
        top_k: int = 10,
        artist_weight: float = 0.6,
        venue_weight: float = 0.4,
        exclude_concert_ids: Optional[Set[str]] = None
    ) -> RecommendationResult:
        """
        Recommend concerts using hybrid content-based approach.
        
        Combines artist-based and venue-based recommendations with weights.
        
        Args:
            preferred_artist_ids: List of artist IDs the user likes
            preferred_venue_ids: List of venue IDs the user likes
            top_k: Number of recommendations to return
            artist_weight: Weight for artist-based recommendations
            venue_weight: Weight for venue-based recommendations
            exclude_concert_ids: Concert IDs to exclude
            
        Returns:
            Recommendation result with scored concerts
        """
        if exclude_concert_ids is None:
            exclude_concert_ids = set()
        
        # Get artist-based recommendations
        artist_recs = self.recommend_concerts_by_artist_preference(
            preferred_artist_ids,
            top_k=top_k * 2,
            exclude_concert_ids=exclude_concert_ids
        )
        
        # Get venue-based recommendations
        venue_recs = self.recommend_concerts_by_venue_preference(
            preferred_venue_ids,
            top_k=top_k * 2,
            exclude_concert_ids=exclude_concert_ids
        )
        
        # Combine scores
        combined_scores: Dict[str, Tuple[float, float]] = {}  # concert_id -> (score, confidence)
        
        # Add artist-based scores
        for rec in artist_recs.recommendations:
            combined_scores[rec.item_id] = (
                artist_weight * rec.score,
                rec.confidence
            )
        
        # Add venue-based scores
        for rec in venue_recs.recommendations:
            if rec.item_id in combined_scores:
                # Concert appears in both - combine scores
                existing_score, existing_conf = combined_scores[rec.item_id]
                combined_scores[rec.item_id] = (
                    existing_score + venue_weight * rec.score,
                    max(existing_conf, rec.confidence)
                )
            else:
                combined_scores[rec.item_id] = (
                    venue_weight * rec.score,
                    rec.confidence
                )
        
        # Create final recommendations
        recommendations = []
        for concert_id, (score, confidence) in combined_scores.items():
            concert = self.concerts[concert_id]
            
            recommendations.append(
                RecommendationScore(
                    item_id=concert_id,
                    item_type="concert",
                    score=score,
                    confidence=confidence,
                    reasoning="Combined artist and venue preferences",
                    metadata={
                        "artist_id": concert.artist_id,
                        "venue_id": concert.venue_id
                    }
                )
            )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return RecommendationResult(
            user_id="content_based_hybrid",
            recommendations=recommendations[:top_k],
            algorithm="content_based_hybrid",
            total_candidates=len(combined_scores)
        )
