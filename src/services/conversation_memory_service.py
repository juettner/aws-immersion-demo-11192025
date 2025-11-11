"""
Conversation Memory Service using AWS DynamoDB.

This service provides persistent storage for conversation history,
user preferences, and session context across chatbot interactions.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from src.config.settings import settings


class UserPreferences(BaseModel):
    """User preferences stored across sessions."""
    user_id: str
    favorite_genres: List[str] = Field(default_factory=list)
    preferred_venues: List[str] = Field(default_factory=list)
    preferred_artists: List[str] = Field(default_factory=list)
    location_preference: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMemoryService:
    """
    Conversation Memory Service with DynamoDB persistence.
    
    Provides:
    - Persistent conversation history storage
    - User preference tracking across sessions
    - Session context management
    - Context-aware response generation support
    """
    
    def __init__(
        self,
        table_name: Optional[str] = None,
        preferences_table_name: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize the conversation memory service.
        
        Args:
            table_name: DynamoDB table name for conversations (default: from settings)
            preferences_table_name: DynamoDB table name for user preferences (default: from settings)
            region: AWS region (optional, uses settings if not provided)
        """
        self.region = region or settings.aws.region
        self.table_name = table_name or settings.aws.dynamodb_conversations_table
        self.preferences_table_name = preferences_table_name or settings.aws.dynamodb_preferences_table
        
        # Initialize DynamoDB client
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.conversations_table = self.dynamodb.Table(self.table_name)
            self.preferences_table = self.dynamodb.Table(self.preferences_table_name)
        except Exception as e:
            print(f"Warning: Could not initialize DynamoDB client: {e}")
            self.dynamodb = None
            self.conversations_table = None
            self.preferences_table = None
    
    def create_tables_if_not_exist(self) -> Dict[str, bool]:
        """
        Create DynamoDB tables if they don't exist.
        
        Returns:
            Dictionary with table creation status
        """
        if not self.dynamodb:
            return {"conversations": False, "preferences": False}
        
        results = {}
        
        # Create conversations table
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'UserIdIndex',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            results["conversations"] = True
            print(f"Created conversations table: {self.table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                results["conversations"] = True  # Table already exists
            else:
                results["conversations"] = False
                print(f"Error creating conversations table: {e}")
        
        # Create preferences table
        try:
            self.dynamodb.create_table(
                TableName=self.preferences_table_name,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            results["preferences"] = True
            print(f"Created preferences table: {self.preferences_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                results["preferences"] = True  # Table already exists
            else:
                results["preferences"] = False
                print(f"Error creating preferences table: {e}")
        
        return results
    
    def store_conversation_message(
        self,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Store a conversation message in DynamoDB.
        
        Args:
            session_id: Session identifier
            message_id: Unique message identifier
            role: Message role (user, assistant, system)
            content: Message content
            user_id: Optional user identifier
            metadata: Optional message metadata
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.conversations_table:
            print("Warning: DynamoDB not initialized, cannot store message")
            return False
        
        try:
            timestamp_str = (timestamp or datetime.utcnow()).isoformat()
            
            item = {
                'session_id': session_id,
                'timestamp': timestamp_str,
                'message_id': message_id,
                'role': role,
                'content': content,
                'metadata': json.dumps(metadata or {})
            }
            
            if user_id:
                item['user_id'] = user_id
            
            self.conversations_table.put_item(Item=item)
            return True
            
        except ClientError as e:
            print(f"Error storing conversation message: {e}")
            return False
    
    def retrieve_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of conversation messages
        """
        if not self.conversations_table:
            print("Warning: DynamoDB not initialized, cannot retrieve history")
            return []
        
        try:
            # Build query parameters
            query_params = {
                'KeyConditionExpression': 'session_id = :session_id',
                'ExpressionAttributeValues': {
                    ':session_id': session_id
                },
                'ScanIndexForward': True  # Sort by timestamp ascending
            }
            
            # Add time range filter if provided
            if start_time or end_time:
                conditions = []
                if start_time:
                    conditions.append('timestamp >= :start_time')
                    query_params['ExpressionAttributeValues'][':start_time'] = start_time.isoformat()
                if end_time:
                    conditions.append('timestamp <= :end_time')
                    query_params['ExpressionAttributeValues'][':end_time'] = end_time.isoformat()
                
                if conditions:
                    query_params['KeyConditionExpression'] += ' AND ' + ' AND '.join(conditions)
            
            if limit:
                query_params['Limit'] = limit
            
            response = self.conversations_table.query(**query_params)
            
            # Parse and return messages
            messages = []
            for item in response.get('Items', []):
                message = {
                    'session_id': item['session_id'],
                    'message_id': item['message_id'],
                    'role': item['role'],
                    'content': item['content'],
                    'timestamp': item['timestamp'],
                    'metadata': json.loads(item.get('metadata', '{}'))
                }
                if 'user_id' in item:
                    message['user_id'] = item['user_id']
                messages.append(message)
            
            return messages
            
        except ClientError as e:
            print(f"Error retrieving conversation history: {e}")
            return []
    
    def retrieve_user_conversations(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of conversation messages across all sessions
        """
        if not self.conversations_table:
            print("Warning: DynamoDB not initialized, cannot retrieve user conversations")
            return []
        
        try:
            query_params = {
                'IndexName': 'UserIdIndex',
                'KeyConditionExpression': 'user_id = :user_id',
                'ExpressionAttributeValues': {
                    ':user_id': user_id
                },
                'ScanIndexForward': False  # Sort by timestamp descending (most recent first)
            }
            
            if limit:
                query_params['Limit'] = limit
            
            response = self.conversations_table.query(**query_params)
            
            # Parse and return messages
            messages = []
            for item in response.get('Items', []):
                message = {
                    'session_id': item['session_id'],
                    'message_id': item['message_id'],
                    'role': item['role'],
                    'content': item['content'],
                    'timestamp': item['timestamp'],
                    'user_id': item['user_id'],
                    'metadata': json.loads(item.get('metadata', '{}'))
                }
                messages.append(message)
            
            return messages
            
        except ClientError as e:
            print(f"Error retrieving user conversations: {e}")
            return []
    
    def delete_conversation_history(self, session_id: str) -> bool:
        """
        Delete all messages for a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.conversations_table:
            print("Warning: DynamoDB not initialized, cannot delete history")
            return False
        
        try:
            # Query all messages for the session
            response = self.conversations_table.query(
                KeyConditionExpression='session_id = :session_id',
                ExpressionAttributeValues={':session_id': session_id}
            )
            
            # Delete each message
            with self.conversations_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'session_id': item['session_id'],
                            'timestamp': item['timestamp']
                        }
                    )
            
            return True
            
        except ClientError as e:
            print(f"Error deleting conversation history: {e}")
            return False
    
    def store_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Store or update user preferences.
        
        Args:
            user_id: User identifier
            preferences: Dictionary of user preferences
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.preferences_table:
            print("Warning: DynamoDB not initialized, cannot store preferences")
            return False
        
        try:
            now = datetime.utcnow().isoformat()
            
            item = {
                'user_id': user_id,
                'preferences': json.dumps(preferences),
                'updated_at': now
            }
            
            # Check if preferences exist
            try:
                existing = self.preferences_table.get_item(Key={'user_id': user_id})
                if 'Item' not in existing:
                    item['created_at'] = now
            except:
                item['created_at'] = now
            
            self.preferences_table.put_item(Item=item)
            return True
            
        except ClientError as e:
            print(f"Error storing user preferences: {e}")
            return False
    
    def retrieve_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of user preferences or None if not found
        """
        if not self.preferences_table:
            print("Warning: DynamoDB not initialized, cannot retrieve preferences")
            return None
        
        try:
            response = self.preferences_table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                item = response['Item']
                return {
                    'user_id': item['user_id'],
                    'preferences': json.loads(item.get('preferences', '{}')),
                    'created_at': item.get('created_at'),
                    'updated_at': item.get('updated_at')
                }
            
            return None
            
        except ClientError as e:
            print(f"Error retrieving user preferences: {e}")
            return None
    
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
        # Retrieve existing preferences
        user_prefs = self.retrieve_user_preferences(user_id)
        
        if user_prefs is None:
            # Create new preferences
            preferences = {preference_key: preference_value}
        else:
            # Update existing preferences
            preferences = user_prefs.get('preferences', {})
            preferences[preference_key] = preference_value
        
        return self.store_user_preferences(user_id, preferences)
    
    def delete_user_preferences(self, user_id: str) -> bool:
        """
        Delete user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.preferences_table:
            print("Warning: DynamoDB not initialized, cannot delete preferences")
            return False
        
        try:
            self.preferences_table.delete_item(Key={'user_id': user_id})
            return True
            
        except ClientError as e:
            print(f"Error deleting user preferences: {e}")
            return False
    
    def get_context_for_response(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        message_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get conversation context for generating context-aware responses.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            message_limit: Number of recent messages to include
            
        Returns:
            Dictionary with conversation context including history and preferences
        """
        context = {
            'session_id': session_id,
            'recent_messages': [],
            'user_preferences': None,
            'conversation_summary': {}
        }
        
        # Get recent conversation history
        messages = self.retrieve_conversation_history(
            session_id=session_id,
            limit=message_limit
        )
        context['recent_messages'] = messages
        
        # Get user preferences if user_id provided
        if user_id:
            preferences = self.retrieve_user_preferences(user_id)
            context['user_preferences'] = preferences
        
        # Generate conversation summary
        if messages:
            context['conversation_summary'] = {
                'message_count': len(messages),
                'first_message_time': messages[0].get('timestamp') if messages else None,
                'last_message_time': messages[-1].get('timestamp') if messages else None,
                'user_message_count': sum(1 for m in messages if m.get('role') == 'user'),
                'assistant_message_count': sum(1 for m in messages if m.get('role') == 'assistant')
            }
        
        return context
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored conversations and preferences.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            'conversations_table': self.table_name,
            'preferences_table': self.preferences_table_name,
            'dynamodb_available': self.dynamodb is not None
        }
        
        if not self.dynamodb:
            return stats
        
        try:
            # Get conversations table info
            conv_table = self.dynamodb.Table(self.table_name)
            conv_response = conv_table.scan(Select='COUNT')
            stats['total_messages'] = conv_response.get('Count', 0)
            
            # Get preferences table info
            pref_table = self.dynamodb.Table(self.preferences_table_name)
            pref_response = pref_table.scan(Select='COUNT')
            stats['total_users_with_preferences'] = pref_response.get('Count', 0)
            
        except ClientError as e:
            print(f"Error getting memory statistics: {e}")
            stats['error'] = str(e)
        
        return stats
