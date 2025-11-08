"""
Example usage of the recommendation service.

This script demonstrates how to use the recommendation engine for
generating concert, artist, and venue recommendations.
"""
from datetime import datetime, timedelta
from typing import List

from src.models.artist import Artist
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.base import Location
from src.models.recommendation import UserInteraction
from src.services.recommendation_service import RecommendationService, RecommendationStrategy


def create_sample_artists() -> List[Artist]:
    """Create sample artist data."""
    return [
        Artist(
            artist_id="art_001",
            name="The Rolling Stones",
            genre=["rock", "blues rock"],
            popularity_score=85.5,
            members=["Mick Jagger", "Keith Richards"]
        ),
        Artist(
            artist_id="art_002",
            name="Led Zeppelin",
            genre=["rock", "hard rock", "blues rock"],
            popularity_score=88.0,
            members=["Robert Plant", "Jimmy Page"]
        ),
        Artist(
            artist_id="art_003",
            name="Pink Floyd",
            genre=["progressive rock", "psychedelic rock"],
            popularity_score=82.0,
            members=["David Gilmour", "Roger Waters"]
        ),
        Artist(
            artist_id="art_004",
            name="Queen",
            genre=["rock", "glam rock"],
            popularity_score=90.0,
            members=["Freddie Mercury", "Brian May"]
        ),
        Artist(
            artist_id="art_005",
            name="The Beatles",
            genre=["rock", "pop rock"],
            popularity_score=95.0,
            members=["John Lennon", "Paul McCartney"]
        ),
        Artist(
            artist_id="art_006",
            name="Metallica",
            genre=["heavy metal", "thrash metal"],
            popularity_score=87.0,
            members=["James Hetfield", "Lars Ulrich"]
        ),
        Artist(
            artist_id="art_007",
            name="Radiohead",
            genre=["alternative rock", "art rock"],
            popularity_score=79.0,
            members=["Thom Yorke", "Jonny Greenwood"]
        ),
    ]


def create_sample_venues() -> List[Venue]:
    """Create sample venue data."""
    return [
        Venue(
            venue_id="ven_001",
            name="Madison Square Garden",
            location=Location(
                address="4 Pennsylvania Plaza",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001",
                latitude=40.7505,
                longitude=-73.9934
            ),
            capacity=20789,
            venue_type="arena",
            amenities=["parking", "concessions"]
        ),
        Venue(
            venue_id="ven_002",
            name="Red Rocks Amphitheatre",
            location=Location(
                address="18300 W Alameda Pkwy",
                city="Morrison",
                state="CO",
                country="USA",
                postal_code="80465",
                latitude=39.6654,
                longitude=-105.2057
            ),
            capacity=9525,
            venue_type="amphitheater",
            amenities=["outdoor", "scenic"]
        ),
        Venue(
            venue_id="ven_003",
            name="The Forum",
            location=Location(
                address="3900 W Manchester Blvd",
                city="Inglewood",
                state="CA",
                country="USA",
                postal_code="90305",
                latitude=33.9580,
                longitude=-118.3417
            ),
            capacity=17500,
            venue_type="arena",
            amenities=["parking", "vip_boxes"]
        ),
        Venue(
            venue_id="ven_004",
            name="The Troubadour",
            location=Location(
                address="9081 Santa Monica Blvd",
                city="West Hollywood",
                state="CA",
                country="USA",
                postal_code="90069",
                latitude=34.0900,
                longitude=-118.3880
            ),
            capacity=500,
            venue_type="club",
            amenities=["bar", "intimate"]
        ),
    ]


def create_sample_concerts(artists: List[Artist], venues: List[Venue]) -> List[Concert]:
    """Create sample concert data."""
    base_date = datetime.now() + timedelta(days=30)
    concerts = []
    
    concert_mappings = [
        ("art_001", "ven_001", 0),
        ("art_002", "ven_002", 5),
        ("art_003", "ven_003", 10),
        ("art_004", "ven_001", 15),
        ("art_005", "ven_003", 20),
        ("art_006", "ven_002", 25),
        ("art_007", "ven_004", 30),
        ("art_001", "ven_003", 35),
        ("art_003", "ven_002", 40),
    ]
    
    for idx, (artist_id, venue_id, day_offset) in enumerate(concert_mappings):
        concerts.append(
            Concert(
                concert_id=f"con_{idx+1:03d}",
                artist_id=artist_id,
                venue_id=venue_id,
                event_date=base_date + timedelta(days=day_offset),
                ticket_prices={"general": 75.0, "premium": 125.0, "vip": 250.0},
                status="scheduled"
            )
        )
    
    return concerts


