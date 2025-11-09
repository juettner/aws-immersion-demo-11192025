"""
Test script to demonstrate the production pipeline flow.
This simulates the full pipeline without actually writing to AWS.
"""
import asyncio
import json
from datetime import datetime
from src.config.environment import load_env_file
from src.services.external_apis.ingestion_service import DataIngestionService

# Load environment variables
load_env_file()

async def simulate_production_pipeline():
    """
    Simulate the production pipeline to show how data flows.
    """
    print("=" * 70)
    print("PRODUCTION PIPELINE SIMULATION")
    print("=" * 70)
    print()
    
    # Step 1: Initialize the ingestion service
    print("Step 1: Initializing Data Ingestion Service...")
    print("-" * 70)
    
    async with DataIngestionService() as service:
        if service.spotify_client:
            print("✓ Spotify client initialized")
        else:
            print("✗ Spotify client not available (credentials missing)")
        
        if service.ticketmaster_client:
            print("✓ Ticketmaster client initialized")
        else:
            print("✗ Ticketmaster client not available (credentials missing)")
        
        print()
        
        # Step 2: Ingest artist data
        print("Step 2: Ingesting Artist Data from Spotify...")
        print("-" * 70)
        
        if service.spotify_client:
            artist_result = await service.ingest_artist_data(
                search_queries=["rock"],
                max_results_per_query=5
            )
            
            print(f"Status: {'SUCCESS' if artist_result.success else 'FAILED'}")
            print(f"Records Processed: {artist_result.records_processed}")
            print(f"Records Successful: {artist_result.records_successful}")
            print(f"Records Failed: {artist_result.records_failed}")
            
            if artist_result.data:
                print(f"\nSample Artist Data (first record):")
                print(json.dumps(artist_result.data[0], indent=2, default=str))
                
                # Simulate S3 save
                print(f"\n→ Would save to S3:")
                timestamp = datetime.utcnow()
                s3_key = (
                    f"s3://concert-data-raw/raw/spotify/artists/"
                    f"year={timestamp.year}/month={timestamp.month:02d}/"
                    f"day={timestamp.day:02d}/artists_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"  Location: {s3_key}")
                print(f"  Records: {len(artist_result.data)}")
                
                # Simulate Kinesis stream
                print(f"\n→ Would stream to Kinesis:")
                print(f"  Stream: concert-data-stream")
                print(f"  Records: {len(artist_result.data)}")
                print(f"  Partition Keys: artist_id")
            
            if artist_result.errors:
                print(f"\nErrors encountered:")
                for error in artist_result.errors[:3]:
                    print(f"  - {error}")
        else:
            print("Skipping - Spotify client not available")
        
        print()
        
        # Step 3: Ingest venue data
        print("Step 3: Ingesting Venue Data from Ticketmaster...")
        print("-" * 70)
        
        if service.ticketmaster_client:
            venue_result = await service.ingest_venue_data(
                cities=["New York"],
                max_results_per_city=5
            )
            
            print(f"Status: {'SUCCESS' if venue_result.success else 'FAILED'}")
            print(f"Records Processed: {venue_result.records_processed}")
            print(f"Records Successful: {venue_result.records_successful}")
            print(f"Records Failed: {venue_result.records_failed}")
            
            if venue_result.data:
                print(f"\nSample Venue Data (first record):")
                print(json.dumps(venue_result.data[0], indent=2, default=str))
                
                # Simulate S3 save
                print(f"\n→ Would save to S3:")
                timestamp = datetime.utcnow()
                s3_key = (
                    f"s3://concert-data-raw/raw/ticketmaster/venues/"
                    f"year={timestamp.year}/month={timestamp.month:02d}/"
                    f"day={timestamp.day:02d}/venues_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"  Location: {s3_key}")
                print(f"  Records: {len(venue_result.data)}")
                
                # Simulate Kinesis stream
                print(f"\n→ Would stream to Kinesis:")
                print(f"  Stream: concert-data-stream")
                print(f"  Records: {len(venue_result.data)}")
                print(f"  Partition Keys: venue_id")
            
            if venue_result.errors:
                print(f"\nErrors encountered:")
                for error in venue_result.errors[:3]:
                    print(f"  - {error}")
        else:
            print("Skipping - Ticketmaster client not available")
        
        print()
        
        # Step 4: Ingest event data
        print("Step 4: Ingesting Event Data from Ticketmaster...")
        print("-" * 70)
        
        if service.ticketmaster_client:
            event_result = await service.ingest_event_data(
                cities=["New York"],
                keywords=["concert"],
                max_results=5
            )
            
            print(f"Status: {'SUCCESS' if event_result.success else 'FAILED'}")
            print(f"Records Processed: {event_result.records_processed}")
            print(f"Records Successful: {event_result.records_successful}")
            print(f"Records Failed: {event_result.records_failed}")
            
            if event_result.data:
                print(f"\nSample Event Data (first record):")
                print(json.dumps(event_result.data[0], indent=2, default=str))
                
                # Simulate S3 save
                print(f"\n→ Would save to S3:")
                timestamp = datetime.utcnow()
                s3_key = (
                    f"s3://concert-data-raw/raw/ticketmaster/events/"
                    f"year={timestamp.year}/month={timestamp.month:02d}/"
                    f"day={timestamp.day:02d}/events_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"  Location: {s3_key}")
                print(f"  Records: {len(event_result.data)}")
                
                # Simulate Kinesis stream
                print(f"\n→ Would stream to Kinesis:")
                print(f"  Stream: concert-data-stream")
                print(f"  Records: {len(event_result.data)}")
                print(f"  Partition Keys: concert_id")
            
            if event_result.errors:
                print(f"\nErrors encountered:")
                for error in event_result.errors[:3]:
                    print(f"  - {error}")
        else:
            print("Skipping - Ticketmaster client not available")
        
        print()
        print("=" * 70)
        print("PIPELINE SIMULATION COMPLETE")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("  1. Data in S3 would be processed by AWS Glue ETL jobs")
        print("  2. Kinesis stream would trigger Lambda functions")
        print("  3. Processed data would be loaded into Redshift")
        print("  4. Analytics and ML models would use the data")
        print()


if __name__ == "__main__":
    asyncio.run(simulate_production_pipeline())