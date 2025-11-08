"""
AWS Lambda functions for processing Kinesis stream data.
"""
import json
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

# Configure structured logging for Lambda
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class StreamProcessor:
    """Base class for processing Kinesis stream records."""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    def decode_kinesis_record(self, kinesis_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Decode and parse a Kinesis record.
        
        Args:
            kinesis_record: Raw Kinesis record from event
            
        Returns:
            Parsed record data or None if parsing fails
        """
        try:
            # Decode base64 data
            encoded_data = kinesis_record['data']
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            
            # Parse JSON
            record_data = json.loads(decoded_data)
            
            # Add Kinesis metadata
            record_data['kinesis_metadata'] = {
                'sequence_number': kinesis_record['sequenceNumber'],
                'partition_key': kinesis_record['partitionKey'],
                'approximate_arrival_timestamp': kinesis_record['approximateArrivalTimestamp'],
                'kinesis_schema_version': kinesis_record['kinesisSchemaVersion']
            }
            
            return record_data
            
        except Exception as e:
            self.logger.error(
                "Failed to decode Kinesis record",
                error=str(e),
                sequence_number=kinesis_record.get('sequenceNumber', 'unknown')
            )
            return None
    
    def validate_record_structure(self, record: Dict[str, Any]) -> bool:
        """
        Validate that the record has the expected structure.
        
        Args:
            record: Parsed record data
            
        Returns:
            True if record is valid, False otherwise
        """
        required_fields = ['source', 'data_type', 'ingestion_timestamp', 'payload']
        
        for field in required_fields:
            if field not in record:
                self.logger.warning(f"Missing required field: {field}", record_id=record.get('record_id', 'unknown'))
                return False
        
        return True
    
    def write_to_s3(
        self,
        bucket: str,
        key: str,
        data: Any,
        content_type: str = 'application/json'
    ) -> bool:
        """
        Write data to S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            data: Data to write
            content_type: Content type for the object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(data, (dict, list)):
                body = json.dumps(data, default=str)
            else:
                body = str(data)
            
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=content_type
            )
            
            self.logger.info(f"Successfully wrote data to S3", bucket=bucket, key=key)
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to write to S3", bucket=bucket, key=key, error=str(e))
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error writing to S3", bucket=bucket, key=key, error=str(e))
            return False


