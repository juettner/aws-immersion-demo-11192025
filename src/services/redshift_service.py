"""
Redshift data warehouse service for managing schema, data loading, and analytics.
Orchestrates all Redshift operations including schema creation, data loading, and stored procedures.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..infrastructure.redshift_client import RedshiftClient
from ..infrastructure.redshift_schema import RedshiftSchemaManager
from ..infrastructure.redshift_data_loader import RedshiftDataLoader
from ..infrastructure.redshift_stored_procedures import RedshiftStoredProcedures
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class RedshiftService:
    """Main service for Redshift data warehouse operations."""
    
    def __init__(self, iam_role: Optional[str] = None):
        """Initialize Redshift service with all components."""
        self.settings = get_settings()
        self.client = RedshiftClient()
        self.schema_manager = RedshiftSchemaManager(self.client)
        
        # Use provided IAM role or get from settings
        self.iam_role = iam_role or self.settings.aws.sagemaker_execution_role
        if not self.iam_role:
            logger.warning("No IAM role provided for COPY operations")
        
        self.data_loader = RedshiftDataLoader(self.client, self.iam_role) if self.iam_role else None
        self.stored_procedures = RedshiftStoredProcedures(self.client)
    
    def initialize_data_warehouse(self) -> Dict[str, bool]:
        """Initialize the complete data warehouse setup."""
        results = {
            'schema_created': False,
            'tables_created': False,
            'procedures_created': False
        }
        
        try:
            logger.info("Starting data warehouse initialization...")
            
            # Create schema and tables
            if self.schema_manager.create_all_tables():
                results['schema_created'] = True
                results['tables_created'] = True
                logger.info("Schema and tables created successfully")
            
            # Create stored procedures
            if self.stored_procedures.create_all_procedures():
                results['procedures_created'] = True
                logger.info("Stored procedures created successfully")
            
            logger.info("Data warehouse initialization completed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to initialize data warehouse: {e}")
            return results
    
    def load_data_from_s3(self, data_sources: Dict[str, str]) -> Dict[str, bool]:
        """Load data from multiple S3 sources."""
        if not self.data_loader:
            logger.error("Data loader not available - IAM role not configured")
            return {}
        
        results = {}
        
        # Load data in dependency order
        load_order = [
            ('artists', 'load_artists_data'),
            ('venues', 'load_venues_data'),
            ('concerts', 'load_concerts_data'),
            ('ticket_sales', 'load_ticket_sales_data')
        ]
        
        for table_name, loader_method in load_order:
            if table_name in data_sources:
                s3_path = data_sources[table_name]
                logger.info(f"Loading {table_name} data from {s3_path}")
                
                try:
                    loader_func = getattr(self.data_loader, loader_method)
                    results[table_name] = loader_func(s3_path)
                    
                    if results[table_name]:
                        logger.info(f"Successfully loaded {table_name} data")
                    else:
                        logger.error(f"Failed to load {table_name} data")
                        
                except Exception as e:
                    logger.error(f"Error loading {table_name} data: {e}")
                    results[table_name] = False
            else:
                logger.warning(f"No S3 path provided for {table_name}")
        
        return results
    
    def run_analytics_calculations(self) -> Dict[str, bool]:
        """Run all analytics calculations."""
        results = {
            'venue_popularity': False,
            'artist_performance': False,
            'daily_sales_summary': False
        }
        
        try:
            # Calculate venue popularity
            if self.stored_procedures.execute_venue_popularity_calculation():
                results['venue_popularity'] = True
                logger.info("Venue popularity calculation completed")
            
            # Calculate artist performance
            if self.stored_procedures.execute_artist_performance_calculation():
                results['artist_performance'] = True
                logger.info("Artist performance calculation completed")
            
            # Generate daily sales summary for yesterday
            if self.stored_procedures.execute_daily_sales_summary():
                results['daily_sales_summary'] = True
                logger.info("Daily sales summary generation completed")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to run analytics calculations: {e}")
            return results
    
    def get_venue_insights(self, limit: int = 10, days: int = 365) -> List[Dict[str, Any]]:
        """Get venue performance insights."""
        try:
            return self.stored_procedures.get_top_venues(limit, days)
        except Exception as e:
            logger.error(f"Failed to get venue insights: {e}")
            return []
    
    def get_artist_insights(self, limit: int = 20, trend_filter: str = 'all') -> List[Dict[str, Any]]:
        """Get artist performance insights."""
        try:
            return self.stored_procedures.get_artist_trends(limit, trend_filter)
        except Exception as e:
            logger.error(f"Failed to get artist insights: {e}")
            return []
    
    def get_revenue_analytics(self, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None, 
                            period: str = 'month') -> List[Dict[str, Any]]:
        """Get revenue analytics by period."""
        try:
            return self.stored_procedures.get_revenue_analytics(start_date, end_date, period)
        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {e}")
            return []
    
    def get_data_warehouse_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the data warehouse."""
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'tables': {},
            'data_integrity': {},
            'recent_analytics': {}
        }
        
        try:
            # Check table row counts
            tables = ['artists', 'venues', 'concerts', 'ticket_sales', 
                     'venue_popularity', 'artist_performance', 'daily_sales_summary']
            
            for table in tables:
                try:
                    count = self.client.get_table_row_count(table, 'concert_dw')
                    status['tables'][table] = {
                        'exists': self.client.table_exists(table, 'concert_dw'),
                        'row_count': count
                    }
                except Exception as e:
                    status['tables'][table] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            # Check data integrity if data loader is available
            if self.data_loader:
                status['data_integrity'] = self.data_loader.validate_data_integrity()
            
            # Get recent analytics info
            try:
                # Check latest venue popularity calculation
                latest_venue_calc = self.client.execute_query("""
                    SELECT MAX(calculated_at) as latest_calculation, COUNT(*) as venue_count
                    FROM concert_dw.venue_popularity 
                    WHERE DATE(calculated_at) = (
                        SELECT MAX(DATE(calculated_at)) FROM concert_dw.venue_popularity
                    );
                """)
                
                if latest_venue_calc:
                    status['recent_analytics']['venue_popularity'] = latest_venue_calc[0]
                
                # Check latest artist performance calculation
                latest_artist_calc = self.client.execute_query("""
                    SELECT MAX(calculated_at) as latest_calculation, COUNT(*) as artist_count
                    FROM concert_dw.artist_performance 
                    WHERE DATE(calculated_at) = (
                        SELECT MAX(DATE(calculated_at)) FROM concert_dw.artist_performance
                    );
                """)
                
                if latest_artist_calc:
                    status['recent_analytics']['artist_performance'] = latest_artist_calc[0]
                
            except Exception as e:
                status['recent_analytics']['error'] = str(e)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get data warehouse status: {e}")
            status['error'] = str(e)
            return status
    
    def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a custom SQL query."""
        try:
            return self.client.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to execute custom query: {e}")
            return []
    
    def optimize_tables(self) -> Dict[str, bool]:
        """Run VACUUM and ANALYZE on all tables for optimization."""
        results = {}
        tables = ['artists', 'venues', 'concerts', 'ticket_sales', 
                 'venue_popularity', 'artist_performance', 'daily_sales_summary']
        
        for table in tables:
            try:
                # Run ANALYZE to update statistics
                analyze_success = self.client.analyze_table(table, 'concert_dw')
                
                # Run VACUUM to reclaim space and sort data
                vacuum_success = self.client.vacuum_table(table, 'concert_dw')
                
                results[table] = analyze_success and vacuum_success
                
                if results[table]:
                    logger.info(f"Successfully optimized table {table}")
                else:
                    logger.warning(f"Failed to fully optimize table {table}")
                    
            except Exception as e:
                logger.error(f"Error optimizing table {table}: {e}")
                results[table] = False
        
        return results
    
    def cleanup_old_analytics(self, days_to_keep: int = 30) -> bool:
        """Clean up old analytics data to save space."""
        try:
            cleanup_queries = [
                f"""
                DELETE FROM concert_dw.venue_popularity 
                WHERE calculated_at < CURRENT_DATE - INTERVAL '{days_to_keep} days';
                """,
                f"""
                DELETE FROM concert_dw.artist_performance 
                WHERE calculated_at < CURRENT_DATE - INTERVAL '{days_to_keep} days';
                """,
                f"""
                DELETE FROM concert_dw.daily_sales_summary 
                WHERE created_at < CURRENT_DATE - INTERVAL '{days_to_keep} days';
                """
            ]
            
            for query in cleanup_queries:
                self.client.execute_query(query)
            
            logger.info(f"Successfully cleaned up analytics data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old analytics data: {e}")
            return False
    
    def close(self):
        """Close the Redshift connection."""
        if self.client:
            self.client.close_connection()
            logger.info("Redshift service connection closed")