"""Unified Memory Manager - Agent never queries DB directly."""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, Port as PortModel, Finding as FindingModel, Target as TargetModel, Embedding as EmbeddingModel
from app.core.redis import redis_client
from app.schemas.port import Port, PortCreate, PortQuery
from app.schemas.finding import Finding, FindingCreate, FindingQuery
from app.schemas.target import Target, TargetCreate


class MemoryManager:
    """Abstraction layer for agent memory.
    
    - Short-term (Redis): session context, scan progress, tool stdout
    - Long-term (PostgreSQL): targets, ports, findings, embeddings
    - Vector (pgvector): tool embeddings.
    - RAG
    """
    
    # ================== SHORT-TERM (Redis) ==================
    
    async def set_session_context(self, session_id: str, context: dict):
        """Store session context in Redis."""
        await redis_client.set_session_context(session_id, context)
    
    async def get_session_context(self, session_id: str) -> Optional[dict]:
        """Get session context from Redis."""
        return await redis_client.get_session_context(session_id)
    
    async def set_scan_progress(self, scan_id: str, progress: dict):
        """Store scan progress in Redis."""
        await redis_client.set_scan_progress(scan_id, progress)
    
    async def get_scan_progress(self, scan_id: str) -> Optional[dict]:
        """Get scan progress from Redis."""
        return await redis_client.get_scan_progress(scan_id)
    
    async def append_tool_stdout(self, scan_id: str, tool_name: str, line: str):
        """Append tool stdout to Redis buffer."""
        await redis_client.append_tool_stdout(scan_id, tool_name, line)
    
    async def get_tool_stdout(self, scan_id: str, tool_name: str, limit: int = 100) -> list:
        """Get tool stdout from Redis."""
        return await redis_client.get_tool_stdout(scan_id, tool_name, limit)
    
    # ================== LONG-TERM (PostgreSQL) ==================
    
    # --- Targets ---
    async def store_target(self, data: TargetCreate) -> Target:
        """Store a target in PostgreSQL."""
        async with async_session() as session:
            target = TargetModel(
                id=str(uuid.uuid4()),
                domain=data.domain,
                ip=data.ip,
                extra_metadata=data.extra_metadata
            )
            session.add(target)
            await session.commit()
            await session.refresh(target)
            return Target.model_validate(target)
    
    async def list_targets(self) -> List[Target]:
        """Get all targets from PostgreSQL."""
        async with async_session() as session:
            stmt = select(TargetModel).order_by(TargetModel.created_at.desc())
            result = await session.execute(stmt)
            targets = result.scalars().all()
            return [Target.model_validate(t) for t in targets]

    # --- Ports ---
    async def store_port(self, data: PortCreate) -> Port:
        """Store a port in PostgreSQL."""
        async with async_session() as session:
            port = PortModel(
                id=str(uuid.uuid4()),
                target_id=data.target_id,
                ip=data.ip,
                port=data.port,
                protocol=data.protocol,
                state=data.state,
                service=data.service,
                version=data.version,
                source_tool=data.source_tool
            )
            session.add(port)
            await session.commit()
            await session.refresh(port)
            return Port.model_validate(port)
    
    async def query_ports(self, filters: PortQuery) -> List[Port]:
        """Query ports from PostgreSQL."""
        async with async_session() as session:
            stmt = select(PortModel)
            conditions = []
            
            if filters.target_id:
                conditions.append(PortModel.target_id == filters.target_id)
            if filters.ip:
                conditions.append(PortModel.ip == filters.ip)
            if filters.port:
                conditions.append(PortModel.port == filters.port)
            if filters.state:
                conditions.append(PortModel.state == filters.state)
            if filters.service:
                conditions.append(PortModel.service.ilike(f"%{filters.service}%"))
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await session.execute(stmt)
            ports = result.scalars().all()
            return [Port.model_validate(p) for p in ports]
    
    # --- Findings ---
    async def store_finding(self, data: FindingCreate) -> Finding:
        """Store a finding in PostgreSQL."""
        async with async_session() as session:
            finding = FindingModel(
                id=str(uuid.uuid4()),
                target_id=data.target_id,
                type=data.type,
                value=data.value,
                severity=data.severity,
                confidence=data.confidence,
                source_tool=data.source_tool,
                extra_metadata=data.extra_metadata
            )
            session.add(finding)
            await session.commit()
            await session.refresh(finding)
            return Finding.model_validate(finding)
    
    async def query_findings(self, filters: FindingQuery) -> List[Finding]:
        """Query findings from PostgreSQL."""
        async with async_session() as session:
            stmt = select(FindingModel)
            conditions = []
            
            if filters.target_id:
                conditions.append(FindingModel.target_id == filters.target_id)
            if filters.type:
                conditions.append(FindingModel.type == filters.type)
            if filters.severity:
                conditions.append(FindingModel.severity == filters.severity)
            if filters.min_confidence:
                conditions.append(FindingModel.confidence >= filters.min_confidence)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await session.execute(stmt)
            findings = result.scalars().all()
            return [Finding.model_validate(f) for f in findings]
    
    # ================== STRUCTURED STORAGE ==================
    
    async def store_structured(self, tool_name: str, parsed_data: dict, target_id: str):
        """Store structured tool output into appropriate tables.
        
        This is the main entry point for storing parsed tool results.
        """
        # Ports
        ports = parsed_data.get("ports", [])
        for port_data in ports:
            await self.store_port(PortCreate(
                target_id=target_id,
                ip=port_data.get("ip", ""),
                port=port_data.get("port", 0),
                protocol=port_data.get("protocol", "tcp"),
                state=port_data.get("state", "open"),
                service=port_data.get("service"),
                version=port_data.get("version"),
                source_tool=tool_name
            ))
        
        # Findings (subdomains, vulns, etc.)
        findings = parsed_data.get("findings", [])
        for finding_data in findings:
            await self.store_finding(FindingCreate(
                target_id=target_id,
                type=finding_data.get("type", "info"),
                value=finding_data.get("value", ""),
                severity=finding_data.get("severity", "info"),
                confidence=finding_data.get("confidence", 80),
                source_tool=tool_name,
                metadata=finding_data.get("metadata", {})
            ))
    
    # ================== SEMANTIC SEARCH (pgvector) ==================
    
    async def semantic_search(self, query_vector: List[float], k: int = 5) -> List[dict]:
        """Semantic search using pgvector."""
        async with async_session() as session:
            # Using raw SQL for pgvector cosine similarity
            from sqlalchemy import text
            stmt = text("""
                SELECT id, object_type, object_id, metadata, 
                       1 - (vector <=> :query_vector) as similarity
                FROM embeddings
                ORDER BY vector <=> :query_vector
                LIMIT :k
            """)
            result = await session.execute(stmt, {"query_vector": str(query_vector), "k": k})
            rows = result.fetchall()
            return [{"id": r[0], "object_type": r[1], "object_id": r[2], 
                     "metadata": r[3], "similarity": r[4]} for r in rows]


# Singleton instance
memory_manager = MemoryManager()
