# Infrastructure Setup

This directory contains scripts and templates for setting up the AWS infrastructure for the Concert Data Platform.

## Quick Start - Redshift Setup

Choose one of the following methods to set up your Redshift data warehouse:

### Method 1: CloudFormation (Recommended for Production)

CloudFormation provides infrastructure-as-code with automatic rollback and easier management.

```bash
# Make script executable
chmod +x infrastructure/deploy_redshift_cloudformation.sh

# Deploy the stack
./infrastructure/deploy_redshift_cloudformation.sh
```

This will:
- Create a complete VPC with subnets and security groups
- Deploy a Redshift cluster with encryption enabled
- Set up IAM roles for S3 access
- Configure CloudWatch alarms for monitoring
- Save credentials to `redshift_cloudformation_credentials.txt`

### Method 2: Bash Script (Quick Setup)

For quick testing or development environments:

```bash
# Make script executable
chmod +x infrastructure/redshift_setup.sh

# Run the setup
./infrastructure/redshift_setup.sh
```

This will:
- Use your default VPC
- Create necessary IAM roles and security groups
- Launch a Redshift cluster
- Save credentials to `redshift_credentials.txt`

## After Deployment

### 1. Update Environment Variables

Copy the credentials from the generated file to your `.env`:

```bash
# From CloudFormation deployment
cat redshift_cloudformation_credentials.txt >> .env

# OR from bash script deployment
cat redshift_credentials.txt >> .env
```

### 2. Initialize Database Schema

Run the initialization script to create tables and stored procedures:

```bash
python infrastructure/initialize_redshift_schema.py
```

This will create:
- Schema: `concert_dw`
- 7 tables with optimized distribution keys
- 6 stored procedures for analytics

### 3. Verify Setup

Test the connection:

```python
from src.services.redshift_service import RedshiftService

service = RedshiftService()
status = service.get_data_warehouse_status()
print(status)
```

## Configuration Files

- **redshift_setup.sh** - Automated bash script for quick setup
- **deploy_redshift_cloudformation.sh** - CloudFormation deployment script
- **redshift_cloudformation.yaml** - CloudFormation template
- **initialize_redshift_schema.py** - Database schema initialization
- **REDSHIFT_SETUP_GUIDE.md** - Comprehensive setup and usage guide

## Environment Variables

Required environment variables for Redshift:

```bash
AWS_REGION=us-east-1
AWS_REDSHIFT_HOST=<cluster-endpoint>
AWS_REDSHIFT_PORT=5439
AWS_REDSHIFT_DATABASE=concerts
AWS_REDSHIFT_USER=admin
AWS_REDSHIFT_PASSWORD=<secure-password>
AWS_SAGEMAKER_EXECUTION_ROLE=<iam-role-arn>
```

## Cost Estimates

### Development Environment
- **ra3.xlplus** (2 nodes): ~$2.60/hour (~$1,872/month)
- Pause cluster when not in use to save costs

### Production Environment
- **ra3.xlplus** (4 nodes): ~$5.20/hour (~$3,744/month)
- **ra3.4xlarge** (2 nodes): ~$6.52/hour (~$4,694/month)

## Cleanup

### Delete CloudFormation Stack

```bash
aws cloudformation delete-stack \
  --stack-name concert-redshift-stack \
  --region us-east-1
```

### Delete Manually Created Resources

```bash
# Delete cluster
aws redshift delete-cluster \
  --cluster-identifier concert-data-warehouse \
  --skip-final-cluster-snapshot

# Delete IAM role
aws iam detach-role-policy \
  --role-name RedshiftS3AccessRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam delete-role --role-name RedshiftS3AccessRole
```

## Troubleshooting

### Connection Issues

1. Check security group allows your IP on port 5439
2. Verify cluster is in "available" state
3. Ensure credentials are correct

### Data Loading Issues

1. Verify IAM role has S3 access
2. Check S3 bucket paths are correct
3. Review `stl_load_errors` table in Redshift

### Performance Issues

1. Run ANALYZE on tables after loading data
2. Run VACUUM to reclaim space
3. Review query execution plans with EXPLAIN

## Additional Resources

- [Redshift Setup Guide](./REDSHIFT_SETUP_GUIDE.md) - Detailed setup instructions
- [AWS Redshift Documentation](https://docs.aws.amazon.com/redshift/)
- [Redshift Best Practices](https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html)

## Support

For issues:
1. Check the troubleshooting section in REDSHIFT_SETUP_GUIDE.md
2. Review application logs
3. Check AWS CloudWatch for cluster metrics
4. Consult AWS Redshift documentation
