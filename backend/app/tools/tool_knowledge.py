"""Tool Knowledge Schema - Pydantic models for RAG-based tool selection.

Defines structured knowledge about tools that can be embedded and retrieved
via semantic search.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification for tools."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolCommand(BaseModel):
    """A specific command within a tool."""
    name: str = Field(..., description="Command name (e.g., 'quick', 'full', 'enum')")
    purpose: str = Field(..., description="What this command does")
    template: str = Field(..., description="Command template with placeholders (e.g., 'nmap -sV {target}')")
    timeout: int = Field(default=300, description="Timeout in seconds")
    requires_sudo: bool = Field(default=False)
    risk_level: Optional[RiskLevel] = Field(default=None, description="Override tool-level risk")
    
    def get_embedding_text(self) -> str:
        """Generate text for embedding this command."""
        return f"{self.name}: {self.purpose}"


class ToolKnowledge(BaseModel):
    """Complete knowledge about a security tool for RAG retrieval."""
    
    # Identity
    tool: str = Field(..., description="Tool name (e.g., 'nmap', 'subfinder')")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    
    # Categorization
    categories: List[str] = Field(default_factory=list, description="Categories (e.g., ['RECON_PORT', 'SERVICE_ENUM'])")
    capabilities: List[str] = Field(default_factory=list, description="What the tool can do")
    
    # RAG-specific fields
    description: str = Field(..., description="Human-readable description for embedding")
    when_to_use: List[str] = Field(default_factory=list, description="Use case descriptions for semantic matching")
    
    # Technical details
    inputs: List[str] = Field(default_factory=list, description="Input types: ip, domain, url, cidr")
    commands: List[ToolCommand] = Field(default_factory=list)
    implementation: Optional[str] = Field(default=None, description="Python implementation path")
    
    # Risk assessment
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    requires_confirmation: bool = Field(default=False, description="Always needs HITL confirmation")
    
    # Metadata
    install_hint: Optional[str] = None
    is_available: bool = Field(default=False, description="Tool is installed on system")
    
    def get_embedding_text(self) -> str:
        """Generate comprehensive text for embedding this tool."""
        parts = [
            f"Tool: {self.tool}",
            f"Description: {self.description}",
        ]
        
        if self.capabilities:
            parts.append(f"Capabilities: {', '.join(self.capabilities)}")
        
        if self.when_to_use:
            parts.append(f"Use when: {'. '.join(self.when_to_use)}")
        
        if self.inputs:
            parts.append(f"Inputs: {', '.join(self.inputs)}")
            
        # Include command purposes
        for cmd in self.commands:
            parts.append(f"Command {cmd.name}: {cmd.purpose}")
        
        return "\n".join(parts)
    
    def get_command_embedding_texts(self) -> List[Dict[str, str]]:
        """Generate embedding texts for each command separately."""
        texts = []
        for cmd in self.commands:
            text = f"Tool: {self.tool}\nCommand: {cmd.name}\nPurpose: {cmd.purpose}"
            texts.append({
                "tool": self.tool,
                "command": cmd.name,
                "text": text
            })
        return texts


class ToolCandidate(BaseModel):
    """A tool retrieved from semantic search."""
    tool: str
    command: Optional[str] = None
    similarity: float = Field(..., ge=0, le=1)
    description: str
    risk_level: RiskLevel
    template: Optional[str] = None


class ToolSelection(BaseModel):
    """LLM's selected tool and command."""
    tool: str
    command: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = Field(..., description="Why this tool was selected")
    confidence: float = Field(default=0.8, ge=0, le=1)
    risk_level: RiskLevel = RiskLevel.LOW
    
    def get_command_string(self, target: str) -> str:
        """Build the actual command string."""
        params = {**self.parameters, "target": target, "domain": target, "url": target}
        if hasattr(self, '_template') and self._template:
            try:
                return self._template.format(**params)
            except KeyError:
                pass
        return f"{self.tool} {target}"
