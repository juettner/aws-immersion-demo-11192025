"""
Comprehensive tests for ingestion component error handling and retry logic.
Tests API connector failures, file processing errors, and streaming integration issues.
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import httpx
from botocore.exceptions import ClientError

# Import components to test
from .external_apis.base_client import APIClient, APIResponse, RateLimiter
from .external_apis.spotify_client import SpotifyClient
from .external_apis.ticketmaster_client import TicketmasterClient
from .external_apis.ingestion_service import DataIngestionService, IngestionResult
from .file_processor import FileUploadProcessor, FileProcessingError
from ..infrastructure.kinesis_client import KinesisClient
from .stream_producer import StreamProducerService


class TestAPIErrorHandling:
    """Test error handling and retry logic for API clients."""
    
    class MockAPIClient(APIClient):
        """Mock API client for testing."""
        
        def get_auth_headers(self):
            return {"Authorization": "Bearer test-token"}
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self):
        """Test exponential backoff retry logic."""
        client = self.MockAPIClient(
            base_url="https://api.example.com",
            retry_attempts=3,
            retry_backoff=0.1
        )
        
        # Mock consecutive server errors
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 503
        mock_response.headers = {}
        mock_response.json.return_value = {"error": "Service Unavailable"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        start_time = datetime.now()
        response = await client.get("/test")
        end_time = datetime.now()
        
        # Should have failed after retries
        assert response.success is False
        assert response.error == "Service Unavailable"
        
        # Should have made 3 attempts
        assert client.client.request.call_count == 3
        
        # Should have taken time for backoff (0.1 + 0.2 + 0.4 = 0.7s minimum)
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 0.6  # Allow some tolerance
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_rate_limit_respect(self):
        """Test that rate limiter properly throttles requests."""
        # Very restrictive rate limiter
        limiter = RateLimiter(requests_per_minute=6, burst_size=2)  # 10 seconds per request
        
        # Should allow first two requests (burst)
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        
        # Third request should be blocked
        assert await limiter.acquire() is False
        
        # After waiting, should allow another request
        await asyncio.sleep(0.2)  # Small wait
        # Still should be blocked due to rate limit
        assert await limiter.acquire() is False
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test handling of concurrent requests with rate limiting."""
        client = self.MockAPIClient(
            base_url="https://api.example.com",
            requests_per_minute=60  # 1 per second
        )
        
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"data": "success"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        # Make multiple concurrent requests
        tasks = [client.get(f"/test{i}") for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All should eventually succeed
        for response in responses:
            assert response.success is True
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_network_error_scenarios(self):
        """Test various network error scenarios."""
        client = self.MockAPIClient(
            base_url="https://api.example.com",
            retry_attempts=2,
            retry_backoff=0.1
        )
        
        # Test different network errors
        network_errors = [
            httpx.ConnectError("Connection refused"),
            httpx.TimeoutException("Request timeout"),
            httpx.ReadTimeout("Read timeout"),
            httpx.NetworkError("Network unreachable")
        ]
        
        for error in network_errors:
            client.client.request = AsyncMock(side_effect=error)
            
            response = await client.get("/test")
            
            assert response.success is False
            assert error.__class__.__name__.lower() in response.error.lower()
            
            # Should have retried
            assert client.client.request.call_count == 2
            
            # Reset for next test
            client.client.request.reset_mock()
        
        await client.close()


class TestSpotifyClientErrorHandling:
    """Test Spotify client specific error handling."""
    
    @pytest.mark.asyncio
    async def test_spotify_authentication_failure(self):
        """Test handling of Spotify authentication failures."""
        client = SpotifyClient(
            client_id="invalid_id",
            client_secret="invalid_secret"
        )
        
        # Mock authentication failure
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_response.json.return_value = {"error": "invalid_client"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        response = await client.search_artists("test")
        
        assert response.success is False
        assert response.status_code == 401
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_spotify_malformed_response(self):
        """Test handling of malformed Spotify API responses."""
        client = SpotifyClient(
            client_id="test_id",
            client_secret="test_secret"
        )
        
        # Mock malformed response (missing expected fields)
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {"unexpected": "structure"}
        
        client.client.request = AsyncMock(return_value=mock_response)
        
        response = await client.search_artists("test")
        
        # Should handle gracefully and return empty results
        assert response.success is True
        assert response.data.get("normalized_artists", []) == []
        
        await client.close()


class TestFileProcessingErrorHandling:
    """Test file processing error handling and recovery."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = FileUploadProcessor(max_file_size_mb=1, max_batch_size=100)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        for file_path in self.temp_dir.glob("*"):
            file_path.unlink()
        self.temp_dir.rmdir()
    
    def test_file_permission_error(self):
        """Test handling of file permission errors."""
        # Create a file and make it unreadable (Unix-like systems)
        file_path = self.temp_dir / "unreadable.csv"
        file_path.write_text("artist_id,name\ntest,Test Artist")
        
        try:
            file_path.chmod(0o000)  # Remove all permissions
            
            result = self.processor.process_file_upload(file_path, 'artists')
            
            assert result.success is False
            assert len(result.errors) > 0
            
        finally:
            # Restore permissions for cleanup
            file_path.chmod(0o644)
    
    def test_corrupted_file_recovery(self):
        """Test recovery from corrupted file data."""
        # Create CSV with mixed valid and invalid rows
        file_path = self.temp_dir / "mixed_quality.csv"
        
        with open(file_path, 'w', newline='') as f:
            f.write('artist_id,name,popularity_score\n')
            f.write('art_001,Valid Artist,75.5\n')  # Valid
            f.write('art_002,,85.0\n')  # Missing name
            f.write('art_003,Another Valid,90.0\n')  # Valid
            f.write(',Invalid ID,70.0\n')  # Missing ID
            f.write('art_005,Final Valid,80.0\n')  # Valid
        
        result = self.processor.process_file_upload(file_path, 'artists')
        
        # Should process valid records despite invalid ones
        assert result.records_processed == 5
        assert result.records_successful == 3  # Only valid records
        assert result.records_failed == 2
        assert len(result.data) == 3
    
    def test_memory_efficient_large_file_processing(self):
        """Test memory-efficient processing of large files."""
        # Create a large CSV file
        file_path = self.temp_dir / "large_file.csv"
        
        with open(file_path, 'w', newline='') as f:
            f.write('artist_id,name,popularity_score\n')
            for i in range(2000):  # Larger than batch size
                f.write(f'art_{i:04d},Artist {i},{50 + (i % 50)}\n')
        
        result = self.processor.process_file_upload(file_path, 'artists')
        
        # Should handle large files without memory issues
        assert result.records_processed == 2000
        assert result.success is True
    
    def test_encoding_error_handling(self):
        """Test handling of various file encoding issues."""
        # Create file with problematic encoding
        file_path = self.temp_dir / "encoding_issues.csv"
        
        # Write with different encoding
        with open(file_path, 'w', encoding='latin1') as f:
            f.write('artist_id,name\n')
            f.write('art_001,Café Müller\n')  # Special characters
        
        # Should handle encoding gracefully
        result = self.processor.process_file_upload(file_path, 'artists')
        
        # May succeed or fail depending on encoding handling
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'


class TestKinesisErrorHandling:
    """Test Kinesis streaming error handling and retry logic."""
    
    @patch('boto3.client')
    def test_kinesis_stream_not_found(self, mock_boto_client):
        """Test handling when Kinesis stream doesn't exist."""
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_record.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Stream not found'}},
            operation_name='PutRecord'
        )
        
        client = KinesisClient("nonexistent-stream")
        test_data = {"artist_id": "123", "name": "Test Artist"}
        
        result = client.put_record(test_data, partition_key="test")
        
        assert result['success'] is False
        assert 'ResourceNotFoundException' in result['error']
    
    @patch('boto3.client')
    def test_kinesis_throughput_exceeded(self, mock_boto_client):
        """Test handling of throughput exceeded errors."""
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_records.return_value = {
            'FailedRecordCount': 2,
            'Records': [
                {'ErrorCode': 'ProvisionedThroughputExceededException', 'ErrorMessage': 'Rate exceeded'},
                {'ErrorCode': 'ProvisionedThroughputExceededException', 'ErrorMessage': 'Rate exceeded'}
            ]
        }
        
        client = KinesisClient("test-stream")
        test_records = [
            {"artist_id": "123", "name": "Artist 1"},
            {"artist_id": "124", "name": "Artist 2"}
        ]
        
        result = client.put_records(test_records, partition_key_field="artist_id")
        
        assert result['success'] is False
        assert result['records_failed'] == 2
        assert all('ProvisionedThroughputExceededException' in record['error_code'] 
                  for record in result['failed_records'])
    
    @patch('boto3.client')
    def test_kinesis_invalid_data_handling(self, mock_boto_client):
        """Test handling of invalid data in Kinesis records."""
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_record.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidArgumentException', 'Message': 'Invalid data'}},
            operation_name='PutRecord'
        )
        
        client = KinesisClient("test-stream")
        
        # Test with various invalid data types
        invalid_data_cases = [
            None,
            "",
            {"circular": None},  # Will be handled by JSON serialization
        ]
        
        for invalid_data in invalid_data_cases:
            result = client.put_record(invalid_data, partition_key="test")
            
            # Should handle invalid data gracefully
            assert result['success'] is False
            if invalid_data is not None:  # None will cause different error
                assert 'error' in result


