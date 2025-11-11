"""
Setup script for AWS API Gateway configuration.

Creates and configures API Gateway REST API with all required routes,
CORS settings, throttling, and Lambda integrations.
"""
import os
import sys
import json
import argparse
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.api_gateway_client import APIGatewayClient
from src.config.settings import Settings


class APIGatewaySetup:
    """Setup and configure API Gateway for Concert AI Platform."""
    
    def __init__(
        self,
        environment: str = "development",
        region: str = "us-east-1"
    ):
        """
        Initialize API Gateway setup.
        
        Args:
            environment: Environment name (development, staging, production)
            region: AWS region
        """
        self.environment = environment
        self.region = region
        self.client = APIGatewayClient(region=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        # API configuration
        self.api_name = f"concert-ai-api-{environment}"
        self.api_description = "REST API for Concert AI Platform"
        
        # Store created resources
        self.api_id: Optional[str] = None
        self.root_resource_id: Optional[str] = None
        self.resources: Dict[str, str] = {}
    
    def find_lambda_function(self, function_name_pattern: str) -> Optional[str]:
        """
        Find Lambda function ARN by name pattern.
        
        Args:
            function_name_pattern: Function name or pattern
            
        Returns:
            Function ARN or None if not found
        """
        try:
            response = self.lambda_client.list_functions()
            
            for function in response.get('Functions', []):
                if function_name_pattern in function['FunctionName']:
                    return function['FunctionArn']
            
            return None
        
        except ClientError as e:
            print(f"Error finding Lambda function: {e}")
            return None
    
    def create_api(self) -> str:
        """
        Create REST API.
        
        Returns:
            API ID
        """
        print(f"Creating REST API: {self.api_name}")
        
        # Check if API already exists
        apis = self.client.list_rest_apis()
        for api in apis:
            if api['name'] == self.api_name:
                print(f"API already exists: {api['id']}")
                self.api_id = api['id']
                
                # Get root resource
                resources = self.client.get_resources(self.api_id)
                for resource in resources:
                    if resource['path'] == '/':
                        self.root_resource_id = resource['id']
                        break
                
                return self.api_id
        
        # Create new API
        api = self.client.create_rest_api(
            name=self.api_name,
            description=self.api_description,
            endpoint_type="REGIONAL"
        )
        
        self.api_id = api['id']
        self.root_resource_id = api.get('rootResourceId')
        
        # If root resource ID not in response, get it from resources
        if not self.root_resource_id:
            resources = self.client.get_resources(self.api_id)
            for resource in resources:
                if resource['path'] == '/':
                    self.root_resource_id = resource['id']
                    break
        
        print(f"Created API: {self.api_id}")
        return self.api_id
    
    def create_resource_path(self, path_parts: List[str]) -> str:
        """
        Create a resource path (e.g., /chat, /history/{session_id}).
        
        Args:
            path_parts: List of path parts
            
        Returns:
            Resource ID of the final path part
        """
        parent_id = self.root_resource_id
        
        for part in path_parts:
            # Check if resource already exists
            resources = self.client.get_resources(self.api_id)
            existing_resource = None
            
            for resource in resources:
                if resource.get('parentId') == parent_id and resource.get('pathPart') == part:
                    existing_resource = resource
                    break
            
            if existing_resource:
                parent_id = existing_resource['id']
                print(f"Resource already exists: /{part} ({parent_id})")
            else:
                # Create new resource
                resource = self.client.create_resource(
                    api_id=self.api_id,
                    parent_id=parent_id,
                    path_part=part
                )
                parent_id = resource['id']
                print(f"Created resource: /{part} ({parent_id})")
        
        return parent_id
    
    def setup_chatbot_endpoints(self, lambda_arn: Optional[str] = None):
        """
        Set up chatbot endpoints (/chat, /history/{session_id}).
        
        Args:
            lambda_arn: Lambda function ARN for chatbot
        """
        print("\n=== Setting up Chatbot Endpoints ===")
        
        if not lambda_arn:
            lambda_arn = self.find_lambda_function("chatbot")
            if not lambda_arn:
                print("Warning: Chatbot Lambda function not found. Using placeholder ARN.")
                lambda_arn = f"arn:aws:lambda:{self.region}:123456789012:function:chatbot-handler"
        
        # Create /chat endpoint
        chat_resource_id = self.create_resource_path(['chat'])
        self.resources['chat'] = chat_resource_id
        
        # POST /chat
        self.client.create_method(
            api_id=self.api_id,
            resource_id=chat_resource_id,
            http_method='POST',
            authorization_type='NONE'
        )
        
        integration_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        self.client.create_integration(
            api_id=self.api_id,
            resource_id=chat_resource_id,
            http_method='POST',
            integration_type='AWS_PROXY',
            integration_http_method='POST',
            uri=integration_uri
        )
        
        self.client.create_method_response(
            api_id=self.api_id,
            resource_id=chat_resource_id,
            http_method='POST',
            status_code='200',
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        # Enable CORS for /chat
        self.client.enable_cors(
            api_id=self.api_id,
            resource_id=chat_resource_id,
            allowed_methods="'POST,OPTIONS'"
        )
        
        print("Created POST /chat endpoint")
        
        # Create /history/{session_id} endpoint
        history_resource_id = self.create_resource_path(['history', '{session_id}'])
        self.resources['history'] = history_resource_id
        
        # GET /history/{session_id}
        self.client.create_method(
            api_id=self.api_id,
            resource_id=history_resource_id,
            http_method='GET',
            authorization_type='NONE',
            request_parameters={
                'method.request.path.session_id': True
            }
        )
        
        self.client.create_integration(
            api_id=self.api_id,
            resource_id=history_resource_id,
            http_method='GET',
            integration_type='AWS_PROXY',
            integration_http_method='POST',
            uri=integration_uri
        )
        
        self.client.create_method_response(
            api_id=self.api_id,
            resource_id=history_resource_id,
            http_method='GET',
            status_code='200',
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        # Enable CORS for /history/{session_id}
        self.client.enable_cors(
            api_id=self.api_id,
            resource_id=history_resource_id,
            allowed_methods="'GET,DELETE,OPTIONS'"
        )
        
        print("Created GET /history/{session_id} endpoint")
    
    def setup_analytics_endpoints(
        self,
        venue_lambda_arn: Optional[str] = None,
        prediction_lambda_arn: Optional[str] = None,
        recommendation_lambda_arn: Optional[str] = None
    ):
        """
        Set up analytics endpoints (/venues, /predictions, /recommendations).
        
        Args:
            venue_lambda_arn: Lambda ARN for venue popularity
            prediction_lambda_arn: Lambda ARN for ticket predictions
            recommendation_lambda_arn: Lambda ARN for recommendations
        """
        print("\n=== Setting up Analytics Endpoints ===")
        
        # Find Lambda functions if not provided
        if not venue_lambda_arn:
            venue_lambda_arn = self.find_lambda_function("venue-popularity")
            if not venue_lambda_arn:
                print("Warning: Venue popularity Lambda not found. Using placeholder.")
                venue_lambda_arn = f"arn:aws:lambda:{self.region}:123456789012:function:venue-popularity"
        
        if not prediction_lambda_arn:
            prediction_lambda_arn = self.find_lambda_function("ticket-prediction")
            if not prediction_lambda_arn:
                print("Warning: Ticket prediction Lambda not found. Using placeholder.")
                prediction_lambda_arn = f"arn:aws:lambda:{self.region}:123456789012:function:ticket-prediction"
        
        if not recommendation_lambda_arn:
            recommendation_lambda_arn = self.find_lambda_function("recommendation")
            if not recommendation_lambda_arn:
                print("Warning: Recommendation Lambda not found. Using placeholder.")
                recommendation_lambda_arn = f"arn:aws:lambda:{self.region}:123456789012:function:recommendation"
        
        # Create /venues/popularity endpoint
        venues_resource_id = self.create_resource_path(['venues', 'popularity'])
        self.resources['venues'] = venues_resource_id
        
        self.client.create_method(
            api_id=self.api_id,
            resource_id=venues_resource_id,
            http_method='GET',
            authorization_type='NONE'
        )
        
        venue_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{venue_lambda_arn}/invocations"
        
        self.client.create_integration(
            api_id=self.api_id,
            resource_id=venues_resource_id,
            http_method='GET',
            integration_type='AWS_PROXY',
            integration_http_method='POST',
            uri=venue_uri
        )
        
        self.client.create_method_response(
            api_id=self.api_id,
            resource_id=venues_resource_id,
            http_method='GET',
            status_code='200',
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        self.client.enable_cors(
            api_id=self.api_id,
            resource_id=venues_resource_id,
            allowed_methods="'GET,OPTIONS'"
        )
        
        print("Created GET /venues/popularity endpoint")
        
        # Create /predictions/tickets endpoint
        predictions_resource_id = self.create_resource_path(['predictions', 'tickets'])
        self.resources['predictions'] = predictions_resource_id
        
        self.client.create_method(
            api_id=self.api_id,
            resource_id=predictions_resource_id,
            http_method='POST',
            authorization_type='NONE'
        )
        
        prediction_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{prediction_lambda_arn}/invocations"
        
        self.client.create_integration(
            api_id=self.api_id,
            resource_id=predictions_resource_id,
            http_method='POST',
            integration_type='AWS_PROXY',
            integration_http_method='POST',
            uri=prediction_uri
        )
        
        self.client.create_method_response(
            api_id=self.api_id,
            resource_id=predictions_resource_id,
            http_method='POST',
            status_code='200',
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        self.client.enable_cors(
            api_id=self.api_id,
            resource_id=predictions_resource_id,
            allowed_methods="'POST,OPTIONS'"
        )
        
        print("Created POST /predictions/tickets endpoint")
        
        # Create /recommendations endpoint
        recommendations_resource_id = self.create_resource_path(['recommendations'])
        self.resources['recommendations'] = recommendations_resource_id
        
        self.client.create_method(
            api_id=self.api_id,
            resource_id=recommendations_resource_id,
            http_method='GET',
            authorization_type='NONE'
        )
        
        recommendation_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{recommendation_lambda_arn}/invocations"
        
        self.client.create_integration(
            api_id=self.api_id,
            resource_id=recommendations_resource_id,
            http_method='GET',
            integration_type='AWS_PROXY',
            integration_http_method='POST',
            uri=recommendation_uri
        )
        
        self.client.create_method_response(
            api_id=self.api_id,
            resource_id=recommendations_resource_id,
            http_method='GET',
            status_code='200',
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        self.client.enable_cors(
            api_id=self.api_id,
            resource_id=recommendations_resource_id,
            allowed_methods="'GET,POST,OPTIONS'"
        )
        
        print("Created GET /recommendations endpoint")
    
    def create_usage_plan_and_throttling(self):
        """Create usage plan with throttling and rate limiting."""
        print("\n=== Setting up Usage Plan and Throttling ===")
        
        usage_plan_name = f"concert-ai-usage-plan-{self.environment}"
        
        try:
            usage_plan = self.client.create_usage_plan(
                name=usage_plan_name,
                description=f"Usage plan for Concert AI API ({self.environment})",
                throttle_burst_limit=1000,
                throttle_rate_limit=500.0,
                quota_limit=100000,
                quota_period="DAY"
            )
            
            print(f"Created usage plan: {usage_plan['id']}")
            
            # Create API key
            api_key_name = f"concert-ai-api-key-{self.environment}"
            api_key = self.client.create_api_key(
                name=api_key_name,
                description=f"API key for Concert AI Platform ({self.environment})",
                enabled=True
            )
            
            print(f"Created API key: {api_key['id']}")
            print(f"API key value: {api_key.get('value', 'N/A')}")
            
            return usage_plan, api_key
        
        except ClientError as e:
            print(f"Error creating usage plan: {e}")
            return None, None
    
    def deploy_api(self, stage_name: Optional[str] = None):
        """
        Deploy API to a stage.
        
        Args:
            stage_name: Stage name (defaults to environment)
        """
        if not stage_name:
            stage_name = self.environment
        
        print(f"\n=== Deploying API to stage: {stage_name} ===")
        
        deployment = self.client.create_deployment(
            api_id=self.api_id,
            stage_name=stage_name,
            description=f"Deployment to {stage_name} environment"
        )
        
        print(f"Deployment created: {deployment['id']}")
        
        # Get API endpoint
        endpoint = self.client.get_api_endpoint(self.api_id, stage_name)
        print(f"\nAPI Endpoint: {endpoint}")
        
        return endpoint
    
    def setup_complete_api(self):
        """Run complete API Gateway setup."""
        print("=" * 60)
        print("AWS API Gateway Setup for Concert AI Platform")
        print("=" * 60)
        
        # Create API
        self.create_api()
        
        # Setup endpoints
        self.setup_chatbot_endpoints()
        self.setup_analytics_endpoints()
        
        # Create usage plan and throttling
        self.create_usage_plan_and_throttling()
        
        # Deploy API
        endpoint = self.deploy_api()
        
        print("\n" + "=" * 60)
        print("API Gateway Setup Complete!")
        print("=" * 60)
        print(f"API ID: {self.api_id}")
        print(f"API Endpoint: {endpoint}")
        print(f"Environment: {self.environment}")
        print(f"Region: {self.region}")
        print("\nEndpoints configured:")
        print(f"  - POST {endpoint}/chat")
        print(f"  - GET  {endpoint}/history/{{session_id}}")
        print(f"  - GET  {endpoint}/venues/popularity")
        print(f"  - POST {endpoint}/predictions/tickets")
        print(f"  - GET  {endpoint}/recommendations")
        print("\nCORS enabled for all endpoints")
        print("Throttling: 500 requests/sec, burst 1000")
        print("Quota: 100,000 requests/day")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AWS API Gateway for Concert AI Platform"
    )
    parser.add_argument(
        '--environment',
        type=str,
        default='development',
        choices=['development', 'staging', 'production'],
        help='Environment name'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region'
    )
    
    args = parser.parse_args()
    
    # Run setup
    setup = APIGatewaySetup(
        environment=args.environment,
        region=args.region
    )
    
    setup.setup_complete_api()


if __name__ == "__main__":
    main()