def create_sample_interactions() -> List[UserInteraction]:
    """Create sample user interaction data."""
    return [
        # User 1 likes rock classics
        UserInteraction(user_id="user_001", concert_id="con_001", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="user_001", concert_id="con_002", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="user_001", concert_id="con_004", interaction_type="attended", interaction_strength=0.8),
        
        # User 2 likes progressive rock
        UserInteraction(user_id="user_002", concert_id="con_003", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="user_002", concert_id="con_007", interaction_type="attended", interaction_strength=0.9),
        UserInteraction(user_id="user_002", concert_id="con_009", interaction_type="attended", interaction_strength=0.8),
        
        # User 3 likes heavy metal
        UserInteraction(user_id="user_003", concert_id="con_006", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="user_003", concert_id="con_002", interaction_type="attended", interaction_strength=0.7),
        
        # User 4 has similar taste to User 1
        UserInteraction(user_id="user_004", concert_id="con_001", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="user_004", concert_id="con_004", interaction_type="attended", interaction_strength=0.9),
        UserInteraction(user_id="user_004", concert_id="con_005", interaction_type="attended", interaction_strength=0.8),
    ]


def demonstrate_collaborative_filtering(service: RecommendationService):
    """Demonstrate collaborative filtering recommendations."""
    print("\n" + "="*80)
    print("COLLABORATIVE FILTERING RECOMMENDATIONS")
    print("="*80)
    
    # User-based collaborative filtering
    print("\n--- User-Based Collaborative Filtering for user_001 ---")
    user_recs = service.recommend_concerts(
        user_id="user_001",
        strategy=RecommendationStrategy.COLLABORATIVE_USER,
        top_k=5
    )
    
    print(f"Algorithm: {user_recs.algorithm}")
    print(f"Total candidates: {user_recs.total_candidates}")
    print(f"Recommendations ({len(user_recs.recommendations)}):")
    for rec in user_recs.recommendations:
        print(f"  - Concert {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")
    
    # Item-based collaborative filtering
    print("\n--- Item-Based Collaborative Filtering for user_002 ---")
    item_recs = service.recommend_concerts(
        user_id="user_002",
        strategy=RecommendationStrategy.COLLABORATIVE_ITEM,
        top_k=5
    )
    
    print(f"Algorithm: {item_recs.algorithm}")
    print(f"Total candidates: {item_recs.total_candidates}")
    print(f"Recommendations ({len(item_recs.recommendations)}):")
    for rec in item_recs.recommendations:
        print(f"  - Concert {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")


def demonstrate_content_based_filtering(service: RecommendationService):
    """Demonstrate content-based filtering recommendations."""
    print("\n" + "="*80)
    print("CONTENT-BASED FILTERING RECOMMENDATIONS")
    print("="*80)
    
    # Artist-based recommendations
    print("\n--- Artist-Based Recommendations ---")
    print("User likes: The Rolling Stones, Led Zeppelin")
    artist_recs = service.recommend_concerts(
        user_id="content_user",
        strategy=RecommendationStrategy.CONTENT_ARTIST,
        top_k=5,
        user_preferences={
            "preferred_artist_ids": ["art_001", "art_002"],
            "exclude_concert_ids": {"con_001", "con_002"}
        }
    )
    
    print(f"Algorithm: {artist_recs.algorithm}")
    print(f"Total candidates: {artist_recs.total_candidates}")
    print(f"Recommendations ({len(artist_recs.recommendations)}):")
    for rec in artist_recs.recommendations:
        print(f"  - Concert {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")
        if rec.metadata:
            print(f"    Artist: {rec.metadata.get('artist_id')}, Venue: {rec.metadata.get('venue_id')}")
    
    # Venue-based recommendations
    print("\n--- Venue-Based Recommendations ---")
    print("User likes: Madison Square Garden, The Forum")
    venue_recs = service.recommend_concerts(
        user_id="content_user",
        strategy=RecommendationStrategy.CONTENT_VENUE,
        top_k=5,
        user_preferences={
            "preferred_venue_ids": ["ven_001", "ven_003"]
        }
    )
    
    print(f"Algorithm: {venue_recs.algorithm}")
    print(f"Total candidates: {venue_recs.total_candidates}")
    print(f"Recommendations ({len(venue_recs.recommendations)}):")
    for rec in venue_recs.recommendations:
        print(f"  - Concert {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")


