# CloudFormation Deployment Guide

Complete guide for deploying the Concert Data Platform infrastructure using AWS CloudFormation.

## Overview

The infrastructure is organized into 6 modular CloudFormation stacks:

1. **Networking** - VPC, subnets, security groups, NAT gateway
2. **Storage & Processing** - S3 buckets, Redshift, Glue, Kinesis
3. **Compute & Application** - Lambda functions, API Gateway, DynamoDB
4. **Chatbot Infrastructure** - Chatbot-specific resources, EventBridge rules
5. **Monitoring & Observability** - CloudWatch dashboards, alarms, SNS topics
6. **Tracing & Logging** - X-Ray, CloudWatch Logs, log metric filters

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Bash shell (for deployment script)
- Redshift master password (min 8 characters)

## Quick Start

### Automated Deployment

Use the deployment script for automated stack deployment:

```bash
cd infrastructure
./deploy_cloudformation_stacks.sh development us-east-1
```

The script will prompt you for:
- Redshift master password
- Alert email address (optional)
- Bedrock Agent ID (optional)
- Bedrock Agent Alias ID (optional)

### Manual Deployment

Deploy stacks individually in order:

```bash
# 1. Networking
aws cloudformation create-stack \
  --stack-name concert-platform-networking-development \
  --template-body file://cloudformation/01-networking.yaml \
  --parameters ParameterKey=Environment,ParameterValue=development \
  --region us-east-1

# 2. Storage & Processing
aws cloudformation create-stack \
  --stack-name concert-platform-storage-development \
  --template-body file://cloudformation/02-storage-processing.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=NetworkStackName,ParameterValue=concert-platform-networking-development \
    ParameterKey=RedshiftMasterPassword,ParameterValue=YourPassword123 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# 3. Compute & Application
aws cloudformation create-stack \
  --stack-name concert-platform-compute-development \
  --template-body file://cloudformation/03-compute-application.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=development \
    ParameterKey=NetworkStackName,ParameterValue=concert-platform-networking-development \
    ParameterKey=StorageStackName,ParameterValue=concert-platform-storage-development \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Continue with remaining stacks...
```

## Stack Details

### 1. Networking Stack

**Template**: `01-networking.yaml`

**Resources Created**:
- VPC with DNS support
- 2 public subnets (across AZs)
- 2 private subnets (across AZs)
- Internet Gateway
- NAT Gateway with Elastic IP
- Route tables and associations
- Security groups for Lambda, Redshift, API Gateway
- S3 VPC Endpoint (Gateway)

**Parameters**:
- `Environment`: development, staging, or production
- `VpcCidr`: VPC CIDR block (default: 10.0.0.0/16)
- `PublicSubnet1Cidr`: Public subnet 1 CIDR (default: 10.0.1.0/24)
- `PublicSubnet2Cidr`: Public subnet 2 CIDR (default: 10.0.2.0/24)
- `PrivateSubnet1Cidr`: Private subnet 1 CIDR (default: 10.0.10.0/24)
- `PrivateSubnet2Cidr`: Private subnet 2 CIDR (default: 10.0.11.0/24)

**Outputs**:
- VPC ID
- Subnet IDs (public and private)
- Security Group IDs
- NAT Gateway ID

### 2. Storage & Processing Stack

**Template**: `02-storage-processing.yaml`

**Resources Created**:
- S3 buckets:
  - Raw data bucket (with lifecycle policies)
  - Processed data bucket
  - Model artifacts bucket
  - Lambda deployment bucket
- Kinesis Data Streams:
  - Concert events stream
  - Artist data stream
  - Venue data stream
- AWS Glue:
  - Glue database
  - Glue service role
- Redshift Serverless:
  - Namespace
  - Workgroup
  - Service role
  - Subnet group

**Parameters**:
- `Environment`: Environment name
- `NetworkStackName`: Name of networking stack (for imports)
- `RedshiftMasterUsername`: Redshift admin username (default: admin)
- `RedshiftMasterPassword`: Redshift admin password (required)
- `RedshiftNodeType`: Node type (default: ra3.xlplus)

