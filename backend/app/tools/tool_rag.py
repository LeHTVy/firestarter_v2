"""Tool RAG - Semantic retrieval and LLM-based tool selection.

Replaces hard-coded CATEGORY_TO_TOOL mapping with:
1. Semantic search via pgvector
2. LLM reasoning to select best tool+command
"""

import uuid
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, ToolEmbedding
from app.tools.tool_knowledge import (
    ToolKnowledge, ToolCommand, ToolCandidate, ToolSelection, RiskLevel
)


class ToolRAG:
    """Semantic tool retrieval and selection."""
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self._tools_cache: Dict[str, ToolKnowledge] = {}
        self._ollama_base_url = "http://localhost:11434"
        
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector from Ollama."""
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._ollama_base_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
    
    async def load_tools_from_json(self) -> List[ToolKnowledge]:
        """Load tools from tools.json and specs, convert to ToolKnowledge."""
        tools_path = Path(__file__).parent / "metadata" / "tools.json"
        
        tools = []
        
        if tools_path.exists():
            with open(tools_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for tool_data in data.get("tools", []):
                # Build RAG description from existing fields
                name = tool_data.get("name", "")
                description = tool_data.get("description", "")
                capabilities = tool_data.get("capability", [])
                
                # Convert commands to ToolCommand objects
                commands = []
                for cmd_name, cmd_data in tool_data.get("commands", {}).items():
                    commands.append(ToolCommand(
                        name=cmd_name,
                        purpose=cmd_data.get("description", f"{cmd_name} command"),
                        template=f"{name} {cmd_name}",  # Simplified
                        timeout=cmd_data.get("timeout", 300)
                    ))
                
                # Build when_to_use from capabilities
                when_to_use = []
                for cap in capabilities:
                    when_to_use.append(f"when you need to {cap.replace('_', ' ')}")
                
                # Determine risk level
                risk_str = tool_data.get("risk_level", "low")
                risk_level = RiskLevel(risk_str) if risk_str in [r.value for r in RiskLevel] else RiskLevel.LOW
                
                tk = ToolKnowledge(
                    tool=name,
                    aliases=tool_data.get("aliases", []),
                    categories=[tool_data.get("category", "unknown")],
                    capabilities=capabilities,
                    description=description,
                    when_to_use=when_to_use,
                    inputs=tool_data.get("scope", ["ip", "domain"]),
                    commands=commands,
                    implementation=tool_data.get("implementation"),
                    risk_level=risk_level,
                    requires_confirmation=tool_data.get("risk_level", "low") in ["high", "critical"]
                )
                tools.append(tk)
                self._tools_cache[name] = tk
        
        # Also load from specs
        try:
            from app.tools.specs import get_all_specs
            for spec in get_all_specs():
                if spec.name not in self._tools_cache:
                    commands = []
                    for cmd_name, cmd_template in spec.commands.items():
                        commands.append(ToolCommand(
                            name=cmd_name,
                            purpose=cmd_template.description or f"{cmd_name} operation",
                            template=" ".join([spec.name] + cmd_template.args),
                            timeout=cmd_template.timeout,
                            requires_sudo=cmd_template.requires_sudo
                        ))
                    
                    tk = ToolKnowledge(
                        tool=spec.name,
                        aliases=spec.aliases,
                        categories=[spec.category.value],
                        capabilities=[],
                        description=spec.description,
                        when_to_use=[],
                        inputs=["ip", "domain", "url"],
                        commands=commands,
                        implementation=spec.implementation,
                        risk_level=RiskLevel.LOW,
                        is_available=spec.is_available
                    )
                    tools.append(tk)
                    self._tools_cache[spec.name] = tk
        except ImportError:
            pass
        
        return tools
    
    async def index_tools(self) -> int:
        """Index all tools into pgvector. Returns count of indexed tools."""
        tools = await self.load_tools_from_json()
        indexed = 0
        
        async with async_session() as session:
            # Clear existing tool embeddings
            await session.execute(text("DELETE FROM tool_embeddings"))
            
            for tool in tools:
                # Create tool-level embedding
                embed_text = tool.get_embedding_text()
                try:
                    vector = await self._get_embedding(embed_text)
                    if not vector or len(vector) != self.embedding_dim:
                        print(f"⚠️ Skipping {tool.tool}: invalid embedding dimension")
                        continue
                    
                    embedding = ToolEmbedding(
                        id=str(uuid.uuid4()),
                        tool_name=tool.tool,
                        command_name=None,  # Tool-level
                        description=embed_text,
                        vector=vector,
                        risk_level=tool.risk_level.value,
                        extra_metadata={
                            "capabilities": tool.capabilities,
                            "aliases": tool.aliases
                        }
                    )
                    session.add(embedding)
                    indexed += 1
                    
                    # Also index individual commands
                    for cmd_text in tool.get_command_embedding_texts():
                        cmd_vector = await self._get_embedding(cmd_text["text"])
                        if cmd_vector and len(cmd_vector) == self.embedding_dim:
                            cmd_embedding = ToolEmbedding(
                                id=str(uuid.uuid4()),
                                tool_name=tool.tool,
                                command_name=cmd_text["command"],
                                description=cmd_text["text"],
                                vector=cmd_vector,
                                risk_level=tool.risk_level.value,
                                extra_metadata={}
                            )
                            session.add(cmd_embedding)
                            indexed += 1
                            
                except Exception as e:
                    print(f"❌ Error indexing {tool.tool}: {e}")
                    continue
            
            await session.commit()
        
        print(f"✅ Indexed {indexed} tool embeddings")
        return indexed
    
    async def search(self, query: str, k: int = 5) -> List[ToolCandidate]:
        """Semantic search for relevant tools."""
        query_vector = await self._get_embedding(query)
        
        if not query_vector:
            return []
        
        async with async_session() as session:
            # pgvector cosine distance search
            stmt = text("""
                SELECT tool_name, command_name, description, risk_level,
                       1 - (vector <=> :query_vector::vector) as similarity
                FROM tool_embeddings
                ORDER BY vector <=> :query_vector::vector
                LIMIT :k
            """)
            
            result = await session.execute(stmt, {
                "query_vector": str(query_vector),
                "k": k
            })
            rows = result.fetchall()
            
            candidates = []
            seen_tools = set()
            
            for row in rows:
                tool_name = row[0]
                command_name = row[1]
                description = row[2]
                risk_level = row[3]
                similarity = row[4]
                
                # Get template from cache
                template = None
                if tool_name in self._tools_cache:
                    tool = self._tools_cache[tool_name]
                    if command_name:
                        for cmd in tool.commands:
                            if cmd.name == command_name:
                                template = cmd.template
                                break
                
                # Deduplicate by tool (keep highest similarity)
                if tool_name not in seen_tools:
                    seen_tools.add(tool_name)
                    candidates.append(ToolCandidate(
                        tool=tool_name,
                        command=command_name,
                        similarity=float(similarity),
                        description=description,
                        risk_level=RiskLevel(risk_level) if risk_level in [r.value for r in RiskLevel] else RiskLevel.LOW,
                        template=template
                    ))
            
            return candidates
    
    async def select_tool(
        self, 
        intent: str, 
        target: str, 
        candidates: List[ToolCandidate],
        model: str = "mistral"
    ) -> Optional[ToolSelection]:
        """Use LLM to select the best tool from candidates."""
        if not candidates:
            return None
        
        import httpx
        
        # Build candidate list for prompt
        candidate_text = "\n".join([
            f"{i+1}. {c.tool}" + (f" ({c.command})" if c.command else "") + 
            f" - {c.description[:100]}... [risk: {c.risk_level.value}]"
            for i, c in enumerate(candidates)
        ])
        
        prompt = f"""You are a security tool selector. Given the user's intent and available tools, select the BEST tool.

