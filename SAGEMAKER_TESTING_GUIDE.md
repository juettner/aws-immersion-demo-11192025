# SageMaker Ticket Sales Prediction Testing Guide

This guide walks you through testing the ticket sales prediction system in AWS SageMaker, from setup to making predictions.

## Prerequisites

Before you begin, ensure you have:
- AWS account with appropriate permissions
- AWS CLI configured with credentials
- Python environment with required packages installed
- Redshift cluster with concert/ticket data populated
- S3 bucket for storing training data and model artifacts

## Step 1: AWS Console Setup

### 1.1 Create IAM Role for SageMaker

1. Go to **IAM Console** → **Roles** → **Create role**
2. Select **AWS service** → **SageMaker**
3. Select use case: **SageMaker - Execution**
4. Click **Next**
5. Attach these policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess` (or create a custom policy with access to your specific bucket)
   - `AmazonRedshiftDataFullAccess` (if querying Redshift directly)
6. Name the role: `SageMaker-TicketSales-ExecutionRole`
7. Click **Create role**
8. Copy the **Role ARN** (you'll need this later)

### 1.2 Create S3 Bucket Structure

1. Go to **S3 Console** → **Create bucket**
2. Name: `your-project-ml-models` (or use existing bucket)
3. Create the following folder structure:
   ```
   s3://your-project-ml-models/
   ├── ml-models/
   │   └── ticket-sales/
   │       ├── training_data.csv (will be created by script)
   │       └── output/ (model artifacts will be stored here)
   ```

## Step 2: Configure Your Environment

### 2.1 Update Configuration File

Edit `src/config/settings.py` and add/update:

```python
# SageMaker Configuration
SAGEMAKER_ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMaker-TicketSales-ExecutionRole"
S3_BUCKET = "your-project-ml-models"

# Redshift Configuration (ensure these are set)
REDSHIFT_HOST = "your-cluster.region.redshift.amazonaws.com"
REDSHIFT_DATABASE = "concerts_db"
REDSHIFT_USER = "admin"
REDSHIFT_PASSWORD = "your-password"
REDSHIFT_PORT = 5439
```

### 2.2 Set Environment Variables (Alternative)

```bash
export SAGEMAKER_ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMaker-TicketSales-ExecutionRole"
export S3_BUCKET="your-project-ml-models"
export REDSHIFT_HOST="your-cluster.region.redshift.amazonaws.com"
export REDSHIFT_DATABASE="concerts_db"
export REDSHIFT_USER="admin"
export REDSHIFT_PASSWORD="your-password"
```

## Step 3: Prepare Training Data

### 3.1 Run Data Preparation Script

Create a test script `test_prepare_training_data.py`:

```python
import logging
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    # Initialize clients
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Prepare training data
    output_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales"
    
    logger.info("Extracting features and preparing training data...")
    s3_path, num_records = service.prepare_training_data(
        output_path=output_path,
        lookback_days=730
    )
    
    logger.info(f"✓ Training data prepared: {s3_path}")
    logger.info(f"✓ Total records: {num_records}")
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_prepare_training_data.py
```

### 3.2 Verify Data in S3

1. Go to **S3 Console**
2. Navigate to `s3://your-project-ml-models/ml-models/ticket-sales/`
3. Verify `training_data.csv` exists
4. Download and inspect the file to ensure it has data

## Step 4: Train the Model

### Option A: Using Python Script (Recommended)

Create `test_train_model.py`:

```python
import logging
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Train model
    training_data_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales/training_data.csv"
    model_output_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales/output"
    
    logger.info("Starting model training...")
    logger.info("This may take 5-15 minutes depending on data size...")
    
    result = service.train_sagemaker_model(
        training_data_path=training_data_path,
        model_output_path=model_output_path,
        role_arn=settings.SAGEMAKER_ROLE_ARN,
        instance_type='ml.m5.xlarge'
    )
    
    logger.info(f"✓ Training completed!")
    logger.info(f"  Job name: {result['job_name']}")
    logger.info(f"  Model artifacts: {result['model_data']}")
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_train_model.py
```

### Option B: Monitor Training in AWS Console

1. Go to **SageMaker Console** → **Training** → **Training jobs**
2. Find your job (starts with `ticket-sales-`)
3. Click on the job name to see details
4. Monitor the **Status** (should go from `InProgress` to `Completed`)
5. Check **CloudWatch logs** for detailed training output
6. Once complete, note the **Model artifacts** S3 path

**Training typically takes 5-15 minutes depending on data size.**