**Outputs**:
- S3 bucket names
- Kinesis stream names
- Glue database name
- Redshift namespace and workgroup names
- IAM role ARNs

### 3. Compute & Application Stack

**Template**: `03-compute-application.yaml`

**Resources Created**:
- IAM roles:
  - Lambda execution role
  - SageMaker execution role
- Lambda functions:
  - Chatbot handler
  - Venue popularity handler
  - Ticket prediction handler
  - Recommendations handler
  - Health check handler
- Lambda layer for shared dependencies
- DynamoDB table for conversation history
- API Gateway:
  - REST API
  - Resources and methods
  - Deployment and stage
  - Lambda permissions

**Parameters**:
- `Environment`: Environment name
- `NetworkStackName`: Networking stack name
- `StorageStackName`: Storage stack name
- `BedrockAgentId`: Bedrock Agent ID (optional)
- `BedrockAgentAliasId`: Bedrock Agent Alias ID (optional)

**Outputs**:
- Lambda function ARNs
- IAM role ARNs
- DynamoDB table name
- API Gateway ID and endpoint URL

### 4. Chatbot Infrastructure Stack

**Template**: `04-chatbot-infrastructure.yaml`

**Resources Created**:
- DynamoDB tables:
  - User preferences table
  - Session state table
- Lambda functions:
  - Chatbot maintenance function
  - Conversation analytics function
- EventBridge rules:
  - Daily maintenance schedule
  - Hourly analytics schedule
- SNS topic for chatbot alerts
- CloudWatch alarm for high error rate

**Parameters**:
- `Environment`: Environment name
- `NetworkStackName`: Networking stack name
- `ComputeStackName`: Compute stack name
- `BedrockAgentId`: Bedrock Agent ID (optional)
- `BedrockAgentAliasId`: Bedrock Agent Alias ID (optional)

**Outputs**:
- DynamoDB table names
- Lambda function ARNs
- SNS topic ARN

### 5. Monitoring & Observability Stack

**Template**: `05-monitoring-observability.yaml`

**Resources Created**:
- SNS topics:
  - Critical alerts topic
  - Warning alerts topic
- CloudWatch alarms:
  - Lambda errors, throttles, duration
  - API Gateway 5xx, 4xx, latency
  - Kinesis iterator age, throttles
  - DynamoDB errors, throttles
- CloudWatch dashboards:
  - Data pipeline dashboard
  - ML models dashboard
  - Chatbot dashboard
  - API Gateway dashboard

**Parameters**:
- `Environment`: Environment name
- `ComputeStackName`: Compute stack name
- `StorageStackName`: Storage stack name
- `AlertEmail`: Email for alarm notifications (optional)

**Outputs**:
- SNS topic ARNs
- Dashboard URLs

### 6. Tracing & Logging Stack

**Template**: `06-tracing-logging.yaml`

**Resources Created**:
- CloudWatch Log Groups (with retention):
  - Lambda function logs
  - API Gateway logs
  - Glue job logs
- Log metric filters:
  - Error tracking
  - Latency monitoring
  - Data quality issues
- CloudWatch Insights queries:
  - Error analysis
  - Conversation stats
  - Latency analysis
  - Cold start tracking
- X-Ray:
  - Sampling rule
  - X-Ray group
  - X-Ray SDK Lambda layer
- Lambda function for error processing
- Log subscription filters

**Parameters**:
- `Environment`: Environment name
- `ComputeStackName`: Compute stack name
- `LogRetentionDays`: Log retention period (default: 7 days)

**Outputs**:
- Log group names
- X-Ray group name
- X-Ray SDK layer ARN
- Error processing function ARN

## Post-Deployment Steps

### 1. Upload Lambda Deployment Packages

Before Lambda functions can execute, upload deployment packages:

```bash
# Package Lambda functions
cd src/infrastructure
zip -r ../../build/api-handlers.zip api_lambda_handlers.py

# Upload to S3
aws s3 cp build/api-handlers.zip \
  s3://concert-lambda-deployment-development-<account-id>/functions/

# Update Lambda functions
aws lambda update-function-code \
  --function-name concert-api-chatbot-development \
  --s3-bucket concert-lambda-deployment-development-<account-id> \
  --s3-key functions/api-handlers.zip
```

