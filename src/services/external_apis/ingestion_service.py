"""
Data ingestion service that orchestrates external API clients.
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import structlog

from .spotify_client import SpotifyClient
from .ticketmaster_client import TicketmasterClient
from .base_client import APIResponse
from ...config.environment import load_env_file
from ..file_processor import FileUploadProcessor

# Load environment variables
load_env_file()

# Import and reload settings
from ...config import settings as settings_module_import
# Get the actual module
import sys
settings_module = sys.modules['src.config.settings']
settings_module.reload_settings()

# Now get the settings object
settings = settings_module.settings

logger = structlog.get_logger(__name__)


class IngestionResult:
    """Result of a data ingestion operation."""
    
    def __init__(
        self,
        success: bool,
        source: str,
        data_type: str,
        records_processed: int = 0,
        records_successful: int = 0,
        records_failed: int = 0,
        errors: Optional[List[str]] = None,
        data: Optional[List[Dict[str, Any]]] = None
    ):
        self.success = success
        self.source = source
        self.data_type = data_type
        self.records_processed = records_processed
        self.records_successful = records_successful
        self.records_failed = records_failed
        self.errors = errors or []
        self.data = data or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "source": self.source,
            "data_type": self.data_type,
            "records_processed": self.records_processed,
            "records_successful": self.records_successful,
            "records_failed": self.records_failed,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
            "data_count": len(self.data)
        }


class DataIngestionService:
    """
    Service for ingesting data from external APIs with unified interface.
    """
    
    def __init__(self):
        self.spotify_client: Optional[SpotifyClient] = None
        self.ticketmaster_client: Optional[TicketmasterClient] = None
        self.file_processor = FileUploadProcessor()
        self.logger = structlog.get_logger("DataIngestionService")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_clients()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_clients()
    
    async def initialize_clients(self) -> None:
        """Initialize API clients with configuration."""
        try:
            # Initialize Spotify client if credentials are available
            if settings.external_apis.spotify_client_id and settings.external_apis.spotify_client_secret:
                self.spotify_client = SpotifyClient(
                    client_id=settings.external_apis.spotify_client_id,
                    client_secret=settings.external_apis.spotify_client_secret,
                    base_url=settings.external_apis.spotify_base_url,
                    requests_per_minute=settings.external_apis.api_rate_limit_requests,
                    retry_attempts=settings.external_apis.api_retry_attempts,
                    retry_backoff=settings.external_apis.api_retry_backoff
                )
                self.logger.info("Spotify client initialized")
            else:
                self.logger.warning("Spotify credentials not configured")
            
            # Initialize Ticketmaster client if API key is available
            if settings.external_apis.ticketmaster_api_key:
                self.ticketmaster_client = TicketmasterClient(
                    api_key=settings.external_apis.ticketmaster_api_key,
                    base_url=settings.external_apis.ticketmaster_base_url,
                    requests_per_minute=settings.external_apis.api_rate_limit_requests,
                    retry_attempts=settings.external_apis.api_retry_attempts,
                    retry_backoff=settings.external_apis.api_retry_backoff
                )
                self.logger.info("Ticketmaster client initialized")
            else:
                self.logger.warning("Ticketmaster API key not configured")
                
        except Exception as e:
            self.logger.error("Failed to initialize API clients", error=str(e))
            raise
    
    async def close_clients(self) -> None:
        """Close all API clients."""
        if self.spotify_client:
            await self.spotify_client.close()
        if self.ticketmaster_client:
            await self.ticketmaster_client.close()
    
    async def ingest_artist_data(
        self,
        search_queries: List[str],
        max_results_per_query: int = 50
    ) -> IngestionResult:
        """
        Ingest artist data from Spotify.
        
        Args:
            search_queries: List of search terms for artists
            max_results_per_query: Maximum results per search query
            
        Returns:
            IngestionResult with artist data
        """
        if not self.spotify_client:
            return IngestionResult(
                success=False,
                source="spotify",
                data_type="artists",
                errors=["Spotify client not initialized"]
            )
        
        all_artists = []
        all_errors = []
        total_processed = 0
        successful_count = 0
        
        try:
            for query in search_queries:
                self.logger.info("Searching for artists", query=query)
                
                # Search for artists with pagination
                offset = 0
                while offset < max_results_per_query:
                    limit = min(50, max_results_per_query - offset)
                    
                    response = await self.spotify_client.search_artists(
                        query=query,
                        limit=limit,
                        offset=offset
                    )
                    
                    if not response.success:
                        error_msg = f"Failed to search artists for query '{query}': {response.error}"
                        all_errors.append(error_msg)
                        self.logger.error(error_msg)
                        break
                    
                    # Extract normalized artists
                    normalized_artists = response.data.get("normalized_artists", [])
                    total_processed += len(normalized_artists)
                    
                    for artist in normalized_artists:
                        try:
                            # Additional validation or processing can be added here
                            all_artists.append(artist)
                            successful_count += 1
                        except Exception as e:
                            all_errors.append(f"Failed to process artist {artist.get('name', 'unknown')}: {str(e)}")
                    
                    # Check if we have more results
                    total_results = response.data.get("artists", {}).get("total", 0)
                    if offset + limit >= total_results:
                        break
                    
                    offset += limit
                    
                    # Small delay to be respectful to the API
                    await asyncio.sleep(0.1)
            
            return IngestionResult(
                success=len(all_errors) == 0,
                source="spotify",
                data_type="artists",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors,
                data=all_artists
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during artist ingestion: {str(e)}"
            self.logger.error(error_msg)
            return IngestionResult(
                success=False,
                source="spotify",
                data_type="artists",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors + [error_msg],
                data=all_artists
            )
    
    async def ingest_venue_data(
        self,
        cities: List[str],
        max_results_per_city: int = 100
    ) -> IngestionResult:
        """
        Ingest venue data from Ticketmaster.
        
        Args:
            cities: List of city names to search for venues
            max_results_per_city: Maximum results per city
            
        Returns:
            IngestionResult with venue data
        """
        if not self.ticketmaster_client:
            return IngestionResult(
                success=False,
                source="ticketmaster",
                data_type="venues",
                errors=["Ticketmaster client not initialized"]
            )
        
        all_venues = []
        all_errors = []
        total_processed = 0
        successful_count = 0
        
        try:
            for city in cities:
                self.logger.info("Searching for venues", city=city)
                
                # Search for venues with pagination
                page = 0
                while page * 200 < max_results_per_city:
                    size = min(200, max_results_per_city - (page * 200))
                    
                    response = await self.ticketmaster_client.search_venues(
                        city=city,
                        size=size,
                        page=page
                    )
                    
                    if not response.success:
                        error_msg = f"Failed to search venues for city '{city}': {response.error}"
                        all_errors.append(error_msg)
                        self.logger.error(error_msg)
                        break
                    
                    # Extract normalized venues
                    normalized_venues = response.data.get("normalized_venues", [])
                    total_processed += len(normalized_venues)
                    
                    for venue in normalized_venues:
                        try:
                            # Additional validation or processing can be added here
                            all_venues.append(venue)
                            successful_count += 1
                        except Exception as e:
                            all_errors.append(f"Failed to process venue {venue.get('name', 'unknown')}: {str(e)}")
                    
                    # Check if we have more results
                    page_info = response.data.get("page", {})
                    total_pages = page_info.get("totalPages", 1)
                    if page >= total_pages - 1:
                        break
                    
                    page += 1
                    
                    # Small delay to be respectful to the API
                    await asyncio.sleep(0.2)
            
            return IngestionResult(
                success=len(all_errors) == 0,
                source="ticketmaster",
                data_type="venues",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors,
                data=all_venues
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during venue ingestion: {str(e)}"
            self.logger.error(error_msg)
            return IngestionResult(
                success=False,
                source="ticketmaster",
                data_type="venues",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors + [error_msg],
                data=all_venues
            )
    
    async def ingest_event_data(
        self,
        cities: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        classification_name: str = "Music",
        max_results: int = 200
    ) -> IngestionResult:
        """
        Ingest event/concert data from Ticketmaster.
        
        Args:
            cities: List of city names to search for events
            keywords: List of keywords to search for
            classification_name: Event classification (default: "Music")
            max_results: Maximum total results
            
        Returns:
            IngestionResult with event data
        """
        if not self.ticketmaster_client:
            return IngestionResult(
                success=False,
                source="ticketmaster",
                data_type="events",
                errors=["Ticketmaster client not initialized"]
            )
        
        all_events = []
        all_errors = []
        total_processed = 0
        successful_count = 0
        
        try:
            # Prepare search parameters
            search_params = []
            
            if cities and keywords:
                # Combine cities and keywords
                for city in cities:
                    for keyword in keywords:
                        search_params.append({"city": city, "keyword": keyword})
            elif cities:
                # Search by cities only
                for city in cities:
                    search_params.append({"city": city})
            elif keywords:
                # Search by keywords only
                for keyword in keywords:
                    search_params.append({"keyword": keyword})
            else:
                # General music events search
                search_params.append({})
            
            results_per_search = max_results // len(search_params) if search_params else max_results
            
            for params in search_params:
                self.logger.info("Searching for events", params=params)
                
                # Search for events with pagination
                page = 0
                while page * 200 < results_per_search:
                    size = min(200, results_per_search - (page * 200))
                    
                    search_kwargs = {
                        "classification_name": classification_name,
                        "size": size,
                        "page": page,
                        **params
                    }
                    
                    response = await self.ticketmaster_client.search_events(**search_kwargs)
                    
                    if not response.success:
                        error_msg = f"Failed to search events with params {params}: {response.error}"
                        all_errors.append(error_msg)
                        self.logger.error(error_msg)
                        break
                    
                    # Extract normalized events
                    normalized_events = response.data.get("normalized_events", [])
                    total_processed += len(normalized_events)
                    
                    for event in normalized_events:
                        try:
                            # Additional validation or processing can be added here
                            all_events.append(event)
                            successful_count += 1
                        except Exception as e:
                            all_errors.append(f"Failed to process event {event.get('concert_id', 'unknown')}: {str(e)}")
                    
                    # Check if we have more results
                    page_info = response.data.get("page", {})
                    total_pages = page_info.get("totalPages", 1)
                    if page >= total_pages - 1:
                        break
                    
                    page += 1
                    
                    # Small delay to be respectful to the API
                    await asyncio.sleep(0.2)
            
            return IngestionResult(
                success=len(all_errors) == 0,
                source="ticketmaster",
                data_type="events",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors,
                data=all_events
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during event ingestion: {str(e)}"
            self.logger.error(error_msg)
            return IngestionResult(
                success=False,
                source="ticketmaster",
                data_type="events",
                records_processed=total_processed,
                records_successful=successful_count,
                records_failed=total_processed - successful_count,
                errors=all_errors + [error_msg],
                data=all_events
            )
    
    async def ingest_comprehensive_data(
        self,
        artist_queries: List[str] = None,
        venue_cities: List[str] = None,
        event_cities: List[str] = None,
        event_keywords: List[str] = None
    ) -> Dict[str, IngestionResult]:
        """
        Perform comprehensive data ingestion from all sources.
        
        Args:
            artist_queries: Search queries for artists
            venue_cities: Cities to search for venues
            event_cities: Cities to search for events
            event_keywords: Keywords to search for events
            
        Returns:
            Dictionary of ingestion results by data type
        """
        results = {}
        
        # Default values
        if artist_queries is None:
            artist_queries = ["rock", "pop", "jazz", "blues", "country", "electronic"]
        if venue_cities is None:
            venue_cities = ["New York", "Los Angeles", "Chicago", "Nashville", "Austin"]
        if event_cities is None:
            event_cities = venue_cities
        if event_keywords is None:
            event_keywords = ["concert", "music", "live"]
        
        try:
            # Run all ingestion tasks concurrently
            tasks = []
            
            if self.spotify_client:
                tasks.append(("artists", self.ingest_artist_data(artist_queries)))
            
            if self.ticketmaster_client:
                tasks.append(("venues", self.ingest_venue_data(venue_cities)))
                tasks.append(("events", self.ingest_event_data(event_cities, event_keywords)))
            
            # Execute all tasks
            if tasks:
                task_results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
                
                for i, (data_type, result) in enumerate(zip([task[0] for task in tasks], task_results)):
                    if isinstance(result, Exception):
                        results[data_type] = IngestionResult(
                            success=False,
                            source="unknown",
                            data_type=data_type,
                            errors=[f"Task failed with exception: {str(result)}"]
                        )
                    else:
                        results[data_type] = result
            
            # Log summary
            total_records = sum(result.records_successful for result in results.values())
            total_errors = sum(len(result.errors) for result in results.values())
            
            self.logger.info(
                "Comprehensive data ingestion completed",
                total_records=total_records,
                total_errors=total_errors,
                sources=list(results.keys())
            )
            
        except Exception as e:
            self.logger.error("Comprehensive data ingestion failed", error=str(e))
            results["error"] = IngestionResult(
                success=False,
                source="ingestion_service",
                data_type="comprehensive",
                errors=[f"Comprehensive ingestion failed: {str(e)}"]
            )
        
        return results
    
    def process_file_upload(
        self,
        file_path: Union[str, Path],
        data_type: str,
        validate_data: bool = True
    ) -> IngestionResult:
        """
        Process uploaded file with parsing and validation.
        
        Args:
            file_path: Path to the uploaded file
            data_type: Type of data in the file (artists, venues, concerts, ticket_sales)
            validate_data: Whether to perform data quality validation
            
        Returns:
            IngestionResult with processing results
        """
        return self.file_processor.process_file_upload(file_path, data_type, validate_data)
    
    def process_batch_files(
        self,
        file_paths: List[Union[str, Path]],
        data_types: Union[str, List[str]],
        validate_data: bool = True
    ) -> Dict[str, IngestionResult]:
        """
        Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            data_types: Single data type or list of data types (one per file)
            validate_data: Whether to perform data quality validation
            
        Returns:
            Dictionary mapping file paths to ingestion results
        """
        return self.file_processor.process_batch_files(file_paths, data_types, validate_data)