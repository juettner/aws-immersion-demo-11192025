"""
External Data Enrichment Service for Concert AI Chatbot.

This service provides real-time data fetching from external APIs with caching,
validation, and fallback to local data sources.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import structlog
from pydantic import BaseModel, Field

from .external_apis.spotify_client import SpotifyClient
from .external_apis.ticketmaster_client import TicketmasterClient
from ..config.settings import Settings

logger = structlog.get_logger(__name__)


class CachedData(BaseModel):
    """Cached data entry with expiration."""
    data: Dict[str, Any]
    cached_at: datetime
    expires_at: datetime
    source: str


class EnrichmentResult(BaseModel):
    """Result of data enrichment operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    source: str  # "external", "cache", "local_fallback"
    error: Optional[str] = None
    cached: bool = False


class ExternalDataEnrichmentService:
    """
    Service for enriching concert data with real-time information from external APIs.
    
    Features:
    - Fetches artist and venue data from Spotify and Ticketmaster
    - Caches frequently accessed data to reduce API calls
    - Validates and normalizes external data
    - Falls back to local data when external sources are unavailable
    """
    
    def __init__(
        self,
        spotify_client: Optional[SpotifyClient] = None,
        ticketmaster_client: Optional[TicketmasterClient] = None,
        cache_ttl_minutes: int = 60,
        max_cache_size: int = 1000
    ):
        """
        Initialize the external data enrichment service.
        
        Args:
            spotify_client: Spotify API client instance
            ticketmaster_client: Ticketmaster API client instance
            cache_ttl_minutes: Time-to-live for cached data in minutes
            max_cache_size: Maximum number of entries in cache
        """
        self.spotify_client = spotify_client
        self.ticketmaster_client = ticketmaster_client
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.max_cache_size = max_cache_size
        
        # In-memory cache: key -> CachedData
        self._cache: Dict[str, CachedData] = {}
        self._cache_access_times: Dict[str, datetime] = {}
        
        self.logger = structlog.get_logger("ExternalDataEnrichmentService")
    
    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "ExternalDataEnrichmentService":
        """
        Create service instance from settings.
        
        Args:
            settings: Application settings (loads from env if not provided)
            
        Returns:
            ExternalDataEnrichmentService instance
        """
        if settings is None:
            settings = Settings.from_env()
        
        # Initialize API clients if credentials are available
        spotify_client = None
        if settings.external_api.spotify_client_id and settings.external_api.spotify_client_secret:
            spotify_client = SpotifyClient(
                client_id=settings.external_api.spotify_client_id,
                client_secret=settings.external_api.spotify_client_secret
            )
        
        ticketmaster_client = None
        if settings.external_api.ticketmaster_api_key:
            ticketmaster_client = TicketmasterClient(
                api_key=settings.external_api.ticketmaster_api_key
            )
        
        return cls(
            spotify_client=spotify_client,
            ticketmaster_client=ticketmaster_client
        )
    
    def _generate_cache_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Generate a unique cache key for the request."""
        key_parts = [data_type, identifier]
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache if available and not expired."""
        if cache_key not in self._cache:
            return None
        
        cached_entry = self._cache[cache_key]
        
        # Check if expired
        if datetime.utcnow() > cached_entry.expires_at:
            self.logger.debug("Cache entry expired", cache_key=cache_key)
            del self._cache[cache_key]
            if cache_key in self._cache_access_times:
                del self._cache_access_times[cache_key]
            return None
        
        # Update access time
        self._cache_access_times[cache_key] = datetime.utcnow()
        
        self.logger.debug("Cache hit", cache_key=cache_key)
        return cached_entry.data
    
    def _add_to_cache(self, cache_key: str, data: Dict[str, Any], source: str) -> None:
        """Add data to cache with expiration."""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_cache_size:
            self._evict_oldest_cache_entries(count=int(self.max_cache_size * 0.1))
        
        now = datetime.utcnow()
        cached_entry = CachedData(
            data=data,
            cached_at=now,
            expires_at=now + self.cache_ttl,
            source=source
        )
        
        self._cache[cache_key] = cached_entry
        self._cache_access_times[cache_key] = now
        
        self.logger.debug("Added to cache", cache_key=cache_key, source=source)
    
    def _evict_oldest_cache_entries(self, count: int = 1) -> None:
        """Evict the oldest cache entries based on access time."""
        if not self._cache_access_times:
            return
        
        # Sort by access time and remove oldest
        sorted_keys = sorted(
            self._cache_access_times.items(),
            key=lambda x: x[1]
        )
        
        for cache_key, _ in sorted_keys[:count]:
            if cache_key in self._cache:
                del self._cache[cache_key]
            if cache_key in self._cache_access_times:
                del self._cache_access_times[cache_key]
        
        self.logger.debug("Evicted cache entries", count=count)
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_access_times.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_cache_size,
            "ttl_minutes": self.cache_ttl.total_seconds() / 60,
            "entries": [
                {
                    "key": key,
                    "source": entry.source,
                    "cached_at": entry.cached_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat()
                }
                for key, entry in list(self._cache.items())[:10]  # Show first 10
            ]
        }

    async def enrich_artist_data(
        self,
        artist_name: Optional[str] = None,
        artist_id: Optional[str] = None,
        use_cache: bool = True
    ) -> EnrichmentResult:
        """
        Enrich artist data from external sources.
        
        Args:
            artist_name: Artist name to search for
            artist_id: Spotify artist ID (if known)
            use_cache: Whether to use cached data
            
        Returns:
            EnrichmentResult with artist data
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            "artist",
            artist_id or artist_name or "",
            name=artist_name
        )
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return EnrichmentResult(
                    success=True,
                    data=cached_data,
                    source="cache",
                    cached=True
                )
        
        # Try to fetch from Spotify
        if self.spotify_client:
            try:
                if artist_id:
                    # Fetch by ID
                    response = await self.spotify_client.get_artist(artist_id)
                elif artist_name:
                    # Search by name
                    response = await self.spotify_client.search_artists(
                        query=artist_name,
                        limit=1
                    )
                else:
                    return EnrichmentResult(
                        success=False,
                        source="external",
                        error="Either artist_name or artist_id must be provided"
                    )
                
                if response.success and response.data:
                    # Extract normalized artist data
                    if artist_id and "normalized_artist" in response.data:
                        artist_data = response.data["normalized_artist"]
                    elif "normalized_artists" in response.data and response.data["normalized_artists"]:
                        artist_data = response.data["normalized_artists"][0]
                    else:
                        artist_data = response.data
                    
                    # Validate and normalize
                    validated_data = self._validate_artist_data(artist_data)
                    
                    # Cache the result
                    self._add_to_cache(cache_key, validated_data, "spotify")
                    
                    return EnrichmentResult(
                        success=True,
                        data=validated_data,
                        source="external",
                        cached=False
                    )
                else:
                    self.logger.warning(
                        "Failed to fetch artist from Spotify",
                        artist_name=artist_name,
                        artist_id=artist_id,
                        error=response.error
                    )
            
            except Exception as e:
                self.logger.error(
                    "Error fetching artist from Spotify",
                    artist_name=artist_name,
                    artist_id=artist_id,
                    error=str(e)
                )
        
        # Fallback to local data (placeholder - would query local database)
        return self._fallback_artist_data(artist_name, artist_id)
    
    async def enrich_venue_data(
        self,
        venue_name: Optional[str] = None,
        venue_id: Optional[str] = None,
        city: Optional[str] = None,
        use_cache: bool = True
    ) -> EnrichmentResult:
        """
        Enrich venue data from external sources.
        
        Args:
            venue_name: Venue name to search for
            venue_id: Ticketmaster venue ID (if known)
            city: City to narrow search
            use_cache: Whether to use cached data
            
        Returns:
            EnrichmentResult with venue data
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            "venue",
            venue_id or venue_name or "",
            name=venue_name,
            city=city
        )
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return EnrichmentResult(
                    success=True,
                    data=cached_data,
                    source="cache",
                    cached=True
                )
        
        # Try to fetch from Ticketmaster
        if self.ticketmaster_client:
            try:
                if venue_id:
                    # Fetch by ID
                    response = await self.ticketmaster_client.get_venue(venue_id)
                elif venue_name:
                    # Search by name
                    response = await self.ticketmaster_client.search_venues(
                        keyword=venue_name,
                        city=city,
                        size=1
                    )
                else:
                    return EnrichmentResult(
                        success=False,
                        source="external",
                        error="Either venue_name or venue_id must be provided"
                    )
                
                if response.success and response.data:
                    # Extract normalized venue data
                    if venue_id and "normalized_venue" in response.data:
                        venue_data = response.data["normalized_venue"]
                    elif "normalized_venues" in response.data and response.data["normalized_venues"]:
                        venue_data = response.data["normalized_venues"][0]
                    else:
                        venue_data = response.data
                    
                    # Validate and normalize
                    validated_data = self._validate_venue_data(venue_data)
                    
                    # Cache the result
                    self._add_to_cache(cache_key, validated_data, "ticketmaster")
                    
                    return EnrichmentResult(
                        success=True,
                        data=validated_data,
                        source="external",
                        cached=False
                    )
                else:
                    self.logger.warning(
                        "Failed to fetch venue from Ticketmaster",
                        venue_name=venue_name,
                        venue_id=venue_id,
                        error=response.error
                    )
            
            except Exception as e:
                self.logger.error(
                    "Error fetching venue from Ticketmaster",
                    venue_name=venue_name,
                    venue_id=venue_id,
                    error=str(e)
                )
        
        # Fallback to local data
        return self._fallback_venue_data(venue_name, venue_id, city)
    
    async def enrich_concert_data(
        self,
        artist_name: Optional[str] = None,
        venue_name: Optional[str] = None,
        city: Optional[str] = None,
        use_cache: bool = True
    ) -> EnrichmentResult:
        """
        Enrich concert/event data from external sources.
        
        Args:
            artist_name: Artist name to search for
            venue_name: Venue name to search for
            city: City to narrow search
            use_cache: Whether to use cached data
            
        Returns:
            EnrichmentResult with concert data
        """
        # Generate cache key
        cache_key = self._generate_cache_key(
            "concert",
            f"{artist_name}_{venue_name}_{city}",
            artist=artist_name,
            venue=venue_name,
            city=city
        )
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return EnrichmentResult(
                    success=True,
                    data=cached_data,
                    source="cache",
                    cached=True
                )
        
        # Try to fetch from Ticketmaster
        if self.ticketmaster_client:
            try:
                response = await self.ticketmaster_client.search_events(
                    keyword=artist_name,
                    city=city,
                    classification_name="Music",
                    size=10
                )
                
                if response.success and response.data:
                    # Extract normalized events
                    events = response.data.get("normalized_events", [])
                    
                    if events:
                        # Filter by venue if specified
                        if venue_name:
                            events = [
                                e for e in events
                                if venue_name.lower() in e.get("raw_data", {}).get("name", "").lower()
                            ]
                        
                        concert_data = {
                            "events": events,
                            "count": len(events),
                            "source": "ticketmaster"
                        }
                        
                        # Cache the result
                        self._add_to_cache(cache_key, concert_data, "ticketmaster")
                        
                        return EnrichmentResult(
                            success=True,
                            data=concert_data,
                            source="external",
                            cached=False
                        )
                else:
                    self.logger.warning(
                        "Failed to fetch concerts from Ticketmaster",
                        artist_name=artist_name,
                        venue_name=venue_name,
                        error=response.error
                    )
            
            except Exception as e:
                self.logger.error(
                    "Error fetching concerts from Ticketmaster",
                    artist_name=artist_name,
                    venue_name=venue_name,
                    error=str(e)
                )
        
        # Fallback to local data
        return self._fallback_concert_data(artist_name, venue_name, city)
    
    def _validate_artist_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize artist data."""
        validated = {
            "artist_id": data.get("artist_id", ""),
            "name": data.get("name", "Unknown Artist"),
            "genre": data.get("genre", []),
            "popularity_score": float(data.get("popularity_score", 0)),
            "spotify_id": data.get("spotify_id"),
            "source": data.get("source", "external"),
            "enriched_at": datetime.utcnow().isoformat()
        }
        
        # Add additional metadata if available
        if "raw_data" in data:
            validated["metadata"] = data["raw_data"]
        
        return validated
    
    def _validate_venue_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize venue data."""
        validated = {
            "venue_id": data.get("venue_id", ""),
            "name": data.get("name", "Unknown Venue"),
            "city": data.get("city", ""),
            "state": data.get("state"),
            "country": data.get("country", ""),
            "capacity": int(data.get("capacity", 0)),
            "venue_type": data.get("venue_type", "other"),
            "source": data.get("source", "external"),
            "enriched_at": datetime.utcnow().isoformat()
        }
        
        return validated
    
    def _fallback_artist_data(
        self,
        artist_name: Optional[str],
        artist_id: Optional[str]
    ) -> EnrichmentResult:
        """Fallback to local artist data when external sources fail."""
        self.logger.info(
            "Using fallback artist data",
            artist_name=artist_name,
            artist_id=artist_id
        )
        
        # Return placeholder data indicating local fallback
        fallback_data = {
            "artist_id": artist_id or f"local_{artist_name}",
            "name": artist_name or "Unknown Artist",
            "genre": [],
            "popularity_score": 50.0,
            "source": "local_fallback",
            "enriched_at": datetime.utcnow().isoformat(),
            "note": "External data unavailable, using local fallback"
        }
        
        return EnrichmentResult(
            success=True,
            data=fallback_data,
            source="local_fallback",
            cached=False
        )
    
    def _fallback_venue_data(
        self,
        venue_name: Optional[str],
        venue_id: Optional[str],
        city: Optional[str]
    ) -> EnrichmentResult:
        """Fallback to local venue data when external sources fail."""
        self.logger.info(
            "Using fallback venue data",
            venue_name=venue_name,
            venue_id=venue_id,
            city=city
        )
        
        # Return placeholder data indicating local fallback
        fallback_data = {
            "venue_id": venue_id or f"local_{venue_name}",
            "name": venue_name or "Unknown Venue",
            "city": city or "",
            "state": None,
            "country": "",
            "capacity": 1000,
            "venue_type": "other",
            "source": "local_fallback",
            "enriched_at": datetime.utcnow().isoformat(),
            "note": "External data unavailable, using local fallback"
        }
        
        return EnrichmentResult(
            success=True,
            data=fallback_data,
            source="local_fallback",
            cached=False
        )
    
    def _fallback_concert_data(
        self,
        artist_name: Optional[str],
        venue_name: Optional[str],
        city: Optional[str]
    ) -> EnrichmentResult:
        """Fallback to local concert data when external sources fail."""
        self.logger.info(
            "Using fallback concert data",
            artist_name=artist_name,
            venue_name=venue_name,
            city=city
        )
        
        # Return placeholder data indicating local fallback
        fallback_data = {
            "events": [],
            "count": 0,
            "source": "local_fallback",
            "enriched_at": datetime.utcnow().isoformat(),
            "note": "External data unavailable, using local fallback"
        }
        
        return EnrichmentResult(
            success=True,
            data=fallback_data,
            source="local_fallback",
            cached=False
        )
    
    async def close(self) -> None:
        """Close API clients and cleanup resources."""
        if self.spotify_client:
            await self.spotify_client.close()
        if self.ticketmaster_client:
            await self.ticketmaster_client.close()
        
        self.logger.info("External data enrichment service closed")
