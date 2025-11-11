"""
Deployment script for API Lambda functions.

This script packages and deploys Lambda functions for API Gateway endpoints.
"""
import os
import sys
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


class LambdaDeployer:
    """Deploy Lambda functions for API Gateway."""
    
    def __init__(
        self,
        region: str = 'us-east-1',
        role_arn: Optional[str] = None,
        s3_bucket: Optional[str] = None
    ):
        """
        Initialize Lambda deployer.
        
        Args:
            region: AWS region
            role_arn: IAM role ARN for Lambda execution
            s3_bucket: S3 bucket for Lambda deployment packages
        """
        self.region = region
        self.role_arn = role_arn
        self.s3_bucket = s3_bucket
        
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Lambda function configurations
        self.functions = {
            'chatbot': {
                'handler': 'api_lambda_handlers.chatbot_handler',
                'description': 'Chatbot message processing',
                'timeout': 30,
                'memory': 512,
                'environment': {
                    'BEDROCK_AGENT_ID': os.environ.get('BEDROCK_AGENT_ID', ''),
                    'BEDROCK_AGENT_ALIAS_ID': os.environ.get('BEDROCK_AGENT_ALIAS_ID', ''),
                    'REDSHIFT_CLUSTER_ID': os.environ.get('REDSHIFT_CLUSTER_ID', ''),
                    'REDSHIFT_DATABASE': os.environ.get('REDSHIFT_DATABASE', 'concert_data')
                }
            },
            'venue-popularity': {
                'handler': 'api_lambda_handlers.venue_popularity_handler',
                'description': 'Venue popularity queries',
                'timeout': 60,
                'memory': 512,
                'environment': {
                    'REDSHIFT_CLUSTER_ID': os.environ.get('REDSHIFT_CLUSTER_ID', ''),
                    'REDSHIFT_DATABASE': os.environ.get('REDSHIFT_DATABASE', 'concert_data')
                }
            },
            'ticket-prediction': {
                'handler': 'api_lambda_handlers.ticket_prediction_handler',
                'description': 'Ticket sales predictions',
                'timeout': 30,
                'memory': 512,
                'environment': {
                    'SAGEMAKER_TICKET_ENDPOINT': os.environ.get('SAGEMAKER_TICKET_ENDPOINT', ''),
                    'REDSHIFT_CLUSTER_ID': os.environ.get('REDSHIFT_CLUSTER_ID', ''),
                    'REDSHIFT_DATABASE': os.environ.get('REDSHIFT_DATABASE', 'concert_data')
                }
            },
            'recommendations': {
                'handler': 'api_lambda_handlers.recommendations_handler',
                'description': 'Concert recommendations',
                'timeout': 60,
                'memory': 512,
                'environment': {
                    'REDSHIFT_CLUSTER_ID': os.environ.get('REDSHIFT_CLUSTER_ID', ''),
                    'REDSHIFT_DATABASE': os.environ.get('REDSHIFT_DATABASE', 'concert_data')
                }
            },
            'health-check': {
                'handler': 'api_lambda_handlers.health_check_handler',
                'description': 'API health check',
                'timeout': 10,
                'memory': 256,
                'environment': {
                    'REDSHIFT_CLUSTER_ID': os.environ.get('REDSHIFT_CLUSTER_ID', ''),
                    'BEDROCK_AGENT_ID': os.environ.get('BEDROCK_AGENT_ID', ''),
                    'BEDROCK_AGENT_ALIAS_ID': os.environ.get('BEDROCK_AGENT_ALIAS_ID', ''),
                    'SAGEMAKER_VENUE_ENDPOINT': os.environ.get('SAGEMAKER_VENUE_ENDPOINT', ''),
                    'SAGEMAKER_TICKET_ENDPOINT': os.environ.get('SAGEMAKER_TICKET_ENDPOINT', '')
                }
            }
        }
    
    def create_execution_role(self, role_name: str = 'ConcertAPILambdaRole') -> str:
        """
        Create IAM role for Lambda execution.
        
        Args:
            role_name: Name for the IAM role
            
        Returns:
            Role ARN
        """
        try:
            # Check if role already exists
            try:
                response = self.iam_client.get_role(RoleName=role_name)
                logger.info("IAM role already exists", role_name=role_name)
                return response['Role']['Arn']
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create role
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
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for Concert API Lambda functions'
            )
            
            role_arn = response['Role']['Arn']
            logger.info("Created IAM role", role_name=role_name, role_arn=role_arn)
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonRedshiftDataFullAccess',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
            ]
            
            for policy_arn in policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                    logger.info("Attached policy to role", policy=policy_arn)
                except ClientError as e:
                    logger.warning("Failed to attach policy", policy=policy_arn, error=str(e))
            
            # Wait for role to be available
            import time
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            logger.error("Failed to create execution role", error=str(e))
            raise
    
    def create_deployment_package(self, output_path: str) -> str:
        """
        Create Lambda deployment package with dependencies.
        
        Args:
            output_path: Path to save the deployment package
            
        Returns:
            Path to the deployment package
        """
        logger.info("Creating Lambda deployment package")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy Lambda handler file
            handler_source = Path('src/infrastructure/api_lambda_handlers.py')
            if not handler_source.exists():
                raise FileNotFoundError(f"Handler file not found: {handler_source}")
            
            shutil.copy(handler_source, temp_path / 'api_lambda_handlers.py')
            
            # Install dependencies
            requirements = [
                'boto3',
                'botocore',
                'structlog'
            ]
            
            # Note: In production, you would install these to temp_path
            # For now, we rely on Lambda's built-in boto3
            
            # Create ZIP file
            zip_path = Path(output_path)
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)
            
            logger.info("Created deployment package", path=str(zip_path))
            return str(zip_path)
    
    def upload_to_s3(self, local_path: str, s3_key: str) -> str:
        """
        Upload deployment package to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key
            
        Returns:
            S3 URI
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        logger.info("Uploading to S3", bucket=self.s3_bucket, key=s3_key)
        
        with open(local_path, 'rb') as f:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=f
            )
        
        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
        logger.info("Uploaded to S3", uri=s3_uri)
        return s3_uri
    
    def deploy_function(
        self,
        function_name: str,
        config: Dict,
        deployment_package_path: str
    ) -> Dict:
        """
        Deploy or update a Lambda function.
        
        Args:
            function_name: Lambda function name
            config: Function configuration
            deployment_package_path: Path to deployment package
            
        Returns:
            Function details
        """
        full_function_name = f"concert-api-{function_name}"
        
        logger.info("Deploying Lambda function", function_name=full_function_name)
        
        # Read deployment package
        with open(deployment_package_path, 'rb') as f:
            zip_content = f.read()
        
        try:
            # Try to update existing function
            try:
                response = self.lambda_client.update_function_code(
                    FunctionName=full_function_name,
                    ZipFile=zip_content
                )
                logger.info("Updated function code", function_name=full_function_name)
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=full_function_name,
                    Handler=config['handler'],
                    Timeout=config['timeout'],
                    MemorySize=config['memory'],
                    Environment={'Variables': config['environment']}
                )
                logger.info("Updated function configuration", function_name=full_function_name)
                
                return response
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
                
                # Create new function
                if not self.role_arn:
                    self.role_arn = self.create_execution_role()
                
                response = self.lambda_client.create_function(
                    FunctionName=full_function_name,
                    Runtime='python3.11',
                    Role=self.role_arn,
                    Handler=config['handler'],
                    Code={'ZipFile': zip_content},
                    Description=config['description'],
                    Timeout=config['timeout'],
                    MemorySize=config['memory'],
                    Environment={'Variables': config['environment']},
                    Tags={
                        'Project': 'ConcertDataPlatform',
                        'Component': 'API',
                        'ManagedBy': 'Deployment Script'
                    }
                )
                
                logger.info("Created Lambda function", function_name=full_function_name)
                return response
                
        except Exception as e:
            logger.error("Failed to deploy function", function_name=full_function_name, error=str(e))
            raise
    
    def add_api_gateway_permission(self, function_name: str, api_id: str) -> None:
        """
        Add permission for API Gateway to invoke Lambda function.
        
        Args:
            function_name: Lambda function name
            api_id: API Gateway ID
        """
        full_function_name = f"concert-api-{function_name}"
        
        try:
            self.lambda_client.add_permission(
                FunctionName=full_function_name,
                StatementId=f'apigateway-{api_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.region}:*:{api_id}/*'
            )
            logger.info("Added API Gateway permission", function_name=full_function_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                logger.info("Permission already exists", function_name=full_function_name)
            else:
                raise
    
    def deploy_all(self, api_gateway_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Deploy all Lambda functions.
        
        Args:
            api_gateway_id: Optional API Gateway ID for permissions
            
        Returns:
            Dictionary of deployment results
        """
        logger.info("Starting deployment of all Lambda functions")
        
        # Create deployment package
        package_path = self.create_deployment_package('build/lambda-deployment.zip')
        
        results = {}
        
        for function_name, config in self.functions.items():
            try:
                result = self.deploy_function(function_name, config, package_path)
                results[function_name] = {
                    'status': 'success',
                    'function_arn': result['FunctionArn'],
                    'function_name': result['FunctionName']
                }
                
                # Add API Gateway permission if provided
                if api_gateway_id:
                    self.add_api_gateway_permission(function_name, api_gateway_id)
                
            except Exception as e:
                results[function_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                logger.error("Failed to deploy function", function_name=function_name, error=str(e))
        
        logger.info("Deployment completed", results=results)
        return results


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy API Lambda functions')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--role-arn', help='IAM role ARN for Lambda execution')
    parser.add_argument('--s3-bucket', help='S3 bucket for deployment packages')
    parser.add_argument('--api-gateway-id', help='API Gateway ID for permissions')
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    try:
        deployer = LambdaDeployer(
            region=args.region,
            role_arn=args.role_arn,
            s3_bucket=args.s3_bucket
        )
        
        results = deployer.deploy_all(api_gateway_id=args.api_gateway_id)
        
        # Print summary
        print("\n" + "="*80)
        print("DEPLOYMENT SUMMARY")
        print("="*80)
        
        for function_name, result in results.items():
            status = result['status']
            print(f"\n{function_name}: {status.upper()}")
            
            if status == 'success':
                print(f"  Function Name: {result['function_name']}")
                print(f"  Function ARN: {result['function_arn']}")
            else:
                print(f"  Error: {result['error']}")
        
        print("\n" + "="*80)
        
        # Exit with error if any deployment failed
        if any(r['status'] == 'failed' for r in results.values()):
            sys.exit(1)
        
    except Exception as e:
        logger.error("Deployment failed", error=str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
