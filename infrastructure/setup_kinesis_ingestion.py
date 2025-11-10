"""
Python script to set up Kinesis stream for API data ingestion.
Integrates with existing infrastructure code.
"""
import boto3
import json
import time
from botocore.exceptions import ClientError
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.environment import load_env_file
from src.config.settings import settings

# Load environment
load_env_file()


class KinesisSetup:
    """Setup and configure Kinesis stream for API data ingestion."""
    
    def __init__(self):
        # Build AWS config
        aws_config = {'region_name': settings.aws.region}
        
        # Add credentials if available from environment
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if access_key and secret_key and access_key != 'your_aws_access_key_here':
            aws_config['aws_access_key_id'] = access_key
            aws_config['aws_secret_access_key'] = secret_key
        
        self.kinesis_client = boto3.client('kinesis', **aws_config)
        self.iam_client = boto3.client('iam', **aws_config)
        self.cloudwatch_client = boto3.client('cloudwatch', **aws_config)
        
        self.stream_name = settings.aws.kinesis_stream_name
        self.shard_count = settings.aws.kinesis_shard_count
        self.region = settings.aws.region
        
        print("=" * 70)
        print("  Kinesis Stream Setup for API Data Ingestion")
        print("=" * 70)
        print()
        print(f"Stream Name: {self.stream_name}")
        print(f"Shard Count: {self.shard_count}")
        print(f"Region: {self.region}")
        print()
    
    def check_stream_exists(self):
        """Check if the Kinesis stream already exists."""
        try:
            response = self.kinesis_client.describe_stream(
                StreamName=self.stream_name
            )
            return True, response['StreamDescription']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False, None
            raise
    
    def create_stream(self):
        """Create the Kinesis stream."""
        print("Creating Kinesis stream...")
        
        try:
            self.kinesis_client.create_stream(
                StreamName=self.stream_name,
                ShardCount=self.shard_count,
                StreamModeDetails={'StreamMode': 'PROVISIONED'}
            )
            print("✓ Stream creation initiated")
            
            # Wait for stream to become active
            print("Waiting for stream to become active...")
            waiter = self.kinesis_client.get_waiter('stream_exists')
            waiter.wait(
                StreamName=self.stream_name,
                WaiterConfig={'Delay': 10, 'MaxAttempts': 30}
            )
            print("✓ Stream is active")
            return True
            
        except ClientError as e:
            print(f"✗ Failed to create stream: {e}")
            return False
    
    def enable_enhanced_monitoring(self):
        """Enable enhanced monitoring for the stream."""
        print("\nEnabling enhanced monitoring...")
        
        try:
            self.kinesis_client.enable_enhanced_monitoring(
                StreamName=self.stream_name,
                ShardLevelMetrics=[
                    'IncomingBytes',
                    'IncomingRecords',
                    'OutgoingBytes',
                    'OutgoingRecords',
                    'WriteProvisionedThroughputExceeded',
                    'ReadProvisionedThroughputExceeded',
                    'IteratorAgeMilliseconds'
                ]
            )
            print("✓ Enhanced monitoring enabled")
            return True
        except ClientError as e:
            print(f"⚠ Enhanced monitoring: {e}")
            return False
    
    def enable_encryption(self):
        """Enable server-side encryption for the stream."""
        print("\nEnabling server-side encryption...")
        
        try:
            self.kinesis_client.start_stream_encryption(
                StreamName=self.stream_name,
                EncryptionType='KMS',
                KeyId='alias/aws/kinesis'
            )
            print("✓ Encryption enabled")
            return True
        except ClientError as e:
            if 'already encrypted' in str(e).lower():
                print("⚠ Stream is already encrypted")
                return True
            print(f"⚠ Encryption: {e}")
            return False
    
    def add_tags(self):
        """Add tags to the stream."""
        print("\nAdding tags...")
        
        try:
            self.kinesis_client.add_tags_to_stream(
                StreamName=self.stream_name,
                Tags={
                    'Project': 'ConcertDataPlatform',
                    'Environment': settings.app.environment,
                    'Purpose': 'APIDataIngestion',
                    'ManagedBy': 'Python'
                }
            )
            print("✓ Tags added")
            return True
        except ClientError as e:
            print(f"⚠ Tags: {e}")
            return False
    
    def create_iam_policy(self):
        """Create IAM policy for stream access."""
        print("\nCreating IAM policy...")
        
        # Get stream ARN
        try:
            response = self.kinesis_client.describe_stream(
                StreamName=self.stream_name
            )
            stream_arn = response['StreamDescription']['StreamARN']
        except ClientError as e:
            print(f"✗ Failed to get stream ARN: {e}")
            return False
        
        policy_name = "ConcertDataIngestionKinesisPolicy"
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "kinesis:PutRecord",
                        "kinesis:PutRecords",
                        "kinesis:DescribeStream",
                        "kinesis:DescribeStreamSummary",
                        "kinesis:GetRecords",
                        "kinesis:GetShardIterator",
                        "kinesis:ListShards"
                    ],
                    "Resource": stream_arn
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kinesis:ListStreams"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Check if policy exists
            aws_config = {'region_name': settings.aws.region}
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if access_key and secret_key and access_key != 'your_aws_access_key_here':
                aws_config['aws_access_key_id'] = access_key
                aws_config['aws_secret_access_key'] = secret_key
            
            account_id = boto3.client('sts', **aws_config).get_caller_identity()['Account']
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            
            try:
                self.iam_client.get_policy(PolicyArn=policy_arn)
                print(f"⚠ IAM policy already exists: {policy_name}")
                print(f"  Policy ARN: {policy_arn}")
                return True
            except ClientError:
                pass
            
            # Create policy
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Policy for Concert Data Ingestion to write to Kinesis stream"
            )
            
            print(f"✓ IAM policy created: {policy_name}")
            print(f"  Policy ARN: {response['Policy']['Arn']}")
            print()
            print("  Attach this policy to your Lambda execution role or EC2 instance profile:")
            print(f"  aws iam attach-role-policy --role-name YOUR_ROLE_NAME --policy-arn {response['Policy']['Arn']}")
            return True
            
        except ClientError as e:
            print(f"⚠ IAM policy: {e}")
            return False
    
    def test_stream(self):
        """Send a test record to the stream."""
        print("\nTesting stream...")
        
        test_data = {
            'test': True,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'message': 'Test record from setup script'
        }
        
        try:
            response = self.kinesis_client.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(test_data).encode('utf-8'),
                PartitionKey='test'
            )
            print("✓ Test record sent successfully")
            print(f"  Shard ID: {response['ShardId']}")
            print(f"  Sequence Number: {response['SequenceNumber']}")
            return True
        except ClientError as e:
            print(f"✗ Test failed: {e}")
            return False
    
    def get_stream_details(self):
        """Get and display stream details."""
        print("\n" + "=" * 70)
        print("  Stream Details")
        print("=" * 70)
        
        try:
            response = self.kinesis_client.describe_stream(
                StreamName=self.stream_name
            )
            
            stream_desc = response['StreamDescription']
            
            print(f"\nStream Name: {stream_desc['StreamName']}")
            print(f"Stream ARN: {stream_desc['StreamARN']}")
            print(f"Status: {stream_desc['StreamStatus']}")
            print(f"Shard Count: {len(stream_desc['Shards'])}")
            print(f"Retention Period: {stream_desc['RetentionPeriodHours']} hours")
            print(f"Encryption: {'Enabled' if stream_desc.get('EncryptionType') else 'Disabled'}")
            
            # Get enhanced monitoring status
            enhanced_monitoring = stream_desc.get('EnhancedMonitoring', [])
            if enhanced_monitoring:
                print(f"Enhanced Monitoring: Enabled")
                print(f"  Metrics: {', '.join(enhanced_monitoring[0].get('ShardLevelMetrics', []))}")
            else:
                print(f"Enhanced Monitoring: Disabled")
            
            return True
        except ClientError as e:
            print(f"✗ Failed to get stream details: {e}")
            return False
    
    def setup(self):
        """Run the complete setup process."""
        # Check if stream exists
        exists, stream_desc = self.check_stream_exists()
        
        if exists:
            print(f"⚠ Stream already exists: {self.stream_name}")
            print(f"  Status: {stream_desc['StreamStatus']}")
            print(f"  Shard Count: {len(stream_desc['Shards'])}")
            print()
            
            response = input("Do you want to update the stream configuration? (y/n): ")
            if response.lower() != 'y':
                print("\nSkipping stream creation.")
                self.get_stream_details()
                return True
        else:
            # Create stream
            if not self.create_stream():
                return False
        
        # Configure stream
        self.enable_enhanced_monitoring()
        
        # Ask about encryption
        response = input("\nEnable encryption with AWS managed key? (y/n): ")
        if response.lower() == 'y':
            self.enable_encryption()
        
        # Add tags
        self.add_tags()
        
        # Create IAM policy
        self.create_iam_policy()
        
        # Test stream
        self.test_stream()
        
        # Show details
        self.get_stream_details()
        
        # Print next steps
        print("\n" + "=" * 70)
        print("  Setup Complete!")
        print("=" * 70)
        print()
        print("✓ Kinesis stream is ready for API data ingestion")
        print()
        print("Next steps:")
        print("  1. Run the ingestion pipeline:")
        print("     python -m src.services.external_apis.production_ingestion")
        print()
        print("  2. Monitor the stream in CloudWatch:")
        print(f"     https://console.aws.amazon.com/kinesis/home?region={self.region}#/streams/details/{self.stream_name}/monitoring")
        print()
        print("  3. Set up Lambda consumers for real-time processing")
        print()
        print("Useful Python code:")
        print()
        print("  # Send records to stream")
        print("  from src.services.external_apis.production_ingestion import ProductionDataPipeline")
        print("  async with ProductionDataPipeline() as pipeline:")
        print("      await pipeline.run_full_ingestion()")
        print()
        
        return True


def main():
    """Main entry point."""
    try:
        setup = KinesisSetup()
        success = setup.setup()
        
        if success:
            print("✓ Setup completed successfully")
            return 0
        else:
            print("✗ Setup failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())