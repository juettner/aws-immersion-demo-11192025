"""
Integration tests for the complete ETL pipeline.
Tests end-to-end data flow from ingestion to warehouse, data quality validation,
and error handling/retry mechanisms.
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import pandas as pd


class TestETLPipelineIntegration:
    """Integration tests for the complete ETL pipeline."""
    
    @pytest.fixture
    def sample_artist_data(self):
        """Create sample artist data for testing."""
        return [
            {
                'artist_id': 'art_001',
                'name': 'The Rolling Stones',
                'genre': ['rock', 'blues rock'],
                'popularity_score': 85.5,
                'formation_date': '1962-07-12',
                'members': ['Mick Jagger', 'Keith Richards'],
                'spotify_id': '22bE4uQ6baNwSHPVcDxLCe'
            },
            {
                'artist_id': 'art_002',
                'name': 'Led Zeppelin',
                'genre': ['rock', 'hard rock'],
                'popularity_score': 92.3,
                'formation_date': '1968-09-07',
                'members': ['Robert Plant', 'Jimmy Page'],
                'spotify_id': '36QJpDe2go2KgaRleHCDTp'
            }
        ]
    
    @pytest.fixture
    def sample_venue_data(self):
        """Create sample venue data for testing."""
        return [
            {
                'venue_id': 'ven_001',
                'name': 'Madison Square Garden',
                'location': {
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'USA',
                    'latitude': 40.7505,
                    'longitude': -73.9934
                },
                'capacity': 20789,
                'venue_type': 'arena',
                'amenities': ['parking', 'concessions']
            }
        ]
    
    @pytest.fixture
    def sample_concert_data(self):
        """Create sample concert data for testing."""
        return [
            {
                'concert_id': 'con_001',
                'artist_id': 'art_001',
                'venue_id': 'ven_001',
                'event_date': '2024-07-15T20:00:00Z',
                'ticket_prices': {'general': 75.0, 'vip': 250.0},
                'total_attendance': 18500,
                'revenue': 1875000.0,
                'status': 'completed'
            }
        ]
    
    @pytest.fixture
    def temp_data_files(self, sample_artist_data, sample_venue_data, sample_concert_data):
        """Create temporary data files for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create JSON files
        artist_file = temp_dir / 'artists.json'
        with open(artist_file, 'w') as f:
            json.dump(sample_artist_data, f)
        
        venue_file = temp_dir / 'venues.json'
        with open(venue_file, 'w') as f:
            json.dump(sample_venue_data, f)
        
        concert_file = temp_dir / 'concerts.json'
        with open(concert_file, 'w') as f:
            json.dump(sample_concert_data, f)
        
        yield {
            'artists': artist_file,
            'venues': venue_file,
            'concerts': concert_file,
            'temp_dir': temp_dir
        }
        
        # Cleanup
        for file in temp_dir.glob('*'):
            file.unlink()
        temp_dir.rmdir()
    
    def test_file_processing_integration(self, temp_data_files):
        """Test file processing component of ETL pipeline."""
        from ..services.file_processor import FileUploadProcessor
        
        # Initialize file processor
        file_processor = FileUploadProcessor()
        
        # Process artist file
        result = file_processor.process_file_upload(
            temp_data_files['artists'],
            'artists'
        )
        
        # Verify processing results
        assert result.success is True
        assert result.records_processed == 2
        assert len(result.data) == 2
        assert result.data[0]['artist_id'] == 'art_001'
        assert result.data[1]['artist_id'] == 'art_002'
    
    @patch('boto3.client')
    def test_glue_job_workflow(self, mock_boto_client):
        """Test Glue ETL job workflow."""
        # Mock Glue and S3 clients
        mock_glue = Mock()
        mock_s3 = Mock()
        
        def get_client(service, **kwargs):
            if service == 'glue':
                return mock_glue
            elif service == 's3':
                return mock_s3
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        # Mock S3 operations
        mock_s3.head_bucket.return_value = {}
        mock_s3.put_object.return_value = {}
        
        # Mock Glue operations
        mock_glue.get_job.side_effect = Exception("EntityNotFoundException")
        mock_glue.create_job.return_value = {}
        mock_glue.start_job_run.return_value = {'JobRunId': 'jr_test123'}
        mock_glue.get_job_run.return_value = {
            'JobRun': {
                'JobRunState': 'SUCCEEDED',
                'StartedOn': datetime.utcnow(),
                'CompletedOn': datetime.utcnow(),
                'ExecutionTime': 300
            }
        }
        
        # Import with mocked boto3
        from ..infrastructure.glue_job_manager import GlueJobManager
        
        # Initialize Glue job manager
        glue_manager = GlueJobManager()
        
        # Test job creation
        job_created = glue_manager.create_or_update_job(
            'artist-data-etl',
            'arn:aws:iam::123456789012:role/GlueServiceRole'
        )
        assert job_created is True
        
        # Test job execution
        job_run_id = glue_manager.start_job_run(
            'artist-data-etl',
            's3://test-bucket/input/',
            's3://test-bucket/output/',
            's3://test-bucket/duplicates/'
        )
        assert job_run_id == 'jr_test123'
        
        # Test status check
        status = glue_manager.get_job_run_status('artist-data-etl', job_run_id)
        assert status['job_run_state'] == 'SUCCEEDED'
    
    @patch('boto3.client')
    def test_data_quality_validation(self, mock_boto_client):
        """Test data quality validation in pipeline."""
        # Create test data
        test_data = pd.DataFrame([
            {'artist_id': 'art_001', 'name': 'Artist 1', 'genre': ['rock'], 'popularity_score': 85.0},
            {'artist_id': 'art_002', 'name': 'Artist 2', 'genre': ['pop'], 'popularity_score': 90.0}
        ])
        
        # Mock S3 and CloudWatch
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        
        def get_client(service, **kwargs):
            if service == 's3':
                return mock_s3
            elif service == 'cloudwatch':
                return mock_cloudwatch
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        # Mock S3 operations
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'artists/data.json'}]
        }
        mock_s3.get_object.return_value = {
            'Body': Mock(read=lambda: test_data.to_json().encode())
        }
        
        # Import with mocked boto3
        from ..services.data_quality_service import DataQualityService
        
        # Initialize quality service
        quality_service = DataQualityService()
        
        # Run validation
        with patch.object(quality_service, '_send_quality_metrics'):
            with patch.object(quality_service, '_send_quality_alert'):
                result = quality_service.validate_data_quality(
                    'artists',
                    's3://test-bucket/artists/'
                )
        
        # Verify results
        assert 'status' in result
        assert result['status'] in ['passed', 'warning', 'failed']
        assert result['total_records'] == 2
        assert 'overall_score' in result
    
    @patch('psycopg2.connect')
    @patch('boto3.client')
    def test_redshift_loading_workflow(self, mock_boto_client, mock_psycopg2):
        """Test Redshift data loading workflow."""
        # Mock Redshift connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.description = None
        mock_psycopg2.return_value = mock_conn
        
        # Mock boto3 client
        mock_redshift = Mock()
        mock_boto_client.return_value = mock_redshift
        
        # Import with mocked dependencies
        from ..infrastructure.redshift_client import RedshiftClient
        
        # Initialize client
        redshift_client = RedshiftClient()
        
        # Test COPY command execution
        result = redshift_client.execute_copy_command(
            'concert_dw.artists',
            's3://test-bucket/artists/',
            'arn:aws:iam::123456789012:role/RedshiftRole'
        )
        
        # Verify execution
        assert result is True
        mock_cursor.execute.assert_called_once()
        
        # Verify COPY command structure
        call_args = mock_cursor.execute.call_args[0][0]
        assert 'COPY' in call_args
        assert 'concert_dw.artists' in call_args
        assert 's3://test-bucket/artists/' in call_args
    
    @patch('boto3.client')
    def test_error_handling_in_pipeline(self, mock_boto_client):
        """Test error handling and recovery mechanisms."""
        # Mock Glue client with failure scenario
        mock_glue = Mock()
        mock_s3 = Mock()
        
        def get_client(service, **kwargs):
            return mock_glue if service == 'glue' else mock_s3
        
        mock_boto_client.side_effect = get_client
        
        # Mock job failure
        mock_glue.get_job.side_effect = Exception("EntityNotFoundException")
        mock_glue.create_job.return_value = {}
        mock_glue.start_job_run.return_value = {'JobRunId': 'jr_fail'}
        mock_glue.get_job_run.return_value = {
            'JobRun': {
                'JobRunState': 'FAILED',
                'ErrorMessage': 'Data quality check failed',
                'StartedOn': datetime.utcnow(),
                'CompletedOn': datetime.utcnow()
            }
        }
        
        mock_s3.head_bucket.return_value = {}
        mock_s3.put_object.return_value = {}
        
        # Import with mocked boto3
        from ..infrastructure.glue_job_manager import GlueJobManager
        
        glue_manager = GlueJobManager()
        
        # Create and start job
        glue_manager.create_or_update_job(
            'artist-data-etl',
            'arn:aws:iam::123456789012:role/GlueRole'
        )
        
        job_run_id = glue_manager.start_job_run(
            'artist-data-etl',
            's3://test/input/',
            's3://test/output/'
        )
        
        # Verify failure is detected
        status = glue_manager.get_job_run_status('artist-data-etl', job_run_id)
        assert status['job_run_state'] == 'FAILED'
        assert 'error_message' in status
        assert 'Data quality check failed' in status['error_message']
    
    @patch('boto3.client')
    def test_data_transformation_accuracy(self, mock_boto_client):
        """Test data transformation accuracy with quality issues."""
        # Create test data with quality issues
        test_data = pd.DataFrame([
            {
                'artist_id': 'art_001',
                'name': '  The Rolling Stones  ',  # Extra whitespace
                'genre': 'rock,blues rock',  # Comma-separated string
                'popularity_score': 150.0,  # Out of range
                'formation_date': '1962-07-12'
            },
            {
                'artist_id': 'art_002',
                'name': 'Led Zeppelin!!!',  # Special characters
                'genre': 'rock;hard rock',  # Semicolon separator
                'popularity_score': -10.0,  # Negative value
                'formation_date': '1968-09-07'
            }
        ])
        
        # Mock S3 and CloudWatch
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        
        def get_client(service, **kwargs):
            if service == 's3':
                return mock_s3
            elif service == 'cloudwatch':
                return mock_cloudwatch
            return Mock()
        
        mock_boto_client.side_effect = get_client
        
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'artists/data.json'}]
        }
        mock_s3.get_object.return_value = {
            'Body': Mock(read=lambda: test_data.to_json().encode())
        }
        
        # Import with mocked boto3
        from ..services.data_quality_service import DataQualityService
        
        quality_service = DataQualityService()
        
        # Run validation
        with patch.object(quality_service, '_send_quality_metrics'):
            with patch.object(quality_service, '_send_quality_alert'):
                result = quality_service.validate_data_quality(
                    'artists',
                    's3://test-bucket/artists/'
                )
        
        # Verify transformation issues were detected
        assert result['status'] in ['warning', 'failed']
        assert result['total_records'] == 2
        
        # Check that quality rules detected issues
        results_by_rule = {r['rule_id']: r for r in result['results']}
        if 'popularity_score_validity' in results_by_rule:
            # Popularity scores out of range should fail
            assert results_by_rule['popularity_score_validity']['passed'] is False


