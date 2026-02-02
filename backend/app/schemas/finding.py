"""Pydantic schemas for Finding data."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class FindingBase(BaseModel):
    """Base finding schema."""
    type: str  # subdomain, vuln, info, cve, etc.
    value: str
    severity: str = "info"  # info/low/medium/high/critical
    confidence: int = Field(default=80, ge=0, le=100)
    source_tool: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FindingCreate(FindingBase):
    """Schema for creating a finding."""
    target_id: str


class Finding(FindingBase):
    """Full finding schema with ID and timestamps."""
    id: str
    target_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FindingQuery(BaseModel):
    """Schema for querying findings."""
    target_id: Optional[str] = None
    type: Optional[str] = None
    severity: Optional[str] = None
    min_confidence: Optional[int] = None
