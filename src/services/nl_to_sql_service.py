"""
Natural Language to SQL Query Translator Service.

This service translates natural language queries about concert data into safe SQL queries
that can be executed against the Redshift data warehouse.
"""
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.services.redshift_service import RedshiftService


class QueryIntent(str, Enum):
    """Supported query intents for concert data."""
    ARTIST_LOOKUP = "artist_lookup"
    VENUE_SEARCH = "venue_search"
    CONCERT_SEARCH = "concert_search"
    TICKET_SALES_QUERY = "ticket_sales_query"
    POPULARITY_RANKING = "popularity_ranking"
    REVENUE_ANALYSIS = "revenue_analysis"
    UNKNOWN = "unknown"


class ExtractedEntity(BaseModel):
    """Extracted entity from natural language query."""
    entity_type: str  # artist, venue, date, location, genre, etc.
    value: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class QueryContext(BaseModel):
    """Context for query generation."""
    intent: QueryIntent
    entities: List[ExtractedEntity] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="DESC")


class SQLQuery(BaseModel):
    """Generated SQL query with metadata."""
    sql: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    intent: QueryIntent
    is_safe: bool = True
    safety_warnings: List[str] = Field(default_factory=list)
    estimated_complexity: str = "low"  # low, medium, high


class QueryResult(BaseModel):
    """Result from query execution."""
    success: bool
    data: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    query: Optional[SQLQuery] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class NLToSQLService:
    """
    Natural Language to SQL Query Translator Service.
    
    Provides:
    - Intent classification for concert data queries
    - Entity extraction using AWS Bedrock
    - SQL query generation with template-based approach
    - Query validation and SQL injection prevention
    - Integration with Redshift for query execution
    """
    
    def __init__(
        self,
        redshift_service: Optional[RedshiftService] = None,
        region: Optional[str] = None,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    ):
        """
        Initialize NL to SQL service.
        
        Args:
            redshift_service: Optional RedshiftService instance
            region: AWS region for Bedrock
            model_id: Bedrock model ID for entity extraction
        """
        self.region = region or settings.aws.region
        self.model_id = model_id
        self.redshift_service = redshift_service
        
        # Initialize Bedrock Runtime client for entity extraction
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock Runtime client: {e}")
            self.bedrock_runtime = None
        
        # Intent classification patterns (order matters - more specific first)
        self.intent_patterns = {
            QueryIntent.REVENUE_ANALYSIS: [
                r'\b(revenue|earnings|income|profit)\b',
                r'\b(total|sum)\b.*\b(revenue|earnings)\b',
                r'\b(financial|money)\b.*\b(artist|concert|venue)\b',
                r'\b(highest|most)\b.*\b(earning|revenue)\b'
            ],
            QueryIntent.TICKET_SALES_QUERY: [
                r'\b(ticket|sales|sold)\b',
                r'\b(how many|total)\b.*\b(ticket|sales)\b',
                r'\b(price|pricing)\b',
                r'\b(ticket).*\b(revenue|sales)\b'
            ],
            QueryIntent.POPULARITY_RANKING: [
                r'\b(popular|top|best|ranking|rank)\b',
                r'\b(most|highest)\b.*\b(popular|attended)\b',
                r'\b(trending|hot)\b'
            ],
            QueryIntent.ARTIST_LOOKUP: [
                r'\b(tell me about|who is|information about)\b',
                r'\b(find|search|show|list)\b.*\b(artist|band|musician)\b',
                r'\b(artist|band|musician|performer|singer)\b.*\b(genre|style|type)\b'
            ],
            QueryIntent.VENUE_SEARCH: [
                r'\b(venue|location|place|arena|theater|stadium)\b',
                r'\b(where|find|search)\b.*\b(venue|location)\b',
                r'\b(capacity|seating)\b'
            ],
            QueryIntent.CONCERT_SEARCH: [
                r'\b(concert|show|event|performance|gig)\b',
                r'\b(when|upcoming|scheduled)\b.*\b(concert|show)\b',
                r'\b(find|search|list)\b.*\b(concert|show)\b'
            ]
        }
        
        # SQL injection patterns to block
        self.dangerous_patterns = [
            r'\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b',
            r';.*\b(SELECT|INSERT|UPDATE|DELETE)\b',
            r'--',
            r'/\*.*\*/',
            r'\bUNION\b.*\bSELECT\b',
            r'\bEXEC\b|\bEXECUTE\b',
            r'xp_cmdshell',
            r'\bINTO\b.*\bOUTFILE\b'
        ]
    
    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify the intent of a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Detected query intent
        """
        query_lower = query.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent
        
        return QueryIntent.UNKNOWN
    
    def extract_entities(self, query: str, intent: QueryIntent) -> List[ExtractedEntity]:
        """
        Extract entities from natural language query using Bedrock.
        
        Args:
            query: Natural language query
            intent: Detected intent
            
        Returns:
            List of extracted entities
        """
        if not self.bedrock_runtime:
            # Fallback to simple regex-based extraction
            return self._extract_entities_regex(query, intent)
        
        try:
            # Create prompt for entity extraction
            prompt = self._create_entity_extraction_prompt(query, intent)
            
            # Call Bedrock
            response = self._invoke_bedrock(prompt)
            
            # Parse entities from response
            entities = self._parse_entity_response(response)
            
            return entities
            
        except Exception as e:
            print(f"Bedrock entity extraction failed: {e}, falling back to regex")
            return self._extract_entities_regex(query, intent)
    
    def _create_entity_extraction_prompt(self, query: str, intent: QueryIntent) -> str:
        """Create prompt for Bedrock entity extraction."""
        prompt = f"""Extract entities from this concert-related query.

