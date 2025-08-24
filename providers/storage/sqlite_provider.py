"""
SQLite Storage Provider
Implements storage interface for conversation and data persistence.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.interfaces.storage_provider import IStorageProvider
from core.models.conversation import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)

class SQLiteProvider(IStorageProvider):
    """SQLite storage provider for conversation persistence."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "data/assistant.db"
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self, connection_string: Optional[str] = None) -> bool:
        """Connect to SQLite database."""
        try:
            db_path = connection_string or self.db_path
            
            # Create directory if it doesn't exist
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # Initialize tables
            self._initialize_tables()
            
            logger.info(f"Connected to SQLite database: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from database."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from database: {e}")
            return False
    
    def _initialize_tables(self):
        """Initialize database tables."""
        cursor = self.connection.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        self.connection.commit()
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """Save a conversation to storage."""
        try:
            cursor = self.connection.cursor()
            
            # Save conversation
            cursor.execute('''
                INSERT OR REPLACE INTO conversations 
                (id, title, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                conversation.id,
                conversation.title,
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat() if conversation.updated_at else None,
                json.dumps(conversation.metadata or {})
            ))
            
            # Delete existing messages
            cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation.id,))
            
            # Save messages
            for message in conversation.messages:
                cursor.execute('''
                    INSERT INTO messages 
                    (id, conversation_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    message.id,
                    conversation.id,
                    message.role.value,
                    message.content,
                    message.timestamp.isoformat(),
                    json.dumps(message.metadata or {})
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation.id}: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from storage."""
        try:
            cursor = self.connection.cursor()
            
            # Load conversation
            cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
            conv_row = cursor.fetchone()
            
            if not conv_row:
                return None
            
            # Load messages
            cursor.execute('''
                SELECT * FROM messages WHERE conversation_id = ? 
                ORDER BY timestamp
            ''', (conversation_id,))
            message_rows = cursor.fetchall()
            
            # Create conversation object
            conversation = Conversation(
                id=conv_row['id'],
                title=conv_row['title'],
                created_at=datetime.fromisoformat(conv_row['created_at']),
                updated_at=datetime.fromisoformat(conv_row['updated_at']) if conv_row['updated_at'] else None,
                metadata=json.loads(conv_row['metadata']) if conv_row['metadata'] else {}
            )
            
            # Add messages
            for msg_row in message_rows:
                message = Message(
                    id=msg_row['id'],
                    role=MessageRole(msg_row['role']),
                    content=msg_row['content'],
                    timestamp=datetime.fromisoformat(msg_row['timestamp']),
                    metadata=json.loads(msg_row['metadata']) if msg_row['metadata'] else {}
                )
                conversation.add_message(message)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
                FROM conversations 
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append({
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'message_count': row['message_count']
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
            cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def save_setting(self, key: str, value: str) -> bool:
        """Save a setting."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.utcnow().isoformat()))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save setting {key}: {e}")
            return False
    
    def load_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Load a setting."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            return row['value'] if row else default
            
        except Exception as e:
            logger.error(f"Failed to load setting {key}: {e}")
            return default
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        try:
            cursor = self.connection.cursor()
            
            # Count conversations
            cursor.execute('SELECT COUNT(*) as count FROM conversations')
            conv_count = cursor.fetchone()['count']
            
            # Count messages
            cursor.execute('SELECT COUNT(*) as count FROM messages')
            msg_count = cursor.fetchone()['count']
            
            # Database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            return {
                'type': 'SQLite',
                'path': self.db_path,
                'conversations': conv_count,
                'messages': msg_count,
                'size_bytes': db_size,
                'connected': self.connection is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {
                'type': 'SQLite',
                'path': self.db_path,
                'error': str(e),
                'connected': False
            }