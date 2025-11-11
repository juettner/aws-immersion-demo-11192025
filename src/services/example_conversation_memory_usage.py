"""
Example usage of Conversation Memory Service with DynamoDB persistence.

This script demonstrates:
- Creating DynamoDB tables for conversation storage
- Storing and retrieving conversation history
- Managing user preferences across sessions
- Context-aware response generation
"""
import time
from datetime import datetime
from src.services.conversation_memory_service import ConversationMemoryService
from src.services.chatbot_service import ConcertChatbotService


def example_memory_service_basic():
    """Basic conversation memory service operations."""
    print("=" * 80)
    print("Example 1: Basic Conversation Memory Service Operations")
    print("=" * 80)
    
    # Initialize memory service
    memory_service = ConversationMemoryService()
    
    # Create tables if they don't exist
    print("\n1. Creating DynamoDB tables...")
    result = memory_service.create_tables_if_not_exist()
    print(f"   Conversations table: {'✓' if result['conversations'] else '✗'}")
    print(f"   Preferences table: {'✓' if result['preferences'] else '✗'}")
    
    # Store conversation messages
    print("\n2. Storing conversation messages...")
    session_id = "test-session-001"
    user_id = "user-123"
    
    messages = [
        ("msg-1", "user", "Hello, I'm looking for rock concerts in New York"),
        ("msg-2", "assistant", "I can help you find rock concerts in New York! Let me search for upcoming events."),
        ("msg-3", "user", "What about venues with capacity over 5000?"),
        ("msg-4", "assistant", "I'll filter for large venues with capacity over 5000 people.")
    ]
    
    for msg_id, role, content in messages:
        success = memory_service.store_conversation_message(
            session_id=session_id,
            message_id=msg_id,
            role=role,
            content=content,
            user_id=user_id,
            metadata={"example": True}
        )
        print(f"   Stored message {msg_id}: {'✓' if success else '✗'}")
        time.sleep(0.1)  # Small delay to ensure timestamp ordering
    
    # Retrieve conversation history
    print("\n3. Retrieving conversation history...")
    history = memory_service.retrieve_conversation_history(session_id=session_id)
    print(f"   Retrieved {len(history)} messages:")
    for msg in history:
        print(f"   - [{msg['role']}] {msg['content'][:50]}...")
    
    # Store user preferences
    print("\n4. Storing user preferences...")
    preferences = {
        "favorite_genres": ["rock", "alternative", "indie"],
        "preferred_venues": ["Madison Square Garden", "Barclays Center"],
        "location_preference": "New York, NY",
        "price_range": {"min": 50, "max": 200}
    }
    
    success = memory_service.store_user_preferences(user_id, preferences)
    print(f"   Stored preferences: {'✓' if success else '✗'}")
    
    # Retrieve user preferences
    print("\n5. Retrieving user preferences...")
    stored_prefs = memory_service.retrieve_user_preferences(user_id)
    if stored_prefs:
        print(f"   User ID: {stored_prefs['user_id']}")
        print(f"   Favorite genres: {stored_prefs['preferences']['favorite_genres']}")
        print(f"   Location: {stored_prefs['preferences']['location_preference']}")
    
    # Get context for response generation
    print("\n6. Getting context for response generation...")
    context = memory_service.get_context_for_response(
        session_id=session_id,
        user_id=user_id,
        message_limit=5
    )
    print(f"   Session ID: {context['session_id']}")
    print(f"   Recent messages: {len(context['recent_messages'])}")
    print(f"   User preferences available: {context['user_preferences'] is not None}")
    print(f"   Conversation summary:")
    for key, value in context['conversation_summary'].items():
        print(f"     - {key}: {value}")
    
    # Get memory statistics
    print("\n7. Memory service statistics...")
    stats = memory_service.get_memory_statistics()
    print(f"   Conversations table: {stats['conversations_table']}")
    print(f"   Preferences table: {stats['preferences_table']}")
    print(f"   DynamoDB available: {stats['dynamodb_available']}")
    if 'total_messages' in stats:
        print(f"   Total messages stored: {stats['total_messages']}")
    if 'total_users_with_preferences' in stats:
        print(f"   Total users with preferences: {stats['total_users_with_preferences']}")


