"""
File upload processor for CSV, JSON, and XML formats.
Handles parsing, validation, and batch processing of uploaded concert data files.
"""
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, IO
import structlog
from pydantic import ValidationError

try:
    from ..models.artist import Artist
    from ..models.venue import Venue
    from ..models.concert import Concert
    from ..models.ticket_sale import TicketSale
    from .external_apis.ingestion_service import IngestionResult
except ImportError:
    # Fallback for standalone testing
    try:
        from models.artist import Artist
        from models.venue import Venue
        from models.concert import Concert
        from models.ticket_sale import TicketSale
        from services.external_apis.ingestion_service import IngestionResult
    except ImportError:
        # Create minimal classes for testing
        from pydantic import BaseModel
        
        class Artist(BaseModel):
            artist_id: str
            name: str
            
        class Venue(BaseModel):
            venue_id: str
            name: str
            
        class Concert(BaseModel):
            concert_id: str
            artist_id: str
            venue_id: str
            
        class TicketSale(BaseModel):
            sale_id: str
            concert_id: str
            
        class IngestionResult:
            def __init__(self, success, source, data_type, records_processed=0, records_successful=0, records_failed=0, errors=None, data=None):
                self.success = success
                self.source = source
                self.data_type = data_type
                self.records_processed = records_processed
                self.records_successful = records_successful
                self.records_failed = records_failed
                self.errors = errors or []
                self.data = data or []
                self.timestamp = datetime.utcnow()

logger = structlog.get_logger(__name__)


class ValidationResult:
    """Result of data validation operation."""
    
    def __init__(
        self,
        success: bool,
        valid_records: List[Dict[str, Any]] = None,
        invalid_records: List[Dict[str, Any]] = None,
        errors: List[str] = None
    ):
        self.success = success
        self.valid_records = valid_records or []
        self.invalid_records = invalid_records or []
        self.errors = errors or []
        self.timestamp = datetime.utcnow()
    
    @property
    def total_records(self) -> int:
        return len(self.valid_records) + len(self.invalid_records)
    
    @property
    def validation_rate(self) -> float:
        if self.total_records == 0:
            return 0.0
        return len(self.valid_records) / self.total_records


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass


