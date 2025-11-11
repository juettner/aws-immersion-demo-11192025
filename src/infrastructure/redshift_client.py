"""
Amazon Redshift client for data warehouse operations.
Handles connections, schema management, and data loading operations.
"""
import logging
from typing import Dict, List, Optional, Any
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from botocore.exceptions import ClientError
from ..config.settings import settings

logger = logging.getLogger(__name__)


class RedshiftClient:
    """Client for Amazon Redshift data warehouse operations."""
    
    def __init__(self):
        """Initialize Redshift client with configuration."""
        self.settings = settings
        self.redshift_client = boto3.client('redshift', region_name=self.settings.aws_region)
        self.redshift_data_client = boto3.client('redshift-data', region_name=self.settings.aws_region)
        self._connection = None
    
    def get_connection(self) -> psycopg2.extensions.connection:
        """Get or create a connection to Redshift."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    host=self.settings.redshift_host,
                    port=self.settings.redshift_port,
                    database=self.settings.redshift_database,
                    user=self.settings.redshift_user,
                    password=self.settings.redshift_password,
                    sslmode='require'
                )
                logger.info("Successfully connected to Redshift")
            except psycopg2.Error as e:
                logger.error(f"Failed to connect to Redshift: {e}")
                raise
        
        return self._connection
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    results = [dict(row) for row in cursor.fetchall()]
                    logger.info(f"Query executed successfully, returned {len(results)} rows")
                    return results
                else:
                    conn.commit()
                    logger.info("Query executed successfully (no results)")
                    return []
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_copy_command(self, table_name: str, s3_path: str, 
                           iam_role: str, format_options: str = "JSON 'auto'") -> bool:
        """Execute COPY command to load data from S3."""
        copy_query = f"""
        COPY {table_name}
        FROM '{s3_path}'
        IAM_ROLE '{iam_role}'
        FORMAT AS {format_options}
        TIMEFORMAT 'auto'
        DATEFORMAT 'auto'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL;
        """
        
        try:
            self.execute_query(copy_query)
            logger.info(f"Successfully loaded data into {table_name} from {s3_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load data into {table_name}: {e}")
            return False
    
    def create_schema_if_not_exists(self, schema_name: str) -> bool:
        """Create schema if it doesn't exist."""
        query = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        try:
            self.execute_query(query)
            logger.info(f"Schema {schema_name} created or already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {e}")
            return False
    
    def table_exists(self, table_name: str, schema_name: str = 'public') -> bool:
        """Check if a table exists."""
        query = """
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s;
        """
        try:
            result = self.execute_query(query, (schema_name, table_name))
            return result[0]['count'] > 0
        except Exception as e:
            logger.error(f"Failed to check if table exists: {e}")
            return False
    
    def get_table_row_count(self, table_name: str, schema_name: str = 'public') -> int:
        """Get the number of rows in a table."""
        query = f"SELECT COUNT(*) as count FROM {schema_name}.{table_name};"
        try:
            result = self.execute_query(query)
            return result[0]['count']
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0
    
    def analyze_table(self, table_name: str, schema_name: str = 'public') -> bool:
        """Run ANALYZE on a table to update statistics."""
        query = f"ANALYZE {schema_name}.{table_name};"
        try:
            self.execute_query(query)
            logger.info(f"Successfully analyzed table {schema_name}.{table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return False
    
    def vacuum_table(self, table_name: str, schema_name: str = 'public') -> bool:
        """Run VACUUM on a table to reclaim space and sort data."""
        query = f"VACUUM {schema_name}.{table_name};"
        try:
            self.execute_query(query)
            logger.info(f"Successfully vacuumed table {schema_name}.{table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to vacuum table {table_name}: {e}")
            return False
    
    def close_connection(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Redshift connection closed")