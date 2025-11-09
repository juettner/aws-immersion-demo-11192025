"""
Ticket sale data model with validation schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from .base import BaseEntity


class TicketSale(BaseEntity):
    """Ticket sale transaction entity."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sale_id": "sale_001",
                "concert_id": "con_001",
                "customer_id": "cust_001",
                "ticket_tier": "premium",
                "quantity": 2,
                "unit_price": 125.0,
                "total_price": 250.0,
                "purchase_timestamp": "2024-06-15T14:30:00Z",
                "payment_method": "credit_card"
            }
        }
    )
    
    sale_id: str = Field(..., description="Unique sale identifier")
    concert_id: str = Field(..., description="Reference to concert")
    customer_id: str = Field(..., description="Reference to customer")
    ticket_tier: str = Field(..., description="Ticket tier (general, premium, vip, etc.)")
    quantity: int = Field(..., gt=0, le=20, description="Number of tickets purchased")
    unit_price: float = Field(..., gt=0.0, description="Price per ticket")
    total_price: float = Field(..., gt=0.0, description="Total transaction amount")
    purchase_timestamp: datetime = Field(..., description="When the purchase was made")
    payment_method: Optional[str] = Field(None, description="Payment method used")
    
    @field_validator('ticket_tier')
    @classmethod
    def validate_ticket_tier(cls, v):
        """Validate ticket tier."""
        allowed_tiers = ['general', 'premium', 'vip', 'early_bird', 'student', 'standing', 'seated']
        if v.lower() not in allowed_tiers:
            raise ValueError(f'Ticket tier must be one of: {", ".join(allowed_tiers)}')
        return v.lower()
    
    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v, info):
        """Validate total price matches quantity * unit_price."""
        # Note: In Pydantic V2, we use info.data to access other field values
        if hasattr(info, 'data'):
            quantity = info.data.get('quantity')
            unit_price = info.data.get('unit_price')
            if quantity and unit_price:
                expected_total = quantity * unit_price
                if abs(v - expected_total) > 0.01:  # Allow small floating point differences
                    raise ValueError(f'Total price ({v}) does not match quantity * unit_price ({expected_total})')
        return v
    
    @field_validator('unit_price', 'total_price')
    @classmethod
    def validate_prices(cls, v):
        """Validate prices are reasonable."""
        if v > 10000:
            raise ValueError('Price seems unreasonably high')
        return v
    
    @field_validator('purchase_timestamp')
    @classmethod
    def validate_purchase_timestamp(cls, v):
        """Ensure purchase timestamp is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Purchase timestamp cannot be in the future')
        return v
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v):
        """Validate payment method."""
        if v:
            allowed_methods = ['credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay', 'cash', 'other']
            if v.lower() not in allowed_methods:
                raise ValueError(f'Payment method must be one of: {", ".join(allowed_methods)}')
            return v.lower()
        return v