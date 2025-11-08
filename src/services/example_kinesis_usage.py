"""
Example usage of Kinesis streaming integration for concert data.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import structlog

from .kinesis_integration_service import KinesisIntegrationService
from .stream_producer import StreamProducerService
from ..infrastructure.kinesis_client import KinesisClient
from ..config.settings import settings

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def demonstrate_kinesis_setup():
    """
    Demonstrate setting up the complete Kinesis streaming integration.
    """
    print("\n=== Kinesis Integration Setup Demo ===")
    
    integration_service = KinesisIntegrationService()
    
    try:
        # Setup complete integration
        print("Setting up Kinesis streaming integration...")
        setup_result = await integration_service.setup_complete_integration()
        
        print(f"Setup Result: {'SUCCESS' if setup_result.success else 'FAILED'}")
        print(f"Stream Created: {setup_result.details.get('stream_created', False)}")
        print(f"Lambda Functions Deployed: {len(setup_result.details.get('lambda_functions_deployed', []))}")
        print(f"Event Source Mappings: {len(setup_result.details.get('event_source_mappings', []))}")
        
        if setup_result.errors:
            print("Errors encountered:")
            for error in setup_result.errors:
                print(f"  - {error}")
        
        # Check integration status
        print("\nChecking integration status...")
        status_result = integration_service.get_integration_status()
        
        print(f"Integration Health: {status_result.details.get('integration_health', 'unknown')}")
        print(f"Stream Status: {status_result.details.get('stream_status', {}).get('stream_status', 'unknown')}")
        print(f"Lambda Functions: {len(status_result.details.get('lambda_functions', []))}")
        
        return setup_result.success
        
    except Exception as e:
        print(f"Setup failed with error: {str(e)}")
        return False


async def demonstrate_api_data_streaming():
    """
    Demonstrate streaming data from external APIs to Kinesis.
    """
    print("\n=== API Data Streaming Demo ===")
    
    integration_service = KinesisIntegrationService()
    
    try:
        # Test streaming pipeline with small dataset
        print("Testing streaming pipeline with API data...")
        test_result = await integration_service.test_streaming_pipeline(test_data_size="small")
        
        print(f"Test Result: {'SUCCESS' if test_result.success else 'FAILED'}")
        print(f"Records Sent: {test_result.details.get('records_sent', 0)}")
        print(f"Records Failed: {test_result.details.get('records_failed', 0)}")
        print(f"Test Duration: {test_result.details.get('test_duration_seconds', 0):.2f} seconds")
        
        # Show streaming results by data type
        streaming_results = test_result.details.get('streaming_results', {})
        for data_type, result_dict in streaming_results.items():
            print(f"\n{data_type.upper()} Data:")
            print(f"  Source: {result_dict.get('source', 'unknown')}")
            print(f"  Records Sent: {result_dict.get('records_sent', 0)}")
            print(f"  Records Failed: {result_dict.get('records_failed', 0)}")
            print(f"  Success: {result_dict.get('success', False)}")
        
        if test_result.errors:
            print("\nErrors encountered:")
            for error in test_result.errors:
                print(f"  - {error}")
        
        return test_result.success
        
    except Exception as e:
        print(f"API streaming test failed with error: {str(e)}")
        return False


async def demonstrate_file_data_streaming():
    """
    Demonstrate streaming data from files to Kinesis.
    """
    print("\n=== File Data Streaming Demo ===")
    
    # Check if sample data files exist
    sample_files = [
        "sample_data/artists.csv",
        "sample_data/venues.json",
        "sample_data/concerts.xml"
    ]
    
    existing_files = []
    data_types = []
    
    for file_path in sample_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            if "artists" in file_path:
                data_types.append("artists")
            elif "venues" in file_path:
                data_types.append("venues")
            elif "concerts" in file_path:
                data_types.append("concerts")
    
    if not existing_files:
        print("No sample data files found. Skipping file streaming demo.")
        return True
    
    integration_service = KinesisIntegrationService()
    
    try:
        print(f"Streaming data from {len(existing_files)} files...")
        
        # Stream batch files
        file_result = await integration_service.stream_file_data_batch(
            file_paths=existing_files,
            data_types=data_types
        )
        
        print(f"File Streaming Result: {'SUCCESS' if file_result.success else 'FAILED'}")
        print(f"Files Processed: {file_result.details.get('files_processed', 0)}")
        print(f"Total Records Sent: {file_result.details.get('total_records_sent', 0)}")
        print(f"Total Records Failed: {file_result.details.get('total_records_failed', 0)}")
        
        # Show results by file
        streaming_results = file_result.details.get('streaming_results', {})
        for file_path, result_dict in streaming_results.items():
            print(f"\nFile: {file_path}")
            print(f"  Data Type: {result_dict.get('data_type', 'unknown')}")
            print(f"  Records Sent: {result_dict.get('records_sent', 0)}")
            print(f"  Records Failed: {result_dict.get('records_failed', 0)}")
            print(f"  Success: {result_dict.get('success', False)}")
        
        if file_result.errors:
            print("\nErrors encountered:")
            for error in file_result.errors:
                print(f"  - {error}")
        
        return file_result.success
        
    except Exception as e:
        print(f"File streaming test failed with error: {str(e)}")
        return False


async def demonstrate_direct_kinesis_operations():
    """
    Demonstrate direct Kinesis client operations.
    """
    print("\n=== Direct Kinesis Operations Demo ===")
    
    kinesis_client = KinesisClient()
    
    try:
        # Create stream if not exists
        print("Ensuring Kinesis stream exists...")
        stream_created = await kinesis_client.create_stream_if_not_exists()
        print(f"Stream Ready: {stream_created}")
        
        # Get stream information
        print("\nGetting stream information...")
        stream_info = kinesis_client.get_stream_description()
        
        if stream_info.get('success'):
            print(f"Stream Name: {stream_info.get('stream_name')}")
            print(f"Stream Status: {stream_info.get('stream_status')}")
            print(f"Shard Count: {stream_info.get('shard_count')}")
            print(f"Retention Period: {stream_info.get('retention_period')} hours")
        else:
            print(f"Failed to get stream info: {stream_info.get('error')}")
        
        # Send sample records
        print("\nSending sample records...")
        sample_records = [
            {
                "artist_id": "demo_001",
                "name": "Demo Artist 1",
                "genre": ["rock"],
                "popularity_score": 85.5
            },
            {
                "artist_id": "demo_002", 
                "name": "Demo Artist 2",
                "genre": ["pop"],
                "popularity_score": 92.3
            }
        ]
        
        # Send records in batch
        batch_result = kinesis_client.put_records(
            records=sample_records,
            partition_key_field="artist_id"
        )
        
        print(f"Batch Send Result: {'SUCCESS' if batch_result.get('success') else 'FAILED'}")
        print(f"Records Processed: {batch_result.get('records_processed', 0)}")
        print(f"Records Successful: {batch_result.get('records_successful', 0)}")
        print(f"Records Failed: {batch_result.get('records_failed', 0)}")
        
        if batch_result.get('failed_records'):
            print("Failed records:")
            for failed_record in batch_result['failed_records']:
                print(f"  - Index {failed_record['index']}: {failed_record.get('error_message', 'Unknown error')}")
        
        return batch_result.get('success', False)
        
    except Exception as e:
        print(f"Direct Kinesis operations failed with error: {str(e)}")
        return False


async def demonstrate_stream_producer_service():
    """
    Demonstrate StreamProducerService functionality.
    """
    print("\n=== Stream Producer Service Demo ===")
    
    try:
        async with StreamProducerService() as producer:
            # Get stream information
            print("Getting stream information...")
            stream_info = producer.get_stream_info()
            
            if stream_info.get('success'):
                print(f"Stream Status: {stream_info.get('stream_status')}")
                print(f"Shard Count: {stream_info.get('shard_count')}")
            
            # Test with small API data streaming
            print("\nStreaming small dataset from APIs...")
            api_result = await producer.stream_api_data(
                artist_queries=["rock"],
                venue_cities=["New York"],
                event_cities=["New York"],
                event_keywords=["concert"]
            )
            
            total_sent = sum(result.records_sent for result in api_result.values())
            total_failed = sum(result.records_failed for result in api_result.values())
            
            print(f"API Streaming Result: {'SUCCESS' if total_failed == 0 else 'PARTIAL SUCCESS'}")
            print(f"Total Records Sent: {total_sent}")
            print(f"Total Records Failed: {total_failed}")
            
            for data_type, result in api_result.items():
                if result.records_sent > 0 or result.records_failed > 0:
                    print(f"  {data_type}: {result.records_sent} sent, {result.records_failed} failed")
        
        return True
        
    except Exception as e:
        print(f"Stream producer demo failed with error: {str(e)}")
        return False


def print_configuration_info():
    """
    Print current configuration information.
    """
    print("\n=== Configuration Information ===")
    print(f"AWS Region: {settings.aws.region}")
    print(f"Kinesis Stream Name: {settings.aws.kinesis_stream_name}")
    print(f"Kinesis Shard Count: {settings.aws.kinesis_shard_count}")
    print(f"S3 Raw Bucket: {settings.aws.s3_bucket_raw}")
    print(f"S3 Processed Bucket: {settings.aws.s3_bucket_processed}")
    print(f"Environment: {settings.app.environment}")
    print(f"Debug Mode: {settings.app.debug}")


async def run_complete_demo():
    """
    Run the complete Kinesis integration demonstration.
    """
    print("🎵 Concert Data Platform - Kinesis Streaming Integration Demo 🎵")
    print("=" * 70)
    
    # Print configuration
    print_configuration_info()
    
    # Track demo results
    demo_results = {}
    
    # 1. Setup integration
    demo_results['setup'] = await demonstrate_kinesis_setup()
    
    # 2. Direct Kinesis operations
    demo_results['direct_kinesis'] = await demonstrate_direct_kinesis_operations()
    
    # 3. Stream producer service
    demo_results['stream_producer'] = await demonstrate_stream_producer_service()
    
    # 4. API data streaming
    demo_results['api_streaming'] = await demonstrate_api_data_streaming()
    
    # 5. File data streaming
    demo_results['file_streaming'] = await demonstrate_file_data_streaming()
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 DEMO SUMMARY")
    print("=" * 70)
    
    for demo_name, success in demo_results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{demo_name.replace('_', ' ').title()}: {status}")
    
    overall_success = all(demo_results.values())
    print(f"\nOverall Demo Result: {'✅ SUCCESS' if overall_success else '❌ SOME FAILURES'}")
    
    if not overall_success:
        print("\n⚠️  Some demos failed. This might be due to:")
        print("   - Missing AWS credentials")
        print("   - Missing API keys (Spotify, Ticketmaster)")
        print("   - Network connectivity issues")
        print("   - AWS service limits or permissions")
        print("   - Missing sample data files")
    
    return overall_success


if __name__ == "__main__":
    # Run the complete demo
    asyncio.run(run_complete_demo())