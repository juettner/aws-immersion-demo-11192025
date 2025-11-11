"""
Example usage of the Concert AI Chatbot Service.

This script demonstrates how to use the ConcertChatbotService for
conversational interactions about concert data.
"""
from src.services.chatbot_service import (
    ConcertChatbotService,
    ConversationIntent,
    MessageRole
)


def example_basic_conversation():
    """Example: Basic conversation flow."""
    print("=" * 60)
    print("Example 1: Basic Conversation Flow")
    print("=" * 60)
    
    # Initialize chatbot service
    chatbot = ConcertChatbotService()
    
    # Create a new session
    session_id = chatbot.create_session(user_id="user_123")
    print(f"Created session: {session_id}\n")
    
    # Send messages and get responses
    messages = [
        "Hello! What can you help me with?",
        "Tell me about rock artists",
        "Can you recommend a concert for me?",
        "What venues are available in New York?"
    ]
    
    for message in messages:
        print(f"User: {message}")
        response = chatbot.process_message(message, session_id=session_id)
        print(f"Assistant: {response.message}")
        print(f"Intent: {response.intent}")
        print(f"Confidence: {response.confidence}")
        if response.suggestions:
            print(f"Suggestions: {', '.join(response.suggestions[:2])}")
        print()


def example_session_management():
    """Example: Session management and history."""
    print("=" * 60)
    print("Example 2: Session Management")
    print("=" * 60)
    
    chatbot = ConcertChatbotService()
    
    # Create session
    session_id = chatbot.create_session(user_id="user_456")
    
    # Have a conversation
    chatbot.process_message("Hello!", session_id=session_id)
    chatbot.process_message("Tell me about artists", session_id=session_id)
    chatbot.process_message("Recommend a concert", session_id=session_id)
    
    # Get conversation history
    history = chatbot.get_conversation_history(session_id)
    print(f"Conversation history ({len(history)} messages):")
    for msg in history:
        print(f"  [{msg.role.value}] {msg.content[:50]}...")
    print()
    
    # Get session
    session = chatbot.get_session(session_id)
    print(f"Session info:")
    print(f"  Session ID: {session.session_id}")
    print(f"  User ID: {session.user_id}")
    print(f"  Current Intent: {session.current_intent}")
    print(f"  Total Messages: {len(session.messages)}")
    print()


def example_intent_detection():
    """Example: Intent detection for different query types."""
    print("=" * 60)
    print("Example 3: Intent Detection")
    print("=" * 60)
    
    chatbot = ConcertChatbotService()
    
    test_queries = [
        "Who is performing at Madison Square Garden?",
        "Find venues in Los Angeles",
        "Recommend some concerts for me",
        "Predict ticket sales for the next show",
        "Analyze concert trends this year",
        "What's the weather like?"
    ]
    
    for query in test_queries:
        intent = chatbot.detect_intent(query)
        print(f"Query: {query}")
        print(f"Detected Intent: {intent.value}\n")


def example_context_management():
    """Example: Managing session context."""
    print("=" * 60)
    print("Example 4: Context Management")
    print("=" * 60)
    
    chatbot = ConcertChatbotService()
    session_id = chatbot.create_session(user_id="user_789")
    
    # Update session context with user preferences
    context_updates = {
        "preferred_genres": ["rock", "alternative"],
        "preferred_venues": ["venue_123", "venue_456"],
        "location": "New York, NY"
    }
    
    chatbot.update_session_context(session_id, context_updates)
    
    # Get session and check context
    session = chatbot.get_session(session_id)
    print("Session context:")
    for key, value in session.context.items():
        print(f"  {key}: {value}")
    print()
    
    # Process message with context
    response = chatbot.process_message(
        "Recommend concerts based on my preferences",
        session_id=session_id
    )
    print(f"Response: {response.message}\n")


def example_error_handling():
    """Example: Error handling and fallback responses."""
    print("=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    chatbot = ConcertChatbotService()
    
    # Try to use invalid session
    response = chatbot.process_message(
        "Hello",
        session_id="invalid_session_id"
    )
    print(f"Invalid session response:")
    print(f"  Message: {response.message}")
    print(f"  Error: {response.error}")
    print()
    
    # Get history for non-existent session
    history = chatbot.get_conversation_history("non_existent_session")
    print(f"History for non-existent session: {len(history)} messages")
    print()


def example_statistics():
    """Example: Get chatbot statistics."""
    print("=" * 60)
    print("Example 6: Chatbot Statistics")
    print("=" * 60)
    
    chatbot = ConcertChatbotService()
    
    # Create multiple sessions with conversations
    for i in range(3):
        session_id = chatbot.create_session(user_id=f"user_{i}")
        chatbot.process_message("Hello", session_id=session_id)
        chatbot.process_message("Tell me about artists", session_id=session_id)
        if i % 2 == 0:
            chatbot.process_message("Recommend a concert", session_id=session_id)
    
    # Get statistics
    stats = chatbot.get_session_statistics()
    print("Chatbot statistics:")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Avg messages per session: {stats['average_messages_per_session']:.2f}")
    print(f"  Intent distribution:")
    for intent, count in stats['intent_distribution'].items():
        print(f"    {intent}: {count}")
    print()


def example_with_bedrock_agent():
    """Example: Using with AWS Bedrock Agent (requires configuration)."""
    print("=" * 60)
    print("Example 7: Bedrock Agent Integration")
    print("=" * 60)
    
    # Initialize with Bedrock Agent configuration
    # Note: This requires actual AWS Bedrock Agent setup
    chatbot = ConcertChatbotService(
        agent_id="your-agent-id",  # Replace with actual agent ID
        agent_alias_id="your-alias-id",  # Replace with actual alias ID
        region="us-east-1"
    )
    
    session_id = chatbot.create_session(user_id="user_bedrock")
    
    # Process message - will attempt to use Bedrock Agent if configured
    response = chatbot.process_message(
        "Tell me about upcoming rock concerts",
        session_id=session_id
    )
    
    print(f"Response: {response.message}")
    print(f"Intent: {response.intent}")
    print()
    
    print("Note: Bedrock Agent integration requires:")
    print("  1. AWS Bedrock Agent created and deployed")
    print("  2. Proper IAM permissions")
    print("  3. Agent ID and Alias ID configured")
    print("  4. If not configured, service falls back to intent handlers")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Concert AI Chatbot Service - Usage Examples")
    print("=" * 60 + "\n")
    
    try:
        example_basic_conversation()
        example_session_management()
        example_intent_detection()
        example_context_management()
        example_error_handling()
        example_statistics()
        example_with_bedrock_agent()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
