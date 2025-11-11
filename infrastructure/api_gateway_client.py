"""
AWS API Gateway client for managing Concert AI Platform API.

Provides programmatic access to create, configure, and manage API Gateway
resources including REST APIs, resources, methods, and deployments.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


class APIGatewayClient:
    """Client for managing AWS API Gateway resources."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize API Gateway client.
        
        Args:
            region: AWS region
        """
        self.region = region
        self.client = boto3.client('apigateway', region_name=region)
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    def create_rest_api(
        self,
        name: str,
        description: str = "",
        endpoint_type: str = "REGIONAL"
    ) -> Dict[str, Any]:
        """
        Create a new REST API.
        
        Args:
            name: API name
            description: API description
            endpoint_type: Endpoint configuration type (REGIONAL, EDGE, PRIVATE)
            
        Returns:
            API details including API ID
        """
        try:
            response = self.client.create_rest_api(
                name=name,
                description=description,
                endpointConfiguration={'types': [endpoint_type]}
            )
            
            self.logger.info(
                "Created REST API",
                api_id=response['id'],
                name=name
            )
            
            return response
        
        except ClientError as e:
            self.logger.error("Failed to create REST API", error=str(e))
            raise
    
    def get_rest_api(self, api_id: str) -> Optional[Dict[str, Any]]:
        """
        Get REST API details.
        
        Args:
            api_id: API Gateway REST API ID
            
        Returns:
            API details or None if not found
        """
        try:
            response = self.client.get_rest_api(restApiId=api_id)
            return response
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                return None
            self.logger.error("Failed to get REST API", api_id=api_id, error=str(e))
            raise
    
    def list_rest_apis(self) -> List[Dict[str, Any]]:
        """
        List all REST APIs.
        
        Returns:
            List of REST APIs
        """
        try:
            response = self.client.get_rest_apis()
            return response.get('items', [])
        
        except ClientError as e:
            self.logger.error("Failed to list REST APIs", error=str(e))
            raise
    
    def create_resource(
        self,
        api_id: str,
        parent_id: str,
        path_part: str
    ) -> Dict[str, Any]:
        """
        Create a resource under a parent resource.
        
        Args:
            api_id: API Gateway REST API ID
            parent_id: Parent resource ID
            path_part: Path part for the resource
            
        Returns:
            Resource details including resource ID
        """
        try:
            response = self.client.create_resource(
                restApiId=api_id,
                parentId=parent_id,
                pathPart=path_part
            )
            
            self.logger.info(
                "Created resource",
                api_id=api_id,
                resource_id=response['id'],
                path=path_part
            )
            
            return response
        
        except ClientError as e:
            self.logger.error(
                "Failed to create resource",
                api_id=api_id,
                path=path_part,
                error=str(e)
            )
            raise
    
    def get_resources(self, api_id: str) -> List[Dict[str, Any]]:
        """
        Get all resources for an API.
        
        Args:
            api_id: API Gateway REST API ID
            
        Returns:
            List of resources
        """
        try:
            response = self.client.get_resources(restApiId=api_id)
            return response.get('items', [])
        
        except ClientError as e:
            self.logger.error("Failed to get resources", api_id=api_id, error=str(e))
            raise
    
    def create_method(
        self,
        api_id: str,
        resource_id: str,
        http_method: str,
        authorization_type: str = "NONE",
        api_key_required: bool = False,
        request_parameters: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Create a method on a resource.
        
        Args:
            api_id: API Gateway REST API ID
            resource_id: Resource ID
            http_method: HTTP method (GET, POST, PUT, DELETE, etc.)
            authorization_type: Authorization type (NONE, AWS_IAM, CUSTOM, etc.)
            api_key_required: Whether API key is required
            request_parameters: Request parameters configuration
            
        Returns:
            Method details
        """
        try:
            params = {
                'restApiId': api_id,
                'resourceId': resource_id,
                'httpMethod': http_method,
                'authorizationType': authorization_type,
                'apiKeyRequired': api_key_required
            }
            
            if request_parameters:
                params['requestParameters'] = request_parameters
            
            response = self.client.put_method(**params)
            
            self.logger.info(
                "Created method",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method
            )
            
            return response
        
        except ClientError as e:
            self.logger.error(
                "Failed to create method",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method,
                error=str(e)
            )
            raise
    
    def create_integration(
        self,
        api_id: str,
        resource_id: str,
        http_method: str,
        integration_type: str,
        integration_http_method: Optional[str] = None,
        uri: Optional[str] = None,
        request_templates: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create an integration for a method.
        
        Args:
            api_id: API Gateway REST API ID
            resource_id: Resource ID
            http_method: HTTP method
            integration_type: Integration type (AWS, AWS_PROXY, HTTP, HTTP_PROXY, MOCK)
            integration_http_method: HTTP method for integration
            uri: Integration URI (Lambda ARN, HTTP endpoint, etc.)
            request_templates: Request templates for transformation
            
        Returns:
            Integration details
        """
        try:
            params = {
                'restApiId': api_id,
                'resourceId': resource_id,
                'httpMethod': http_method,
                'type': integration_type
            }
            
            if integration_http_method:
                params['integrationHttpMethod'] = integration_http_method
            
            if uri:
                params['uri'] = uri
            
            if request_templates:
                params['requestTemplates'] = request_templates
            
            response = self.client.put_integration(**params)
            
            self.logger.info(
                "Created integration",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method,
                type=integration_type
            )
            
            return response
        
        except ClientError as e:
            self.logger.error(
                "Failed to create integration",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method,
                error=str(e)
            )
            raise
    
    def create_method_response(
        self,
        api_id: str,
        resource_id: str,
        http_method: str,
        status_code: str,
        response_parameters: Optional[Dict[str, bool]] = None,
        response_models: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a method response.
        
        Args:
            api_id: API Gateway REST API ID
            resource_id: Resource ID
            http_method: HTTP method
            status_code: HTTP status code
            response_parameters: Response parameters (headers)
            response_models: Response models
            
        Returns:
            Method response details
        """
        try:
            params = {
                'restApiId': api_id,
                'resourceId': resource_id,
                'httpMethod': http_method,
                'statusCode': status_code
            }
            
            if response_parameters:
                params['responseParameters'] = response_parameters
            
            if response_models:
                params['responseModels'] = response_models
            
            response = self.client.put_method_response(**params)
            
            self.logger.info(
                "Created method response",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method,
                status_code=status_code
            )
            
            return response
        
        except ClientError as e:
            self.logger.error(
                "Failed to create method response",
                api_id=api_id,
                resource_id=resource_id,
                method=http_method,
                status_code=status_code,
                error=str(e)
            )
            raise
    
    def enable_cors(
        self,
        api_id: str,
        resource_id: str,
        allowed_origins: str = "'*'",
        allowed_methods: str = "'GET,POST,PUT,DELETE,OPTIONS'",
        allowed_headers: str = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    ) -> Dict[str, Any]:
        """
        Enable CORS for a resource by creating OPTIONS method.
        
        Args:
            api_id: API Gateway REST API ID
            resource_id: Resource ID
            allowed_origins: Allowed origins
            allowed_methods: Allowed HTTP methods
            allowed_headers: Allowed headers
            
        Returns:
            OPTIONS method details
        """
        try:
            # Create OPTIONS method
            self.create_method(
                api_id=api_id,
                resource_id=resource_id,
                http_method='OPTIONS',
                authorization_type='NONE'
            )
            
            # Create MOCK integration
            self.create_integration(
                api_id=api_id,
                resource_id=resource_id,
                http_method='OPTIONS',
                integration_type='MOCK',
                request_templates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Create integration response
            self.client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': allowed_headers,
                    'method.response.header.Access-Control-Allow-Methods': allowed_methods,
                    'method.response.header.Access-Control-Allow-Origin': allowed_origins
                },
                responseTemplates={
                    'application/json': ''
                }
            )
            
            # Create method response
            self.create_method_response(
                api_id=api_id,
                resource_id=resource_id,
                http_method='OPTIONS',
                status_code='200',
                response_parameters={
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            
            self.logger.info(
                "Enabled CORS",
                api_id=api_id,
                resource_id=resource_id
            )
            
            return {'message': 'CORS enabled successfully'}
        
        except ClientError as e:
            self.logger.error(
                "Failed to enable CORS",
                api_id=api_id,
                resource_id=resource_id,
                error=str(e)
            )
            raise
    
    def create_deployment(
        self,
        api_id: str,
        stage_name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a deployment.
        
        Args:
            api_id: API Gateway REST API ID
            stage_name: Stage name
            description: Deployment description
            
        Returns:
            Deployment details
        """
        try:
            response = self.client.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=description or f"Deployment to {stage_name}"
            )
            
            self.logger.info(
                "Created deployment",
                api_id=api_id,
                stage=stage_name,
                deployment_id=response['id']
            )
            
            return response
        
        except ClientError as e:
            self.logger.error(
                "Failed to create deployment",
                api_id=api_id,
                stage=stage_name,
                error=str(e)
            )
            raise
    
    def create_usage_plan(
        self,
        name: str,
        description: str = "",
        throttle_burst_limit: int = 1000,
        throttle_rate_limit: float = 500.0,
        quota_limit: int = 100000,
        quota_period: str = "DAY"
    ) -> Dict[str, Any]:
        """
        Create a usage plan for throttling and rate limiting.
        
        Args:
            name: Usage plan name
            description: Usage plan description
            throttle_burst_limit: Burst limit
            throttle_rate_limit: Rate limit (requests per second)
            quota_limit: Quota limit
            quota_period: Quota period (DAY, WEEK, MONTH)
            
        Returns:
            Usage plan details
        """
        try:
            response = self.client.create_usage_plan(
                name=name,
                description=description,
                throttle={
                    'burstLimit': throttle_burst_limit,
                    'rateLimit': throttle_rate_limit
                },
                quota={
                    'limit': quota_limit,
                    'period': quota_period
                }
            )
            
            self.logger.info(
                "Created usage plan",
                usage_plan_id=response['id'],
                name=name
            )
            
            return response
        
        except ClientError as e:
            self.logger.error("Failed to create usage plan", name=name, error=str(e))
            raise
    
    def create_api_key(
        self,
        name: str,
        description: str = "",
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Create an API key.
        
        Args:
            name: API key name
            description: API key description
            enabled: Whether the key is enabled
            
        Returns:
            API key details including key value
        """
        try:
            response = self.client.create_api_key(
                name=name,
                description=description,
                enabled=enabled
            )
            
            self.logger.info(
                "Created API key",
                api_key_id=response['id'],
                name=name
            )
            
            return response
        
        except ClientError as e:
            self.logger.error("Failed to create API key", name=name, error=str(e))
            raise
    
    def get_api_endpoint(self, api_id: str, stage_name: str) -> str:
        """
        Get the API endpoint URL.
        
        Args:
            api_id: API Gateway REST API ID
            stage_name: Stage name
            
        Returns:
            API endpoint URL
        """
        return f"https://{api_id}.execute-api.{self.region}.amazonaws.com/{stage_name}"
    
    def delete_rest_api(self, api_id: str) -> bool:
        """
        Delete a REST API.
        
        Args:
            api_id: API Gateway REST API ID
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_rest_api(restApiId=api_id)
            self.logger.info("Deleted REST API", api_id=api_id)
            return True
        
        except ClientError as e:
            self.logger.error("Failed to delete REST API", api_id=api_id, error=str(e))
            raise
