"""
Data models package for the concert data platform.

This package contains all the core data models with Pydantic validation:
- Artist: Musical artists and bands
- Venue: Concert venues and locations
- Concert: Concert events linking artists and venues
- TicketSale: Individual ticket purchase transactions
"""

from .base import BaseEntity, Location
from .artist import Artist
from .venue import Venue
from .concert import Concert
from .ticket_sale import TicketSale

__all__ = [
    'BaseEntity',
    'Location',
    'Artist',
    'Venue', 
    'Concert',
    'TicketSale'
]