"""
Example usage of External Data Enrichment Service.
"""
import asyncio
from external_data_enrichment_service import ExternalDataEnrichmentService


async def main():
    """Demonstrate external data enrichment capabilities."""
    print("=== External Data Enrichment Service Demo ===\n")
    
    # Initialize service from settings
    service = ExternalDataEnrichmentService.from_settings()
    
    try:
        # Example 1: Enrich artist data
        print("1. Enriching artist data for 'Metallica'...")
        artist_result = await service.enrich_artist_data(artist_name="Metallica")
        print(f"   Success: {artist_result.success}")
        print(f"   Source: {artist_result.source}")
        print(f"   Cached: {artist_result.cached}")
        if artist_result.data:
            print(f"   Artist: {artist_result.data.get('name')}")
            print(f"   Popularity: {artist_result.data.get('popularity_score')}")
            print(f"   Genres: {', '.join(artist_result.data.get('genre', []))}")
        print()
        
        # Example 2: Enrich artist data again (should use cache)
        print("2. Enriching same artist data (should use cache)...")
        artist_result_cached = await service.enrich_artist_data(artist_name="Metallica")
        print(f"   Success: {artist_result_cached.success}")
        print(f"   Source: {artist_result_cached.source}")
        print(f"   Cached: {artist_result_cached.cached}")
        print()
        
        # Example 3: Enrich venue data
        print("3. Enriching venue data for 'Madison Square Garden'...")
        venue_result = await service.enrich_venue_data(
            venue_name="Madison Square Garden",
            city="New York"
        )
        print(f"   Success: {venue_result.success}")
        print(f"   Source: {venue_result.source}")
        print(f"   Cached: {venue_result.cached}")
        if venue_result.data:
            print(f"   Venue: {venue_result.data.get('name')}")
            print(f"   City: {venue_result.data.get('city')}")
            print(f"   Capacity: {venue_result.data.get('capacity')}")
        print()
        
        # Example 4: Enrich concert data
        print("4. Enriching concert data for 'Taylor Swift' in 'Los Angeles'...")
        concert_result = await service.enrich_concert_data(
            artist_name="Taylor Swift",
            city="Los Angeles"
        )
        print(f"   Success: {concert_result.success}")
        print(f"   Source: {concert_result.source}")
        print(f"   Cached: {concert_result.cached}")
        if concert_result.data:
            event_count = concert_result.data.get('count', 0)
            print(f"   Events found: {event_count}")
            if event_count > 0:
                events = concert_result.data.get('events', [])
                for i, event in enumerate(events[:3], 1):
                    print(f"   Event {i}: {event.get('raw_data', {}).get('name', 'N/A')}")
        print()
        
        # Example 5: Cache statistics
        print("5. Cache statistics:")
        stats = service.get_cache_stats()
        print(f"   Cache size: {stats['size']}/{stats['max_size']}")
        print(f"   TTL: {stats['ttl_minutes']} minutes")
        print()
        
        # Example 6: Clear cache
        print("6. Clearing cache...")
        service.clear_cache()
        stats_after = service.get_cache_stats()
        print(f"   Cache size after clear: {stats_after['size']}")
        print()
        
        # Example 7: Test fallback behavior (with invalid data)
        print("7. Testing fallback behavior with non-existent artist...")
        fallback_result = await service.enrich_artist_data(
            artist_name="NonExistentArtist12345XYZ"
        )
        print(f"   Success: {fallback_result.success}")
        print(f"   Source: {fallback_result.source}")
        if fallback_result.data:
            print(f"   Note: {fallback_result.data.get('note', 'N/A')}")
        print()
        
    finally:
        # Cleanup
        await service.close()
        print("Service closed successfully")


if __name__ == "__main__":
    asyncio.run(main())
