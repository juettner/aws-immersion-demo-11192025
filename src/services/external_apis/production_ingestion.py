"""
Production data ingestion pipeline that fetches data from external APIs
and persists it to S3 and streams to Kinesis.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionDataPipeline:
    """
    Production pipeline for ingesting external API data and persisting to AWS.
    
    Data Flow:
    1. Fetch data from Spotify/Ticketmaster APIs
    2. Save raw data to S3 (data lake - raw zone)
    3. Stream normalized data to Kinesis for real-time processing
    4. Log ingestion metrics and errors
    """
    
    def __init__(self, 
                 s3_bucket_raw: str = None,
                 s3_bucket_processed: str = None,
                 kinesis_stream_name: str = None,
                 aws_region: str = None):
        self.s3_client = None
        self.kinesis_client = None
        self.ingestion_service = None
        
        # S3 configuration - use provided or get from environment
        self.s3_bucket_raw = s3_bucket_raw or os.getenv('AWS_S3_BUCKET_RAW', 'concert-data-raw')
        self.s3_bucket_processed = s3_bucket_processed or os.getenv('AWS_S3_BUCKET_PROCESSED', 'concert-data-processed')
        
        # Kinesis configuration
        self.kinesis_stream_name = kinesis_stream_name or os.getenv('AWS_KINESIS_STREAM_NAME', 'concert-data-stream')
        
        # AWS region
        self.aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
        
        logger.info("Production pipeline initialized")
    
    async def __aenter__(self):
        """Initialize AWS clients and ingestion service."""
        # Initialize AWS clients
        aws_config = {'region_name': self.aws_region}
        
        # Add credentials if available from environment
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if access_key and secret_key and access_key != 'your_aws_access_key_here':
            aws_config['aws_access_key_id'] = access_key
            aws_config['aws_secret_access_key'] = secret_key
        
        self.s3_client = boto3.client('s3', **aws_config)
        self.kinesis_client = boto3.client('kinesis', **aws_config)
        
        # Initialize ingestion service - import here to avoid circular dependency
        from .ingestion_service import DataIngestionService
        self.ingestion_service = DataIngestionService()
        await self.ingestion_service.initialize_clients()
        
        logger.info("AWS clients and ingestion service initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        if self.ingestion_service:
            await self.ingestion_service.close_clients()
    
    def save_to_s3(
        self,
        data: Dict[str, Any],
        data_type: str,
        source: str,
        bucket: str = None
    ) -> bool:
        """
        Save data to S3 in JSON format.
        
        Args:
            data: Data to save
            data_type: Type of data (artists, venues, events)
            source: Data source (spotify, ticketmaster)
            bucket: S3 bucket name (defaults to raw bucket)
            
        Returns:
            True if successful, False otherwise
        """
        if bucket is None:
            bucket = self.s3_bucket_raw
        
        try:
            # Create S3 key with partitioning by date and source
            timestamp = datetime.utcnow()
            s3_key = (
                f"raw/{source}/{data_type}/"
                f"year={timestamp.year}/"
                f"month={timestamp.month:02d}/"
                f"day={timestamp.day:02d}/"
                f"{data_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Convert data to JSON
            json_data = json.dumps(data, default=str, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'source': source,
                    'data_type': data_type,
                    'ingestion_timestamp': timestamp.isoformat()
                }
            )
            
            logger.info(f"Saved data to S3: s3://{bucket}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to save to S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving to S3: {str(e)}")
            return False
    
    def stream_to_kinesis(
        self,
        records: List[Dict[str, Any]],
        data_type: str,
        source: str
    ) -> int:
        """
        Stream normalized records to Kinesis for real-time processing.
        
        Args:
            records: List of normalized records
            data_type: Type of data (artists, venues, events)
            source: Data source (spotify, ticketmaster)
            
        Returns:
            Number of successfully streamed records
        """
        if not records:
            return 0
        
        successful_count = 0
        
        try:
            # Batch records for Kinesis (max 500 per request)
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Prepare Kinesis records
                kinesis_records = []
                for record in batch:
                    # Add metadata
                    enriched_record = {
                        **record,
                        'ingestion_timestamp': datetime.utcnow().isoformat(),
                        'data_type': data_type,
                        'source': source
                    }
                    
                    kinesis_records.append({
                        'Data': json.dumps(enriched_record, default=str).encode('utf-8'),
                        'PartitionKey': record.get('artist_id') or record.get('venue_id') or record.get('concert_id', 'default')
                    })
                
                # Send to Kinesis
                response = self.kinesis_client.put_records(
                    StreamName=self.kinesis_stream_name,
                    Records=kinesis_records
                )
                
                # Count successful records
                failed_count = response.get('FailedRecordCount', 0)
                successful_count += len(kinesis_records) - failed_count
                
                if failed_count > 0:
                    logger.warning(f"Failed to stream {failed_count} records to Kinesis")
            
            logger.info(f"Streamed {successful_count} records to Kinesis stream: {self.kinesis_stream_name}")
            return successful_count
            
        except ClientError as e:
            logger.error(f"Failed to stream to Kinesis: {str(e)}")
            return successful_count
        except Exception as e:
            logger.error(f"Unexpected error streaming to Kinesis: {str(e)}")
            return successful_count
    
    async def ingest_and_persist_artists(
        self,
        search_queries: List[str],
        max_results_per_query: int = 50
    ) -> Dict[str, Any]:
        """
        Ingest artist data from Spotify and persist to S3 and Kinesis.
        
        Args:
            search_queries: List of search terms for artists
            max_results_per_query: Maximum results per query
            
        Returns:
            Dictionary with ingestion metrics
        """
        logger.info(f"Starting artist ingestion for queries: {search_queries}")
        
        # Ingest data from Spotify
        result = await self.ingestion_service.ingest_artist_data(
            search_queries=search_queries,
            max_results_per_query=max_results_per_query
        )
        
        metrics = {
            'data_type': 'artists',
            'source': 'spotify',
            'records_fetched': result.records_successful,
            'records_saved_to_s3': 0,
            'records_streamed_to_kinesis': 0,
            'errors': result.errors
        }
        
        if result.success and result.data:
            # Save raw data to S3
            raw_data = {
                'ingestion_result': result.to_dict(),
                'records': result.data
            }
            if self.save_to_s3(raw_data, 'artists', 'spotify'):
                metrics['records_saved_to_s3'] = len(result.data)
            
            # Stream normalized data to Kinesis
            streamed_count = self.stream_to_kinesis(result.data, 'artists', 'spotify')
            metrics['records_streamed_to_kinesis'] = streamed_count
        
        logger.info(f"Artist ingestion completed: {metrics}")
        return metrics
    
    async def ingest_and_persist_venues(
        self,
        cities: List[str],
        max_results_per_city: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest venue data from Ticketmaster and persist to S3 and Kinesis.
        
        Args:
            cities: List of city names
            max_results_per_city: Maximum results per city
            
        Returns:
            Dictionary with ingestion metrics
        """
        logger.info(f"Starting venue ingestion for cities: {cities}")
        
        # Ingest data from Ticketmaster
        result = await self.ingestion_service.ingest_venue_data(
            cities=cities,
            max_results_per_city=max_results_per_city
        )
        
        metrics = {
            'data_type': 'venues',
            'source': 'ticketmaster',
            'records_fetched': result.records_successful,
            'records_saved_to_s3': 0,
            'records_streamed_to_kinesis': 0,
            'errors': result.errors
        }
        
        if result.success and result.data:
            # Save raw data to S3
            raw_data = {
                'ingestion_result': result.to_dict(),
                'records': result.data
            }
            if self.save_to_s3(raw_data, 'venues', 'ticketmaster'):
                metrics['records_saved_to_s3'] = len(result.data)
            
            # Stream normalized data to Kinesis
            streamed_count = self.stream_to_kinesis(result.data, 'venues', 'ticketmaster')
            metrics['records_streamed_to_kinesis'] = streamed_count
        
        logger.info(f"Venue ingestion completed: {metrics}")
        return metrics
    
    async def ingest_and_persist_events(
        self,
        cities: List[str] = None,
        keywords: List[str] = None,
        max_results: int = 200
    ) -> Dict[str, Any]:
        """
        Ingest event data from Ticketmaster and persist to S3 and Kinesis.
        
        Args:
            cities: List of city names
            keywords: List of keywords
            max_results: Maximum total results
            
        Returns:
            Dictionary with ingestion metrics
        """
        logger.info(f"Starting event ingestion for cities: {cities}, keywords: {keywords}")
        
        # Ingest data from Ticketmaster
        result = await self.ingestion_service.ingest_event_data(
            cities=cities,
            keywords=keywords,
            max_results=max_results
        )
        
        metrics = {
            'data_type': 'events',
            'source': 'ticketmaster',
            'records_fetched': result.records_successful,
            'records_saved_to_s3': 0,
            'records_streamed_to_kinesis': 0,
            'errors': result.errors
        }
        
        if result.success and result.data:
            # Save raw data to S3
            raw_data = {
                'ingestion_result': result.to_dict(),
                'records': result.data
            }
            if self.save_to_s3(raw_data, 'events', 'ticketmaster'):
                metrics['records_saved_to_s3'] = len(result.data)
            
            # Stream normalized data to Kinesis
            streamed_count = self.stream_to_kinesis(result.data, 'events', 'ticketmaster')
            metrics['records_streamed_to_kinesis'] = streamed_count
        
        logger.info(f"Event ingestion completed: {metrics}")
        return metrics
    
    async def run_full_ingestion(
        self,
        artist_queries: List[str] = None,
        venue_cities: List[str] = None,
        event_cities: List[str] = None,
        event_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run full data ingestion pipeline for all data types.
        
        Args:
            artist_queries: Search queries for artists
            venue_cities: Cities to search for venues
            event_cities: Cities to search for events
            event_keywords: Keywords to search for events
            
        Returns:
            Dictionary with comprehensive metrics
        """
        logger.info("Starting full ingestion pipeline")
        
        # Default values
        if artist_queries is None:
            artist_queries = ["rock", "pop", "jazz", "country", "electronic"]
        if venue_cities is None:
            venue_cities = ["New York", "Los Angeles", "Chicago", "Nashville", "Austin"]
        if event_cities is None:
            event_cities = venue_cities
        if event_keywords is None:
            event_keywords = ["concert", "music"]
        
        # Run all ingestion tasks
        results = {}
        
        try:
            # Ingest artists
            results['artists'] = await self.ingest_and_persist_artists(
                search_queries=artist_queries,
                max_results_per_query=50
            )
            
            # Ingest venues
            results['venues'] = await self.ingest_and_persist_venues(
                cities=venue_cities,
                max_results_per_city=100
            )
            
            # Ingest events
            results['events'] = await self.ingest_and_persist_events(
                cities=event_cities,
                keywords=event_keywords,
                max_results=200
            )
            
            # Calculate totals
            results['summary'] = {
                'total_records_fetched': sum(r['records_fetched'] for r in results.values() if isinstance(r, dict) and 'records_fetched' in r),
                'total_records_saved_to_s3': sum(r['records_saved_to_s3'] for r in results.values() if isinstance(r, dict) and 'records_saved_to_s3' in r),
                'total_records_streamed_to_kinesis': sum(r['records_streamed_to_kinesis'] for r in results.values() if isinstance(r, dict) and 'records_streamed_to_kinesis' in r),
                'total_errors': sum(len(r['errors']) for r in results.values() if isinstance(r, dict) and 'errors' in r),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Full ingestion pipeline completed: {results['summary']}")
            
        except Exception as e:
            logger.error(f"Full ingestion pipeline failed: {str(e)}")
            results['error'] = str(e)
        
        return results


async def main():
    """Main entry point for production ingestion."""
    logger.info("=" * 60)
    logger.info("PRODUCTION DATA INGESTION PIPELINE")
    logger.info("=" * 60)
    
    async with ProductionDataPipeline() as pipeline:
        # Run full ingestion
        results = await pipeline.run_full_ingestion(
            artist_queries=["rock", "pop", "jazz"],
            venue_cities=["New York", "Los Angeles"],
            event_cities=["New York", "Los Angeles"],
            event_keywords=["concert"]
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("INGESTION SUMMARY")
        print("=" * 60)
        print(json.dumps(results, indent=2, default=str))
        print("=" * 60)


if __name__ == "__main__":
    # Load environment variables before running
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Load environment
    from src.config.environment import load_env_file
    load_env_file()
    
    # Run the pipeline
    asyncio.run(main())