class FileUploadProcessor:
    """
    Processor for handling file uploads in CSV, JSON, and XML formats.
    Provides parsing, validation, and batch processing capabilities.
    """
    
    SUPPORTED_FORMATS = ['csv', 'json', 'xml']
    SUPPORTED_DATA_TYPES = ['artists', 'venues', 'concerts', 'ticket_sales']
    
    # Model mapping for validation
    MODEL_MAPPING = {
        'artists': Artist,
        'venues': Venue,
        'concerts': Concert,
        'ticket_sales': TicketSale
    }
    
    def __init__(self, max_file_size_mb: int = 100, max_batch_size: int = 10000):
        """
        Initialize file processor with configuration.
        
        Args:
            max_file_size_mb: Maximum file size in megabytes
            max_batch_size: Maximum number of records to process in a batch
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_batch_size = max_batch_size
        self.logger = structlog.get_logger("FileUploadProcessor")
    
    def validate_file(self, file_path: Union[str, Path], data_type: str) -> None:
        """
        Validate file before processing.
        
        Args:
            file_path: Path to the file
            data_type: Type of data expected (artists, venues, concerts, ticket_sales)
            
        Raises:
            FileProcessingError: If file validation fails
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            raise FileProcessingError(f"File does not exist: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise FileProcessingError(
                f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum "
                f"allowed size ({self.max_file_size_bytes / 1024 / 1024}MB)"
            )
        
        # Check file format
        file_extension = file_path.suffix.lower().lstrip('.')
        if file_extension not in self.SUPPORTED_FORMATS:
            raise FileProcessingError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Check data type
        if data_type not in self.SUPPORTED_DATA_TYPES:
            raise FileProcessingError(
                f"Unsupported data type: {data_type}. "
                f"Supported types: {', '.join(self.SUPPORTED_DATA_TYPES)}"
            )
    
    def parse_csv_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse CSV file and return list of records.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of dictionaries representing records
            
        Raises:
            FileProcessingError: If CSV parsing fails
        """
        try:
            records = []
            with open(file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    # Clean empty values and strip whitespace
                    cleaned_row = {}
                    for key, value in row.items():
                        if key and value is not None:
                            cleaned_key = key.strip()
                            cleaned_value = value.strip() if isinstance(value, str) else value
                            if cleaned_value:  # Only include non-empty values
                                cleaned_row[cleaned_key] = cleaned_value
                    
                    if cleaned_row:  # Only add non-empty rows
                        cleaned_row['_source_row'] = row_num
                        records.append(cleaned_row)
            
            self.logger.info(f"Parsed CSV file with {len(records)} records", file_path=str(file_path))
            return records
            
        except Exception as e:
            raise FileProcessingError(f"Failed to parse CSV file: {str(e)}")
    
    def parse_json_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse JSON file and return list of records.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of dictionaries representing records
            
        Raises:
            FileProcessingError: If JSON parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects
                records = data
            elif isinstance(data, dict):
                # Single object or object with array property
                if 'data' in data and isinstance(data['data'], list):
                    records = data['data']
                elif 'records' in data and isinstance(data['records'], list):
                    records = data['records']
                elif 'items' in data and isinstance(data['items'], list):
                    records = data['items']
                else:
                    # Treat as single record
                    records = [data]
            else:
                raise FileProcessingError("JSON file must contain an object or array")
            
            # Add source information
            for i, record in enumerate(records):
                if isinstance(record, dict):
                    record['_source_row'] = i + 1
            
            self.logger.info(f"Parsed JSON file with {len(records)} records", file_path=str(file_path))
            return records
            
        except json.JSONDecodeError as e:
            raise FileProcessingError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"Failed to parse JSON file: {str(e)}")
    
    def parse_xml_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse XML file and return list of records.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            List of dictionaries representing records
            
        Raises:
            FileProcessingError: If XML parsing fails
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            records = []
            
            # Try to find record elements (common patterns)
            record_elements = []
            
            # Look for common record element names
            for pattern in ['record', 'item', 'row', 'entry', 'artist', 'venue', 'concert', 'ticket_sale']:
                elements = root.findall(f".//{pattern}")
                if elements:
                    record_elements = elements
                    break
            
            # If no common patterns found, use direct children
            if not record_elements:
                record_elements = list(root)
            
            for i, element in enumerate(record_elements):
                record = self._xml_element_to_dict(element)
                if record:  # Only add non-empty records
                    record['_source_row'] = i + 1
                    records.append(record)
            
            self.logger.info(f"Parsed XML file with {len(records)} records", file_path=str(file_path))
            return records
            
        except ET.ParseError as e:
            raise FileProcessingError(f"Invalid XML format: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"Failed to parse XML file: {str(e)}")
    
    def _xml_element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary.
        
        Args:
            element: XML element
            
        Returns:
            Dictionary representation of the element
        """
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # Leaf node
                result['value'] = element.text.strip()
            else:
                result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)
            
            if child.tag in result:
                # Handle multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def validate_data_quality(self, records: List[Dict[str, Any]], data_type: str) -> ValidationResult:
        """
        Validate data quality using Pydantic models.
        
        Args:
            records: List of record dictionaries
            data_type: Type of data being validated
            
        Returns:
            ValidationResult with valid and invalid records
        """
        model_class = self.MODEL_MAPPING.get(data_type)
        if not model_class:
            return ValidationResult(
                success=False,
                errors=[f"No validation model found for data type: {data_type}"]
            )
        
        valid_records = []
        invalid_records = []
        errors = []
        
        for i, record in enumerate(records):
            try:
                # Remove source metadata for validation
                validation_record = {k: v for k, v in record.items() if not k.startswith('_')}
                
                # Validate using Pydantic model
                validated_instance = model_class(**validation_record)
                
                # Convert back to dict and preserve source info
                validated_dict = validated_instance.dict()
                if '_source_row' in record:
                    validated_dict['_source_row'] = record['_source_row']
                
                valid_records.append(validated_dict)
                
            except ValidationError as e:
                error_msg = f"Row {record.get('_source_row', i+1)}: {str(e)}"
                errors.append(error_msg)
                
                # Add to invalid records with error info
                invalid_record = record.copy()
                invalid_record['_validation_errors'] = [str(err) for err in e.errors()]
                invalid_records.append(invalid_record)
                
            except Exception as e:
                error_msg = f"Row {record.get('_source_row', i+1)}: Unexpected validation error: {str(e)}"
                errors.append(error_msg)
                
                invalid_record = record.copy()
                invalid_record['_validation_errors'] = [error_msg]
                invalid_records.append(invalid_record)
        
        success = len(errors) == 0
        
        self.logger.info(
            "Data quality validation completed",
            total_records=len(records),
            valid_records=len(valid_records),
            invalid_records=len(invalid_records),
            validation_rate=len(valid_records) / len(records) if records else 0
        )
        
        return ValidationResult(
            success=success,
            valid_records=valid_records,
            invalid_records=invalid_records,
            errors=errors
        )
    
    def process_file_upload(
        self,
        file_path: Union[str, Path],
        data_type: str,
        validate_data: bool = True
    ) -> IngestionResult:
        """
        Process uploaded file with parsing and validation.
        
        Args:
            file_path: Path to the uploaded file
            data_type: Type of data in the file (artists, venues, concerts, ticket_sales)
            validate_data: Whether to perform data quality validation
            
        Returns:
            IngestionResult with processing results
        """
        file_path = Path(file_path)
        
        try:
            # Validate file
            self.validate_file(file_path, data_type)
            
            # Parse file based on format
            file_extension = file_path.suffix.lower().lstrip('.')
            
            if file_extension == 'csv':
                records = self.parse_csv_file(file_path)
            elif file_extension == 'json':
                records = self.parse_json_file(file_path)
            elif file_extension == 'xml':
                records = self.parse_xml_file(file_path)
            else:
                raise FileProcessingError(f"Unsupported file format: {file_extension}")
            
            # Validate data quality if requested
            validation_result = None
            if validate_data:
                validation_result = self.validate_data_quality(records, data_type)
                processed_records = validation_result.valid_records
                errors = validation_result.errors
            else:
                processed_records = records
                errors = []
            
            # Create ingestion result
            result = IngestionResult(
                success=len(errors) == 0,
                source="file_upload",
                data_type=data_type,
                records_processed=len(records),
                records_successful=len(processed_records),
                records_failed=len(records) - len(processed_records),
                errors=errors,
                data=processed_records
            )
            
            # Add validation metadata
            if validation_result:
                result.validation_rate = validation_result.validation_rate
                result.invalid_records = validation_result.invalid_records
            
            self.logger.info(
                "File processing completed",
                file_path=str(file_path),
                data_type=data_type,
                success=result.success,
                records_processed=result.records_processed,
                records_successful=result.records_successful
            )
            
            return result
            
        except FileProcessingError as e:
            self.logger.error("File processing failed", error=str(e), file_path=str(file_path))
            return IngestionResult(
                success=False,
                source="file_upload",
                data_type=data_type,
                errors=[str(e)]
            )
        except Exception as e:
            self.logger.error("Unexpected error during file processing", error=str(e), file_path=str(file_path))
            return IngestionResult(
                success=False,
                source="file_upload",
                data_type=data_type,
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    def process_batch_files(
        self,
        file_paths: List[Union[str, Path]],
        data_types: Union[str, List[str]],
        validate_data: bool = True
    ) -> Dict[str, IngestionResult]:
        """
        Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            data_types: Single data type or list of data types (one per file)
            validate_data: Whether to perform data quality validation
            
        Returns:
            Dictionary mapping file paths to ingestion results
        """
        if isinstance(data_types, str):
            data_types = [data_types] * len(file_paths)
        
        if len(file_paths) != len(data_types):
            raise ValueError("Number of file paths must match number of data types")
        
        results = {}
        
        for file_path, data_type in zip(file_paths, data_types):
            file_key = str(Path(file_path).name)
            
            try:
                result = self.process_file_upload(file_path, data_type, validate_data)
                results[file_key] = result
                
            except Exception as e:
                self.logger.error(
                    "Batch file processing failed",
                    file_path=str(file_path),
                    error=str(e)
                )
                results[file_key] = IngestionResult(
                    success=False,
                    source="file_upload",
                    data_type=data_type,
                    errors=[f"Batch processing error: {str(e)}"]
                )
        
        # Log batch summary
        total_files = len(results)
        successful_files = sum(1 for result in results.values() if result.success)
        total_records = sum(result.records_successful for result in results.values())
        
        self.logger.info(
            "Batch file processing completed",
            total_files=total_files,
            successful_files=successful_files,
            total_records=total_records
        )
        
        return results