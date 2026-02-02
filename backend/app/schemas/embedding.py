"""Pydantic schemas for Embedding data."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class EmbeddingBase(BaseModel):
    """Base embedding schema."""
    object_type: str  # finding, port, vuln, subdomain
    object_id: str
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingCreate(EmbeddingBase):
    """Schema for creating an embedding."""
    pass


class Embedding(EmbeddingBase):
    """Full embedding schema with ID and timestamps."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmbeddingQuery(BaseModel):
    """Schema for querying embeddings."""
    object_type: Optional[str] = None
    object_id: Optional[str] = None