class ConcertDataProcessor(StreamProcessor):
    """Processor for concert-related data from Kinesis streams."""
    
    def __init__(self, raw_bucket: str = "concert-data-raw", processed_bucket: str = "concert-data-processed"):
        super().__init__()
        self.raw_bucket = raw_bucket
        self.processed_bucket = processed_bucket
    
    def process_artist_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an artist record for data warehouse loading.
        
        Args:
            record: Artist record from stream
            
        Returns:
            Processed record ready for data warehouse
        """
        payload = record['payload']
        
        # Normalize artist data
        processed_record = {
            'artist_id': payload.get('artist_id'),
            'name': payload.get('name', '').strip(),
            'genres': payload.get('genre', []) if isinstance(payload.get('genre'), list) else [payload.get('genre', '')],
            'popularity_score': float(payload.get('popularity_score', 0.0)),
            'formation_date': payload.get('formation_date'),
            'members': payload.get('members', []),
            'spotify_id': payload.get('spotify_id'),
            'external_urls': payload.get('external_urls', {}),
            'followers': payload.get('followers', 0),
            'images': payload.get('images', []),
            'processed_timestamp': datetime.utcnow().isoformat(),
            'source': record['source'],
            'ingestion_timestamp': record['ingestion_timestamp']
        }
        
        return processed_record
    
    def process_venue_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a venue record for data warehouse loading.
        
        Args:
            record: Venue record from stream
            
        Returns:
            Processed record ready for data warehouse
        """
        payload = record['payload']
        
        # Normalize venue data
        processed_record = {
            'venue_id': payload.get('venue_id'),
            'name': payload.get('name', '').strip(),
            'location': {
                'address': payload.get('location', {}).get('address', ''),
                'city': payload.get('location', {}).get('city', ''),
                'state': payload.get('location', {}).get('state', ''),
                'country': payload.get('location', {}).get('country', ''),
                'postal_code': payload.get('location', {}).get('postal_code', ''),
                'latitude': payload.get('location', {}).get('latitude'),
                'longitude': payload.get('location', {}).get('longitude')
            },
            'capacity': int(payload.get('capacity', 0)) if payload.get('capacity') else None,
            'venue_type': payload.get('venue_type', ''),
            'amenities': payload.get('amenities', []),
            'ticketmaster_id': payload.get('ticketmaster_id'),
            'external_urls': payload.get('external_urls', {}),
            'processed_timestamp': datetime.utcnow().isoformat(),
            'source': record['source'],
            'ingestion_timestamp': record['ingestion_timestamp']
        }
        
        return processed_record
    
    def process_concert_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a concert/event record for data warehouse loading.
        
        Args:
            record: Concert record from stream
            
        Returns:
            Processed record ready for data warehouse
        """
        payload = record['payload']
        
        # Normalize concert data
        processed_record = {
            'concert_id': payload.get('concert_id') or payload.get('event_id'),
            'artist_id': payload.get('artist_id'),
            'venue_id': payload.get('venue_id'),
            'event_date': payload.get('event_date'),
            'event_time': payload.get('event_time'),
            'ticket_prices': payload.get('ticket_prices', {}),
            'total_attendance': payload.get('total_attendance'),
            'revenue': payload.get('revenue'),
            'status': payload.get('status', 'scheduled'),
            'genre': payload.get('genre', ''),
            'description': payload.get('description', ''),
            'external_urls': payload.get('external_urls', {}),
            'ticketmaster_id': payload.get('ticketmaster_id'),
            'processed_timestamp': datetime.utcnow().isoformat(),
            'source': record['source'],
            'ingestion_timestamp': record['ingestion_timestamp']
        }
        
        return processed_record
    
    def process_ticket_sale_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket sale record for data warehouse loading.
        
        Args:
            record: Ticket sale record from stream
            
        Returns:
            Processed record ready for data warehouse
        """
        payload = record['payload']
        
        # Normalize ticket sale data
        processed_record = {
            'sale_id': payload.get('sale_id'),
            'concert_id': payload.get('concert_id'),
            'price_tier': payload.get('price_tier', ''),
            'quantity': int(payload.get('quantity', 1)),
            'unit_price': float(payload.get('unit_price', 0.0)),
            'total_price': float(payload.get('total_price', 0.0)),
            'purchase_timestamp': payload.get('purchase_timestamp'),
            'customer_segment': payload.get('customer_segment', ''),
            'payment_method': payload.get('payment_method', ''),
            'processed_timestamp': datetime.utcnow().isoformat(),
            'source': record['source'],
            'ingestion_timestamp': record['ingestion_timestamp']
        }
        
        return processed_record
    
    def process_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of records from Kinesis stream.
        
        Args:
            records: List of Kinesis records
            
        Returns:
            Processing results summary
        """
        results = {
            'total_records': len(records),
            'successful_records': 0,
            'failed_records': 0,
            'records_by_type': {},
            'errors': []
        }
        
        processed_data = {
            'artists': [],
            'venues': [],
            'concerts': [],
            'ticket_sales': []
        }
        
        for kinesis_record in records:
            try:
                # Decode Kinesis record
                record = self.decode_kinesis_record(kinesis_record)
                if not record:
                    results['failed_records'] += 1
                    continue
                
                # Validate record structure
                if not self.validate_record_structure(record):
                    results['failed_records'] += 1
                    continue
                
                # Process based on data type
                data_type = record['data_type']
                
                if data_type == 'artists':
                    processed_record = self.process_artist_record(record)
                    processed_data['artists'].append(processed_record)
                elif data_type == 'venues':
                    processed_record = self.process_venue_record(record)
                    processed_data['venues'].append(processed_record)
                elif data_type in ['concerts', 'events']:
                    processed_record = self.process_concert_record(record)
                    processed_data['concerts'].append(processed_record)
                elif data_type == 'ticket_sales':
                    processed_record = self.process_ticket_sale_record(record)
                    processed_data['ticket_sales'].append(processed_record)
                else:
                    self.logger.warning(f"Unknown data type: {data_type}")
                    results['failed_records'] += 1
                    continue
                
                # Update counters
                results['successful_records'] += 1
                results['records_by_type'][data_type] = results['records_by_type'].get(data_type, 0) + 1
                
                # Store raw record in S3
                raw_key = f"raw/{data_type}/{datetime.utcnow().strftime('%Y/%m/%d')}/{record.get('record_id', 'unknown')}.json"
                self.write_to_s3(self.raw_bucket, raw_key, record)
                
            except Exception as e:
                error_msg = f"Failed to process record: {str(e)}"
                results['errors'].append(error_msg)
                results['failed_records'] += 1
                self.logger.error(error_msg, record=kinesis_record)
        
        # Write processed data to S3 by type
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        for data_type, records_list in processed_data.items():
            if records_list:
                processed_key = f"processed/{data_type}/{datetime.utcnow().strftime('%Y/%m/%d')}/batch_{timestamp}.json"
                self.write_to_s3(self.processed_bucket, processed_key, records_list)
        
        self.logger.info(
            "Batch processing completed",
            total_records=results['total_records'],
            successful_records=results['successful_records'],
            failed_records=results['failed_records'],
            records_by_type=results['records_by_type']
        )
        
        return results


# Lambda function handlers
def kinesis_stream_processor_handler(event, context):
    """
    AWS Lambda handler for processing Kinesis stream records.
    
    Args:
        event: Lambda event containing Kinesis records
        context: Lambda context object
        
    Returns:
        Processing results
    """
    logger.info("Kinesis stream processor started", event_source=event.get('eventSource'))
    
    try:
        # Initialize processor
        processor = ConcertDataProcessor()
        
        # Extract Kinesis records from event
        kinesis_records = []
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:kinesis':
                kinesis_records.append(record['kinesis'])
        
        if not kinesis_records:
            logger.warning("No Kinesis records found in event")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No records to process'})
            }
        
        # Process records
        results = processor.process_records(kinesis_records)
        
        logger.info("Kinesis stream processing completed", results=results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Records processed successfully',
                'results': results
            })
        }
        
    except Exception as e:
        error_msg = f"Lambda function failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }


def data_quality_processor_handler(event, context):
    """
    AWS Lambda handler for data quality processing and validation.
    
    Args:
        event: Lambda event containing S3 or Kinesis records
        context: Lambda context object
        
    Returns:
        Data quality results
    """
    logger.info("Data quality processor started", event_source=event.get('eventSource'))
    
    try:
        # This is a placeholder for data quality processing
        # In a full implementation, this would:
        # 1. Validate data against schemas
        # 2. Check for duplicates
        # 3. Perform data profiling
        # 4. Generate quality metrics
        # 5. Send alerts for quality issues
        
        quality_results = {
            'records_validated': 0,
            'quality_score': 100.0,
            'issues_found': [],
            'recommendations': []
        }
        
        logger.info("Data quality processing completed", results=quality_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data quality processing completed',
                'results': quality_results
            })
        }
        
    except Exception as e:
        error_msg = f"Data quality processor failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }


def stream_analytics_processor_handler(event, context):
    """
    AWS Lambda handler for real-time stream analytics.
    
    Args:
        event: Lambda event containing Kinesis records
        context: Lambda context object
        
    Returns:
        Analytics results
    """
    logger.info("Stream analytics processor started", event_source=event.get('eventSource'))
    
    try:
        # This is a placeholder for real-time analytics
        # In a full implementation, this would:
        # 1. Calculate real-time metrics
        # 2. Detect anomalies
        # 3. Update dashboards
        # 4. Trigger alerts
        # 5. Update ML model features
        
        analytics_results = {
            'metrics_calculated': 0,
            'anomalies_detected': 0,
            'alerts_sent': 0,
            'dashboard_updates': 0
        }
        
        logger.info("Stream analytics processing completed", results=analytics_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Stream analytics processing completed',
                'results': analytics_results
            })
        }
        
    except Exception as e:
        error_msg = f"Stream analytics processor failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }