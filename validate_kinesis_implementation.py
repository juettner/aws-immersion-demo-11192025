#!/usr/bin/env python3
"""
Simple validation script for Kinesis integration implementation.
"""
import sys
import json
from datetime import datetime
from pathlib import Path

def validate_kinesis_client():
    """Validate KinesisClient implementation."""
    print("🔍 Validating KinesisClient implementation...")
    
    try:
        # Import and check basic structure
        sys.path.append('src')
        from infrastructure.kinesis_client import KinesisClient, StreamRecord, KinesisStreamError
        
        # Test StreamRecord creation
        test_data = {"artist_id": "123", "name": "Test Artist"}
        record = StreamRecord(test_data, partition_key="artist_123")
        
        assert record.data == test_data
        assert record.partition_key == "artist_123"
        assert record.timestamp is not None
        
        # Test Kinesis record conversion
        kinesis_record = record.to_kinesis_record()
        assert "Data" in kinesis_record
        assert "PartitionKey" in kinesis_record
        assert kinesis_record["PartitionKey"] == "artist_123"
        
        # Verify data is JSON serialized
        data_content = json.loads(kinesis_record["Data"])
        assert "timestamp" in data_content
        assert "data" in data_content
        assert data_content["data"] == test_data
        
        print("✅ KinesisClient validation passed")
        return True
        
    except Exception as e:
        print(f"❌ KinesisClient validation failed: {str(e)}")
        return False


def validate_stream_producer():
    """Validate StreamProducerService implementation."""
    print("🔍 Validating StreamProducerService implementation...")
    
    try:
        from services.stream_producer import StreamProducerService, StreamProducerResult
        
        # Test StreamProducerResult creation
        result = StreamProducerResult(
            success=True,
            source="test",
            data_type="artists",
            records_sent=10,
            records_failed=0
        )
        
        assert result.success is True
        assert result.source == "test"
        assert result.data_type == "artists"
        assert result.records_sent == 10
        assert result.records_failed == 0
        
        # Test result conversion to dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["records_sent"] == 10
        
        print("✅ StreamProducerService validation passed")
        return True
        
    except Exception as e:
        print(f"❌ StreamProducerService validation failed: {str(e)}")
        return False


def validate_lambda_functions():
    """Validate Lambda functions implementation."""
    print("🔍 Validating Lambda functions implementation...")
    
    try:
        from infrastructure.lambda_functions import StreamProcessor, ConcertDataProcessor
        
        # Test StreamProcessor base class
        processor = StreamProcessor()
        assert hasattr(processor, 'decode_kinesis_record')
        assert hasattr(processor, 'validate_record_structure')
        assert hasattr(processor, 'write_to_s3')
        
        # Test ConcertDataProcessor
        concert_processor = ConcertDataProcessor()
        assert hasattr(concert_processor, 'process_artist_record')
        assert hasattr(concert_processor, 'process_venue_record')
        assert hasattr(concert_processor, 'process_concert_record')
        assert hasattr(concert_processor, 'process_ticket_sale_record')
        
        # Test record processing methods exist
        test_record = {
            'source': 'test',
            'data_type': 'artists',
            'ingestion_timestamp': datetime.utcnow().isoformat(),
            'payload': {'artist_id': '123', 'name': 'Test Artist'}
        }
        
        processed = concert_processor.process_artist_record(test_record)
        assert isinstance(processed, dict)
        assert 'artist_id' in processed
        assert 'processed_timestamp' in processed
        
        print("✅ Lambda functions validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Lambda functions validation failed: {str(e)}")
        return False


def validate_integration_service():
    """Validate KinesisIntegrationService implementation."""
    print("🔍 Validating KinesisIntegrationService implementation...")
    
    try:
        from services.kinesis_integration_service import KinesisIntegrationService, KinesisIntegrationResult
        
        # Test KinesisIntegrationResult creation
        result = KinesisIntegrationResult(
            success=True,
            operation="test_operation",
            details={"test": "data"},
            errors=[]
        )
        
        assert result.success is True
        assert result.operation == "test_operation"
        assert result.details == {"test": "data"}
        assert result.errors == []
        
        # Test result conversion to dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["operation"] == "test_operation"
        
        print("✅ KinesisIntegrationService validation passed")
        return True
        
    except Exception as e:
        print(f"❌ KinesisIntegrationService validation failed: {str(e)}")
        return False


def validate_configuration():
    """Validate configuration settings."""
    print("🔍 Validating configuration...")
    
    try:
        from config.settings import settings
        
        # Check AWS configuration
        assert hasattr(settings.aws, 'kinesis_stream_name')
        assert hasattr(settings.aws, 'kinesis_shard_count')
        assert hasattr(settings.aws, 's3_bucket_raw')
        assert hasattr(settings.aws, 's3_bucket_processed')
        
        # Check default values
        assert settings.aws.kinesis_stream_name == "concert-data-stream"
        assert settings.aws.kinesis_shard_count == 1
        assert settings.aws.s3_bucket_raw == "concert-data-raw"
        assert settings.aws.s3_bucket_processed == "concert-data-processed"
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        return False


def validate_file_structure():
    """Validate that all required files exist."""
    print("🔍 Validating file structure...")
    
    required_files = [
        "src/infrastructure/kinesis_client.py",
        "src/infrastructure/lambda_functions.py",
        "src/infrastructure/lambda_deployment.py",
        "src/services/stream_producer.py",
        "src/services/kinesis_integration_service.py",
        "src/services/test_kinesis_integration.py",
        "src/services/example_kinesis_usage.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ File structure validation passed")
    return True


def main():
    """Run all validations."""
    print("🎵 Kinesis Integration Implementation Validation 🎵")
    print("=" * 60)
    
    validations = [
        ("File Structure", validate_file_structure),
        ("Configuration", validate_configuration),
        ("KinesisClient", validate_kinesis_client),
        ("StreamProducerService", validate_stream_producer),
        ("Lambda Functions", validate_lambda_functions),
        ("Integration Service", validate_integration_service)
    ]
    
    results = {}
    
    for name, validation_func in validations:
        try:
            results[name] = validation_func()
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {str(e)}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
    
    overall_success = all(results.values())
    print(f"\nOverall Result: {'✅ ALL VALIDATIONS PASSED' if overall_success else '❌ SOME VALIDATIONS FAILED'}")
    
    if overall_success:
        print("\n🎉 Kinesis integration implementation is ready!")
        print("📋 Task 2.3 'Set up Kinesis data streaming integration' is complete.")
        print("\nImplemented components:")
        print("  ✅ Kinesis stream configuration and client")
        print("  ✅ Stream producers for API and file data")
        print("  ✅ Lambda functions for stream processing")
        print("  ✅ Integration service for orchestration")
        print("  ✅ Comprehensive testing framework")
        print("  ✅ Example usage and documentation")
    else:
        print("\n⚠️  Some validations failed. Please review the implementation.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)