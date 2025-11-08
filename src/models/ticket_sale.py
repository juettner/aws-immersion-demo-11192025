"""
Ticket sale data model with validation schemas.
"""
from datetime import datetime
from pydantic import Field, validator
from .base import BaseEntity


class TicketSale(BaseEntity):
    """Individual ticket sale transaction."""
    sale_id: str = Field(..., description="Unique sale transaction identifier")
    concert_id: str = Field(..., description="Reference to the concert")
    price_tier: str = Field(..., description="Ticket price tier (general, premium, vip, etc.)")
    quantity: int = Field(..., gt=0, le=50, description="Number of tickets purchased")
    unit_price: float = Field(..., gt=0.0, description="Price per individual ticket")
    purchase_timestamp: datetime = Field(..., description="When the purchase was made")
    customer_segment: str = Field(
        default="general", 
        description="Customer segment (general, member, corporate, etc.)"
    )
    
    @validator('price_tier')
    def validate_price_tier(cls, v):
        """Validate price tier format."""
        if not v or not v.strip():
            raise ValueError('Price tier cannot be empty')
        return v.strip().lower()
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        """Validate ticket price."""
        if v > 10000:  # Reasonable upper limit for individual tickets
            raise ValueError('Unit price seems unreasonably high')
        return v
    
    @validator('customer_segment')
    def validate_customer_segment(cls, v):
        """Validate customer segment."""
        allowed_segments = ['general', 'member', 'corporate', 'student', 'senior', 'vip']
        if v.lower() not in allowed_segments:
            raise ValueError(f'Customer segment must be one of: {", ".join(allowed_segments)}')
        return v.lower()
    
    @validator('purchase_timestamp')
    def validate_purchase_timestamp(cls, v):
        """Ensure purchase timestamp is reasonable."""
        now = datetime.utcnow()
        # Allow purchases up to 10 years in the past and not in the future
        if v.year < now.year - 10:
            raise ValueError('Purchase timestamp is too far in the past')
        if v > now:
            raise ValueError('Purchase timestamp cannot be in the future')
        return v
    
    @property
    def total_amount(self) -> float:
        """Calculate total purchase amount."""
        return self.quantity * self.unit_price
    
    class Config:
        schema_extra = {
            "example": {
                "sale_id": "sale_001",
                "concert_id": "con_001",
                "price_tier": "premium",
                "quantity": 2,
                "unit_price": 125.0,
                "purchase_timestamp": "2024-06-15T14:30:00Z",
                "customer_segment": "member"
            }
        }