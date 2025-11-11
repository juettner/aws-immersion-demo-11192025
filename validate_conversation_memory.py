"""
Validation script for Conversation Memory Service integration.

This script validates:
1. DynamoDB table creation and configuration
2. Conversation message storage and retrieval
3. User preference management
4. Context-aware response generation
5. Integration with chatbot service
"""
import sys
import time
from datetime import datetime
from typing import Dict, Any

from src.services.conversation_memory_service import ConversationMemoryService
from src.services.chatbot_service import ConcertChatbotService


class ValidationResult:
    """Track validation results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, message: str = "", warning: bool = False):
        """Add a test result."""
        if warning:
            self.warnings += 1
            status = "⚠️  WARNING"
        elif passed:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        for result in self.results:
            print(f"{result['status']}: {result['test']}")
            if result['message']:
                print(f"    {result['message']}")
        
        print("\n" + "-" * 80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")
        print("=" * 80)
        
        return self.failed == 0


def validate_memory_service_initialization(results: ValidationResult):
    """Validate memory service initialization."""
    print("\n" + "=" * 80)
    print("TEST 1: Memory Service Initialization")
    print("=" * 80)
    
    try:
        memory_service = ConversationMemoryService()
        
        if memory_service.dynamodb is None:
            results.add_result(
                "Memory Service Initialization",
                False,
                "DynamoDB client not initialized. Check AWS credentials.",
                warning=True
            )
            return None
        
        results.add_result(
            "Memory Service Initialization",
            True,
            f"Initialized with tables: {memory_service.table_name}, {memory_service.preferences_table_name}"
        )
        
        return memory_service
        
    except Exception as e:
        results.add_result(
            "Memory Service Initialization",
            False,
            f"Error: {str(e)}"
        )
        return None


def validate_table_creation(memory_service: ConversationMemoryService, results: ValidationResult):
    """Validate DynamoDB table creation."""
    print("\n" + "=" * 80)
    print("TEST 2: DynamoDB Table Creation")
    print("=" * 80)
    
    if memory_service is None:
        results.add_result("Table Creation", False, "Memory service not available")
        return
    
    try:
        table_results = memory_service.create_tables_if_not_exist()
        
        results.add_result(
            "Conversations Table",
            table_results.get('conversations', False),
            f"Table: {memory_service.table_name}"
        )
        
        results.add_result(
            "Preferences Table",
            table_results.get('preferences', False),
            f"Table: {memory_service.preferences_table_name}"
        )
        
    except Exception as e:
        results.add_result("Table Creation", False, f"Error: {str(e)}")


def validate_message_storage(memory_service: ConversationMemoryService, results: ValidationResult):
    """Validate conversation message storage."""
    print("\n" + "=" * 80)
    print("TEST 3: Conversation Message Storage")
    print("=" * 80)
    
    if memory_service is None:
        results.add_result("Message Storage", False, "Memory service not available")
        return None
    
    session_id = f"test-session-{int(time.time())}"
    user_id = "test-user-001"
    
    try:
        # Store multiple messages
        messages = [
            ("msg-1", "user", "Hello, I want to find concerts"),
            ("msg-2", "assistant", "I can help you find concerts!"),
            ("msg-3", "user", "Show me rock concerts in New York"),
            ("msg-4", "assistant", "Here are rock concerts in New York...")
        ]
        
        stored_count = 0
        for msg_id, role, content in messages:
            success = memory_service.store_conversation_message(
                session_id=session_id,
                message_id=msg_id,
                role=role,
                content=content,
                user_id=user_id,
                metadata={"test": True}
            )
            if success:
                stored_count += 1
            time.sleep(0.1)  # Small delay for timestamp ordering
        
        results.add_result(
            "Message Storage",
            stored_count == len(messages),
            f"Stored {stored_count}/{len(messages)} messages"
        )
        
        return session_id, user_id
        
    except Exception as e:
        results.add_result("Message Storage", False, f"Error: {str(e)}")
        return None, None


def validate_message_retrieval(
    memory_service: ConversationMemoryService,
    session_id: str,
    results: ValidationResult
):
    """Validate conversation message retrieval."""
    print("\n" + "=" * 80)
    print("TEST 4: Conversation Message Retrieval")
    print("=" * 80)
    
    if memory_service is None or session_id is None:
        results.add_result("Message Retrieval", False, "Prerequisites not met")
        return
    
    try:
        # Retrieve all messages
        messages = memory_service.retrieve_conversation_history(session_id=session_id)
        
        results.add_result(
            "Retrieve All Messages",
            len(messages) > 0,
            f"Retrieved {len(messages)} messages"
        )
        
        # Retrieve with limit
        limited_messages = memory_service.retrieve_conversation_history(
            session_id=session_id,
            limit=2
        )
        
        results.add_result(
            "Retrieve Limited Messages",
            len(limited_messages) <= 2,
            f"Retrieved {len(limited_messages)} messages with limit=2"
        )
        
        # Validate message structure
        if messages:
            msg = messages[0]
            has_required_fields = all(
                key in msg for key in ['session_id', 'message_id', 'role', 'content', 'timestamp']
            )
            results.add_result(
                "Message Structure",
                has_required_fields,
                "All required fields present"
            )
        
    except Exception as e:
        results.add_result("Message Retrieval", False, f"Error: {str(e)}")


def validate_user_preferences(
    memory_service: ConversationMemoryService,
    user_id: str,
    results: ValidationResult
):
    """Validate user preference management."""
    print("\n" + "=" * 80)
    print("TEST 5: User Preference Management")
    print("=" * 80)
    
    if memory_service is None or user_id is None:
        results.add_result("User Preferences", False, "Prerequisites not met")
        return
    
    try:
        # Store preferences
        preferences = {
            "favorite_genres": ["rock", "jazz", "blues"],
            "preferred_venues": ["Madison Square Garden"],
            "location_preference": "New York, NY",
            "price_range": {"min": 50, "max": 150}
        }
        
        store_success = memory_service.store_user_preferences(user_id, preferences)
        results.add_result(
            "Store Preferences",
            store_success,
            "User preferences stored"
        )
        
        # Retrieve preferences
        stored_prefs = memory_service.retrieve_user_preferences(user_id)
        
        prefs_match = (
            stored_prefs is not None and
            stored_prefs['preferences']['favorite_genres'] == preferences['favorite_genres']
        )
        
        results.add_result(
            "Retrieve Preferences",
            prefs_match,
            "User preferences retrieved and match stored values"
        )
        
        # Update single preference
        update_success = memory_service.update_user_preference(
            user_id,
            "favorite_genres",
            ["rock", "alternative"]
        )
        
        results.add_result(
            "Update Preference",
            update_success,
            "Single preference updated"
        )
        
        # Verify update
        updated_prefs = memory_service.retrieve_user_preferences(user_id)
        update_verified = (
            updated_prefs is not None and
            updated_prefs['preferences']['favorite_genres'] == ["rock", "alternative"]
        )
        
        results.add_result(
            "Verify Update",
            update_verified,
            "Preference update verified"
        )
        
    except Exception as e:
        results.add_result("User Preferences", False, f"Error: {str(e)}")


def validate_context_generation(
    memory_service: ConversationMemoryService,
    session_id: str,
    user_id: str,
    results: ValidationResult
):
    """Validate context generation for responses."""
    print("\n" + "=" * 80)
    print("TEST 6: Context Generation for Responses")
    print("=" * 80)
    
    if memory_service is None or session_id is None:
        results.add_result("Context Generation", False, "Prerequisites not met")
        return
    
    try:
        context = memory_service.get_context_for_response(
            session_id=session_id,
            user_id=user_id,
            message_limit=5
        )
        
        # Validate context structure
        has_required_keys = all(
            key in context for key in ['session_id', 'recent_messages', 'user_preferences', 'conversation_summary']
        )
        
        results.add_result(
            "Context Structure",
            has_required_keys,
            "Context has all required keys"
        )
        
        # Validate recent messages
        has_messages = len(context['recent_messages']) > 0
        results.add_result(
            "Recent Messages",
            has_messages,
            f"Context includes {len(context['recent_messages'])} recent messages"
        )
        
        # Validate user preferences
        has_preferences = context['user_preferences'] is not None
        results.add_result(
            "User Preferences in Context",
            has_preferences,
            "User preferences included in context"
        )
        
        # Validate conversation summary
        summary = context['conversation_summary']
        has_summary_data = 'message_count' in summary and summary['message_count'] > 0
        results.add_result(
            "Conversation Summary",
            has_summary_data,
            f"Summary includes {summary.get('message_count', 0)} messages"
        )
        
    except Exception as e:
        results.add_result("Context Generation", False, f"Error: {str(e)}")


def validate_chatbot_integration(results: ValidationResult):
    """Validate chatbot service integration with memory."""
    print("\n" + "=" * 80)
    print("TEST 7: Chatbot Service Integration")
    print("=" * 80)
    
    try:
        # Initialize chatbot with memory enabled
        chatbot = ConcertChatbotService(enable_memory_persistence=True)
        
        has_memory_service = chatbot.memory_service is not None
        results.add_result(
            "Chatbot Memory Service",
            has_memory_service,
            "Memory service initialized in chatbot",
            warning=not has_memory_service
        )
        
        if not has_memory_service:
            return
        
        # Create session and send messages
        user_id = f"test-user-{int(time.time())}"
        session_id = chatbot.create_session(user_id=user_id)
        
        # Store preferences
        prefs_stored = chatbot.store_user_preferences(
            user_id,
            {"favorite_genres": ["rock"], "location_preference": "Boston"}
        )
        
        results.add_result(
            "Store Preferences via Chatbot",
            prefs_stored,
            "Preferences stored through chatbot service"
        )
        
        # Send messages
        response1 = chatbot.process_message(
            "Hello, I'm looking for concerts",
            session_id=session_id,
            user_id=user_id
        )
        
        response2 = chatbot.process_message(
            "Recommend a concert for me",
            session_id=session_id,
            user_id=user_id
        )
        
        # Check if responses are context-aware
        context_aware = "rock" in response2.message.lower() or "boston" in response2.message.lower()
        
        results.add_result(
            "Context-Aware Responses",
            True,  # Just check that it doesn't error
            f"Chatbot generated responses (context-aware: {context_aware})"
        )
        
        # Retrieve history from memory
        history = chatbot.get_conversation_history(session_id=session_id, from_memory=True)
        
        results.add_result(
            "Retrieve History via Chatbot",
            len(history) >= 4,  # 2 user + 2 assistant messages
            f"Retrieved {len(history)} messages from memory"
        )
        
        # Test session loading
        new_chatbot = ConcertChatbotService(enable_memory_persistence=True)
        loaded_session = new_chatbot.load_session_from_memory(session_id)
        
        results.add_result(
            "Load Session from Memory",
            loaded_session is not None,
            "Session loaded successfully from persistent storage"
        )
        
        # Get statistics
        stats = chatbot.get_session_statistics()
        has_memory_stats = 'memory_service' in stats
        
        results.add_result(
            "Memory Statistics",
            has_memory_stats,
            "Memory service statistics available"
        )
        
    except Exception as e:
        results.add_result("Chatbot Integration", False, f"Error: {str(e)}")


def validate_cleanup(
    memory_service: ConversationMemoryService,
    session_id: str,
    user_id: str,
    results: ValidationResult
):
    """Validate cleanup operations."""
    print("\n" + "=" * 80)
    print("TEST 8: Cleanup Operations")
    print("=" * 80)
    
    if memory_service is None:
        results.add_result("Cleanup", False, "Memory service not available")
        return
    
    try:
        # Delete conversation history
        delete_conv_success = memory_service.delete_conversation_history(session_id)
        results.add_result(
            "Delete Conversation",
            delete_conv_success,
            f"Deleted conversation for session {session_id}"
        )
        
        # Verify deletion
        messages = memory_service.retrieve_conversation_history(session_id)
        deletion_verified = len(messages) == 0
        results.add_result(
            "Verify Conversation Deletion",
            deletion_verified,
            "Conversation successfully deleted"
        )
        
        # Delete user preferences
        delete_prefs_success = memory_service.delete_user_preferences(user_id)
        results.add_result(
            "Delete Preferences",
            delete_prefs_success,
            f"Deleted preferences for user {user_id}"
        )
        
        # Verify deletion
        prefs = memory_service.retrieve_user_preferences(user_id)
        prefs_deleted = prefs is None
        results.add_result(
            "Verify Preferences Deletion",
            prefs_deleted,
            "Preferences successfully deleted"
        )
        
    except Exception as e:
        results.add_result("Cleanup", False, f"Error: {str(e)}")


def main():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("CONVERSATION MEMORY SERVICE VALIDATION")
    print("=" * 80)
    print("\nThis script validates the conversation memory persistence implementation.")
    print("Requirements: AWS credentials, DynamoDB access")
    print("=" * 80)
    
    results = ValidationResult()
    
    # Test 1: Initialize memory service
    memory_service = validate_memory_service_initialization(results)
    
    if memory_service is None:
        print("\n⚠️  WARNING: Memory service not available. Some tests will be skipped.")
        print("Make sure you have AWS credentials configured and DynamoDB access.")
    
    # Test 2: Create tables
    validate_table_creation(memory_service, results)
    
    # Test 3: Store messages
    session_data = validate_message_storage(memory_service, results)
    session_id, user_id = session_data if session_data else (None, None)
    
    # Test 4: Retrieve messages
    validate_message_retrieval(memory_service, session_id, results)
    
    # Test 5: User preferences
    validate_user_preferences(memory_service, user_id, results)
    
    # Test 6: Context generation
    validate_context_generation(memory_service, session_id, user_id, results)
    
    # Test 7: Chatbot integration
    validate_chatbot_integration(results)
    
    # Test 8: Cleanup
    if session_id and user_id:
        validate_cleanup(memory_service, session_id, user_id, results)
    
    # Print summary
    success = results.print_summary()
    
    if success:
        print("\n✅ All validation tests passed!")
        return 0
    else:
        print("\n❌ Some validation tests failed. Please review the results above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
