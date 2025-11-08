"""
Example usage and validation of the data models.
This file demonstrates how to use the Pydantic models and their validation features.
"""
from datetime import datetime, date
from typing import Dict, Any

from .artist import Artist
from .venue import Venue, Location
from .concert import Concert
from .ticket_sale import TicketSale


def create_sample_artist() -> Artist:
    """Create a sample artist with valid data."""
    return Artist(
        artist_id="art_001",
        name="The Rolling Stones",
        genre=["rock", "blues rock"],
        popularity_score=85.5,
        formation_date=date(1962, 7, 12),
        members=["Mick Jagger", "Keith Richards", "Charlie Watts", "Ronnie Wood"],
        spotify_id="22bE4uQ6baNwSHPVcDxLCe"
    )


def create_sample_venue() -> Venue:
    """Create a sample venue with valid data."""
    location = Location(
        address="4 Pennsylvania Plaza",
        city="New York",
        state="NY",
        country="USA",
        postal_code="10001",
        latitude=40.7505,
        longitude=-73.9934
    )
    
    return Venue(
        venue_id="ven_001",
        name="Madison Square Garden",
        location=location,
        capacity=20789,
        venue_type="arena",
        amenities=["parking", "concessions", "merchandise", "vip_boxes"],
        ticketmaster_id="KovZpZAEkJ7A"
    )


def create_sample_concert() -> Concert:
    """Create a sample concert with valid data."""
    return Concert(
        concert_id="con_001",
        artist_id="art_001",
        venue_id="ven_001",
        event_date=datetime(2024, 7, 15, 20, 0, 0),
        ticket_prices={
            "general": 75.0,
            "premium": 125.0,
            "vip": 250.0
        },
        total_attendance=18500,
        revenue=1875000.0,
        status="completed"
    )


def create_sample_ticket_sale() -> TicketSale:
    """Create a sample ticket sale with valid data."""
    return TicketSale(
        sale_id="sale_001",
        concert_id="con_001",
        price_tier="premium",
        quantity=2,
        unit_price=125.0,
        purchase_timestamp=datetime(2024, 6, 15, 14, 30, 0),
        customer_segment="member"
    )


def validate_all_models() -> Dict[str, Any]:
    """
    Validate all models with sample data and return results.
    
    Returns:
        Dictionary containing validation results for each model.
    """
    results = {}
    
    try:
        artist = create_sample_artist()
        results["artist"] = {
            "valid": True,
            "data": artist.dict(),
            "json": artist.json()
        }
    except Exception as e:
        results["artist"] = {
            "valid": False,
            "error": str(e)
        }
    
    try:
        venue = create_sample_venue()
        results["venue"] = {
            "valid": True,
            "data": venue.dict(),
            "json": venue.json()
        }
    except Exception as e:
        results["venue"] = {
            "valid": False,
            "error": str(e)
        }
    
    try:
        concert = create_sample_concert()
        results["concert"] = {
            "valid": True,
            "data": concert.dict(),
            "json": concert.json()
        }
    except Exception as e:
        results["concert"] = {
            "valid": False,
            "error": str(e)
        }
    
    try:
        ticket_sale = create_sample_ticket_sale()
        results["ticket_sale"] = {
            "valid": True,
            "data": ticket_sale.dict(),
            "total_amount": ticket_sale.total_amount,
            "json": ticket_sale.json()
        }
    except Exception as e:
        results["ticket_sale"] = {
            "valid": False,
            "error": str(e)
        }
    
    return results


if __name__ == "__main__":
    """Run validation examples when script is executed directly."""
    import json
    
    print("Validating all data models...")
    results = validate_all_models()
    
    for model_name, result in results.items():
        print(f"\n{model_name.upper()} Model:")
        if result["valid"]:
            print("✓ Validation successful")
            print(f"JSON representation: {result['json']}")
        else:
            print("✗ Validation failed")
            print(f"Error: {result['error']}")
    
    print("\nAll validations completed.")