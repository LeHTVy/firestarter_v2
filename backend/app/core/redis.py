"""Redis client for short-term memory."""

import os
import redis.asyncio as redis
from typing import Optional, Any
import orjson

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Connection pool
pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)


class RedisClient:
    """Short-term memory client."""
    
    def __init__(self):
        self.client = redis.Redis(connection_pool=pool)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value with TTL (default 1 hour)."""
        if isinstance(value, (dict, list)):
            value = orjson.dumps(value).decode()
        return await self.client.set(key, value, ex=ttl)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self.client.get(key)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get and parse JSON value."""
        data = await self.client.get(key)
        if data:
            return orjson.loads(data)
        return None
    
    async def delete(self, key: str) -> int:
        """Delete key."""
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0
    
    # =============== SESSION CONTEXT ===============
    
    async def set_session_context(self, session_id: str, context: dict, ttl: int = 7200):
        """Store session context (2 hour TTL)."""
        key = f"session:{session_id}:context"
        return await self.set(key, context, ttl)
    
    async def get_session_context(self, session_id: str) -> Optional[dict]:
        """Get session context."""
        key = f"session:{session_id}:context"
        return await self.get_json(key)
    
    # =============== SCAN PROGRESS ===============
    
    async def set_scan_progress(self, scan_id: str, progress: dict, ttl: int = 3600):
        """Store scan progress."""
        key = f"scan:{scan_id}:progress"
        return await self.set(key, progress, ttl)
    
    async def get_scan_progress(self, scan_id: str) -> Optional[dict]:
        """Get scan progress."""
        key = f"scan:{scan_id}:progress"
        return await self.get_json(key)
    
    # =============== TOOL STDOUT ===============
    
    async def append_tool_stdout(self, scan_id: str, tool_name: str, line: str):
        """Append line to tool stdout buffer."""
        key = f"scan:{scan_id}:tool:{tool_name}:stdout"
        await self.client.rpush(key, line)
        await self.client.expire(key, 3600)
    
    async def get_tool_stdout(self, scan_id: str, tool_name: str, limit: int = 100) -> list:
        """Get tool stdout lines."""
        key = f"scan:{scan_id}:tool:{tool_name}:stdout"
        return await self.client.lrange(key, -limit, -1)
    
    # =============== DEDUP ===============
    
    async def add_to_dedup(self, dedup_key: str, value: str, ttl: int = 86400) -> bool:
        """Add to dedup set. Returns True if new, False if exists."""
        key = f"dedup:{dedup_key}"
        added = await self.client.sadd(key, value)
        await self.client.expire(key, ttl)
        return added > 0
    
    async def is_in_dedup(self, dedup_key: str, value: str) -> bool:
        """Check if value in dedup set."""
        key = f"dedup:{dedup_key}"
        return await self.client.sismember(key, value)


redis_client = RedisClient()
