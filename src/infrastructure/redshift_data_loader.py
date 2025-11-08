"""
Redshift data loading utilities with optimized COPY commands.
Handles efficient data loading from S3 to Redshift tables.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from .redshift_client import RedshiftClient

logger = logging.getLogger(__name__)


class RedshiftDataLoader:
    """Handles data loading operations from S3 to Redshift."""
    
    def __init__(self, client: RedshiftClient, iam_role: str):
        """Initialize with Redshift client and IAM role for COPY operations."""
        self.client = client
        self.iam_role = iam_role
        self.schema_name = 'concert_dw'
    
    def load_artists_data(self, s3_path: str) -> bool:
        """Load artists data from S3 using optimized COPY command."""
        table_name = f"{self.schema_name}.artists"
        
        copy_query = f"""
        COPY {table_name} (
            artist_id,
            name,
            genre,
            popularity_score,
            formation_date,
            members,
            spotify_id,
            created_at,
            updated_at
        )
        FROM '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS JSON 'auto'
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(table_name, copy_query, s3_path)
    
    def load_venues_data(self, s3_path: str) -> bool:
        """Load venues data from S3 using optimized COPY command."""
        table_name = f"{self.schema_name}.venues"
        
        copy_query = f"""
        COPY {table_name} (
            venue_id,
            name,
            address,
            city,
            state,
            country,
            postal_code,
            latitude,
            longitude,
            capacity,
            venue_type,
            amenities,
            ticketmaster_id,
            created_at,
            updated_at
        )
        FROM '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS JSON 'auto'
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(table_name, copy_query, s3_path)
    
    def load_concerts_data(self, s3_path: str) -> bool:
        """Load concerts data from S3 using optimized COPY command."""
        table_name = f"{self.schema_name}.concerts"
        
        copy_query = f"""
        COPY {table_name} (
            concert_id,
            artist_id,
            venue_id,
            event_date,
            ticket_prices,
            total_attendance,
            revenue,
            status,
            created_at,
            updated_at
        )
        FROM '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS JSON 'auto'
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(table_name, copy_query, s3_path)
    
    def load_ticket_sales_data(self, s3_path: str) -> bool:
        """Load ticket sales data from S3 using optimized COPY command."""
        table_name = f"{self.schema_name}.ticket_sales"
        
        copy_query = f"""
        COPY {table_name} (
            sale_id,
            concert_id,
            price_tier,
            quantity,
            unit_price,
            total_amount,
            purchase_timestamp,
            customer_segment,
            created_at,
            updated_at
        )
        FROM '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS JSON 'auto'
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(table_name, copy_query, s3_path)
    
    def load_csv_data(self, table_name: str, s3_path: str, 
                     column_list: Optional[List[str]] = None,
                     delimiter: str = ',', 
                     has_header: bool = True) -> bool:
        """Load CSV data from S3 with flexible configuration."""
        full_table_name = f"{self.schema_name}.{table_name}"
        
        # Build column specification
        columns_spec = ""
        if column_list:
            columns_spec = f"({', '.join(column_list)})"
        
        # Build format options
        format_options = f"CSV DELIMITER '{delimiter}'"
        if has_header:
            format_options += " IGNOREHEADER 1"
        
        copy_query = f"""
        COPY {full_table_name} {columns_spec}
        FROM '{s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS {format_options}
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(full_table_name, copy_query, s3_path)
    
    def load_manifest_data(self, table_name: str, manifest_s3_path: str) -> bool:
        """Load data using S3 manifest file for multiple files."""
        full_table_name = f"{self.schema_name}.{table_name}"
        
        copy_query = f"""
        COPY {full_table_name}
        FROM '{manifest_s3_path}'
        IAM_ROLE '{self.iam_role}'
        FORMAT AS JSON 'auto'
        MANIFEST
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL
        MAXERROR 100;
        """
        
        return self._execute_copy_with_monitoring(full_table_name, copy_query, manifest_s3_path)
    
    def upsert_data(self, table_name: str, s3_path: str, 
                   primary_keys: List[str], update_columns: List[str]) -> bool:
        """Perform upsert operation using staging table."""
        staging_table = f"{self.schema_name}.{table_name}_staging"
        main_table = f"{self.schema_name}.{table_name}"
        
        try:
            # Create staging table
            create_staging_query = f"""
            CREATE TEMP TABLE {staging_table} (LIKE {main_table});
            """
            self.client.execute_query(create_staging_query)
            
            # Load data into staging table
            copy_query = f"""
            COPY {staging_table}
            FROM '{s3_path}'
            IAM_ROLE '{self.iam_role}'
            FORMAT AS JSON 'auto'
            TIMEFORMAT 'auto'
            DATEFORMAT 'auto'
            TRUNCATECOLUMNS
            BLANKSASNULL
            EMPTYASNULL;
            """
            self.client.execute_query(copy_query)
            
            # Delete existing records that will be updated
            pk_conditions = " AND ".join([f"main.{pk} = staging.{pk}" for pk in primary_keys])
            delete_query = f"""
            DELETE FROM {main_table}
            USING {staging_table} staging
            WHERE {pk_conditions};
            """
            self.client.execute_query(delete_query)
            
            # Insert all records from staging
            insert_query = f"""
            INSERT INTO {main_table}
            SELECT * FROM {staging_table};
            """
            self.client.execute_query(insert_query)
            
            logger.info(f"Successfully upserted data into {main_table}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert data into {table_name}: {e}")
            return False
    
    def _execute_copy_with_monitoring(self, table_name: str, copy_query: str, s3_path: str) -> bool:
        """Execute COPY command with monitoring and error handling."""
        start_time = datetime.utcnow()
        
        try:
            # Get initial row count
            initial_count = self.client.get_table_row_count(
                table_name.split('.')[-1], 
                self.schema_name
            )
            
            # Execute COPY command
            self.client.execute_query(copy_query)
            
            # Get final row count
            final_count = self.client.get_table_row_count(
                table_name.split('.')[-1], 
                self.schema_name
            )
            
            # Calculate metrics
            rows_loaded = final_count - initial_count
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Successfully loaded {rows_loaded} rows into {table_name} "
                       f"from {s3_path} in {duration:.2f} seconds")
            
            # Run ANALYZE to update statistics
            self.client.analyze_table(table_name.split('.')[-1], self.schema_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data into {table_name} from {s3_path}: {e}")
            
            # Check for COPY errors
            self._check_copy_errors()
            return False
    
    def _check_copy_errors(self):
        """Check STL_LOAD_ERRORS for recent COPY command errors."""
        error_query = """
        SELECT 
            starttime,
            filename,
            line_number,
            colname,
            type,
            position,
            raw_line,
            err_reason
        FROM stl_load_errors 
        WHERE starttime >= DATEADD(minute, -10, GETDATE())
        ORDER BY starttime DESC
        LIMIT 10;
        """
        
        try:
            errors = self.client.execute_query(error_query)
            if errors:
                logger.error("Recent COPY errors found:")
                for error in errors:
                    logger.error(f"  File: {error['filename']}, Line: {error['line_number']}, "
                               f"Column: {error['colname']}, Reason: {error['err_reason']}")
        except Exception as e:
            logger.error(f"Failed to check COPY errors: {e}")
    
    def get_load_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get loading statistics for a table."""
        stats_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(created_at) as earliest_record,
            MAX(created_at) as latest_record,
            MAX(updated_at) as last_updated
        FROM {self.schema_name}.{table_name};
        """
        
        try:
            result = self.client.execute_query(stats_query)
            if result:
                return result[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to get load statistics for {table_name}: {e}")
            return {}
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across all tables."""
        validation_results = {}
        
        # Check for orphaned records
        orphaned_concerts_query = f"""
        SELECT COUNT(*) as orphaned_concerts
        FROM {self.schema_name}.concerts c
        LEFT JOIN {self.schema_name}.artists a ON c.artist_id = a.artist_id
        LEFT JOIN {self.schema_name}.venues v ON c.venue_id = v.venue_id
        WHERE a.artist_id IS NULL OR v.venue_id IS NULL;
        """
        
        orphaned_sales_query = f"""
        SELECT COUNT(*) as orphaned_sales
        FROM {self.schema_name}.ticket_sales ts
        LEFT JOIN {self.schema_name}.concerts c ON ts.concert_id = c.concert_id
        WHERE c.concert_id IS NULL;
        """
        
        try:
            validation_results['orphaned_concerts'] = self.client.execute_query(orphaned_concerts_query)[0]['orphaned_concerts']
            validation_results['orphaned_sales'] = self.client.execute_query(orphaned_sales_query)[0]['orphaned_sales']
            
            # Check data quality metrics
            for table in ['artists', 'venues', 'concerts', 'ticket_sales']:
                stats = self.get_load_statistics(table)
                validation_results[f'{table}_stats'] = stats
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate data integrity: {e}")
            return {'error': str(e)}