# Redshift Data Warehouse - Quick Start Guide

Get your Redshift data warehouse up and running in minutes!

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured (`aws configure`)
- Python 3.8+ with dependencies installed (`pip install -r requirements.txt`)

## Step 1: Choose Your Deployment Method

### Option A: CloudFormation (Recommended) ⭐

Best for production environments with full infrastructure-as-code.

```bash
./infrastructure/deploy_redshift_cloudformation.sh
```

**What it does:**
- Creates VPC, subnets, and security groups
- Deploys encrypted Redshift cluster
- Sets up IAM roles and CloudWatch alarms
- Takes ~10-15 minutes

### Option B: Quick Setup Script

Best for quick testing and development.

```bash
./infrastructure/redshift_setup.sh
```

**What it does:**
- Uses your default VPC
- Creates minimal required resources
- Faster deployment (~5-10 minutes)

## Step 2: Configure Environment

After deployment completes, update your `.env` file:

```bash
# Copy credentials from the generated file
cat redshift_cloudformation_credentials.txt >> .env

# Or if you used the bash script:
cat redshift_credentials.txt >> .env
```

Your `.env` should now include:

```bash
AWS_REGION=us-east-1
AWS_REDSHIFT_HOST=concert-data-warehouse.xxxxx.us-east-1.redshift.amazonaws.com
AWS_REDSHIFT_PORT=5439
AWS_REDSHIFT_DATABASE=concerts
AWS_REDSHIFT_USER=admin
AWS_REDSHIFT_PASSWORD=<generated-password>
AWS_SAGEMAKER_EXECUTION_ROLE=arn:aws:iam::xxxxx:role/RedshiftS3AccessRole
```

## Step 3: Initialize Database Schema

Create the tables and stored procedures:

```bash
python infrastructure/initialize_redshift_schema.py
```

**What it creates:**
- Schema: `concert_dw`
- Tables: artists, venues, concerts, ticket_sales, and analytics tables
- Stored procedures: 6 analytics procedures

Expected output:
```
✓ schema_created: Success
✓ tables_created: Success
✓ procedures_created: Success
```

## Step 4: Verify Setup

Test your connection:

```python
from src.services.redshift_service import RedshiftService

service = RedshiftService()
status = service.get_data_warehouse_status()

# Check table status
for table, info in status['tables'].items():
    print(f"{table}: {info['row_count']} rows")
```

## Step 5: Load Data (Optional)

If you have data in S3, load it:

```python
from src.services.redshift_service import RedshiftService

service = RedshiftService()

# Define your S3 paths
data_sources = {
    'artists': 's3://your-bucket/artists/',
    'venues': 's3://your-bucket/venues/',
    'concerts': 's3://your-bucket/concerts/',
    'ticket_sales': 's3://your-bucket/ticket_sales/'
}

# Load data
results = service.load_data_from_s3(data_sources)
print(results)
```

## Step 6: Run Analytics

Calculate analytics and get insights:

```python
# Run analytics calculations
service.run_analytics_calculations()

# Get top venues
top_venues = service.get_venue_insights(limit=10)
for venue in top_venues:
    print(f"{venue['venue_name']}: ${venue['total_revenue']:,.2f}")

# Get trending artists
artists = service.get_artist_insights(limit=10, trend_filter='growing')
for artist in artists:
    print(f"{artist['artist_name']}: {artist['fan_engagement_score']}/10")

# Get revenue analytics
revenue = service.get_revenue_analytics(period='month')
for month in revenue:
    print(f"{month['period_start']}: ${month['total_revenue']:,.2f}")
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Redshift Cluster                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Schema: concert_dw                     │ │
│  │                                                     │ │
│  │  Dimension Tables:                                  │ │
│  │  • artists (DISTSTYLE EVEN)                        │ │
│  │  • venues (DISTSTYLE EVEN)                         │ │
│  │                                                     │ │
│  │  Fact Tables:                                       │ │
│  │  • concerts (DISTKEY artist_id)                    │ │
│  │  • ticket_sales (DISTKEY concert_id)               │ │
│  │                                                     │ │
│  │  Analytics Tables:                                  │ │
│  │  • venue_popularity                                 │ │
│  │  • artist_performance                               │ │
│  │  • daily_sales_summary                              │ │
│  │                                                     │ │
│  │  Stored Procedures:                                 │ │
│  │  • calculate_venue_popularity()                     │ │
│  │  • calculate_artist_performance()                   │ │
│  │  • generate_daily_sales_summary()                   │ │
│  │  • get_top_venues()                                 │ │
│  │  • get_artist_trends()                              │ │
│  │  • get_revenue_analytics()                          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↑
                          │ COPY commands
                          │
                    ┌─────┴─────┐
                    │  S3 Bucket │
                    └───────────┘
```

## Cost Management

### Pause Cluster When Not in Use

```bash
# Pause
aws redshift pause-cluster --cluster-identifier concert-data-warehouse

# Resume
aws redshift resume-cluster --cluster-identifier concert-data-warehouse
```

### Estimated Costs

- **Development** (2 x dc2.large): ~$0.50/hour (~$12/day if running 24/7)
- **Production** (4 x dc2.large): ~$1.00/hour (~$24/day if running 24/7)

💡 **Tip:** Pause the cluster when not actively using it to save costs!

## Cleanup

When you're done testing:

### CloudFormation Deployment

```bash
aws cloudformation delete-stack \
  --stack-name concert-redshift-stack \
  --region us-east-1
```

### Bash Script Deployment

```bash
aws redshift delete-cluster \
  --cluster-identifier concert-data-warehouse \
  --skip-final-cluster-snapshot \
  --region us-east-1
```

## Troubleshooting

### Can't Connect to Cluster

1. **Check cluster status:**
   ```bash
   aws redshift describe-clusters --cluster-identifier concert-data-warehouse
   ```

2. **Verify security group:**
   - Ensure port 5439 is open from your IP
   - Check VPC security group settings

3. **Test with psql:**
   ```bash
   psql -h <endpoint> -p 5439 -U admin -d concerts
   ```

### Data Loading Fails

1. **Check IAM role permissions:**
   ```bash
   aws iam get-role --role-name RedshiftS3AccessRole
   ```

2. **Verify S3 paths exist:**
   ```bash
   aws s3 ls s3://your-bucket/artists/
   ```

3. **Check COPY errors in Redshift:**
   ```sql
   SELECT * FROM stl_load_errors 
   ORDER BY starttime DESC LIMIT 10;
   ```

### Performance Issues

1. **Run ANALYZE:**
   ```python
   service.optimize_tables()
   ```

2. **Check query performance:**
   ```sql
   SELECT * FROM svl_query_summary 
   WHERE query = <query_id>;
   ```

## Next Steps

1. ✅ Set up Redshift cluster
2. ✅ Initialize schema
3. 📊 Load your data from S3
4. 🔍 Run analytics queries
5. 📈 Build dashboards with your favorite BI tool
6. 🚀 Integrate with your application

## Additional Resources

- [Detailed Setup Guide](infrastructure/REDSHIFT_SETUP_GUIDE.md)
- [Infrastructure README](infrastructure/README.md)
- [AWS Redshift Documentation](https://docs.aws.amazon.com/redshift/)
- [Example Usage](src/services/example_redshift_usage.py)

## Need Help?

- Check the [troubleshooting section](#troubleshooting) above
- Review logs: `tail -f logs/redshift.log`
- Consult [REDSHIFT_SETUP_GUIDE.md](infrastructure/REDSHIFT_SETUP_GUIDE.md)

---

**Ready to get started?** Run one of the deployment scripts above! 🚀
