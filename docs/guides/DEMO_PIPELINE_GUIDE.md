# Demo Pipeline Execution Guide

This guide explains how to execute the end-to-end demo data pipeline for the Concert Data Platform.

## Overview

The demo pipeline consists of two main phases:

1. **Data Pipeline (Task 8.2.1)**: Generate synthetic data, upload to S3, run ETL, load to Redshift, and verify quality
2. **Model Training (Task 8.2.2)**: Extract training data, train ML models, validate predictions, and generate demo scenarios

## Prerequisites

### AWS Configuration

Ensure you have the following AWS resources configured:

- **S3 Buckets**: 
  - `concert-data-raw` (for raw data)
  - `concert-data-processed` (for processed data)
- **Redshift Cluster**: 
  - Database with `concert_dw` schema
  - Tables: artists, venues, concerts, ticket_sales
- **IAM Role**: 
  - Role with permissions for Redshift COPY operations
  - S3 read/write access
- **AWS Credentials**: 
  - Configured via `~/.aws/credentials` or environment variables

### Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your AWS credentials and Redshift connection details
```

### Required Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Redshift Configuration
REDSHIFT_HOST=your-cluster.region.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=concert_db
REDSHIFT_USER=admin
REDSHIFT_PASSWORD=your_password
REDSHIFT_IAM_ROLE=arn:aws:iam::account:role/RedshiftCopyRole
```

## Phase 1: Data Pipeline Execution

### Script: `run_demo_pipeline.py`

This script orchestrates the complete data pipeline from generation to verification.

### Basic Usage

```bash
# Run complete pipeline with default settings
python run_demo_pipeline.py

# Generate smaller dataset for testing
python run_demo_pipeline.py --artists 100 --venues 50 --concerts 500 --sales 2000

# Use existing data in S3 (skip generation)
python run_demo_pipeline.py --skip-generation

# Specify custom S3 buckets
python run_demo_pipeline.py --raw-bucket my-raw-bucket --processed-bucket my-processed-bucket

# Specify IAM role for Redshift COPY
python run_demo_pipeline.py --iam-role arn:aws:iam::123456789012:role/RedshiftCopyRole
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--artists` | Number of artists to generate | 1000 |
| `--venues` | Number of venues to generate | 500 |
| `--concerts` | Number of concerts to generate | 10000 |
| `--sales` | Number of ticket sales to generate | 50000 |
| `--seed` | Random seed for reproducibility | 42 |
| `--skip-generation` | Skip data generation, use existing S3 data | False |
| `--raw-bucket` | S3 bucket for raw data | concert-data-raw |
| `--processed-bucket` | S3 bucket for processed data | concert-data-processed |
| `--iam-role` | IAM role ARN for Redshift COPY | From settings |

### Pipeline Steps

The script executes the following steps:

1. **S3 Bucket Setup**
   - Verifies or creates raw and processed data buckets
   - Configures bucket permissions

2. **Data Generation**
   - Generates synthetic concert data using `SyntheticDataGenerator`
   - Creates artists, venues, concerts, and ticket sales
   - Validates data quality and referential integrity

3. **S3 Upload**
   - Uploads generated data to S3 raw bucket
   - Organizes data by type (artists, venues, concerts, ticket_sales)
   - Stores in JSON format for efficient loading

4. **ETL Processing** (Simplified for Demo)
   - In production: Triggers AWS Glue jobs for transformation
   - For demo: Direct load to Redshift with validation
   - Handles data normalization and deduplication

5. **Redshift Loading**
   - Uses optimized COPY commands for bulk loading
   - Loads data into concert_dw schema tables
   - Updates table statistics with ANALYZE

6. **Data Verification**
   - Checks row counts for all tables
   - Validates referential integrity
   - Identifies orphaned records
   - Generates quality metrics

### Output

The script generates a JSON report with detailed execution results:

