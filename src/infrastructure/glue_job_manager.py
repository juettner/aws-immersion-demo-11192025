"""
AWS Glue job management and deployment utilities.
"""
import boto3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
from botocore.exceptions import ClientError
import structlog

from ..config.settings import settings

logger = structlog.get_logger(__name__)


class GlueJobManager:
    """Manage AWS Glue ETL jobs for concert data processing."""
    
    def __init__(self):
        self.glue_client = boto3.client('glue', **settings.get_aws_credentials())
        self.s3_client = boto3.client('s3', **settings.get_aws_credentials())
        self.logger = structlog.get_logger("GlueJobManager")
        
        # Job configurations
        self.job_configs = {
            'artist-data-etl': {
                'name': 'concert-artist-data-etl',
                'description': 'ETL job for normalizing and deduplicating artist data',
                'script_location': 's3://concert-glue-scripts/artist_etl.py',
                'max_capacity': 2.0,
                'timeout': 60,
                'max_retries': 2
            },
            'venue-data-etl': {
                'name': 'concert-venue-data-etl', 
                'description': 'ETL job for normalizing and deduplicating venue data',
                'script_location': 's3://concert-glue-scripts/venue_etl.py',
                'max_capacity': 2.0,
                'timeout': 60,
                'max_retries': 2
            },
            'concert-data-etl': {
                'name': 'concert-event-data-etl',
                'description': 'ETL job for normalizing concert/event data',
                'script_location': 's3://concert-glue-scripts/concert_etl.py',
                'max_capacity': 2.0,
                'timeout': 60,
                'max_retries': 2
            }
        }
    
    def upload_job_scripts(self, script_bucket: str = "concert-glue-scripts") -> Dict[str, bool]:
        """Upload Glue job scripts to S3."""
        results = {}
        
        # Create bucket if it doesn't exist
        try:
            self.s3_client.head_bucket(Bucket=script_bucket)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=script_bucket)
                    self.logger.info(f"Created S3 bucket for Glue scripts: {script_bucket}")
                except ClientError as create_error:
                    self.logger.error(f"Failed to create bucket {script_bucket}: {str(create_error)}")
                    return results
        
        # Read the main ETL script
        try:
            with open('src/infrastructure/glue_etl_jobs.py', 'r') as f:
                script_content = f.read()
        except FileNotFoundError:
            self.logger.error("Glue ETL script file not found")
            return results
        
        # Upload scripts for each job type
        script_uploads = {
            'artist_etl.py': script_content,
            'venue_etl.py': script_content,
            'concert_etl.py': script_content
        }
        
        for script_name, content in script_uploads.items():
            try:
                self.s3_client.put_object(
                    Bucket=script_bucket,
                    Key=script_name,
                    Body=content,
                    ContentType='text/plain'
                )
                results[script_name] = True
                self.logger.info(f"Uploaded Glue script: {script_name}")
            except ClientError as e:
                self.logger.error(f"Failed to upload script {script_name}: {str(e)}")
                results[script_name] = False
        
        return results
    
    def create_or_update_job(self, job_key: str, execution_role_arn: str) -> bool:
        """Create or update a Glue job."""
        if job_key not in self.job_configs:
            self.logger.error(f"Unknown job key: {job_key}")
            return False
        
        config = self.job_configs[job_key]
        job_name = config['name']
        
        # Job definition
        job_definition = {
            'Name': job_name,
            'Description': config['description'],
            'Role': execution_role_arn,
            'Command': {
                'Name': 'glueetl',
                'ScriptLocation': config['script_location'],
                'PythonVersion': '3'
            },
            'DefaultArguments': {
                '--job-language': 'python',
                '--job-bookmark-option': 'job-bookmark-enable',
                '--enable-metrics': 'true',
                '--enable-continuous-cloudwatch-log': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': f's3://{settings.aws.s3_bucket_processed}/spark-logs/',
                '--additional-python-modules': 'fuzzywuzzy,python-levenshtein,structlog'
            },
            'MaxCapacity': config['max_capacity'],
            'Timeout': config['timeout'],
            'MaxRetries': config['max_retries'],
            'GlueVersion': '3.0'
        }
        
        try:
            # Check if job exists
            try:
                self.glue_client.get_job(JobName=job_name)
                # Job exists, update it
                job_update = {k: v for k, v in job_definition.items() if k != 'Name'}
                self.glue_client.update_job(JobName=job_name, JobUpdate=job_update)
                self.logger.info(f"Updated Glue job: {job_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityNotFoundException':
                    # Job doesn't exist, create it
                    self.glue_client.create_job(**job_definition)
                    self.logger.info(f"Created Glue job: {job_name}")
                else:
                    raise
            
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to create/update job {job_name}: {str(e)}")
            return False
    
    def start_job_run(
        self,
        job_key: str,
        input_path: str,
        output_path: str,
        duplicates_output_path: Optional[str] = None,
        additional_args: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Start a Glue job run."""
        if job_key not in self.job_configs:
            self.logger.error(f"Unknown job key: {job_key}")
            return None
        
        job_name = self.job_configs[job_key]['name']
        
        # Prepare job arguments
        job_args = {
            '--input_path': input_path,
            '--output_path': output_path
        }
        
        if duplicates_output_path:
            job_args['--duplicates_output_path'] = duplicates_output_path
        
        if additional_args:
            job_args.update(additional_args)
        
        try:
            response = self.glue_client.start_job_run(
                JobName=job_name,
                Arguments=job_args
            )
            
            job_run_id = response['JobRunId']
            self.logger.info(f"Started Glue job run: {job_name} (ID: {job_run_id})")
            return job_run_id
            
        except ClientError as e:
            self.logger.error(f"Failed to start job run for {job_name}: {str(e)}")
            return None
    
    def get_job_run_status(self, job_key: str, job_run_id: str) -> Dict[str, Any]:
        """Get the status of a Glue job run."""
        if job_key not in self.job_configs:
            return {'error': f'Unknown job key: {job_key}'}
        
        job_name = self.job_configs[job_key]['name']
        
        try:
            response = self.glue_client.get_job_run(
                JobName=job_name,
                RunId=job_run_id
            )
            
            job_run = response['JobRun']
            
            return {
                'job_name': job_name,
                'job_run_id': job_run_id,
                'job_run_state': job_run['JobRunState'],
                'started_on': job_run.get('StartedOn'),
                'completed_on': job_run.get('CompletedOn'),
                'execution_time': job_run.get('ExecutionTime'),
                'error_message': job_run.get('ErrorMessage'),
                'log_group_name': job_run.get('LogGroupName')
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to get job run status: {str(e)}")
            return {'error': str(e)}
    
    def wait_for_job_completion(
        self,
        job_key: str,
        job_run_id: str,
        max_wait_time: int = 3600,
        poll_interval: int = 30
    ) -> Dict[str, Any]:
        """Wait for a Glue job to complete."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_job_run_status(job_key, job_run_id)
            
            if 'error' in status:
                return status
            
            job_state = status['job_run_state']
            
            if job_state in ['SUCCEEDED', 'FAILED', 'STOPPED', 'TIMEOUT']:
                return status
            
            self.logger.info(f"Job {job_run_id} status: {job_state}, waiting...")
            time.sleep(poll_interval)
        
        return {
            'error': f'Job {job_run_id} did not complete within {max_wait_time} seconds',
            'timeout': True
        }
    
    def list_job_runs(self, job_key: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """List recent job runs for a specific job."""
        if job_key not in self.job_configs:
            return []
        
        job_name = self.job_configs[job_key]['name']
        
        try:
            response = self.glue_client.get_job_runs(
                JobName=job_name,
                MaxResults=max_results
            )
            
            job_runs = []
            for run in response['JobRuns']:
                job_runs.append({
                    'job_run_id': run['Id'],
                    'job_run_state': run['JobRunState'],
                    'started_on': run.get('StartedOn'),
                    'completed_on': run.get('CompletedOn'),
                    'execution_time': run.get('ExecutionTime'),
                    'error_message': run.get('ErrorMessage')
                })
            
            return job_runs
            
        except ClientError as e:
            self.logger.error(f"Failed to list job runs for {job_name}: {str(e)}")
            return []
    
    def create_data_quality_crawler(self, crawler_name: str, database_name: str, s3_path: str) -> bool:
        """Create a Glue crawler for data quality monitoring."""
        try:
            crawler_config = {
                'Name': crawler_name,
                'Role': settings.aws.lakeformation_admin_role,
                'DatabaseName': database_name,
                'Targets': {
                    'S3Targets': [
                        {
                            'Path': s3_path,
                            'Exclusions': ['**/_SUCCESS', '**/_metadata']
                        }
                    ]
                },
                'SchemaChangePolicy': {
                    'UpdateBehavior': 'UPDATE_IN_DATABASE',
                    'DeleteBehavior': 'LOG'
                },
                'Configuration': json.dumps({
                    'Version': 1.0,
                    'CrawlerOutput': {
                        'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'},
                        'Tables': {'AddOrUpdateBehavior': 'MergeNewColumns'}
                    }
                })
            }
            
            # Check if crawler exists
            try:
                self.glue_client.get_crawler(Name=crawler_name)
                # Crawler exists, update it
                self.glue_client.update_crawler(**crawler_config)
                self.logger.info(f"Updated Glue crawler: {crawler_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityNotFoundException':
                    # Crawler doesn't exist, create it
                    self.glue_client.create_crawler(**crawler_config)
                    self.logger.info(f"Created Glue crawler: {crawler_name}")
                else:
                    raise
            
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to create/update crawler {crawler_name}: {str(e)}")
            return False
    
    def run_etl_pipeline(
        self,
        input_paths: Dict[str, str],
        output_paths: Dict[str, str],
        execution_role_arn: str
    ) -> Dict[str, Any]:
        """Run the complete ETL pipeline for all data types."""
        results = {
            'pipeline_start_time': datetime.utcnow().isoformat(),
            'jobs': {},
            'overall_status': 'RUNNING'
        }
        
        # Upload scripts first
        script_upload_results = self.upload_job_scripts()
        if not all(script_upload_results.values()):
            results['overall_status'] = 'FAILED'
            results['error'] = 'Failed to upload job scripts'
            return results
        
        # Create/update jobs
        for job_key in self.job_configs.keys():
            if not self.create_or_update_job(job_key, execution_role_arn):
                results['overall_status'] = 'FAILED'
                results['error'] = f'Failed to create/update job: {job_key}'
                return results
        
        # Start job runs
        job_run_ids = {}
        
        for job_key in ['artist-data-etl', 'venue-data-etl', 'concert-data-etl']:
            if job_key.replace('-data-etl', 's') in input_paths:
                data_type = job_key.replace('-data-etl', 's')
                
                duplicates_path = None
                if job_key in ['artist-data-etl', 'venue-data-etl']:
                    duplicates_path = output_paths.get(f'{data_type}_duplicates')
                
                job_run_id = self.start_job_run(
                    job_key,
                    input_paths[data_type],
                    output_paths[data_type],
                    duplicates_path
                )
                
                if job_run_id:
                    job_run_ids[job_key] = job_run_id
                    results['jobs'][job_key] = {
                        'job_run_id': job_run_id,
                        'status': 'RUNNING',
                        'start_time': datetime.utcnow().isoformat()
                    }
                else:
                    results['jobs'][job_key] = {
                        'status': 'FAILED',
                        'error': 'Failed to start job run'
                    }
        
        # Wait for all jobs to complete
        all_succeeded = True
        for job_key, job_run_id in job_run_ids.items():
            self.logger.info(f"Waiting for job {job_key} to complete...")
            
            final_status = self.wait_for_job_completion(job_key, job_run_id)
            results['jobs'][job_key].update(final_status)
            
            if final_status.get('job_run_state') != 'SUCCEEDED':
                all_succeeded = False
        
        results['overall_status'] = 'SUCCEEDED' if all_succeeded else 'FAILED'
        results['pipeline_end_time'] = datetime.utcnow().isoformat()
        
        return results


class DataQualityAlerting:
    """Handle data quality monitoring and alerting."""
    
    def __init__(self):
        self.sns_client = boto3.client('sns', **settings.get_aws_credentials())
        self.cloudwatch_client = boto3.client('cloudwatch', **settings.get_aws_credentials())
        self.logger = structlog.get_logger("DataQualityAlerting")
    
    def create_quality_alarms(self, sns_topic_arn: str) -> Dict[str, bool]:
        """Create CloudWatch alarms for data quality metrics."""
        alarms = {
            'ArtistDataQualityLow': {
                'alarm_name': 'ConcertPlatform-ArtistDataQuality-Low',
                'metric_name': 'ArtistDataQualityScore',
                'threshold': 70.0,
                'comparison_operator': 'LessThanThreshold'
            },
            'VenueDataQualityLow': {
                'alarm_name': 'ConcertPlatform-VenueDataQuality-Low',
                'metric_name': 'VenueDataQualityScore', 
                'threshold': 70.0,
                'comparison_operator': 'LessThanThreshold'
            },
            'ConcertDataQualityLow': {
                'alarm_name': 'ConcertPlatform-ConcertDataQuality-Low',
                'metric_name': 'ConcertDataQualityScore',
                'threshold': 70.0,
                'comparison_operator': 'LessThanThreshold'
            },
            'HighDuplicateRate': {
                'alarm_name': 'ConcertPlatform-HighDuplicateRate',
                'metric_name': 'ArtistDuplicatePercentage',
                'threshold': 10.0,
                'comparison_operator': 'GreaterThanThreshold'
            }
        }
        
        results = {}
        
        for alarm_key, config in alarms.items():
            try:
                self.cloudwatch_client.put_metric_alarm(
                    AlarmName=config['alarm_name'],
                    ComparisonOperator=config['comparison_operator'],
                    EvaluationPeriods=1,
                    MetricName=config['metric_name'],
                    Namespace='ConcertDataPlatform/DataQuality',
                    Period=300,
                    Statistic='Average',
                    Threshold=config['threshold'],
                    ActionsEnabled=True,
                    AlarmActions=[sns_topic_arn],
                    AlarmDescription=f'Data quality alarm for {config["metric_name"]}',
                    Unit='Percent' if 'Percentage' in config['metric_name'] or 'Score' in config['metric_name'] else 'Count'
                )
                
                results[alarm_key] = True
                self.logger.info(f"Created alarm: {config['alarm_name']}")
                
            except ClientError as e:
                self.logger.error(f"Failed to create alarm {config['alarm_name']}: {str(e)}")
                results[alarm_key] = False
        
        return results
    
    def send_quality_report(self, topic_arn: str, quality_metrics: Dict[str, Any]) -> bool:
        """Send data quality report via SNS."""
        try:
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'quality_metrics': quality_metrics,
                'summary': f"Data quality report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
            
            self.sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message, indent=2),
                Subject='Concert Data Platform - Quality Report'
            )
            
            self.logger.info("Data quality report sent successfully")
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to send quality report: {str(e)}")
            return False