class TestETLErrorRecovery:
    """Test error recovery and resilience in ETL pipeline."""
    
    @patch('boto3.client')
    def test_retry_mechanism_on_failure(self, mock_boto_client):
        """Test retry logic when operations fail."""
        mock_glue = Mock()
        mock_s3 = Mock()
        
        def get_client(service, **kwargs):
            return mock_glue if service == 'glue' else mock_s3
        
        mock_boto_client.side_effect = get_client
        
        # Simulate failure then success on retry
        mock_glue.get_job.side_effect = Exception("EntityNotFoundException")
        mock_glue.create_job.return_value = {}
        mock_glue.start_job_run.side_effect = [
            Exception("ThrottlingException"),  # First attempt fails
            {'JobRunId': 'jr_success'}  # Second attempt succeeds
        ]
        
        mock_s3.head_bucket.return_value = {}
        mock_s3.put_object.return_value = {}
        
        # Import with mocked boto3
        from ..infrastructure.glue_job_manager import GlueJobManager
        
        glue_manager = GlueJobManager()
        
        # Create job
        glue_manager.create_or_update_job(
            'artist-data-etl',
            'arn:aws:iam::123456789012:role/GlueRole'
        )
        
        # First attempt should fail
        try:
            job_run_id = glue_manager.start_job_run(
                'artist-data-etl',
                's3://test/input/',
                's3://test/output/'
            )
            assert False, "Should have raised exception"
        except Exception as e:
            assert "ThrottlingException" in str(e)
        
        # Retry should succeed
        job_run_id = glue_manager.start_job_run(
            'artist-data-etl',
            's3://test/input/',
            's3://test/output/'
        )
        assert job_run_id == 'jr_success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
