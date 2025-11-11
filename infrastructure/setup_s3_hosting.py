#!/usr/bin/env python3
"""
S3 Static Website Hosting Setup Script

This script creates and configures an S3 bucket for static website hosting
for the Concert Data Platform web application.
"""

import boto3
import json
import sys
from typing import Dict, Optional
from botocore.exceptions import ClientError


class S3HostingSetup:
    """Manages S3 bucket setup for static website hosting."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize S3 hosting setup.
        
        Args:
            bucket_name: Name of the S3 bucket to create
            region: AWS region for the bucket
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
    def create_bucket(self) -> bool:
        """
        Create S3 bucket with appropriate configuration.
        
        Returns:
            True if bucket was created or already exists, False otherwise
        """
        try:
            # Check if bucket already exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                print(f"✓ Bucket {self.bucket_name} already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            
            # Create bucket
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            print(f"✓ Created bucket: {self.bucket_name}")
            return True
            
        except ClientError as e:
            print(f"✗ Error creating bucket: {e}")
            return False
    
    def configure_website_hosting(self) -> bool:
        """
        Configure bucket for static website hosting.
        
        Returns:
            True if configuration succeeded, False otherwise
        """
        try:
            website_configuration = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}  # SPA routing support
            }
            
            self.s3_client.put_bucket_website(
                Bucket=self.bucket_name,
                WebsiteConfiguration=website_configuration
            )
            
            print(f"✓ Configured website hosting for {self.bucket_name}")
            return True
            
        except ClientError as e:
            print(f"✗ Error configuring website hosting: {e}")
            return False
    
    def configure_public_access(self) -> bool:
        """
        Configure bucket for public read access.
        
        Returns:
            True if configuration succeeded, False otherwise
        """
        try:
            # Disable block public access
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            
            # Set bucket policy for public read access
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [{
                    'Sid': 'PublicReadGetObject',
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': 's3:GetObject',
                    'Resource': f'arn:aws:s3:::{self.bucket_name}/*'
                }]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            print(f"✓ Configured public access for {self.bucket_name}")
            return True
            
        except ClientError as e:
            print(f"✗ Error configuring public access: {e}")
            return False
    
    def enable_versioning(self) -> bool:
        """
        Enable versioning on the bucket.
        
        Returns:
            True if versioning was enabled, False otherwise
        """
        try:
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            print(f"✓ Enabled versioning for {self.bucket_name}")
            return True
            
        except ClientError as e:
            print(f"✗ Error enabling versioning: {e}")
            return False
    
    def get_website_url(self) -> Optional[str]:
        """
        Get the website endpoint URL.
        
        Returns:
            Website URL or None if not configured
        """
        try:
            response = self.s3_client.get_bucket_website(Bucket=self.bucket_name)
            url = f"http://{self.bucket_name}.s3-website-{self.region}.amazonaws.com"
            return url
        except ClientError:
            return None
    
    def setup(self) -> bool:
        """
        Run complete setup process.
        
        Returns:
            True if all steps succeeded, False otherwise
        """
        print(f"\n🚀 Setting up S3 static website hosting...")
        print(f"Bucket: {self.bucket_name}")
        print(f"Region: {self.region}\n")
        
        steps = [
            ("Creating bucket", self.create_bucket),
            ("Configuring website hosting", self.configure_website_hosting),
            ("Configuring public access", self.configure_public_access),
            ("Enabling versioning", self.enable_versioning),
        ]
        
        for step_name, step_func in steps:
            print(f"{step_name}...")
            if not step_func():
                print(f"\n✗ Setup failed at: {step_name}")
                return False
        
        website_url = self.get_website_url()
        if website_url:
            print(f"\n✅ Setup complete!")
            print(f"\nWebsite URL: {website_url}")
            print(f"\nNote: Use CloudFront for production with HTTPS support")
        else:
            print(f"\n⚠️  Setup complete but couldn't retrieve website URL")
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Setup S3 bucket for static website hosting'
    )
    parser.add_argument(
        '--bucket-name',
        default='concert-data-platform-web',
        help='S3 bucket name (default: concert-data-platform-web)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    setup = S3HostingSetup(
        bucket_name=args.bucket_name,
        region=args.region
    )
    
    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
