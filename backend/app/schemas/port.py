"""Pydantic schemas for Port data."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PortBase(BaseModel):
    """Base port schema."""
    ip: str
    port: int
    protocol: str = "tcp"
    state: str = "open"  # open/closed/filtered
    service: Optional[str] = None
    version: Optional[str] = None
    source_tool: Optional[str] = None


class PortCreate(PortBase):
    """Schema for creating a port entry."""
    target_id: str


class Port(PortBase):
    """Full port schema with ID and timestamps."""
    id: str
    target_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PortQuery(BaseModel):
    """Schema for querying ports."""
    target_id: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    state: Optional[str] = None
    service: Optional[str] = None