## Step 5: Deploy the Model

### 5.1 Deploy Using Python Script

Create `test_deploy_model.py`:

```python
import logging
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Deploy model (use the model_data path from training output)
    model_data_path = f"s3://{settings.S3_BUCKET}/ml-models/ticket-sales/output/ticket-sales-YYYYMMDD-HHMMSS/output/model.tar.gz"
    
    logger.info("Deploying model to endpoint...")
    logger.info("This may take 5-10 minutes...")
    
    endpoint_name = service.deploy_model(
        model_data_path=model_data_path,
        role_arn=settings.SAGEMAKER_ROLE_ARN,
        endpoint_name="ticket-sales-prediction-demo",
        instance_type='ml.t2.medium'
    )
    
    logger.info(f"✓ Model deployed to endpoint: {endpoint_name}")
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

**Note:** Update `model_data_path` with the actual path from your training job output.

Run it:
```bash
python test_deploy_model.py
```

### 5.2 Monitor Deployment in AWS Console

1. Go to **SageMaker Console** → **Inference** → **Endpoints**
2. Find your endpoint: `ticket-sales-prediction-demo`
3. Monitor **Status** (should go from `Creating` to `InService`)
4. Once `InService`, the endpoint is ready for predictions

**Deployment typically takes 5-10 minutes.**

## Step 6: Make Predictions

### 6.1 Single Prediction Test

Create `test_prediction.py`:

```python
import logging
from datetime import datetime, timedelta
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Make prediction for an upcoming concert
    prediction = service.predict_ticket_sales(
        concert_id="future_concert_001",
        artist_id="art_001",  # Use actual artist ID from your database
        venue_id="ven_001",   # Use actual venue ID from your database
        event_date=datetime.now() + timedelta(days=60),
        ticket_prices={
            'general': 75.0,
            'premium': 125.0,
            'vip': 250.0
        },
        endpoint_name="ticket-sales-prediction-demo"
    )
    
    logger.info("\n" + "="*60)
    logger.info("PREDICTION RESULTS")
    logger.info("="*60)
    logger.info(f"Concert ID: {prediction.concert_id}")
    logger.info(f"Predicted Sales: ${prediction.predicted_sales:,.2f}")
    logger.info(f"Confidence Score: {prediction.confidence_score:.3f}")
    logger.info(f"Low Confidence Flag: {prediction.low_confidence_flag}")
    
    if prediction.low_confidence_flag:
        logger.warning("⚠️  LOW CONFIDENCE PREDICTION")
        logger.warning("Consider gathering more data or reviewing input features")
    else:
        logger.info("✓ High confidence prediction")
    
    logger.info("="*60)
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_prediction.py
```

### 6.2 Batch Predictions Test

Create `test_batch_predictions.py`:

```python
import logging
from datetime import datetime, timedelta
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    # Define multiple concerts
    concerts = [
        {
            'concert_id': 'future_001',
            'artist_id': 'art_001',
            'venue_id': 'ven_001',
            'event_date': datetime.now() + timedelta(days=30),
            'ticket_prices': {'general': 50.0, 'vip': 150.0}
        },
        {
            'concert_id': 'future_002',
            'artist_id': 'art_002',
            'venue_id': 'ven_002',
            'event_date': datetime.now() + timedelta(days=60),
            'ticket_prices': {'general': 75.0, 'premium': 125.0, 'vip': 250.0}
        },
        {
            'concert_id': 'future_003',
            'artist_id': 'art_003',
            'venue_id': 'ven_001',
            'event_date': datetime.now() + timedelta(days=90),
            'ticket_prices': {'general': 100.0, 'vip': 300.0}
        }
    ]
    
    logger.info("Making batch predictions...")
    predictions = service.batch_predict_sales(
        concerts=concerts,
        endpoint_name="ticket-sales-prediction-demo"
    )
    
    logger.info("\n" + "="*60)
    logger.info("BATCH PREDICTION RESULTS")
    logger.info("="*60)
    
    for i, pred in enumerate(predictions, 1):
        logger.info(f"\nPrediction {i}:")
        logger.info(f"  Concert: {pred.concert_id}")
        logger.info(f"  Predicted Sales: ${pred.predicted_sales:,.2f}")
        logger.info(f"  Confidence: {pred.confidence_score:.3f}")
        logger.info(f"  Low Confidence: {'⚠️ YES' if pred.low_confidence_flag else '✓ NO'}")
    
    low_conf_count = sum(1 for p in predictions if p.low_confidence_flag)
    logger.info(f"\nSummary: {len(predictions)} predictions, {low_conf_count} low confidence")
    logger.info("="*60)
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_batch_predictions.py
```

## Step 7: Evaluate Model Performance

Create `test_model_evaluation.py`:

```python
import logging
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.infrastructure.redshift_client import RedshiftClient
from src.config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    
    redshift_client = RedshiftClient(
        host=settings.REDSHIFT_HOST,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
        port=settings.REDSHIFT_PORT
    )
    
    service = TicketSalesPredictionService(redshift_client)
    
    logger.info("Evaluating model performance on recent concerts...")
    metrics = service.evaluate_model_performance(
        endpoint_name="ticket-sales-prediction-demo",
        lookback_days=730
    )
    
    logger.info("\n" + "="*60)
    logger.info("MODEL PERFORMANCE METRICS")
    logger.info("="*60)
    logger.info(f"Number of predictions: {metrics['num_predictions']}")
    logger.info(f"Mean Absolute Error: ${metrics['mean_absolute_error']:,.2f}")
    logger.info(f"Root Mean Squared Error: ${metrics['root_mean_squared_error']:,.2f}")
    logger.info(f"Mean Absolute Percentage Error: {metrics['mean_absolute_percentage_error']:.2f}%")
    logger.info(f"R-squared: {metrics['r_squared']:.4f}")
    logger.info(f"Average Confidence Score: {metrics['avg_confidence_score']:.3f}")
    logger.info(f"Low Confidence Count: {metrics['low_confidence_count']}")
    logger.info(f"Low Confidence %: {metrics['low_confidence_percentage']:.2f}%")
    logger.info("="*60)
    
    redshift_client.close()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_model_evaluation.py
