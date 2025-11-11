"""
Validation script for Chatbot API implementation.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def validate_imports():
    """Validate that all required modules can be imported."""
    print("Validating imports...")
    
    try:
        from api.chatbot_api import (
            app,
            create_app,
            ChatRequest,
            ChatResponseModel,
            SessionCreateRequest,
            SessionResponse,
            ConversationHistoryResponse,
            HealthResponse,
            ErrorResponse
        )
        print("✓ API module imports successful")
    except ImportError as e:
        print(f"✗ Failed to import API module: {e}")
        return False
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        print("✓ FastAPI imports successful")
    except ImportError as e:
        print(f"✗ Failed to import FastAPI: {e}")
        print("  Install with: pip install fastapi uvicorn")
        return False
    
    return True


def validate_api_structure():
    """Validate API structure and endpoints."""
    print("\nValidating API structure...")
    
    from api.chatbot_api import app
    from fastapi.testclient import TestClient
    
    # Check that app is a FastAPI instance
    from fastapi import FastAPI
    if not isinstance(app, FastAPI):
        print("✗ app is not a FastAPI instance")
        return False
    print("✓ FastAPI app instance created")
    
    # Check routes
    routes = [route.path for route in app.routes]
    required_routes = [
        "/",
        "/health",
        "/chat",
        "/chat/stream",
        "/sessions",
        "/sessions/{session_id}",
        "/history/{session_id}",
        "/sessions/{session_id}/context",
        "/stats"
    ]
    
    for route in required_routes:
        if route in routes:
            print(f"✓ Route exists: {route}")
        else:
            print(f"✗ Missing route: {route}")
            return False
    
    return True


def test_api_endpoints():
    """Test API endpoints with test client."""
    print("\nTesting API endpoints...")
    
    from api.chatbot_api import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test root endpoint
    try:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        print("✓ Root endpoint working")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False
    
    # Test health endpoint
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        print("✓ Health endpoint working")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False
    
    # Test session creation
    try:
        response = client.post("/sessions", json={"user_id": "test_user"})
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        session_id = data["session_id"]
        print(f"✓ Session creation working (ID: {session_id[:8]}...)")
    except Exception as e:
        print(f"✗ Session creation failed: {e}")
        return False
    
    # Test chat endpoint
    try:
        response = client.post(
            "/chat",
            json={
                "message": "Hello, can you help me?",
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data
        print("✓ Chat endpoint working")
    except Exception as e:
        print(f"✗ Chat endpoint failed: {e}")
        return False
    
    # Test conversation history
    try:
        response = client.get(f"/history/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "total_messages" in data
        print(f"✓ History endpoint working ({data['total_messages']} messages)")
    except Exception as e:
        print(f"✗ History endpoint failed: {e}")
        return False
    
    # Test session info
    try:
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        print("✓ Session info endpoint working")
    except Exception as e:
        print(f"✗ Session info endpoint failed: {e}")
        return False
    
    # Test statistics
    try:
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        print("✓ Statistics endpoint working")
    except Exception as e:
        print(f"✗ Statistics endpoint failed: {e}")
        return False
    
    # Test session deletion
    try:
        response = client.delete(f"/sessions/{session_id}")
        assert response.status_code == 204
        print("✓ Session deletion working")
    except Exception as e:
        print(f"✗ Session deletion failed: {e}")
        return False
    
    return True


def validate_request_models():
    """Validate request/response models."""
    print("\nValidating request/response models...")
    
    from api.chatbot_api import (
        ChatRequest,
        ChatResponseModel,
        SessionCreateRequest,
        SessionResponse,
        ConversationHistoryResponse,
        HealthResponse,
        ErrorResponse
    )
    from pydantic import ValidationError
    
    # Test ChatRequest
    try:
        request = ChatRequest(message="Test message")
        assert request.message == "Test message"
        assert request.stream is False
        print("✓ ChatRequest model valid")
    except Exception as e:
        print(f"✗ ChatRequest model failed: {e}")
        return False
    
    # Test ChatResponseModel
    try:
        response = ChatResponseModel(
            message="Test response",
            session_id="test-session",
            confidence=0.95
        )
        assert response.message == "Test response"
        assert response.confidence == 0.95
        print("✓ ChatResponseModel valid")
    except Exception as e:
        print(f"✗ ChatResponseModel failed: {e}")
        return False
    
    # Test SessionResponse
    try:
        from datetime import datetime
        session = SessionResponse(
            session_id="test-session",
            created_at=datetime.utcnow()
        )
        assert session.session_id == "test-session"
        print("✓ SessionResponse model valid")
    except Exception as e:
        print(f"✗ SessionResponse model failed: {e}")
        return False
    
    return True


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Chatbot API Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Validate imports
    if not validate_imports():
        print("\n✗ Import validation failed")
        return False
    
    # Validate API structure
    if not validate_api_structure():
        print("\n✗ API structure validation failed")
        all_passed = False
    
    # Validate request models
    if not validate_request_models():
        print("\n✗ Request model validation failed")
        all_passed = False
    
    # Test API endpoints
    if not test_api_endpoints():
        print("\n✗ API endpoint tests failed")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All validation tests passed!")
        print("\nTo start the API server:")
        print("  python src/api/chatbot_api.py")
        print("\nAPI documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("✗ Some validation tests failed")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
