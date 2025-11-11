#!/usr/bin/env python3
"""
CloudFront Cache Invalidation Script

This script invalidates CloudFront cache after deploying new content.
"""

import boto3
import sys
import time
from typing import List, Optional
from botocore.exceptions import ClientError


class CloudFrontInvalidator:
    """Manages CloudFront cache invalidation."""
    
    def __init__(self, bucket_name: str):
        """
        Initialize CloudFront invalidator.
        
        Args:
            bucket_name: S3 bucket name to find associated distribution
        """
        self.bucket_name = bucket_name
        self.cloudfront_client = boto3.client('cloudfront')
        
    def find_distribution_id(self) -> Optional[str]:
        """
        Find CloudFront distribution ID for the bucket.
        
        Returns:
            Distribution ID if found, None otherwise
        """
        try:
            distributions = self.cloudfront_client.list_distributions()
            
            if 'DistributionList' not in distributions:
                print("✗ No CloudFront distributions found")
                return None
            
            items = distributions['DistributionList'].get('Items', [])
            
            for dist in items:
                if 'Origins' in dist and 'Items' in dist['Origins']:
                    for origin in dist['Origins']['Items']:
                        if self.bucket_name in origin.get('DomainName', ''):
                            dist_id = dist['Id']
                            print(f"✓ Found distribution: {dist_id}")
                            print(f"  Domain: {dist['DomainName']}")
                            return dist_id
            
            print(f"✗ No distribution found for bucket: {self.bucket_name}")
            return None
            
        except ClientError as e:
            print(f"✗ Error finding distribution: {e}")
            return None
    
    def create_invalidation(
        self,
        distribution_id: str,
        paths: List[str] = None
    ) -> Optional[str]:
        """
        Create cache invalidation for specified paths.
        
        Args:
            distribution_id: CloudFront distribution ID
            paths: List of paths to invalidate (default: ['/*'])
            
        Returns:
            Invalidation ID if created, None otherwise
        """
        if paths is None:
            paths = ['/*']
        
        try:
            response = self.cloudfront_client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f"invalidation-{int(time.time())}"
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            status = response['Invalidation']['Status']
            
            print(f"✓ Created invalidation: {invalidation_id}")
            print(f"  Status: {status}")
            print(f"  Paths: {', '.join(paths)}")
            
            return invalidation_id
            
        except ClientError as e:
            print(f"✗ Error creating invalidation: {e}")
            return None
    
    def wait_for_invalidation(
        self,
        distribution_id: str,
        invalidation_id: str,
        timeout: int = 300
    ) -> bool:
        """
        Wait for invalidation to complete.
        
        Args:
            distribution_id: CloudFront distribution ID
            invalidation_id: Invalidation ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if completed, False if timeout or error
        """
        print("\n⏳ Waiting for invalidation to complete...")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                response = self.cloudfront_client.get_invalidation(
                    DistributionId=distribution_id,
                    Id=invalidation_id
                )
                
                status = response['Invalidation']['Status']
                
                if status == 'Completed':
                    print("✓ Invalidation completed")
                    return True
                
                elapsed = int(time.time() - start_time)
                print(f"  Status: {status} (elapsed: {elapsed}s)", end='\r')
                time.sleep(5)
            
            print(f"\n⚠️  Invalidation still in progress after {timeout}s")
            print("   It will complete in the background")
            return False
            
        except ClientError as e:
            print(f"\n✗ Error checking invalidation status: {e}")
            return False
    
    def invalidate(
        self,
        paths: List[str] = None,
        wait: bool = False
    ) -> bool:
        """
        Run complete invalidation process.
        
        Args:
            paths: List of paths to invalidate (default: ['/*'])
            wait: Whether to wait for invalidation to complete
            
        Returns:
            True if invalidation was created, False otherwise
        """
        print(f"\n🔄 Invalidating CloudFront cache...")
        print(f"Bucket: {self.bucket_name}\n")
        
        # Find distribution
        distribution_id = self.find_distribution_id()
        if not distribution_id:
            return False
        
        # Create invalidation
        invalidation_id = self.create_invalidation(distribution_id, paths)
        if not invalidation_id:
            return False
        
        # Wait if requested
        if wait:
            self.wait_for_invalidation(distribution_id, invalidation_id)
        else:
            print("\n✅ Invalidation created successfully")
            print("   Cache will be cleared in a few minutes")
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Invalidate CloudFront cache for deployed content'
    )
    parser.add_argument(
        '--bucket-name',
        default='concert-data-platform-web',
        help='S3 bucket name (default: concert-data-platform-web)'
    )
    parser.add_argument(
        '--paths',
        nargs='+',
        default=['/*'],
        help='Paths to invalidate (default: /*)'
    )
    parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for invalidation to complete'
    )
    
    args = parser.parse_args()
    
    invalidator = CloudFrontInvalidator(bucket_name=args.bucket_name)
    
    success = invalidator.invalidate(paths=args.paths, wait=args.wait)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
