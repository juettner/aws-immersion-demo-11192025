"""
Stream producer service for sending data to Kinesis streams.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import structlog

from ..infrastructure.kinesis_client import KinesisClient, KinesisStreamError
from .external_apis.ingestion_service import DataIngestionService, IngestionResult
from .file_processor import FileUploadProcessor
from ..config.settings import settings

logger = structlog.get_logger(__name__)


class StreamProducerResult:
    """Result of a stream producer operation."""
    
    def __init__(
        self,
        success: bool,
        source: str,
        data_type: str,
        records_sent: int = 0,
        records_failed: int = 0,
        stream_responses: Optional[List[Dict[str, Any]]] = None,
        errors: Optional[List[str]] = None
    ):
        self.success = success
        self.source = source
        self.data_type = data_type
        self.records_sent = records_sent
        self.records_failed = records_failed
        self.stream_responses = stream_responses or []
        self.errors = errors or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "source": self.source,
            "data_type": self.data_type,
            "records_sent": self.records_sent,
            "records_failed": self.records_failed,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
            "stream_response_count": len(self.stream_responses)
        }


class StreamProducerService:
    """
    Service for producing data to Kinesis streams from various sources.
    """
    
    def __init__(self, stream_name: Optional[str] = None):
        self.kinesis_client = KinesisClient(stream_name)
        self.ingestion_service = DataIngestionService()
        self.file_processor = FileUploadProcessor()
        self.logger = structlog.get_logger("StreamProducerService")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.ingestion_service.initialize_clients()
        await self.kinesis_client.create_stream_if_not_exists()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.ingestion_service.close_clients()
    
    def _prepare_stream_record(self, data: Dict[str, Any], data_type: str, source: str) -> Dict[str, Any]:
        """
        Prepare data record for streaming with metadata.
        
        Args:
            data: Raw data record
            data_type: Type of data (artists, venues, concerts, ticket_sales)
            source: Data source (spotify, ticketmaster, file_upload, etc.)
            
        Returns:
            Enhanced record with metadata for streaming
        """
        return {
            "record_id": f"{source}_{data_type}_{datetime.utcnow().timestamp()}",
            "source": source,
            "data_type": data_type,
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "payload": data
        }
    
    def _get_partition_key(self, data: Dict[str, Any], data_type: str) -> str:
        """
        Generate partition key based on data type and content.
        
        Args:
            data: Data record
            data_type: Type of data
            
        Returns:
            Partition key for Kinesis
        """
        if data_type == "artists":
            return f"artist_{data.get('artist_id', 'unknown')}"
        elif data_type == "venues":
            return f"venue_{data.get('venue_id', 'unknown')}"
        elif data_type == "concerts" or data_type == "events":
            return f"concert_{data.get('concert_id', data.get('event_id', 'unknown'))}"
        elif data_type == "ticket_sales":
            return f"ticket_{data.get('concert_id', 'unknown')}"
        else:
            return f"{data_type}_unknown"
    
    async def stream_api_data(
        self,
        artist_queries: Optional[List[str]] = None,
        venue_cities: Optional[List[str]] = None,
        event_cities: Optional[List[str]] = None,
        event_keywords: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> Dict[str, StreamProducerResult]:
        """
        Ingest data from external APIs and stream to Kinesis.
        
        Args:
            artist_queries: Search queries for artists
            venue_cities: Cities to search for venues
            event_cities: Cities to search for events
            event_keywords: Keywords to search for events
            batch_size: Number of records to send in each batch
            
        Returns:
            Dictionary of streaming results by data type
        """
        results = {}
        
        try:
            # Perform comprehensive data ingestion
            ingestion_results = await self.ingestion_service.ingest_comprehensive_data(
                artist_queries=artist_queries,
                venue_cities=venue_cities,
                event_cities=event_cities,
                event_keywords=event_keywords
            )
            
            # Stream each data type
            for data_type, ingestion_result in ingestion_results.items():
                if not ingestion_result.success or not ingestion_result.data:
                    results[data_type] = StreamProducerResult(
                        success=False,
                        source=ingestion_result.source,
                        data_type=data_type,
                        errors=[f"Ingestion failed: {', '.join(ingestion_result.errors)}"]
                    )
                    continue
                
                # Prepare records for streaming
                stream_records = []
                for record in ingestion_result.data:
                    stream_record = self._prepare_stream_record(
                        record, data_type, ingestion_result.source
                    )
                    stream_records.append(stream_record)
                
                # Stream records in batches
                stream_result = await self._stream_records_batch(
                    stream_records, data_type, ingestion_result.source, batch_size
                )
                results[data_type] = stream_result
            
            # Log summary
            total_sent = sum(result.records_sent for result in results.values())
            total_failed = sum(result.records_failed for result in results.values())
            
            self.logger.info(
                "API data streaming completed",
                total_records_sent=total_sent,
                total_records_failed=total_failed,
                data_types=list(results.keys())
            )
            
        except Exception as e:
            error_msg = f"API data streaming failed: {str(e)}"
            self.logger.error(error_msg)
            results["error"] = StreamProducerResult(
                success=False,
                source="stream_producer",
                data_type="api_data",
                errors=[error_msg]
            )
        
        return results
    
    def stream_file_data(
        self,
        file_path: Union[str, Path],
        data_type: str,
        batch_size: int = 100,
        validate_data: bool = True
    ) -> StreamProducerResult:
        """
        Process uploaded file and stream data to Kinesis.
        
        Args:
            file_path: Path to the uploaded file
            data_type: Type of data in the file
            batch_size: Number of records to send in each batch
            validate_data: Whether to perform data quality validation
            
        Returns:
            StreamProducerResult with streaming results
        """
        try:
            # Process file upload
            ingestion_result = self.file_processor.process_file_upload(
                file_path, data_type, validate_data
            )
            
            if not ingestion_result.success or not ingestion_result.data:
                return StreamProducerResult(
                    success=False,
                    source="file_upload",
                    data_type=data_type,
                    errors=[f"File processing failed: {', '.join(ingestion_result.errors)}"]
                )
            
            # Prepare records for streaming
            stream_records = []
            for record in ingestion_result.data:
                stream_record = self._prepare_stream_record(
                    record, data_type, "file_upload"
                )
                stream_records.append(stream_record)
            
            # Stream records in batches
            return asyncio.run(self._stream_records_batch(
                stream_records, data_type, "file_upload", batch_size
            ))
            
        except Exception as e:
            error_msg = f"File data streaming failed: {str(e)}"
            self.logger.error(error_msg, file_path=str(file_path))
            return StreamProducerResult(
                success=False,
                source="file_upload",
                data_type=data_type,
                errors=[error_msg]
            )
    
    def stream_batch_files(
        self,
        file_paths: List[Union[str, Path]],
        data_types: Union[str, List[str]],
        batch_size: int = 100,
        validate_data: bool = True
    ) -> Dict[str, StreamProducerResult]:
        """
        Process multiple files and stream data to Kinesis.
        
        Args:
            file_paths: List of file paths to process
            data_types: Single data type or list of data types (one per file)
            batch_size: Number of records to send in each batch
            validate_data: Whether to perform data quality validation
            
        Returns:
            Dictionary mapping file paths to streaming results
        """
        results = {}
        
        try:
            # Process batch files
            ingestion_results = self.file_processor.process_batch_files(
                file_paths, data_types, validate_data
            )
            
            # Stream each file's data
            for file_path, ingestion_result in ingestion_results.items():
                if not ingestion_result.success or not ingestion_result.data:
                    results[file_path] = StreamProducerResult(
                        success=False,
                        source="file_upload",
                        data_type=ingestion_result.data_type,
                        errors=[f"File processing failed: {', '.join(ingestion_result.errors)}"]
                    )
                    continue
                
                # Prepare records for streaming
                stream_records = []
                for record in ingestion_result.data:
                    stream_record = self._prepare_stream_record(
                        record, ingestion_result.data_type, "file_upload"
                    )
                    stream_records.append(stream_record)
                
                # Stream records in batches
                stream_result = asyncio.run(self._stream_records_batch(
                    stream_records, ingestion_result.data_type, "file_upload", batch_size
                ))
                results[file_path] = stream_result
            
            # Log summary
            total_sent = sum(result.records_sent for result in results.values())
            total_failed = sum(result.records_failed for result in results.values())
            
            self.logger.info(
                "Batch file streaming completed",
                total_records_sent=total_sent,
                total_records_failed=total_failed,
                file_count=len(file_paths)
            )
            
        except Exception as e:
            error_msg = f"Batch file streaming failed: {str(e)}"
            self.logger.error(error_msg)
            results["error"] = StreamProducerResult(
                success=False,
                source="file_upload",
                data_type="batch_files",
                errors=[error_msg]
            )
        
        return results
    
    async def _stream_records_batch(
        self,
        records: List[Dict[str, Any]],
        data_type: str,
        source: str,
        batch_size: int
    ) -> StreamProducerResult:
        """
        Stream records to Kinesis in batches.
        
        Args:
            records: List of records to stream
            data_type: Type of data
            source: Data source
            batch_size: Number of records per batch
            
        Returns:
            StreamProducerResult with streaming results
        """
        if not records:
            return StreamProducerResult(
                success=True,
                source=source,
                data_type=data_type,
                records_sent=0,
                records_failed=0
            )
        
        all_responses = []
        total_sent = 0
        total_failed = 0
        all_errors = []
        
        try:
            # Process records in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Determine partition key field based on data type
                partition_key_field = None
                if data_type == "artists":
                    partition_key_field = "artist_id"
                elif data_type == "venues":
                    partition_key_field = "venue_id"
                elif data_type in ["concerts", "events"]:
                    partition_key_field = "concert_id"
                
                # Send batch to Kinesis
                batch_response = self.kinesis_client.put_records(
                    records=batch,
                    partition_key_field=partition_key_field
                )
                
                all_responses.append(batch_response)
                total_sent += batch_response['records_successful']
                total_failed += batch_response['records_failed']
                
                if not batch_response['success']:
                    all_errors.append(f"Batch {i//batch_size + 1} failed: {batch_response.get('error', 'Unknown error')}")
                
                # Add failed record details
                for failed_record in batch_response.get('failed_records', []):
                    all_errors.append(
                        f"Record {failed_record['index']} failed: {failed_record.get('error_message', 'Unknown error')}"
                    )
                
                # Small delay between batches to avoid overwhelming Kinesis
                if i + batch_size < len(records):
                    await asyncio.sleep(0.1)
            
            success = total_failed == 0
            
            self.logger.info(
                "Records streamed to Kinesis",
                data_type=data_type,
                source=source,
                total_records=len(records),
                records_sent=total_sent,
                records_failed=total_failed,
                batch_count=len(all_responses)
            )
            
            return StreamProducerResult(
                success=success,
                source=source,
                data_type=data_type,
                records_sent=total_sent,
                records_failed=total_failed,
                stream_responses=all_responses,
                errors=all_errors
            )
            
        except Exception as e:
            error_msg = f"Batch streaming failed: {str(e)}"
            self.logger.error(error_msg, data_type=data_type, source=source)
            return StreamProducerResult(
                success=False,
                source=source,
                data_type=data_type,
                records_sent=total_sent,
                records_failed=len(records) - total_sent,
                stream_responses=all_responses,
                errors=all_errors + [error_msg]
            )
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Get information about the Kinesis stream.
        
        Returns:
            Stream description and metadata
        """
        return self.kinesis_client.get_stream_description()
    
    def list_all_streams(self) -> Dict[str, Any]:
        """
        List all available Kinesis streams.
        
        Returns:
            List of stream names and metadata
        """
        return self.kinesis_client.list_streams()