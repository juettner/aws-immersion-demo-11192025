#!/usr/bin/env python3
"""
End-to-end demo data pipeline execution script.

This script orchestrates the complete data pipeline:
1. Generate synthetic concert data
2. Upload to S3 raw data bucket
3. Trigger Glue ETL jobs for processing
4. Load processed data into Redshift
5. Verify data quality and completeness

Usage:
    python run_demo_pipeline.py --generate-data
    python run_demo_pipeline.py --skip-generation --use-existing
    python run_demo_pipeline.py --artists 500 --venues 250 --concerts 5000
"""
import argparse
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import boto3
from botocore.exceptions import ClientError

from src.services.synthetic_data_generator import SyntheticDataGenerator, GeneratorConfig
from src.infrastructure.redshift_client import RedshiftClient
from src.infrastructure.redshift_data_loader import RedshiftDataLoader
from src.infrastructure.glue_job_manager import GlueJobManager
from src.config.settings import settings


class DemoPipelineOrchestrator:
    """Orchestrates the end-to-end demo data pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline orchestrator with configuration."""
        self.config = config
        self.s3_client = boto3.client('s3', region_name=settings.aws_region)
        self.redshift_client = RedshiftClient()
        self.glue_manager = GlueJobManager()
        
        # S3 paths
        self.raw_bucket = config.get('raw_bucket', 'concert-data-raw')
        self.processed_bucket = config.get('processed_bucket', 'concert-data-processed')
        self.raw_prefix = config.get('raw_prefix', 'demo-data')
        self.processed_prefix = config.get('processed_prefix', 'processed')
        
        # IAM role for Redshift COPY
        self.iam_role = config.get('iam_role', settings.aws.redshift_iam_role if hasattr(settings.aws, 'redshift_iam_role') else '')
        
        self.results = {
            'pipeline_start': datetime.utcnow().isoformat(),
            'steps': {}
        }
    
    def ensure_s3_buckets(self) -> bool:
        """Ensure S3 buckets exist."""
        print("\n" + "=" * 70)
        print("Step 1: Ensuring S3 Buckets Exist")
        print("=" * 70)
        
        buckets = [self.raw_bucket, self.processed_bucket]
        
        for bucket in buckets:
            try:
                self.s3_client.head_bucket(Bucket=bucket)
                print(f"✓ Bucket exists: {bucket}")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    try:
                        self.s3_client.create_bucket(
                            Bucket=bucket,
                            CreateBucketConfiguration={'LocationConstraint': settings.aws_region}
                            if settings.aws_region != 'us-east-1' else {}
                        )
                        print(f"✓ Created bucket: {bucket}")
                    except ClientError as create_error:
                        print(f"✗ Failed to create bucket {bucket}: {create_error}")
                        return False
                else:
                    print(f"✗ Error checking bucket {bucket}: {e}")
                    return False
        
        self.results['steps']['s3_buckets'] = {'status': 'success'}
        return True
    
    def generate_and_upload_data(self, generator_config: GeneratorConfig) -> bool:
        """Generate synthetic data and upload to S3."""
        print("\n" + "=" * 70)
        print("Step 2: Generating Synthetic Data")
        print("=" * 70)
        
        try:
            # Generate data
            generator = SyntheticDataGenerator(generator_config)
            data = generator.generate_all()
            
            print(f"\n✓ Generated {len(data['artists'])} artists")
            print(f"✓ Generated {len(data['venues'])} venues")
            print(f"✓ Generated {len(data['concerts'])} concerts")
            print(f"✓ Generated {len(data['ticket_sales'])} ticket sales")
            
            # Validate data quality
            validation_result = generator.validate_data_quality()
            if not validation_result['valid']:
                print("\n⚠ Data quality validation warnings:")
                for issue in validation_result.get('issues', []):
                    print(f"  - {issue}")
            
            # Upload to S3
            print("\n" + "=" * 70)
            print("Step 3: Uploading Data to S3")
            print("=" * 70)
            
            s3_files = generator.upload_to_s3(self.raw_bucket, self.raw_prefix)
            
            for file_info in s3_files:
                print(f"✓ Uploaded: s3://{file_info['bucket']}/{file_info['key']}")
            
            self.results['steps']['data_generation'] = {
                'status': 'success',
                'counts': {
                    'artists': len(data['artists']),
                    'venues': len(data['venues']),
                    'concerts': len(data['concerts']),
                    'ticket_sales': len(data['ticket_sales'])
                },
                's3_files': s3_files
            }
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during data generation/upload: {e}")
            self.results['steps']['data_generation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def run_glue_etl_jobs(self) -> bool:
        """Trigger and monitor Glue ETL jobs."""
        print("\n" + "=" * 70)
        print("Step 4: Running Glue ETL Jobs")
        print("=" * 70)
        
        # Note: This is a simplified version since Glue jobs require
        # actual AWS Glue setup with job definitions and scripts
        print("\nℹ Glue ETL jobs would process:")
        print(f"  - Artist data normalization and deduplication")
        print(f"  - Venue data normalization and deduplication")
        print(f"  - Concert data normalization")
        print(f"  - Data quality checks and monitoring")
        
        print("\n⚠ For this demo, we'll load data directly to Redshift")
        print("  In production, Glue would handle transformation and deduplication")
        
        self.results['steps']['glue_etl'] = {
            'status': 'skipped',
            'note': 'Direct load to Redshift for demo purposes'
        }
        
        return True
    
    def load_data_to_redshift(self) -> bool:
        """Load processed data into Redshift."""
        print("\n" + "=" * 70)
        print("Step 5: Loading Data to Redshift")
        print("=" * 70)
        
        try:
            # Check Redshift connection
            conn = self.redshift_client.get_connection()
            print("✓ Connected to Redshift")
            
            # Initialize data loader
            data_loader = RedshiftDataLoader(self.redshift_client, self.iam_role)
            
            # Define S3 paths for each data type
            s3_paths = {
                'artists': f"s3://{self.raw_bucket}/{self.raw_prefix}/artists.json",
                'venues': f"s3://{self.raw_bucket}/{self.raw_prefix}/venues.json",
                'concerts': f"s3://{self.raw_bucket}/{self.raw_prefix}/concerts.json",
                'ticket_sales': f"s3://{self.raw_bucket}/{self.raw_prefix}/ticket_sales.json"
            }
            
            # Load each data type
            load_results = {}
            
            print("\nLoading artists data...")
            load_results['artists'] = data_loader.load_artists_data(s3_paths['artists'])
            if load_results['artists']:
                print("✓ Artists data loaded successfully")
            else:
                print("✗ Failed to load artists data")
            
            print("\nLoading venues data...")
            load_results['venues'] = data_loader.load_venues_data(s3_paths['venues'])
            if load_results['venues']:
                print("✓ Venues data loaded successfully")
            else:
                print("✗ Failed to load venues data")
            
            print("\nLoading concerts data...")
            load_results['concerts'] = data_loader.load_concerts_data(s3_paths['concerts'])
            if load_results['concerts']:
                print("✓ Concerts data loaded successfully")
            else:
                print("✗ Failed to load concerts data")
            
            print("\nLoading ticket sales data...")
            load_results['ticket_sales'] = data_loader.load_ticket_sales_data(s3_paths['ticket_sales'])
            if load_results['ticket_sales']:
                print("✓ Ticket sales data loaded successfully")
            else:
                print("✗ Failed to load ticket sales data")
            
            self.results['steps']['redshift_load'] = {
                'status': 'success' if all(load_results.values()) else 'partial',
                'load_results': load_results
            }
            
            return all(load_results.values())
            
        except Exception as e:
            print(f"\n✗ Error loading data to Redshift: {e}")
            self.results['steps']['redshift_load'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def verify_data_quality(self) -> bool:
        """Verify data quality and completeness in Redshift."""
        print("\n" + "=" * 70)
        print("Step 6: Verifying Data Quality")
        print("=" * 70)
        
        try:
            schema_name = 'concert_dw'
            tables = ['artists', 'venues', 'concerts', 'ticket_sales']
            
            verification_results = {}
            
            for table in tables:
                print(f"\nVerifying {table}...")
                
                # Get row count
                count = self.redshift_client.get_table_row_count(table, schema_name)
                print(f"  Row count: {count:,}")
                
                # Get sample data
                sample_query = f"SELECT * FROM {schema_name}.{table} LIMIT 5;"
                sample_data = self.redshift_client.execute_query(sample_query)
                
                # Check for nulls in key columns
                null_check_query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(CASE WHEN {table[:-1]}_id IS NULL THEN 1 END) as null_ids
                FROM {schema_name}.{table};
                """
                null_check = self.redshift_client.execute_query(null_check_query)
                
                verification_results[table] = {
                    'row_count': count,
                    'null_ids': null_check[0]['null_ids'] if null_check else 0,
                    'has_data': count > 0
                }
                
                if count > 0:
                    print(f"  ✓ Data loaded successfully")
                else:
                    print(f"  ✗ No data found")
            
            # Check referential integrity
            print("\nChecking referential integrity...")
            
            integrity_query = """
            SELECT 
                (SELECT COUNT(*) FROM concert_dw.concerts c
                 LEFT JOIN concert_dw.artists a ON c.artist_id = a.artist_id
                 WHERE a.artist_id IS NULL) as orphaned_concerts_artists,
                (SELECT COUNT(*) FROM concert_dw.concerts c
                 LEFT JOIN concert_dw.venues v ON c.venue_id = v.venue_id
                 WHERE v.venue_id IS NULL) as orphaned_concerts_venues,
                (SELECT COUNT(*) FROM concert_dw.ticket_sales ts
                 LEFT JOIN concert_dw.concerts c ON ts.concert_id = c.concert_id
                 WHERE c.concert_id IS NULL) as orphaned_sales;
            """
            
            integrity_check = self.redshift_client.execute_query(integrity_query)
            
            if integrity_check:
                orphaned = integrity_check[0]
                if all(v == 0 for v in orphaned.values()):
                    print("  ✓ All referential integrity checks passed")
                else:
                    print("  ⚠ Referential integrity issues found:")
                    for key, value in orphaned.items():
                        if value > 0:
                            print(f"    - {key}: {value}")
                
                verification_results['referential_integrity'] = orphaned
            
            self.results['steps']['data_verification'] = {
                'status': 'success',
                'verification_results': verification_results
            }
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error verifying data quality: {e}")
            self.results['steps']['data_verification'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of the pipeline execution."""
        self.results['pipeline_end'] = datetime.utcnow().isoformat()
        
        print("\n" + "=" * 70)
        print("Pipeline Execution Summary")
        print("=" * 70)
        
        for step_name, step_result in self.results['steps'].items():
            status = step_result.get('status', 'unknown')
            status_symbol = {
                'success': '✓',
                'partial': '⚠',
                'failed': '✗',
                'skipped': 'ℹ'
            }.get(status, '?')
            
            print(f"\n{status_symbol} {step_name.replace('_', ' ').title()}: {status.upper()}")
            
            if 'counts' in step_result:
                for key, value in step_result['counts'].items():
                    print(f"    {key}: {value:,}")
            
            if 'error' in step_result:
                print(f"    Error: {step_result['error']}")
        
        # Save results to file
        report_file = f"pipeline_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✓ Detailed report saved to: {report_file}")
        
        return report_file
    
    def run_pipeline(self, generator_config: Optional[GeneratorConfig] = None, 
                    skip_generation: bool = False) -> bool:
        """Run the complete end-to-end pipeline."""
        print("=" * 70)
        print("Concert Data Platform - Demo Pipeline Execution")
        print("=" * 70)
        print(f"Started at: {self.results['pipeline_start']}")
        
        # Step 1: Ensure S3 buckets
        if not self.ensure_s3_buckets():
            print("\n✗ Pipeline failed at S3 bucket setup")
            return False
        
        # Step 2-3: Generate and upload data (if not skipped)
        if not skip_generation:
            if generator_config is None:
                generator_config = GeneratorConfig()
            
            if not self.generate_and_upload_data(generator_config):
                print("\n✗ Pipeline failed at data generation/upload")
                return False
        else:
            print("\n" + "=" * 70)
            print("Skipping data generation (using existing data)")
            print("=" * 70)
            self.results['steps']['data_generation'] = {'status': 'skipped'}
        
        # Step 4: Run Glue ETL jobs (simplified for demo)
        if not self.run_glue_etl_jobs():
            print("\n✗ Pipeline failed at ETL processing")
            return False
        
        # Step 5: Load data to Redshift
        if not self.load_data_to_redshift():
            print("\n✗ Pipeline failed at Redshift loading")
            return False
        
        # Step 6: Verify data quality
        if not self.verify_data_quality():
            print("\n✗ Pipeline failed at data verification")
            return False
        
        # Generate summary report
        self.generate_summary_report()
        
        print("\n" + "=" * 70)
        print("✓ Pipeline Execution Complete!")
        print("=" * 70)
        
        return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Execute end-to-end demo data pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Data generation parameters
    parser.add_argument('--artists', type=int, default=1000,
                       help='Number of artists to generate (default: 1000)')
    parser.add_argument('--venues', type=int, default=500,
                       help='Number of venues to generate (default: 500)')
    parser.add_argument('--concerts', type=int, default=10000,
                       help='Number of concerts to generate (default: 10000)')
    parser.add_argument('--sales', type=int, default=50000,
                       help='Number of ticket sales to generate (default: 50000)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    # Pipeline control
    parser.add_argument('--skip-generation', action='store_true',
                       help='Skip data generation and use existing S3 data')
    parser.add_argument('--raw-bucket', type=str, default='concert-data-raw',
                       help='S3 bucket for raw data (default: concert-data-raw)')
    parser.add_argument('--processed-bucket', type=str, default='concert-data-processed',
                       help='S3 bucket for processed data (default: concert-data-processed)')
    parser.add_argument('--iam-role', type=str, default='',
                       help='IAM role ARN for Redshift COPY operations')
    
    args = parser.parse_args()
    
    # Create generator config
    generator_config = GeneratorConfig(
        num_artists=args.artists,
        num_venues=args.venues,
        num_concerts=args.concerts,
        num_ticket_sales=args.sales,
        seed=args.seed
    )
    
    # Create pipeline config
    pipeline_config = {
        'raw_bucket': args.raw_bucket,
        'processed_bucket': args.processed_bucket,
        'raw_prefix': 'demo-data',
        'processed_prefix': 'processed',
        'iam_role': args.iam_role
    }
    
    # Run pipeline
    orchestrator = DemoPipelineOrchestrator(pipeline_config)
    
    try:
        success = orchestrator.run_pipeline(
            generator_config=generator_config,
            skip_generation=args.skip_generation
        )
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n✗ Pipeline failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
