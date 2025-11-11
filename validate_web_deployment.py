#!/usr/bin/env python3
"""
Web Deployment Validation Script

Validates that all web deployment infrastructure is properly set up.
"""

import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description} not found: {file_path}")
        return False


def check_file_executable(file_path: str, description: str) -> bool:
    """Check if a file is executable."""
    path = Path(file_path)
    if path.exists() and os.access(path, os.X_OK):
        print(f"✓ {description} is executable: {file_path}")
        return True
    else:
        print(f"✗ {description} not executable: {file_path}")
        return False


def validate_deployment_infrastructure():
    """Validate web deployment infrastructure."""
    print("🔍 Validating Web Deployment Infrastructure\n")
    
    all_checks_passed = True
    
    # Check deployment scripts
    print("Deployment Scripts:")
    scripts = [
        ("infrastructure/setup_s3_hosting.py", "S3 hosting setup script"),
        ("infrastructure/deploy_web_app.py", "Web app deployment script"),
        ("infrastructure/deploy_web_app.sh", "Web app deployment shell script"),
        ("infrastructure/setup_cloudfront.py", "CloudFront setup script"),
        ("infrastructure/invalidate_cloudfront.py", "Cache invalidation script"),
        ("infrastructure/deploy_web_with_cdn.sh", "Complete deployment script"),
    ]
    
    for script_path, description in scripts:
        if not check_file_exists(script_path, description):
            all_checks_passed = False
        elif not check_file_executable(script_path, description):
            all_checks_passed = False
    
    print()
    
    # Check documentation
    print("Documentation:")
    docs = [
        ("docs/infrastructure/WEB_DEPLOYMENT_GUIDE.md", "Deployment guide"),
        ("DEPLOYMENT.md", "Quick reference guide"),
    ]
    
    for doc_path, description in docs:
        if not check_file_exists(doc_path, description):
            all_checks_passed = False
    
    print()
    
    # Check web application structure
    print("Web Application:")
    web_files = [
        ("web/package.json", "Package configuration"),
        ("web/vite.config.ts", "Vite configuration"),
        ("web/tsconfig.json", "TypeScript configuration"),
        ("web/index.html", "HTML entry point"),
        ("web/src/main.tsx", "React entry point"),
    ]
    
    for file_path, description in web_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    print()
    
    # Check environment files
    print("Environment Configuration:")
    env_files = [
        ("web/.env.example", "Environment example file"),
    ]
    
    for file_path, description in env_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    print()
    
    # Summary
    if all_checks_passed:
        print("✅ All validation checks passed!")
        print("\nNext steps:")
        print("1. Configure AWS credentials: aws configure")
        print("2. Set up S3 hosting: python3 infrastructure/setup_s3_hosting.py")
        print("3. Set up CloudFront: python3 infrastructure/setup_cloudfront.py")
        print("4. Deploy application: ./infrastructure/deploy_web_with_cdn.sh")
        return True
    else:
        print("❌ Some validation checks failed")
        print("\nPlease ensure all required files are present and executable")
        return False


def main():
    """Main entry point."""
    success = validate_deployment_infrastructure()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
