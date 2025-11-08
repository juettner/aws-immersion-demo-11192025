"""
Basic tests for external API connectors.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from .base_client import APIClient, APIResponse, RateLimiter
from .spotify_client import SpotifyClient
from .ticketmaster_client import TicketmasterClient
from .ingestion_service import DataIngestionService, IngestionResult


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within the limit."""
        limiter = RateLimiter(requests_per_minute=60)  # 1 request per second
        
        # Should allow first request
        assert await limiter.acquire() is True
        
        # Should allow another request after some time
        await asyncio.sleep(0.1)
        assert await limiter.acquire() is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excessive_requests(self):
        """Test that rate limiter blocks excessive requests."""
        limiter = RateLimiter(requests_per_minute=1, burst_size=1)  # Very restrictive
        
        # Should allow first request
        assert await limiter.acquire() is True
        
        # Should block immediate second request
        assert await limiter.acquire() is False


class TestAPIClient:
    """Test base API client functionality."""
    
    class TestClient(APIClient):
        """Test implementation of APIClient."""
        
        def get_auth_headers(self):
            return {"Authorization": "Bearer test-token"}
    
    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test API client initialization."""
        client = self.TestClient(
            base_url="https://api.example.com",
            api_key="test-key",
            requests_per_minute=100
        )
        
        assert client.base_url == "https://api.example.com"
        assert client.api_key == "test-key"
        assert client.retry_attempts == 3
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_auth_headers(self):
        """Test API client authentication headers."""
        client = self.TestClient(base_url="https://api.example.com")
        
        headers = client.get_default_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/json"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_retry_logic_server_error(self):
        """Test retry logic for server errors (5xx)."""
        client = self.TestClient(
            base_url="https://api.example.com",
            retry_attempts=3,
            retry_backoff=0.1
        )
        
        # Mock httpx client to simulate server errors
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_response.json.return_value = {"error": "Internal Server Error"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        response = await client.get("/test")
        
        assert response.success is False
        assert response.error == "Internal Server Error"
        assert response.status_code == 500
        
        # Verify retry attempts (should be called 3 times)
        assert client.client.request.call_count == 3
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_retry_logic_timeout(self):
        """Test retry logic for timeout errors."""
        import httpx
        
        client = self.TestClient(
            base_url="https://api.example.com",
            retry_attempts=2,
            retry_backoff=0.1
        )
        
        # Mock httpx client to simulate timeout
        client.client.request = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        
        response = await client.get("/test")
        
        assert response.success is False
        assert response.error == "Request timeout"
        
        # Verify retry attempts (should be called 2 times)
        assert client.client.request.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_rate_limit_handling(self):
        """Test rate limit handling with 429 status code."""
        client = self.TestClient(
            base_url="https://api.example.com",
            retry_attempts=2,
            retry_backoff=0.1
        )
        
        # Mock responses: first 429, then success
        mock_rate_limit_response = MagicMock()
        mock_rate_limit_response.is_success = False
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {"Retry-After": "1"}
        
        mock_success_response = MagicMock()
        mock_success_response.is_success = True
        mock_success_response.status_code = 200
        mock_success_response.headers = {}
        mock_success_response.json.return_value = {"data": "success"}
        
        client.client.request = AsyncMock(side_effect=[mock_rate_limit_response, mock_success_response])
        
        response = await client.get("/test")
        
        assert response.success is True
        assert response.data == {"data": "success"}
        assert response.status_code == 200
        
        # Verify both calls were made
        assert client.client.request.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_client_error_no_retry(self):
        """Test that client errors (4xx) are not retried."""
        client = self.TestClient(
            base_url="https://api.example.com",
            retry_attempts=3
        )
        
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.json.return_value = {"error": "Not Found"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        response = await client.get("/test")
        
        assert response.success is False
        assert response.error == "Not Found"
        assert response.status_code == 404
        
        # Verify only one call was made (no retries for 4xx)
        assert client.client.request.call_count == 1
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_api_client_network_error_retry(self):
        """Test retry logic for network errors."""
        import httpx
        
        client = self.TestClient(
            base_url="https://api.example.com",
            retry_attempts=2,
            retry_backoff=0.1
        )
        
        # Mock network error
        client.client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        response = await client.get("/test")
        
        assert response.success is False
        assert "Connection failed" in response.error
        
        # Verify retry attempts
        assert client.client.request.call_count == 2
        
        await client.close()


class TestSpotifyClient:
    """Test Spotify client functionality."""
    
    @pytest.mark.asyncio
    async def test_spotify_client_initialization(self):
        """Test Spotify client initialization."""
        client = SpotifyClient(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        assert client.client_id == "test-client-id"
        assert client.client_secret == "test-client-secret"
        assert client.base_url == "https://api.spotify.com/v1"
        
        await client.close()
    
    def test_transform_artist_data(self):
        """Test Spotify artist data transformation."""
        client = SpotifyClient(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Sample Spotify artist data
        spotify_data = {
            "id": "4Z8W4fKeB5YxbusRsdQVPb",
            "name": "Radiohead",
            "genres": ["alternative rock", "art rock", "electronic"],
            "popularity": 85,
            "followers": {"total": 4500000},
            "external_urls": {"spotify": "https://open.spotify.com/artist/4Z8W4fKeB5YxbusRsdQVPb"},
            "images": []
        }
        
        normalized = client._transform_artist_data(spotify_data)
        
        assert normalized["artist_id"] == "spotify_4Z8W4fKeB5YxbusRsdQVPb"
        assert normalized["name"] == "Radiohead"
        assert normalized["genre"] == ["alternative rock", "art rock", "electronic"]
        assert normalized["popularity_score"] == 85.0
        assert normalized["spotify_id"] == "4Z8W4fKeB5YxbusRsdQVPb"
        assert normalized["source"] == "spotify"


class TestTicketmasterClient:
    """Test Ticketmaster client functionality."""
    
    @pytest.mark.asyncio
    async def test_ticketmaster_client_initialization(self):
        """Test Ticketmaster client initialization."""
        client = TicketmasterClient(api_key="test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://app.ticketmaster.com/discovery/v2"
        
        await client.close()
    
    def test_transform_venue_data(self):
        """Test Ticketmaster venue data transformation."""
        client = TicketmasterClient(api_key="test-api-key")
        
        # Sample Ticketmaster venue data
        ticketmaster_data = {
            "id": "KovZpZAEkJ7A",
            "name": "Madison Square Garden",
            "type": "venue",
            "address": {"line1": "4 Pennsylvania Plaza"},
            "city": {"name": "New York"},
            "state": {"stateCode": "NY"},
            "country": {"countryCode": "US"},
            "location": {"latitude": 40.7505, "longitude": -73.9934},
            "timezone": "America/New_York"
        }
        
        normalized = client._transform_venue_data(ticketmaster_data)
        
        assert normalized["venue_id"] == "ticketmaster_KovZpZAEkJ7A"
        assert normalized["name"] == "Madison Square Garden"
        assert normalized["location"]["city"] == "New York"
        assert normalized["location"]["state"] == "NY"
        assert normalized["location"]["latitude"] == 40.7505
        assert normalized["ticketmaster_id"] == "KovZpZAEkJ7A"
        assert normalized["source"] == "ticketmaster"
    
    def test_transform_event_data(self):
        """Test Ticketmaster event data transformation."""
        client = TicketmasterClient(api_key="test-api-key")
        
        # Sample Ticketmaster event data
        ticketmaster_data = {
            "id": "1AwZjZ8G6kd1234",
            "name": "Radiohead Concert",
            "type": "event",
            "dates": {
                "start": {
                    "dateTime": "2024-07-15T20:00:00Z",
                    "localDate": "2024-07-15"
                }
            },
            "priceRanges": [
                {"type": "standard", "min": 50.0, "max": 150.0}
            ],
            "_embedded": {
                "venues": [{"id": "KovZpZAEkJ7A"}],
                "attractions": [{"id": "K8vZ917G1V7"}]
            }
        }
        
        normalized = client._transform_event_data(ticketmaster_data)
        
        assert normalized["concert_id"] == "ticketmaster_1AwZjZ8G6kd1234"
        assert normalized["venue_id"] == "ticketmaster_KovZpZAEkJ7A"
        assert normalized["artist_id"] == "ticketmaster_K8vZ917G1V7"
        assert "2024-07-15T20:00:00" in normalized["event_date"]
        assert normalized["ticket_prices"]["standard"] == 100.0  # Average of min/max
        assert normalized["source"] == "ticketmaster"


class TestIngestionService:
    """Test data ingestion service functionality."""
    
    @pytest.mark.asyncio
    async def test_ingestion_service_initialization(self):
        """Test ingestion service initialization."""
        service = DataIngestionService()
        
        # Mock the settings to avoid requiring actual API keys
        with patch('src.services.external_apis.ingestion_service.settings') as mock_settings:
            mock_settings.external_apis.spotify_client_id = "test-id"
            mock_settings.external_apis.spotify_client_secret = "test-secret"
            mock_settings.external_apis.ticketmaster_api_key = "test-key"
            mock_settings.external_apis.spotify_base_url = "https://api.spotify.com/v1"
            mock_settings.external_apis.ticketmaster_base_url = "https://app.ticketmaster.com/discovery/v2"
            mock_settings.external_apis.api_rate_limit_requests = 100
            mock_settings.external_apis.api_retry_attempts = 3
            mock_settings.external_apis.api_retry_backoff = 1.0
            
            await service.initialize_clients()
            
            assert service.spotify_client is not None
            assert service.ticketmaster_client is not None
            
            await service.close_clients()
    
    @pytest.mark.asyncio
    async def test_ingestion_service_missing_credentials(self):
        """Test ingestion service with missing credentials."""
        service = DataIngestionService()
        
        # Mock settings with missing credentials
        with patch('src.services.external_apis.ingestion_service.settings') as mock_settings:
            mock_settings.external_apis.spotify_client_id = None
            mock_settings.external_apis.spotify_client_secret = None
            mock_settings.external_apis.ticketmaster_api_key = None
            mock_settings.external_apis.spotify_base_url = "https://api.spotify.com/v1"
            mock_settings.external_apis.ticketmaster_base_url = "https://app.ticketmaster.com/discovery/v2"
            mock_settings.external_apis.api_rate_limit_requests = 100
            mock_settings.external_apis.api_retry_attempts = 3
            mock_settings.external_apis.api_retry_backoff = 1.0
            
            await service.initialize_clients()
            
            # Should handle missing credentials gracefully
            assert service.spotify_client is None
            assert service.ticketmaster_client is None
            
            await service.close_clients()
    
    @pytest.mark.asyncio
    async def test_ingest_artist_data_no_client(self):
        """Test artist data ingestion when Spotify client is not available."""
        service = DataIngestionService()
        # Don't initialize clients
        
        result = await service.ingest_artist_data(["rock"])
        
        assert result.success is False
        assert result.source == "spotify"
        assert result.data_type == "artists"
        assert "Spotify client not initialized" in result.errors
    
    @pytest.mark.asyncio
    async def test_ingest_artist_data_api_failure(self):
        """Test artist data ingestion with API failures."""
        service = DataIngestionService()
        
        # Mock Spotify client with failing search
        mock_spotify = AsyncMock()
        mock_spotify.search_artists.return_value = APIResponse(
            success=False,
            error="API rate limit exceeded"
        )
        service.spotify_client = mock_spotify
        
        result = await service.ingest_artist_data(["rock"])
        
        assert result.success is False
        assert result.source == "spotify"
        assert result.data_type == "artists"
        assert len(result.errors) > 0
        assert "API rate limit exceeded" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_ingest_artist_data_partial_success(self):
        """Test artist data ingestion with partial success."""
        service = DataIngestionService()
        
        # Mock Spotify client with mixed results
        mock_spotify = AsyncMock()
        
        # First query succeeds, second fails
        success_response = APIResponse(
            success=True,
            data={
                "normalized_artists": [
                    {"artist_id": "spotify_123", "name": "Test Artist 1"},
                    {"artist_id": "spotify_124", "name": "Test Artist 2"}
                ],
                "artists": {"total": 2}
            }
        )
        
        failure_response = APIResponse(
            success=False,
            error="Network timeout"
        )
        
        mock_spotify.search_artists.side_effect = [success_response, failure_response]
        service.spotify_client = mock_spotify
        
        result = await service.ingest_artist_data(["rock", "jazz"])
        
        assert result.success is False  # Because there were errors
        assert result.source == "spotify"
        assert result.data_type == "artists"
        assert result.records_processed == 2
        assert result.records_successful == 2
        assert len(result.data) == 2
        assert len(result.errors) == 1
        assert "Network timeout" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_ingest_venue_data_no_client(self):
        """Test venue data ingestion when Ticketmaster client is not available."""
        service = DataIngestionService()
        # Don't initialize clients
        
        result = await service.ingest_venue_data(["New York"])
        
        assert result.success is False
        assert result.source == "ticketmaster"
        assert result.data_type == "venues"
        assert "Ticketmaster client not initialized" in result.errors
    
    @pytest.mark.asyncio
    async def test_comprehensive_ingestion_exception_handling(self):
        """Test comprehensive ingestion with exception handling."""
        service = DataIngestionService()
        
        # Mock clients that raise exceptions
        mock_spotify = AsyncMock()
        mock_spotify.search_artists.side_effect = Exception("Unexpected error")
        service.spotify_client = mock_spotify
        
        mock_ticketmaster = AsyncMock()
        mock_ticketmaster.search_venues.side_effect = Exception("Connection error")
        service.ticketmaster_client = mock_ticketmaster
        
        results = await service.ingest_comprehensive_data()
        
        # Should handle exceptions gracefully
        assert "artists" in results
        assert "venues" in results
        
        # Both should have failed due to exceptions
        for result in results.values():
            assert result.success is False
            assert len(result.errors) > 0
    
    def test_ingestion_result(self):
        """Test ingestion result creation."""
        result = IngestionResult(
            success=True,
            source="spotify",
            data_type="artists",
            records_processed=10,
            records_successful=8,
            records_failed=2,
            errors=["Error 1", "Error 2"],
            data=[{"artist_id": "test"}]
        )
        
        assert result.success is True
        assert result.source == "spotify"
        assert result.data_type == "artists"
        assert result.records_processed == 10
        assert result.records_successful == 8
        assert result.records_failed == 2
        assert len(result.errors) == 2
        assert len(result.data) == 1
        
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["records_processed"] == 10
        assert result_dict["data_count"] == 1


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])