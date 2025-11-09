"""
Demo script showing the production data flow with actual API calls.
"""
import asyncio
import json
import os
from datetime import datetime

# Load environment first
from src.config.environment import load_env_file
load_env_file()

# Now import the clients
from src.services.external_apis.spotify_client import SpotifyClient
from src.services.external_apis.ticketmaster_client import TicketmasterClient


async def demo_production_flow():
    """
    Demonstrate the complete production data flow.
    """
    print("=" * 80)
    print("PRODUCTION DATA FLOW DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Get credentials from environment
    spotify_client_id = os.getenv('API_SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('API_SPOTIFY_CLIENT_SECRET')
    ticketmaster_api_key = os.getenv('API_TICKETMASTER_API_KEY')
    
    print("Configuration:")
    print(f"  Spotify Client ID: {spotify_client_id[:10]}..." if spotify_client_id else "  Spotify: Not configured")
    print(f"  Ticketmaster API Key: {ticketmaster_api_key[:10]}..." if ticketmaster_api_key else "  Ticketmaster: Not configured")
    print(f"  S3 Bucket: {os.getenv('AWS_S3_BUCKET_RAW', 'concert-data-raw')}")
    print(f"  Kinesis Stream: {os.getenv('AWS_KINESIS_STREAM_NAME', 'concert-data-stream')}")
    print()
    
    # Demo 1: Spotify Artist Ingestion
    if spotify_client_id and spotify_client_secret:
        print("-" * 80)
        print("DEMO 1: Spotify Artist Data Ingestion")
        print("-" * 80)
        
        async with SpotifyClient(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret
        ) as spotify:
            # Search for artists
            print("\n1. Fetching artist data from Spotify API...")
            response = await spotify.search_artists("rock", limit=3)
            
            if response.success:
                artists = response.data.get("normalized_artists", [])
                print(f"   ✓ Successfully fetched {len(artists)} artists")
                
                # Show sample data
                if artists:
                    print(f"\n2. Sample Artist Data:")
                    sample_artist = artists[0]
                    print(f"   Name: {sample_artist['name']}")
                    print(f"   ID: {sample_artist['artist_id']}")
                    print(f"   Genres: {', '.join(sample_artist['genre'][:3])}")
                    print(f"   Popularity: {sample_artist['popularity_score']}")
                    
                    # Show where it would be saved
                    timestamp = datetime.utcnow()
                    s3_path = (
                        f"s3://concert-data-raw/raw/spotify/artists/"
                        f"year={timestamp.year}/month={timestamp.month:02d}/"
                        f"day={timestamp.day:02d}/"
                        f"artists_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    
                    print(f"\n3. Data Persistence:")
                    print(f"   → S3 Location: {s3_path}")
                    print(f"   → Kinesis Stream: concert-data-stream")
                    print(f"   → Partition Key: {sample_artist['artist_id']}")
                    
                    print(f"\n4. Downstream Processing:")
                    print(f"   → AWS Glue would process the S3 data")
                    print(f"   → Lambda would process Kinesis stream in real-time")
                    print(f"   → Redshift would store for analytics")
                    
                    # Show full record structure
                    print(f"\n5. Complete Record Structure:")
                    print(json.dumps(sample_artist, indent=2, default=str))
            else:
                print(f"   ✗ Failed: {response.error}")
    else:
        print("Skipping Spotify demo - credentials not configured")
    
    print()
    
    # Demo 2: Ticketmaster Venue Ingestion
    if ticketmaster_api_key:
        print("-" * 80)
        print("DEMO 2: Ticketmaster Venue Data Ingestion")
        print("-" * 80)
        
        async with TicketmasterClient(api_key=ticketmaster_api_key) as tm:
            # Search for venues
            print("\n1. Fetching venue data from Ticketmaster API...")
            response = await tm.search_venues(city="New York", size=3)
            
            if response.success:
                venues = response.data.get("normalized_venues", [])
                print(f"   ✓ Successfully fetched {len(venues)} venues")
                
                # Show sample data
                if venues:
                    print(f"\n2. Sample Venue Data:")
                    sample_venue = venues[0]
                    print(f"   Name: {sample_venue['name']}")
                    print(f"   ID: {sample_venue['venue_id']}")
                    print(f"   Location: {sample_venue.get('city', 'N/A')}, {sample_venue.get('state', 'N/A')}")
                    print(f"   Capacity: {sample_venue['capacity']}")
                    print(f"   Type: {sample_venue['venue_type']}")
                    
                    # Show where it would be saved
                    timestamp = datetime.utcnow()
                    s3_path = (
                        f"s3://concert-data-raw/raw/ticketmaster/venues/"
                        f"year={timestamp.year}/month={timestamp.month:02d}/"
                        f"day={timestamp.day:02d}/"
                        f"venues_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    
                    print(f"\n3. Data Persistence:")
                    print(f"   → S3 Location: {s3_path}")
                    print(f"   → Kinesis Stream: concert-data-stream")
                    print(f"   → Partition Key: {sample_venue['venue_id']}")
                    
                    # Show full record structure
                    print(f"\n4. Complete Record Structure:")
                    print(json.dumps(sample_venue, indent=2, default=str))
            else:
                print(f"   ✗ Failed: {response.error}")
    else:
        print("Skipping Ticketmaster demo - credentials not configured")
    
    print()
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  • Data is fetched from external APIs with rate limiting and retry logic")
    print("  • Raw data is saved to S3 in partitioned structure for data lake")
    print("  • Normalized data is streamed to Kinesis for real-time processing")
    print("  • AWS Glue processes S3 data for batch ETL")
    print("  • AWS Lambda processes Kinesis stream for real-time events")
    print("  • Final data lands in Redshift for analytics and ML")
    print()


if __name__ == "__main__":
    asyncio.run(demo_production_flow())