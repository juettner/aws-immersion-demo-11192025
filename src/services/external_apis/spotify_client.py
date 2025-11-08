"""
Spotify API client for artist data ingestion.
"""
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog
from pydantic import BaseModel

from .base_client import APIClient, APIResponse
from ...models.artist import Artist

logger = structlog.get_logger(__name__)


class SpotifyTokenResponse(BaseModel):
    """Spotify OAuth token response."""
    access_token: str
    token_type: str
    expires_in: int


class SpotifyArtistData(BaseModel):
    """Raw Spotify artist data structure."""
    id: str
    name: str
    genres: List[str]
    popularity: int
    followers: Dict[str, int]
    external_urls: Dict[str, str]
    images: List[Dict[str, Any]]


class SpotifyClient(APIClient):
    """Spotify Web API client for artist data retrieval."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.spotify.com/v1",
        requests_per_minute: int = 100,
        retry_attempts: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(
            base_url=base_url,
            requests_per_minute=requests_per_minute,
            retry_attempts=retry_attempts,
            retry_backoff=retry_backoff
        )
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        self.logger = structlog.get_logger("SpotifyClient")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Spotify API."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    async def _get_client_credentials_token(self) -> bool:
        """Get access token using client credentials flow."""
        try:
            # Encode client credentials
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make token request to Spotify accounts service
            token_url = "https://accounts.spotify.com/api/token"
            data = {"grant_type": "client_credentials"}
            
            response = await self.client.post(
                token_url,
                data=data,
                headers=headers
            )
            
            if response.is_success:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data["expires_in"]
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 60s buffer
                
                self.logger.info("Successfully obtained Spotify access token")
                return True
            else:
                self.logger.error(
                    "Failed to obtain Spotify access token",
                    status_code=response.status_code,
                    response=response.text
                )
                return False
                
        except Exception as e:
            self.logger.error("Error obtaining Spotify access token", error=str(e))
            return False
    
    async def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.access_token or not self.token_expires_at:
            return await self._get_client_credentials_token()
        
        if datetime.utcnow() >= self.token_expires_at:
            self.logger.info("Access token expired, refreshing")
            return await self._get_client_credentials_token()
        
        return True
    
    async def search_artists(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> APIResponse:
        """
        Search for artists on Spotify.
        
        Args:
            query: Search query string
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            
        Returns:
            APIResponse containing search results
        """
        if not await self._ensure_valid_token():
            return APIResponse(success=False, error="Failed to obtain access token")
        
        params = {
            "q": query,
            "type": "artist",
            "limit": min(limit, 50),
            "offset": offset
        }
        
        response = await self.get("search", params=params)
        
        if response.success and response.data:
            # Transform the response to include normalized artist data
            artists_data = response.data.get("artists", {}).get("items", [])
            normalized_artists = []
            
            for artist_data in artists_data:
                try:
                    normalized_artist = self._transform_artist_data(artist_data)
                    normalized_artists.append(normalized_artist)
                except Exception as e:
                    self.logger.warning(
                        "Failed to transform artist data",
                        artist_id=artist_data.get("id"),
                        error=str(e)
                    )
            
            response.data["normalized_artists"] = normalized_artists
        
        return response
    
    async def get_artist(self, artist_id: str) -> APIResponse:
        """
        Get detailed information about a specific artist.
        
        Args:
            artist_id: Spotify artist ID
            
        Returns:
            APIResponse containing artist details
        """
        if not await self._ensure_valid_token():
            return APIResponse(success=False, error="Failed to obtain access token")
        
        response = await self.get(f"artists/{artist_id}")
        
        if response.success and response.data:
            try:
                normalized_artist = self._transform_artist_data(response.data)
                response.data["normalized_artist"] = normalized_artist
            except Exception as e:
                self.logger.warning(
                    "Failed to transform artist data",
                    artist_id=artist_id,
                    error=str(e)
                )
        
        return response
    
    async def get_multiple_artists(self, artist_ids: List[str]) -> APIResponse:
        """
        Get information about multiple artists.
        
        Args:
            artist_ids: List of Spotify artist IDs (max 50)
            
        Returns:
            APIResponse containing multiple artist details
        """
        if not await self._ensure_valid_token():
            return APIResponse(success=False, error="Failed to obtain access token")
        
        if len(artist_ids) > 50:
            return APIResponse(success=False, error="Maximum 50 artist IDs allowed")
        
        params = {"ids": ",".join(artist_ids)}
        response = await self.get("artists", params=params)
        
        if response.success and response.data:
            artists_data = response.data.get("artists", [])
            normalized_artists = []
            
            for artist_data in artists_data:
                if artist_data:  # Spotify returns null for invalid IDs
                    try:
                        normalized_artist = self._transform_artist_data(artist_data)
                        normalized_artists.append(normalized_artist)
                    except Exception as e:
                        self.logger.warning(
                            "Failed to transform artist data",
                            artist_id=artist_data.get("id"),
                            error=str(e)
                        )
            
            response.data["normalized_artists"] = normalized_artists
        
        return response
    
    def _transform_artist_data(self, spotify_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Spotify artist data to our normalized format.
        
        Args:
            spotify_data: Raw Spotify artist data
            
        Returns:
            Normalized artist data dictionary
        """
        try:
            # Generate our internal artist ID
            artist_id = f"spotify_{spotify_data['id']}"
            
            # Extract basic information
            name = spotify_data.get("name", "").strip()
            genres = spotify_data.get("genres", [])
            popularity = spotify_data.get("popularity", 0)
            
            # Convert Spotify popularity (0-100) to our popularity score
            popularity_score = float(popularity)
            
            # Extract follower count for additional context
            followers = spotify_data.get("followers", {}).get("total", 0)
            
            # Create normalized artist data
            normalized_data = {
                "artist_id": artist_id,
                "name": name,
                "genre": genres,
                "popularity_score": popularity_score,
                "formation_date": None,  # Not available from Spotify API
                "members": [],  # Not available from Spotify API
                "spotify_id": spotify_data["id"],
                "source": "spotify",
                "raw_data": {
                    "followers": followers,
                    "external_urls": spotify_data.get("external_urls", {}),
                    "images": spotify_data.get("images", [])
                }
            }
            
            # Validate the data using our Artist model
            try:
                Artist(**normalized_data)
            except Exception as validation_error:
                self.logger.warning(
                    "Artist data validation failed",
                    artist_id=artist_id,
                    validation_error=str(validation_error)
                )
                # Continue with the data even if validation fails for logging purposes
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(
                "Failed to transform Spotify artist data",
                spotify_data=spotify_data,
                error=str(e)
            )
            raise
    
    async def get_artist_top_tracks(self, artist_id: str, market: str = "US") -> APIResponse:
        """
        Get an artist's top tracks.
        
        Args:
            artist_id: Spotify artist ID
            market: Market/country code (ISO 3166-1 alpha-2)
            
        Returns:
            APIResponse containing top tracks
        """
        if not await self._ensure_valid_token():
            return APIResponse(success=False, error="Failed to obtain access token")
        
        params = {"market": market}
        return await self.get(f"artists/{artist_id}/top-tracks", params=params)
    
    async def get_related_artists(self, artist_id: str) -> APIResponse:
        """
        Get artists related to a given artist.
        
        Args:
            artist_id: Spotify artist ID
            
        Returns:
            APIResponse containing related artists
        """
        if not await self._ensure_valid_token():
            return APIResponse(success=False, error="Failed to obtain access token")
        
        response = await self.get(f"artists/{artist_id}/related-artists")
        
        if response.success and response.data:
            artists_data = response.data.get("artists", [])
            normalized_artists = []
            
            for artist_data in artists_data:
                try:
                    normalized_artist = self._transform_artist_data(artist_data)
                    normalized_artists.append(normalized_artist)
                except Exception as e:
                    self.logger.warning(
                        "Failed to transform related artist data",
                        artist_id=artist_data.get("id"),
                        error=str(e)
                    )
            
            response.data["normalized_artists"] = normalized_artists
        
        return response