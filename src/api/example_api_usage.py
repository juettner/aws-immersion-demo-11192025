"""
Example usage of Concert AI Chatbot API.

Demonstrates how to interact with the REST API endpoints.
"""
import requests
import json
from typing import Dict, Any


class ChatbotAPIClient:
    """Client for interacting with the Chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip("/")
        self.session_id = None
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_session(self, user_id: str = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        payload = {}
        if user_id:
            payload["user_id"] = user_id
        
        response = requests.post(
            f"{self.base_url}/sessions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id
    
    def send_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Send a message to the chatbot.
        
        Args:
            message: User message
            session_id: Optional session ID (uses stored if not provided)
            user_id: Optional user ID
            
        Returns:
            Chat response
        """
        payload = {"message": message}
        
        if session_id:
            payload["session_id"] = session_id
        elif self.session_id:
            payload["session_id"] = self.session_id
        
        if user_id:
            payload["user_id"] = user_id
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_conversation_history(
        self,
        session_id: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Get conversation history.
        
        Args:
            session_id: Session ID (uses stored if not provided)
            limit: Maximum number of messages
            
        Returns:
            Conversation history
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        params = {}
        if limit:
            params["limit"] = limit
        
        response = requests.get(
            f"{self.base_url}/history/{sid}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_session_info(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get session information.
        
        Args:
            session_id: Session ID (uses stored if not provided)
            
        Returns:
            Session information
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        response = requests.get(f"{self.base_url}/sessions/{sid}")
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: str = None) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session ID (uses stored if not provided)
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided or stored")
        
        response = requests.delete(f"{self.base_url}/sessions/{sid}")
        response.raise_for_status()
        
        if sid == self.session_id:
            self.session_id = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get chatbot statistics."""
        response = requests.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()


def main():
    """Demonstrate API usage."""
    print("=== Concert AI Chatbot API Demo ===\n")
    
    # Initialize client
    client = ChatbotAPIClient()
    
    # Check health
    print("1. Checking API health...")
    try:
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Services: {health['services']}")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the API server is running: python src/api/chatbot_api.py")
        return
    print()
    
    # Create session
    print("2. Creating conversation session...")
    try:
        session_id = client.create_session(user_id="demo_user")
        print(f"   Session ID: {session_id}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    print()
    
    # Send messages
    print("3. Sending messages to chatbot...")
    
    messages = [
        "Hello! Can you help me find concerts?",
        "What are the most popular venues?",
        "Tell me about upcoming concerts in New York",
        "What's the predicted ticket sales for Taylor Swift concerts?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n   Message {i}: {message}")
        try:
            response = client.send_message(message)
            print(f"   Response: {response['message'][:200]}...")
            print(f"   Intent: {response.get('intent', 'N/A')}")
            print(f"   Confidence: {response.get('confidence', 0):.2f}")
            if response.get('suggestions'):
                print(f"   Suggestions: {', '.join(response['suggestions'][:3])}")
        except Exception as e:
            print(f"   Error: {e}")
    print()
    
    # Get conversation history
    print("4. Retrieving conversation history...")
    try:
        history = client.get_conversation_history(limit=10)
        print(f"   Total messages: {history['total_messages']}")
        print(f"   Last 3 messages:")
        for msg in history['messages'][-3:]:
            print(f"     - [{msg['role']}]: {msg['content'][:80]}...")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Get session info
    print("5. Getting session information...")
    try:
        session_info = client.get_session_info()
        print(f"   Session ID: {session_info['session_id']}")
        print(f"   User ID: {session_info.get('user_id', 'N/A')}")
        print(f"   Message count: {session_info['message_count']}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Get statistics
    print("6. Getting chatbot statistics...")
    try:
        stats = client.get_statistics()
        print(f"   Active sessions: {stats.get('active_sessions', 0)}")
        print(f"   Total messages: {stats.get('total_messages', 0)}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Clean up
    print("7. Cleaning up session...")
    try:
        client.delete_session()
        print("   Session deleted successfully")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    print("Demo completed!")
    print("\nAPI Documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