```

## Step 8: Monitor in AWS Console

### 8.1 View Endpoint Metrics

1. Go to **SageMaker Console** → **Inference** → **Endpoints**
2. Click on `ticket-sales-prediction-demo`
3. Click **Monitor** tab
4. View metrics:
   - Invocations
   - Model latency
   - Overhead latency
   - CPU/Memory utilization

### 8.2 View CloudWatch Logs

1. Go to **CloudWatch Console** → **Logs** → **Log groups**
2. Find `/aws/sagemaker/Endpoints/ticket-sales-prediction-demo`
3. View invocation logs and any errors

## Step 9: Cost Management

### 9.1 Stop Endpoint When Not in Use

To avoid ongoing costs, delete the endpoint when testing is complete:

```python
import boto3

sagemaker = boto3.client('sagemaker')
sagemaker.delete_endpoint(EndpointName='ticket-sales-prediction-demo')
```

Or via AWS Console:
1. Go to **SageMaker Console** → **Inference** → **Endpoints**
2. Select `ticket-sales-prediction-demo`
3. Click **Delete**

### 9.2 Estimated Costs

- **Training**: ~$0.50-$2.00 per training job (ml.m5.xlarge for 10-15 min)
- **Endpoint**: ~$0.05/hour (ml.t2.medium) = ~$36/month if left running
- **S3 Storage**: Minimal (~$0.01/month for training data)

## Troubleshooting

### Issue: "No module named 'sagemaker'"
**Solution**: Install SageMaker SDK
```bash
pip install sagemaker>=2.150.0
```

### Issue: "Access Denied" errors
**Solution**: Check IAM role has proper permissions:
- AmazonSageMakerFullAccess
- S3 bucket access
- Redshift access (if needed)

### Issue: Training job fails
**Solution**: 
1. Check CloudWatch logs for the training job
2. Verify training data format (CSV with target in first column)
3. Ensure sufficient data (at least 100 records recommended)

### Issue: Low confidence predictions
**Solution**: This is expected when:
- Artist has limited history
- Venue has no performance data
- No historical sales data available
- Event is far in the future

Consider gathering more data or using the predictions with caution.

### Issue: Endpoint deployment timeout
**Solution**:
- Check endpoint status in SageMaker console
- Verify IAM role permissions
- Check CloudWatch logs for errors
- Ensure model artifacts exist in S3

## Next Steps

1. **Integrate with Application**: Use the prediction service in your application
2. **Automate Retraining**: Set up scheduled retraining with new data
3. **A/B Testing**: Deploy multiple model versions and compare
4. **Feature Engineering**: Add more features to improve accuracy
5. **Monitoring**: Set up CloudWatch alarms for endpoint health

## Additional Resources

- [SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/)
- [XGBoost Algorithm Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/xgboost.html)
- [SageMaker Python SDK](https://sagemaker.readthedocs.io/)
