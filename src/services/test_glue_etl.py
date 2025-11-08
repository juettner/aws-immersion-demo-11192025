"""
Tests for AWS Glue ETL jobs and data quality monitoring.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from ..infrastructure.glue_job_manager import GlueJobManager, DataQualityAlerting
from ..services.data_quality_service import DataQualityService, QualityRule, QualityResult


class TestGlueJobManager:
    """Test cases for Glue job management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.glue_manager = GlueJobManager()
    
    @patch('boto3.client')
    def test_upload_job_scripts(self, mock_boto_client):
        """Test uploading Glue job scripts to S3."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock successful bucket operations
        mock_s3.head_bucket.return_value = {}
        mock_s3.put_object.return_value = {}
        
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Test Glue script\nprint('Hello Glue')")
            script_path = f.name
        
        try:
            # Mock the file path
            with patch('builtins.open', mock_open_file(script_path)):
                results = self.glue_manager.upload_job_scripts()
            
            # Verify results
            assert isinstance(results, dict)
            assert len(results) == 3  # artist, venue, concert scripts
            
            # Verify S3 calls
            assert mock_s3.put_object.call_count == 3
            
        finally:
            os.unlink(script_path)
    
    @patch('boto3.client')
    def test_create_glue_job(self, mock_boto_client):
        """Test creating a new Glue job."""
        # Mock Glue client
        mock_glue = Mock()
        mock_boto_client.return_value = mock_glue
        
        # Mock job doesn't exist (will create new)
        mock_glue.get_job.side_effect = Exception("EntityNotFoundException")
        mock_glue.create_job.return_value = {}
        
        # Test job creation
        result = self.glue_manager.create_or_update_job(
            'artist-data-etl',
            'arn:aws:iam::123456789012:role/GlueServiceRole'
        )
        
        assert result is True
        mock_glue.create_job.assert_called_once()
    
    @patch('boto3.client')
    def test_start_job_run(self, mock_boto_client):
        """Test starting a Glue job run."""
        # Mock Glue client
        mock_glue = Mock()
        mock_boto_client.return_value = mock_glue
        
        # Mock successful job run start
        mock_glue.start_job_run.return_value = {'JobRunId': 'jr_test123'}
        
        # Test job run start
        job_run_id = self.glue_manager.start_job_run(
            'artist-data-etl',
            's3://test-bucket/input/',
            's3://test-bucket/output/',
            's3://test-bucket/duplicates/'
        )
        
        assert job_run_id == 'jr_test123'
        mock_glue.start_job_run.assert_called_once()
    
    @patch('boto3.client')
    def test_get_job_run_status(self, mock_boto_client):
        """Test getting job run status."""
        # Mock Glue client
        mock_glue = Mock()
        mock_boto_client.return_value = mock_glue
        
        # Mock job run status response
        mock_glue.get_job_run.return_value = {
            'JobRun': {
                'JobRunState': 'SUCCEEDED',
                'StartedOn': datetime.utcnow(),
                'CompletedOn': datetime.utcnow(),
                'ExecutionTime': 300
            }
        }
        
        # Test status retrieval
        status = self.glue_manager.get_job_run_status('artist-data-etl', 'jr_test123')
        
        assert status['job_run_state'] == 'SUCCEEDED'
        assert 'execution_time' in status
        mock_glue.get_job_run.assert_called_once()


class TestDataQualityService:
    """Test cases for data quality monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quality_service = DataQualityService()
    
    def test_quality_rules_initialization(self):
        """Test that quality rules are properly initialized."""
        rules = self.quality_service.quality_rules
        
        assert 'artists' in rules
        assert 'venues' in rules
        assert 'concerts' in rules
        
        # Check artist rules
        artist_rules = rules['artists']
        assert len(artist_rules) > 0
        assert any(rule.rule_id == 'artist_name_completeness' for rule in artist_rules)
        assert any(rule.rule_id == 'artist_id_uniqueness' for rule in artist_rules)
    
    def test_check_completeness(self):
        """Test data completeness checking."""
        # Create test data
        df = pd.DataFrame({
            'name': ['Artist 1', 'Artist 2', '', None, 'Artist 5'],
            'genre': ['rock', 'pop', 'jazz', 'blues', None]
        })
        
        # Test completeness for name column
        completeness_score = self.quality_service._check_completeness(df, 'name')
        assert completeness_score == 60.0  # 3 out of 5 valid names
        
        # Test completeness for genre column
        genre_score = self.quality_service._check_completeness(df, 'genre')
        assert genre_score == 80.0  # 4 out of 5 valid genres
    
    def test_check_uniqueness(self):
        """Test uniqueness checking."""
        # Create test data with duplicates
        df = pd.DataFrame({
            'artist_id': ['art_1', 'art_2', 'art_3', 'art_2', 'art_4'],
            'name': ['Artist 1', 'Artist 2', 'Artist 3', 'Artist 2 Duplicate', 'Artist 4']
        })
        
        # Test uniqueness for artist_id column
        uniqueness_score = self.quality_service._check_uniqueness(df, 'artist_id')
        assert uniqueness_score == 80.0  # 4 unique out of 5 total
    
    def test_check_range(self):
        """Test range validation."""
        # Create test data
        df = pd.DataFrame({
            'popularity_score': [85.5, 92.0, 150.0, -10.0, 75.5, None],
            'capacity': [1000, 5000, 250000, -100, 15000, 0]
        })
        
        # Test popularity score range (0-100)
        popularity_score = self.quality_service._check_range(df, 'popularity_score', 0, 100)
        assert popularity_score == 60.0  # 3 out of 5 valid scores
        
        # Test capacity range (1-200000)
        capacity_score = self.quality_service._check_range(df, 'capacity', 1, 200000)
        assert capacity_score == 50.0  # 3 out of 6 valid capacities
    
    def test_check_date_range(self):
        """Test date range validation."""
        # Create test data
        df = pd.DataFrame({
            'event_date': [
                '2024-07-15',
                '2025-12-31',
                '1900-01-01',  # Too old
                '2030-01-01',  # Too far in future
                '2023-06-15',
                'invalid-date'
            ]
        })
        
        # Test date range validation
        date_score = self.quality_service._check_date_range(df, 'event_date')
        assert date_score > 0  # Should have some valid dates
    
    def test_execute_quality_rule(self):
        """Test executing a quality rule."""
        # Create test data
        df = pd.DataFrame({
            'name': ['Artist 1', 'Artist 2', '', 'Artist 4'],
            'artist_id': ['art_1', 'art_2', 'art_3', 'art_4']
        })
        
        # Create a test rule
        rule = QualityRule(
            rule_id='test_completeness',
            rule_name='Test Completeness',
            rule_type='completeness',
            column_name='name',
            threshold=80.0,
            severity='warning',
            description='Test rule',
            validation_logic='not_null_and_not_empty'
        )
        
        # Execute the rule
        result = self.quality_service._execute_quality_rule(df, rule)
        
        assert isinstance(result, QualityResult)
        assert result.rule_id == 'test_completeness'
        assert result.score == 75.0  # 3 out of 4 valid names
        assert result.passed is False  # Below 80% threshold
    
    @patch('boto3.client')
    def test_validate_data_quality_success(self, mock_boto_client):
        """Test successful data quality validation."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock S3 list_objects_v2 response
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'test_data.json'}]
        }
        
        # Mock S3 get_object response
        test_data = pd.DataFrame({
            'artist_id': ['art_1', 'art_2', 'art_3'],
            'name': ['Artist 1', 'Artist 2', 'Artist 3'],
            'genre': ['rock', 'pop', 'jazz'],
            'popularity_score': [85.0, 92.0, 78.0]
        })
        
        mock_s3.get_object.return_value = {
            'Body': Mock(read=lambda: test_data.to_json().encode())
        }
        
        # Mock CloudWatch client
        mock_cloudwatch = Mock()
        
        # Patch the data loading method
        with patch.object(self.quality_service, '_load_data_from_s3', return_value=test_data):
            with patch.object(self.quality_service, '_send_quality_metrics'):
                result = self.quality_service.validate_data_quality('artists', 's3://test-bucket/data/')
        
        assert result['status'] in ['passed', 'warning', 'failed']
        assert 'overall_score' in result
        assert 'total_records' in result
        assert result['total_records'] == 3
    
    def test_coordinate_consistency(self):
        """Test coordinate consistency checking."""
        # Create test data with location information
        df = pd.DataFrame({
            'location': [
                {'latitude': 40.7505, 'longitude': -73.9934},  # Both present
                {'latitude': 34.0522, 'longitude': -118.2437},  # Both present
                {'latitude': 41.8781, 'longitude': None},  # Only lat
                {'latitude': None, 'longitude': None},  # Both absent
                {'latitude': None, 'longitude': -87.6298}  # Only lon
            ]
        })
        
        # Test coordinate consistency
        consistency_score = self.quality_service._check_coordinate_consistency(df)
        assert consistency_score == 60.0  # 3 out of 5 consistent (both present or both absent)
    
    def test_revenue_consistency(self):
        """Test revenue consistency checking."""
        # Create test data
        df = pd.DataFrame({
            'revenue': [50000, 75000, 1000000, 100],  # Last one is inconsistent
            'total_attendance': [1000, 1500, 2000, 1],  # Revenue per person: 50, 50, 500, 100
            'ticket_prices': [{'general': 50}, {'general': 50}, {'vip': 500}, {'general': 100}]
        })
        
        # Test revenue consistency
        consistency_score = self.quality_service._check_revenue_consistency(df)
        assert consistency_score > 0  # Should detect some consistency


def mock_open_file(file_path):
    """Mock file opening for testing."""
    def mock_open(*args, **kwargs):
        if args[0] == 'src/infrastructure/glue_etl_jobs.py':
            mock_file = Mock()
            mock_file.read.return_value = "# Mock Glue script content"
            mock_file.__enter__.return_value = mock_file
            mock_file.__exit__.return_value = None
            return mock_file
        else:
            # Fall back to real file opening for other files
            return open(*args, **kwargs)
    return mock_open


class TestDataQualityIntegration:
    """Integration tests for data quality monitoring."""
    
    @patch('boto3.client')
    def test_full_quality_pipeline(self, mock_boto_client):
        """Test the complete data quality monitoring pipeline."""
        # Mock AWS clients
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: {
            's3': mock_s3,
            'cloudwatch': mock_cloudwatch
        }[service]
        
        # Create test data for all data types
        test_data = {
            'artists': pd.DataFrame({
                'artist_id': ['art_1', 'art_2', 'art_3'],
                'name': ['Artist 1', 'Artist 2', 'Artist 3'],
                'genre': ['rock', 'pop', 'jazz'],
                'popularity_score': [85.0, 92.0, 78.0]
            }),
            'venues': pd.DataFrame({
                'venue_id': ['ven_1', 'ven_2', 'ven_3'],
                'name': ['Venue 1', 'Venue 2', 'Venue 3'],
                'capacity': [1000, 5000, 15000],
                'location': [
                    {'city': 'New York', 'latitude': 40.7505, 'longitude': -73.9934},
                    {'city': 'Los Angeles', 'latitude': 34.0522, 'longitude': -118.2437},
                    {'city': 'Chicago', 'latitude': 41.8781, 'longitude': -87.6298}
                ]
            }),
            'concerts': pd.DataFrame({
                'concert_id': ['con_1', 'con_2', 'con_3'],
                'artist_id': ['art_1', 'art_2', 'art_3'],
                'venue_id': ['ven_1', 'ven_2', 'ven_3'],
                'event_date': ['2024-07-15', '2024-08-20', '2024-09-10'],
                'total_attendance': [800, 4500, 12000],
                'revenue': [40000, 225000, 600000]
            })
        }
        
        # Mock S3 responses
        def mock_list_objects(Bucket, Prefix):
            data_type = Prefix.split('/')[0]
            if data_type in test_data:
                return {'Contents': [{'Key': f'{Prefix}test_data.json'}]}
            return {'Contents': []}
        
        def mock_get_object(Bucket, Key):
            data_type = Key.split('/')[0]
            if data_type in test_data:
                return {'Body': Mock(read=lambda: test_data[data_type].to_json().encode())}
            raise Exception("Object not found")
        
        mock_s3.list_objects_v2.side_effect = mock_list_objects
        mock_s3.get_object.side_effect = mock_get_object
        
        # Initialize quality service
        quality_service = DataQualityService()
        
        # Run quality monitoring pipeline
        data_paths = {
            'artists': 's3://test-bucket/artists/',
            'venues': 's3://test-bucket/venues/',
            'concerts': 's3://test-bucket/concerts/'
        }
        
        with patch.object(quality_service, '_send_quality_metrics'):
            with patch.object(quality_service, '_send_quality_alert'):
                results = quality_service.run_quality_monitoring_pipeline(data_paths)
        
        # Verify results
        assert 'pipeline_start_time' in results
        assert 'pipeline_end_time' in results
        assert 'data_types' in results
        assert 'overall_status' in results
        
        # Check that all data types were processed
        for data_type in ['artists', 'venues', 'concerts']:
            assert data_type in results['data_types']
            assert 'status' in results['data_types'][data_type]
            assert 'overall_score' in results['data_types'][data_type]


if __name__ == '__main__':
    pytest.main([__file__])