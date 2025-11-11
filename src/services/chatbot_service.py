"""
Concert AI Chatbot Service using AWS Bedrock Agent Runtime.

This service provides conversational AI capabilities for querying concert data,
generating recommendations, and providing insights through natural language.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.services.conversation_memory_service import ConversationMemoryService
from src.services.nl_to_sql_service import NLToSQLService
from src.services.data_analysis_service import DataAnalysisService


class MessageRole(str, Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationIntent(str, Enum):
    """Detected user intent categories."""
    ARTIST_LOOKUP = "artist_lookup"
    VENUE_SEARCH = "venue_search"
    CONCERT_RECOMMENDATION = "concert_recommendation"
    TICKET_PREDICTION = "ticket_prediction"
    DATA_ANALYSIS = "data_analysis"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"


class ChatMessage(BaseModel):
    """Individual chat message."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Conversation state tracking."""
    session_id: str
    user_id: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    current_intent: Optional[ConversationIntent] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    """Response from chatbot."""
    message: str
    session_id: str
    intent: Optional[ConversationIntent] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ConcertChatbotService:
    """
    Concert AI Chatbot Service with Bedrock Agent Runtime integration.
    
    Provides:
    - Natural language conversation interface
    - Session management and state tracking
    - Intent detection and routing
    - Error handling and fallback responses
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_alias_id: Optional[str] = None,
        region: Optional[str] = None,
        enable_memory_persistence: bool = True,
        redshift_service: Optional[Any] = None,
        venue_popularity_service: Optional[Any] = None,
        ticket_sales_service: Optional[Any] = None,
        recommendation_service: Optional[Any] = None
    ):
        """
        Initialize the chatbot service.
        
        Args:
            agent_id: AWS Bedrock Agent ID (optional, uses env if not provided)
            agent_alias_id: Agent alias ID (optional, uses env if not provided)
            region: AWS region (optional, uses settings if not provided)
            enable_memory_persistence: Enable DynamoDB persistence (default: True)
            redshift_service: Optional RedshiftService for data queries
            venue_popularity_service: Optional VenuePopularityService for predictions
            ticket_sales_service: Optional TicketSalesPredictionService for predictions
            recommendation_service: Optional RecommendationService for recommendations
        """
        self.region = region or settings.aws.region
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.enable_memory_persistence = enable_memory_persistence
        
        # Initialize Bedrock Agent Runtime client
        try:
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock Agent Runtime client: {e}")
            self.bedrock_agent_runtime = None
        
        # Initialize conversation memory service for persistence
        if self.enable_memory_persistence:
            try:
                self.memory_service = ConversationMemoryService(region=self.region)
            except Exception as e:
                print(f"Warning: Could not initialize memory service: {e}")
                self.memory_service = None
        else:
            self.memory_service = None
        
        # Initialize NL to SQL service for data queries
        try:
            self.nl_to_sql_service = NLToSQLService(
                redshift_service=redshift_service,
                region=self.region
            )
        except Exception as e:
            print(f"Warning: Could not initialize NL to SQL service: {e}")
            self.nl_to_sql_service = None
        
        # Initialize data analysis service for analytical insights
        try:
            self.data_analysis_service = DataAnalysisService(
                redshift_service=redshift_service,
                venue_popularity_service=venue_popularity_service,
                ticket_sales_service=ticket_sales_service,
                recommendation_service=recommendation_service
            )
        except Exception as e:
            print(f"Warning: Could not initialize data analysis service: {e}")
            self.data_analysis_service = None
        
        # In-memory session storage (for active sessions and fallback)
        self.sessions: Dict[str, ConversationState] = {}
        
        # Intent detection patterns (simple keyword-based for now)
        self.intent_patterns = {
            ConversationIntent.ARTIST_LOOKUP: [
                "artist", "band", "musician", "performer", "who is"
            ],
            ConversationIntent.VENUE_SEARCH: [
                "venue", "location", "place", "where", "arena", "theater"
            ],
            ConversationIntent.CONCERT_RECOMMENDATION: [
                "recommend", "suggest", "should i", "what concert", "upcoming"
            ],
            ConversationIntent.TICKET_PREDICTION: [
                "ticket", "sales", "predict", "forecast", "how many"
            ],
            ConversationIntent.DATA_ANALYSIS: [
                "analyze", "trend", "statistics", "data", "insights"
            ]
        }
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationState(
            session_id=session_id,
            user_id=user_id
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """
        Retrieve conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation state or None if not found
        """
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def detect_intent(self, message: str) -> ConversationIntent:
        """
        Detect user intent from message content.
        
        Args:
            message: User message text
            
        Returns:
            Detected intent
        """
        message_lower = message.lower()
        
        # Check each intent pattern
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        # Default to general query
        return ConversationIntent.GENERAL_QUERY
    
    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Process a user message and generate response.
        
        Args:
            message: User message text
            session_id: Optional session ID (creates new if not provided)
            user_id: Optional user identifier
            
        Returns:
            Chat response with assistant message
        """
        # Create or retrieve session
        if session_id is None:
            session_id = self.create_session(user_id)
        
        session = self.get_session(session_id)
        if session is None:
            return ChatResponse(
                message="Session not found. Please start a new conversation.",
                session_id=session_id,
                error="SESSION_NOT_FOUND"
            )
        
        try:
            # Detect intent
            intent = self.detect_intent(message)
            session.current_intent = intent
            
            # Add user message to session
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=message
            )
            session.messages.append(user_message)
            session.updated_at = datetime.utcnow()
            
            # Store user message in persistent memory
            if self.memory_service:
                self.memory_service.store_conversation_message(
                    session_id=session_id,
                    message_id=user_message.message_id,
                    role=user_message.role.value,
                    content=user_message.content,
                    user_id=session.user_id,
                    metadata=user_message.metadata,
                    timestamp=user_message.timestamp
                )
            
            # Get context for context-aware response generation
            context = self._get_response_context(session_id, session.user_id)
            
            # Route to appropriate handler
            response = self._route_intent(message, intent, session, context)
            
            # Add assistant response to session
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response.message,
                metadata={
                    "intent": intent.value,
                    "confidence": response.confidence
                }
            )
            session.messages.append(assistant_message)
            session.updated_at = datetime.utcnow()
            
            # Store assistant message in persistent memory
            if self.memory_service:
                self.memory_service.store_conversation_message(
                    session_id=session_id,
                    message_id=assistant_message.message_id,
                    role=assistant_message.role.value,
                    content=assistant_message.content,
                    user_id=session.user_id,
                    metadata=assistant_message.metadata,
                    timestamp=assistant_message.timestamp
                )
            
            return response
            
        except Exception as e:
            return self._handle_error(e, session_id)
    
    def _get_response_context(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get context for generating context-aware responses.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            Dictionary with conversation context
        """
        if self.memory_service:
            return self.memory_service.get_context_for_response(
                session_id=session_id,
                user_id=user_id,
                message_limit=10
            )
        return {}
    
    def _route_intent(
        self,
        message: str,
        intent: ConversationIntent,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Route message to appropriate handler based on intent.
        
        Args:
            message: User message
            intent: Detected intent
            session: Conversation session
            context: Optional conversation context for context-aware responses
            
        Returns:
            Chat response
        """
        # Try Bedrock Agent Runtime if available
        if self.bedrock_agent_runtime and self.agent_id and self.agent_alias_id:
            try:
                return self._invoke_bedrock_agent(message, session, context)
            except Exception as e:
                print(f"Bedrock Agent invocation failed: {e}")
                # Fall through to fallback handlers
        
        # Fallback to intent-specific handlers
        if intent == ConversationIntent.ARTIST_LOOKUP:
            return self._handle_artist_lookup(message, session, context)
        elif intent == ConversationIntent.VENUE_SEARCH:
            return self._handle_venue_search(message, session, context)
        elif intent == ConversationIntent.CONCERT_RECOMMENDATION:
            return self._handle_concert_recommendation(message, session, context)
        elif intent == ConversationIntent.TICKET_PREDICTION:
            return self._handle_ticket_prediction(message, session, context)
        elif intent == ConversationIntent.DATA_ANALYSIS:
            return self._handle_data_analysis(message, session, context)
        else:
            return self._handle_general_query(message, session, context)
    
    def _invoke_bedrock_agent(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Invoke AWS Bedrock Agent Runtime.
        
        Args:
            message: User message
            session: Conversation session
            
        Returns:
            Chat response from Bedrock Agent
        """
        try:
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session.session_id,
                inputText=message
            )
            
            # Parse response from event stream
            response_text = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            return ChatResponse(
                message=response_text or "I processed your request.",
                session_id=session.session_id,
                intent=session.current_intent,
                confidence=0.9
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise Exception(f"Bedrock Agent not found: {self.agent_id}")
            elif error_code == 'AccessDeniedException':
                raise Exception("Access denied to Bedrock Agent")
            else:
                raise Exception(f"Bedrock Agent error: {error_code}")
    
    def _handle_artist_lookup(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle artist lookup queries."""
        # Try to use NL to SQL service for data queries
        if self.nl_to_sql_service:
            try:
                result = self.nl_to_sql_service.translate_and_execute(message, execute=True)
                
                if result.success and result.data:
                    # Format response with data
                    response_message = f"I found {result.row_count} artist(s):\n\n"
                    
                    for i, artist in enumerate(result.data[:5], 1):
                        name = artist.get('name', 'Unknown')
                        genre = artist.get('genre', 'N/A')
                        popularity = artist.get('popularity_score', 0)
                        response_message += f"{i}. {name} - Genre: {genre}, Popularity: {popularity}\n"
                    
                    if result.row_count > 5:
                        response_message += f"\n... and {result.row_count - 5} more artists."
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.ARTIST_LOOKUP,
                        confidence=0.9,
                        data={"artists": result.data, "query": result.query.sql if result.query else None}
                    )
            except Exception as e:
                print(f"NL to SQL query failed: {e}")
        
        # Fallback response
        response_message = "I can help you find information about artists. "
        
        if context and context.get('user_preferences'):
            prefs = context['user_preferences'].get('preferences', {})
            if prefs.get('favorite_genres'):
                genres = ', '.join(prefs['favorite_genres'][:3])
                response_message += f"Based on your interest in {genres}, "
        
        response_message += "Try asking about specific artists or genres."
        
        return ChatResponse(
            message=response_message,
            session_id=session.session_id,
            intent=ConversationIntent.ARTIST_LOOKUP,
            confidence=0.8,
            suggestions=[
                "Tell me about popular rock artists",
                "Which artists are performing this month?",
                "Show me artist details"
            ]
        )
    
    def _handle_venue_search(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle venue search queries."""
        # Try to use NL to SQL service for data queries
        if self.nl_to_sql_service:
            try:
                result = self.nl_to_sql_service.translate_and_execute(message, execute=True)
                
                if result.success and result.data:
                    # Format response with data
                    response_message = f"I found {result.row_count} venue(s):\n\n"
                    
                    for i, venue in enumerate(result.data[:5], 1):
                        name = venue.get('name', 'Unknown')
                        city = venue.get('city', 'N/A')
                        capacity = venue.get('capacity', 0)
                        venue_type = venue.get('venue_type', 'N/A')
                        response_message += f"{i}. {name} - {city}, Capacity: {capacity}, Type: {venue_type}\n"
                    
                    if result.row_count > 5:
                        response_message += f"\n... and {result.row_count - 5} more venues."
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.VENUE_SEARCH,
                        confidence=0.9,
                        data={"venues": result.data, "query": result.query.sql if result.query else None}
                    )
            except Exception as e:
                print(f"NL to SQL query failed: {e}")
        
        # Fallback response
        response_message = "I can help you search for concert venues. "
        
        if context and context.get('user_preferences'):
            prefs = context['user_preferences'].get('preferences', {})
            if prefs.get('location_preference'):
                location = prefs['location_preference']
                response_message += f"I see you're interested in venues near {location}. "
        
        response_message += "Try asking about venues in specific cities or with certain capacities."
        
        return ChatResponse(
            message=response_message,
            session_id=session.session_id,
            intent=ConversationIntent.VENUE_SEARCH,
            confidence=0.8,
            suggestions=[
                "Find venues in New York",
                "Show me large capacity venues",
                "What venues are available?"
            ]
        )
    
    def _handle_concert_recommendation(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle concert recommendation queries."""
        # Use context to provide personalized response
        response_message = "I can recommend concerts based on your preferences. "
        
        if context and context.get('user_preferences'):
            prefs = context['user_preferences'].get('preferences', {})
            personalization_parts = []
            
            if prefs.get('favorite_genres'):
                genres = ', '.join(prefs['favorite_genres'][:2])
                personalization_parts.append(f"your love for {genres}")
            
            if prefs.get('preferred_artists'):
                artists = ', '.join(prefs['preferred_artists'][:2])
                personalization_parts.append(f"your interest in {artists}")
            
            if personalization_parts:
                response_message += f"I'll consider {' and '.join(personalization_parts)}. "
        
        response_message += "This feature will be integrated with the recommendation engine in upcoming tasks."
        
        return ChatResponse(
            message=response_message,
            session_id=session.session_id,
            intent=ConversationIntent.CONCERT_RECOMMENDATION,
            confidence=0.8,
            suggestions=[
                "Recommend concerts for me",
                "What concerts should I attend?",
                "Show me upcoming rock concerts"
            ]
        )
    
    def _handle_ticket_prediction(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle ticket sales prediction queries."""
        return ChatResponse(
            message="I can predict ticket sales for concerts. "
                   "This feature will be integrated with the ML prediction service in upcoming tasks.",
            session_id=session.session_id,
            intent=ConversationIntent.TICKET_PREDICTION,
            confidence=0.8,
            suggestions=[
                "Predict ticket sales for upcoming concerts",
                "How many tickets will sell?",
                "Show me sales forecasts"
            ]
        )
    
    def _handle_data_analysis(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle data analysis queries with dynamic insights generation."""
        message_lower = message.lower()
        
        # Use data analysis service if available
        if self.data_analysis_service:
            try:
                # Detect analysis type from message
                if any(word in message_lower for word in ["trend", "over time", "growth", "change"]):
                    # Trend analysis
                    result = self.data_analysis_service.analyze_concert_trends(
                        time_period="last_year",
                        metric="attendance",
                        group_by="month"
                    )
                    response_message = self.data_analysis_service.format_for_chatbot(result)
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.DATA_ANALYSIS,
                        confidence=0.9,
                        data={
                            "analysis_type": result.analysis_type.value,
                            "visualization": result.visualization,
                            "insights": result.insights
                        }
                    )
                
                elif any(word in message_lower for word in ["compare", "versus", "vs", "difference"]):
                    # Comparison analysis - would need entity extraction
                    response_message = "I can compare artists or venues for you. Please specify which entities you'd like to compare."
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.DATA_ANALYSIS,
                        confidence=0.7,
                        suggestions=[
                            "Compare artist_001 and artist_002",
                            "Compare venues in New York",
                            "Show me artist statistics"
                        ]
                    )
                
                elif any(word in message_lower for word in ["statistics", "summary", "overview", "stats"]):
                    # Statistical summary
                    entity_type = "concert"
                    if "artist" in message_lower:
                        entity_type = "artist"
                    elif "venue" in message_lower:
                        entity_type = "venue"
                    
                    result = self.data_analysis_service.generate_statistical_summary(
                        entity_type=entity_type
                    )
                    response_message = self.data_analysis_service.format_for_chatbot(result)
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.DATA_ANALYSIS,
                        confidence=0.9,
                        data={
                            "analysis_type": result.analysis_type.value,
                            "statistics": result.data.get("statistics", {}),
                            "visualization": result.visualization
                        }
                    )
                
            except Exception as e:
                print(f"Data analysis service failed: {e}")
                # Fall through to NL to SQL fallback
        
        # Try to use NL to SQL service for data queries
        if self.nl_to_sql_service:
            try:
                result = self.nl_to_sql_service.translate_and_execute(message, execute=True)
                
                if result.success and result.data:
                    # Format response with data
                    response_message = f"Here's the analysis based on your query:\n\n"
                    
                    # Show first few rows of data
                    for i, row in enumerate(result.data[:5], 1):
                        row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                        response_message += f"{i}. {row_str}\n"
                    
                    if result.row_count > 5:
                        response_message += f"\n... and {result.row_count - 5} more results."
                    
                    response_message += f"\n\nQuery executed in {result.execution_time_ms:.2f}ms"
                    
                    return ChatResponse(
                        message=response_message,
                        session_id=session.session_id,
                        intent=ConversationIntent.DATA_ANALYSIS,
                        confidence=0.9,
                        data={"results": result.data, "query": result.query.sql if result.query else None}
                    )
            except Exception as e:
                print(f"NL to SQL query failed: {e}")
        
        # Fallback response
        return ChatResponse(
            message="I can analyze concert data and provide insights. "
                   "Try asking about trends, statistics, or comparisons.",
            session_id=session.session_id,
            intent=ConversationIntent.DATA_ANALYSIS,
            confidence=0.8,
            suggestions=[
                "Analyze concert trends",
                "Show me venue statistics",
                "What are the top performing artists?"
            ]
        )
    
    def _handle_general_query(
        self,
        message: str,
        session: ConversationState,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Handle general queries."""
        # Check if this is a returning user with conversation history
        greeting = "I'm your Concert AI assistant."
        
        if context and context.get('conversation_summary'):
            summary = context['conversation_summary']
            if summary.get('message_count', 0) > 0:
                greeting = "Welcome back! I'm your Concert AI assistant."
        
        return ChatResponse(
            message=f"{greeting} I can help you with:\n"
                   "- Finding information about artists and venues\n"
                   "- Recommending concerts based on your preferences\n"
                   "- Predicting ticket sales\n"
                   "- Analyzing concert data and trends\n\n"
                   "What would you like to know?",
            session_id=session.session_id,
            intent=ConversationIntent.GENERAL_QUERY,
            confidence=1.0,
            suggestions=[
                "Tell me about artists",
                "Recommend a concert",
                "Analyze concert trends",
                "Search for venues"
            ]
        )
    
    def _handle_error(self, error: Exception, session_id: str) -> ChatResponse:
        """
        Handle errors and provide fallback response.
        
        Args:
            error: Exception that occurred
            session_id: Session identifier
            
        Returns:
            Error response
        """
        error_message = str(error)
        
        # Log error (in production, use proper logging)
        print(f"Chatbot error: {error_message}")
        
        return ChatResponse(
            message="I apologize, but I encountered an error processing your request. "
                   "Please try rephrasing your question or ask something else.",
            session_id=session_id,
            error=error_message,
            confidence=0.0,
            suggestions=[
                "Start a new conversation",
                "Ask a different question",
                "Get help"
            ]
        )
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        from_memory: bool = True
    ) -> List[ChatMessage]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return
            from_memory: If True, retrieve from DynamoDB; otherwise use in-memory session
            
        Returns:
            List of chat messages
        """
        # Try to get from persistent memory first
        if from_memory and self.memory_service:
            stored_messages = self.memory_service.retrieve_conversation_history(
                session_id=session_id,
                limit=limit
            )
            
            if stored_messages:
                # Convert stored messages to ChatMessage objects
                chat_messages = []
                for msg in stored_messages:
                    chat_messages.append(ChatMessage(
                        message_id=msg['message_id'],
                        role=MessageRole(msg['role']),
                        content=msg['content'],
                        timestamp=datetime.fromisoformat(msg['timestamp']),
                        metadata=msg.get('metadata', {})
                    ))
                return chat_messages
        
        # Fallback to in-memory session
        session = self.get_session(session_id)
        if session is None:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def clear_conversation_history(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.messages = []
        session.context = {}
        session.current_intent = None
        session.updated_at = datetime.utcnow()
        return True
    
    def update_session_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session context with additional information.
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
            
        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.context.update(context_updates)
        session.updated_at = datetime.utcnow()
        return True
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about active sessions.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self.sessions)
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        
        intent_counts = {}
        for session in self.sessions.values():
            if session.current_intent:
                intent = session.current_intent.value
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        stats = {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": (
                total_messages / total_sessions if total_sessions > 0 else 0
            ),
            "intent_distribution": intent_counts
        }
        
        # Add memory service statistics if available
        if self.memory_service:
            memory_stats = self.memory_service.get_memory_statistics()
            stats["memory_service"] = memory_stats
        
        return stats
    
    def store_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Store user preferences for personalized responses.
        
        Args:
            user_id: User identifier
            preferences: Dictionary of user preferences
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.memory_service:
            print("Warning: Memory service not available, cannot store preferences")
            return False
        
        return self.memory_service.store_user_preferences(user_id, preferences)
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of user preferences or None if not found
        """
        if not self.memory_service:
            print("Warning: Memory service not available, cannot retrieve preferences")
            return None
        
        return self.memory_service.retrieve_user_preferences(user_id)
    
    def update_user_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any
    ) -> bool:
        """
        Update a specific user preference.
        
        Args:
            user_id: User identifier
            preference_key: Preference key to update
            preference_value: New preference value
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.memory_service:
            print("Warning: Memory service not available, cannot update preference")
            return False
        
        return self.memory_service.update_user_preference(
            user_id, preference_key, preference_value
        )
    
    def load_session_from_memory(self, session_id: str) -> Optional[ConversationState]:
        """
        Load a session from persistent memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation state or None if not found
        """
        if not self.memory_service:
            return None
        
        # Retrieve conversation history from memory
        stored_messages = self.memory_service.retrieve_conversation_history(
            session_id=session_id
        )
        
        if not stored_messages:
            return None
        
        # Reconstruct session from stored messages
        messages = []
        user_id = None
        
        for msg in stored_messages:
            messages.append(ChatMessage(
                message_id=msg['message_id'],
                role=MessageRole(msg['role']),
                content=msg['content'],
                timestamp=datetime.fromisoformat(msg['timestamp']),
                metadata=msg.get('metadata', {})
            ))
            
            if not user_id and 'user_id' in msg:
                user_id = msg['user_id']
        
        # Create session state
        session = ConversationState(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            created_at=datetime.fromisoformat(stored_messages[0]['timestamp']) if stored_messages else datetime.utcnow(),
            updated_at=datetime.fromisoformat(stored_messages[-1]['timestamp']) if stored_messages else datetime.utcnow()
        )
        
        # Store in active sessions
        self.sessions[session_id] = session
        
        return session
