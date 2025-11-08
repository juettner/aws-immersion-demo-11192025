"""
AWS Kinesis client for real-time data streaming.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import structlog

from ..config.settings import settings

logger = structlog.get_logger(__name__)


class KinesisStreamError(Exception):
    """Custom exception for Kinesis stream operations."""
    pass


class StreamRecord:
    """Represents a record to be sent to Kinesis stream."""
    
    def __init__(
        self,
        data: Dict[str, Any],
        partition_key: Optional[str] = None,
        explicit_hash_key: Optional[str] = None
    ):
        self.data = data
        self.partition_key = partition_key or str(uuid.uuid4())
        self.explicit_hash_key = explicit_hash_key
        self.timestamp = datetime.utcnow()
    
    def to_kinesis_record(self) -> Dict[str, Any]:
        """Convert to Kinesis record format."""
        record = {
            'Data': json.dumps({
                'timestamp': self.timestamp.isoformat(),
                'data': self.data
            }),
            'PartitionKey': self.partition_key
        }
        
        if self.explicit_hash_key:
            record['ExplicitHashKey'] = self.explicit_hash_key
        
        return record


class KinesisClient:
    """
    AWS Kinesis client for streaming concert data.
    """
    
    def __init__(self, stream_name: Optional[str] = None):
        self.stream_name = stream_name or settings.aws.kinesis_stream_name
        self.logger = structlog.get_logger("KinesisClient")
        
        # Initialize Kinesis client
        try:
            aws_credentials = settings.get_aws_credentials()
            self.kinesis_client = boto3.client('kinesis', **aws_credentials)
            self.logger.info("Kinesis client initialized", stream_name=self.stream_name)
        except Exception as e:
            self.logger.error("Failed to initialize Kinesis client", error=str(e))
            raise KinesisStreamError(f"Failed to initialize Kinesis client: {str(e)}")
    
    async def create_stream_if_not_exists(self, shard_count: Optional[int] = None) -> bool:
        """
        Create Kinesis stream if it doesn't exist.
        
        Args:
            shard_count: Number of shards for the stream
            
        Returns:
            True if stream was created or already exists, False otherwise
        """
        shard_count = shard_count or settings.aws.kinesis_shard_count
        
        try:
            # Check if stream exists
            response = self.kinesis_client.describe_stream(StreamName=self.stream_name)
            stream_status = response['StreamDescription']['StreamStatus']
            
            if stream_status == 'ACTIVE':
                self.logger.info("Stream already exists and is active", stream_name=self.stream_name)
                return True
            elif stream_status in ['CREATING', 'UPDATING']:
                self.logger.info("Stream is being created/updated", stream_name=self.stream_name, status=stream_status)
                return True
            else:
                self.logger.warning("Stream exists but not active", stream_name=self.stream_name, status=stream_status)
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ResourceNotFoundException':
                # Stream doesn't exist, create it
                try:
                    self.kinesis_client.create_stream(
                        StreamName=self.stream_name,
                        ShardCount=shard_count
                    )
                    self.logger.info(
                        "Stream creation initiated",
                        stream_name=self.stream_name,
                        shard_count=shard_count
                    )
                    return True
                except ClientError as create_error:
                    self.logger.error(
                        "Failed to create stream",
                        stream_name=self.stream_name,
                        error=str(create_error)
                    )
                    raise KinesisStreamError(f"Failed to create stream: {str(create_error)}")
            else:
                self.logger.error("Error checking stream status", error=str(e))
                raise KinesisStreamError(f"Error checking stream status: {str(e)}")
        
        except Exception as e:
            self.logger.error("Unexpected error during stream creation", error=str(e))
            raise KinesisStreamError(f"Unexpected error: {str(e)}")
    
    def put_record(
        self,
        data: Dict[str, Any],
        partition_key: Optional[str] = None,
        explicit_hash_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Put a single record to the Kinesis stream.
        
        Args:
            data: Data to send to the stream
            partition_key: Partition key for the record
            explicit_hash_key: Explicit hash key for the record
            
        Returns:
            Response from Kinesis put_record operation
        """
        try:
            record = StreamRecord(data, partition_key, explicit_hash_key)
            kinesis_record = record.to_kinesis_record()
            
            response = self.kinesis_client.put_record(
                StreamName=self.stream_name,
                **kinesis_record
            )
            
            self.logger.debug(
                "Record sent to stream",
                stream_name=self.stream_name,
                sequence_number=response['SequenceNumber'],
                shard_id=response['ShardId']
            )
            
            return {
                'success': True,
                'sequence_number': response['SequenceNumber'],
                'shard_id': response['ShardId'],
                'timestamp': record.timestamp.isoformat()
            }
            
        except ClientError as e:
            error_msg = f"Failed to put record to stream: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error putting record: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def put_records(
        self,
        records: List[Dict[str, Any]],
        partition_key_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Put multiple records to the Kinesis stream in batch.
        
        Args:
            records: List of data records to send
            partition_key_field: Field name to use as partition key from each record
            
        Returns:
            Batch operation results
        """
        if not records:
            return {
                'success': True,
                'records_processed': 0,
                'records_successful': 0,
                'records_failed': 0,
                'failed_records': []
            }
        
        try:
            # Prepare Kinesis records
            kinesis_records = []
            for i, record_data in enumerate(records):
                partition_key = None
                if partition_key_field and partition_key_field in record_data:
                    partition_key = str(record_data[partition_key_field])
                
                stream_record = StreamRecord(record_data, partition_key)
                kinesis_records.append(stream_record.to_kinesis_record())
            
            # Send batch to Kinesis
            response = self.kinesis_client.put_records(
                Records=kinesis_records,
                StreamName=self.stream_name
            )
            
            # Process results
            failed_record_count = response['FailedRecordCount']
            successful_count = len(records) - failed_record_count
            failed_records = []
            
            if failed_record_count > 0:
                for i, record_result in enumerate(response['Records']):
                    if 'ErrorCode' in record_result:
                        failed_records.append({
                            'index': i,
                            'error_code': record_result['ErrorCode'],
                            'error_message': record_result['ErrorMessage'],
                            'data': records[i]
                        })
            
            self.logger.info(
                "Batch records sent to stream",
                stream_name=self.stream_name,
                total_records=len(records),
                successful_records=successful_count,
                failed_records=failed_record_count
            )
            
            return {
                'success': failed_record_count == 0,
                'records_processed': len(records),
                'records_successful': successful_count,
                'records_failed': failed_record_count,
                'failed_records': failed_records,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_msg = f"Failed to put batch records to stream: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name, record_count=len(records))
            return {
                'success': False,
                'records_processed': len(records),
                'records_successful': 0,
                'records_failed': len(records),
                'error': error_msg,
                'failed_records': [{'index': i, 'data': record} for i, record in enumerate(records)],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error putting batch records: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name, record_count=len(records))
            return {
                'success': False,
                'records_processed': len(records),
                'records_successful': 0,
                'records_failed': len(records),
                'error': error_msg,
                'failed_records': [{'index': i, 'data': record} for i, record in enumerate(records)],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_stream_description(self) -> Dict[str, Any]:
        """
        Get detailed information about the Kinesis stream.
        
        Returns:
            Stream description and metadata
        """
        try:
            response = self.kinesis_client.describe_stream(StreamName=self.stream_name)
            stream_desc = response['StreamDescription']
            
            return {
                'success': True,
                'stream_name': stream_desc['StreamName'],
                'stream_arn': stream_desc['StreamARN'],
                'stream_status': stream_desc['StreamStatus'],
                'shard_count': len(stream_desc['Shards']),
                'retention_period': stream_desc['RetentionPeriodHours'],
                'creation_timestamp': stream_desc['StreamCreationTimestamp'].isoformat(),
                'shards': [
                    {
                        'shard_id': shard['ShardId'],
                        'hash_key_range': shard['HashKeyRange'],
                        'sequence_number_range': shard['SequenceNumberRange']
                    }
                    for shard in stream_desc['Shards']
                ]
            }
            
        except ClientError as e:
            error_msg = f"Failed to describe stream: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error describing stream: {str(e)}"
            self.logger.error(error_msg, stream_name=self.stream_name)
            return {
                'success': False,
                'error': error_msg
            }
    
    def list_streams(self) -> Dict[str, Any]:
        """
        List all Kinesis streams in the account.
        
        Returns:
            List of stream names and metadata
        """
        try:
            response = self.kinesis_client.list_streams()
            
            return {
                'success': True,
                'stream_names': response['StreamNames'],
                'has_more_streams': response['HasMoreStreams']
            }
            
        except ClientError as e:
            error_msg = f"Failed to list streams: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error listing streams: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }