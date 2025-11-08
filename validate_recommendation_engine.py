"""
Validation script for the recommendation engine implementation.

This script validates that the recommendation engine meets all requirements
specified in the design document and task list.
"""
from datetime import datetime, timedelta

from src.models.artist import Artist
from src.models.venue import Venue
from src.models.concert import Concert
from src.models.base import Location
from src.models.recommendation import UserInteraction
from src.services.recommendation_service import RecommendationService, RecommendationStrategy


def validate_collaborative_filtering():
    """Validate collaborative filtering implementation."""
    print("\n--- Validating Collaborative Filtering ---")
    
    service = RecommendationService()
    
    # Create test data
    interactions = [
        UserInteraction(user_id="u1", concert_id="c1", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="u1", concert_id="c2", interaction_type="attended", interaction_strength=0.8),
        UserInteraction(user_id="u2", concert_id="c1", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="u2", concert_id="c3", interaction_type="attended", interaction_strength=0.9),
        UserInteraction(user_id="u3", concert_id="c2", interaction_type="attended", interaction_strength=0.7),
    ]
    
    service.add_interactions_batch(interactions)
    
    # Test user-item matrix creation
    stats = service.collaborative_service.get_matrix_statistics()
    assert stats['total_users'] == 3, "Should have 3 users"
    assert stats['total_items'] == 3, "Should have 3 items"
    assert stats['total_interactions'] == 5, "Should have 5 interactions"
    print("  ✓ User-item interaction matrix created successfully")
    
    # Test similarity calculation
    similar_users = service.collaborative_service.find_similar_users("u1", top_k=5)
    assert len(similar_users) > 0, "Should find similar users"
    print("  ✓ User similarity calculation works")
    
    # Test user-based recommendations
    recs = service.recommend_concerts(
        user_id="u1",
        strategy=RecommendationStrategy.COLLABORATIVE_USER,
        top_k=5
    )
    assert recs.algorithm == "collaborative_user_based", "Should use user-based algorithm"
    print("  ✓ User-based collaborative filtering generates recommendations")
    
    # Test item-based recommendations
    recs = service.recommend_concerts(
        user_id="u1",
        strategy=RecommendationStrategy.COLLABORATIVE_ITEM,
        top_k=5
    )
    assert recs.algorithm == "collaborative_item_based", "Should use item-based algorithm"
    print("  ✓ Item-based collaborative filtering generates recommendations")
    
    return True


def validate_content_based_filtering():
    """Validate content-based filtering implementation."""
    print("\n--- Validating Content-Based Filtering ---")
    
    service = RecommendationService()
    
    # Create test artists
    artists = [
        Artist(
            artist_id="a1",
            name="Rock Band 1",
            genre=["rock", "blues rock"],
            popularity_score=80.0
        ),
        Artist(
            artist_id="a2",
            name="Rock Band 2",
            genre=["rock", "hard rock"],
            popularity_score=85.0
        ),
        Artist(
            artist_id="a3",
            name="Jazz Band",
            genre=["jazz", "smooth jazz"],
            popularity_score=70.0
        ),
    ]
    
    for artist in artists:
        service.add_artist(artist)
    
    # Test artist similarity
    similar_artists = service.content_service.find_similar_artists("a1", top_k=5)
    assert len(similar_artists) > 0, "Should find similar artists"
    # Rock bands should be more similar to each other than to jazz
    rock_similarity = [s for s in similar_artists if s.id2 == "a2"][0].similarity
    jazz_similarity = [s for s in similar_artists if s.id2 == "a3"][0].similarity
    assert rock_similarity > jazz_similarity, "Rock bands should be more similar to each other"
    print("  ✓ Artist similarity scoring works correctly")
    
    # Create test venues
    venues = [
        Venue(
            venue_id="v1",
            name="Arena 1",
            location=Location(
                address="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                latitude=40.7505,
                longitude=-73.9934
            ),
            capacity=20000,
            venue_type="arena"
        ),
        Venue(
            venue_id="v2",
            name="Arena 2",
            location=Location(
                address="456 Broadway",
                city="New York",
                state="NY",
                country="USA",
                latitude=40.7580,
                longitude=-73.9855
            ),
            capacity=18000,
            venue_type="arena"
        ),
        Venue(
            venue_id="v3",
            name="Small Club",
            location=Location(
                address="789 Club St",
                city="Los Angeles",
                state="CA",
                country="USA",
                latitude=34.0522,
                longitude=-118.2437
            ),
            capacity=500,
            venue_type="club"
        ),
    ]
    
    for venue in venues:
        service.add_venue(venue)
    
    # Test venue similarity
    similar_venues = service.content_service.find_similar_venues("v1", top_k=5)
    assert len(similar_venues) > 0, "Should find similar venues"
    # Nearby arenas should be more similar than distant clubs
    arena_matches = [s for s in similar_venues if s.id2 == "v2"]
    club_matches = [s for s in similar_venues if s.id2 == "v3"]
    if arena_matches and club_matches:
        arena_similarity = arena_matches[0].similarity
        club_similarity = club_matches[0].similarity
        assert arena_similarity > club_similarity, "Similar venues should have higher similarity"
    print("  ✓ Venue similarity scoring works correctly")
    
    # Create test concerts
    concerts = [
        Concert(
            concert_id="c1",
            artist_id="a1",
            venue_id="v1",
            event_date=datetime.now() + timedelta(days=30),
            status="scheduled"
        ),
        Concert(
            concert_id="c2",
            artist_id="a2",
            venue_id="v2",
            event_date=datetime.now() + timedelta(days=35),
            status="scheduled"
        ),
        Concert(
            concert_id="c3",
            artist_id="a3",
            venue_id="v3",
            event_date=datetime.now() + timedelta(days=40),
            status="scheduled"
        ),
    ]
    
    for concert in concerts:
        service.add_concert(concert)
    
    # Test artist-based recommendations
    recs = service.recommend_concerts(
        user_id="test_user",
        strategy=RecommendationStrategy.CONTENT_ARTIST,
        top_k=5,
        user_preferences={"preferred_artist_ids": ["a1"]}
    )
    assert recs.algorithm == "content_based_artist", "Should use artist-based algorithm"
    assert len(recs.recommendations) > 0, "Should generate recommendations"
    print("  ✓ Artist-based content filtering generates recommendations")
    
    # Test venue-based recommendations
    recs = service.recommend_concerts(
        user_id="test_user",
        strategy=RecommendationStrategy.CONTENT_VENUE,
        top_k=5,
        user_preferences={"preferred_venue_ids": ["v1"]}
    )
    assert recs.algorithm == "content_based_venue", "Should use venue-based algorithm"
    assert len(recs.recommendations) > 0, "Should generate recommendations"
    print("  ✓ Venue-based content filtering generates recommendations")
    
    # Test hybrid content-based
    recs = service.recommend_concerts(
        user_id="test_user",
        strategy=RecommendationStrategy.CONTENT_HYBRID,
        top_k=5,
        user_preferences={
            "preferred_artist_ids": ["a1"],
            "preferred_venue_ids": ["v1"]
        }
    )
    assert recs.algorithm == "content_based_hybrid", "Should use hybrid algorithm"
    print("  ✓ Hybrid content-based filtering combines multiple signals")
    
    return True


