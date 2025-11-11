"""
Validation script for API Gateway setup.

Verifies that API Gateway is properly configured with all required
endpoints, CORS settings, throttling, and Lambda integrations.
"""
import os
import sys
import json
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from infrastructure.api_gateway_client import APIGatewayClient


class APIGatewayValidator:
    """Validator for API Gateway configuration."""
    
    def __init__(self, api_name: str = "concert-ai-api", region: str = "us-east-1"):
        """
        Initialize validator.
        
        Args:
            api_name: API Gateway name pattern
            region: AWS region
        """
        self.api_name = api_name
        self.region = region
        self.client = APIGatewayClient(region=region)
        self.api_id: Optional[str] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def find_api(self) -> bool:
        """
        Find API Gateway by name.
        
        Returns:
            True if found, False otherwise
        """
        print(f"Looking for API Gateway: {self.api_name}*")
        
        try:
            apis = self.client.list_rest_apis()
            
            for api in apis:
                if self.api_name in api['name']:
                    self.api_id = api['id']
                    print(f"✓ Found API: {api['name']} (ID: {self.api_id})")
                    return True
            
            self.errors.append(f"API Gateway not found with name pattern: {self.api_name}")
            return False
        
        except Exception as e:
            self.errors.append(f"Error finding API: {str(e)}")
            return False
    
    def validate_resources(self) -> bool:
        """
        Validate that all required resources exist.
        
        Returns:
            True if all resources exist
        """
        print("\nValidating API resources...")
        
        required_paths = [
            '/chat',
            '/history/{session_id}',
            '/venues/popularity',
            '/predictions/tickets',
            '/recommendations'
        ]
        
        try:
            resources = self.client.get_resources(self.api_id)
            
            # Build path map
            path_map = {resource['path']: resource for resource in resources}
            
            all_found = True
            for path in required_paths:
                if path in path_map:
                    print(f"✓ Resource exists: {path}")
                else:
                    self.errors.append(f"Missing resource: {path}")
                    all_found = False
            
            return all_found
        
        except Exception as e:
            self.errors.append(f"Error validating resources: {str(e)}")
            return False
    
    def validate_methods(self) -> bool:
        """
        Validate that all required methods exist.
        
        Returns:
            True if all methods exist
        """
        print("\nValidating API methods...")
        
        required_methods = [
            ('/chat', 'POST'),
            ('/chat', 'OPTIONS'),
            ('/history/{session_id}', 'GET'),
            ('/history/{session_id}', 'OPTIONS'),
            ('/venues/popularity', 'GET'),
            ('/venues/popularity', 'OPTIONS'),
            ('/predictions/tickets', 'POST'),
            ('/predictions/tickets', 'OPTIONS'),
            ('/recommendations', 'GET'),
            ('/recommendations', 'OPTIONS')
        ]
        
        try:
            resources = self.client.get_resources(self.api_id)
            path_map = {resource['path']: resource for resource in resources}
            
            all_found = True
            for path, method in required_methods:
                if path in path_map:
                    resource = path_map[path]
                    resource_methods = resource.get('resourceMethods', {})
                    
                    if method in resource_methods:
                        print(f"✓ Method exists: {method} {path}")
                    else:
                        self.errors.append(f"Missing method: {method} {path}")
                        all_found = False
                else:
                    self.errors.append(f"Resource not found for method: {method} {path}")
                    all_found = False
            
            return all_found
        
        except Exception as e:
            self.errors.append(f"Error validating methods: {str(e)}")
            return False
    
    def validate_cors(self) -> bool:
        """
        Validate CORS configuration.
        
        Returns:
            True if CORS is properly configured
        """
        print("\nValidating CORS configuration...")
        
        cors_paths = [
            '/chat',
            '/history/{session_id}',
            '/venues/popularity',
            '/predictions/tickets',
            '/recommendations'
        ]
        
        try:
            resources = self.client.get_resources(self.api_id)
            path_map = {resource['path']: resource for resource in resources}
            
            all_valid = True
            for path in cors_paths:
                if path in path_map:
                    resource = path_map[path]
                    resource_methods = resource.get('resourceMethods', {})
                    
                    if 'OPTIONS' in resource_methods:
                        print(f"✓ CORS enabled: {path}")
                    else:
                        self.warnings.append(f"CORS not enabled (no OPTIONS method): {path}")
                        all_valid = False
                else:
                    self.warnings.append(f"Resource not found for CORS check: {path}")
                    all_valid = False
            
            return all_valid
        
        except Exception as e:
            self.errors.append(f"Error validating CORS: {str(e)}")
            return False
    
    def validate_integrations(self) -> bool:
        """
        Validate Lambda integrations.
        
        Returns:
            True if integrations are configured
        """
        print("\nValidating Lambda integrations...")
        
        integration_methods = [
            ('/chat', 'POST'),
            ('/history/{session_id}', 'GET'),
            ('/venues/popularity', 'GET'),
            ('/predictions/tickets', 'POST'),
            ('/recommendations', 'GET')
        ]
        
        try:
            resources = self.client.get_resources(self.api_id)
            path_map = {resource['path']: resource for resource in resources}
            
            all_valid = True
            for path, method in integration_methods:
                if path in path_map:
                    resource = path_map[path]
                    resource_id = resource['id']
                    
                    try:
                        # Get method integration
                        response = self.client.client.get_integration(
                            restApiId=self.api_id,
                            resourceId=resource_id,
                            httpMethod=method
                        )
                        
                        integration_type = response.get('type')
                        if integration_type in ['AWS_PROXY', 'AWS']:
                            print(f"✓ Integration configured: {method} {path} ({integration_type})")
                        else:
                            self.warnings.append(
                                f"Unexpected integration type: {method} {path} ({integration_type})"
                            )
                    
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NotFoundException':
                            self.errors.append(f"Integration not found: {method} {path}")
                            all_valid = False
                        else:
                            raise
                else:
                    self.errors.append(f"Resource not found for integration: {method} {path}")
                    all_valid = False
            
            return all_valid
        
        except Exception as e:
            self.errors.append(f"Error validating integrations: {str(e)}")
            return False
    
    def validate_deployment(self) -> bool:
        """
        Validate API deployment.
        
        Returns:
            True if API is deployed
        """
        print("\nValidating API deployment...")
        
        try:
            # Get stages
            response = self.client.client.get_stages(restApiId=self.api_id)
            stages = response.get('item', [])
            
            if stages:
                for stage in stages:
                    stage_name = stage['stageName']
                    print(f"✓ Deployed to stage: {stage_name}")
                    
                    # Get endpoint URL
                    endpoint = self.client.get_api_endpoint(self.api_id, stage_name)
                    print(f"  Endpoint: {endpoint}")
                
                return True
            else:
                self.errors.append("API not deployed to any stage")
                return False
        
        except Exception as e:
            self.errors.append(f"Error validating deployment: {str(e)}")
            return False
    
    def validate_throttling(self) -> bool:
        """
        Validate throttling and usage plan configuration.
        
        Returns:
            True if throttling is configured
        """
        print("\nValidating throttling and usage plans...")
        
        try:
            # Get usage plans
            response = self.client.client.get_usage_plans()
            usage_plans = response.get('items', [])
            
            # Find usage plan for this API
            api_usage_plans = [
                plan for plan in usage_plans
                if any(
                    stage.get('apiId') == self.api_id
                    for stage in plan.get('apiStages', [])
                )
            ]
            
            if api_usage_plans:
                for plan in api_usage_plans:
                    print(f"✓ Usage plan: {plan['name']}")
                    
                    throttle = plan.get('throttle', {})
                    print(f"  Burst limit: {throttle.get('burstLimit', 'N/A')}")
                    print(f"  Rate limit: {throttle.get('rateLimit', 'N/A')}")
                    
                    quota = plan.get('quota', {})
                    if quota:
                        print(f"  Quota: {quota.get('limit', 'N/A')} per {quota.get('period', 'N/A')}")
                
                return True
            else:
                self.warnings.append("No usage plan configured for this API")
                return False
        
        except Exception as e:
            self.warnings.append(f"Error validating throttling: {str(e)}")
            return False
    
    def run_validation(self) -> bool:
        """
        Run complete validation.
        
        Returns:
            True if all validations pass
        """
        print("=" * 60)
        print("API Gateway Configuration Validation")
        print("=" * 60)
        
        # Find API
        if not self.find_api():
            self.print_results()
            return False
        
        # Run validations
        validations = [
            self.validate_resources(),
            self.validate_methods(),
            self.validate_cors(),
            self.validate_integrations(),
            self.validate_deployment(),
            self.validate_throttling()
        ]
        
        # Print results
        self.print_results()
        
        return all(validations) and not self.errors
    
    def print_results(self):
        """Print validation results."""
        print("\n" + "=" * 60)
        print("Validation Results")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print("\n✅ Validation passed with warnings")
        else:
            print("\n❌ Validation failed")
        
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate API Gateway configuration"
    )
    parser.add_argument(
        '--api-name',
        type=str,
        default='concert-ai-api',
        help='API Gateway name pattern'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = APIGatewayValidator(
        api_name=args.api_name,
        region=args.region
    )
    
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
