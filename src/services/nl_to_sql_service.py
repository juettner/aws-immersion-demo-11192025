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
        
        # Intent classification patterns
        self.intent_patterns = {
            QueryIntent.ARTIST_LOOKUP: [
                r'\b(artist|band|musician|performer|singer)\b',
                r'\b(who is|tell me about|information about)\b.*\b(artist|band)\b',
                r'\b(find|search|show|list)\b.*\b(artist|band)\b'
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
            ],
            QueryIntent.TICKET_SALES_QUERY: [
                r'\b(ticket|sales|sold|revenue)\b',
                r'\b(how many|total)\b.*\b(ticket|sales)\b',
                r'\b(price|pricing)\b'
            ],
            QueryIntent.POPULARITY_RANKING: [
                r'\b(popular|top|best|ranking|rank)\b',
                r'\b(most|highest)\b.*\b(popular|attended)\b',
                r'\b(trending|hot)\b'
            ],
            QueryIntent.REVENUE_ANALYSIS: [
                r'\b(revenue|earnings|income|profit)\b',
                r'\b(total|sum)\b.*\b(revenue|earnings)\b',
                r'\b(financial|money)\b'
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
                entities.append(ExtractedEntity(
                    entity_type=entity_dict['entity_type'],
                    value=entity_dict['value'],
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
