"""Conversation Manager for persistent conversation storage and context management."""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles
import uuid


@dataclass
class ConversationMessage:
    """Individual message in a conversation."""
    id: str
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    files: Optional[List[Dict[str, Any]]] = None


@dataclass
class Conversation:
    """Complete conversation with metadata."""
    id: str
    title: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationManager:
    """Manages conversation storage, retrieval, and context management."""
    
    def __init__(self, storage_path: str = "data/conversations", max_memory_conversations: int = 100):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.max_memory_conversations = max_memory_conversations
        
        # In-memory cache for fast access
        self._conversations_cache: Dict[str, Conversation] = {}
        self._conversation_index: Dict[str, str] = {}  # conversation_id -> file_path
        self._session_conversations: Dict[str, List[str]] = {}  # session_id -> conversation_ids
        
        # Load existing conversations on startup (lazy loading)
        self._initialized = False
    
    async def _load_existing_conversations(self):
        """Load existing conversations from storage."""
        try:
            for file_path in self.storage_path.glob("*.json"):
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        data = json.loads(await f.read())
                        conversation = self._dict_to_conversation(data)
                        
                        # Add to cache if under limit
                        if len(self._conversations_cache) < self.max_memory_conversations:
                            self._conversations_cache[conversation.id] = conversation
                        
                        # Update indexes
                        self._conversation_index[conversation.id] = str(file_path)
                        
                        if conversation.session_id:
                            if conversation.session_id not in self._session_conversations:
                                self._session_conversations[conversation.session_id] = []
                            self._session_conversations[conversation.session_id].append(conversation.id)
                
                except Exception as e:
                    print(f"⚠️ Error loading conversation from {file_path}: {e}")
        
        except Exception as e:
            print(f"⚠️ Error loading conversations: {e}")
    
    def _dict_to_conversation(self, data: Dict[str, Any]) -> Conversation:
        """Convert dictionary to Conversation object."""
        messages = [
            ConversationMessage(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                metadata=msg.get("metadata"),
                files=msg.get("files")
            )
            for msg in data.get("messages", [])
        ]
        
        return Conversation(
            id=data["id"],
            title=data["title"],
            messages=messages,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            session_id=data.get("session_id"),
            metadata=data.get("metadata")
        )
    
    def _conversation_to_dict(self, conversation: Conversation) -> Dict[str, Any]:
        """Convert Conversation object to dictionary."""
        return {
            "id": conversation.id,
            "title": conversation.title,
            "messages": [asdict(msg) for msg in conversation.messages],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "session_id": conversation.session_id,
            "metadata": conversation.metadata
        }
    
    async def _ensure_initialized(self):
        """Ensure the conversation manager is initialized."""
        if not self._initialized:
            await self._load_existing_conversations()
            self._initialized = True

    async def create_conversation(
        self,
        title: str = "New Conversation",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation."""
        await self._ensure_initialized()
        
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to cache
        self._conversations_cache[conversation_id] = conversation
        
        # Update indexes
        if session_id:
            if session_id not in self._session_conversations:
                self._session_conversations[session_id] = []
            self._session_conversations[session_id].append(conversation_id)
        
        # Persist to storage
        await self._persist_conversation(conversation)
        
        return conversation
    
    async def create_conversation_with_id(
        self,
        conversation_id: str,
        title: str = "New Conversation",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation with a specific ID."""
        await self._ensure_initialized()
        
        now = datetime.utcnow().isoformat()
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to cache
        self._conversations_cache[conversation_id] = conversation
        
        # Update indexes
        if session_id:
            if session_id not in self._session_conversations:
                self._session_conversations[session_id] = []
            self._session_conversations[session_id].append(conversation_id)
        
        # Persist to storage
        await self._persist_conversation(conversation)
        
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        await self._ensure_initialized()
        
        # Check cache first
        if conversation_id in self._conversations_cache:
            return self._conversations_cache[conversation_id]
        
        # Load from storage if not in cache
        if conversation_id in self._conversation_index:
            file_path = self._conversation_index[conversation_id]
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    data = json.loads(await f.read())
                    conversation = self._dict_to_conversation(data)
                    
                    # Add to cache if under limit
                    if len(self._conversations_cache) < self.max_memory_conversations:
                        self._conversations_cache[conversation_id] = conversation
                    
                    return conversation
            except Exception as e:
                print(f"⚠️ Error loading conversation {conversation_id}: {e}")
        
        return None
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ConversationMessage]:
        """Add a message to a conversation."""
        await self._ensure_initialized()
        
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata,
            files=files
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow().isoformat()
        
        # Update cache
        self._conversations_cache[conversation_id] = conversation
        
        # Persist to storage
        await self._persist_conversation(conversation)
        
        return message
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> List[ConversationMessage]:
        """Get conversation history with optional filtering."""
        await self._ensure_initialized()
        
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation.messages
        
        # Filter out system messages if not requested
        if not include_system:
            messages = [msg for msg in messages if msg.role != "system"]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        max_tokens: int = 4000,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """Get conversation context optimized for LLM input."""
        await self._ensure_initialized()
        
        messages = await self.get_conversation_history(
            conversation_id,
            include_system=include_system
        )
        
        # Convert to LLM format and apply token limit
        context_messages = []
        current_tokens = 0
        
        # Start from the most recent messages and work backwards
        for message in reversed(messages):
            message_tokens = len(message.content.split()) * 1.3  # Rough token estimation
            
            if current_tokens + message_tokens > max_tokens:
                break
            
            context_messages.insert(0, {
                "role": message.role,
                "content": message.content,
                "metadata": message.metadata
            })
            
            current_tokens += message_tokens
        
        return context_messages
    
    async def get_session_conversations(self, session_id: str) -> List[Conversation]:
        """Get all conversations for a session."""
        await self._ensure_initialized()
        
        conversation_ids = self._session_conversations.get(session_id, [])
        conversations = []
        
        for conv_id in conversation_ids:
            conversation = await self.get_conversation(conv_id)
            if conversation:
                conversations.append(conversation)
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations
    
    async def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        await self._ensure_initialized()
        
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.title = title
        conversation.updated_at = datetime.utcnow().isoformat()
        
        # Update cache
        self._conversations_cache[conversation_id] = conversation
        
        # Persist to storage
        await self._persist_conversation(conversation)
        
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        await self._ensure_initialized()
        
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Remove from cache
        if conversation_id in self._conversations_cache:
            del self._conversations_cache[conversation_id]
        
        # Remove from indexes
        if conversation_id in self._conversation_index:
            del self._conversation_index[conversation_id]
        
        if conversation.session_id and conversation.session_id in self._session_conversations:
            if conversation_id in self._session_conversations[conversation.session_id]:
                self._session_conversations[conversation.session_id].remove(conversation_id)
        
        # Delete from storage
        file_path = self.storage_path / f"{conversation_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"⚠️ Error deleting conversation file: {e}")
        
        return True
    
    async def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """Clean up conversations older than specified days."""
        await self._ensure_initialized()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = 0
        
        for file_path in self.storage_path.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    data = json.loads(await f.read())
                    updated_at = datetime.fromisoformat(data["updated_at"])
                    
                    if updated_at < cutoff_date:
                        conversation_id = data["id"]
                        if await self.delete_conversation(conversation_id):
                            deleted_count += 1
            
            except Exception as e:
                print(f"⚠️ Error checking conversation {file_path}: {e}")
        
        return deleted_count
    
    async def _persist_conversation(self, conversation: Conversation):
        """Persist conversation to storage."""
        try:
            file_path = self.storage_path / f"{conversation.id}.json"
            data = self._conversation_to_dict(conversation)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
            # Update index
            self._conversation_index[conversation.id] = str(file_path)
        
        except Exception as e:
            print(f"⚠️ Error persisting conversation {conversation.id}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_conversations": len(self._conversations_cache),
            "total_indexed": len(self._conversation_index),
            "active_sessions": len(self._session_conversations),
            "cache_limit": self.max_memory_conversations
        }


# Global conversation manager instance
conversation_manager = ConversationManager()