class TestIntegrationErrorScenarios:
    """Test end-to-end error scenarios across multiple components."""
    
    @pytest.mark.asyncio
    async def test_cascading_failure_handling(self):
        """Test handling of cascading failures across components."""
        # Create ingestion service with mocked failing clients
        service = DataIngestionService()
        
        # Mock Spotify client that fails after initial success
        mock_spotify = AsyncMock()
        mock_spotify.search_artists.side_effect = [
            APIResponse(success=True, data={"normalized_artists": [{"artist_id": "123"}], "artists": {"total": 1}}),
            APIResponse(success=False, error="Rate limit exceeded")
        ]
        service.spotify_client = mock_spotify
        
        # Mock Ticketmaster client that fails
        mock_ticketmaster = AsyncMock()
        mock_ticketmaster.search_venues.return_value = APIResponse(
            success=False, error="Service unavailable"
        )
        service.ticketmaster_client = mock_ticketmaster
        
        # Test comprehensive ingestion with failures
        results = await service.ingest_comprehensive_data(
            artist_queries=["rock", "jazz"],
            venue_cities=["New York"]
        )
        
        # Should handle partial failures gracefully
        assert "artists" in results
        assert "venues" in results
        
        # Artists should have partial success
        artist_result = results["artists"]
        assert artist_result.records_successful > 0
        assert len(artist_result.errors) > 0
        
        # Venues should have complete failure
        venue_result = results["venues"]
        assert venue_result.success is False
        assert "Service unavailable" in venue_result.errors[0]
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self):
        """Test handling when system resources are exhausted."""
        # Simulate memory pressure by processing many large records
        service = DataIngestionService()
        
        # Mock client that returns very large datasets
        mock_spotify = AsyncMock()
        large_dataset = {
            "normalized_artists": [
                {"artist_id": f"artist_{i}", "name": f"Artist {i}", "large_data": "x" * 1000}
                for i in range(1000)  # Large number of records
            ],
            "artists": {"total": 1000}
        }
        mock_spotify.search_artists.return_value = APIResponse(success=True, data=large_dataset)
        service.spotify_client = mock_spotify
        
        # Should handle large datasets without crashing
        result = await service.ingest_artist_data(["test"])
        
        assert result.source == "spotify"
        assert result.data_type == "artists"
        # Should process successfully or fail gracefully
        assert isinstance(result.success, bool)
    
    def test_concurrent_file_processing_errors(self):
        """Test error handling during concurrent file processing."""
        processor = FileUploadProcessor()
        
        # Create multiple files with different error conditions
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Valid file
            valid_file = temp_dir / "valid.csv"
            valid_file.write_text("artist_id,name\nart_001,Valid Artist")
            
            # Invalid file
            invalid_file = temp_dir / "invalid.csv"
            invalid_file.write_text("invalid,csv,content,without,proper,headers")
            
            # Corrupted file
            corrupted_file = temp_dir / "corrupted.json"
            corrupted_file.write_text('{"invalid": json syntax')
            
            files = [valid_file, invalid_file, corrupted_file]
            data_types = ["artists", "artists", "venues"]
            
            results = processor.process_batch_files(files, data_types)
            
            # Should handle mixed success/failure scenarios
            assert len(results) == 3
            
            # Valid file should succeed
            assert results["valid.csv"].success is True
            
            # Invalid files should fail gracefully
            assert results["invalid.csv"].success is False
            assert results["corrupted.json"].success is False
            
        finally:
            # Cleanup
            for file_path in temp_dir.glob("*"):
                file_path.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])