User Intent: {intent}
Target: {target}

Available Tools:
{candidate_text}

Respond in JSON format ONLY:
{{
    "tool": "<tool_name>",
    "command": "<command_name or null>",
    "reasoning": "<why this tool>",
    "confidence": <0.0-1.0>
}}"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "{}")
        
        # Parse JSON response
        import re
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                selection_data = json.loads(json_match.group())
            else:
                selection_data = json.loads(content)
            
            # Find the selected candidate to get risk level
            selected_candidate = next(
                (c for c in candidates if c.tool == selection_data.get("tool")), 
                candidates[0]
            )
            
            selection = ToolSelection(
                tool=selection_data.get("tool", candidates[0].tool),
                command=selection_data.get("command"),
                reasoning=selection_data.get("reasoning", "Selected based on similarity"),
                confidence=selection_data.get("confidence", 0.8),
                risk_level=selected_candidate.risk_level
            )
            selection._template = selected_candidate.template
            return selection
            
        except Exception as e:
            print(f"⚠️ LLM selection parse error: {e}")
            # Fallback to highest similarity
            best = candidates[0]
            return ToolSelection(
                tool=best.tool,
                command=best.command,
                reasoning="Selected based on highest semantic similarity",
                confidence=best.similarity,
                risk_level=best.risk_level
            )


# Singleton instance
tool_rag = ToolRAG()


async def index_all_tools():
    """Convenience function to index all tools."""
    return await tool_rag.index_tools()
