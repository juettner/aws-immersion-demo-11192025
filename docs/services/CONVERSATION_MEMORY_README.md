# Conversation Memory Service

## Overview

The Conversation Memory Service provides persistent storage for chatbot conversations using AWS DynamoDB. This enables:

- **Persistent Conversation History**: Store and retrieve conversation messages across sessions
- **User Preference Tracking**: Maintain user preferences for personalized responses
- **Context-Aware Responses**: Generate responses based on conversation history and user preferences
- **Multi-Session Support**: Track conversations across multiple sessions for the same user

## Architecture

### DynamoDB Tables

#### 1. Conversations Table (`concert-chatbot-conversations`)

Stores individual conversation messages with the following schema:

- **Primary Key**: 
  - `session_id` (HASH): Unique session identifier
  - `timestamp` (RANGE): ISO 8601 timestamp
- **Attributes**:
  - `message_id`: Unique message identifier
  - `role`: Message role (user, assistant, system)
  - `content`: Message content
  - `user_id`: Optional user identifier
  - `metadata`: JSON-encoded metadata
- **Global Secondary Index**:
  - `UserIdIndex`: Query all conversations for a user
    - `user_id` (HASH)
    - `timestamp` (RANGE)

#### 2. Preferences Table (`concert-chatbot-preferences`)

Stores user preferences with the following schema:

- **Primary Key**:
  - `user_id` (HASH): Unique user identifier
- **Attributes**:
  - `preferences`: JSON-encoded user preferences
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

## Usage

### Basic Usage

```python
from src.services.conversation_memory_service import ConversationMemoryService

# Initialize the service
memory_service = ConversationMemoryService()

# Create tables (if they don't exist)
memory_service.create_tables_if_not_exist()

# Store a conversation message
memory_service.store_conversation_message(
    session_id="session-123",
    message_id="msg-1",
    role="user",
    content="Hello, I'm looking for concerts",
    user_id="user-456",
    metadata={"intent": "general_query"}
)

# Retrieve conversation history
history = memory_service.retrieve_conversation_history(
    session_id="session-123",
    limit=10
)

# Store user preferences
preferences = {
    "favorite_genres": ["rock", "jazz"],
    "location_preference": "New York, NY"
}
memory_service.store_user_preferences("user-456", preferences)

# Get context for response generation
context = memory_service.get_context_for_response(
    session_id="session-123",
    user_id="user-456",
    message_limit=10
)
```

### Integration with Chatbot Service

```python
from src.services.chatbot_service import ConcertChatbotService

# Initialize chatbot with memory persistence enabled
chatbot = ConcertChatbotService(enable_memory_persistence=True)

# Create a session
session_id = chatbot.create_session(user_id="user-789")

# Store user preferences
chatbot.store_user_preferences("user-789", {
    "favorite_genres": ["blues", "soul"],
    "preferred_venues": ["Blue Note", "Apollo Theater"]
})

# Process messages (automatically stored in DynamoDB)
response = chatbot.process_message(
    message="Recommend a concert for me",
    session_id=session_id,
    user_id="user-789"
)

# Retrieve conversation history from persistent storage
history = chatbot.get_conversation_history(
    session_id=session_id,
    from_memory=True
)

# Load a session from memory in a new chatbot instance
new_chatbot = ConcertChatbotService(enable_memory_persistence=True)
loaded_session = new_chatbot.load_session_from_memory(session_id)
```

## Context-Aware Response Generation

The memory service provides context for generating personalized responses:

```python
context = memory_service.get_context_for_response(
    session_id="session-123",
    user_id="user-456",
    message_limit=10
)

# Context includes:
# - recent_messages: Last N messages from the conversation
# - user_preferences: User's stored preferences
# - conversation_summary: Statistics about the conversation
```

The chatbot service uses this context to:

1. **Personalize greetings**: Welcome back returning users
2. **Reference preferences**: Mention user's favorite genres or locations
3. **Maintain conversation flow**: Use previous messages for context
4. **Provide relevant suggestions**: Based on user history

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# AWS DynamoDB Configuration
AWS_DYNAMODB_CONVERSATIONS_TABLE=concert-chatbot-conversations
AWS_DYNAMODB_PREFERENCES_TABLE=concert-chatbot-preferences
AWS_REGION=us-east-1
```

### Settings

The service uses the application settings from `src/config/settings.py`:

```python
from src.config.settings import settings