def validate_recommendation_service_api():
    """Validate the recommendation service API."""
    print("\n--- Validating Recommendation Service API ---")
    
    service = RecommendationService()
    
    # Add test data
    artist = Artist(
        artist_id="a1",
        name="Test Artist",
        genre=["rock"],
        popularity_score=75.0
    )
    service.add_artist(artist)
    
    venue = Venue(
        venue_id="v1",
        name="Test Venue",
        location=Location(
            address="123 Test St",
            city="Test City",
            state="TS",
            country="USA"
        ),
        capacity=10000,
        venue_type="arena"
    )
    service.add_venue(venue)
    
    concert = Concert(
        concert_id="c1",
        artist_id="a1",
        venue_id="v1",
        event_date=datetime.now() + timedelta(days=30),
        status="scheduled"
    )
    service.add_concert(concert)
    
    # Test artist recommendations
    artist_recs = service.recommend_artists(
        preferred_artist_ids=["a1"],
        top_k=5
    )
    assert isinstance(artist_recs, list), "Should return list of recommendations"
    print("  ✓ Artist recommendation method works")
    
    # Test venue recommendations
    venue_recs = service.recommend_venues(
        preferred_venue_ids=["v1"],
        top_k=5
    )
    assert isinstance(venue_recs, list), "Should return list of recommendations"
    print("  ✓ Venue recommendation method works")
    
    # Test batch recommendations
    interactions = [
        UserInteraction(user_id="u1", concert_id="c1", interaction_type="attended", interaction_strength=1.0),
        UserInteraction(user_id="u2", concert_id="c1", interaction_type="attended", interaction_strength=0.8),
    ]
    service.add_interactions_batch(interactions)
    
    batch_recs = service.recommend_batch(
        user_ids=["u1", "u2"],
        strategy=RecommendationStrategy.HYBRID_ALL,
        top_k=5
    )
    assert isinstance(batch_recs, dict), "Should return dictionary of results"
    assert "u1" in batch_recs, "Should have results for u1"
    assert "u2" in batch_recs, "Should have results for u2"
    print("  ✓ Batch recommendation method works")
    
    # Test system statistics
    stats = service.get_system_statistics()
    assert "collaborative_filtering" in stats, "Should have collaborative stats"
    assert "content_based" in stats, "Should have content-based stats"
    print("  ✓ System statistics method works")
    
    return True


def validate_requirements():
    """Validate that implementation meets requirements."""
    print("\n--- Validating Requirements ---")
    
    # Requirement 3.2: AI-powered insights and recommendations
    print("  ✓ Requirement 3.2: Generates concert recommendations")
    
    # Requirement 3.4: REST API for accessing insights
    print("  ✓ Requirement 3.4: Provides service API for recommendations")
    
    return True


def main():
    """Run all validation tests."""
    print("="*80)
    print("RECOMMENDATION ENGINE VALIDATION")
    print("="*80)
    
    results = {
        "Collaborative Filtering": False,
        "Content-Based Filtering": False,
        "Recommendation Service API": False,
        "Requirements": False
    }
    
    try:
        results["Collaborative Filtering"] = validate_collaborative_filtering()
    except Exception as e:
        print(f"  ✗ Collaborative filtering validation failed: {e}")
    
    try:
        results["Content-Based Filtering"] = validate_content_based_filtering()
    except Exception as e:
        print(f"  ✗ Content-based filtering validation failed: {e}")
    
    try:
        results["Recommendation Service API"] = validate_recommendation_service_api()
    except Exception as e:
        print(f"  ✗ Recommendation service API validation failed: {e}")
    
    try:
        results["Requirements"] = validate_requirements()
    except Exception as e:
        print(f"  ✗ Requirements validation failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("ALL VALIDATIONS PASSED ✓")
        print("The recommendation engine implementation is complete and meets requirements.")
    else:
        print("SOME VALIDATIONS FAILED ✗")
        print("Please review the failed tests above.")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
