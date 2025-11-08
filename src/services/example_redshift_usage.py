"""
Example usage of the Redshift data warehouse service.
Demonstrates how to set up and use the Redshift service for concert data analytics.
"""
import logging
from datetime import datetime, timedelta
from ..services.redshift_service import RedshiftService
from ..config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_data_warehouse():
    """Set up the complete data warehouse infrastructure."""
    logger.info("Setting up Redshift data warehouse...")
    
    # Initialize the service
    # Note: Requires proper AWS credentials and Redshift cluster configuration
    redshift_service = RedshiftService()
    
    try:
        # Initialize schema, tables, and stored procedures
        init_results = redshift_service.initialize_data_warehouse()
        
        logger.info("Data warehouse initialization results:")
        for component, success in init_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {component}: {'Success' if success else 'Failed'}")
        
        return redshift_service, all(init_results.values())
        
    except Exception as e:
        logger.error(f"Failed to set up data warehouse: {e}")
        return redshift_service, False


def load_sample_data(redshift_service: RedshiftService):
    """Load sample data from S3 into the data warehouse."""
    logger.info("Loading sample data from S3...")
    
    # Example S3 paths - these would be actual S3 locations in production
    data_sources = {
        'artists': 's3://concert-data-processed/artists/2024/',
        'venues': 's3://concert-data-processed/venues/2024/',
        'concerts': 's3://concert-data-processed/concerts/2024/',
        'ticket_sales': 's3://concert-data-processed/ticket_sales/2024/'
    }
    
    try:
        load_results = redshift_service.load_data_from_s3(data_sources)
        
        logger.info("Data loading results:")
        for table, success in load_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {table}: {'Loaded' if success else 'Failed'}")
        
        return all(load_results.values())
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False


def run_analytics_pipeline(redshift_service: RedshiftService):
    """Run the complete analytics pipeline."""
    logger.info("Running analytics calculations...")
    
    try:
        # Run all analytics calculations
        analytics_results = redshift_service.run_analytics_calculations()
        
        logger.info("Analytics calculation results:")
        for calculation, success in analytics_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {calculation}: {'Completed' if success else 'Failed'}")
        
        return all(analytics_results.values())
        
    except Exception as e:
        logger.error(f"Failed to run analytics: {e}")
        return False


def demonstrate_insights_queries(redshift_service: RedshiftService):
    """Demonstrate various insights queries."""
    logger.info("Demonstrating insights queries...")
    
    try:
        # Get top venues
        logger.info("\n--- Top 5 Venues by Popularity ---")
        top_venues = redshift_service.get_venue_insights(limit=5, days=365)
        
        for i, venue in enumerate(top_venues, 1):
            logger.info(f"{i}. {venue['venue_name']} ({venue['city']})")
            logger.info(f"   Events: {venue['total_events']}, Revenue: ${venue['total_revenue']:,.2f}")
            logger.info(f"   Attendance Rate: {venue['avg_attendance_rate']:.1f}%")
        
        # Get trending artists
        logger.info("\n--- Top 5 Growing Artists ---")
        growing_artists = redshift_service.get_artist_insights(limit=5, trend_filter='growing')
        
        for i, artist in enumerate(growing_artists, 1):
            logger.info(f"{i}. {artist['artist_name']}")
            logger.info(f"   Concerts: {artist['total_concerts']}, Revenue: ${artist['revenue_generated']:,.2f}")
            logger.info(f"   Engagement Score: {artist['fan_engagement_score']:.1f}/10")
        
        # Get revenue analytics by month
        logger.info("\n--- Monthly Revenue Analytics (Last 6 Months) ---")
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        monthly_revenue = redshift_service.get_revenue_analytics(
            start_date=six_months_ago,
            end_date=today,
            period='month'
        )
        
        for month in monthly_revenue:
            logger.info(f"{month['period_start']} to {month['period_end']}")
            logger.info(f"   Concerts: {month['total_concerts']}, Revenue: ${month['total_revenue']:,.2f}")
            logger.info(f"   Avg per Concert: ${month['avg_revenue_per_concert']:,.2f}")
            logger.info(f"   Tickets Sold: {month['total_tickets_sold']:,}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to demonstrate insights: {e}")
        return False


def demonstrate_custom_analytics(redshift_service: RedshiftService):
    """Demonstrate custom analytics queries."""
    logger.info("Running custom analytics queries...")
    
    try:
        # Custom query: Top artists by average attendance
        custom_query = """
        SELECT 
            a.name as artist_name,
            COUNT(c.concert_id) as total_concerts,
            AVG(c.total_attendance) as avg_attendance,
            SUM(c.revenue) as total_revenue
        FROM concert_dw.artists a
        JOIN concert_dw.concerts c ON a.artist_id = c.artist_id
        WHERE c.status = 'completed'
            AND c.event_date >= CURRENT_DATE - INTERVAL '1 year'
        GROUP BY a.artist_id, a.name
        HAVING COUNT(c.concert_id) >= 3
        ORDER BY avg_attendance DESC
        LIMIT 10;
        """
        
        results = redshift_service.execute_custom_query(custom_query)
        
        logger.info("\n--- Top Artists by Average Attendance ---")
        for i, artist in enumerate(results, 1):
            logger.info(f"{i}. {artist['artist_name']}")
            logger.info(f"   Concerts: {artist['total_concerts']}")
            logger.info(f"   Avg Attendance: {artist['avg_attendance']:,.0f}")
            logger.info(f"   Total Revenue: ${artist['total_revenue']:,.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to run custom analytics: {e}")
        return False


