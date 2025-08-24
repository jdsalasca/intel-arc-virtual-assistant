"""
SQLite Repository Implementations
Concrete implementations of repository interfaces using SQLite database.
"""

import aiosqlite
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..interfaces.repositories import (
    IMessageRepository, IConversationRepository, IModelRepository, IConfigRepository
)
from ..models.domain import Message, Conversation, ModelInfo, MessageRole, ConversationStatus, ModelType


class SQLiteMessageRepository(IMessageRepository):
    """SQLite implementation of message repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize the database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    tools_used TEXT,
                    processing_time REAL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                ON messages (conversation_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages (timestamp)
            """)
            await db.commit()

    async def create_message(self, message: Message) -> Message:
        """Create a new message."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages (
                    id, conversation_id, role, content, timestamp, 
                    metadata, tools_used, processing_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.conversation_id,
                message.role.value,
                message.content,
                message.timestamp.isoformat(),
                json.dumps(message.metadata) if message.metadata else None,
                json.dumps(message.tools_used) if message.tools_used else None,
                message.processing_time
            ))
            await db.commit()
        return message

    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by its ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_message(row)
        return None

    async def get_messages_by_conversation(
        self, 
        conversation_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Retrieve messages for a conversation with pagination."""
        query = """
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        """
        params = [conversation_id]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_message(row) for row in rows]

    async def update_message(self, message: Message) -> Message:
        """Update an existing message."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE messages SET
                    content = ?, metadata = ?, tools_used = ?, processing_time = ?
                WHERE id = ?
            """, (
                message.content,
                json.dumps(message.metadata) if message.metadata else None,
                json.dumps(message.tools_used) if message.tools_used else None,
                message.processing_time,
                message.id
            ))
            await db.commit()
        return message

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM messages WHERE id = ?", (message_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    def _row_to_message(self, row) -> Message:
        """Convert database row to Message object."""
        return Message(
            id=row[0],
            conversation_id=row[1],
            role=MessageRole(row[2]),
            content=row[3],
            timestamp=datetime.fromisoformat(row[4]),
            metadata=json.loads(row[5]) if row[5] else None,
            tools_used=json.loads(row[6]) if row[6] else None,
            processing_time=row[7]
        )


class SQLiteConversationRepository(IConversationRepository):
    """SQLite implementation of conversation repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize the database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_status 
                ON conversations (status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated 
                ON conversations (updated_at)
            """)
            await db.commit()

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO conversations (
                    id, title, created_at, updated_at, status, message_count, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation.id,
                conversation.title,
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat(),
                conversation.status.value,
                conversation.message_count,
                json.dumps(conversation.metadata) if conversation.metadata else None
            ))
            await db.commit()
        return conversation

    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by its ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_conversation(row)
        return None

    async def get_conversations(
        self, 
        limit: Optional[int] = None,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Conversation]:
        """Retrieve conversations with optional filtering."""
        query = "SELECT * FROM conversations"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY updated_at DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_conversation(row) for row in rows]

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE conversations SET
                    title = ?, updated_at = ?, status = ?, 
                    message_count = ?, metadata = ?
                WHERE id = ?
            """, (
                conversation.title,
                conversation.updated_at.isoformat(),
                conversation.status.value,
                conversation.message_count,
                json.dumps(conversation.metadata) if conversation.metadata else None,
                conversation.id
            ))
            await db.commit()
        return conversation

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            # Delete messages first (cascade)
            await db.execute(
                "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
            )
            cursor = await db.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_conversation_with_messages(
        self, 
        conversation_id: str,
        message_limit: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with its messages."""
        conversation = await self.get_conversation_by_id(conversation_id)
        if not conversation:
            return None
        
        # Get messages for this conversation
        from .sqlite_repositories import SQLiteMessageRepository
        message_repo = SQLiteMessageRepository(self.db_path)
        messages = await message_repo.get_messages_by_conversation(
            conversation_id, limit=message_limit
        )
        
        return {
            "conversation": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in messages]
        }

    def _row_to_conversation(self, row) -> Conversation:
        """Convert database row to Conversation object."""
        return Conversation(
            id=row[0],
            title=row[1],
            created_at=datetime.fromisoformat(row[2]),
            updated_at=datetime.fromisoformat(row[3]),
            status=ConversationStatus(row[4]),
            message_count=row[5],
            metadata=json.loads(row[6]) if row[6] else None
        )


class SQLiteModelRepository(IModelRepository):
    """SQLite implementation of model repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize the database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    loaded BOOLEAN DEFAULT 0,
                    device TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_type 
                ON models (type)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_loaded 
                ON models (loaded)
            """)
            await db.commit()

    async def save_model_info(self, model_info: ModelInfo) -> ModelInfo:
        """Save model information."""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO models (
                    id, name, type, version, size, loaded, device, metadata,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_info.id,
                model_info.name,
                model_info.type.value,
                model_info.version,
                model_info.size,
                model_info.loaded,
                model_info.device.value if model_info.device else None,
                json.dumps(model_info.metadata) if model_info.metadata else None,
                now,
                now
            ))
            await db.commit()
        return model_info

    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retrieve model information by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM models WHERE id = ?", (model_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_model_info(row)
        return None

    async def get_all_models(self) -> List[ModelInfo]:
        """Retrieve all model information."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM models ORDER BY name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_model_info(row) for row in rows]

    async def update_model_status(self, model_id: str, loaded: bool) -> bool:
        """Update model load status."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE models SET loaded = ?, updated_at = ? WHERE id = ?
            """, (loaded, datetime.now().isoformat(), model_id))
            await db.commit()
            return cursor.rowcount > 0

    async def delete_model_info(self, model_id: str) -> bool:
        """Delete model information."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM models WHERE id = ?", (model_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    def _row_to_model_info(self, row) -> ModelInfo:
        """Convert database row to ModelInfo object."""
        from ..models.domain import HardwareType
        return ModelInfo(
            id=row[0],
            name=row[1],
            type=ModelType(row[2]),
            version=row[3],
            size=row[4],
            loaded=bool(row[5]),
            device=HardwareType(row[6]) if row[6] else None,
            metadata=json.loads(row[7]) if row[7] else None
        )


class SQLiteConfigRepository(IConfigRepository):
    """SQLite implementation of configuration repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize the database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.commit()

    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value by key."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM config WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
        return None

    async def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO config (key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, json.dumps(value), now, now))
            await db.commit()
        return True

    async def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT key, value FROM config") as cursor:
                rows = await cursor.fetchall()
                return {row[0]: json.loads(row[1]) for row in rows}

    async def delete_config(self, key: str) -> bool:
        """Delete configuration by key."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM config WHERE key = ?", (key,)
            )
            await db.commit()
            return cursor.rowcount > 0