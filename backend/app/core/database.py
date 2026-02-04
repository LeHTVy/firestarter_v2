"""Database connection module using asyncpg/SQLAlchemy (NOT Supabase SDK)."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, func
from pgvector.sqlalchemy import Vector

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL không tìm thấy trong file .env. Hãy kiểm tra lại!")

if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    pool_size=5, 
    max_overflow=10,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# ================== MODELS ==================

class Target(Base):
    __tablename__ = "targets"
    
    id = Column(String, primary_key=True)
    domain = Column(String, nullable=False, index=True)
    ip = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    metadata_ = Column("metadata", JSON, default={})


class Port(Base):
    __tablename__ = "ports"
    
    id = Column(String, primary_key=True)
    target_id = Column(String, nullable=False, index=True)
    ip = Column(String, nullable=False, index=True)
    port = Column(Integer, nullable=False, index=True)
    protocol = Column(String, default="tcp")
    state = Column(String, default="open")  # open/closed/filtered
    service = Column(String, nullable=True)
    version = Column(String, nullable=True)
    source_tool = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True)
    target_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  
    value = Column(Text, nullable=False)
    severity = Column(String, default="info")  
    confidence = Column(Integer, default=80)
    source_tool = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime, server_default=func.now())


class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(String, primary_key=True)
    object_type = Column(String, nullable=False, index=True)  
    object_id = Column(String, nullable=False, index=True)
    vector = Column(Vector(1536))  
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime, server_default=func.now())


class ToolEmbedding(Base):
    """Dedicated table for tool knowledge embeddings (RAG)."""
    __tablename__ = "tool_embeddings"
    
    id = Column(String, primary_key=True)
    tool_name = Column(String, nullable=False, index=True)
    command_name = Column(String, nullable=True, index=True)  # NULL = tool-level embedding
    description = Column(Text, nullable=False)  # The text that was embedded
    vector = Column(Vector(1536))
    risk_level = Column(String, default="low")
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime, server_default=func.now())


# ================== DB UTILITIES ==================

async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session
