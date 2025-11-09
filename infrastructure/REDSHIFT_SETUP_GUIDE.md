# Redshift Data Warehouse Setup Guide

This guide will help you set up and configure the Amazon Redshift data warehouse for the concert data platform.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Python 3.8+** with required dependencies
4. **Network access** to create VPC resources

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
chmod +x infrastructure/redshift_setup.sh
./infrastructure/redshift_setup.sh
```

This script will:
- Create an IAM role for Redshift with S3 access
- Set up VPC subnet groups
- Create security groups with appropriate rules
- Launch a Redshift cluster
- Save credentials to `redshift_credentials.txt`

### Option 2: Manual Setup

If you prefer manual setup or need custom configuration, follow these steps:

#### Step 1: Create IAM Role

Create an IAM role that allows Redshift to access S3:

```bash
aws iam create-role \
  --role-name RedshiftS3AccessRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "redshift.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name RedshiftS3AccessRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

#### Step 2: Create Redshift Cluster

```bash
aws redshift create-cluster \
  --cluster-identifier concert-data-warehouse \
  --node-type dc2.large \
  --master-username admin \
  --master-user-password <YOUR_SECURE_PASSWORD> \
  --db-name concerts \
  --cluster-type multi-node \
  --number-of-nodes 2 \
  --publicly-accessible \
  --iam-roles <IAM_ROLE_ARN>
```

#### Step 3: Wait for Cluster to be Available

```bash
aws redshift wait cluster-available \
  --cluster-identifier concert-data-warehouse
```

#### Step 4: Get Cluster Endpoint

```bash
aws redshift describe-clusters \
  --cluster-identifier concert-data-warehouse \
  --query 'Clusters[0].Endpoint.Address' \
  --output text
```

## Configuration

### Environment Variables

Create or update your `.env` file with the Redshift credentials:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

# Redshift Configuration
AWS_REDSHIFT_HOST=<cluster-endpoint>.redshift.amazonaws.com
AWS_REDSHIFT_PORT=5439
AWS_REDSHIFT_DATABASE=concerts
AWS_REDSHIFT_USER=admin
AWS_REDSHIFT_PASSWORD=<your-password>
AWS_REDSHIFT_CLUSTER_IDENTIFIER=concert-data-warehouse

# S3 Buckets
AWS_S3_BUCKET_RAW=concert-data-raw
AWS_S3_BUCKET_PROCESSED=concert-data-processed

# IAM Role for COPY operations
AWS_SAGEMAKER_EXECUTION_ROLE=arn:aws:iam::<account-id>:role/RedshiftS3AccessRole
```

### Security Group Configuration

Ensure your security group allows inbound traffic on port 5439 from your IP:

```bash
aws ec2 authorize-security-group-ingress \
  --group-id <security-group-id> \
  --protocol tcp \
  --port 5439 \
  --cidr <your-ip>/32
```

## Initialize Schema

After the cluster is available and configured, initialize the database schema:

```bash
python infrastructure/initialize_redshift_schema.py
```

This will create:
- Schema: `concert_dw`
- Tables: `artists`, `venues`, `concerts`, `ticket_sales`, `venue_popularity`, `artist_performance`, `daily_sales_summary`
- Stored procedures for analytics

## Verify Setup

Test the connection using psql:

```bash
psql -h <cluster-endpoint> -p 5439 -U admin -d concerts
```

Or use Python:

```python
from src.services.redshift_service import RedshiftService

service = RedshiftService()
status = service.get_data_warehouse_status()
print(status)
```

## Data Loading

### Load Data from S3

```python
from src.services.redshift_service import RedshiftService

service = RedshiftService()

# Define S3 paths
data_sources = {
    'artists': 's3://concert-data-processed/artists/',
    'venues': 's3://concert-data-processed/venues/',
    'concerts': 's3://concert-data-processed/concerts/',
    'ticket_sales': 's3://concert-data-processed/ticket_sales/'
}

# Load data
results = service.load_data_from_s3(data_sources)
print(results)
```

### Run Analytics

```python
# Calculate analytics
analytics_results = service.run_analytics_calculations()

