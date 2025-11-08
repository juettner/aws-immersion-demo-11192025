"""
Tests for the file upload processor.
"""
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pathlib import Path
import tempfile
import pytest

from .file_processor import FileUploadProcessor, FileProcessingError, ValidationResult


class TestFileUploadProcessor:
    """Test cases for FileUploadProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = FileUploadProcessor(max_file_size_mb=10, max_batch_size=1000)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file_path in self.temp_dir.glob("*"):
            file_path.unlink()
        self.temp_dir.rmdir()
    
    def create_sample_csv_artists(self) -> Path:
        """Create sample CSV file with artist data."""
        file_path = self.temp_dir / "artists.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['artist_id', 'name', 'genre', 'popularity_score', 'formation_date', 'members', 'spotify_id'])
            writer.writerow(['art_001', 'The Rolling Stones', 'rock,blues rock', '85.5', '1962-07-12', 'Mick Jagger,Keith Richards', '22bE4uQ6baNwSHPVcDxLCe'])
            writer.writerow(['art_002', 'Led Zeppelin', 'rock,hard rock', '92.3', '1968-09-07', 'Robert Plant,Jimmy Page,John Paul Jones,John Bonham', '36QJpDe2go2KgaRleHCDTp'])
            writer.writerow(['art_003', 'Pink Floyd', 'progressive rock,psychedelic rock', '88.7', '1965-01-01', 'David Gilmour,Roger Waters,Nick Mason,Richard Wright', '0k17h0D3J5VfsdmQ1iZtE9'])
        
        return file_path
    
    def create_sample_json_venues(self) -> Path:
        """Create sample JSON file with venue data."""
        file_path = self.temp_dir / "venues.json"
        
        venues_data = [
            {
                "venue_id": "ven_001",
                "name": "Madison Square Garden",
                "location": {
                    "address": "4 Pennsylvania Plaza",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "postal_code": "10001",
                    "latitude": 40.7505,
                    "longitude": -73.9934
                },
                "capacity": 20789,
                "venue_type": "arena",
                "amenities": ["parking", "concessions", "merchandise", "vip_boxes"],
                "ticketmaster_id": "KovZpZAEkJ7A"
            },
            {
                "venue_id": "ven_002",
                "name": "Red Rocks Amphitheatre",
                "location": {
                    "address": "18300 W Alameda Pkwy",
                    "city": "Morrison",
                    "state": "CO",
                    "country": "USA",
                    "postal_code": "80465",
                    "latitude": 39.6654,
                    "longitude": -105.2057
                },
                "capacity": 9525,
                "venue_type": "amphitheater",
                "amenities": ["parking", "concessions", "outdoor_seating"],
                "ticketmaster_id": "KovZpZAJ6eA"
            }
        ]
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(venues_data, jsonfile, indent=2)
        
        return file_path
    
    def create_sample_xml_concerts(self) -> Path:
        """Create sample XML file with concert data."""
        file_path = self.temp_dir / "concerts.xml"
        
        root = ET.Element("concerts")
        
        # Concert 1
        concert1 = ET.SubElement(root, "concert")
        ET.SubElement(concert1, "concert_id").text = "con_001"
        ET.SubElement(concert1, "artist_id").text = "art_001"
        ET.SubElement(concert1, "venue_id").text = "ven_001"
        ET.SubElement(concert1, "event_date").text = "2024-07-15T20:00:00Z"
        
        prices1 = ET.SubElement(concert1, "ticket_prices")
        ET.SubElement(prices1, "general").text = "75.0"
        ET.SubElement(prices1, "premium").text = "125.0"
        ET.SubElement(prices1, "vip").text = "250.0"
        
        ET.SubElement(concert1, "total_attendance").text = "18500"
        ET.SubElement(concert1, "revenue").text = "1875000.0"
        ET.SubElement(concert1, "status").text = "completed"
        
        # Concert 2
        concert2 = ET.SubElement(root, "concert")
        ET.SubElement(concert2, "concert_id").text = "con_002"
        ET.SubElement(concert2, "artist_id").text = "art_002"
        ET.SubElement(concert2, "venue_id").text = "ven_002"
        ET.SubElement(concert2, "event_date").text = "2024-08-20T19:30:00Z"
        
        prices2 = ET.SubElement(concert2, "ticket_prices")
        ET.SubElement(prices2, "general").text = "65.0"
        ET.SubElement(prices2, "premium").text = "110.0"
        
        ET.SubElement(concert2, "status").text = "scheduled"
        
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        return file_path
    
    def create_invalid_csv_file(self) -> Path:
        """Create CSV file with invalid data."""
        file_path = self.temp_dir / "invalid_artists.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['artist_id', 'name', 'popularity_score'])
            writer.writerow(['', 'Empty ID Artist', '85.5'])  # Empty artist_id
            writer.writerow(['art_002', '', '92.3'])  # Empty name
            writer.writerow(['art_003', 'Valid Artist', '150.0'])  # Invalid popularity score (>100)
        
        return file_path
    
    def test_validate_file_success(self):
        """Test successful file validation."""
        file_path = self.create_sample_csv_artists()
        
        # Should not raise exception
        self.processor.validate_file(file_path, 'artists')
    
    def test_validate_file_not_exists(self):
        """Test validation with non-existent file."""
        with pytest.raises(FileProcessingError, match="File does not exist"):
            self.processor.validate_file("nonexistent.csv", 'artists')
    
    def test_validate_file_unsupported_format(self):
        """Test validation with unsupported file format."""
        file_path = self.temp_dir / "test.txt"
        file_path.write_text("test content")
        
        with pytest.raises(FileProcessingError, match="Unsupported file format"):
            self.processor.validate_file(file_path, 'artists')
    
    def test_validate_file_unsupported_data_type(self):
        """Test validation with unsupported data type."""
        file_path = self.create_sample_csv_artists()
        
        with pytest.raises(FileProcessingError, match="Unsupported data type"):
            self.processor.validate_file(file_path, 'invalid_type')
    
    def test_parse_csv_file(self):
        """Test CSV file parsing."""
        file_path = self.create_sample_csv_artists()
        records = self.processor.parse_csv_file(file_path)
        
        assert len(records) == 3
        assert records[0]['artist_id'] == 'art_001'
        assert records[0]['name'] == 'The Rolling Stones'
        assert records[0]['_source_row'] == 2  # First data row
    
    def test_parse_json_file(self):
        """Test JSON file parsing."""
        file_path = self.create_sample_json_venues()
        records = self.processor.parse_json_file(file_path)
        
        assert len(records) == 2
        assert records[0]['venue_id'] == 'ven_001'
        assert records[0]['name'] == 'Madison Square Garden'
        assert records[0]['_source_row'] == 1
    
    def test_parse_xml_file(self):
        """Test XML file parsing."""
        file_path = self.create_sample_xml_concerts()
        records = self.processor.parse_xml_file(file_path)
        
        assert len(records) == 2
        assert records[0]['concert_id'] == 'con_001'
        assert records[0]['artist_id'] == 'art_001'
        assert records[0]['_source_row'] == 1
    
    def test_validate_data_quality_valid(self):
        """Test data quality validation with valid data."""
        records = [
            {
                'artist_id': 'art_001',
                'name': 'Test Artist',
                'genre': ['rock'],
                'popularity_score': 75.0,
                '_source_row': 1
            }
        ]
        
        result = self.processor.validate_data_quality(records, 'artists')
        
        assert result.success is True
        assert len(result.valid_records) == 1
        assert len(result.invalid_records) == 0
        assert result.validation_rate == 1.0
    
    def test_validate_data_quality_invalid(self):
        """Test data quality validation with invalid data."""
        records = [
            {
                # Missing required field 'name' - should fail validation
                'artist_id': 'art_001',
                'popularity_score': 75.0,
                '_source_row': 1
            },
            {
                'artist_id': 'art_002',
                'name': 'Valid Artist',
                'popularity_score': 85.0,
                '_source_row': 2
            }
        ]
        
        result = self.processor.validate_data_quality(records, 'artists')
        
        # Should fail because first record is missing required 'name' field
        assert result.success is False
        assert len(result.valid_records) == 1  # Only the second record is valid
        assert len(result.invalid_records) == 1  # First record has validation error
        assert result.validation_rate == 0.5
        assert len(result.errors) > 0
    
    def test_process_file_upload_csv_success(self):
        """Test successful CSV file processing."""
        file_path = self.create_sample_csv_artists()
        result = self.processor.process_file_upload(file_path, 'artists')
        
        assert result.success is True
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'
        assert result.records_processed == 3
        assert result.records_successful > 0
        assert len(result.data) > 0
    
    def test_process_file_upload_json_success(self):
        """Test successful JSON file processing."""
        file_path = self.create_sample_json_venues()
        result = self.processor.process_file_upload(file_path, 'venues')
        
        assert result.success is True
        assert result.source == 'file_upload'
        assert result.data_type == 'venues'
        assert result.records_processed == 2
        assert result.records_successful > 0
        assert len(result.data) > 0
    
    def test_process_file_upload_xml_success(self):
        """Test successful XML file processing."""
        file_path = self.create_sample_xml_concerts()
        result = self.processor.process_file_upload(file_path, 'concerts')
        
        assert result.success is True
        assert result.source == 'file_upload'
        assert result.data_type == 'concerts'
        assert result.records_processed == 2
        assert len(result.data) > 0
    
    def test_process_file_upload_with_validation_errors(self):
        """Test file processing with validation errors."""
        file_path = self.create_invalid_csv_file()
        result = self.processor.process_file_upload(file_path, 'artists')
        
        assert result.success is False
        assert result.records_processed > 0
        assert result.records_failed > 0
        assert len(result.errors) > 0
    
    def create_malformed_csv_file(self) -> Path:
        """Create CSV file with malformed data."""
        file_path = self.temp_dir / "malformed_artists.csv"
        
        # Create CSV with inconsistent columns and malformed data
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvfile.write('artist_id,name,popularity_score\n')
            csvfile.write('art_001,"Artist with "quotes"",85.5\n')  # Malformed quotes
            csvfile.write('art_002,Artist 2,not_a_number\n')  # Invalid number
            csvfile.write('art_003\n')  # Missing columns
            csvfile.write(',,""\n')  # Empty values
        
        return file_path
    
    def create_large_csv_file(self) -> Path:
        """Create large CSV file to test batch processing limits."""
        file_path = self.temp_dir / "large_artists.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['artist_id', 'name', 'genre', 'popularity_score'])
            
            # Create more records than batch size
            for i in range(1500):  # Exceeds default batch size of 1000
                writer.writerow([f'art_{i:04d}', f'Artist {i}', 'rock', str(50 + (i % 50))])
        
        return file_path
    
    def create_corrupted_json_file(self) -> Path:
        """Create JSON file with syntax errors."""
        file_path = self.temp_dir / "corrupted_venues.json"
        
        # Invalid JSON with trailing comma and missing bracket
        json_content = '''[
            {
                "venue_id": "ven_001",
                "name": "Test Venue 1",
                "capacity": 1000,
            },
            {
                "venue_id": "ven_002",
                "name": "Test Venue 2",
                "capacity": 2000
            }
        '''  # Missing closing bracket
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            jsonfile.write(json_content)
        
        return file_path
    
    def create_empty_xml_file(self) -> Path:
        """Create empty XML file."""
        file_path = self.temp_dir / "empty_concerts.xml"
        
        with open(file_path, 'w', encoding='utf-8') as xmlfile:
            xmlfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<concerts></concerts>')
        
        return file_path
    
    def create_mixed_encoding_file(self) -> Path:
        """Create file with mixed character encoding issues."""
        file_path = self.temp_dir / "mixed_encoding.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['artist_id', 'name', 'genre'])
            writer.writerow(['art_001', 'Café Tacvba', 'rock'])  # Unicode characters
            writer.writerow(['art_002', 'Sigur Rós', 'post-rock'])  # Special characters
            writer.writerow(['art_003', 'Мумий Тролль', 'rock'])  # Cyrillic characters
        
        return file_path
    
    def test_process_malformed_csv_file(self):
        """Test processing CSV file with malformed data."""
        file_path = self.create_malformed_csv_file()
        
        # Should handle malformed data gracefully
        result = self.processor.process_file_upload(file_path, 'artists')
        
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'
        # Some records may be processed despite malformation
        assert result.records_processed >= 0
    
    def test_process_large_csv_file(self):
        """Test processing large CSV file that exceeds batch size."""
        file_path = self.create_large_csv_file()
        result = self.processor.process_file_upload(file_path, 'artists')
        
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'
        assert result.records_processed == 1500
        # Should process all records even if exceeding batch size
        assert result.records_successful > 0
    
    def test_process_corrupted_json_file(self):
        """Test processing corrupted JSON file."""
        file_path = self.create_corrupted_json_file()
        result = self.processor.process_file_upload(file_path, 'venues')
        
        assert result.success is False
        assert result.source == 'file_upload'
        assert result.data_type == 'venues'
        assert len(result.errors) > 0
        assert any("JSON" in error for error in result.errors)
    
    def test_process_empty_xml_file(self):
        """Test processing empty XML file."""
        file_path = self.create_empty_xml_file()
        result = self.processor.process_file_upload(file_path, 'concerts')
        
        assert result.success is True  # Empty file is valid
        assert result.source == 'file_upload'
        assert result.data_type == 'concerts'
        assert result.records_processed == 0
        assert len(result.data) == 0
    
    def test_process_mixed_encoding_file(self):
        """Test processing file with mixed character encodings."""
        file_path = self.create_mixed_encoding_file()
        result = self.processor.process_file_upload(file_path, 'artists')
        
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'
        assert result.records_processed == 3
        # Should handle Unicode characters properly
        assert any('Café Tacvba' in str(record) for record in result.data)
    
    def test_file_size_validation(self):
        """Test file size validation."""
        # Create processor with very small max file size
        small_processor = FileUploadProcessor(max_file_size_mb=0.0001)  # 100 bytes limit
        
        file_path = self.create_sample_csv_artists()
        
        # Check actual file size first
        file_size = file_path.stat().st_size
        max_allowed = small_processor.max_file_size_bytes
        
        if file_size > max_allowed:
            with pytest.raises(FileProcessingError, match="exceeds maximum allowed size"):
                small_processor.validate_file(file_path, 'artists')
        else:
            # If file is smaller than limit, create a larger file
            large_file = self.temp_dir / "large_file.csv"
            with open(large_file, 'w') as f:
                f.write('artist_id,name\n')
                f.write('x' * (max_allowed + 100))  # Exceed the limit
            
            with pytest.raises(FileProcessingError, match="exceeds maximum allowed size"):
                small_processor.validate_file(large_file, 'artists')
    
    def test_unsupported_file_extension(self):
        """Test handling of unsupported file extensions."""
        file_path = self.temp_dir / "test.pdf"
        file_path.write_text("dummy content")
        
        with pytest.raises(FileProcessingError, match="Unsupported file format"):
            self.processor.validate_file(file_path, 'artists')
    
    def test_data_quality_validation_edge_cases(self):
        """Test data quality validation with edge cases."""
        # Test with records containing None values, empty strings, etc.
        edge_case_records = [
            {
                'artist_id': 'art_001',
                'name': None,  # None value
                'popularity_score': 75.0,
                '_source_row': 1
            },
            {
                'artist_id': '',  # Empty string
                'name': 'Valid Artist',
                'popularity_score': 85.0,
                '_source_row': 2
            },
            {
                'artist_id': 'art_003',
                'name': 'Another Artist',
                'popularity_score': '75.5',  # String number
                '_source_row': 3
            }
        ]
        
        result = self.processor.validate_data_quality(edge_case_records, 'artists')
        
        assert result.success is False
        assert len(result.invalid_records) > 0
        assert len(result.errors) > 0
        assert result.validation_rate < 1.0
    
    def test_process_batch_files(self):
        """Test batch file processing."""
        csv_file = self.create_sample_csv_artists()
        json_file = self.create_sample_json_venues()
        
        file_paths = [csv_file, json_file]
        data_types = ['artists', 'venues']
        
        results = self.processor.process_batch_files(file_paths, data_types)
        
        assert len(results) == 2
        assert 'artists.csv' in results
        assert 'venues.json' in results
        
        for result in results.values():
            assert result.source == 'file_upload'
            assert result.records_processed > 0


def test_file_processor_integration():
    """Integration test for file processor functionality."""
    processor = FileUploadProcessor()
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a simple CSV file
        csv_file = temp_path / "test_artists.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['artist_id', 'name', 'genre', 'popularity_score'])
            writer.writerow(['test_001', 'Test Band', 'rock', '75.5'])
        
        # Process the file
        result = processor.process_file_upload(csv_file, 'artists')
        
        # Verify results
        assert result.source == 'file_upload'
        assert result.data_type == 'artists'
        assert result.records_processed == 1


if __name__ == "__main__":
    # Run basic integration test
    test_file_processor_integration()
    print("File processor integration test passed!")