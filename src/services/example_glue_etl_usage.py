"""
Example usage of AWS Glue ETL jobs for concert data transformation.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from ..infrastructure.glue_job_manager import GlueJobManager, DataQualityAlerting
from ..services.data_quality_service import DataQualityService
from ..config.settings import settings


async def run_complete_etl_pipeline():
    """
    Example of running the complete ETL pipeline for concert data.
    """
    print("Starting Concert Data ETL Pipeline...")
    
    # Initialize managers
    glue_manager = GlueJobManager()
    quality_service = DataQualityService()
    quality_alerting = DataQualityAlerting()
    
    # Configuration
    execution_role_arn = "arn:aws:iam::123456789012:role/GlueServiceRole"  # Replace with actual role
    sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:data-quality-alerts"  # Replace with actual topic
    
    # Define data paths
    input_paths = {
        'artists': f's3://{settings.aws.s3_bucket_raw}/processed/artists/',
        'venues': f's3://{settings.aws.s3_bucket_raw}/processed/venues/',
        'concerts': f's3://{settings.aws.s3_bucket_raw}/processed/concerts/'
    }
    
    output_paths = {
        'artists': f's3://{settings.aws.s3_bucket_processed}/normalized/artists/',
        'venues': f's3://{settings.aws.s3_bucket_processed}/normalized/venues/',
        'concerts': f's3://{settings.aws.s3_bucket_processed}/normalized/concerts/',
        'artists_duplicates': f's3://{settings.aws.s3_bucket_processed}/duplicates/artists/',
        'venues_duplicates': f's3://{settings.aws.s3_bucket_processed}/duplicates/venues/'
    }
    
    try:
        # Step 1: Set up data quality monitoring
        print("Setting up data quality monitoring...")
        alarm_results = quality_alerting.create_quality_alarms(sns_topic_arn)
        print(f"Created {sum(alarm_results.values())} quality alarms")
        
        # Step 2: Run ETL pipeline
        print("Running ETL pipeline...")
        pipeline_results = glue_manager.run_etl_pipeline(
            input_paths=input_paths,
            output_paths=output_paths,
            execution_role_arn=execution_role_arn
        )
        
        print(f"ETL Pipeline Status: {pipeline_results['overall_status']}")
        
        # Print job results
        for job_name, job_result in pipeline_results['jobs'].items():
            print(f"  {job_name}: {job_result.get('status', 'Unknown')}")
            if 'error' in job_result:
                print(f"    Error: {job_result['error']}")
        
        # Step 3: Run data quality validation
        if pipeline_results['overall_status'] == 'SUCCEEDED':
            print("Running data quality validation...")
            
            quality_results = quality_service.run_quality_monitoring_pipeline(output_paths)
            print(f"Quality Monitoring Status: {quality_results['overall_status']}")
            
            # Print quality results
            for data_type, quality_result in quality_results['data_types'].items():
                print(f"  {data_type}: {quality_result.get('status', 'Unknown')} "
                      f"(Score: {quality_result.get('overall_score', 0):.1f}%)")
                
                if quality_result.get('critical_failures', 0) > 0:
                    print(f"    Critical Failures: {quality_result['critical_failures']}")
        
        # Step 4: Generate summary report
        summary_report = generate_pipeline_summary(pipeline_results, quality_results if 'quality_results' in locals() else None)
        print("\n" + "="*50)
        print("PIPELINE SUMMARY REPORT")
        print("="*50)
        print(json.dumps(summary_report, indent=2))
        
        return pipeline_results
        
    except Exception as e:
        print(f"Pipeline failed with error: {str(e)}")
        raise


def run_individual_etl_job(job_type: str, input_path: str, output_path: str):
    """
    Example of running an individual ETL job.
    
    Args:
        job_type: Type of job ('artist', 'venue', or 'concert')
        input_path: S3 path to input data
        output_path: S3 path for output data
    """
    print(f"Running individual {job_type} ETL job...")
    
    glue_manager = GlueJobManager()
    execution_role_arn = "arn:aws:iam::123456789012:role/GlueServiceRole"  # Replace with actual role
    
    # Map job type to job key
    job_key_map = {
        'artist': 'artist-data-etl',
        'venue': 'venue-data-etl', 
        'concert': 'concert-data-etl'
    }
    
    if job_type not in job_key_map:
        raise ValueError(f"Unknown job type: {job_type}")
    
    job_key = job_key_map[job_type]
    
    try:
        # Create/update the job
        print(f"Creating/updating Glue job: {job_key}")
        if not glue_manager.create_or_update_job(job_key, execution_role_arn):
            raise Exception(f"Failed to create/update job: {job_key}")
        
        # Start job run
        duplicates_path = None
        if job_type in ['artist', 'venue']:
            duplicates_path = output_path.replace('/normalized/', '/duplicates/')
        
        job_run_id = glue_manager.start_job_run(
            job_key=job_key,
            input_path=input_path,
            output_path=output_path,
            duplicates_output_path=duplicates_path
        )
        
        if not job_run_id:
            raise Exception(f"Failed to start job run for: {job_key}")
        
        print(f"Started job run: {job_run_id}")
        
        # Wait for completion
        print("Waiting for job to complete...")
        final_status = glue_manager.wait_for_job_completion(job_key, job_run_id)
        
        print(f"Job completed with status: {final_status.get('job_run_state', 'Unknown')}")
        
        if final_status.get('job_run_state') == 'SUCCEEDED':
            print(f"Job succeeded! Output written to: {output_path}")
            if duplicates_path:
                print(f"Duplicates report written to: {duplicates_path}")
        else:
            print(f"Job failed: {final_status.get('error_message', 'Unknown error')}")
        
        return final_status
        
    except Exception as e:
        print(f"Individual ETL job failed: {str(e)}")
        raise


def run_data_quality_check(data_type: str, data_path: str):
    """
    Example of running data quality validation on processed data.
    
    Args:
        data_type: Type of data ('artists', 'venues', or 'concerts')
        data_path: S3 path to the data to validate
    """
    print(f"Running data quality check for {data_type}...")
    
    quality_service = DataQualityService()
    
    try:
        # Run quality validation
        result = quality_service.validate_data_quality(data_type, data_path)
        
        print(f"Quality Check Status: {result['status']}")
        print(f"Overall Score: {result.get('overall_score', 0):.1f}%")
        print(f"Total Records: {result.get('total_records', 0)}")
        print(f"Rules Passed: {result.get('rules_passed', 0)}/{result.get('rules_evaluated', 0)}")
        
        if result.get('critical_failures', 0) > 0:
            print(f"Critical Failures: {result['critical_failures']}")
        
        # Print detailed rule results
        if 'results' in result:
            print("\nDetailed Rule Results:")
            for rule_result in result['results']:
                status_icon = "✓" if rule_result['passed'] else "✗"
                print(f"  {status_icon} {rule_result['rule_name']}: {rule_result['score']:.1f}% "
                      f"(threshold: {rule_result['threshold']}%)")
                
                if not rule_result['passed'] and rule_result['severity'] == 'critical':
                    print(f"    CRITICAL: {rule_result['message']}")
        
        return result
        
    except Exception as e:
        print(f"Data quality check failed: {str(e)}")
        raise


def generate_pipeline_summary(pipeline_results: Dict[str, Any], quality_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a comprehensive pipeline summary report."""
    summary = {
        'pipeline_execution': {
            'start_time': pipeline_results.get('pipeline_start_time'),
            'end_time': pipeline_results.get('pipeline_end_time'),
            'overall_status': pipeline_results.get('overall_status'),
            'jobs_executed': len(pipeline_results.get('jobs', {}))
        },
        'job_details': {},
        'data_quality': {},
        'recommendations': []
    }
    
    # Summarize job results
    for job_name, job_result in pipeline_results.get('jobs', {}).items():
        summary['job_details'][job_name] = {
            'status': job_result.get('status'),
            'execution_time': job_result.get('execution_time'),
            'error': job_result.get('error_message') if job_result.get('job_run_state') == 'FAILED' else None
        }
    
    # Summarize quality results
    if quality_results:
        summary['data_quality'] = {
            'overall_status': quality_results.get('overall_status'),
            'data_types_validated': len(quality_results.get('data_types', {}))
        }
        
        for data_type, quality_result in quality_results.get('data_types', {}).items():
            summary['data_quality'][data_type] = {
                'status': quality_result.get('status'),
                'score': quality_result.get('overall_score'),
                'critical_failures': quality_result.get('critical_failures', 0),
                'total_records': quality_result.get('total_records', 0)
            }
    
    # Generate recommendations
    if pipeline_results.get('overall_status') != 'SUCCEEDED':
        summary['recommendations'].append("Review failed ETL jobs and check input data quality")
    
    if quality_results and quality_results.get('overall_status') in ['failed', 'warning']:
        summary['recommendations'].append("Address data quality issues before proceeding to ML model training")
    
    if not summary['recommendations']:
        summary['recommendations'].append("Pipeline completed successfully - ready for ML model training")
    
    return summary


def main():
    """Main function demonstrating various ETL operations."""
    print("Concert Data ETL Examples")
    print("=" * 40)
    
    # Example 1: Run complete pipeline
    print("\n1. Running complete ETL pipeline...")
    try:
        asyncio.run(run_complete_etl_pipeline())
    except Exception as e:
        print(f"Complete pipeline failed: {str(e)}")
    
    # Example 2: Run individual job
    print("\n2. Running individual artist ETL job...")
    try:
        run_individual_etl_job(
            job_type='artist',
            input_path='s3://concert-data-raw/processed/artists/',
            output_path='s3://concert-data-processed/normalized/artists/'
        )
    except Exception as e:
        print(f"Individual job failed: {str(e)}")
    
    # Example 3: Run quality check
    print("\n3. Running data quality check...")
    try:
        run_data_quality_check(
            data_type='artists',
            data_path='s3://concert-data-processed/normalized/artists/'
        )
    except Exception as e:
        print(f"Quality check failed: {str(e)}")


if __name__ == "__main__":
    main()