```json
{
  "pipeline_start": "2025-01-15T10:30:00",
  "pipeline_end": "2025-01-15T10:45:00",
  "steps": {
    "s3_buckets": {"status": "success"},
    "data_generation": {
      "status": "success",
      "counts": {
        "artists": 1000,
        "venues": 500,
        "concerts": 10000,
        "ticket_sales": 50000
      }
    },
    "redshift_load": {
      "status": "success",
      "load_results": {
        "artists": true,
        "venues": true,
        "concerts": true,
        "ticket_sales": true
      }
    },
    "data_verification": {
      "status": "success",
      "verification_results": {
        "artists": {"row_count": 1000, "has_data": true},
        "venues": {"row_count": 500, "has_data": true},
        "concerts": {"row_count": 10000, "has_data": true},
        "ticket_sales": {"row_count": 50000, "has_data": true}
      }
    }
  }
}
```

## Phase 2: Model Training

### Script: `train_demo_models.py`

This script trains and validates ML models using the loaded demo data.

### Basic Usage

```bash
# Train all models with default settings
python train_demo_models.py

# Use custom test/train split
python train_demo_models.py --test-size 0.3

# Use different random seed
python train_demo_models.py --random-state 123
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--test-size` | Test set size as fraction | 0.2 |
| `--random-state` | Random seed for reproducibility | 42 |
| `--validate-only` | Only validate existing models | False |

### Training Steps

The script executes the following steps:

1. **Venue Popularity Model**
   - Extracts venue data with concert history from Redshift
   - Engineers features: capacity utilization, revenue metrics, booking frequency
   - Trains Random Forest regression model
   - Evaluates with MAE, RMSE, R² metrics
   - Identifies top feature importance

2. **Ticket Sales Prediction Model**
   - Extracts concert data with artist and venue information
   - Engineers features: artist popularity, venue capacity, time-based features
   - Trains Gradient Boosting regression model
   - Evaluates prediction accuracy
   - Analyzes feature contributions

3. **Sample Predictions**
   - Generates venue popularity rankings for demo venues
   - Predicts ticket sales for upcoming concerts
   - Creates demo scenarios for presentation

### Model Evaluation Metrics

Both models are evaluated using:

- **MAE (Mean Absolute Error)**: Average prediction error
- **RMSE (Root Mean Squared Error)**: Penalizes larger errors
- **R² Score**: Proportion of variance explained (0-1, higher is better)

### Output

The script generates a JSON report with training results:

```json
{
  "training_start": "2025-01-15T11:00:00",
  "training_end": "2025-01-15T11:15:00",
  "models": {
    "venue_popularity": {
      "model_type": "venue_popularity",
      "algorithm": "RandomForestRegressor",
      "train_samples": 400,
      "test_samples": 100,
      "train_metrics": {
        "mae": 5.23,
        "rmse": 7.45,
        "r2": 0.8934
      },
      "test_metrics": {
        "mae": 6.12,
        "rmse": 8.67,
        "r2": 0.8521
      },
      "feature_importance": [
        {"feature": "avg_capacity_utilization", "importance": 0.3245},
        {"feature": "total_revenue", "importance": 0.2134}
      ],
      "status": "success"
    },
    "ticket_sales_prediction": {
      "model_type": "ticket_sales_prediction",
      "algorithm": "GradientBoostingRegressor",
      "train_samples": 8000,
      "test_samples": 2000,
      "train_metrics": {
        "mae": 245.67,
        "rmse": 356.23,
        "r2": 0.7823
      },
      "test_metrics": {
        "mae": 278.45,
        "rmse": 389.12,
        "r2": 0.7456
      },
      "status": "success"
    }
  },
  "sample_predictions": {
    "venue_popularity_samples": 10,
    "ticket_sales_samples": 10,
    "status": "success"
  }
}
```

## Complete Workflow Example

Here's a complete example of running both phases:

