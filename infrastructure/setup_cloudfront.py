#!/usr/bin/env python3
"""
CloudFront CDN Setup Script

This script creates and configures a CloudFront distribution for the
Concert Data Platform web application with S3 origin.
"""

import boto3
import json
import sys
import time
from typing import Dict, Optional
from botocore.exceptions import ClientError


class CloudFrontSetup:
    """Manages CloudFront distribution setup for S3-hosted website."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        price_class: str = "PriceClass_100"
    ):
        """
        Initialize CloudFront setup.
        
        Args:
            bucket_name: S3 bucket name serving as origin
            region: AWS region of the S3 bucket
            price_class: CloudFront price class (PriceClass_100, PriceClass_200, PriceClass_All)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.price_class = price_class
        self.cloudfront_client = boto3.client('cloudfront')
        self.s3_client = boto3.client('s3', region_name=region)
        
    def verify_bucket_exists(self) -> bool:
        """
        Verify that the S3 bucket exists.
        
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Verified bucket exists: {self.bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"✗ Bucket not found: {self.bucket_name}")
                print(f"  Run: python infrastructure/setup_s3_hosting.py --bucket-name {self.bucket_name}")
            else:
                print(f"✗ Error checking bucket: {e}")
            return False
    
    def create_origin_access_identity(self) -> Optional[str]:
        """
        Create CloudFront Origin Access Identity (OAI) for S3 access.
        
        Returns:
            OAI ID if created, None otherwise
        """
        try:
            # Check if OAI already exists
            oais = self.cloudfront_client.list_cloud_front_origin_access_identities()
            
            if 'CloudFrontOriginAccessIdentityList' in oais:
                items = oais['CloudFrontOriginAccessIdentityList'].get('Items', [])
                for oai in items:
                    if self.bucket_name in oai.get('Comment', ''):
                        print(f"✓ Using existing OAI: {oai['Id']}")
                        return oai['Id']
            
            # Create new OAI
            response = self.cloudfront_client.create_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={
                    'CallerReference': f"{self.bucket_name}-{int(time.time())}",
                    'Comment': f"OAI for {self.bucket_name}"
                }
            )
            
            oai_id = response['CloudFrontOriginAccessIdentity']['Id']
            print(f"✓ Created Origin Access Identity: {oai_id}")
            return oai_id
            
        except ClientError as e:
            print(f"✗ Error creating OAI: {e}")
            return None
    
    def update_bucket_policy_for_oai(self, oai_id: str) -> bool:
        """
        Update S3 bucket policy to allow CloudFront OAI access.
        
        Args:
            oai_id: CloudFront Origin Access Identity ID
            
        Returns:
            True if policy was updated, False otherwise
        """
        try:
            # Get OAI canonical user ID
            oai = self.cloudfront_client.get_cloud_front_origin_access_identity(Id=oai_id)
            canonical_user_id = oai['CloudFrontOriginAccessIdentity']['S3CanonicalUserId']
            
            # Create bucket policy
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Sid': 'CloudFrontOAIAccess',
                        'Effect': 'Allow',
                        'Principal': {
                            'CanonicalUser': canonical_user_id
                        },
                        'Action': 's3:GetObject',
                        'Resource': f'arn:aws:s3:::{self.bucket_name}/*'
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            print(f"✓ Updated bucket policy for OAI access")
            return True
            
        except ClientError as e:
            print(f"✗ Error updating bucket policy: {e}")
            return False
    
    def get_distribution_config(self, oai_id: str) -> Dict:
        """
        Generate CloudFront distribution configuration.
        
        Args:
            oai_id: CloudFront Origin Access Identity ID
            
        Returns:
            Distribution configuration dictionary
        """
        origin_domain = f"{self.bucket_name}.s3.{self.region}.amazonaws.com"
        
        config = {
            'CallerReference': f"{self.bucket_name}-{int(time.time())}",
            'Comment': f"CDN for {self.bucket_name}",
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f"S3-{self.bucket_name}",
                        'DomainName': origin_domain,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': f"origin-access-identity/cloudfront/{oai_id}"
                        }
                    }
                ]
            },
            'DefaultRootObject': 'index.html',
            'DefaultCacheBehavior': {
                'TargetOriginId': f"S3-{self.bucket_name}",
                'ViewerProtocolPolicy': 'redirect-to-https',
                'AllowedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD']
                    }
                },
                'Compress': True,
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': {
                        'Quantity': 0
                    }
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000,
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'CustomErrorResponses': {
                'Quantity': 1,
                'Items': [
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 300
                    }
                ]
            },
            'PriceClass': self.price_class,
            'ViewerCertificate': {
                'CloudFrontDefaultCertificate': True,
                'MinimumProtocolVersion': 'TLSv1.2_2021'
            }
        }
        
        return config
    
    def find_existing_distribution(self) -> Optional[Dict]:
        """
        Find existing CloudFront distribution for the bucket.
        
        Returns:
            Distribution info if found, None otherwise
        """
        try:
            distributions = self.cloudfront_client.list_distributions()
            
            if 'DistributionList' not in distributions:
                return None
            
            items = distributions['DistributionList'].get('Items', [])
            
            for dist in items:
                if 'Origins' in dist and 'Items' in dist['Origins']:
                    for origin in dist['Origins']['Items']:
                        if self.bucket_name in origin.get('DomainName', ''):
                            return {
                                'Id': dist['Id'],
                                'DomainName': dist['DomainName'],
                                'Status': dist['Status']
                            }
            
            return None
            
        except ClientError as e:
            print(f"✗ Error listing distributions: {e}")
            return None
    
    def create_distribution(self, oai_id: str) -> Optional[Dict]:
        """
        Create CloudFront distribution.
        
        Args:
            oai_id: CloudFront Origin Access Identity ID
            
        Returns:
            Distribution info if created, None otherwise
        """
        try:
            # Check if distribution already exists
            existing = self.find_existing_distribution()
            if existing:
                print(f"✓ Using existing distribution: {existing['Id']}")
                print(f"  Domain: {existing['DomainName']}")
                print(f"  Status: {existing['Status']}")
                return existing
            
            # Create new distribution
            config = self.get_distribution_config(oai_id)
            
            response = self.cloudfront_client.create_distribution(
                DistributionConfig=config
            )
            
            distribution = response['Distribution']
            dist_info = {
                'Id': distribution['Id'],
                'DomainName': distribution['DomainName'],
                'Status': distribution['Status']
            }
            
            print(f"✓ Created CloudFront distribution: {dist_info['Id']}")
            print(f"  Domain: {dist_info['DomainName']}")
            print(f"  Status: {dist_info['Status']}")
            
            return dist_info
            
        except ClientError as e:
            print(f"✗ Error creating distribution: {e}")
            return None
    
    def setup(self) -> Optional[Dict]:
        """
        Run complete CloudFront setup process.
        
        Returns:
            Distribution info if successful, None otherwise
        """
        print(f"\n🚀 Setting up CloudFront CDN...")
        print(f"Bucket: {self.bucket_name}")
        print(f"Region: {self.region}")
        print(f"Price Class: {self.price_class}\n")
        
        # Verify bucket exists
        if not self.verify_bucket_exists():
            return None
        
        # Create or get OAI
        print("\nCreating Origin Access Identity...")
        oai_id = self.create_origin_access_identity()
        if not oai_id:
            return None
        
        # Update bucket policy
        print("\nUpdating bucket policy...")
        if not self.update_bucket_policy_for_oai(oai_id):
            return None
        
        # Create distribution
        print("\nCreating CloudFront distribution...")
        dist_info = self.create_distribution(oai_id)
        
        if dist_info:
            print(f"\n✅ CloudFront setup complete!")
            print(f"\nDistribution ID: {dist_info['Id']}")
            print(f"Domain Name: {dist_info['DomainName']}")
            print(f"URL: https://{dist_info['DomainName']}")
            print(f"\nStatus: {dist_info['Status']}")
            
            if dist_info['Status'] == 'InProgress':
                print("\n⏳ Distribution is being deployed (this may take 15-20 minutes)")
                print("   You can check status with:")
                print(f"   aws cloudfront get-distribution --id {dist_info['Id']}")
            
            return dist_info
        
        return None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Setup CloudFront CDN for S3-hosted website'
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
    parser.add_argument(
        '--price-class',
        default='PriceClass_100',
        choices=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
        help='CloudFront price class (default: PriceClass_100 - US, Canada, Europe)'
    )
    
    args = parser.parse_args()
    
    setup = CloudFrontSetup(
        bucket_name=args.bucket_name,
        region=args.region,
        price_class=args.price_class
    )
    
    result = setup.setup()
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
