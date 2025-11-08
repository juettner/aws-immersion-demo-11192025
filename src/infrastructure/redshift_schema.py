"""
Redshift data warehouse schema definitions.
Defines table structures with appropriate distribution keys and sort keys for optimal performance.
"""
import logging
from typing import Dict, List
from .redshift_client import RedshiftClient

logger = logging.getLogger(__name__)


class RedshiftSchemaManager:
    """Manages Redshift schema creation and maintenance."""
    
    def __init__(self, client: RedshiftClient):
        """Initialize with Redshift client."""
        self.client = client
        self.schema_name = 'concert_dw'
    
    def create_all_tables(self) -> bool:
        """Create all data warehouse tables."""
        try:
            # Create schema first
            self.client.create_schema_if_not_exists(self.schema_name)
            
            # Create tables in dependency order
            tables_created = []
            
            # Dimension tables first
            if self._create_artists_table():
                tables_created.append('artists')
            
            if self._create_venues_table():
                tables_created.append('venues')
            
            # Fact tables
            if self._create_concerts_table():
                tables_created.append('concerts')
            
            if self._create_ticket_sales_table():
                tables_created.append('ticket_sales')
            
            # Analytics tables
            if self._create_venue_popularity_table():
                tables_created.append('venue_popularity')
            
            if self._create_artist_performance_table():
                tables_created.append('artist_performance')
            
            if self._create_daily_sales_summary_table():
                tables_created.append('daily_sales_summary')
            
            logger.info(f"Successfully created tables: {', '.join(tables_created)}")
            return len(tables_created) > 0
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def _create_artists_table(self) -> bool:
        """Create artists dimension table with EVEN distribution."""
        table_name = f"{self.schema_name}.artists"
        
        if self.client.table_exists('artists', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            artist_id VARCHAR(50) NOT NULL,
            name VARCHAR(200) NOT NULL,
            genre VARCHAR(500),
            popularity_score DECIMAL(5,2) DEFAULT 0.0,
            formation_date DATE,
            members VARCHAR(1000),
            spotify_id VARCHAR(50),
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (artist_id)
        )
        DISTSTYLE EVEN
        SORTKEY (name, popularity_score DESC);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_venues_table(self) -> bool:
        """Create venues dimension table with EVEN distribution."""
        table_name = f"{self.schema_name}.venues"
        
        if self.client.table_exists('venues', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            venue_id VARCHAR(50) NOT NULL,
            name VARCHAR(200) NOT NULL,
            address VARCHAR(500),
            city VARCHAR(100) NOT NULL,
            state VARCHAR(50),
            country VARCHAR(50) NOT NULL,
            postal_code VARCHAR(20),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            capacity INTEGER NOT NULL,
            venue_type VARCHAR(50) NOT NULL,
            amenities VARCHAR(1000),
            ticketmaster_id VARCHAR(50),
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (venue_id)
        )
        DISTSTYLE EVEN
        SORTKEY (city, capacity DESC);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_concerts_table(self) -> bool:
        """Create concerts fact table distributed by artist_id."""
        table_name = f"{self.schema_name}.concerts"
        
        if self.client.table_exists('concerts', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            concert_id VARCHAR(50) NOT NULL,
            artist_id VARCHAR(50) NOT NULL,
            venue_id VARCHAR(50) NOT NULL,
            event_date TIMESTAMP NOT NULL,
            ticket_prices VARCHAR(2000),
            total_attendance INTEGER,
            revenue DECIMAL(12,2),
            status VARCHAR(20) DEFAULT 'scheduled',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (concert_id),
            FOREIGN KEY (artist_id) REFERENCES {self.schema_name}.artists(artist_id),
            FOREIGN KEY (venue_id) REFERENCES {self.schema_name}.venues(venue_id)
        )
        DISTKEY (artist_id)
        SORTKEY (event_date DESC, artist_id);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_ticket_sales_table(self) -> bool:
        """Create ticket sales fact table distributed by concert_id."""
        table_name = f"{self.schema_name}.ticket_sales"
        
        if self.client.table_exists('ticket_sales', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            sale_id VARCHAR(50) NOT NULL,
            concert_id VARCHAR(50) NOT NULL,
            price_tier VARCHAR(50) NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(8,2) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            purchase_timestamp TIMESTAMP NOT NULL,
            customer_segment VARCHAR(50) DEFAULT 'general',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (sale_id),
            FOREIGN KEY (concert_id) REFERENCES {self.schema_name}.concerts(concert_id)
        )
        DISTKEY (concert_id)
        SORTKEY (purchase_timestamp DESC, concert_id);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_venue_popularity_table(self) -> bool:
        """Create venue popularity analytics table."""
        table_name = f"{self.schema_name}.venue_popularity"
        
        if self.client.table_exists('venue_popularity', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            venue_id VARCHAR(50) NOT NULL,
            popularity_rank INTEGER,
            avg_attendance_rate DECIMAL(5,2),
            revenue_per_event DECIMAL(12,2),
            booking_frequency DECIMAL(8,2),
            total_events INTEGER,
            calculated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (venue_id, calculated_at),
            FOREIGN KEY (venue_id) REFERENCES {self.schema_name}.venues(venue_id)
        )
        DISTSTYLE EVEN
        SORTKEY (calculated_at DESC, popularity_rank);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_artist_performance_table(self) -> bool:
        """Create artist performance analytics table."""
        table_name = f"{self.schema_name}.artist_performance"
        
        if self.client.table_exists('artist_performance', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            artist_id VARCHAR(50) NOT NULL,
            total_concerts INTEGER DEFAULT 0,
            avg_ticket_sales DECIMAL(10,2) DEFAULT 0.0,
            revenue_generated DECIMAL(15,2) DEFAULT 0.0,
            fan_engagement_score DECIMAL(5,2) DEFAULT 0.0,
            growth_trend VARCHAR(20) DEFAULT 'stable',
            calculated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (artist_id, calculated_at),
            FOREIGN KEY (artist_id) REFERENCES {self.schema_name}.artists(artist_id)
        )
        DISTSTYLE EVEN
        SORTKEY (calculated_at DESC, revenue_generated DESC);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _create_daily_sales_summary_table(self) -> bool:
        """Create daily sales summary table for fast aggregations."""
        table_name = f"{self.schema_name}.daily_sales_summary"
        
        if self.client.table_exists('daily_sales_summary', self.schema_name):
            logger.info(f"Table {table_name} already exists")
            return True
        
        create_query = f"""
        CREATE TABLE {table_name} (
            summary_date DATE NOT NULL,
            artist_id VARCHAR(50) NOT NULL,
            venue_id VARCHAR(50) NOT NULL,
            concert_id VARCHAR(50) NOT NULL,
            total_tickets_sold INTEGER DEFAULT 0,
            total_revenue DECIMAL(12,2) DEFAULT 0.0,
            avg_ticket_price DECIMAL(8,2) DEFAULT 0.0,
            unique_customers INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL,
            PRIMARY KEY (summary_date, concert_id),
            FOREIGN KEY (artist_id) REFERENCES {self.schema_name}.artists(artist_id),
            FOREIGN KEY (venue_id) REFERENCES {self.schema_name}.venues(venue_id),
            FOREIGN KEY (concert_id) REFERENCES {self.schema_name}.concerts(concert_id)
        )
        DISTKEY (artist_id)
        SORTKEY (summary_date DESC, total_revenue DESC);
        """
        
        try:
            self.client.execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def drop_all_tables(self) -> bool:
        """Drop all tables (for testing/cleanup)."""
        tables = [
            'daily_sales_summary',
            'artist_performance', 
            'venue_popularity',
            'ticket_sales',
            'concerts',
            'venues',
            'artists'
        ]
        
        dropped_tables = []
        for table in tables:
            try:
                drop_query = f"DROP TABLE IF EXISTS {self.schema_name}.{table} CASCADE;"
                self.client.execute_query(drop_query)
                dropped_tables.append(table)
                logger.info(f"Dropped table {self.schema_name}.{table}")
            except Exception as e:
                logger.error(f"Failed to drop table {table}: {e}")
        
        return len(dropped_tables) == len(tables)
    
    def get_table_info(self) -> Dict[str, Dict]:
        """Get information about all tables in the schema."""
        query = f"""
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = '{self.schema_name}'
        ORDER BY table_name, ordinal_position;
        """
        
        try:
            results = self.client.execute_query(query)
            tables_info = {}
            
            for row in results:
                table_name = row['table_name']
                if table_name not in tables_info:
                    tables_info[table_name] = {'columns': []}
                
                tables_info[table_name]['columns'].append({
                    'name': row['column_name'],
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES',
                    'default': row['column_default']
                })
            
            return tables_info
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}