# Get insights
top_venues = service.get_venue_insights(limit=10)
trending_artists = service.get_artist_insights(limit=20, trend_filter='growing')
revenue_data = service.get_revenue_analytics(period='month')
```

## Table Schema

### Dimension Tables

#### artists
- Distribution: EVEN
- Sort Key: name, popularity_score DESC
- Columns: artist_id, name, genre, popularity_score, formation_date, members, spotify_id

#### venues
- Distribution: EVEN
- Sort Key: city, capacity DESC
- Columns: venue_id, name, address, city, state, country, capacity, venue_type, amenities

### Fact Tables

#### concerts
- Distribution: DISTKEY(artist_id)
- Sort Key: event_date DESC, artist_id
- Columns: concert_id, artist_id, venue_id, event_date, ticket_prices, total_attendance, revenue, status

#### ticket_sales
- Distribution: DISTKEY(concert_id)
- Sort Key: purchase_timestamp DESC, concert_id
- Columns: sale_id, concert_id, price_tier, quantity, unit_price, total_amount, purchase_timestamp, customer_segment

### Analytics Tables

#### venue_popularity
- Stores calculated venue performance metrics
- Updated by stored procedure

#### artist_performance
- Stores calculated artist engagement metrics
- Updated by stored procedure

#### daily_sales_summary
- Aggregated daily sales data
- Updated by stored procedure

## Stored Procedures

### Analytics Procedures

1. **calculate_venue_popularity()** - Calculates venue performance metrics
2. **calculate_artist_performance()** - Calculates artist engagement scores
3. **generate_daily_sales_summary(date)** - Generates daily sales aggregations

### Query Functions

1. **get_top_venues(limit, days)** - Returns top performing venues
2. **get_artist_trends(limit, trend_filter)** - Returns artist performance trends
3. **get_revenue_analytics(start_date, end_date, period)** - Returns revenue analytics

## Maintenance

### Optimize Tables

Run VACUUM and ANALYZE regularly:

```python
service = RedshiftService()
results = service.optimize_tables()
```

### Cleanup Old Analytics

Remove old analytics data:

```python
service.cleanup_old_analytics(days_to_keep=30)
```

### Monitor Health

Check data warehouse health:

```python
status = service.get_data_warehouse_status()
print(status)
```

## Cost Optimization

### Cluster Sizing

- **Development**: dc2.large with 1-2 nodes (~$0.25/hour per node)
- **Production**: dc2.large with 2-4 nodes or ra3.xlplus for larger datasets

### Pause/Resume Cluster

Pause cluster when not in use:

```bash
aws redshift pause-cluster --cluster-identifier concert-data-warehouse
```

Resume cluster:

```bash
aws redshift resume-cluster --cluster-identifier concert-data-warehouse
```

### Delete Cluster

When done testing:

```bash
aws redshift delete-cluster \
  --cluster-identifier concert-data-warehouse \
  --skip-final-cluster-snapshot
```

## Troubleshooting

### Connection Issues

1. **Check security group**: Ensure port 5439 is open from your IP
2. **Verify cluster status**: `aws redshift describe-clusters --cluster-identifier concert-data-warehouse`
3. **Check VPC settings**: Ensure cluster is publicly accessible or you're connecting from within VPC

### Data Loading Issues

1. **Check IAM role**: Ensure Redshift has S3 access
2. **Verify S3 paths**: Ensure data exists at specified paths
3. **Check COPY errors**: Query `stl_load_errors` table

```sql
SELECT * FROM stl_load_errors 
WHERE starttime >= DATEADD(hour, -1, GETDATE())
ORDER BY starttime DESC;
```

### Performance Issues

1. **Run ANALYZE**: Update table statistics
2. **Run VACUUM**: Reclaim space and sort data
3. **Check query execution**: Use `EXPLAIN` to analyze queries
4. **Review distribution keys**: Ensure optimal data distribution

## Security Best Practices

1. **Use strong passwords**: Generate secure passwords for master user
2. **Rotate credentials**: Regularly update passwords
3. **Use IAM authentication**: Consider using IAM database authentication
4. **Encrypt data**: Enable encryption at rest and in transit
5. **Restrict access**: Use security groups to limit access
6. **Audit access**: Enable CloudTrail logging for Redshift

## Additional Resources

- [Amazon Redshift Documentation](https://docs.aws.amazon.com/redshift/)
- [Redshift Best Practices](https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html)
- [Redshift SQL Reference](https://docs.aws.amazon.com/redshift/latest/dg/c_SQL_commands.html)
- [Redshift Performance Tuning](https://docs.aws.amazon.com/redshift/latest/dg/c-optimizing-query-performance.html)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS Redshift documentation
3. Check application logs for detailed error messages
4. Contact your AWS support team for infrastructure issues
