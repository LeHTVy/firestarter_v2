"""Pydantic schemas for Target data."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TargetBase(BaseModel):
    """Base target schema."""
    domain: str
    ip: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True
    }


class TargetCreate(TargetBase):
    """Schema for creating a target."""
    pass


class Target(TargetBase):
    """Full target schema with ID and timestamps."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TargetQuery(BaseModel):
    """Schema for querying targets."""
    domain: Optional[str] = None
    ip: Optional[str] = None
