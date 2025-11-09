#!/usr/bin/env python3
"""
Simple Redshift schema initialization script.
Avoids complex imports by directly using psycopg2.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_redshift_config():
    """Get Redshift configuration from environment."""
    config = {
        'host': os.getenv('AWS_REDSHIFT_HOST'),
        'port': int(os.getenv('AWS_REDSHIFT_PORT', 5439)),
        'database': os.getenv('AWS_REDSHIFT_DATABASE'),
        'user': os.getenv('AWS_REDSHIFT_USER'),
        'password': os.getenv('AWS_REDSHIFT_PASSWORD')
    }
    
    # Validate configuration
    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please set the following environment variables:")
        for key in missing:
            logger.error(f"  AWS_REDSHIFT_{key.upper()}")
        return None
    
    return config

def test_connection(config):
    """Test connection to Redshift."""
    try:
        import psycopg2
        
        logger.info("Testing connection to Redshift...")
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            sslmode='require'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✓ Connected successfully!")
        logger.info(f"  Redshift version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        logger.error("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

def create_schema(config):
    """Create the concert_dw schema and tables."""
    try:
        import psycopg2
        
        logger.info("Connecting to Redshift...")
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create schema
        logger.info("Creating schema concert_dw...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS concert_dw;")
        logger.info("✓ Schema created")
        
        # Create artists table
        logger.info("Creating artists table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.artists (
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
            SORTKEY (name);
        """)
        logger.info("✓ Artists table created")
        
        # Create venues table
        logger.info("Creating venues table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.venues (
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
            SORTKEY (city, capacity);
        """)
        logger.info("✓ Venues table created")
        
        # Create concerts table
        logger.info("Creating concerts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.concerts (
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
                PRIMARY KEY (concert_id)
            )
            DISTKEY (artist_id)
            SORTKEY (event_date, artist_id);
        """)
        logger.info("✓ Concerts table created")
        
        # Create ticket_sales table
        logger.info("Creating ticket_sales table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.ticket_sales (
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
                PRIMARY KEY (sale_id)
            )
            DISTKEY (concert_id)
            SORTKEY (purchase_timestamp, concert_id);
        """)
        logger.info("✓ Ticket sales table created")
        
        # Create analytics tables
        logger.info("Creating venue_popularity table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.venue_popularity (
                venue_id VARCHAR(50) NOT NULL,
                popularity_rank INTEGER,
                avg_attendance_rate DECIMAL(5,2),
                revenue_per_event DECIMAL(12,2),
                booking_frequency DECIMAL(8,2),
                total_events INTEGER,
                calculated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (venue_id, calculated_at)
            )
            DISTSTYLE EVEN
            SORTKEY (calculated_at, popularity_rank);
        """)
        logger.info("✓ Venue popularity table created")
        
        logger.info("Creating artist_performance table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.artist_performance (
                artist_id VARCHAR(50) NOT NULL,
                total_concerts INTEGER DEFAULT 0,
                avg_ticket_sales DECIMAL(10,2) DEFAULT 0.0,
                revenue_generated DECIMAL(15,2) DEFAULT 0.0,
                fan_engagement_score DECIMAL(5,2) DEFAULT 0.0,
                growth_trend VARCHAR(20) DEFAULT 'stable',
                calculated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (artist_id, calculated_at)
            )
            DISTSTYLE EVEN
            SORTKEY (calculated_at, revenue_generated);
        """)
        logger.info("✓ Artist performance table created")
        
        logger.info("Creating daily_sales_summary table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concert_dw.daily_sales_summary (
                summary_date DATE NOT NULL,
                artist_id VARCHAR(50) NOT NULL,
                venue_id VARCHAR(50) NOT NULL,
                concert_id VARCHAR(50) NOT NULL,
                total_tickets_sold INTEGER DEFAULT 0,
                total_revenue DECIMAL(12,2) DEFAULT 0.0,
                avg_ticket_price DECIMAL(8,2) DEFAULT 0.0,
                unique_customers INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                PRIMARY KEY (summary_date, concert_id)
            )
            DISTKEY (artist_id)
            SORTKEY (summary_date, total_revenue);
        """)
        logger.info("✓ Daily sales summary table created")
        
        # Get table counts
        logger.info("\nVerifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'concert_dw'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        logger.info(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  • {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create schema: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Redshift Schema Initialization")
    logger.info("=" * 60)
    
    # Get configuration
    config = get_redshift_config()
    if not config:
        sys.exit(1)
    
    logger.info(f"\nConnecting to:")
    logger.info(f"  Host: {config['host']}")
    logger.info(f"  Database: {config['database']}")
    logger.info(f"  User: {config['user']}")
    
    # Test connection
    if not test_connection(config):
        logger.error("\nConnection test failed. Please check your credentials.")
        sys.exit(1)
    
    # Create schema
    logger.info("\n" + "=" * 60)
    if create_schema(config):
        logger.info("\n" + "=" * 60)
        logger.info("✓ Schema initialization completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Load data from S3 using RedshiftService.load_data_from_s3()")
        logger.info("2. Run analytics using RedshiftService.run_analytics_calculations()")
        logger.info("3. Query insights using the get_*_insights() methods")
        sys.exit(0)
    else:
        logger.error("\n✗ Schema initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
