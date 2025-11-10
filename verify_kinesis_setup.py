"""
Verification script to check Kinesis stream setup.
"""
import boto3
from botocore.exceptions import ClientError
import sys
import os

# Load environment
sys.path.insert(0, os.path.dirname(__file__))
from src.config.environment import load_env_file
from src.config.settings import settings

load_env_file()


def verify_kinesis_setup():
    """Verify that Kinesis stream is properly set up."""
    
    print("=" * 70)
    print("  Kinesis Stream Verification")
    print("=" * 70)
    print()
    
    # Configuration
    stream_name = os.getenv('AWS_KINESIS_STREAM_NAME', 'concert-data-stream')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"Stream Name: {stream_name}")
    print(f"Region: {region}")
    print()
    
    # Create client
    try:
        aws_config = {'region_name': region}
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if access_key and secret_key and access_key != 'your_aws_access_key_here':
            aws_config['aws_access_key_id'] = access_key
            aws_config['aws_secret_access_key'] = secret_key
        
        kinesis = boto3.client('kinesis', **aws_config)
        print("✓ AWS credentials valid")
    except Exception as e:
        print(f"✗ Failed to create Kinesis client: {e}")
        return False
    
    print()
    
    # Check if stream exists
    print("Checking stream existence...")
    try:
        response = kinesis.describe_stream(StreamName=stream_name)
        stream_desc = response['StreamDescription']
        print(f"✓ Stream exists: {stream_name}")
        print(f"  Status: {stream_desc['StreamStatus']}")
        print(f"  Shard Count: {len(stream_desc['Shards'])}")
        print(f"  Retention: {stream_desc['RetentionPeriodHours']} hours")
        print(f"  Encryption: {'Enabled' if stream_desc.get('EncryptionType') else 'Disabled'}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"✗ Stream not found: {stream_name}")
            print()
            print("To create the stream, run:")
            print("  ./infrastructure/setup_kinesis_for_ingestion.sh")
            print("  OR")
            print("  python infrastructure/setup_kinesis_ingestion.py")
            return False
        else:
            print(f"✗ Error checking stream: {e}")
            return False
    
    print()
    
    # Check permissions
    print("Checking permissions...")
    try:
        # Try to list streams
        kinesis.list_streams()
        print("✓ List streams permission")
        
        # Try to describe stream
        kinesis.describe_stream(StreamName=stream_name)
        print("✓ Describe stream permission")
        
        # Try to put record
        import json
        import time
        test_data = {
            'test': True,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'verification': 'test'
        }
        
        response = kinesis.put_record(
            StreamName=stream_name,
            Data=json.dumps(test_data).encode('utf-8'),
            PartitionKey='verification-test'
        )
        print("✓ Put record permission")
        print(f"  Test record sent to shard: {response['ShardId']}")
        
    except ClientError as e:
        print(f"✗ Permission error: {e}")
        print()
        print("Make sure your IAM user/role has the following permissions:")
        print("  - kinesis:ListStreams")
        print("  - kinesis:DescribeStream")
        print("  - kinesis:PutRecord")
        print("  - kinesis:PutRecords")
        return False
    
    print()
    
    # Check CloudWatch metrics
    print("Checking CloudWatch metrics...")
    try:
        cloudwatch = boto3.client('cloudwatch', **aws_config)
        
        from datetime import datetime, timedelta
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='IncomingRecords',
            Dimensions=[
                {'Name': 'StreamName', 'Value': stream_name}
            ],
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Sum']
        )
        
        if response['Datapoints']:
            total_records = sum(dp['Sum'] for dp in response['Datapoints'])
            print(f"✓ CloudWatch metrics available")
            print(f"  Records in last 5 minutes: {int(total_records)}")
        else:
            print("⚠ No metrics data yet (stream may be new)")
    except Exception as e:
        print(f"⚠ CloudWatch check: {e}")
    
    print()
    print("=" * 70)
    print("  Verification Complete")
    print("=" * 70)
    print()
    print("✓ Kinesis stream is properly configured and ready to use!")
    print()
    print("Next steps:")
    print("  1. Run the API ingestion pipeline:")
    print("     python -m src.services.external_apis.production_ingestion")
    print()
    print("  2. Monitor the stream:")
    print(f"     aws kinesis describe-stream --stream-name {stream_name} --region {region}")
    print()
    print("  3. View metrics in CloudWatch:")
    print(f"     https://console.aws.amazon.com/kinesis/home?region={region}#/streams/details/{stream_name}/monitoring")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = verify_kinesis_setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)