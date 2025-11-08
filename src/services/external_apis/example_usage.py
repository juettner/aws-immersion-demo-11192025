"""
Example usage of external API connectors.
"""
import asyncio
import json
from typing import Dict, Any

from .ingestion_service import DataIngestionService
from .spotify_client import SpotifyClient
from .ticketmaster_client import TicketmasterClient
from ...config.settings import settings


async def example_spotify_usage():
    """Example of using Spotify client directly."""
    print("=== Spotify API Example ===")
    
    if not settings.external_apis.spotify_client_id or not settings.external_apis.spotify_client_secret:
        print("Spotify credentials not configured. Set API_SPOTIFY_CLIENT_ID and API_SPOTIFY_CLIENT_SECRET environment variables.")
        return
    
    async with SpotifyClient(
        client_id=settings.external_apis.spotify_client_id,
        client_secret=settings.external_apis.spotify_client_secret
    ) as spotify:
        
        # Search for artists
        print("\n1. Searching for rock artists...")
        response = await spotify.search_artists("rock", limit=5)
        
        if response.success:
            artists = response.data.get("normalized_artists", [])
            print(f"Found {len(artists)} artists:")
            for artist in artists[:3]:  # Show first 3
                print(f"  - {artist['name']} (Popularity: {artist['popularity_score']})")
        else:
            print(f"Search failed: {response.error}")
        
        # Get specific artist details
        if response.success and artists:
            artist_id = artists[0]["spotify_id"]
            print(f"\n2. Getting details for artist ID: {artist_id}")
            
            detail_response = await spotify.get_artist(artist_id)
            if detail_response.success:
                artist_detail = detail_response.data.get("normalized_artist")
                print(f"Artist: {artist_detail['name']}")
                print(f"Genres: {', '.join(artist_detail['genre'])}")
                print(f"Popularity: {artist_detail['popularity_score']}")
            else:
                print(f"Failed to get artist details: {detail_response.error}")


async def example_ticketmaster_usage():
    """Example of using Ticketmaster client directly."""
    print("\n=== Ticketmaster API Example ===")
    
    if not settings.external_apis.ticketmaster_api_key:
        print("Ticketmaster API key not configured. Set API_TICKETMASTER_API_KEY environment variable.")
        return
    
    async with TicketmasterClient(
        api_key=settings.external_apis.ticketmaster_api_key
    ) as ticketmaster:
        
        # Search for venues
        print("\n1. Searching for venues in New York...")
        response = await ticketmaster.search_venues(city="New York", size=5)
        
        if response.success:
            venues = response.data.get("normalized_venues", [])
            print(f"Found {len(venues)} venues:")
            for venue in venues[:3]:  # Show first 3
                print(f"  - {venue['name']} (Capacity: {venue['capacity']}, Type: {venue['venue_type']})")
        else:
            print(f"Venue search failed: {response.error}")
        
        # Search for music events
        print("\n2. Searching for music events...")
        event_response = await ticketmaster.search_events(
            classification_name="Music",
            city="New York",
            size=5
        )
        
        if event_response.success:
            events = event_response.data.get("normalized_events", [])
            print(f"Found {len(events)} events:")
            for event in events[:3]:  # Show first 3
                event_date = event.get("event_date", "Unknown date")
                print(f"  - Concert ID: {event['concert_id']} (Date: {event_date})")
        else:
            print(f"Event search failed: {event_response.error}")


async def example_ingestion_service_usage():
    """Example of using the comprehensive ingestion service."""
    print("\n=== Data Ingestion Service Example ===")
    
    async with DataIngestionService() as ingestion_service:
        
        # Ingest artist data
        print("\n1. Ingesting artist data...")
        artist_result = await ingestion_service.ingest_artist_data(
            search_queries=["rock", "jazz"],
            max_results_per_query=10
        )
        
        print(f"Artist ingestion result:")
        print(f"  Success: {artist_result.success}")
        print(f"  Records processed: {artist_result.records_processed}")
        print(f"  Records successful: {artist_result.records_successful}")
        print(f"  Errors: {len(artist_result.errors)}")
        
        if artist_result.errors:
            print("  Error details:")
            for error in artist_result.errors[:3]:  # Show first 3 errors
                print(f"    - {error}")
        
        # Ingest venue data
        print("\n2. Ingesting venue data...")
        venue_result = await ingestion_service.ingest_venue_data(
            cities=["New York", "Los Angeles"],
            max_results_per_city=10
        )
        
        print(f"Venue ingestion result:")
        print(f"  Success: {venue_result.success}")
        print(f"  Records processed: {venue_result.records_processed}")
        print(f"  Records successful: {venue_result.records_successful}")
        print(f"  Errors: {len(venue_result.errors)}")
        
        # Comprehensive ingestion
        print("\n3. Running comprehensive ingestion...")
        comprehensive_results = await ingestion_service.ingest_comprehensive_data(
            artist_queries=["rock", "pop"],
            venue_cities=["Chicago"],
            event_cities=["Chicago"],
            event_keywords=["concert"]
        )
        
        print("Comprehensive ingestion results:")
        for data_type, result in comprehensive_results.items():
            print(f"  {data_type.capitalize()}:")
            print(f"    Success: {result.success}")
            print(f"    Records: {result.records_successful}")
            print(f"    Errors: {len(result.errors)}")


def print_sample_data(data: Dict[str, Any], title: str):
    """Print sample data in a formatted way."""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, default=str))


async def main():
    """Main example function."""
    print("External API Connectors Example")
    print("=" * 40)
    
    try:
        # Run individual client examples
        await example_spotify_usage()
        await example_ticketmaster_usage()
        
        # Run ingestion service example
        await example_ingestion_service_usage()
        
    except Exception as e:
        print(f"Example failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())