### 2. Initialize Redshift Schema

Run the schema initialization script:

```bash
python infrastructure/initialize_redshift_schema.py \
  --environment development \
  --region us-east-1
```

### 3. Configure API Gateway Logging

Enable CloudWatch logging for API Gateway:

```bash
aws apigateway update-stage \
  --rest-api-id <api-id> \
  --stage-name development \
  --patch-operations \
    op=replace,path=/accessLogSettings/destinationArn,value=<log-group-arn> \
    op=replace,path=/accessLogSettings/format,value='$context.requestId'
```

### 4. Subscribe to SNS Topics

If you didn't provide an email during deployment:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:<account-id>:concert-critical-alerts-development \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### 5. Enable X-Ray Tracing

Update Lambda functions to enable X-Ray:

```bash
aws lambda update-function-configuration \
  --function-name concert-api-chatbot-development \
  --tracing-config Mode=Active
```

## Stack Updates

To update an existing stack:

```bash
aws cloudformation update-stack \
  --stack-name concert-platform-networking-development \
  --template-body file://cloudformation/01-networking.yaml \
  --parameters ParameterKey=Environment,ParameterValue=development \
  --region us-east-1
```

Or use the deployment script which handles updates automatically.

## Stack Deletion

Delete stacks in reverse order:

```bash
# Delete in reverse order
aws cloudformation delete-stack --stack-name concert-platform-logging-development
aws cloudformation delete-stack --stack-name concert-platform-monitoring-development
aws cloudformation delete-stack --stack-name concert-platform-chatbot-development
aws cloudformation delete-stack --stack-name concert-platform-compute-development
aws cloudformation delete-stack --stack-name concert-platform-storage-development
aws cloudformation delete-stack --stack-name concert-platform-networking-development
```

**Note**: Empty S3 buckets before deleting the storage stack.

## Troubleshooting

### Stack Creation Fails

Check CloudFormation events:

```bash
aws cloudformation describe-stack-events \
  --stack-name concert-platform-networking-development \
  --max-items 20
```

### Lambda Functions Not Working

1. Check Lambda logs in CloudWatch
2. Verify IAM role permissions
3. Ensure VPC configuration is correct
4. Check security group rules

### API Gateway 5xx Errors

1. Check Lambda function logs
2. Verify Lambda permissions for API Gateway
3. Test Lambda function directly
4. Check API Gateway integration configuration

### Redshift Connection Issues

1. Verify security group allows inbound on port 5439
2. Check VPC and subnet configuration
3. Verify Redshift is publicly accessible (if needed)
4. Check IAM role for Redshift

## Cost Optimization

### Development Environment

- Use smaller Redshift node types
- Reduce Kinesis shard count
- Set shorter log retention periods
- Use on-demand DynamoDB billing

### Production Environment

- Use reserved capacity for Redshift
- Enable S3 lifecycle policies
- Use provisioned DynamoDB capacity
- Implement auto-scaling for Lambda

## Security Best Practices

1. **Restrict Redshift Access**: Update security group to allow only specific IPs
2. **Enable Encryption**: All S3 buckets use AES256 encryption
3. **Use Secrets Manager**: Store Redshift password in Secrets Manager
4. **Enable MFA Delete**: For S3 buckets in production
5. **Review IAM Policies**: Follow principle of least privilege
6. **Enable CloudTrail**: For audit logging
7. **Use VPC Endpoints**: Reduce data transfer costs and improve security

## Monitoring

Access CloudWatch dashboards:

1. Data Pipeline: Monitor ingestion, ETL, and data quality
2. ML Models: Track prediction latency and accuracy
3. Chatbot: Monitor response times and conversation volume
4. API Gateway: Track request rates, errors, and latency

## Support

For issues or questions:
- Check CloudWatch Logs for error details
- Review CloudFormation stack events
- Consult AWS documentation
- Contact platform team
