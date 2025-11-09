"""
Scheduled ingestion job for running periodic data collection.
Can be triggered by:
- AWS EventBridge (CloudWatch Events)
- Cron job
- AWS Lambda on schedule
- Manual execution
"""
import asyncio
import argparse
import sys
from datetime import datetime
from production_ingestion import ProductionDataPipeline
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_daily_ingestion():
    """
    Daily ingestion job - fetches comprehensive data from all sources.
    Recommended schedule: Once per day at off-peak hours (e.g., 2 AM UTC)
    """
    logger.info("Starting daily ingestion job")
    
    async with ProductionDataPipeline() as pipeline:
        results = await pipeline.run_full_ingestion(
            artist_queries=["rock", "pop", "jazz", "country", "electronic", "hip hop"],
            venue_cities=["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
                         "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"],
            event_cities=["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"],
            event_keywords=["concert", "music", "live"]
        )
        
        return results


async def run_hourly_ingestion():
    """
    Hourly ingestion job - fetches recent events and updates.
    Recommended schedule: Every hour
    """
    logger.info("Starting hourly ingestion job")
    
    async with ProductionDataPipeline() as pipeline:
        # Focus on events for hourly updates
        results = await pipeline.ingest_and_persist_events(
            cities=["New York", "Los Angeles", "Chicago"],
            keywords=["concert"],
            max_results=100
        )
        
        return {'events': results}


async def run_artist_refresh():
    """
    Artist data refresh - updates artist popularity and metadata.
    Recommended schedule: Twice per week
    """
    logger.info("Starting artist refresh job")
    
    async with ProductionDataPipeline() as pipeline:
        results = await pipeline.ingest_and_persist_artists(
            search_queries=["trending", "top", "popular", "new"],
            max_results_per_query=100
        )
        
        return {'artists': results}


async def run_venue_refresh():
    """
    Venue data refresh - updates venue information.
    Recommended schedule: Once per week
    """
    logger.info("Starting venue refresh job")
    
    async with ProductionDataPipeline() as pipeline:
        results = await pipeline.ingest_and_persist_venues(
            cities=["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                   "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
                   "Nashville", "Miami", "Seattle", "Boston", "Atlanta"],
            max_results_per_city=200
        )
        
        return {'venues': results}


def lambda_handler(event, context):
    """
    AWS Lambda handler for scheduled ingestion.
    
    Event structure:
    {
        "job_type": "daily" | "hourly" | "artist_refresh" | "venue_refresh"
    }
    """
    job_type = event.get('job_type', 'daily')
    
    logger.info(f"Lambda invoked with job_type: {job_type}")
    
    # Map job types to functions
    job_functions = {
        'daily': run_daily_ingestion,
        'hourly': run_hourly_ingestion,
        'artist_refresh': run_artist_refresh,
        'venue_refresh': run_venue_refresh
    }
    
    if job_type not in job_functions:
        logger.error(f"Invalid job_type: {job_type}")
        return {
            'statusCode': 400,
            'body': f'Invalid job_type: {job_type}'
        }
    
    try:
        # Run the appropriate job
        results = asyncio.run(job_functions[job_type]())
        
        return {
            'statusCode': 200,
            'body': {
                'message': f'{job_type} ingestion completed successfully',
                'results': results
            }
        }
    except Exception as e:
        logger.error(f"Job failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'message': f'{job_type} ingestion failed',
                'error': str(e)
            }
        }


async def main():
    """CLI entry point for manual execution."""
    parser = argparse.ArgumentParser(description='Run scheduled data ingestion jobs')
    parser.add_argument(
        '--job-type',
        choices=['daily', 'hourly', 'artist_refresh', 'venue_refresh'],
        default='daily',
        help='Type of ingestion job to run'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Running {args.job_type} ingestion job")
    
    # Map job types to functions
    job_functions = {
        'daily': run_daily_ingestion,
        'hourly': run_hourly_ingestion,
        'artist_refresh': run_artist_refresh,
        'venue_refresh': run_venue_refresh
    }
    
    try:
        results = await job_functions[args.job_type]()
        
        print("\n" + "=" * 60)
        print(f"{args.job_type.upper()} INGESTION COMPLETED")
        print("=" * 60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        
        if 'summary' in results:
            print(f"\nTotal Records Fetched: {results['summary']['total_records_fetched']}")
            print(f"Total Records Saved to S3: {results['summary']['total_records_saved_to_s3']}")
            print(f"Total Records Streamed to Kinesis: {results['summary']['total_records_streamed_to_kinesis']}")
            print(f"Total Errors: {results['summary']['total_errors']}")
        else:
            for key, value in results.items():
                if isinstance(value, dict) and 'records_fetched' in value:
                    print(f"\n{key.upper()}:")
                    print(f"  Records Fetched: {value['records_fetched']}")
                    print(f"  Saved to S3: {value['records_saved_to_s3']}")
                    print(f"  Streamed to Kinesis: {value['records_streamed_to_kinesis']}")
        
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Job failed: {str(e)}", exc_info=True)
        print(f"\nERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))