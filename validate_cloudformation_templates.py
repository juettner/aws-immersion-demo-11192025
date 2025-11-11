#!/usr/bin/env python3
"""
Validation script for CloudFormation templates.

Validates all CloudFormation templates for syntax, structure, and best practices.
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import boto3
from botocore.exceptions import ClientError


class CloudFormationValidator:
    """Validate CloudFormation templates."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize validator."""
        self.region = region
        self.cfn_client = boto3.client('cloudformation', region_name=region)
        self.templates_dir = Path('infrastructure/cloudformation')
        self.results = []
    
    def validate_template_syntax(self, template_path: Path) -> Tuple[bool, str]:
        """
        Validate template syntax using AWS CloudFormation API.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            with open(template_path, 'r') as f:
                template_body = f.read()
            
            response = self.cfn_client.validate_template(
                TemplateBody=template_body
            )
            
            return True, "Template syntax is valid"
        
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            return False, f"Template validation failed: {error_msg}"
        
        except Exception as e:
            return False, f"Error reading template: {str(e)}"
    
    def check_template_structure(self, template_path: Path) -> Tuple[bool, List[str]]:
        """
        Check template structure and best practices.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        try:
            # Add CloudFormation constructors for YAML parsing
            yaml.add_multi_constructor('!', lambda loader, suffix, node: None, Loader=yaml.SafeLoader)
            
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)
            
            # Check required sections
            if 'AWSTemplateFormatVersion' not in template:
                issues.append("Missing AWSTemplateFormatVersion")
            
            if 'Description' not in template:
                issues.append("Missing Description")
            
            if 'Resources' not in template:
                issues.append("Missing Resources section")
            
            # Check for outputs
            if 'Outputs' not in template:
                issues.append("Warning: No Outputs defined")
            
            # Check resource naming
            if 'Resources' in template:
                for resource_name, resource in template['Resources'].items():
                    # Check for tags
                    if 'Properties' in resource:
                        props = resource['Properties']
                        
                        # Check if taggable resource has tags
                        taggable_types = [
                            'AWS::EC2::VPC',
                            'AWS::EC2::Subnet',
                            'AWS::EC2::SecurityGroup',
                            'AWS::S3::Bucket',
                            'AWS::Lambda::Function',
                            'AWS::DynamoDB::Table',
                            'AWS::Kinesis::Stream'
                        ]
                        
                        if resource.get('Type') in taggable_types:
                            if 'Tags' not in props:
                                issues.append(
                                    f"Resource {resource_name} missing Tags"
                                )
            
            # Check parameters have descriptions
            if 'Parameters' in template:
                for param_name, param in template['Parameters'].items():
                    if 'Description' not in param:
                        issues.append(
                            f"Parameter {param_name} missing Description"
                        )
            
            return len(issues) == 0, issues
        
        except Exception as e:
            return False, [f"Error parsing template: {str(e)}"]
    
    def validate_all_templates(self) -> bool:
        """
        Validate all CloudFormation templates.
        
        Returns:
            True if all templates are valid
        """
        print("=" * 80)
        print("CloudFormation Template Validation")
        print("=" * 80)
        print()
        
        if not self.templates_dir.exists():
            print(f"❌ Templates directory not found: {self.templates_dir}")
            return False
        
        template_files = sorted(self.templates_dir.glob('*.yaml'))
        
        if not template_files:
            print(f"❌ No template files found in {self.templates_dir}")
            return False
        
        print(f"Found {len(template_files)} templates to validate\n")
        
        all_valid = True
        
        for template_path in template_files:
            print(f"Validating: {template_path.name}")
            print("-" * 80)
            
            # Validate syntax
            syntax_valid, syntax_msg = self.validate_template_syntax(template_path)
            
            if syntax_valid:
                print(f"✅ Syntax: {syntax_msg}")
            else:
                print(f"❌ Syntax: {syntax_msg}")
                all_valid = False
            
            # Check structure
            structure_valid, issues = self.check_template_structure(template_path)
            
            if structure_valid:
                print("✅ Structure: No issues found")
            else:
                print("⚠️  Structure: Issues found:")
                for issue in issues:
                    print(f"   - {issue}")
                
                # Structure issues are warnings, not failures
                if any('Missing' in issue and 'Tags' not in issue for issue in issues):
                    all_valid = False
            
            print()
            
            self.results.append({
                'template': template_path.name,
                'syntax_valid': syntax_valid,
                'structure_valid': structure_valid,
                'issues': issues
            })
        
        # Print summary
        print("=" * 80)
        print("Validation Summary")
        print("=" * 80)
        print()
        
        for result in self.results:
            status = "✅ PASS" if result['syntax_valid'] and result['structure_valid'] else "❌ FAIL"
            print(f"{status} - {result['template']}")
        
        print()
        
        if all_valid:
            print("✅ All templates are valid!")
        else:
            print("❌ Some templates have validation errors")
        
        print()
        
        return all_valid
    
    def check_deployment_script(self) -> bool:
        """Check if deployment script exists and is executable."""
        print("=" * 80)
        print("Deployment Script Check")
        print("=" * 80)
        print()
        
        script_path = Path('infrastructure/deploy_cloudformation_stacks.sh')
        
        if not script_path.exists():
            print(f"❌ Deployment script not found: {script_path}")
            return False
        
        print(f"✅ Deployment script exists: {script_path}")
        
        # Check if executable
        if os.access(script_path, os.X_OK):
            print("✅ Deployment script is executable")
        else:
            print("⚠️  Deployment script is not executable")
            print("   Run: chmod +x infrastructure/deploy_cloudformation_stacks.sh")
        
        print()
        return True
    
    def check_documentation(self) -> bool:
        """Check if documentation exists."""
        print("=" * 80)
        print("Documentation Check")
        print("=" * 80)
        print()
        
        docs = [
            'docs/infrastructure/CLOUDFORMATION_DEPLOYMENT_GUIDE.md',
            'docs/infrastructure/INFRASTRUCTURE_AS_CODE_SUMMARY.md'
        ]
        
        all_exist = True
        
        for doc_path in docs:
            path = Path(doc_path)
            if path.exists():
                print(f"✅ {doc_path}")
            else:
                print(f"❌ {doc_path} not found")
                all_exist = False
        
        print()
        return all_exist


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate CloudFormation templates'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for validation'
    )
    
    args = parser.parse_args()
    
    validator = CloudFormationValidator(region=args.region)
    
    # Validate templates
    templates_valid = validator.validate_all_templates()
    
    # Check deployment script
    script_exists = validator.check_deployment_script()
    
    # Check documentation
    docs_exist = validator.check_documentation()
    
    # Overall result
    print("=" * 80)
    print("Overall Result")
    print("=" * 80)
    print()
    
    if templates_valid and script_exists and docs_exist:
        print("✅ All validation checks passed!")
        print()
        print("Next steps:")
        print("1. Review the deployment guide: docs/infrastructure/CLOUDFORMATION_DEPLOYMENT_GUIDE.md")
        print("2. Deploy infrastructure: ./infrastructure/deploy_cloudformation_stacks.sh development us-east-1")
        print()
        return 0
    else:
        print("❌ Some validation checks failed")
        print()
        print("Please fix the issues above before deploying")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
