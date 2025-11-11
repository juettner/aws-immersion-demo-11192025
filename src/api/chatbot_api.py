"""
FastAPI REST API for Concert AI Chatbot.

Provides HTTP endpoints for chatbot interactions, conversation management,
and session handling.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import structlog
import json
import asyncio

from src.services.chatbot_service import (
    ConcertChatbotService,
    ChatResponse,
    ConversationIntent,
    MessageRole
)
from src.services.redshift_service import RedshiftService
from src.services.venue_popularity_service import VenuePopularityService
from src.services.ticket_sales_prediction_service import TicketSalesPredictionService
from src.services.recommendation_service import RecommendationService
from src.config.settings import Settings

logger = structlog.get_logger(__name__)

# Import ML API router
try:
    from src.api import ml_api
    ML_API_AVAILABLE = True
except ImportError:
    ML_API_AVAILABLE = False
    logger.warning("ML API module not available")


# Request/Response Models

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponseModel(BaseModel):
    """Response model for chat endpoint."""
    message: str
    session_id: str
    intent: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    user_id: Optional[str] = Field(None, description="User ID")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime
    message_count: int = 0


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: str
    messages: List[Dict[str, Any]]
    total_messages: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# FastAPI Application

def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        settings: Application settings (loads from env if not provided)
        
    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = Settings.from_env()
    
    app = FastAPI(
        title="Concert AI Chatbot API",
        description="REST API for Concert AI Chatbot with natural language processing",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    redshift_service = None
    venue_service = None
    ticket_service = None
    recommendation_service = None
    
    try:
        # Initialize Redshift service if configured
        if settings.aws.redshift_cluster_id:
            redshift_service = RedshiftService(
                cluster_id=settings.aws.redshift_cluster_id,
                database=settings.aws.redshift_database,
                region=settings.aws.region
            )
            logger.info("Redshift service initialized")
        
        # Initialize ML services
        venue_service = VenuePopularityService()
        ticket_service = TicketSalesPredictionService()
        recommendation_service = RecommendationService()
        logger.info("ML services initialized")
    
    except Exception as e:
        logger.warning("Some services failed to initialize", error=str(e))
    
    # Initialize chatbot service
    chatbot_service = ConcertChatbotService(
        agent_id=None,  # Will use environment variable if set
        agent_alias_id=None,  # Will use environment variable if set
        region=settings.aws.region,
        enable_memory_persistence=True,
        redshift_service=redshift_service,
        venue_popularity_service=venue_service,
        ticket_sales_service=ticket_service,
        recommendation_service=recommendation_service
    )
    
    # Store services in app state
    app.state.chatbot_service = chatbot_service
    app.state.settings = settings
    
    # Include ML API router if available
    if ML_API_AVAILABLE:
        ml_api.initialize_ml_services(settings)
        app.include_router(ml_api.router)
        logger.info("ML API router included")
    
    logger.info("FastAPI application created successfully")
    
    return app


# Create app instance
app = create_app()


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Concert AI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and availability.
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    services_status = {
        "chatbot": "healthy",
        "memory": "healthy" if hasattr(chatbot_service, 'memory_service') and chatbot_service.memory_service else "unavailable",
        "nl_to_sql": "healthy" if hasattr(chatbot_service, 'nl_to_sql_service') and chatbot_service.nl_to_sql_service else "unavailable",
        "data_analysis": "healthy" if hasattr(chatbot_service, 'data_analysis_service') and chatbot_service.data_analysis_service else "unavailable",
        "redshift": "healthy" if hasattr(chatbot_service, 'redshift_service') and chatbot_service.redshift_service else "unavailable"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services=services_status
    )


@app.post("/chat", response_model=ChatResponseModel)
async def chat(request: ChatRequest):
    """
    Process a chat message and return response.
    
    Args:
        request: Chat request with message and optional session_id
        
    Returns:
        Chat response with message, intent, and suggestions
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = chatbot_service.create_session(user_id=request.user_id)
            logger.info("Created new session", session_id=session_id)
        
        # Process message
        response: ChatResponse = chatbot_service.process_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        # Convert to response model
        return ChatResponseModel(
            message=response.message,
            session_id=response.session_id,
            intent=response.intent.value if response.intent else None,
            confidence=response.confidence,
            data=response.data,
            suggestions=response.suggestions,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error("Error processing chat message", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Process a chat message with streaming response.
    
    Args:
        request: Chat request with message and optional session_id
        
    Returns:
        Server-sent events stream with response chunks
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    async def generate_stream():
        """Generate streaming response."""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = chatbot_service.create_session(user_id=request.user_id)
            
            # Process message (non-streaming for now, can be enhanced)
            response: ChatResponse = chatbot_service.process_message(
                message=request.message,
                session_id=session_id,
                user_id=request.user_id
            )
            
            # Simulate streaming by chunking the response
            words = response.message.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "session_id": session_id,
                    "done": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send final metadata
            final_chunk = {
                "content": "",
                "session_id": session_id,
                "intent": response.intent.value if response.intent else None,
                "data": response.data,
                "suggestions": response.suggestions,
                "done": True
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
        
        except Exception as e:
            error_chunk = {
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )


@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreateRequest):
    """
    Create a new conversation session.
    
    Args:
        request: Session creation request with optional user_id
        
    Returns:
        Session information including session_id
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    try:
        session_id = chatbot_service.create_session(user_id=request.user_id)
        
        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            created_at=datetime.utcnow(),
            message_count=0
        )
    
    except Exception as e:
        logger.error("Error creating session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get session information.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    session = chatbot_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at,
        message_count=len(session.messages)
    )


@app.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a conversation session.
    
    Args:
        session_id: Session identifier
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    success = chatbot_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return None


@app.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = None
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return
        
    Returns:
        Conversation history with messages
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    try:
        messages = chatbot_service.get_conversation_history(
            session_id=session_id,
            limit=limit
        )
        
        # Convert messages to dict format
        message_dicts = [
            {
                "message_id": msg.message_id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in messages
        ]
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=message_dicts,
            total_messages=len(message_dicts)
        )
    
    except Exception as e:
        logger.error("Error retrieving conversation history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@app.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_conversation_history(session_id: str):
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    success = chatbot_service.clear_conversation_history(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return None


@app.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str):
    """
    Get session context information.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session context data
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    session = chatbot_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return {
        "session_id": session_id,
        "context": session.context,
        "current_intent": session.current_intent.value if session.current_intent else None,
        "updated_at": session.updated_at.isoformat()
    }


@app.put("/sessions/{session_id}/context")
async def update_session_context(session_id: str, context: Dict[str, Any]):
    """
    Update session context.
    
    Args:
        session_id: Session identifier
        context: Context data to update
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    success = chatbot_service.update_session_context(session_id, context)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return {"message": "Context updated successfully"}


@app.get("/stats")
async def get_statistics():
    """
    Get chatbot service statistics.
    
    Returns:
        Statistics about active sessions and usage
    """
    chatbot_service: ConcertChatbotService = app.state.chatbot_service
    
    return chatbot_service.get_session_statistics()


# Exception Handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "chatbot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
