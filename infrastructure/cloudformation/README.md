# CloudFormation Templates

Infrastructure as Code templates for the Concert Data Platform.

## Templates

1. **01-networking.yaml** - VPC, subnets, security groups, NAT gateway
2. **02-storage-processing.yaml** - S3, Redshift, Glue, Kinesis
3. **03-compute-application.yaml** - Lambda, API Gateway, DynamoDB
4. **04-chatbot-infrastructure.yaml** - Chatbot resources, EventBridge
5. **05-monitoring-observability.yaml** - CloudWatch dashboards and alarms
6. **06-tracing-logging.yaml** - X-Ray, CloudWatch Logs

## Deployment

### Quick Start

```bash
cd infrastructure
./deploy_cloudformation_stacks.sh development us-east-1
```

### Manual Deployment

Deploy stacks in order using AWS CLI:

```bash
aws cloudformation create-stack \
  --stack-name concert-platform-networking-development \
  --template-body file://cloudformation/01-networking.yaml \
  --parameters ParameterKey=Environment,ParameterValue=development \
  --region us-east-1
```

## Validation

Validate all templates before deployment:

```bash
python validate_cloudformation_templates.py
```

## Documentation

See comprehensive deployment guide:
- [CloudFormation Deployment Guide](../../docs/infrastructure/CLOUDFORMATION_DEPLOYMENT_GUIDE.md)
- [Infrastructure as Code Summary](../../docs/infrastructure/INFRASTRUCTURE_AS_CODE_SUMMARY.md)

## Stack Dependencies

```
Networking → Storage & Processing → Compute & Application → Chatbot → Monitoring → Logging
```

## Parameters

All templates support:
- `Environment`: development, staging, production

Additional parameters vary by template. See individual template files for details.

## Outputs

Each stack exports values for use by dependent stacks via CloudFormation exports.

## Support

For issues or questions, see the troubleshooting section in the deployment guide.