def demonstrate_artist_recommendations(service: RecommendationService):
    """Demonstrate artist recommendations."""
    print("\n" + "="*80)
    print("ARTIST RECOMMENDATIONS")
    print("="*80)
    
    print("\n--- Similar Artists to The Rolling Stones and Queen ---")
    artist_recs = service.recommend_artists(
        preferred_artist_ids=["art_001", "art_004"],
        top_k=5
    )
    
    print(f"Recommendations ({len(artist_recs)}):")
    for rec in artist_recs:
        print(f"  - Artist {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")
        if rec.metadata:
            print(f"    Name: {rec.metadata.get('name')}, Genres: {rec.metadata.get('genres')}")


def demonstrate_venue_recommendations(service: RecommendationService):
    """Demonstrate venue recommendations."""
    print("\n" + "="*80)
    print("VENUE RECOMMENDATIONS")
    print("="*80)
    
    print("\n--- Similar Venues to Madison Square Garden ---")
    venue_recs = service.recommend_venues(
        preferred_venue_ids=["ven_001"],
        top_k=3
    )
    
    print(f"Recommendations ({len(venue_recs)}):")
    for rec in venue_recs:
        print(f"  - Venue {rec.item_id}: score={rec.score:.3f}, confidence={rec.confidence:.3f}")
        print(f"    Reasoning: {rec.reasoning}")
        if rec.metadata:
            print(f"    Name: {rec.metadata.get('name')}, Type: {rec.metadata.get('type')}")
            print(f"    Capacity: {rec.metadata.get('capacity')}")


def demonstrate_batch_recommendations(service: RecommendationService):
    """Demonstrate batch recommendations for multiple users."""
    print("\n" + "="*80)
    print("BATCH RECOMMENDATIONS")
    print("="*80)
    
    user_ids = ["user_001", "user_002", "user_003"]
    batch_results = service.recommend_batch(
        user_ids=user_ids,
        strategy=RecommendationStrategy.HYBRID_ALL,
        top_k=3
    )
    
    for user_id, result in batch_results.items():
        print(f"\n--- Recommendations for {user_id} ---")
        print(f"Algorithm: {result.algorithm}")
        print(f"Recommendations ({len(result.recommendations)}):")
        for rec in result.recommendations[:3]:
            print(f"  - Concert {rec.item_id}: score={rec.score:.3f}")


def demonstrate_system_statistics(service: RecommendationService):
    """Display system statistics."""
    print("\n" + "="*80)
    print("SYSTEM STATISTICS")
    print("="*80)
    
    stats = service.get_system_statistics()
    
    print("\nCollaborative Filtering:")
    collab_stats = stats["collaborative_filtering"]
    print(f"  Total users: {collab_stats['total_users']}")
    print(f"  Total items: {collab_stats['total_items']}")
    print(f"  Total interactions: {collab_stats['total_interactions']}")
    print(f"  Matrix sparsity: {collab_stats['sparsity']:.2%}")
    print(f"  Avg interactions per user: {collab_stats['avg_interactions_per_user']:.2f}")
    
    print("\nContent-Based Filtering:")
    content_stats = stats["content_based"]
    print(f"  Total artists: {content_stats['total_artists']}")
    print(f"  Total venues: {content_stats['total_venues']}")
    print(f"  Total concerts: {content_stats['total_concerts']}")


def main():
    """Main demonstration function."""
    print("="*80)
    print("CONCERT RECOMMENDATION ENGINE DEMONSTRATION")
    print("="*80)
    
    # Initialize service
    service = RecommendationService()
    
    # Load sample data
    print("\nLoading sample data...")
    artists = create_sample_artists()
    venues = create_sample_venues()
    concerts = create_sample_concerts(artists, venues)
    interactions = create_sample_interactions()
    
    # Add data to service
    for artist in artists:
        service.add_artist(artist)
    
    for venue in venues:
        service.add_venue(venue)
    
    for concert in concerts:
        service.add_concert(concert)
    
    service.add_interactions_batch(interactions)
    
    print(f"Loaded {len(artists)} artists, {len(venues)} venues, {len(concerts)} concerts")
    print(f"Loaded {len(interactions)} user interactions")
    
    # Run demonstrations
    demonstrate_system_statistics(service)
    demonstrate_collaborative_filtering(service)
    demonstrate_content_based_filtering(service)
    demonstrate_artist_recommendations(service)
    demonstrate_venue_recommendations(service)
    demonstrate_batch_recommendations(service)
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