```bash
# Step 1: Generate and load demo data
python run_demo_pipeline.py \
  --artists 1000 \
  --venues 500 \
  --concerts 10000 \
  --sales 50000 \
  --seed 42

# Wait for pipeline to complete (check output for success)

# Step 2: Train ML models
python train_demo_models.py \
  --test-size 0.2 \
  --random-state 42

# Review training reports
ls -lh pipeline_report_*.json model_training_report_*.json
```

## Troubleshooting

### Common Issues

#### 1. S3 Access Denied

**Error**: `ClientError: An error occurred (AccessDenied) when calling the PutObject operation`

**Solution**: 
- Verify AWS credentials are configured correctly
- Check IAM user/role has S3 write permissions
- Ensure bucket names are correct and accessible

#### 2. Redshift Connection Failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
- Verify Redshift cluster is running
- Check security group allows inbound connections
- Confirm connection details in `.env` file
- Test connection: `psql -h $REDSHIFT_HOST -U $REDSHIFT_USER -d $REDSHIFT_DATABASE`

#### 3. COPY Command Failed

**Error**: `Failed to load data into table`

**Solution**:
- Check IAM role has permissions for Redshift and S3
- Verify S3 paths are correct
- Review STL_LOAD_ERRORS table in Redshift:
  ```sql
  SELECT * FROM stl_load_errors 
  WHERE starttime >= DATEADD(hour, -1, GETDATE())
  ORDER BY starttime DESC;
  ```

#### 4. Insufficient Training Data

**Error**: `Not enough data for model training`

**Solution**:
- Ensure data pipeline completed successfully
- Check Redshift tables have data: `SELECT COUNT(*) FROM concert_dw.concerts;`
- Verify concerts have status='completed' for training data

#### 5. Model Training Memory Error

**Error**: `MemoryError: Unable to allocate array`

**Solution**:
- Reduce dataset size with smaller generation parameters
- Use `--test-size 0.3` to reduce training set
- Close other applications to free memory

## Validation Queries

Use these SQL queries to validate the pipeline execution:

```sql
-- Check data counts
SELECT 
  'artists' as table_name, COUNT(*) as row_count FROM concert_dw.artists
UNION ALL
SELECT 'venues', COUNT(*) FROM concert_dw.venues
UNION ALL
SELECT 'concerts', COUNT(*) FROM concert_dw.concerts
UNION ALL
SELECT 'ticket_sales', COUNT(*) FROM concert_dw.ticket_sales;

-- Check referential integrity
SELECT 
  COUNT(*) as orphaned_concerts
FROM concert_dw.concerts c
LEFT JOIN concert_dw.artists a ON c.artist_id = a.artist_id
WHERE a.artist_id IS NULL;

-- Check data quality
SELECT 
  status,
  COUNT(*) as concert_count,
  AVG(total_attendance) as avg_attendance,
  SUM(revenue) as total_revenue
FROM concert_dw.concerts
GROUP BY status;

-- Sample venue popularity data
SELECT 
  v.name,
  v.capacity,
  COUNT(c.concert_id) as total_concerts,
  AVG(c.total_attendance) as avg_attendance
FROM concert_dw.venues v
LEFT JOIN concert_dw.concerts c ON v.venue_id = c.venue_id
GROUP BY v.venue_id, v.name, v.capacity
ORDER BY total_concerts DESC
LIMIT 10;
```

## Next Steps

After successfully running the demo pipeline:

1. **Test the Chatbot**: Use the trained models with the AI chatbot interface
2. **Explore Analytics**: Query the data warehouse for insights
3. **Run Predictions**: Generate predictions for upcoming concerts
4. **Monitor Performance**: Set up CloudWatch dashboards for pipeline monitoring
5. **Scale Up**: Increase data volumes for production-scale testing

## Additional Resources

- [Synthetic Data Generator Documentation](../api-ingestion/README.md)
- [Redshift Setup Guide](../redshift/REDSHIFT_QUICKSTART.md)
- [Model Evaluation Guide](../features/MODEL_MONITORING_SUMMARY.md)
- [Data Quality Service](../services/DATA_ANALYSIS_README.md)
