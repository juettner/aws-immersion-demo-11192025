# Redshift Deployment Checklist

Use this checklist to ensure a smooth deployment of your Redshift data warehouse.

## Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS account created and active
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Appropriate IAM permissions for:
  - [ ] Redshift cluster creation
  - [ ] VPC and networking resources
  - [ ] IAM role creation
  - [ ] S3 access

### Local Environment
- [ ] Python 3.8+ installed (`python --version`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Git repository cloned
- [ ] `.env` file created (copy from `.env.example` if available)

### Cost Awareness
- [ ] Understand Redshift pricing (~$0.25/hour per dc2.large node)
- [ ] Plan to pause cluster when not in use
- [ ] Set up billing alerts in AWS Console

## Deployment Steps

### Step 1: Choose Deployment Method

**Option A: CloudFormation (Recommended)**
- [ ] Review `infrastructure/redshift_cloudformation.yaml`
- [ ] Make script executable: `chmod +x infrastructure/deploy_redshift_cloudformation.sh`
- [ ] Run deployment: `./infrastructure/deploy_redshift_cloudformation.sh`
- [ ] Wait for completion (~10-15 minutes)
- [ ] Save credentials from `redshift_cloudformation_credentials.txt`

**Option B: Quick Setup Script**
- [ ] Review `infrastructure/redshift_setup.sh`
- [ ] Make script executable: `chmod +x infrastructure/redshift_setup.sh`
- [ ] Run deployment: `./infrastructure/redshift_setup.sh`
- [ ] Wait for completion (~5-10 minutes)
- [ ] Save credentials from `redshift_credentials.txt`

### Step 2: Configure Environment
- [ ] Copy credentials to `.env` file
- [ ] Verify all required variables are set:
  ```bash
  AWS_REGION
  AWS_REDSHIFT_HOST
  AWS_REDSHIFT_PORT
  AWS_REDSHIFT_DATABASE
  AWS_REDSHIFT_USER
  AWS_REDSHIFT_PASSWORD
  AWS_SAGEMAKER_EXECUTION_ROLE
  ```
- [ ] Test environment variables: `python -c "from src.config.settings import get_settings; print(get_settings().redshift_host)"`

### Step 3: Initialize Schema
- [ ] Make script executable: `chmod +x infrastructure/initialize_redshift_schema.py`
- [ ] Run initialization: `python infrastructure/initialize_redshift_schema.py`
- [ ] Verify success messages:
  - [ ] ✓ schema_created: Success
  - [ ] ✓ tables_created: Success
  - [ ] ✓ procedures_created: Success

### Step 4: Verify Deployment
- [ ] Test connection with psql (optional):
  ```bash
  psql -h <endpoint> -p 5439 -U admin -d concerts
  ```
- [ ] Run validation script: `python validate_redshift_structure.py`
- [ ] Test Python connection:
  ```python
  from src.services.redshift_service import RedshiftService
  service = RedshiftService()
  status = service.get_data_warehouse_status()
  print(status)
  ```

## Post-Deployment Checklist

### Security
- [ ] Credentials saved securely (not in version control)
- [ ] Security group reviewed and restricted to necessary IPs
- [ ] IAM roles have minimal required permissions
- [ ] Encryption verified (at-rest and in-transit)

### Monitoring
- [ ] CloudWatch alarms configured (if using CloudFormation)
- [ ] Billing alerts set up
- [ ] Query monitoring enabled
- [ ] Bookmark Redshift console URL

### Documentation
- [ ] Team members have access to credentials (via secure method)
- [ ] Connection details documented
- [ ] Deployment date and configuration recorded
- [ ] Maintenance schedule planned

### Testing
- [ ] Schema validated
- [ ] Sample queries tested
- [ ] Data loading tested (if data available)
- [ ] Analytics procedures tested
- [ ] Performance benchmarked

## Optional: Data Loading

If you have data ready to load:

- [ ] S3 buckets created and accessible
- [ ] Data formatted correctly (JSON or CSV)
- [ ] IAM role has S3 read permissions
- [ ] Test data loading with small dataset:
  ```python
  service = RedshiftService()
  results = service.load_data_from_s3({
      'artists': 's3://your-bucket/artists/'
  })
  ```
- [ ] Verify data loaded correctly
- [ ] Run analytics calculations
- [ ] Test query performance

## Maintenance Setup

### Daily Tasks
- [ ] Set up automated monitoring
- [ ] Configure log aggregation
- [ ] Set up alerting for errors

### Weekly Tasks
- [ ] Schedule ANALYZE operations
- [ ] Review query performance
- [ ] Check disk space usage

### Monthly Tasks
- [ ] Schedule VACUUM operations
- [ ] Clean up old analytics data
- [ ] Review and optimize queries
- [ ] Update documentation

## Cost Management

- [ ] Understand current cluster cost
- [ ] Set up cost alerts
- [ ] Plan pause/resume schedule
- [ ] Consider reserved instances for production
- [ ] Document cost optimization strategies

## Cleanup (When Done Testing)

If you need to tear down the environment:

### CloudFormation Deployment
- [ ] Delete stack: `aws cloudformation delete-stack --stack-name concert-redshift-stack`
- [ ] Verify deletion complete
- [ ] Check for any remaining resources

### Manual Deployment
- [ ] Delete cluster: `aws redshift delete-cluster --cluster-identifier concert-data-warehouse --skip-final-cluster-snapshot`
- [ ] Delete IAM role
- [ ] Delete security groups
- [ ] Delete subnet groups
- [ ] Verify all resources deleted

## Troubleshooting Checklist

If something goes wrong:

### Connection Issues
- [ ] Cluster status is "available"
- [ ] Security group allows your IP on port 5439
- [ ] Credentials are correct
- [ ] VPC and subnet configuration correct
- [ ] DNS resolution working

### Schema Initialization Issues
- [ ] Python dependencies installed
- [ ] Environment variables set correctly
- [ ] Database connection successful
- [ ] Sufficient permissions
- [ ] Check error logs

### Data Loading Issues
- [ ] IAM role has S3 access
- [ ] S3 paths are correct
- [ ] Data format is valid
- [ ] Check `stl_load_errors` table
- [ ] Verify COPY command syntax

### Performance Issues
- [ ] ANALYZE run on tables
- [ ] VACUUM run on tables
- [ ] Distribution keys optimal
- [ ] Sort keys appropriate
- [ ] Query plans reviewed

## Success Criteria

Your deployment is successful when:

- [ ] ✅ Cluster is running and accessible
- [ ] ✅ All tables created successfully
- [ ] ✅ All stored procedures created
- [ ] ✅ Can connect from Python application
- [ ] ✅ Can run sample queries
- [ ] ✅ Analytics procedures execute successfully
- [ ] ✅ Monitoring is in place
- [ ] ✅ Team has access to documentation
- [ ] ✅ Cost management plan in place

## Next Steps After Deployment

1. **Integrate with Application**
   - [ ] Update application code to use RedshiftService
   - [ ] Test end-to-end data flow
   - [ ] Implement error handling

2. **Load Production Data**
   - [ ] Prepare data in S3
   - [ ] Test with sample data first
   - [ ] Load full dataset
   - [ ] Verify data integrity

3. **Build Analytics**
   - [ ] Create custom queries
   - [ ] Build dashboards
   - [ ] Set up scheduled analytics
   - [ ] Share insights with team

4. **Optimize Performance**
   - [ ] Monitor query performance
   - [ ] Optimize slow queries
   - [ ] Adjust distribution keys if needed
   - [ ] Fine-tune cluster size

## Resources

- **Quick Start:** [REDSHIFT_QUICKSTART.md](REDSHIFT_QUICKSTART.md)
- **Detailed Guide:** [infrastructure/REDSHIFT_SETUP_GUIDE.md](infrastructure/REDSHIFT_SETUP_GUIDE.md)
- **Summary:** [REDSHIFT_DEPLOYMENT_SUMMARY.md](REDSHIFT_DEPLOYMENT_SUMMARY.md)
- **AWS Docs:** https://docs.aws.amazon.com/redshift/

---

**Ready to start?** Begin with the Pre-Deployment Checklist above! ✅