Query: "{query}"
Intent: {intent.value}

Extract the following entity types if present:
- artist_name: Name of artist or band
- venue_name: Name of venue or location
- city: City name
- state: State or province
- country: Country name
- genre: Music genre
- date: Date or date range
- capacity: Venue capacity
- price: Ticket price
- limit: Number of results requested

Return ONLY a JSON array of entities in this format:
[
  {{"entity_type": "artist_name", "value": "The Beatles", "confidence": 0.9}},
  {{"entity_type": "city", "value": "New York", "confidence": 0.95}}
]

If no entities found, return an empty array: []
"""
        return prompt
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock model for entity extraction."""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            raise Exception(f"Bedrock invocation failed: {e}")
    
    def _parse_entity_response(self, response: str) -> List[ExtractedEntity]:
        """Parse entity extraction response from Bedrock."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                return []
            
            entities_data = json.loads(json_match.group(0))
            
            entities = []
            for entity_dict in entities_data:
                # Convert value to string if it's not already
                value = entity_dict['value']
                if not isinstance(value, str):
                    value = str(value)
                
                entities.append(ExtractedEntity(
                    entity_type=entity_dict['entity_type'],
                    value=value,
                    confidence=entity_dict.get('confidence', 1.0)
                ))
            
            return entities
            
        except Exception as e:
            print(f"Failed to parse entity response: {e}")
            return []
    
    def _extract_entities_regex(self, query: str, intent: QueryIntent) -> List[ExtractedEntity]:
        """Fallback regex-based entity extraction."""
        entities = []
        query_lower = query.lower()
        
        # Extract numbers (for limits, capacity, prices)
        number_match = re.search(r'\b(\d+)\b', query)
        if number_match:
            number = int(number_match.group(1))
            if number <= 100:
                entities.append(ExtractedEntity(
                    entity_type="limit",
                    value=str(number),
                    confidence=0.8
                ))
        
        # Extract quoted strings (likely names)
        quoted_matches = re.findall(r'"([^"]+)"', query)
        for match in quoted_matches:
            if intent == QueryIntent.ARTIST_LOOKUP:
                entities.append(ExtractedEntity(
                    entity_type="artist_name",
                    value=match,
                    confidence=0.9
                ))
            elif intent == QueryIntent.VENUE_SEARCH:
                entities.append(ExtractedEntity(
                    entity_type="venue_name",
                    value=match,
                    confidence=0.9
                ))
        
        # Extract common city names
        cities = ['new york', 'los angeles', 'chicago', 'houston', 'phoenix', 
                 'philadelphia', 'san antonio', 'san diego', 'dallas', 'san jose',
                 'austin', 'boston', 'seattle', 'denver', 'nashville', 'miami']
        for city in cities:
            if city in query_lower:
                entities.append(ExtractedEntity(
                    entity_type="city",
                    value=city.title(),
                    confidence=0.85
                ))
        
        # Extract genres
        genres = ['rock', 'pop', 'jazz', 'blues', 'country', 'hip hop', 'rap',
                 'electronic', 'classical', 'metal', 'indie', 'folk']
        for genre in genres:
            if genre in query_lower:
                entities.append(ExtractedEntity(
                    entity_type="genre",
                    value=genre,
                    confidence=0.8
                ))
        
        return entities

    
    def build_query_context(
        self,
        query: str,
        intent: Optional[QueryIntent] = None,
        entities: Optional[List[ExtractedEntity]] = None
    ) -> QueryContext:
        """
        Build query context from natural language query.
        
        Args:
            query: Natural language query
            intent: Optional pre-classified intent
            entities: Optional pre-extracted entities
            
        Returns:
            Query context for SQL generation
        """
        # Classify intent if not provided
        if intent is None:
            intent = self.classify_intent(query)
        
        # Extract entities if not provided
        if entities is None:
            entities = self.extract_entities(query, intent)
        
        # Build filters from entities
        filters = {}
        limit = 10
        sort_by = None
        sort_order = "DESC"
        
        for entity in entities:
            if entity.entity_type == "limit":
                limit = min(int(entity.value), 100)
            elif entity.entity_type == "artist_name":
                filters["artist_name"] = entity.value
            elif entity.entity_type == "venue_name":
                filters["venue_name"] = entity.value
            elif entity.entity_type == "city":
                filters["city"] = entity.value
            elif entity.entity_type == "state":
                filters["state"] = entity.value
            elif entity.entity_type == "country":
                filters["country"] = entity.value
            elif entity.entity_type == "genre":
                filters["genre"] = entity.value
            elif entity.entity_type == "date":
                filters["date"] = entity.value
            elif entity.entity_type == "capacity":
                filters["capacity"] = entity.value
            elif entity.entity_type == "price":
                filters["price"] = entity.value
        
        # Determine sort based on intent
        if intent == QueryIntent.POPULARITY_RANKING:
            sort_by = "popularity_score"
        elif intent == QueryIntent.REVENUE_ANALYSIS:
            sort_by = "revenue"
        elif intent == QueryIntent.TICKET_SALES_QUERY:
            sort_by = "total_tickets_sold"
        
        return QueryContext(
            intent=intent,
            entities=entities,
            filters=filters,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    def generate_sql(self, context: QueryContext) -> SQLQuery:
        """
        Generate SQL query from query context using template-based approach.
        
        Args:
            context: Query context
            
        Returns:
            Generated SQL query with safety validation
        """
        # Route to appropriate SQL generator based on intent
        if context.intent == QueryIntent.ARTIST_LOOKUP:
            sql = self._generate_artist_lookup_sql(context)
        elif context.intent == QueryIntent.VENUE_SEARCH:
            sql = self._generate_venue_search_sql(context)
        elif context.intent == QueryIntent.CONCERT_SEARCH:
            sql = self._generate_concert_search_sql(context)
        elif context.intent == QueryIntent.TICKET_SALES_QUERY:
            sql = self._generate_ticket_sales_sql(context)
        elif context.intent == QueryIntent.POPULARITY_RANKING:
            sql = self._generate_popularity_ranking_sql(context)
        elif context.intent == QueryIntent.REVENUE_ANALYSIS:
            sql = self._generate_revenue_analysis_sql(context)
        else:
            sql = self._generate_default_sql(context)
        
        # Validate SQL safety
        is_safe, warnings = self._validate_sql_safety(sql)
        
        # Estimate query complexity
        complexity = self._estimate_query_complexity(sql)
        
        return SQLQuery(
            sql=sql,
            parameters={},
            intent=context.intent,
            is_safe=is_safe,
            safety_warnings=warnings,
            estimated_complexity=complexity
        )
    
    def _generate_artist_lookup_sql(self, context: QueryContext) -> str:
        """Generate SQL for artist lookup queries."""
        base_query = """
        SELECT 
            artist_id,
            name,
            genre,
            popularity_score,
            formation_date,
            members,
            spotify_id
        FROM concert_dw.artists
        WHERE 1=1
        """
        
        conditions = []
        
        # Add filters
        if "artist_name" in context.filters:
            artist_name = context.filters["artist_name"].replace("'", "''")
            conditions.append(f"AND LOWER(name) LIKE LOWER('%{artist_name}%')")
        
        if "genre" in context.filters:
            genre = context.filters["genre"].replace("'", "''")
            conditions.append(f"AND LOWER(genre) LIKE LOWER('%{genre}%')")
        
        # Add conditions to query
        for condition in conditions:
            base_query += f"\n{condition}"
        
        # Add sorting
        if context.sort_by:
            base_query += f"\nORDER BY {context.sort_by} {context.sort_order}"
        else:
            base_query += "\nORDER BY popularity_score DESC"
        
        # Add limit
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_venue_search_sql(self, context: QueryContext) -> str:
        """Generate SQL for venue search queries."""
        base_query = """
        SELECT 
            venue_id,
            name,
            city,
            state,
            country,
            capacity,
            venue_type,
            address,
            postal_code
        FROM concert_dw.venues
        WHERE 1=1
        """
        
        conditions = []
        
        # Add filters
        if "venue_name" in context.filters:
            venue_name = context.filters["venue_name"].replace("'", "''")
            conditions.append(f"AND LOWER(name) LIKE LOWER('%{venue_name}%')")
        
        if "city" in context.filters:
            city = context.filters["city"].replace("'", "''")
            conditions.append(f"AND LOWER(city) = LOWER('{city}')")
        
        if "state" in context.filters:
            state = context.filters["state"].replace("'", "''")
            conditions.append(f"AND LOWER(state) = LOWER('{state}')")
        
        if "country" in context.filters:
            country = context.filters["country"].replace("'", "''")
            conditions.append(f"AND LOWER(country) = LOWER('{country}')")
        
        if "capacity" in context.filters:
            capacity = int(context.filters["capacity"])
            conditions.append(f"AND capacity >= {capacity}")
        
        # Add conditions to query
        for condition in conditions:
            base_query += f"\n{condition}"
        
        # Add sorting
        if context.sort_by:
            base_query += f"\nORDER BY {context.sort_by} {context.sort_order}"
        else:
            base_query += "\nORDER BY capacity DESC"
        
        # Add limit
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_concert_search_sql(self, context: QueryContext) -> str:
        """Generate SQL for concert search queries."""
        base_query = """
        SELECT 
            c.concert_id,
            c.event_date,
            a.name as artist_name,
            v.name as venue_name,
            v.city,
            v.state,
            c.status,
            c.total_attendance,
            c.revenue
        FROM concert_dw.concerts c
        JOIN concert_dw.artists a ON c.artist_id = a.artist_id
        JOIN concert_dw.venues v ON c.venue_id = v.venue_id
        WHERE 1=1
        """
        
        conditions = []
        
        # Add filters
        if "artist_name" in context.filters:
            artist_name = context.filters["artist_name"].replace("'", "''")
            conditions.append(f"AND LOWER(a.name) LIKE LOWER('%{artist_name}%')")
        
        if "venue_name" in context.filters:
            venue_name = context.filters["venue_name"].replace("'", "''")
            conditions.append(f"AND LOWER(v.name) LIKE LOWER('%{venue_name}%')")
        
        if "city" in context.filters:
            city = context.filters["city"].replace("'", "''")
            conditions.append(f"AND LOWER(v.city) = LOWER('{city}')")
        
        # Default to upcoming concerts if no date filter
        if "date" not in context.filters:
            conditions.append("AND c.event_date >= CURRENT_DATE")
        
        # Add conditions to query
        for condition in conditions:
            base_query += f"\n{condition}"
        
        # Add sorting
        if context.sort_by:
            base_query += f"\nORDER BY {context.sort_by} {context.sort_order}"
        else:
            base_query += "\nORDER BY c.event_date ASC"
        
        # Add limit
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_ticket_sales_sql(self, context: QueryContext) -> str:
        """Generate SQL for ticket sales queries."""
        base_query = """
        SELECT 
            c.concert_id,
            a.name as artist_name,
            v.name as venue_name,
            c.event_date,
            COUNT(ts.sale_id) as total_sales,
            SUM(ts.quantity) as total_tickets_sold,
            SUM(ts.total_amount) as total_revenue,
            AVG(ts.unit_price) as avg_ticket_price
        FROM concert_dw.concerts c
        JOIN concert_dw.artists a ON c.artist_id = a.artist_id
        JOIN concert_dw.venues v ON c.venue_id = v.venue_id
        LEFT JOIN concert_dw.ticket_sales ts ON c.concert_id = ts.concert_id
        WHERE 1=1
        """
        
        conditions = []
        
        # Add filters
        if "artist_name" in context.filters:
            artist_name = context.filters["artist_name"].replace("'", "''")
            conditions.append(f"AND LOWER(a.name) LIKE LOWER('%{artist_name}%')")
        
        if "venue_name" in context.filters:
            venue_name = context.filters["venue_name"].replace("'", "''")
            conditions.append(f"AND LOWER(v.name) LIKE LOWER('%{venue_name}%')")
        
        # Add conditions to query
        for condition in conditions:
            base_query += f"\n{condition}"
        
        # Add GROUP BY
        base_query += """
        GROUP BY c.concert_id, a.name, v.name, c.event_date
        """
        
        # Add sorting
        if context.sort_by:
            base_query += f"\nORDER BY {context.sort_by} {context.sort_order}"
        else:
            base_query += "\nORDER BY total_revenue DESC"
        
        # Add limit
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_popularity_ranking_sql(self, context: QueryContext) -> str:
        """Generate SQL for popularity ranking queries."""
        # Determine what to rank based on filters
        if "artist_name" in context.filters or "genre" in context.filters:
            # Rank artists
            base_query = """
            SELECT 
                artist_id,
                name,
                genre,
                popularity_score,
                (SELECT COUNT(*) FROM concert_dw.concerts WHERE artist_id = a.artist_id) as total_concerts
            FROM concert_dw.artists a
            WHERE 1=1
            """
            
            conditions = []
            
            if "genre" in context.filters:
                genre = context.filters["genre"].replace("'", "''")
                conditions.append(f"AND LOWER(genre) LIKE LOWER('%{genre}%')")
            
            for condition in conditions:
                base_query += f"\n{condition}"
            
            base_query += "\nORDER BY popularity_score DESC"
            
        else:
            # Rank venues by popularity
            base_query = """
            SELECT 
                v.venue_id,
                v.name,
                v.city,
                v.state,
                v.capacity,
                vp.popularity_rank,
                vp.avg_attendance_rate,
                vp.revenue_per_event,
                vp.total_events
            FROM concert_dw.venues v
            LEFT JOIN concert_dw.venue_popularity vp ON v.venue_id = vp.venue_id
            WHERE vp.calculated_at = (
                SELECT MAX(calculated_at) FROM concert_dw.venue_popularity
            )
            ORDER BY vp.popularity_rank ASC
            """
        
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_revenue_analysis_sql(self, context: QueryContext) -> str:
        """Generate SQL for revenue analysis queries."""
        base_query = """
        SELECT 
            a.name as artist_name,
            COUNT(DISTINCT c.concert_id) as total_concerts,
            SUM(c.revenue) as total_revenue,
            AVG(c.revenue) as avg_revenue_per_concert,
            SUM(c.total_attendance) as total_attendance
        FROM concert_dw.concerts c
        JOIN concert_dw.artists a ON c.artist_id = a.artist_id
        WHERE c.revenue IS NOT NULL
        """
        
        conditions = []
        
        # Add filters
        if "artist_name" in context.filters:
            artist_name = context.filters["artist_name"].replace("'", "''")
            conditions.append(f"AND LOWER(a.name) LIKE LOWER('%{artist_name}%')")
        
        for condition in conditions:
            base_query += f"\n{condition}"
        
        base_query += """
        GROUP BY a.name
        ORDER BY total_revenue DESC
        """
        
        base_query += f"\nLIMIT {context.limit};"
        
        return base_query
    
    def _generate_default_sql(self, context: QueryContext) -> str:
        """Generate default SQL for unknown intents."""
        return """
        SELECT 
            'No specific query generated' as message,
            'Please provide more specific information about what you want to know' as suggestion
        FROM concert_dw.artists
        LIMIT 1;
        """
    
    def _validate_sql_safety(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query for safety and prevent SQL injection.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_safe, list of warnings)
        """
        warnings = []
        is_safe = True
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(f"Dangerous pattern detected: {pattern}")
                is_safe = False
        
        # Ensure query is read-only (SELECT only)
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith('SELECT'):
            warnings.append("Query must be a SELECT statement")
            is_safe = False
        
        # Check for multiple statements
        if sql.count(';') > 1:
            warnings.append("Multiple SQL statements not allowed")
            is_safe = False
        
        # Ensure schema is specified
        if 'concert_dw.' not in sql:
            warnings.append("Schema must be explicitly specified (concert_dw)")
            is_safe = False
        
        return is_safe, warnings
    
    def _estimate_query_complexity(self, sql: str) -> str:
        """
        Estimate query complexity based on SQL structure.
        
        Args:
            sql: SQL query
            
        Returns:
            Complexity level: low, medium, high
        """
        sql_upper = sql.upper()
        
        # Count joins
        join_count = sql_upper.count('JOIN')
        
        # Check for aggregations
        has_aggregation = any(agg in sql_upper for agg in ['SUM', 'AVG', 'COUNT', 'MAX', 'MIN'])
        
        # Check for subqueries
        has_subquery = sql_upper.count('SELECT') > 1
        
        # Determine complexity
        if join_count >= 3 or has_subquery:
            return "high"
        elif join_count >= 1 or has_aggregation:
            return "medium"
        else:
            return "low"
    
    def translate_and_execute(
        self,
        query: str,
        execute: bool = True
    ) -> QueryResult:
        """
        Translate natural language query to SQL and optionally execute it.
        
        Args:
            query: Natural language query
            execute: Whether to execute the query (default: True)
            
        Returns:
            Query result with data or error
        """
        start_time = datetime.utcnow()
        
        try:
            # Build query context
            context = self.build_query_context(query)
            
            # Generate SQL
            sql_query = self.generate_sql(context)
            
            # Check safety
            if not sql_query.is_safe:
                return QueryResult(
                    success=False,
                    query=sql_query,
                    error=f"Unsafe query: {', '.join(sql_query.safety_warnings)}"
                )
            
            # Execute if requested and Redshift service is available
            if execute and self.redshift_service:
                try:
                    data = self.redshift_service.execute_custom_query(sql_query.sql)
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    return QueryResult(
                        success=True,
                        data=data,
                        row_count=len(data),
                        query=sql_query,
                        execution_time_ms=execution_time
                    )
                    
                except Exception as e:
                    return QueryResult(
                        success=False,
                        query=sql_query,
                        error=f"Query execution failed: {str(e)}"
                    )
            
            # Return query without execution
            return QueryResult(
                success=True,
                query=sql_query,
                row_count=0
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                error=f"Query translation failed: {str(e)}"
            )
    
    def get_supported_intents(self) -> List[Dict[str, str]]:
        """
        Get list of supported query intents with examples.
        
        Returns:
            List of intent descriptions and examples
        """
        return [
            {
                "intent": QueryIntent.ARTIST_LOOKUP.value,
                "description": "Find information about artists and bands",
                "examples": [
                    "Tell me about The Beatles",
                    "Find rock artists",
                    "Show me popular musicians"
                ]
            },
            {
                "intent": QueryIntent.VENUE_SEARCH.value,
                "description": "Search for concert venues",
                "examples": [
                    "Find venues in New York",
                    "Show me large capacity arenas",
                    "What venues are in California?"
                ]
            },
            {
                "intent": QueryIntent.CONCERT_SEARCH.value,
                "description": "Search for concerts and events",
                "examples": [
                    "Show me upcoming concerts",
                    "Find concerts in Chicago",
                    "What shows are scheduled?"
                ]
            },
            {
                "intent": QueryIntent.TICKET_SALES_QUERY.value,
                "description": "Query ticket sales data",
                "examples": [
                    "How many tickets were sold?",
                    "Show me ticket sales for The Rolling Stones",
                    "What's the revenue from concerts?"
                ]
            },
            {
                "intent": QueryIntent.POPULARITY_RANKING.value,
                "description": "Get popularity rankings",
                "examples": [
                    "Show me the most popular artists",
                    "What are the top venues?",
                    "Rank artists by popularity"
                ]
            },
            {
                "intent": QueryIntent.REVENUE_ANALYSIS.value,
                "description": "Analyze revenue and financial data",
                "examples": [
                    "Show me total revenue by artist",
                    "What's the highest earning concert?",
                    "Analyze revenue trends"
                ]
            }
        ]
