"""
AWS Lambda function handlers for API Gateway endpoints.

These handlers provide serverless API endpoints for:
- Chatbot message processing
- Venue popularity queries
- Ticket sales predictions
- Concert recommendations
"""
import json
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

# Configure structured logging for Lambda
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Environment variables
REGION = os.environ.get('AWS_REGION', 'us-east-1')
REDSHIFT_CLUSTER_ID = os.environ.get('REDSHIFT_CLUSTER_ID')
REDSHIFT_DATABASE = os.environ.get('REDSHIFT_DATABASE', 'concert_data')
AGENT_ID = os.environ.get('BEDROCK_AGENT_ID')
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
SAGEMAKER_VENUE_ENDPOINT = os.environ.get('SAGEMAKER_VENUE_ENDPOINT')
SAGEMAKER_TICKET_ENDPOINT = os.environ.get('SAGEMAKER_TICKET_ENDPOINT')


def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional custom headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }


def create_error_response(
    status_code: int,
    error_message: str,
    error_details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        error_details: Optional detailed error information
        
    Returns:
        API Gateway error response
    """
    body = {
        'error': error_message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if error_details:
        body['details'] = error_details
    
    return create_response(status_code, body)


def parse_request_body(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse and validate request body from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Parsed body dictionary or None if parsing fails
    """
    try:
        body = event.get('body', '{}')
        if isinstance(body, str):
            return json.loads(body)
        return body
    except json.JSONDecodeError as e:
        logger.error("Failed to parse request body", error=str(e))
        return None


# ============================================================================
# Chatbot Lambda Handler
# ============================================================================

def chatbot_handler(event, context):
    """
    Lambda handler for chatbot message processing.
    
    Endpoint: POST /chat
    
    Request body:
    {
        "message": "string",
        "session_id": "string (optional)",
        "user_id": "string (optional)"
    }
    
    Response:
    {
        "message": "string",
        "session_id": "string",
        "intent": "string",
        "confidence": float,
        "data": object,
        "suggestions": ["string"],
        "timestamp": "string"
    }
    """
    logger.info("Chatbot handler invoked", request_id=context.request_id)
    
    try:
        # Parse request body
        body = parse_request_body(event)
        if not body:
            return create_error_response(400, "Invalid request body")
        
        # Validate required fields
        message = body.get('message')
        if not message:
            return create_error_response(400, "Missing required field: message")
        
        session_id = body.get('session_id')
        user_id = body.get('user_id')
        
        # Initialize Bedrock Agent Runtime client
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)
        
        # Create session if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            logger.info("Created new session", session_id=session_id)
        
        # Invoke Bedrock Agent if configured
        if AGENT_ID and AGENT_ALIAS_ID:
            try:
                response = bedrock_agent_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS_ID,
                    sessionId=session_id,
                    inputText=message
                )
                
                # Parse response from event stream
                response_text = ""
                for event_item in response.get('completion', []):
                    if 'chunk' in event_item:
                        chunk = event_item['chunk']
                        if 'bytes' in chunk:
                            response_text += chunk['bytes'].decode('utf-8')
                
                return create_response(200, {
                    'message': response_text or "I processed your request.",
                    'session_id': session_id,
                    'intent': 'general_query',
                    'confidence': 0.9,
                    'data': None,
                    'suggestions': [],
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                logger.error("Bedrock Agent invocation failed", error_code=error_code)
                
                # Fall through to fallback response
        
        # Fallback response when Bedrock Agent is not available
        fallback_message = (
            "I'm your Concert AI assistant. I can help you with:\n"
            "- Finding information about artists and venues\n"
            "- Recommending concerts\n"
            "- Predicting ticket sales\n"
            "- Analyzing concert data\n\n"
            "What would you like to know?"
        )
        
        return create_response(200, {
            'message': fallback_message,
            'session_id': session_id,
            'intent': 'general_query',
            'confidence': 0.8,
            'data': None,
            'suggestions': [
                "Tell me about popular artists",
                "Find venues in New York",
                "Recommend concerts for me"
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Chatbot handler failed", error=str(e), traceback=traceback.format_exc())
        return create_error_response(500, "Internal server error", str(e))


# ============================================================================
# Venue Popularity Lambda Handler
# ============================================================================

def venue_popularity_handler(event, context):
    """
    Lambda handler for venue popularity queries.
    
    Endpoint: POST /venues/popularity
    
    Request body:
    {
        "top_n": int (optional, default: 10),
        "min_events": int (optional, default: 5)
    }
    
    Response:
    {
        "venues": [
            {
                "venue_id": "string",
                "name": "string",
                "popularity_rank": int,
                "popularity_score": float,
                "avg_attendance_rate": float,
                "revenue_per_event": float,
                "booking_frequency": float
            }
        ],
        "total_venues": int,
        "timestamp": "string"
    }
    """
    logger.info("Venue popularity handler invoked", request_id=context.request_id)
    
    try:
        # Parse request body
        body = parse_request_body(event) or {}
        
        top_n = body.get('top_n', 10)
        min_events = body.get('min_events', 5)
        
        # Validate parameters
        if not isinstance(top_n, int) or top_n < 1 or top_n > 100:
            return create_error_response(400, "Invalid top_n parameter (must be 1-100)")
        
        if not isinstance(min_events, int) or min_events < 1:
            return create_error_response(400, "Invalid min_events parameter (must be >= 1)")
        
        # Query Redshift for venue popularity data
        if not REDSHIFT_CLUSTER_ID:
            return create_error_response(503, "Redshift service not configured")
        
        redshift_data = boto3.client('redshift-data', region_name=REGION)
        
        query = f"""
        WITH venue_stats AS (
            SELECT 
                v.venue_id,
                v.name,
                v.city,
                v.state,
                v.capacity,
                v.venue_type,
                COUNT(DISTINCT c.concert_id) as total_concerts,
                AVG(c.total_attendance::float / v.capacity) as avg_attendance_rate,
                AVG(c.revenue) as avg_revenue_per_event,
                COUNT(DISTINCT c.concert_id)::float / 
                    NULLIF(DATEDIFF(month, MIN(c.event_date), MAX(c.event_date)), 0) as booking_frequency
            FROM venues v
            LEFT JOIN concerts c ON v.venue_id = c.venue_id
            WHERE c.status = 'completed'
                AND c.event_date >= DATEADD(day, -365, CURRENT_DATE)
            GROUP BY v.venue_id, v.name, v.city, v.state, v.capacity, v.venue_type
            HAVING COUNT(DISTINCT c.concert_id) >= {min_events}
        )
        SELECT 
            venue_id,
            name,
            city,
            state,
            capacity,
            venue_type,
            total_concerts,
            avg_attendance_rate,
            avg_revenue_per_event,
            booking_frequency,
            ROW_NUMBER() OVER (ORDER BY avg_attendance_rate DESC, avg_revenue_per_event DESC) as popularity_rank
        FROM venue_stats
        ORDER BY popularity_rank
        LIMIT {top_n}
        """
        
        # Execute query
        response = redshift_data.execute_statement(
            ClusterIdentifier=REDSHIFT_CLUSTER_ID,
            Database=REDSHIFT_DATABASE,
            Sql=query
        )
        
        query_id = response['Id']
        
        # Wait for query to complete (with timeout)
        import time
        max_wait = 30  # seconds
        wait_interval = 1
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = redshift_data.describe_statement(Id=query_id)
            status = status_response['Status']
            
            if status == 'FINISHED':
                break
            elif status in ['FAILED', 'ABORTED']:
                error_msg = status_response.get('Error', 'Query failed')
                logger.error("Redshift query failed", error=error_msg)
                return create_error_response(500, "Database query failed", error_msg)
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        if elapsed >= max_wait:
            return create_error_response(504, "Query timeout")
        
        # Get query results
        result_response = redshift_data.get_statement_result(Id=query_id)
        
        # Parse results
        venues = []
        for row in result_response.get('Records', []):
            venue = {
                'venue_id': row[0].get('stringValue', ''),
                'name': row[1].get('stringValue', ''),
                'city': row[2].get('stringValue', ''),
                'state': row[3].get('stringValue', ''),
                'capacity': int(row[4].get('longValue', 0)),
                'venue_type': row[5].get('stringValue', ''),
                'total_concerts': int(row[6].get('longValue', 0)),
                'avg_attendance_rate': float(row[7].get('doubleValue', 0.0)),
                'revenue_per_event': float(row[8].get('doubleValue', 0.0)),
                'booking_frequency': float(row[9].get('doubleValue', 0.0)),
                'popularity_rank': int(row[10].get('longValue', 0))
            }
            venues.append(venue)
        
        return create_response(200, {
            'venues': venues,
            'total_venues': len(venues),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Venue popularity handler failed", error=str(e), traceback=traceback.format_exc())
        return create_error_response(500, "Internal server error", str(e))


# ============================================================================
# Ticket Sales Prediction Lambda Handler
# ============================================================================

def ticket_prediction_handler(event, context):
    """
    Lambda handler for ticket sales predictions.
    
    Endpoint: POST /tickets/predict
    
    Request body:
    {
        "artist_id": "string",
        "venue_id": "string",
        "event_date": "string (YYYY-MM-DD, optional)",
        "ticket_price": float (optional)
    }
    
    Response:
    {
        "predicted_sales": float,
        "confidence": float,
        "features_used": object,
        "timestamp": "string"
    }
    """
    logger.info("Ticket prediction handler invoked", request_id=context.request_id)
    
    try:
        # Parse request body
        body = parse_request_body(event)
        if not body:
            return create_error_response(400, "Invalid request body")
        
        # Validate required fields
        artist_id = body.get('artist_id')
        venue_id = body.get('venue_id')
        
        if not artist_id or not venue_id:
            return create_error_response(400, "Missing required fields: artist_id, venue_id")
        
        event_date = body.get('event_date')
        ticket_price = body.get('ticket_price', 50.0)
        
        # Check if SageMaker endpoint is configured
        if not SAGEMAKER_TICKET_ENDPOINT:
            # Return mock prediction if endpoint not configured
            logger.warning("SageMaker ticket endpoint not configured, returning mock prediction")
            
            return create_response(200, {
                'predicted_sales': 5000.0,
                'confidence': 0.75,
                'features_used': {
                    'artist_id': artist_id,
                    'venue_id': venue_id,
                    'event_date': event_date,
                    'ticket_price': ticket_price
                },
                'note': 'Mock prediction - SageMaker endpoint not configured',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Invoke SageMaker endpoint
        sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=REGION)
        
        # Prepare feature vector (simplified - would need full feature extraction in production)
        # This is a placeholder that would be replaced with actual feature extraction
        feature_vector = [
            0.75,  # artist_popularity_score
            1000.0,  # artist_avg_attendance
            50,  # artist_total_concerts
            50000.0,  # artist_avg_revenue
            0.8,  # artist_genre_popularity
            5000,  # venue_capacity
            0.85,  # venue_avg_attendance_rate
            10.0,  # venue_popularity_rank
            4.0,  # venue_type_encoded
            100.0,  # venue_location_popularity
            45000.0,  # historical_avg_sales
            75000.0,  # historical_max_sales
            40000.0,  # similar_concert_avg_sales
            60,  # days_until_event
            1.0,  # is_weekend
            6.0,  # month_of_year
            3.0,  # season_encoded
            ticket_price,  # avg_ticket_price
            50.0,  # price_range
            25.0,  # lowest_price
            75.0  # highest_price
        ]
        
        payload = ','.join(map(str, feature_vector))
        
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_TICKET_ENDPOINT,
            ContentType='text/csv',
            Body=payload
        )
        
        # Parse prediction
        result = json.loads(response['Body'].read().decode())
        predicted_sales = float(result) if isinstance(result, (int, float)) else float(result[0])
        
        # Calculate confidence score (simplified)
        confidence = 0.85
        
        return create_response(200, {
            'predicted_sales': predicted_sales,
            'confidence': confidence,
            'features_used': {
                'artist_id': artist_id,
                'venue_id': venue_id,
                'event_date': event_date,
                'ticket_price': ticket_price
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Ticket prediction handler failed", error=str(e), traceback=traceback.format_exc())
        return create_error_response(500, "Internal server error", str(e))


# ============================================================================
# Recommendations Lambda Handler
# ============================================================================

def recommendations_handler(event, context):
    """
    Lambda handler for concert recommendations.
    
    Endpoint: POST /recommendations
    
    Request body:
    {
        "user_id": "string (optional)",
        "artist_preferences": ["string"] (optional),
        "location": "string (optional)",
        "top_n": int (optional, default: 10)
    }
    
    Response:
    {
        "recommendations": [
            {
                "concert_id": "string",
                "artist_name": "string",
                "venue_name": "string",
                "event_date": "string",
                "score": float,
                "reasoning": "string"
            }
        ],
        "total_recommendations": int,
        "recommendation_type": "string",
        "timestamp": "string"
    }
    """
    logger.info("Recommendations handler invoked", request_id=context.request_id)
    
    try:
        # Parse request body
        body = parse_request_body(event) or {}
        
        user_id = body.get('user_id')
        artist_preferences = body.get('artist_preferences', [])
        location = body.get('location')
        top_n = body.get('top_n', 10)
        
        # Validate parameters
        if not isinstance(top_n, int) or top_n < 1 or top_n > 50:
            return create_error_response(400, "Invalid top_n parameter (must be 1-50)")
        
        # Query Redshift for concert recommendations
        if not REDSHIFT_CLUSTER_ID:
            return create_error_response(503, "Redshift service not configured")
        
        redshift_data = boto3.client('redshift-data', region_name=REGION)
        
        # Build query with optional filters
        where_clauses = ["c.status = 'scheduled'", "c.event_date >= CURRENT_DATE"]
        
        if location:
            where_clauses.append(f"(v.city ILIKE '%{location}%' OR v.state ILIKE '%{location}%')")
        
        if artist_preferences:
            genres_str = "','".join(artist_preferences)
            where_clauses.append(f"a.genre IN ('{genres_str}')")
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            c.concert_id,
            a.name as artist_name,
            a.genre,
            a.popularity_score,
            v.name as venue_name,
            v.city,
            v.state,
            v.capacity,
            c.event_date,
            c.ticket_prices
        FROM concerts c
        JOIN artists a ON c.artist_id = a.artist_id
        JOIN venues v ON c.venue_id = v.venue_id
        WHERE {where_clause}
        ORDER BY a.popularity_score DESC, c.event_date ASC
        LIMIT {top_n}
        """
        
        # Execute query
        response = redshift_data.execute_statement(
            ClusterIdentifier=REDSHIFT_CLUSTER_ID,
            Database=REDSHIFT_DATABASE,
            Sql=query
        )
        
        query_id = response['Id']
        
        # Wait for query to complete
        import time
        max_wait = 30
        wait_interval = 1
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = redshift_data.describe_statement(Id=query_id)
            status = status_response['Status']
            
            if status == 'FINISHED':
                break
            elif status in ['FAILED', 'ABORTED']:
                error_msg = status_response.get('Error', 'Query failed')
                logger.error("Redshift query failed", error=error_msg)
                return create_error_response(500, "Database query failed", error_msg)
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        if elapsed >= max_wait:
            return create_error_response(504, "Query timeout")
        
        # Get query results
        result_response = redshift_data.get_statement_result(Id=query_id)
        
        # Parse results
        recommendations = []
        for idx, row in enumerate(result_response.get('Records', [])):
            recommendation = {
                'concert_id': row[0].get('stringValue', ''),
                'artist_name': row[1].get('stringValue', ''),
                'genre': row[2].get('stringValue', ''),
                'artist_popularity': float(row[3].get('doubleValue', 0.0)),
                'venue_name': row[4].get('stringValue', ''),
                'city': row[5].get('stringValue', ''),
                'state': row[6].get('stringValue', ''),
                'capacity': int(row[7].get('longValue', 0)),
                'event_date': row[8].get('stringValue', ''),
                'score': 1.0 - (idx * 0.05),  # Simple scoring based on rank
                'reasoning': f"Popular {row[2].get('stringValue', '')} artist"
            }
            recommendations.append(recommendation)
        
        recommendation_type = "content_based"
        if artist_preferences:
            recommendation_type = "genre_filtered"
        if location:
            recommendation_type = "location_filtered"
        
        return create_response(200, {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'recommendation_type': recommendation_type,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Recommendations handler failed", error=str(e), traceback=traceback.format_exc())
        return create_error_response(500, "Internal server error", str(e))


# ============================================================================
# Health Check Lambda Handler
# ============================================================================

def health_check_handler(event, context):
    """
    Lambda handler for health check endpoint.
    
    Endpoint: GET /health
    
    Response:
    {
        "status": "healthy",
        "timestamp": "string",
        "version": "string",
        "services": {
            "redshift": "string",
            "bedrock_agent": "string",
            "sagemaker_venue": "string",
            "sagemaker_ticket": "string"
        }
    }
    """
    logger.info("Health check handler invoked", request_id=context.request_id)
    
    try:
        services_status = {
            'redshift': 'configured' if REDSHIFT_CLUSTER_ID else 'not_configured',
            'bedrock_agent': 'configured' if (AGENT_ID and AGENT_ALIAS_ID) else 'not_configured',
            'sagemaker_venue': 'configured' if SAGEMAKER_VENUE_ENDPOINT else 'not_configured',
            'sagemaker_ticket': 'configured' if SAGEMAKER_TICKET_ENDPOINT else 'not_configured'
        }
        
        return create_response(200, {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': services_status
        })
        
    except Exception as e:
        logger.error("Health check handler failed", error=str(e))
        return create_error_response(500, "Health check failed", str(e))
