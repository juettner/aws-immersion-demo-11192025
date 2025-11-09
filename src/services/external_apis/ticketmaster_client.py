"""
Ticketmaster API client for venue and event data ingestion.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import structlog
from pydantic import BaseModel

from .base_client import APIClient, APIResponse
from ...models.venue import Venue
from ...models.concert import Concert
from ...models.base import Location

logger = structlog.get_logger(__name__)


class TicketmasterVenueData(BaseModel):
    """Raw Ticketmaster venue data structure."""
    id: str
    name: str
    type: str
    url: Optional[str]
    locale: Optional[str]
    timezone: Optional[str]
    city: Optional[Dict[str, str]]
    state: Optional[Dict[str, str]]
    country: Optional[Dict[str, str]]
    address: Optional[Dict[str, str]]
    location: Optional[Dict[str, float]]
    markets: Optional[List[Dict[str, Any]]]
    dmas: Optional[List[Dict[str, Any]]]


class TicketmasterEventData(BaseModel):
    """Raw Ticketmaster event data structure."""
    id: str
    name: str
    type: str
    url: Optional[str]
    locale: Optional[str]
    dates: Optional[Dict[str, Any]]
    sales: Optional[Dict[str, Any]]
    info: Optional[str]
    pleaseNote: Optional[str]
    priceRanges: Optional[List[Dict[str, Any]]]
    seatmap: Optional[Dict[str, Any]]
    accessibility: Optional[Dict[str, Any]]
    ticketLimit: Optional[Dict[str, Any]]
    ageRestrictions: Optional[Dict[str, Any]]
    classifications: Optional[List[Dict[str, Any]]]


class TicketmasterClient(APIClient):
    """Ticketmaster Discovery API client for venue and event data."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.ticketmaster.com/discovery/v2",
        requests_per_minute: int = 5000,  # Ticketmaster allows 5000 requests per day
        retry_attempts: int = 3,
        retry_backoff: float = 1.0
    ):
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            requests_per_minute=requests_per_minute,
            retry_attempts=retry_attempts,
            retry_backoff=retry_backoff
        )
        
        self.logger = structlog.get_logger("TicketmasterClient")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Ticketmaster API."""
        return {}  # Ticketmaster uses API key in query parameters
    
    def _add_api_key_to_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add API key to request parameters."""
        if params is None:
            params = {}
        params["apikey"] = self.api_key
        return params
    
    async def search_events(
        self,
        keyword: Optional[str] = None,
        attraction_id: Optional[str] = None,
        venue_id: Optional[str] = None,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        country_code: Optional[str] = None,
        classification_name: Optional[str] = None,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        size: int = 20,
        page: int = 0,
        sort: str = "date,asc"
    ) -> APIResponse:
        """
        Search for events on Ticketmaster.
        
        Args:
            keyword: Search keyword
            attraction_id: Attraction/artist ID
            venue_id: Venue ID
            city: City name
            state_code: State code (US only)
            country_code: Country code (ISO 3166-1 alpha-2)
            classification_name: Event classification (e.g., "Music")
            start_date_time: Start date/time (ISO 8601)
            end_date_time: End date/time (ISO 8601)
            size: Number of results per page (max 200)
            page: Page number
            sort: Sort order
            
        Returns:
            APIResponse containing event search results
        """
        params = {
            "size": min(size, 200),
            "page": page,
            "sort": sort
        }
        
        # Add optional parameters
        if keyword:
            params["keyword"] = keyword
        if attraction_id:
            params["attractionId"] = attraction_id
        if venue_id:
            params["venueId"] = venue_id
        if city:
            params["city"] = city
        if state_code:
            params["stateCode"] = state_code
        if country_code:
            params["countryCode"] = country_code
        if classification_name:
            params["classificationName"] = classification_name
        if start_date_time:
            params["startDateTime"] = start_date_time
        if end_date_time:
            params["endDateTime"] = end_date_time
        
        params = self._add_api_key_to_params(params)
        response = await self.get("events.json", params=params)
        
        if response.success and response.data:
            # Transform events data
            events_data = response.data.get("_embedded", {}).get("events", [])
            normalized_events = []
            
            for event_data in events_data:
                try:
                    normalized_event = self._transform_event_data(event_data)
                    if normalized_event:
                        normalized_events.append(normalized_event)
                except Exception as e:
                    self.logger.warning(
                        "Failed to transform event data",
                        event_id=event_data.get("id"),
                        error=str(e)
                    )
            
            response.data["normalized_events"] = normalized_events
        
        return response
    
    async def get_event(self, event_id: str) -> APIResponse:
        """
        Get detailed information about a specific event.
        
        Args:
            event_id: Ticketmaster event ID
            
        Returns:
            APIResponse containing event details
        """
        params = self._add_api_key_to_params()
        response = await self.get(f"events/{event_id}.json", params=params)
        
        if response.success and response.data:
            try:
                normalized_event = self._transform_event_data(response.data)
                if normalized_event:
                    response.data["normalized_event"] = normalized_event
            except Exception as e:
                self.logger.warning(
                    "Failed to transform event data",
                    event_id=event_id,
                    error=str(e)
                )
        
        return response
    
    async def search_venues(
        self,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        country_code: Optional[str] = None,
        size: int = 20,
        page: int = 0,
        sort: str = "name,asc"
    ) -> APIResponse:
        """
        Search for venues on Ticketmaster.
        
        Args:
            keyword: Search keyword
            city: City name
            state_code: State code (US only)
            country_code: Country code (ISO 3166-1 alpha-2)
            size: Number of results per page (max 200)
            page: Page number
            sort: Sort order
            
        Returns:
            APIResponse containing venue search results
        """
        params = {
            "size": min(size, 200),
            "page": page,
            "sort": sort
        }
        
        # Add optional parameters
        if keyword:
            params["keyword"] = keyword
        if city:
            params["city"] = city
        if state_code:
            params["stateCode"] = state_code
        if country_code:
            params["countryCode"] = country_code
        
        params = self._add_api_key_to_params(params)
        response = await self.get("venues.json", params=params)
        
        if response.success and response.data:
            # Transform venues data
            venues_data = response.data.get("_embedded", {}).get("venues", [])
            normalized_venues = []
            
            for venue_data in venues_data:
                try:
                    normalized_venue = self._transform_venue_data(venue_data)
                    if normalized_venue:
                        normalized_venues.append(normalized_venue)
                except Exception as e:
                    self.logger.warning(
                        "Failed to transform venue data",
                        venue_id=venue_data.get("id"),
                        error=str(e)
                    )
            
            response.data["normalized_venues"] = normalized_venues
        
        return response
    
    async def get_venue(self, venue_id: str) -> APIResponse:
        """
        Get detailed information about a specific venue.
        
        Args:
            venue_id: Ticketmaster venue ID
            
        Returns:
            APIResponse containing venue details
        """
        params = self._add_api_key_to_params()
        response = await self.get(f"venues/{venue_id}.json", params=params)
        
        if response.success and response.data:
            try:
                normalized_venue = self._transform_venue_data(response.data)
                if normalized_venue:
                    response.data["normalized_venue"] = normalized_venue
            except Exception as e:
                self.logger.warning(
                    "Failed to transform venue data",
                    venue_id=venue_id,
                    error=str(e)
                )
        
        return response
    
    def _transform_venue_data(self, ticketmaster_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transform Ticketmaster venue data to our normalized format.
    
        Args:
            ticketmaster_data: Raw Ticketmaster venue data
        
        Returns:
            Normalized venue data dictionary or None if transformation fails
        """
        try:
            # Generate our internal venue ID
            venue_id = f"ticketmaster_{ticketmaster_data['id']}"
        
            # Extract basic information
            name = ticketmaster_data.get("name", "").strip()
            if not name:
                return None
        
            # Extract location information
            address_data = ticketmaster_data.get("address", {})
            city_data = ticketmaster_data.get("city", {})
            state_data = ticketmaster_data.get("state", {})
            country_data = ticketmaster_data.get("country", {})
            location_data = ticketmaster_data.get("location", {})
        
            # Extract location fields as top-level attributes
            city = city_data.get("name", "") if city_data else ""
            state = state_data.get("stateCode", "") if state_data else None
            country = country_data.get("countryCode", "") if country_data else ""
            address = address_data.get("line1", "") if address_data else None
            postal_code = ticketmaster_data.get("postalCode")
            
            # Skip venues without required fields
            if not city or not country:
                self.logger.warning(
                    "Venue missing required location fields",
                    venue_id=venue_id,
                    name=name,
                    has_city=bool(city),
                    has_country=bool(country)
                )
                return None
        
            # Determine venue type
            venue_type = "arena"  # Default
            tm_type = ticketmaster_data.get("type", "").lower()
            if "theater" in tm_type or "theatre" in tm_type:
                venue_type = "theater"
            elif "club" in tm_type:
                venue_type = "club"
            elif "outdoor" in tm_type or "amphitheater" in tm_type:
                venue_type = "amphitheater"
            elif "stadium" in tm_type:
                venue_type = "stadium"
            elif "hall" in tm_type:
                venue_type = "hall"
            else:
                venue_type = "other"
        
            # Extract capacity (not always available)
            capacity = 10000  # Default capacity if not specified
        
            # Create normalized venue data matching the Venue model structure
            normalized_data = {
                "venue_id": venue_id,
                "name": name,
                "city": city,
                "state": state,
                "country": country,
                "capacity": capacity,
                "venue_type": venue_type,
                "address": address,
                "postal_code": postal_code,
            }
        
            # Validate the data using our Venue model
            try:
                Venue(**normalized_data)
            except Exception as validation_error:
                self.logger.warning(
                    "Venue data validation failed",
                    venue_id=venue_id,
                    validation_error=str(validation_error)
                )
                return None
        
            return normalized_data
        
        except Exception as e:
            self.logger.error(
                "Failed to transform Ticketmaster venue data",
                ticketmaster_data=ticketmaster_data,
                error=str(e)
            )
            return None
    
    def _transform_event_data(self, ticketmaster_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transform Ticketmaster event data to our normalized format.
        
        Args:
            ticketmaster_data: Raw Ticketmaster event data
            
        Returns:
            Normalized concert data dictionary or None if transformation fails
        """
        try:
            # Generate our internal concert ID
            concert_id = f"ticketmaster_{ticketmaster_data['id']}"
            
            # Extract basic information
            name = ticketmaster_data.get("name", "").strip()
            if not name:
                return None
            
            # Extract date information
            dates_data = ticketmaster_data.get("dates", {})
            start_data = dates_data.get("start", {})
            
            event_date = None
            if start_data.get("dateTime"):
                try:
                    event_date = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
                except Exception:
                    if start_data.get("localDate"):
                        try:
                            event_date = datetime.fromisoformat(start_data["localDate"] + "T20:00:00")
                        except Exception:
                            pass
            
            if not event_date:
                return None
            
            # Extract venue information
            venues = ticketmaster_data.get("_embedded", {}).get("venues", [])
            venue_id = None
            if venues:
                venue_id = f"ticketmaster_{venues[0]['id']}"
            
            # Extract artist information
            attractions = ticketmaster_data.get("_embedded", {}).get("attractions", [])
            artist_id = None
            if attractions:
                artist_id = f"ticketmaster_{attractions[0]['id']}"
            
            # Extract price information
            price_ranges = ticketmaster_data.get("priceRanges", [])
            ticket_prices = {}
            
            for price_range in price_ranges:
                price_type = price_range.get("type", "general").lower()
                min_price = price_range.get("min", 0)
                max_price = price_range.get("max", min_price)
                avg_price = (min_price + max_price) / 2
                ticket_prices[price_type] = avg_price
            
            # Determine status
            status = "scheduled"
            sales_data = ticketmaster_data.get("sales", {})
            if sales_data.get("public", {}).get("endDateTime"):
                # Check if sales have ended
                try:
                    end_time = datetime.fromisoformat(sales_data["public"]["endDateTime"].replace("Z", "+00:00"))
                    if datetime.utcnow() > end_time:
                        status = "completed"
                except Exception:
                    pass
            
            # Create normalized concert data
            normalized_data = {
                "concert_id": concert_id,
                "artist_id": artist_id,
                "venue_id": venue_id,
                "event_date": event_date.isoformat(),
                "ticket_prices": ticket_prices,
                "total_attendance": None,  # Not available from Ticketmaster API
                "revenue": None,  # Not available from Ticketmaster API
                "status": status,
                "source": "ticketmaster",
                "raw_data": {
                    "name": name,
                    "url": ticketmaster_data.get("url"),
                    "info": ticketmaster_data.get("info"),
                    "pleaseNote": ticketmaster_data.get("pleaseNote"),
                    "classifications": ticketmaster_data.get("classifications", []),
                    "seatmap": ticketmaster_data.get("seatmap"),
                    "accessibility": ticketmaster_data.get("accessibility")
                }
            }
            
            # Validate the data using our Concert model (skip if missing required fields)
            if artist_id and venue_id:
                try:
                    Concert(**normalized_data)
                except Exception as validation_error:
                    self.logger.warning(
                        "Concert data validation failed",
                        concert_id=concert_id,
                        validation_error=str(validation_error)
                    )

            return normalized_data
            
        except Exception as e:
            self.logger.error(
                "Failed to transform Ticketmaster event data",
                ticketmaster_data=ticketmaster_data,
                error=str(e)
            )
            return None