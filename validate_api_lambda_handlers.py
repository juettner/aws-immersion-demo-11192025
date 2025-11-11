"""
Validation script for API Lambda handlers.

This script validates the Lambda handler implementations for correctness,
structure, and integration with AWS services.
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class LambdaHandlerValidator:
    """Validator for Lambda handler implementations."""
    
    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
    
    def validate_file_structure(self) -> bool:
        """Validate that required files exist."""
        logger.info("Validating file structure")
        
        required_files = [
            'src/infrastructure/api_lambda_handlers.py',
            'infrastructure/deploy_api_lambdas.py',
            'infrastructure/deploy_api_lambdas.sh'
        ]
        
        all_exist = True
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                self.successes.append(f"✓ Found {file_path}")
            else:
                self.errors.append(f"✗ Missing {file_path}")
                all_exist = False
        
        return all_exist
    
    def validate_handler_imports(self) -> bool:
        """Validate that handler file has correct imports."""
        logger.info("Validating handler imports")
        
        try:
            # Add src to path
            sys.path.insert(0, str(Path.cwd()))
            
            from src.infrastructure import api_lambda_handlers
            
            required_functions = [
                'chatbot_handler',
                'venue_popularity_handler',
                'ticket_prediction_handler',
                'recommendations_handler',
                'health_check_handler',
                'create_response',
                'create_error_response',
                'parse_request_body'
            ]
            
            all_present = True
            for func_name in required_functions:
                if hasattr(api_lambda_handlers, func_name):
                    self.successes.append(f"✓ Found handler: {func_name}")
                else:
                    self.errors.append(f"✗ Missing handler: {func_name}")
                    all_present = False
            
            return all_present
            
        except ImportError as e:
            self.errors.append(f"✗ Failed to import handlers: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"✗ Unexpected error during import: {str(e)}")
            return False
    
    def validate_handler_signatures(self) -> bool:
        """Validate that handlers have correct signatures."""
        logger.info("Validating handler signatures")
        
        try:
            from src.infrastructure import api_lambda_handlers
            import inspect
            
            handlers = [
                'chatbot_handler',
                'venue_popularity_handler',
                'ticket_prediction_handler',
                'recommendations_handler',
                'health_check_handler'
            ]
            
            all_valid = True
            for handler_name in handlers:
                handler = getattr(api_lambda_handlers, handler_name)
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                
                # Lambda handlers should accept (event, context)
                if params == ['event', 'context']:
                    self.successes.append(f"✓ {handler_name} has correct signature")
                else:
                    self.errors.append(
                        f"✗ {handler_name} has incorrect signature: {params}"
                    )
                    all_valid = False
            
            return all_valid
            
        except Exception as e:
            self.errors.append(f"✗ Failed to validate signatures: {str(e)}")
            return False
    
    def test_response_creation(self) -> bool:
        """Test response creation functions."""
        logger.info("Testing response creation")
        
        try:
            from src.infrastructure.api_lambda_handlers import (
                create_response,
                create_error_response
            )
            
            # Test successful response
            response = create_response(200, {'message': 'test'})
            
            if response['statusCode'] == 200:
                self.successes.append("✓ create_response works correctly")
            else:
                self.errors.append("✗ create_response returned wrong status code")
                return False
            
            if 'Access-Control-Allow-Origin' in response['headers']:
                self.successes.append("✓ CORS headers present")
            else:
                self.warnings.append("⚠ CORS headers missing")
            
            # Test error response
            error_response = create_error_response(400, "Test error")
            
            if error_response['statusCode'] == 400:
                self.successes.append("✓ create_error_response works correctly")
            else:
                self.errors.append("✗ create_error_response returned wrong status code")
                return False
            
            body = json.loads(error_response['body'])
            if 'error' in body and 'timestamp' in body:
                self.successes.append("✓ Error response has correct structure")
            else:
                self.errors.append("✗ Error response missing required fields")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"✗ Response creation test failed: {str(e)}")
            return False
    
    def test_request_parsing(self) -> bool:
        """Test request body parsing."""
        logger.info("Testing request parsing")
        
        try:
            from src.infrastructure.api_lambda_handlers import parse_request_body
            
            # Test with JSON string
            event1 = {'body': '{"message": "test"}'}
            result1 = parse_request_body(event1)
            
            if result1 and result1.get('message') == 'test':
                self.successes.append("✓ JSON string parsing works")
            else:
                self.errors.append("✗ JSON string parsing failed")
                return False
            
            # Test with dict
            event2 = {'body': {'message': 'test'}}
            result2 = parse_request_body(event2)
            
            if result2 and result2.get('message') == 'test':
                self.successes.append("✓ Dict parsing works")
            else:
                self.errors.append("✗ Dict parsing failed")
                return False
            
            # Test with invalid JSON
            event3 = {'body': 'invalid json'}
            result3 = parse_request_body(event3)
            
            if result3 is None:
                self.successes.append("✓ Invalid JSON handled correctly")
            else:
                self.warnings.append("⚠ Invalid JSON should return None")
            
            return True
            
        except Exception as e:
            self.errors.append(f"✗ Request parsing test failed: {str(e)}")
            return False
    
    def test_handler_execution(self) -> bool:
        """Test handler execution with mock events."""
        logger.info("Testing handler execution")
        
        try:
            from src.infrastructure.api_lambda_handlers import (
                health_check_handler,
                chatbot_handler
            )
            
            # Mock context
            class MockContext:
                request_id = 'test-request-id'
                function_name = 'test-function'
                memory_limit_in_mb = 512
                invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
            
            context = MockContext()
            
            # Test health check handler
            event = {'httpMethod': 'GET', 'path': '/health'}
            response = health_check_handler(event, context)
            
            if response['statusCode'] == 200:
                self.successes.append("✓ Health check handler executes successfully")
                
                body = json.loads(response['body'])
                if 'status' in body and 'services' in body:
                    self.successes.append("✓ Health check response has correct structure")
                else:
                    self.warnings.append("⚠ Health check response missing fields")
            else:
                self.errors.append("✗ Health check handler returned error")
                return False
            
            # Test chatbot handler with valid request
            event = {
                'httpMethod': 'POST',
                'path': '/chat',
                'body': json.dumps({'message': 'Hello'})
            }
            response = chatbot_handler(event, context)
            
            if response['statusCode'] in [200, 503]:  # 503 if services not configured
                self.successes.append("✓ Chatbot handler executes successfully")
            else:
                self.errors.append(f"✗ Chatbot handler returned unexpected status: {response['statusCode']}")
                return False
            
            # Test chatbot handler with invalid request
            event = {
                'httpMethod': 'POST',
                'path': '/chat',
                'body': json.dumps({})  # Missing message
            }
            response = chatbot_handler(event, context)
            
            if response['statusCode'] == 400:
                self.successes.append("✓ Chatbot handler validates input correctly")
            else:
                self.warnings.append("⚠ Chatbot handler should return 400 for invalid input")
            
            return True
            
        except Exception as e:
            self.errors.append(f"✗ Handler execution test failed: {str(e)}")
            import traceback
            self.errors.append(f"  Traceback: {traceback.format_exc()}")
            return False
    
    def validate_deployment_script(self) -> bool:
        """Validate deployment script structure."""
        logger.info("Validating deployment script")
        
        try:
            # Check if deployment script is importable
            sys.path.insert(0, str(Path('infrastructure')))
            
            import deploy_api_lambdas
            
            if hasattr(deploy_api_lambdas, 'LambdaDeployer'):
                self.successes.append("✓ LambdaDeployer class found")
            else:
                self.errors.append("✗ LambdaDeployer class not found")
                return False
            
            deployer = deploy_api_lambdas.LambdaDeployer(region='us-east-1')
            
            if hasattr(deployer, 'functions') and len(deployer.functions) > 0:
                self.successes.append(f"✓ Found {len(deployer.functions)} function configurations")
            else:
                self.errors.append("✗ No function configurations found")
                return False
            
            required_methods = [
                'create_execution_role',
                'create_deployment_package',
                'deploy_function',
                'deploy_all'
            ]
            
            all_present = True
            for method_name in required_methods:
                if hasattr(deployer, method_name):
                    self.successes.append(f"✓ Found method: {method_name}")
                else:
                    self.errors.append(f"✗ Missing method: {method_name}")
                    all_present = False
            
            return all_present
            
        except ImportError as e:
            self.errors.append(f"✗ Failed to import deployment script: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"✗ Deployment script validation failed: {str(e)}")
            return False
    
    def validate_error_handling(self) -> bool:
        """Validate error handling in handlers."""
        logger.info("Validating error handling")
        
        try:
            from src.infrastructure.api_lambda_handlers import chatbot_handler
            
            class MockContext:
                request_id = 'test-request-id'
            
            context = MockContext()
            
            # Test with malformed event
            event = {'body': 'not valid json {'}
            response = chatbot_handler(event, context)
            
            if response['statusCode'] in [400, 500]:
                self.successes.append("✓ Handlers handle malformed input gracefully")
            else:
                self.warnings.append("⚠ Handlers should return error for malformed input")
            
            return True
            
        except Exception as e:
            self.errors.append(f"✗ Error handling validation failed: {str(e)}")
            return False
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        logger.info("Starting Lambda handler validation")
        
        validations = [
            ("File Structure", self.validate_file_structure),
            ("Handler Imports", self.validate_handler_imports),
            ("Handler Signatures", self.validate_handler_signatures),
            ("Response Creation", self.test_response_creation),
            ("Request Parsing", self.test_request_parsing),
            ("Handler Execution", self.test_handler_execution),
            ("Deployment Script", self.validate_deployment_script),
            ("Error Handling", self.validate_error_handling)
        ]
        
        all_passed = True
        
        for name, validation_func in validations:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print('='*60)
            
            try:
                passed = validation_func()
                if not passed:
                    all_passed = False
            except Exception as e:
                self.errors.append(f"✗ {name} validation crashed: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if self.successes:
            print(f"\n✓ Successes ({len(self.successes)}):")
            for success in self.successes:
                print(f"  {success}")
        
        if self.warnings:
            print(f"\n⚠ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print(f"\n✗ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n" + "="*60)
        
        if not self.errors:
            print("✓ ALL VALIDATIONS PASSED")
        else:
            print(f"✗ VALIDATION FAILED ({len(self.errors)} errors)")
        
        print("="*60 + "\n")


def main():
    """Main validation function."""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    validator = LambdaHandlerValidator()
    
    try:
        all_passed = validator.run_all_validations()
        validator.print_summary()
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        logger.error("Validation failed with exception", error=str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