def monitor_data_warehouse_health(redshift_service: RedshiftService):
    """Monitor data warehouse health and performance."""
    logger.info("Checking data warehouse health...")
    
    try:
        # Get comprehensive status
        status = redshift_service.get_data_warehouse_status()
        
        logger.info(f"\n--- Data Warehouse Status ({status['timestamp']}) ---")
        
        # Table status
        logger.info("\nTable Status:")
        for table_name, table_info in status['tables'].items():
            if 'error' in table_info:
                logger.warning(f"  ✗ {table_name}: {table_info['error']}")
            else:
                exists = "✓" if table_info['exists'] else "✗"
                logger.info(f"  {exists} {table_name}: {table_info['row_count']:,} rows")
        
        # Data integrity
        if 'data_integrity' in status and status['data_integrity']:
            logger.info("\nData Integrity:")
            integrity = status['data_integrity']
            
            if 'orphaned_concerts' in integrity:
                logger.info(f"  Orphaned concerts: {integrity['orphaned_concerts']}")
            if 'orphaned_sales' in integrity:
                logger.info(f"  Orphaned ticket sales: {integrity['orphaned_sales']}")
        
        # Recent analytics
        if 'recent_analytics' in status and status['recent_analytics']:
            logger.info("\nRecent Analytics:")
            analytics = status['recent_analytics']
            
            if 'venue_popularity' in analytics:
                vp = analytics['venue_popularity']
                logger.info(f"  Venue popularity: {vp['venue_count']} venues calculated at {vp['latest_calculation']}")
            
            if 'artist_performance' in analytics:
                ap = analytics['artist_performance']
                logger.info(f"  Artist performance: {ap['artist_count']} artists calculated at {ap['latest_calculation']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check data warehouse health: {e}")
        return False


def optimize_and_maintain(redshift_service: RedshiftService):
    """Perform optimization and maintenance tasks."""
    logger.info("Running optimization and maintenance...")
    
    try:
        # Optimize tables
        logger.info("Optimizing tables (VACUUM and ANALYZE)...")
        optimization_results = redshift_service.optimize_tables()
        
        for table, success in optimization_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {table}: {'Optimized' if success else 'Failed'}")
        
        # Clean up old analytics data (keep last 30 days)
        logger.info("Cleaning up old analytics data...")
        cleanup_success = redshift_service.cleanup_old_analytics(days_to_keep=30)
        
        if cleanup_success:
            logger.info("  ✓ Old analytics data cleaned up")
        else:
            logger.warning("  ✗ Failed to clean up old analytics data")
        
        return all(optimization_results.values()) and cleanup_success
        
    except Exception as e:
        logger.error(f"Failed to optimize and maintain: {e}")
        return False


def main():
    """Main demonstration function."""
    logger.info("Starting Redshift Data Warehouse Demo")
    logger.info("=" * 50)
    
    try:
        # Step 1: Set up data warehouse
        redshift_service, setup_success = setup_data_warehouse()
        
        if not setup_success:
            logger.error("Failed to set up data warehouse. Exiting.")
            return
        
        # Step 2: Load sample data
        if load_sample_data(redshift_service):
            logger.info("✓ Sample data loaded successfully")
        else:
            logger.warning("✗ Failed to load sample data")
        
        # Step 3: Run analytics pipeline
        if run_analytics_pipeline(redshift_service):
            logger.info("✓ Analytics pipeline completed successfully")
        else:
            logger.warning("✗ Analytics pipeline failed")
        
        # Step 4: Demonstrate insights queries
        if demonstrate_insights_queries(redshift_service):
            logger.info("✓ Insights queries demonstrated successfully")
        
        # Step 5: Run custom analytics
        if demonstrate_custom_analytics(redshift_service):
            logger.info("✓ Custom analytics demonstrated successfully")
        
        # Step 6: Monitor health
        if monitor_data_warehouse_health(redshift_service):
            logger.info("✓ Data warehouse health check completed")
        
        # Step 7: Optimize and maintain
        if optimize_and_maintain(redshift_service):
            logger.info("✓ Optimization and maintenance completed")
        
        logger.info("\n" + "=" * 50)
        logger.info("Redshift Data Warehouse Demo Completed Successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
    
    finally:
        # Always close the connection
        if 'redshift_service' in locals():
            redshift_service.close()
            logger.info("Redshift connection closed")


if __name__ == "__main__":
    main()