# Redshift Data Warehouse Documentation

Documentation for Amazon Redshift setup, configuration, and data warehouse operations.

## 📄 Documents

### Quick Start
- **[Redshift Quickstart](REDSHIFT_QUICKSTART.md)** ⭐ **START HERE**
  - Quick setup guide
  - Essential commands
  - Connection instructions

### Deployment Guides
- **[Redshift Deployment Checklist](REDSHIFT_DEPLOYMENT_CHECKLIST.md)**
  - Pre-deployment checklist
  - Required resources
  - Configuration steps
  - Verification procedures

- **[Redshift Deployment Summary](REDSHIFT_DEPLOYMENT_SUMMARY.md)**
  - Deployment overview
  - Architecture details
  - Post-deployment steps

### Detailed Setup
- **[Redshift Setup Guide](../../infrastructure/REDSHIFT_SETUP_GUIDE.md)**
  - Complete setup instructions
  - Schema creation
  - Data loading
  - Query optimization

## 🚀 Quick Setup

### Option 1: Automated Script

```bash
./infrastructure/redshift_setup.sh
```

### Option 2: CloudFormation

```bash
aws cloudformation create-stack \
    --stack-name concert-data-redshift \
    --template-body file://infrastructure/redshift_cloudformation.yaml \
    --parameters ParameterKey=MasterUsername,ParameterValue=admin \
                 ParameterKey=MasterUserPassword,ParameterValue=YourPassword123
```

### Option 3: Initialize Schema

```bash
python infrastructure/initialize_redshift_schema.py
```

## 📊 Cluster Configuration

- **Cluster Type**: dc2.large
- **Nodes**: 1 (development) / 2+ (production)
- **Database**: concerts
- **Port**: 5439
- **Encryption**: Enabled

## 🗄️ Schema

### Tables
- `artists` - Artist information
- `venues` - Venue details
- `concerts` - Concert events
- `ticket_sales` - Sales transactions
- `venue_popularity` - Aggregated metrics

### Views
- `concert_analytics` - Concert insights
- `venue_performance` - Venue metrics
- `artist_trends` - Artist popularity trends

## 💰 Cost

### Development
- **dc2.large (1 node)**: ~$180/month
- **Storage**: ~$0.024/GB/month
- **Backup**: Included

### Production
- **dc2.large (2 nodes)**: ~$360/month
- **Reserved Instances**: 30-75% savings

## 🔍 Connection

### Using psql

```bash
psql -h your-cluster.redshift.amazonaws.com \
     -U admin \
     -d concerts \
     -p 5439
```

### Using Python

```python
from src.services.redshift_service import RedshiftService

redshift = RedshiftService()
results = redshift.execute_query("SELECT * FROM artists LIMIT 10")
```

## 📈 Monitoring

### CloudWatch Metrics
- **CPUUtilization**: Cluster CPU usage
- **DatabaseConnections**: Active connections
- **PercentageDiskSpaceUsed**: Storage utilization
- **QueryDuration**: Query performance

### Query Monitoring
```sql
-- View running queries
SELECT * FROM STV_RECENTS WHERE status = 'Running';

-- View query performance
SELECT * FROM STL_QUERY ORDER BY starttime DESC LIMIT 10;
```

## 🔗 Related Documentation

- [API Ingestion](../api-ingestion/PRODUCTION_INGESTION_FIXED.md) - Data source
- [Kinesis Setup](../kinesis/KINESIS_QUICKSTART.md) - Streaming data
- [Main Documentation](../README.md) - Full documentation index

## 🆘 Troubleshooting

### Connection Failed
```bash
# Check security group
aws redshift describe-clusters \
    --cluster-identifier concert-data-warehouse \
    --query 'Clusters[0].VpcSecurityGroups'

# Test connection
telnet your-cluster.redshift.amazonaws.com 5439
```

### Slow Queries
```sql
-- Analyze table statistics
ANALYZE artists;

-- Vacuum tables
VACUUM concerts;

-- Check query execution plan
EXPLAIN SELECT * FROM concerts WHERE event_date > '2024-01-01';
```

### Storage Full
```bash
# Check disk usage
SELECT * FROM STV_PARTITIONS;

# Drop old data or resize cluster
```

## ✅ Success Checklist

- ✅ Cluster created and available
- ✅ Security groups configured
- ✅ Schema initialized
- ✅ Sample data loaded
- ✅ Queries executing successfully
- ✅ Monitoring enabled

## 📚 Example Queries

### Top Artists by Popularity
```sql
SELECT name, popularity_score, genre
FROM artists
ORDER BY popularity_score DESC
LIMIT 10;
```

### Upcoming Concerts
```sql
SELECT c.event_date, a.name as artist, v.name as venue
FROM concerts c
JOIN artists a ON c.artist_id = a.artist_id
JOIN venues v ON c.venue_id = v.venue_id
WHERE c.event_date > CURRENT_DATE
ORDER BY c.event_date;
```

### Venue Revenue
```sql
SELECT v.name, SUM(c.revenue) as total_revenue
FROM venues v
JOIN concerts c ON v.venue_id = c.venue_id
GROUP BY v.name
ORDER BY total_revenue DESC;
```

---

[← Back to Main Documentation](../README.md)