# Access DynamoDB configuration
table_name = settings.aws.dynamodb_conversations_table
preferences_table = settings.aws.dynamodb_preferences_table
region = settings.aws.region
```

## API Reference

### ConversationMemoryService

#### Methods

##### `create_tables_if_not_exist() -> Dict[str, bool]`
Create DynamoDB tables if they don't exist.

##### `store_conversation_message(...) -> bool`
Store a conversation message in DynamoDB.

##### `retrieve_conversation_history(session_id, limit=None, start_time=None, end_time=None) -> List[Dict]`
Retrieve conversation history for a session.

##### `retrieve_user_conversations(user_id, limit=None) -> List[Dict]`
Retrieve all conversations for a user across sessions.

##### `delete_conversation_history(session_id) -> bool`
Delete all messages for a conversation session.

##### `store_user_preferences(user_id, preferences) -> bool`
Store or update user preferences.

##### `retrieve_user_preferences(user_id) -> Optional[Dict]`
Retrieve user preferences.

##### `update_user_preference(user_id, preference_key, preference_value) -> bool`
Update a specific user preference.

##### `delete_user_preferences(user_id) -> bool`
Delete user preferences.

##### `get_context_for_response(session_id, user_id=None, message_limit=10) -> Dict`
Get conversation context for generating context-aware responses.

##### `get_memory_statistics() -> Dict`
Get statistics about stored conversations and preferences.

### ConcertChatbotService (Memory Integration)

#### New Methods

##### `store_user_preferences(user_id, preferences) -> bool`
Store user preferences through the chatbot service.

##### `get_user_preferences(user_id) -> Optional[Dict]`
Retrieve user preferences through the chatbot service.

##### `update_user_preference(user_id, preference_key, preference_value) -> bool`
Update a specific user preference through the chatbot service.

##### `load_session_from_memory(session_id) -> Optional[ConversationState]`
Load a session from persistent memory.

##### `get_conversation_history(session_id, limit=None, from_memory=True) -> List[ChatMessage]`
Get conversation history with option to retrieve from DynamoDB.

## Examples

See the following files for detailed examples:

- `src/services/example_conversation_memory_usage.py`: Comprehensive examples of memory service usage
- `validate_conversation_memory.py`: Validation script demonstrating all features

## Testing

Run the validation script to test the implementation:

```bash
python validate_conversation_memory.py
```

This will:
1. Initialize the memory service
2. Create DynamoDB tables
3. Test message storage and retrieval
4. Test user preference management
5. Test context generation
6. Test chatbot integration
7. Test cleanup operations

## AWS Permissions Required

The service requires the following AWS IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable",
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DeleteItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/concert-chatbot-conversations",
        "arn:aws:dynamodb:*:*:table/concert-chatbot-conversations/index/*",
        "arn:aws:dynamodb:*:*:table/concert-chatbot-preferences"
      ]
    }
  ]
}
```

## Performance Considerations

### Read/Write Capacity

The tables are created with provisioned throughput:
- **Read Capacity Units**: 5
- **Write Capacity Units**: 5

For production use, consider:
- Using **On-Demand** billing mode for variable workloads
- Increasing provisioned capacity for high-traffic applications
- Implementing caching for frequently accessed data

### Query Optimization

- Use `limit` parameter to reduce data transfer
- Use time range filters for large conversation histories
- Cache user preferences in memory for active sessions
- Use batch operations for bulk message storage

## Troubleshooting

### ResourceNotFoundException

If you see "Requested resource not found" errors:
1. Tables may still be creating (wait 30-60 seconds)
2. Check AWS credentials are configured correctly
3. Verify table names match configuration
4. Ensure IAM permissions are correct

### Access Denied

If you see "AccessDeniedException":
1. Check IAM user/role has required DynamoDB permissions
2. Verify AWS credentials are valid
3. Check resource ARNs in IAM policy

### Table Already Exists

If table creation fails with "ResourceInUseException":
- This is normal - the table already exists
- The service will use the existing table

## Future Enhancements

Potential improvements for the conversation memory service:

1. **Time-to-Live (TTL)**: Automatically expire old conversations
2. **Encryption**: Enable encryption at rest for sensitive data
3. **Backup**: Implement automated backups
4. **Analytics**: Track conversation patterns and user behavior
5. **Search**: Add full-text search capabilities
6. **Compression**: Compress large conversation histories
7. **Streaming**: Real-time conversation updates via DynamoDB Streams

## Related Documentation

- [Chatbot Service Documentation](./chatbot_service.py)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [AgentCore Memory Service](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-memory.html)