def example_chatbot_with_memory():
    """Chatbot service with conversation memory integration."""
    print("\n" + "=" * 80)
    print("Example 2: Chatbot Service with Conversation Memory")
    print("=" * 80)
    
    # Initialize chatbot with memory persistence enabled
    chatbot = ConcertChatbotService(enable_memory_persistence=True)
    
    # Create a new session
    print("\n1. Creating new conversation session...")
    user_id = "user-456"
    session_id = chatbot.create_session(user_id=user_id)
    print(f"   Session ID: {session_id}")
    
    # Store user preferences
    print("\n2. Setting user preferences...")
    preferences = {
        "favorite_genres": ["jazz", "blues"],
        "preferred_artists": ["Miles Davis", "B.B. King"],
        "location_preference": "Chicago, IL"
    }
    chatbot.store_user_preferences(user_id, preferences)
    print("   Preferences stored ✓")
    
    # Have a conversation
    print("\n3. Having a conversation...")
    messages = [
        "Hello! I'm looking for concert recommendations.",
        "What jazz concerts are coming up?",
        "Tell me about venues in Chicago."
    ]
    
    for user_message in messages:
        print(f"\n   User: {user_message}")
        response = chatbot.process_message(
            message=user_message,
            session_id=session_id,
            user_id=user_id
        )
        print(f"   Assistant: {response.message[:100]}...")
        print(f"   Intent: {response.intent.value if response.intent else 'None'}")
        print(f"   Confidence: {response.confidence}")
    
    # Retrieve conversation history from memory
    print("\n4. Retrieving conversation history from memory...")
    history = chatbot.get_conversation_history(session_id=session_id, from_memory=True)
    print(f"   Retrieved {len(history)} messages from persistent storage")
    
    # Simulate loading session from memory in a new chatbot instance
    print("\n5. Loading session from memory in new chatbot instance...")
    new_chatbot = ConcertChatbotService(enable_memory_persistence=True)
    loaded_session = new_chatbot.load_session_from_memory(session_id)
    
    if loaded_session:
        print(f"   Session loaded successfully ✓")
        print(f"   Session ID: {loaded_session.session_id}")
        print(f"   User ID: {loaded_session.user_id}")
        print(f"   Messages in session: {len(loaded_session.messages)}")
        print(f"   Created at: {loaded_session.created_at}")
        print(f"   Updated at: {loaded_session.updated_at}")
    else:
        print("   Failed to load session ✗")
    
    # Continue conversation with loaded session
    print("\n6. Continuing conversation with loaded session...")
    response = new_chatbot.process_message(
        message="Can you recommend a concert based on my preferences?",
        session_id=session_id,
        user_id=user_id
    )
    print(f"   Assistant: {response.message[:150]}...")
    
    # Get session statistics
    print("\n7. Session statistics...")
    stats = new_chatbot.get_session_statistics()
    print(f"   Active sessions: {stats['total_sessions']}")
    print(f"   Total messages: {stats['total_messages']}")
    if 'memory_service' in stats:
        print(f"   Memory service available: ✓")


def example_multi_session_tracking():
    """Track conversations across multiple sessions for a user."""
    print("\n" + "=" * 80)
    print("Example 3: Multi-Session User Tracking")
    print("=" * 80)
    
    memory_service = ConversationMemoryService()
    user_id = "user-789"
    
    # Create multiple sessions for the same user
    print("\n1. Creating multiple conversation sessions...")
    sessions = []
    for i in range(3):
        session_id = f"session-{user_id}-{i+1}"
        sessions.append(session_id)
        
        # Store some messages in each session
        memory_service.store_conversation_message(
            session_id=session_id,
            message_id=f"msg-{i}-1",
            role="user",
            content=f"This is session {i+1}",
            user_id=user_id
        )
        time.sleep(0.1)
        
        memory_service.store_conversation_message(
            session_id=session_id,
            message_id=f"msg-{i}-2",
            role="assistant",
            content=f"Welcome to session {i+1}!",
            user_id=user_id
        )
        time.sleep(0.1)
        
        print(f"   Created session: {session_id}")
    
    # Retrieve all conversations for the user
    print("\n2. Retrieving all user conversations...")
    all_messages = memory_service.retrieve_user_conversations(user_id=user_id)
    print(f"   Retrieved {len(all_messages)} messages across all sessions")
    
    # Group by session
    sessions_dict = {}
    for msg in all_messages:
        sid = msg['session_id']
        if sid not in sessions_dict:
            sessions_dict[sid] = []
        sessions_dict[sid].append(msg)
    
    print(f"   Messages grouped into {len(sessions_dict)} sessions:")
    for sid, msgs in sessions_dict.items():
        print(f"     - {sid}: {len(msgs)} messages")
    
    # Update user preferences based on conversation history
    print("\n3. Updating user preferences...")
    memory_service.update_user_preference(
        user_id=user_id,
        preference_key="favorite_genres",
        preference_value=["electronic", "techno", "house"]
    )
    print("   Updated favorite genres ✓")
    
    # Retrieve updated preferences
    prefs = memory_service.retrieve_user_preferences(user_id)
    if prefs:
        print(f"   Current preferences: {prefs['preferences']}")


def example_cleanup():
    """Clean up test data."""
    print("\n" + "=" * 80)
    print("Example 4: Cleanup Operations")
    print("=" * 80)
    
    memory_service = ConversationMemoryService()
    
    # Delete specific conversation
    print("\n1. Deleting specific conversation...")
    session_id = "test-session-001"
    success = memory_service.delete_conversation_history(session_id)
    print(f"   Deleted session {session_id}: {'✓' if success else '✗'}")
    
    # Delete user preferences
    print("\n2. Deleting user preferences...")
    user_ids = ["user-123", "user-456", "user-789"]
    for user_id in user_ids:
        success = memory_service.delete_user_preferences(user_id)
        print(f"   Deleted preferences for {user_id}: {'✓' if success else '✗'}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CONVERSATION MEMORY SERVICE EXAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate conversation memory persistence with DynamoDB.")
    print("Note: Requires AWS credentials and DynamoDB access.")
    print("=" * 80)
    
    try:
        # Run examples
        example_memory_service_basic()
        example_chatbot_with_memory()
        example_multi_session_tracking()
        
        # Uncomment to clean up test data
        # example_cleanup()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. AWS credentials configured")
        print("2. DynamoDB access permissions")
        print("3. Required Python packages installed")
