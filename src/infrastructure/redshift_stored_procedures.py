"""
Redshift stored procedures for data aggregation and analytics.
Contains procedures for calculating venue popularity, artist performance, and other analytics.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .redshift_client import RedshiftClient

logger = logging.getLogger(__name__)


class RedshiftStoredProcedures:
    """Manages stored procedures for analytics and data aggregation."""
    
    def __init__(self, client: RedshiftClient):
        """Initialize with Redshift client."""
        self.client = client
        self.schema_name = 'concert_dw'
    
    def create_all_procedures(self) -> bool:
        """Create all stored procedures."""
        procedures_created = []
        
        try:
            if self._create_calculate_venue_popularity_procedure():
                procedures_created.append('calculate_venue_popularity')
            
            if self._create_calculate_artist_performance_procedure():
                procedures_created.append('calculate_artist_performance')
            
            if self._create_generate_daily_sales_summary_procedure():
                procedures_created.append('generate_daily_sales_summary')
            
            if self._create_get_top_venues_procedure():
                procedures_created.append('get_top_venues')
            
            if self._create_get_artist_trends_procedure():
                procedures_created.append('get_artist_trends')
            
            if self._create_get_revenue_analytics_procedure():
                procedures_created.append('get_revenue_analytics')
            
            logger.info(f"Successfully created procedures: {', '.join(procedures_created)}")
            return len(procedures_created) > 0
            
        except Exception as e:
            logger.error(f"Failed to create stored procedures: {e}")
            return False
    
    def _create_calculate_venue_popularity_procedure(self) -> bool:
        """Create procedure to calculate venue popularity metrics."""
        procedure_name = f"{self.schema_name}.calculate_venue_popularity"
        
        create_procedure = f"""
        CREATE OR REPLACE PROCEDURE {procedure_name}()
        LANGUAGE plpgsql
        AS $$
        BEGIN
            -- Delete existing records for today
            DELETE FROM {self.schema_name}.venue_popularity 
            WHERE DATE(calculated_at) = CURRENT_DATE;
            
            -- Calculate and insert new venue popularity metrics
            INSERT INTO {self.schema_name}.venue_popularity (
                venue_id,
                popularity_rank,
                avg_attendance_rate,
                revenue_per_event,
                booking_frequency,
                total_events,
                calculated_at
            )
            WITH venue_metrics AS (
                SELECT 
                    v.venue_id,
                    v.name,
                    v.capacity,
                    COUNT(c.concert_id) as total_events,
                    AVG(CASE 
                        WHEN c.total_attendance IS NOT NULL AND v.capacity > 0 
                        THEN (c.total_attendance::DECIMAL / v.capacity) * 100 
                        ELSE NULL 
                    END) as avg_attendance_rate,
                    AVG(c.revenue) as avg_revenue_per_event,
                    COUNT(c.concert_id)::DECIMAL / 
                        NULLIF(EXTRACT(days FROM (MAX(c.event_date) - MIN(c.event_date))), 0) * 30 
                        as booking_frequency_per_month
                FROM {self.schema_name}.venues v
                LEFT JOIN {self.schema_name}.concerts c ON v.venue_id = c.venue_id
                    AND c.status = 'completed'
                    AND c.event_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY v.venue_id, v.name, v.capacity
                HAVING COUNT(c.concert_id) > 0
            ),
            ranked_venues AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (
                        ORDER BY 
                            COALESCE(avg_attendance_rate, 0) * 0.4 + 
                            COALESCE(avg_revenue_per_event, 0) / 100000 * 0.3 + 
                            COALESCE(booking_frequency_per_month, 0) * 0.3 DESC
                    ) as popularity_rank
                FROM venue_metrics
            )
            SELECT 
                venue_id,
                popularity_rank,
                ROUND(COALESCE(avg_attendance_rate, 0), 2),
                ROUND(COALESCE(avg_revenue_per_event, 0), 2),
                ROUND(COALESCE(booking_frequency_per_month, 0), 2),
                total_events,
                CURRENT_TIMESTAMP
            FROM ranked_venues;
            
            -- Log the operation
            RAISE NOTICE 'Venue popularity calculation completed for % venues', 
                (SELECT COUNT(*) FROM {self.schema_name}.venue_popularity WHERE DATE(calculated_at) = CURRENT_DATE);
        END;
        $$;
        """
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created procedure {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create procedure {procedure_name}: {e}")
            return False
    
    def _create_calculate_artist_performance_procedure(self) -> bool:
        """Create procedure to calculate artist performance metrics."""
        procedure_name = f"{self.schema_name}.calculate_artist_performance"
        
        create_procedure = f"""
        CREATE OR REPLACE PROCEDURE {procedure_name}()
        LANGUAGE plpgsql
        AS $$
        BEGIN
            -- Delete existing records for today
            DELETE FROM {self.schema_name}.artist_performance 
            WHERE DATE(calculated_at) = CURRENT_DATE;
            
            -- Calculate and insert new artist performance metrics
            INSERT INTO {self.schema_name}.artist_performance (
                artist_id,
                total_concerts,
                avg_ticket_sales,
                revenue_generated,
                fan_engagement_score,
                growth_trend,
                calculated_at
            )
            WITH artist_metrics AS (
                SELECT 
                    a.artist_id,
                    a.name,
                    a.popularity_score,
                    COUNT(c.concert_id) as total_concerts,
                    AVG(c.total_attendance) as avg_attendance,
                    SUM(c.revenue) as total_revenue,
                    -- Calculate growth trend based on recent vs older concerts
                    CASE 
                        WHEN COUNT(CASE WHEN c.event_date >= CURRENT_DATE - INTERVAL '6 months' THEN 1 END) > 
                             COUNT(CASE WHEN c.event_date < CURRENT_DATE - INTERVAL '6 months' 
                                        AND c.event_date >= CURRENT_DATE - INTERVAL '1 year' THEN 1 END)
                        THEN 'growing'
                        WHEN COUNT(CASE WHEN c.event_date >= CURRENT_DATE - INTERVAL '6 months' THEN 1 END) < 
                             COUNT(CASE WHEN c.event_date < CURRENT_DATE - INTERVAL '6 months' 
                                        AND c.event_date >= CURRENT_DATE - INTERVAL '1 year' THEN 1 END)
                        THEN 'declining'
                        ELSE 'stable'
                    END as growth_trend
                FROM {self.schema_name}.artists a
                LEFT JOIN {self.schema_name}.concerts c ON a.artist_id = c.artist_id
                    AND c.status = 'completed'
                    AND c.event_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY a.artist_id, a.name, a.popularity_score
            ),
            ticket_sales_metrics AS (
                SELECT 
                    c.artist_id,
                    AVG(ts.quantity * ts.unit_price) as avg_ticket_sale_value
                FROM {self.schema_name}.concerts c
                JOIN {self.schema_name}.ticket_sales ts ON c.concert_id = ts.concert_id
                WHERE c.event_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY c.artist_id
            )
            SELECT 
                am.artist_id,
                COALESCE(am.total_concerts, 0),
                ROUND(COALESCE(tsm.avg_ticket_sale_value, 0), 2),
                ROUND(COALESCE(am.total_revenue, 0), 2),
                ROUND(
                    COALESCE(am.popularity_score, 0) * 0.3 + 
                    LEAST(COALESCE(am.avg_attendance, 0) / 10000, 10) * 0.4 + 
                    LEAST(COALESCE(am.total_revenue, 0) / 1000000, 10) * 0.3, 
                    2
                ) as fan_engagement_score,
                am.growth_trend,
                CURRENT_TIMESTAMP
            FROM artist_metrics am
            LEFT JOIN ticket_sales_metrics tsm ON am.artist_id = tsm.artist_id
            WHERE am.total_concerts > 0;
            
            -- Log the operation
            RAISE NOTICE 'Artist performance calculation completed for % artists', 
                (SELECT COUNT(*) FROM {self.schema_name}.artist_performance WHERE DATE(calculated_at) = CURRENT_DATE);
        END;
        $$;
        """
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created procedure {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create procedure {procedure_name}: {e}")
            return False
    
    def _create_generate_daily_sales_summary_procedure(self) -> bool:
        """Create procedure to generate daily sales summaries."""
        procedure_name = f"{self.schema_name}.generate_daily_sales_summary"
        
        create_procedure = f"""
        CREATE OR REPLACE PROCEDURE {procedure_name}(target_date DATE DEFAULT NULL)
        LANGUAGE plpgsql
        AS $$
        DECLARE
            process_date DATE;
        BEGIN
            -- Use provided date or default to yesterday
            process_date := COALESCE(target_date, CURRENT_DATE - 1);
            
            -- Delete existing records for the target date
            DELETE FROM {self.schema_name}.daily_sales_summary 
            WHERE summary_date = process_date;
            
            -- Generate daily sales summary
            INSERT INTO {self.schema_name}.daily_sales_summary (
                summary_date,
                artist_id,
                venue_id,
                concert_id,
                total_tickets_sold,
                total_revenue,
                avg_ticket_price,
                unique_customers,
                created_at
            )
            SELECT 
                process_date,
                c.artist_id,
                c.venue_id,
                c.concert_id,
                SUM(ts.quantity) as total_tickets_sold,
                SUM(ts.quantity * ts.unit_price) as total_revenue,
                AVG(ts.unit_price) as avg_ticket_price,
                COUNT(DISTINCT ts.sale_id) as unique_customers,
                CURRENT_TIMESTAMP
            FROM {self.schema_name}.concerts c
            JOIN {self.schema_name}.ticket_sales ts ON c.concert_id = ts.concert_id
            WHERE DATE(ts.purchase_timestamp) = process_date
            GROUP BY process_date, c.artist_id, c.venue_id, c.concert_id;
            
            -- Log the operation
            RAISE NOTICE 'Daily sales summary generated for % with % records', 
                process_date,
                (SELECT COUNT(*) FROM {self.schema_name}.daily_sales_summary WHERE summary_date = process_date);
        END;
        $$;
        """
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created procedure {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create procedure {procedure_name}: {e}")
            return False
    
    def _create_get_top_venues_procedure(self) -> bool:
        """Create procedure to get top performing venues."""
        procedure_name = f"{self.schema_name}.get_top_venues"
        
        create_procedure = f"""
        CREATE OR REPLACE FUNCTION {procedure_name}(
            limit_count INTEGER DEFAULT 10,
            time_period_days INTEGER DEFAULT 365
        )
        RETURNS TABLE (
            venue_id VARCHAR(50),
            venue_name VARCHAR(200),
            city VARCHAR(100),
            total_events INTEGER,
            total_revenue DECIMAL(15,2),
            avg_attendance_rate DECIMAL(5,2),
            popularity_rank INTEGER
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                v.venue_id,
                v.name as venue_name,
                v.city,
                COUNT(c.concert_id)::INTEGER as total_events,
                COALESCE(SUM(c.revenue), 0)::DECIMAL(15,2) as total_revenue,
                COALESCE(AVG(
                    CASE 
                        WHEN c.total_attendance IS NOT NULL AND v.capacity > 0 
                        THEN (c.total_attendance::DECIMAL / v.capacity) * 100 
                        ELSE NULL 
                    END
                ), 0)::DECIMAL(5,2) as avg_attendance_rate,
                COALESCE(vp.popularity_rank, 999)::INTEGER as popularity_rank
            FROM {self.schema_name}.venues v
            LEFT JOIN {self.schema_name}.concerts c ON v.venue_id = c.venue_id
                AND c.status = 'completed'
                AND c.event_date >= CURRENT_DATE - INTERVAL '%s days'
            LEFT JOIN {self.schema_name}.venue_popularity vp ON v.venue_id = vp.venue_id
                AND DATE(vp.calculated_at) = (
                    SELECT MAX(DATE(calculated_at)) 
                    FROM {self.schema_name}.venue_popularity
                )
            GROUP BY v.venue_id, v.name, v.city, v.capacity, vp.popularity_rank
            HAVING COUNT(c.concert_id) > 0
            ORDER BY 
                COALESCE(vp.popularity_rank, 999),
                total_revenue DESC,
                avg_attendance_rate DESC
            LIMIT limit_count;
        END;
        $$;
        """ % time_period_days
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created function {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create function {procedure_name}: {e}")
            return False
    
    def _create_get_artist_trends_procedure(self) -> bool:
        """Create procedure to get artist performance trends."""
        procedure_name = f"{self.schema_name}.get_artist_trends"
        
        create_procedure = f"""
        CREATE OR REPLACE FUNCTION {procedure_name}(
            limit_count INTEGER DEFAULT 20,
            trend_filter VARCHAR(20) DEFAULT 'all'
        )
        RETURNS TABLE (
            artist_id VARCHAR(50),
            artist_name VARCHAR(200),
            total_concerts INTEGER,
            revenue_generated DECIMAL(15,2),
            fan_engagement_score DECIMAL(5,2),
            growth_trend VARCHAR(20),
            popularity_score DECIMAL(5,2)
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                a.artist_id,
                a.name as artist_name,
                COALESCE(ap.total_concerts, 0)::INTEGER,
                COALESCE(ap.revenue_generated, 0)::DECIMAL(15,2),
                COALESCE(ap.fan_engagement_score, 0)::DECIMAL(5,2),
                COALESCE(ap.growth_trend, 'unknown')::VARCHAR(20),
                COALESCE(a.popularity_score, 0)::DECIMAL(5,2)
            FROM {self.schema_name}.artists a
            LEFT JOIN {self.schema_name}.artist_performance ap ON a.artist_id = ap.artist_id
                AND DATE(ap.calculated_at) = (
                    SELECT MAX(DATE(calculated_at)) 
                    FROM {self.schema_name}.artist_performance
                )
            WHERE 
                CASE 
                    WHEN trend_filter = 'growing' THEN COALESCE(ap.growth_trend, 'unknown') = 'growing'
                    WHEN trend_filter = 'declining' THEN COALESCE(ap.growth_trend, 'unknown') = 'declining'
                    WHEN trend_filter = 'stable' THEN COALESCE(ap.growth_trend, 'unknown') = 'stable'
                    ELSE TRUE
                END
                AND COALESCE(ap.total_concerts, 0) > 0
            ORDER BY 
                COALESCE(ap.fan_engagement_score, 0) DESC,
                COALESCE(ap.revenue_generated, 0) DESC,
                a.popularity_score DESC
            LIMIT limit_count;
        END;
        $$;
        """
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created function {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create function {procedure_name}: {e}")
            return False
    
    def _create_get_revenue_analytics_procedure(self) -> bool:
        """Create procedure to get revenue analytics."""
        procedure_name = f"{self.schema_name}.get_revenue_analytics"
        
        create_procedure = f"""
        CREATE OR REPLACE FUNCTION {procedure_name}(
            start_date DATE DEFAULT NULL,
            end_date DATE DEFAULT NULL,
            group_by_period VARCHAR(10) DEFAULT 'month'
        )
        RETURNS TABLE (
            period_start DATE,
            period_end DATE,
            total_concerts INTEGER,
            total_revenue DECIMAL(15,2),
            avg_revenue_per_concert DECIMAL(10,2),
            total_tickets_sold INTEGER,
            avg_ticket_price DECIMAL(8,2)
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            date_trunc_format VARCHAR(10);
        BEGIN
            -- Set default dates if not provided
            start_date := COALESCE(start_date, CURRENT_DATE - INTERVAL '1 year');
            end_date := COALESCE(end_date, CURRENT_DATE);
            
            -- Validate group_by_period
            IF group_by_period NOT IN ('day', 'week', 'month', 'quarter', 'year') THEN
                group_by_period := 'month';
            END IF;
            
            RETURN QUERY
            WITH period_data AS (
                SELECT 
                    DATE_TRUNC(group_by_period, c.event_date)::DATE as period_start,
                    COUNT(c.concert_id) as concert_count,
                    SUM(c.revenue) as period_revenue,
                    SUM(ts.quantity) as tickets_sold,
                    AVG(ts.unit_price) as avg_price
                FROM {self.schema_name}.concerts c
                LEFT JOIN {self.schema_name}.ticket_sales ts ON c.concert_id = ts.concert_id
                WHERE c.event_date >= start_date 
                    AND c.event_date <= end_date
                    AND c.status = 'completed'
                GROUP BY DATE_TRUNC(group_by_period, c.event_date)
            )
            SELECT 
                pd.period_start,
                CASE 
                    WHEN group_by_period = 'day' THEN pd.period_start
                    WHEN group_by_period = 'week' THEN pd.period_start + INTERVAL '6 days'
                    WHEN group_by_period = 'month' THEN pd.period_start + INTERVAL '1 month' - INTERVAL '1 day'
                    WHEN group_by_period = 'quarter' THEN pd.period_start + INTERVAL '3 months' - INTERVAL '1 day'
                    WHEN group_by_period = 'year' THEN pd.period_start + INTERVAL '1 year' - INTERVAL '1 day'
                END::DATE as period_end,
                pd.concert_count::INTEGER,
                COALESCE(pd.period_revenue, 0)::DECIMAL(15,2),
                CASE 
                    WHEN pd.concert_count > 0 THEN (pd.period_revenue / pd.concert_count)::DECIMAL(10,2)
                    ELSE 0::DECIMAL(10,2)
                END,
                COALESCE(pd.tickets_sold, 0)::INTEGER,
                COALESCE(pd.avg_price, 0)::DECIMAL(8,2)
            FROM period_data pd
            ORDER BY pd.period_start;
        END;
        $$;
        """
        
        try:
            self.client.execute_query(create_procedure)
            logger.info(f"Successfully created function {procedure_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create function {procedure_name}: {e}")
            return False
    
    def execute_venue_popularity_calculation(self) -> bool:
        """Execute venue popularity calculation procedure."""
        try:
            self.client.execute_query(f"CALL {self.schema_name}.calculate_venue_popularity();")
            logger.info("Venue popularity calculation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to execute venue popularity calculation: {e}")
            return False
    
    def execute_artist_performance_calculation(self) -> bool:
        """Execute artist performance calculation procedure."""
        try:
            self.client.execute_query(f"CALL {self.schema_name}.calculate_artist_performance();")
            logger.info("Artist performance calculation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to execute artist performance calculation: {e}")
            return False
    
    def execute_daily_sales_summary(self, target_date: Optional[str] = None) -> bool:
        """Execute daily sales summary generation."""
        try:
            if target_date:
                query = f"CALL {self.schema_name}.generate_daily_sales_summary('{target_date}');"
            else:
                query = f"CALL {self.schema_name}.generate_daily_sales_summary();"
            
            self.client.execute_query(query)
            logger.info(f"Daily sales summary generation completed for {target_date or 'yesterday'}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute daily sales summary generation: {e}")
            return False
    
    def get_top_venues(self, limit: int = 10, days: int = 365) -> List[Dict[str, Any]]:
        """Get top performing venues."""
        try:
            query = f"SELECT * FROM {self.schema_name}.get_top_venues({limit}, {days});"
            return self.client.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get top venues: {e}")
            return []
    
    def get_artist_trends(self, limit: int = 20, trend_filter: str = 'all') -> List[Dict[str, Any]]:
        """Get artist performance trends."""
        try:
            query = f"SELECT * FROM {self.schema_name}.get_artist_trends({limit}, '{trend_filter}');"
            return self.client.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get artist trends: {e}")
            return []
    
    def get_revenue_analytics(self, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None, 
                            period: str = 'month') -> List[Dict[str, Any]]:
        """Get revenue analytics by period."""
        try:
            start_param = f"'{start_date}'" if start_date else 'NULL'
            end_param = f"'{end_date}'" if end_date else 'NULL'
            
            query = f"SELECT * FROM {self.schema_name}.get_revenue_analytics({start_param}, {end_param}, '{period}');"
            return self.client.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {e}")
            return []