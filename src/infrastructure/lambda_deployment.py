"""
Deployment utilities for AWS Lambda functions.
"""
import json
import zipfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError
import structlog

from ..config.settings import settings

logger = structlog.get_logger(__name__)


class LambdaDeploymentError(Exception):
    """Custom exception for Lambda deployment operations."""
    pass


class LambdaDeployer:
    """
    Utility class for deploying Lambda functions for Kinesis stream processing.
    """
    
    def __init__(self):
        self.logger = structlog.get_logger("LambdaDeployer")
        
        # Initialize AWS clients
        try:
            aws_credentials = settings.get_aws_credentials()
            self.lambda_client = boto3.client('lambda', **aws_credentials)
            self.iam_client = boto3.client('iam', **aws_credentials)
            self.s3_client = boto3.client('s3', **aws_credentials)
            self.logger.info("Lambda deployment clients initialized")
        except Exception as e:
            self.logger.error("Failed to initialize Lambda deployment clients", error=str(e))
            raise LambdaDeploymentError(f"Failed to initialize clients: {str(e)}")
    
    def create_lambda_execution_role(self, role_name: str) -> str:
        """
        Create IAM role for Lambda execution with necessary permissions.
        
        Args:
            role_name: Name for the IAM role
            
        Returns:
            ARN of the created role
        """
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Create the role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for Kinesis stream processing Lambda functions"
            )
            
            role_arn = response['Role']['Arn']
            self.logger.info("Lambda execution role created", role_name=role_name, role_arn=role_arn)
            
            # Attach necessary policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess'  # For writing processed data
            ]
            
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                self.logger.info("Policy attached to role", role_name=role_name, policy_arn=policy_arn)
            
            return role_arn
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                # Role already exists, get its ARN
                response = self.iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                self.logger.info("Lambda execution role already exists", role_name=role_name, role_arn=role_arn)
                return role_arn
            else:
                error_msg = f"Failed to create Lambda execution role: {str(e)}"
                self.logger.error(error_msg, role_name=role_name)
                raise LambdaDeploymentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating Lambda execution role: {str(e)}"
            self.logger.error(error_msg, role_name=role_name)
            raise LambdaDeploymentError(error_msg)
    
    def create_deployment_package(self, function_file: str, package_name: str) -> bytes:
        """
        Create deployment package (ZIP file) for Lambda function.
        
        Args:
            function_file: Path to the Python file containing the Lambda function
            package_name: Name for the deployment package
            
        Returns:
            ZIP file content as bytes
        """
        try:
            # Create a temporary ZIP file in memory
            import io
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add the main function file
                function_path = Path(function_file)
                if function_path.exists():
                    zip_file.write(function_path, function_path.name)
                    self.logger.info("Added function file to package", file=function_file)
                else:
                    raise LambdaDeploymentError(f"Function file not found: {function_file}")
                
                # Add dependencies (requirements would be handled by Lambda layers in production)
                # For this demo, we'll include minimal dependencies
                
                # Add configuration
                config_content = json.dumps({
                    "aws_region": settings.aws.region,
                    "kinesis_stream_name": settings.aws.kinesis_stream_name,
                    "s3_bucket_raw": settings.aws.s3_bucket_raw,
                    "s3_bucket_processed": settings.aws.s3_bucket_processed
                })
                
                zip_file.writestr("config.json", config_content)
                self.logger.info("Added configuration to package")
            
            zip_content = zip_buffer.getvalue()
            self.logger.info("Deployment package created", package_name=package_name, size_bytes=len(zip_content))
            
            return zip_content
            
        except Exception as e:
            error_msg = f"Failed to create deployment package: {str(e)}"
            self.logger.error(error_msg, function_file=function_file)
            raise LambdaDeploymentError(error_msg)
    
    def deploy_lambda_function(
        self,
        function_name: str,
        handler: str,
        role_arn: str,
        zip_content: bytes,
        description: str = "",
        timeout: int = 300,
        memory_size: int = 512,
        environment_variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Deploy Lambda function.
        
        Args:
            function_name: Name of the Lambda function
            handler: Handler function (e.g., 'lambda_functions.kinesis_stream_processor_handler')
            role_arn: ARN of the execution role
            zip_content: ZIP file content
            description: Function description
            timeout: Function timeout in seconds
            memory_size: Memory allocation in MB
            environment_variables: Environment variables for the function
            
        Returns:
            ARN of the deployed function
        """
        try:
            # Prepare environment variables
            env_vars = environment_variables or {}
            env_vars.update({
                'AWS_REGION': settings.aws.region,
                'KINESIS_STREAM_NAME': settings.aws.kinesis_stream_name,
                'S3_BUCKET_RAW': settings.aws.s3_bucket_raw,
                'S3_BUCKET_PROCESSED': settings.aws.s3_bucket_processed
            })
            
            # Try to create the function
            try:
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=role_arn,
                    Handler=handler,
                    Code={'ZipFile': zip_content},
                    Description=description,
                    Timeout=timeout,
                    MemorySize=memory_size,
                    Environment={'Variables': env_vars},
                    Publish=True
                )
                
                function_arn = response['FunctionArn']
                self.logger.info("Lambda function created", function_name=function_name, function_arn=function_arn)
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceConflictException':
                    # Function already exists, update it
                    self.logger.info("Function already exists, updating", function_name=function_name)
                    
                    # Update function code
                    self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_content
                    )
                    
                    # Update function configuration
                    response = self.lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Role=role_arn,
                        Handler=handler,
                        Description=description,
                        Timeout=timeout,
                        MemorySize=memory_size,
                        Environment={'Variables': env_vars}
                    )
                    
                    function_arn = response['FunctionArn']
                    self.logger.info("Lambda function updated", function_name=function_name, function_arn=function_arn)
                else:
                    raise
            
            return function_arn
            
        except ClientError as e:
            error_msg = f"Failed to deploy Lambda function: {str(e)}"
            self.logger.error(error_msg, function_name=function_name)
            raise LambdaDeploymentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error deploying Lambda function: {str(e)}"
            self.logger.error(error_msg, function_name=function_name)
            raise LambdaDeploymentError(error_msg)
    
    def create_kinesis_event_source_mapping(
        self,
        function_name: str,
        stream_arn: str,
        batch_size: int = 100,
        starting_position: str = 'LATEST'
    ) -> str:
        """
        Create event source mapping between Kinesis stream and Lambda function.
        
        Args:
            function_name: Name of the Lambda function
            stream_arn: ARN of the Kinesis stream
            batch_size: Number of records to send to function in each batch
            starting_position: Starting position in the stream (LATEST, TRIM_HORIZON)
            
        Returns:
            UUID of the event source mapping
        """
        try:
            response = self.lambda_client.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=function_name,
                StartingPosition=starting_position,
                BatchSize=batch_size,
                MaximumBatchingWindowInSeconds=5,  # Wait up to 5 seconds to collect records
                ParallelizationFactor=1  # Process one shard at a time
            )
            
            mapping_uuid = response['UUID']
            self.logger.info(
                "Kinesis event source mapping created",
                function_name=function_name,
                stream_arn=stream_arn,
                mapping_uuid=mapping_uuid
            )
            
            return mapping_uuid
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                self.logger.info("Event source mapping already exists", function_name=function_name)
                # List existing mappings to find the UUID
                mappings = self.lambda_client.list_event_source_mappings(
                    EventSourceArn=stream_arn,
                    FunctionName=function_name
                )
                if mappings['EventSourceMappings']:
                    return mappings['EventSourceMappings'][0]['UUID']
            
            error_msg = f"Failed to create event source mapping: {str(e)}"
            self.logger.error(error_msg, function_name=function_name, stream_arn=stream_arn)
            raise LambdaDeploymentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating event source mapping: {str(e)}"
            self.logger.error(error_msg, function_name=function_name, stream_arn=stream_arn)
            raise LambdaDeploymentError(error_msg)
    
    def deploy_kinesis_processing_functions(self) -> Dict[str, Any]:
        """
        Deploy all Lambda functions for Kinesis stream processing.
        
        Returns:
            Deployment results with function ARNs and mapping UUIDs
        """
        results = {
            'functions': {},
            'event_source_mappings': {},
            'errors': []
        }
        
        try:
            # Create execution role
            role_name = "KinesisStreamProcessingRole"
            role_arn = self.create_lambda_execution_role(role_name)
            
            # Wait a bit for role to propagate
            import time
            time.sleep(10)
            
            # Function configurations
            functions_config = [
                {
                    'name': 'kinesis-stream-processor',
                    'handler': 'lambda_functions.kinesis_stream_processor_handler',
                    'description': 'Process concert data from Kinesis stream',
                    'timeout': 300,
                    'memory_size': 512
                },
                {
                    'name': 'data-quality-processor',
                    'handler': 'lambda_functions.data_quality_processor_handler',
                    'description': 'Validate and monitor data quality',
                    'timeout': 180,
                    'memory_size': 256
                },
                {
                    'name': 'stream-analytics-processor',
                    'handler': 'lambda_functions.stream_analytics_processor_handler',
                    'description': 'Real-time analytics on stream data',
                    'timeout': 240,
                    'memory_size': 384
                }
            ]
            
            # Deploy each function
            for func_config in functions_config:
                try:
                    # Create deployment package
                    zip_content = self.create_deployment_package(
                        'src/infrastructure/lambda_functions.py',
                        func_config['name']
                    )
                    
                    # Deploy function
                    function_arn = self.deploy_lambda_function(
                        function_name=func_config['name'],
                        handler=func_config['handler'],
                        role_arn=role_arn,
                        zip_content=zip_content,
                        description=func_config['description'],
                        timeout=func_config['timeout'],
                        memory_size=func_config['memory_size']
                    )
                    
                    results['functions'][func_config['name']] = function_arn
                    
                    # Create event source mapping for main processor
                    if func_config['name'] == 'kinesis-stream-processor':
                        # We need the stream ARN - this would be constructed or retrieved
                        stream_arn = f"arn:aws:kinesis:{settings.aws.region}:*:stream/{settings.aws.kinesis_stream_name}"
                        
                        try:
                            mapping_uuid = self.create_kinesis_event_source_mapping(
                                function_name=func_config['name'],
                                stream_arn=stream_arn,
                                batch_size=100
                            )
                            results['event_source_mappings'][func_config['name']] = mapping_uuid
                        except Exception as e:
                            error_msg = f"Failed to create event source mapping for {func_config['name']}: {str(e)}"
                            results['errors'].append(error_msg)
                            self.logger.error(error_msg)
                    
                except Exception as e:
                    error_msg = f"Failed to deploy function {func_config['name']}: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(
                "Lambda functions deployment completed",
                functions_deployed=len(results['functions']),
                mappings_created=len(results['event_source_mappings']),
                errors=len(results['errors'])
            )
            
        except Exception as e:
            error_msg = f"Lambda deployment failed: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return results
    
    def list_deployed_functions(self) -> List[Dict[str, Any]]:
        """
        List all deployed Lambda functions.
        
        Returns:
            List of function information
        """
        try:
            response = self.lambda_client.list_functions()
            functions = []
            
            for func in response['Functions']:
                functions.append({
                    'function_name': func['FunctionName'],
                    'function_arn': func['FunctionArn'],
                    'runtime': func['Runtime'],
                    'handler': func['Handler'],
                    'description': func.get('Description', ''),
                    'timeout': func['Timeout'],
                    'memory_size': func['MemorySize'],
                    'last_modified': func['LastModified']
                })
            
            return functions
            
        except Exception as e:
            self.logger.error("Failed to list Lambda functions", error=str(e))
            return []