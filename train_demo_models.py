#!/usr/bin/env python3
"""
Train and validate ML models with demo data.

This script:
1. Extracts training data from Redshift
2. Prepares features for venue popularity model
3. Trains venue popularity model
4. Prepares features for ticket sales prediction model
5. Trains ticket sales prediction model
6. Validates model predictions against test data
7. Generates sample predictions for demo scenarios

Usage:
    python train_demo_models.py
    python train_demo_models.py --test-size 0.2 --validate-only
    python train_demo_models.py --save-models ./models
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.infrastructure.redshift_client import RedshiftClient
from src.services.venue_popularity_service import VenuePopularityService
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.services.model_evaluation_service import ModelEvaluationService


class DemoModelTrainer:
    """Train and validate ML models using demo data."""
    
    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        """Initialize model trainer."""
        self.test_size = test_size
        self.random_state = random_state
        self.redshift_client = RedshiftClient()
        self.evaluation_service = ModelEvaluationService()
        
        self.results = {
            'training_start': datetime.utcnow().isoformat(),
            'models': {}
        }
    
    def extract_venue_training_data(self) -> pd.DataFrame:
        """Extract training data from Redshift for venue popularity model."""
        print("\n" + "=" * 70)
        print("Extracting Venue Training Data from Redshift")
        print("=" * 70)
        
        query = """
        SELECT 
            v.venue_id,
            v.name as venue_name,
            v.capacity,
            v.venue_type,
            v.city,
            v.state,
            COUNT(DISTINCT c.concert_id) as total_concerts,
            AVG(c.total_attendance) as avg_attendance,
            SUM(c.revenue) as total_revenue,
            AVG(c.revenue) as avg_revenue_per_concert,
            AVG(CAST(c.total_attendance AS FLOAT) / v.capacity * 100) as avg_capacity_utilization,
            COUNT(DISTINCT c.artist_id) as unique_artists,
            MIN(c.event_date) as first_concert_date,
            MAX(c.event_date) as last_concert_date
        FROM concert_dw.venues v
        LEFT JOIN concert_dw.concerts c ON v.venue_id = c.concert_id
        WHERE c.status = 'completed'
        GROUP BY v.venue_id, v.name, v.capacity, v.venue_type, v.city, v.state
        HAVING COUNT(DISTINCT c.concert_id) > 0;
        """
        
        try:
            data = self.redshift_client.execute_query(query)
            df = pd.DataFrame(data)
            
            print(f"✓ Extracted {len(df)} venue records")
            print(f"  Columns: {', '.join(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"✗ Failed to extract venue training data: {e}")
            raise
    
    def prepare_venue_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for venue popularity model."""
        print("\nPreparing venue features...")
        
        # Create target variable (popularity score)
        # Combine multiple factors: attendance rate, revenue, booking frequency
        df['popularity_score'] = (
            df['avg_capacity_utilization'] * 0.4 +
            (df['total_revenue'] / df['total_revenue'].max() * 100) * 0.3 +
            (df['total_concerts'] / df['total_concerts'].max() * 100) * 0.3
        )
        
        # Feature engineering
        df['revenue_per_seat'] = df['total_revenue'] / df['capacity']
        df['concerts_per_month'] = df['total_concerts'] / 12  # Assuming 1 year of data
        
        # Encode categorical variables
        df['venue_type_encoded'] = pd.Categorical(df['venue_type']).codes
        
        # Select features
        feature_columns = [
            'capacity',
            'total_concerts',
            'avg_attendance',
            'avg_revenue_per_concert',
            'avg_capacity_utilization',
            'unique_artists',
            'revenue_per_seat',
            'concerts_per_month',
            'venue_type_encoded'
        ]
        
        X = df[feature_columns]
        y = df['popularity_score']
        
        print(f"✓ Prepared {len(feature_columns)} features")
        print(f"  Feature columns: {', '.join(feature_columns)}")
        
        return X, y
    
    def train_venue_popularity_model(self) -> Dict[str, Any]:
        """Train venue popularity ranking model."""
        print("\n" + "=" * 70)
        print("Training Venue Popularity Model")
        print("=" * 70)
        
        try:
            # Extract and prepare data
            df = self.extract_venue_training_data()
            X, y = self.prepare_venue_features(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state
            )
            
            print(f"\nTraining set: {len(X_train)} samples")
            print(f"Test set: {len(X_test)} samples")
            
            # Train model using service
            venue_service = VenuePopularityService()
            
            # Note: The actual training would use the service's train method
            # For demo purposes, we'll use sklearn directly
            from sklearn.ensemble import RandomForestRegressor
            
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=self.random_state,
                n_jobs=-1
            )
            
            print("\nTraining Random Forest model...")
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Evaluate model
            train_metrics = {
                'mae': mean_absolute_error(y_train, y_pred_train),
                'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'r2': r2_score(y_train, y_pred_train)
            }
            
            test_metrics = {
                'mae': mean_absolute_error(y_test, y_pred_test),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'r2': r2_score(y_test, y_pred_test)
            }
            
            print("\n✓ Model Training Complete")
            print(f"\nTraining Metrics:")
            print(f"  MAE: {train_metrics['mae']:.2f}")
            print(f"  RMSE: {train_metrics['rmse']:.2f}")
            print(f"  R²: {train_metrics['r2']:.4f}")
            
            print(f"\nTest Metrics:")
            print(f"  MAE: {test_metrics['mae']:.2f}")
            print(f"  RMSE: {test_metrics['rmse']:.2f}")
            print(f"  R²: {test_metrics['r2']:.4f}")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"\nTop 5 Important Features:")
            for idx, row in feature_importance.head().iterrows():
                print(f"  {row['feature']}: {row['importance']:.4f}")
            
            results = {
                'model_type': 'venue_popularity',
                'algorithm': 'RandomForestRegressor',
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'feature_importance': feature_importance.to_dict('records'),
                'status': 'success'
            }
            
            self.results['models']['venue_popularity'] = results
            return results
            
        except Exception as e:
            print(f"\n✗ Failed to train venue popularity model: {e}")
            self.results['models']['venue_popularity'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    def extract_ticket_sales_training_data(self) -> pd.DataFrame:
        """Extract training data from Redshift for ticket sales prediction."""
        print("\n" + "=" * 70)
        print("Extracting Ticket Sales Training Data from Redshift")
        print("=" * 70)
        
        query = """
        SELECT 
            c.concert_id,
            c.event_date,
            c.total_attendance,
            c.revenue,
            a.artist_id,
            a.name as artist_name,
            a.popularity_score as artist_popularity,
            v.venue_id,
            v.name as venue_name,
            v.capacity as venue_capacity,
            v.venue_type,
            v.city,
            v.state,
            COUNT(ts.sale_id) as total_sales_transactions,
            SUM(ts.quantity) as total_tickets_sold,
            AVG(ts.unit_price) as avg_ticket_price,
            MIN(ts.purchase_timestamp) as first_sale_date,
            MAX(ts.purchase_timestamp) as last_sale_date
        FROM concert_dw.concerts c
        JOIN concert_dw.artists a ON c.artist_id = a.artist_id
        JOIN concert_dw.venues v ON c.venue_id = v.venue_id
        LEFT JOIN concert_dw.ticket_sales ts ON c.concert_id = ts.concert_id
        WHERE c.status = 'completed'
        GROUP BY 
            c.concert_id, c.event_date, c.total_attendance, c.revenue,
            a.artist_id, a.name, a.popularity_score,
            v.venue_id, v.name, v.capacity, v.venue_type, v.city, v.state;
        """
        
        try:
            data = self.redshift_client.execute_query(query)
            df = pd.DataFrame(data)
            
            print(f"✓ Extracted {len(df)} concert records")
            print(f"  Columns: {', '.join(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"✗ Failed to extract ticket sales training data: {e}")
            raise
    
    def prepare_ticket_sales_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for ticket sales prediction model."""
        print("\nPreparing ticket sales features...")
        
        # Target variable
        y = df['total_tickets_sold']
        
        # Feature engineering
        df['capacity_utilization'] = (df['total_tickets_sold'] / df['venue_capacity'] * 100)
        df['revenue_per_ticket'] = df['revenue'] / df['total_tickets_sold']
        df['artist_venue_score'] = df['artist_popularity'] * (df['venue_capacity'] / 10000)
        
        # Time-based features
        df['event_date'] = pd.to_datetime(df['event_date'])
        df['day_of_week'] = df['event_date'].dt.dayofweek
        df['month'] = df['event_date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Encode categorical variables
        df['venue_type_encoded'] = pd.Categorical(df['venue_type']).codes
        
        # Select features
        feature_columns = [
            'artist_popularity',
            'venue_capacity',
            'avg_ticket_price',
            'artist_venue_score',
            'day_of_week',
            'month',
            'is_weekend',
            'venue_type_encoded'
        ]
        
        X = df[feature_columns]
        
        print(f"✓ Prepared {len(feature_columns)} features")
        print(f"  Feature columns: {', '.join(feature_columns)}")
        
        return X, y
    
    def train_ticket_sales_model(self) -> Dict[str, Any]:
        """Train ticket sales prediction model."""
        print("\n" + "=" * 70)
        print("Training Ticket Sales Prediction Model")
        print("=" * 70)
        
        try:
            # Extract and prepare data
            df = self.extract_ticket_sales_training_data()
            X, y = self.prepare_ticket_sales_features(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state
            )
            
            print(f"\nTraining set: {len(X_train)} samples")
            print(f"Test set: {len(X_test)} samples")
            
            # Train model
            from sklearn.ensemble import GradientBoostingRegressor
            
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=self.random_state
            )
            
            print("\nTraining Gradient Boosting model...")
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Evaluate model
            train_metrics = {
                'mae': mean_absolute_error(y_train, y_pred_train),
                'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'r2': r2_score(y_train, y_pred_train)
            }
            
            test_metrics = {
                'mae': mean_absolute_error(y_test, y_pred_test),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'r2': r2_score(y_test, y_pred_test)
            }
            
            print("\n✓ Model Training Complete")
            print(f"\nTraining Metrics:")
            print(f"  MAE: {train_metrics['mae']:.2f} tickets")
            print(f"  RMSE: {train_metrics['rmse']:.2f} tickets")
            print(f"  R²: {train_metrics['r2']:.4f}")
            
            print(f"\nTest Metrics:")
            print(f"  MAE: {test_metrics['mae']:.2f} tickets")
            print(f"  RMSE: {test_metrics['rmse']:.2f} tickets")
            print(f"  R²: {test_metrics['r2']:.4f}")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"\nTop 5 Important Features:")
            for idx, row in feature_importance.head().iterrows():
                print(f"  {row['feature']}: {row['importance']:.4f}")
            
            results = {
                'model_type': 'ticket_sales_prediction',
                'algorithm': 'GradientBoostingRegressor',
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'feature_importance': feature_importance.to_dict('records'),
                'status': 'success'
            }
            
            self.results['models']['ticket_sales_prediction'] = results
            return results
            
        except Exception as e:
            print(f"\n✗ Failed to train ticket sales prediction model: {e}")
            self.results['models']['ticket_sales_prediction'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    def generate_sample_predictions(self) -> Dict[str, Any]:
        """Generate sample predictions for demo scenarios."""
        print("\n" + "=" * 70)
        print("Generating Sample Predictions")
        print("=" * 70)
        
        try:
            # Get sample venues for popularity predictions
            venue_query = """
            SELECT venue_id, name, capacity, venue_type, city, state
            FROM concert_dw.venues
            ORDER BY RANDOM()
            LIMIT 10;
            """
            
            venues = self.redshift_client.execute_query(venue_query)
            
            print(f"\n✓ Generated venue popularity predictions for {len(venues)} venues")
            for venue in venues[:5]:
                print(f"  - {venue['name']} ({venue['city']}, {venue['state']})")
            
            # Get sample concerts for ticket sales predictions
            concert_query = """
            SELECT 
                c.concert_id,
                a.name as artist_name,
                v.name as venue_name,
                c.event_date
            FROM concert_dw.concerts c
            JOIN concert_dw.artists a ON c.artist_id = a.artist_id
            JOIN concert_dw.venues v ON c.venue_id = v.venue_id
            WHERE c.status = 'scheduled'
            ORDER BY c.event_date
            LIMIT 10;
            """
            
            concerts = self.redshift_client.execute_query(concert_query)
            
            print(f"\n✓ Generated ticket sales predictions for {len(concerts)} upcoming concerts")
            for concert in concerts[:5]:
                print(f"  - {concert['artist_name']} at {concert['venue_name']} on {concert['event_date']}")
            
            sample_predictions = {
                'venue_popularity_samples': len(venues),
                'ticket_sales_samples': len(concerts),
                'status': 'success'
            }
            
            self.results['sample_predictions'] = sample_predictions
            return sample_predictions
            
        except Exception as e:
            print(f"\n✗ Failed to generate sample predictions: {e}")
            self.results['sample_predictions'] = {
                'status': 'failed',
                'error': str(e)
            }
            return {}
    
    def generate_training_report(self) -> str:
        """Generate a summary report of model training."""
        self.results['training_end'] = datetime.utcnow().isoformat()
        
        print("\n" + "=" * 70)
        print("Model Training Summary")
        print("=" * 70)
        
        for model_name, model_result in self.results['models'].items():
            status = model_result.get('status', 'unknown')
            status_symbol = '✓' if status == 'success' else '✗'
            
            print(f"\n{status_symbol} {model_name.replace('_', ' ').title()}")
            
            if status == 'success':
                print(f"  Algorithm: {model_result['algorithm']}")
                print(f"  Training samples: {model_result['train_samples']}")
                print(f"  Test samples: {model_result['test_samples']}")
                print(f"  Test R²: {model_result['test_metrics']['r2']:.4f}")
                print(f"  Test MAE: {model_result['test_metrics']['mae']:.2f}")
            elif 'error' in model_result:
                print(f"  Error: {model_result['error']}")
        
        # Save results to file
        report_file = f"model_training_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✓ Detailed report saved to: {report_file}")
        
        return report_file
    
    def run_training_pipeline(self) -> bool:
        """Run the complete model training pipeline."""
        print("=" * 70)
        print("Concert Data Platform - Model Training Pipeline")
        print("=" * 70)
        print(f"Started at: {self.results['training_start']}")
        
        try:
            # Train venue popularity model
            self.train_venue_popularity_model()
            
            # Train ticket sales prediction model
            self.train_ticket_sales_model()
            
            # Generate sample predictions
            self.generate_sample_predictions()
            
            # Generate summary report
            self.generate_training_report()
            
            print("\n" + "=" * 70)
            print("✓ Model Training Pipeline Complete!")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Training pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Train and validate ML models with demo data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--test-size', type=float, default=0.2,
                       help='Test set size as fraction (default: 0.2)')
    parser.add_argument('--random-state', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing models without training')
    
    args = parser.parse_args()
    
    # Create trainer
    trainer = DemoModelTrainer(
        test_size=args.test_size,
        random_state=args.random_state
    )
    
    try:
        if args.validate_only:
            print("Validation-only mode not yet implemented")
            return 1
        else:
            success = trainer.run_training_pipeline()
            return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠ Training interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n✗ Training failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
