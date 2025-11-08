"""
Kinesis integration service that orchestrates streaming data pipeline.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import structlog

from ..infrastructure.kinesis_client import KinesisClient, KinesisStreamError
from ..infrastructure.lambda_deployment import LambdaDeployer, LambdaDeploymentError
from .stream_producer import StreamProducerService, StreamProducerResult
from .external_apis.ingestion_service import DataIngestionService
from ..config.settings import settings

logger = structlog.get_logger(__name__)


class KinesisIntegrationResult:
    """Result of Kinesis integration operations."""
    
    def __init__(
        self,
        success: bool,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None
    ):
        self.success = success
        self.operation = operation
        self.details = details or {}
        self.errors = errors or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "operation": self.operation,
            "details": self.details,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


class KinesisIntegrationService:
    """
    Service for managing the complete Kinesis streaming integration.
    """
    
    def __init__(self):
        self.kinesis_client = KinesisClient()
        self.lambda_deployer = LambdaDeployer()
        self.stream_producer = StreamProducerService()
        self.logger = structlog.get_logger("KinesisIntegrationService")
    
    async def setup_complete_integration(self) -> KinesisIntegrationResult:
        """
        Set up the complete Kinesis streaming integration including:
        - Kinesis stream creation
        - Lambda function deployment
        - Event source mappings
        
        Returns:
            KinesisIntegrationResult with setup details
        """
        setup_details = {
            'stream_created': False,
            'lambda_functions_deployed': [],
            'event_source_mappings': [],
            'stream_info': {},
            'deployment_results': {}
        }
        errors = []
        
        try:
            self.logger.info("Starting complete Kinesis integration setup")
            
            # Step 1: Create Kinesis stream
            try:
                stream_created = await self.kinesis_client.create_stream_if_not_exists()
                setup_details['stream_created'] = stream_created
                
                if stream_created:
                    # Get stream information
                    stream_info = self.kinesis_client.get_stream_description()
                    setup_details['stream_info'] = stream_info
                    self.logger.info("Kinesis stream setup completed", stream_name=settings.aws.kinesis_stream_name)
                else:
                    errors.append("Failed to create or verify Kinesis stream")
                    
            except KinesisStreamError as e:
                error_msg = f"Kinesis stream setup failed: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
            
            # Step 2: Deploy Lambda functions
            try:
                deployment_results = self.lambda_deployer.deploy_kinesis_processing_functions()
                setup_details['deployment_results'] = deployment_results
                setup_details['lambda_functions_deployed'] = list(deployment_results['functions'].keys())
                setup_details['event_source_mappings'] = list(deployment_results['event_source_mappings'].keys())
                
                if deployment_results['errors']:
                    errors.extend(deployment_results['errors'])
                
                self.logger.info(
                    "Lambda functions deployment completed",
                    functions_deployed=len(deployment_results['functions']),
                    errors=len(deployment_results['errors'])
                )
                
            except LambdaDeploymentError as e:
                error_msg = f"Lambda deployment failed: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
            
            # Step 3: Validate integration
            integration_valid = await self._validate_integration()
            setup_details['integration_valid'] = integration_valid
            
            if not integration_valid:
                errors.append("Integration validation failed")
            
            success = len(errors) == 0 and setup_details['stream_created'] and integration_valid
            
            self.logger.info(
                "Complete Kinesis integration setup finished",
                success=success,
                errors_count=len(errors)
            )
            
            return KinesisIntegrationResult(
                success=success,
                operation="setup_complete_integration",
                details=setup_details,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during integration setup: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return KinesisIntegrationResult(
                success=False,
                operation="setup_complete_integration",
                details=setup_details,
                errors=errors
            )
    
    async def _validate_integration(self) -> bool:
        """
        Validate that the Kinesis integration is working properly.
        
        Returns:
            True if integration is valid, False otherwise
        """
        try:
            # Check stream status
            stream_info = self.kinesis_client.get_stream_description()
            if not stream_info.get('success'):
                self.logger.error("Stream validation failed", error=stream_info.get('error'))
                return False
            
            if stream_info.get('stream_status') != 'ACTIVE':
                self.logger.error("Stream is not active", status=stream_info.get('stream_status'))
                return False
            
            # Check Lambda functions
            deployed_functions = self.lambda_deployer.list_deployed_functions()
            expected_functions = ['kinesis-stream-processor', 'data-quality-processor', 'stream-analytics-processor']
            
            deployed_names = [func['function_name'] for func in deployed_functions]
            missing_functions = [name for name in expected_functions if name not in deployed_names]
            
            if missing_functions:
                self.logger.error("Missing Lambda functions", missing=missing_functions)
                return False
            
            self.logger.info("Integration validation passed")
            return True
            
        except Exception as e:
            self.logger.error("Integration validation failed", error=str(e))
            return False
    
    async def test_streaming_pipeline(
        self,
        test_data_size: str = "small"
    ) -> KinesisIntegrationResult:
        """
        Test the complete streaming pipeline with sample data.
        
        Args:
            test_data_size: Size of test data ("small", "medium", "large")
            
        Returns:
            KinesisIntegrationResult with test results
        """
        test_details = {
            'test_data_size': test_data_size,
            'streaming_results': {},
            'records_sent': 0,
            'records_failed': 0,
            'test_duration_seconds': 0
        }
        errors = []
        
        try:
            start_time = datetime.utcnow()
            self.logger.info("Starting streaming pipeline test", test_data_size=test_data_size)
            
            # Define test parameters based on size
            test_params = {
                "small": {
                    "artist_queries": ["rock", "pop"],
                    "venue_cities": ["New York", "Los Angeles"],
                    "event_cities": ["New York"],
                    "event_keywords": ["concert"]
                },
                "medium": {
                    "artist_queries": ["rock", "pop", "jazz", "blues"],
                    "venue_cities": ["New York", "Los Angeles", "Chicago"],
                    "event_cities": ["New York", "Los Angeles"],
                    "event_keywords": ["concert", "music"]
                },
                "large": {
                    "artist_queries": ["rock", "pop", "jazz", "blues", "country", "electronic"],
                    "venue_cities": ["New York", "Los Angeles", "Chicago", "Nashville", "Austin"],
                    "event_cities": ["New York", "Los Angeles", "Chicago"],
                    "event_keywords": ["concert", "music", "live"]
                }
            }
            
            params = test_params.get(test_data_size, test_params["small"])
            
            # Test streaming with API data
            async with self.stream_producer as producer:
                streaming_results = await producer.stream_api_data(**params)
                test_details['streaming_results'] = {
                    data_type: result.to_dict() for data_type, result in streaming_results.items()
                }
                
                # Calculate totals
                for result in streaming_results.values():
                    test_details['records_sent'] += result.records_sent
                    test_details['records_failed'] += result.records_failed
                    if result.errors:
                        errors.extend(result.errors)
            
            # Calculate test duration
            end_time = datetime.utcnow()
            test_details['test_duration_seconds'] = (end_time - start_time).total_seconds()
            
            success = len(errors) == 0 and test_details['records_sent'] > 0
            
            self.logger.info(
                "Streaming pipeline test completed",
                success=success,
                records_sent=test_details['records_sent'],
                records_failed=test_details['records_failed'],
                duration_seconds=test_details['test_duration_seconds']
            )
            
            return KinesisIntegrationResult(
                success=success,
                operation="test_streaming_pipeline",
                details=test_details,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Streaming pipeline test failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return KinesisIntegrationResult(
                success=False,
                operation="test_streaming_pipeline",
                details=test_details,
                errors=errors
            )
    
    async def stream_file_data_batch(
        self,
        file_paths: List[Union[str, Path]],
        data_types: Union[str, List[str]]
    ) -> KinesisIntegrationResult:
        """
        Stream data from multiple files to Kinesis.
        
        Args:
            file_paths: List of file paths to process
            data_types: Single data type or list of data types (one per file)
            
        Returns:
            KinesisIntegrationResult with streaming results
        """
        streaming_details = {
            'files_processed': len(file_paths),
            'streaming_results': {},
            'total_records_sent': 0,
            'total_records_failed': 0
        }
        errors = []
        
        try:
            self.logger.info("Starting batch file streaming", file_count=len(file_paths))
            
            # Stream batch files
            streaming_results = self.stream_producer.stream_batch_files(
                file_paths=file_paths,
                data_types=data_types,
                batch_size=100,
                validate_data=True
            )
            
            # Process results
            streaming_details['streaming_results'] = {
                str(file_path): result.to_dict() for file_path, result in streaming_results.items()
            }
            
            for result in streaming_results.values():
                streaming_details['total_records_sent'] += result.records_sent
                streaming_details['total_records_failed'] += result.records_failed
                if result.errors:
                    errors.extend(result.errors)
            
            success = len(errors) == 0 and streaming_details['total_records_sent'] > 0
            
            self.logger.info(
                "Batch file streaming completed",
                success=success,
                files_processed=streaming_details['files_processed'],
                records_sent=streaming_details['total_records_sent'],
                records_failed=streaming_details['total_records_failed']
            )
            
            return KinesisIntegrationResult(
                success=success,
                operation="stream_file_data_batch",
                details=streaming_details,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Batch file streaming failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return KinesisIntegrationResult(
                success=False,
                operation="stream_file_data_batch",
                details=streaming_details,
                errors=errors
            )
    
    def get_integration_status(self) -> KinesisIntegrationResult:
        """
        Get the current status of the Kinesis integration.
        
        Returns:
            KinesisIntegrationResult with status information
        """
        status_details = {
            'stream_status': {},
            'lambda_functions': [],
            'integration_health': 'unknown'
        }
        errors = []
        
        try:
            # Check stream status
            stream_info = self.kinesis_client.get_stream_description()
            status_details['stream_status'] = stream_info
            
            if not stream_info.get('success'):
                errors.append(f"Stream status check failed: {stream_info.get('error')}")
            
            # Check Lambda functions
            deployed_functions = self.lambda_deployer.list_deployed_functions()
            status_details['lambda_functions'] = deployed_functions
            
            # Determine overall health
            if stream_info.get('stream_status') == 'ACTIVE' and len(deployed_functions) >= 3:
                status_details['integration_health'] = 'healthy'
            elif stream_info.get('stream_status') == 'ACTIVE':
                status_details['integration_health'] = 'partial'
            else:
                status_details['integration_health'] = 'unhealthy'
            
            success = len(errors) == 0
            
            self.logger.info(
                "Integration status checked",
                health=status_details['integration_health'],
                stream_status=stream_info.get('stream_status'),
                lambda_functions_count=len(deployed_functions)
            )
            
            return KinesisIntegrationResult(
                success=success,
                operation="get_integration_status",
                details=status_details,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Status check failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return KinesisIntegrationResult(
                success=False,
                operation="get_integration_status",
                details=status_details,
                errors=errors
            )
    
    async def cleanup_integration(self) -> KinesisIntegrationResult:
        """
        Clean up the Kinesis integration (for testing/development).
        
        Returns:
            KinesisIntegrationResult with cleanup details
        """
        cleanup_details = {
            'functions_deleted': [],
            'mappings_deleted': [],
            'stream_deleted': False
        }
        errors = []
        
        try:
            self.logger.info("Starting integration cleanup")
            
            # Note: In a production environment, you might not want to delete everything
            # This is primarily for development/testing cleanup
            
            # List functions to delete
            functions_to_delete = ['kinesis-stream-processor', 'data-quality-processor', 'stream-analytics-processor']
            
            for function_name in functions_to_delete:
                try:
                    self.lambda_deployer.lambda_client.delete_function(FunctionName=function_name)
                    cleanup_details['functions_deleted'].append(function_name)
                    self.logger.info("Lambda function deleted", function_name=function_name)
                except Exception as e:
                    if "ResourceNotFoundException" not in str(e):
                        errors.append(f"Failed to delete function {function_name}: {str(e)}")
            
            # Note: Kinesis streams are not deleted automatically as they may contain important data
            # In production, streams should be managed separately
            
            success = len(errors) == 0
            
            self.logger.info(
                "Integration cleanup completed",
                success=success,
                functions_deleted=len(cleanup_details['functions_deleted']),
                errors_count=len(errors)
            )
            
            return KinesisIntegrationResult(
                success=success,
                operation="cleanup_integration",
                details=cleanup_details,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return KinesisIntegrationResult(
                success=False,
                operation="cleanup_integration",
                details=cleanup_details,
                errors=errors
            )