"""Session state schemas for Firestarter AI."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AgentMode(str, Enum):
    """Agent execution mode."""
    HITL = "hitl"   # Human-in-the-loop: requires confirmation
    AUTO = "auto"   # Fully automated: executes immediately


class RiskLevel(str, Enum):
    """Risk level for pending actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PendingAction(BaseModel):
    """Action waiting for user confirmation (HITL mode)."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    target: str
    command: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    estimated_time: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ActionConfirmation(BaseModel):
    """User response to pending action."""
    action_id: str
    approved: bool
    edited_command: Optional[str] = None


class SessionState(BaseModel):
    """Session state for a chat session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: AgentMode = AgentMode.HITL
    current_target: Optional[str] = None
    current_target_id: Optional[str] = None
    pending_action: Optional[PendingAction] = None
    history: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

    def set_pending_action(self, action: PendingAction) -> None:
        """Set a pending action for confirmation."""
        self.pending_action = action
        self.updated_at = datetime.utcnow()

    def clear_pending_action(self) -> Optional[PendingAction]:
        """Clear and return the pending action."""
        action = self.pending_action
        self.pending_action = None
        self.updated_at = datetime.utcnow()
        return action

    def switch_mode(self, mode: AgentMode) -> None:
        """Switch agent mode."""
        self.mode = mode
        self.updated_at = datetime.utcnow()


class ChatRequestWithSession(BaseModel):
    """Extended chat request with session and mode support."""
    messages: List[dict]
    model: str = "mistral"
    session_id: Optional[str] = None
    mode: AgentMode = AgentMode.HITL

    class Config:
        use_enum_values = True


class ConfirmActionRequest(BaseModel):
    """Request to confirm or reject a pending action."""
    session_id: str
    action_id: str
    approved: bool
    edited_command: Optional[str] = None
