#!/usr/bin/env python3
"""
Web Application Deployment Script

This script builds the React application and deploys it to S3 for static hosting.
Includes build optimization and automated upload.
"""

import boto3
import os
import sys
import subprocess
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional
from botocore.exceptions import ClientError


class WebAppDeployer:
    """Manages web application build and deployment to S3."""
    
    # MIME type mappings for common web assets
    MIME_TYPES = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
    }
    
    def __init__(
        self,
        bucket_name: str,
        web_dir: str = "web",
        region: str = "us-east-1"
    ):
        """
        Initialize web app deployer.
        
        Args:
            bucket_name: S3 bucket name for deployment
            web_dir: Directory containing the web application
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.web_dir = Path(web_dir)
        self.dist_dir = self.web_dir / "dist"
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
    def check_prerequisites(self) -> bool:
        """
        Check if all prerequisites are met.
        
        Returns:
            True if prerequisites are met, False otherwise
        """
        print("Checking prerequisites...")
        
        # Check if web directory exists
        if not self.web_dir.exists():
            print(f"✗ Web directory not found: {self.web_dir}")
            return False
        
        # Check if package.json exists
        package_json = self.web_dir / "package.json"
        if not package_json.exists():
            print(f"✗ package.json not found in {self.web_dir}")
            return False
        
        # Check if node_modules exists
        node_modules = self.web_dir / "node_modules"
        if not node_modules.exists():
            print(f"⚠️  node_modules not found. Run 'npm install' first.")
            return False
        
        # Check if bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"✗ Bucket {self.bucket_name} does not exist")
                print(f"  Run: python infrastructure/setup_s3_hosting.py --bucket-name {self.bucket_name}")
                return False
            raise
        
        print("✓ Prerequisites check passed")
        return True
    
    def build_application(self) -> bool:
        """
        Build the React application for production.
        
        Returns:
            True if build succeeded, False otherwise
        """
        print("\n📦 Building application...")
        
        try:
            # Run npm build
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=self.web_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("✓ Build completed successfully")
            
            # Check if dist directory was created
            if not self.dist_dir.exists():
                print(f"✗ Build output directory not found: {self.dist_dir}")
                return False
            
            # Count files in dist
            files = list(self.dist_dir.rglob('*'))
            file_count = len([f for f in files if f.is_file()])
            print(f"✓ Generated {file_count} files in {self.dist_dir}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Build failed:")
            print(e.stderr)
            return False
        except Exception as e:
            print(f"✗ Build error: {e}")
            return False
    
    def get_content_type(self, file_path: Path) -> str:
        """
        Get MIME type for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        suffix = file_path.suffix.lower()
        
        # Check custom mappings first
        if suffix in self.MIME_TYPES:
            return self.MIME_TYPES[suffix]
        
        # Fall back to mimetypes module
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or 'application/octet-stream'
    
    def get_cache_control(self, file_path: Path) -> str:
        """
        Get cache control header for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cache-Control header value
        """
        suffix = file_path.suffix.lower()
        
        # Long cache for hashed assets (Vite adds hashes to filenames)
        if any(hash_pattern in file_path.name for hash_pattern in ['-', '.']):
            if suffix in ['.js', '.css', '.woff', '.woff2', '.ttf']:
                # Check if filename contains hash (Vite pattern)
                parts = file_path.stem.split('.')
                if len(parts) > 1 or '-' in file_path.stem:
                    return 'public, max-age=31536000, immutable'
        
        # Medium cache for images
        if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']:
            return 'public, max-age=86400'
        
        # No cache for HTML files (for SPA routing)
        if suffix == '.html':
            return 'no-cache, no-store, must-revalidate'
        
        # Default cache
        return 'public, max-age=3600'
    
    def upload_file(self, file_path: Path, s3_key: str) -> bool:
        """
        Upload a single file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key
            
        Returns:
            True if upload succeeded, False otherwise
        """
        try:
            content_type = self.get_content_type(file_path)
            cache_control = self.get_cache_control(file_path)
            
            extra_args = {
                'ContentType': content_type,
                'CacheControl': cache_control,
            }
            
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            return True
            
        except ClientError as e:
            print(f"✗ Error uploading {s3_key}: {e}")
            return False
    
    def upload_to_s3(self) -> bool:
        """
        Upload all built files to S3.
        
        Returns:
            True if upload succeeded, False otherwise
        """
        print(f"\n☁️  Uploading to S3 bucket: {self.bucket_name}...")
        
        try:
            # Get all files in dist directory
            files = [f for f in self.dist_dir.rglob('*') if f.is_file()]
            
            if not files:
                print("✗ No files found to upload")
                return False
            
            uploaded = 0
            failed = 0
            
            for file_path in files:
                # Calculate S3 key (relative path from dist)
                relative_path = file_path.relative_to(self.dist_dir)
                s3_key = str(relative_path).replace('\\', '/')
                
                if self.upload_file(file_path, s3_key):
                    uploaded += 1
                    print(f"  ✓ {s3_key}")
                else:
                    failed += 1
                    print(f"  ✗ {s3_key}")
            
            print(f"\n✓ Uploaded {uploaded} files")
            if failed > 0:
                print(f"✗ Failed to upload {failed} files")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Upload error: {e}")
            return False
    
    def get_website_url(self) -> Optional[str]:
        """
        Get the website URL.
        
        Returns:
            Website URL or None
        """
        try:
            # Try to get CloudFront distribution
            cloudfront = boto3.client('cloudfront')
            distributions = cloudfront.list_distributions()
            
            if 'DistributionList' in distributions and 'Items' in distributions['DistributionList']:
                for dist in distributions['DistributionList']['Items']:
                    if 'Origins' in dist and 'Items' in dist['Origins']:
                        for origin in dist['Origins']['Items']:
                            if self.bucket_name in origin.get('DomainName', ''):
                                return f"https://{dist['DomainName']}"
            
            # Fall back to S3 website URL
            return f"http://{self.bucket_name}.s3-website-{self.region}.amazonaws.com"
            
        except Exception:
            return f"http://{self.bucket_name}.s3-website-{self.region}.amazonaws.com"
    
    def deploy(self) -> bool:
        """
        Run complete deployment process.
        
        Returns:
            True if deployment succeeded, False otherwise
        """
        print("\n🚀 Deploying web application...")
        print(f"Bucket: {self.bucket_name}")
        print(f"Region: {self.region}\n")
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Building application", self.build_application),
            ("Uploading to S3", self.upload_to_s3),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n✗ Deployment failed at: {step_name}")
                return False
        
        website_url = self.get_website_url()
        print(f"\n✅ Deployment complete!")
        print(f"\nWebsite URL: {website_url}")
        print(f"\nNote: It may take a few minutes for changes to propagate")
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build and deploy web application to S3'
    )
    parser.add_argument(
        '--bucket-name',
        default='concert-data-platform-web',
        help='S3 bucket name (default: concert-data-platform-web)'
    )
    parser.add_argument(
        '--web-dir',
        default='web',
        help='Web application directory (default: web)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    deployer = WebAppDeployer(
        bucket_name=args.bucket_name,
        web_dir=args.web_dir,
        region=args.region
    )
    
    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
