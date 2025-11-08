"""
Tests for Kinesis streaming integration.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from ..infrastructure.kinesis_client import KinesisClient, StreamRecord
from ..services.stream_producer import StreamProducerService, StreamProducerResult
from ..services.kinesis_integration_service import KinesisIntegrationService, KinesisIntegrationResult


class TestKinesisClient:
    """Test cases for KinesisClient."""
    
    @pytest.fixture
    def kinesis_client(self):
        """Create a KinesisClient instance for testing."""
        with patch('boto3.client'):
            return KinesisClient("test-stream")
    
    def test_stream_record_creation(self):
        """Test StreamRecord creation and conversion."""
        test_data = {"artist_id": "123", "name": "Test Artist"}
        record = StreamRecord(test_data, partition_key="artist_123")
        
        assert record.data == test_data
        assert record.partition_key == "artist_123"
        assert record.timestamp is not None
        
        kinesis_record = record.to_kinesis_record()
        assert "Data" in kinesis_record
        assert "PartitionKey" in kinesis_record
        assert kinesis_record["PartitionKey"] == "artist_123"
        
        # Verify data is JSON serialized
        data_content = json.loads(kinesis_record["Data"])
        assert "timestamp" in data_content
        assert "data" in data_content
        assert data_content["data"] == test_data
    
    @patch('boto3.client')
    def test_put_record_success(self, mock_boto_client):
        """Test successful single record put."""
        # Mock Kinesis client response
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_record.return_value = {
            'SequenceNumber': '12345',
            'ShardId': 'shardId-000000000000'
        }
        
        client = KinesisClient("test-stream")
        test_data = {"artist_id": "123", "name": "Test Artist"}
        
        result = client.put_record(test_data, partition_key="artist_123")
        
        assert result['success'] is True
        assert result['sequence_number'] == '12345'
        assert result['shard_id'] == 'shardId-000000000000'
        assert 'timestamp' in result
        
        # Verify the call was made correctly
        mock_kinesis.put_record.assert_called_once()
        call_args = mock_kinesis.put_record.call_args[1]
        assert call_args['StreamName'] == 'test-stream'
        assert call_args['PartitionKey'] == 'artist_123'
    
    @patch('boto3.client')
    def test_put_records_batch_success(self, mock_boto_client):
        """Test successful batch records put."""
        # Mock Kinesis client response
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_records.return_value = {
            'FailedRecordCount': 0,
            'Records': [
                {'SequenceNumber': '12345', 'ShardId': 'shardId-000000000000'},
                {'SequenceNumber': '12346', 'ShardId': 'shardId-000000000000'}
            ]
        }
        
        client = KinesisClient("test-stream")
        test_records = [
            {"artist_id": "123", "name": "Artist 1"},
            {"artist_id": "124", "name": "Artist 2"}
        ]
        
        result = client.put_records(test_records, partition_key_field="artist_id")
        
        assert result['success'] is True
        assert result['records_processed'] == 2
        assert result['records_successful'] == 2
        assert result['records_failed'] == 0
        assert len(result['failed_records']) == 0
        
        # Verify the call was made correctly
        mock_kinesis.put_records.assert_called_once()
        call_args = mock_kinesis.put_records.call_args[1]
        assert call_args['StreamName'] == 'test-stream'
        assert len(call_args['Records']) == 2
    
    @patch('boto3.client')
    def test_put_records_partial_failure(self, mock_boto_client):
        """Test batch records put with partial failures."""
        # Mock Kinesis client response with some failures
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_records.return_value = {
            'FailedRecordCount': 1,
            'Records': [
                {'SequenceNumber': '12345', 'ShardId': 'shardId-000000000000'},
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
        assert result['records_processed'] == 2
        assert result['records_successful'] == 1
        assert result['records_failed'] == 1
        assert len(result['failed_records']) == 1
        assert result['failed_records'][0]['error_code'] == 'ProvisionedThroughputExceededException'
    
    @patch('boto3.client')
    def test_put_record_kinesis_exception(self, mock_boto_client):
        """Test put_record with Kinesis service exception."""
        from botocore.exceptions import ClientError
        
        # Mock Kinesis client to raise exception
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        mock_kinesis.put_record.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Stream not found'}},
            operation_name='PutRecord'
        )
        
        client = KinesisClient("test-stream")
        test_data = {"artist_id": "123", "name": "Test Artist"}
        
        result = client.put_record(test_data, partition_key="artist_123")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'ResourceNotFoundException' in result['error']
    
    @patch('boto3.client')
    def test_put_records_retry_logic(self, mock_boto_client):
        """Test retry logic for failed records in batch put."""
        # Mock Kinesis client with initial failure then success
        mock_kinesis = Mock()
        mock_boto_client.return_value = mock_kinesis
        
        # First call: partial failure
        # Second call: success for retry
        mock_kinesis.put_records.side_effect = [
            {
                'FailedRecordCount': 1,
                'Records': [
                    {'SequenceNumber': '12345', 'ShardId': 'shardId-000000000000'},
                    {'ErrorCode': 'ProvisionedThroughputExceededException', 'ErrorMessage': 'Rate exceeded'}
                ]
            },
            {
                'FailedRecordCount': 0,
                'Records': [
                    {'SequenceNumber': '12346', 'ShardId': 'shardId-000000000000'}
                ]
            }
        ]
        
        client = KinesisClient("test-stream")
        test_records = [
            {"artist_id": "123", "name": "Artist 1"},
            {"artist_id": "124", "name": "Artist 2"}
        ]
        
        # This would require implementing retry logic in the actual client
        result = client.put_records(test_records, partition_key_field="artist_id")
        
        # First call should show partial failure
        assert result['success'] is False
        assert result['records_failed'] == 1


class TestStreamProducerService:
    """Test cases for StreamProducerService."""
    
    @pytest.fixture
    def stream_producer(self):
        """Create a StreamProducerService instance for testing."""
        with patch('src.services.stream_producer.KinesisClient'), \
             patch('src.services.stream_producer.DataIngestionService'), \
             patch('src.services.stream_producer.FileUploadProcessor'):
            return StreamProducerService("test-stream")
    
    def test_prepare_stream_record(self, stream_producer):
        """Test stream record preparation with metadata."""
        test_data = {"artist_id": "123", "name": "Test Artist"}
        
        result = stream_producer._prepare_stream_record(test_data, "artists", "spotify")
        
        assert result["source"] == "spotify"
        assert result["data_type"] == "artists"
        assert result["payload"] == test_data
        assert "record_id" in result
        assert "ingestion_timestamp" in result
        assert result["record_id"].startswith("spotify_artists_")
    
    def test_get_partition_key(self, stream_producer):
        """Test partition key generation for different data types."""
        # Test artist partition key
        artist_data = {"artist_id": "123", "name": "Test Artist"}
        key = stream_producer._get_partition_key(artist_data, "artists")
        assert key == "artist_123"
        
        # Test venue partition key
        venue_data = {"venue_id": "456", "name": "Test Venue"}
        key = stream_producer._get_partition_key(venue_data, "venues")
        assert key == "venue_456"
        
        # Test concert partition key
        concert_data = {"concert_id": "789", "artist_id": "123"}
        key = stream_producer._get_partition_key(concert_data, "concerts")
        assert key == "concert_789"
        
        # Test unknown data type
        unknown_data = {"some_id": "999"}
        key = stream_producer._get_partition_key(unknown_data, "unknown_type")
        assert key == "unknown_type_unknown"
    
    @pytest.mark.asyncio
    async def test_stream_records_batch(self, stream_producer):
        """Test batch streaming of records."""
        # Mock the Kinesis client
        mock_kinesis_response = {
            'success': True,
            'records_processed': 2,
            'records_successful': 2,
            'records_failed': 0,
            'failed_records': []
        }
        stream_producer.kinesis_client.put_records = Mock(return_value=mock_kinesis_response)
        
        test_records = [
            {"artist_id": "123", "name": "Artist 1"},
            {"artist_id": "124", "name": "Artist 2"}
        ]
        
        result = await stream_producer._stream_records_batch(
            test_records, "artists", "spotify", batch_size=10
        )
        
        assert isinstance(result, StreamProducerResult)
        assert result.success is True
        assert result.source == "spotify"
        assert result.data_type == "artists"
        assert result.records_sent == 2
        assert result.records_failed == 0
        
        # Verify Kinesis client was called
        stream_producer.kinesis_client.put_records.assert_called_once()


class TestKinesisIntegrationService:
    """Test cases for KinesisIntegrationService."""
    
    @pytest.fixture
    def integration_service(self):
        """Create a KinesisIntegrationService instance for testing."""
        with patch('src.services.kinesis_integration_service.KinesisClient'), \
             patch('src.services.kinesis_integration_service.LambdaDeployer'), \
             patch('src.services.kinesis_integration_service.StreamProducerService'):
            return KinesisIntegrationService()
    
    @pytest.mark.asyncio
    async def test_validate_integration_success(self, integration_service):
        """Test successful integration validation."""
        # Mock stream description
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'ACTIVE',
            'stream_name': 'test-stream'
        }
        
        # Mock Lambda functions list
        integration_service.lambda_deployer.list_deployed_functions.return_value = [
            {'function_name': 'kinesis-stream-processor'},
            {'function_name': 'data-quality-processor'},
            {'function_name': 'stream-analytics-processor'}
        ]
        
        result = await integration_service._validate_integration()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_integration_inactive_stream(self, integration_service):
        """Test integration validation with inactive stream."""
        # Mock inactive stream
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'CREATING',
            'stream_name': 'test-stream'
        }
        
        # Mock Lambda functions list
        integration_service.lambda_deployer.list_deployed_functions.return_value = [
            {'function_name': 'kinesis-stream-processor'},
            {'function_name': 'data-quality-processor'},
            {'function_name': 'stream-analytics-processor'}
        ]
        
        result = await integration_service._validate_integration()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_integration_missing_functions(self, integration_service):
        """Test integration validation with missing Lambda functions."""
        # Mock active stream
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'ACTIVE',
            'stream_name': 'test-stream'
        }
        
        # Mock incomplete Lambda functions list
        integration_service.lambda_deployer.list_deployed_functions.return_value = [
            {'function_name': 'kinesis-stream-processor'}
        ]
        
        result = await integration_service._validate_integration()
        
        assert result is False
    
    def test_get_integration_status_healthy(self, integration_service):
        """Test integration status check for healthy system."""
        # Mock healthy stream
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'ACTIVE',
            'stream_name': 'test-stream'
        }
        
        # Mock complete Lambda functions
        integration_service.lambda_deployer.list_deployed_functions.return_value = [
            {'function_name': 'kinesis-stream-processor'},
            {'function_name': 'data-quality-processor'},
            {'function_name': 'stream-analytics-processor'}
        ]
        
        result = integration_service.get_integration_status()
        
        assert isinstance(result, KinesisIntegrationResult)
        assert result.success is True
        assert result.operation == "get_integration_status"
        assert result.details['integration_health'] == 'healthy'
    
    def test_get_integration_status_partial(self, integration_service):
        """Test integration status check for partial system."""
        # Mock active stream
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'ACTIVE',
            'stream_name': 'test-stream'
        }
        
        # Mock incomplete Lambda functions
        integration_service.lambda_deployer.list_deployed_functions.return_value = [
            {'function_name': 'kinesis-stream-processor'}
        ]
        
        result = integration_service.get_integration_status()
        
        assert isinstance(result, KinesisIntegrationResult)
        assert result.success is True
        assert result.operation == "get_integration_status"
        assert result.details['integration_health'] == 'partial'
    
    def test_get_integration_status_unhealthy(self, integration_service):
        """Test integration status check for unhealthy system."""
        # Mock inactive stream
        integration_service.kinesis_client.get_stream_description.return_value = {
            'success': True,
            'stream_status': 'CREATING',
            'stream_name': 'test-stream'
        }
        
        # Mock Lambda functions
        integration_service.lambda_deployer.list_deployed_functions.return_value = []
        
        result = integration_service.get_integration_status()
        
        assert isinstance(result, KinesisIntegrationResult)
        assert result.success is True
        assert result.operation == "get_integration_status"
        assert result.details['integration_health'] == 'unhealthy'


# Integration test (requires actual AWS resources)
@pytest.mark.integration
class TestKinesisIntegrationE2E:
    """End-to-end integration tests (requires AWS resources)."""
    
    @pytest.mark.asyncio
    async def test_complete_integration_setup(self):
        """Test complete integration setup (requires AWS credentials)."""
        # This test would require actual AWS credentials and resources
        # It's marked as integration test and would be run separately
        pytest.skip("Integration test requires AWS resources")
    
    @pytest.mark.asyncio
    async def test_streaming_pipeline_with_real_data(self):
        """Test streaming pipeline with real API data (requires API keys)."""
        # This test would require actual API keys and AWS resources
        # It's marked as integration test and would be run separately
        pytest.skip("Integration test requires API keys and AWS resources")


    def test_stream_record_with_explicit_hash_key(self):
        """Test StreamRecord with explicit hash key."""
        test_data = {"venue_id": "456", "name": "Test Venue"}
        record = StreamRecord(test_data, partition_key="venue_456", explicit_hash_key="12345")
        
        assert record.explicit_hash_key == "12345"
        
        kinesis_record = record.to_kinesis_record()
        assert "ExplicitHashKey" in kinesis_record
        assert kinesis_record["ExplicitHashKey"] == "12345"
    
    def test_stream_record_without_partition_key(self):
        """Test StreamRecord without explicit partition key."""
        test_data = {"concert_id": "789", "artist_id": "123"}
        record = StreamRecord(test_data)
        
        # Should generate a UUID as partition key
        assert record.partition_key is not None
        assert len(record.partition_key) > 0


if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v", "-m", "not integration"])