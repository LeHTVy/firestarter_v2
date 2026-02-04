"""Pentest Orchestrator with HITL/Auto mode support."""

from typing import Dict, Any, Optional, Tuple
from app.core.ollama import ollama_client
from app.target.parser import TargetParser, ParsedTarget
from app.target.validator import TargetValidator
from app.schemas.session import (
    AgentMode, 
    SessionState, 
    PendingAction, 
    RiskLevel,
    ActionConfirmation
)
from jinja2 import Environment, FileSystemLoader
import os
import re
import uuid
import json
import asyncio
from dotenv import load_dotenv

from app.tools.executor import get_executor
from app.core.terminal import terminal_manager
from app.memory.manager import memory_manager


class PentestOrchestrator:
    """
    Orchestrator with two modes:
    - HITL (Human-in-the-Loop): Requires user confirmation before tool execution
    - AUTO: Executes tools immediately (except critical actions)
    """

    def __init__(self):
        self.history = []
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Load environment variables for tools
        load_dotenv()
        
        # Target parsing and validation
        self.parser = TargetParser()
        self.validator = TargetValidator()
        
        # Session management (in-memory for now)
        self.sessions: Dict[str, SessionState] = {}

    def get_or_create_session(self, session_id: Optional[str] = None, mode: AgentMode = AgentMode.HITL) -> SessionState:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if session.mode != mode:
                session.switch_mode(mode)
            return session
        
        # Create new session
        new_session = SessionState(
            session_id=session_id or str(uuid.uuid4()),
            mode=mode
        )
        self.sessions[new_session.session_id] = new_session
        return new_session


    async def handle_request(
        self, 
        user_prompt: str, 
        model: str = "mistral",
        session_id: Optional[str] = None,
        mode: str = "hitl"
    ) -> Dict[str, Any]:
        """
        Handle user request using LLM Intent Router and Task Planner.
        """
        # Get or create session
        agent_mode = AgentMode(mode) if isinstance(mode, str) else mode
        session = self.get_or_create_session(session_id, agent_mode)
        
        # Get LLM Analysis
        template = self.jinja_env.get_template("orchestrator.jinja2")
        prompt_context = {
            "user_prompt": user_prompt,
            "current_target": session.current_target,
            "mode": session.mode
        }
        system_prompt = template.render(**prompt_context)
        messages = [
            {"role": "system", "content": "You are a senior penetration testing intent router. You must always respond in JSON format."},
            {"role": "user", "content": system_prompt}
        ]
        
        response = await ollama_client.chat(model=model, messages=messages, format="json")
        content = response.get("message", {}).get("content", "{}")
        
        # Parse JSON from LLM
        try:
            # Simple JSON extraction in case of surrounding text
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                analysis = json.loads(content)
        except Exception as e:
            # If JSON parsing fails, log and try one more time or return error
            print(f"❌ Failed to parse LLM JSON: {e}\nRaw content: {content}")
            return {
                "type": "error",
                "content": "I'm having trouble planning the next steps in JSON format. Please try again.",
                "session_id": session.session_id
            }

        # Update session targets if LLM found new ones
        if analysis.get("targets"):
            first_target = analysis["targets"][0]
            parsed = self.parser.parse(first_target)
            if parsed.is_valid:
                # Check blacklist
                allowed, reason = self.validator.is_allowed(parsed)
                if not allowed:
                    return {
                        "type": "error",
                        "content": f"🚫 Target blocked: {reason}",
                        "session_id": session.session_id
                    }
                session.current_target = parsed.normalized if isinstance(parsed.normalized, str) else parsed.normalized[0]
                # Store target in DB and get ID
                from app.schemas.target import TargetCreate
                try:
                    # Use metadata_ to be safe with renamed field
                    target_obj = await memory_manager.store_target(TargetCreate(
                        domain=session.current_target if "." in session.current_target else "unknown",
                        ip=session.current_target if re.match(r"^\d+\.\d+\.\d+\.\d+$", session.current_target) else None,
                        extra_metadata={}
                    ))
                    session.current_target_id = target_obj.id
                except Exception as e:
                    print(f"⚠️ Failed to store target in DB: {e}")

        tasks = analysis.get("tasks", [])
        display_response = analysis.get("response", "Processing your request...")

        if not tasks:
            return {
                "type": "response",
                "content": display_response,
                "session_id": session.session_id,
                "current_phase": session.current_phase
            }

        task = tasks[0]
        category = task.get("category", "recon").lower()
        task_description = task.get("description", category)

        # Update Phase for Flow Graph
        if "recon" in category or "subdomain" in category or "discover" in category:
            session.current_phase = "Reconnaissance"
        elif "scan" in category or "port" in category:
            session.current_phase = "Scanning"
        elif "vuln" in category or "exploit" in category or "attack" in category:
            session.current_phase = "Exploitation"
        elif "report" in category:
            session.current_phase = "Reporting"
        else:
            session.current_phase = "Scanning" # Default to scanning if unsure

        # ═══════════════════════════════════════════════════════════════
        # RAG-BASED TOOL SELECTION (replaces hard-coded CATEGORY_TO_TOOL)
        # ═══════════════════════════════════════════════════════════════
        from app.tools.tool_rag import tool_rag
        
        # Build semantic query from intent + target
        query = f"User wants to {task_description} on {session.current_target or 'target'}"
        
        # Retrieve top-5 candidate tools
        candidates = await tool_rag.search(query, k=5)
        
        if not candidates:
            # Fallback: return LLM response without tool execution
            return {
                "type": "response",
                "content": display_response,
                "session_id": session.session_id,
                "current_phase": session.current_phase
            }
        
        # LLM selects best tool+command from candidates
        selection = await tool_rag.select_tool(
            intent=analysis.get("intent", task_description),
            target=session.current_target or "unknown",
            candidates=candidates,
            model=model
        )
        
        if not selection:
            return {
                "type": "response",
                "content": display_response,
                "session_id": session.session_id,
                "current_phase": session.current_phase
            }
        
        tool_name = selection.tool
        command_name = selection.command
        risk_level = selection.risk_level.value
        
        # ═══════════════════════════════════════════════════════════════
        # HITL / Auto mode logic - Critical actions ALWAYS require confirmation
        # ═══════════════════════════════════════════════════════════════
        is_critical = risk_level in ["high", "critical"]
        needs_confirmation = (session.mode == AgentMode.HITL) or is_critical
        
        # Build command string via ToolExecutor (robust parameter mapping)
        executor = get_executor()
        try:
            command_str = executor.get_command_string(
                tool_name=tool_name,
                command_name=command_name or "default",
                params={**selection.parameters, "target": session.current_target or "target"}
            )
        except Exception as e:
            # Fallback to simple building if spec building fails
            command_str = selection.get_command_string(session.current_target or "target")
        
        if needs_confirmation:
            pending = PendingAction(
                tool_name=tool_name,
                target=session.current_target or (analysis["targets"][0] if analysis.get("targets") else "unknown"),
                command=command_str,
                description=f"{selection.reasoning}",
                risk_level=risk_level
            )
            session.set_pending_action(pending)
            
            return {
                "type": "confirmation_required",
                "content": display_response,
                "pending_action": pending.model_dump(),
                "session_id": session.session_id,
                "current_phase": session.current_phase
            }
        
        # Auto-execution: Pipe to interactive terminal AND execute for analysis
        terminal_manager.write_input(f"{command_str}\n")
        
        # In AUTO mode, we execute and analyze synchronously to give immediate feedback
        loop = asyncio.get_event_loop()
        try:
            params = {**selection.parameters, "target": session.current_target or "target"}
            result = await loop.run_in_executor(
                None, 
                lambda: executor.execute_tool(
                    tool_name=tool_name,
                    parameters=params,
                    session_id=session.session_id
                )
            )
            
            analysis_text = ""
            if result.get("success"):
                # Store results
                if result.get("results"):
                    await memory_manager.store_structured(
                        tool_name=tool_name,
                        parsed_data=result["results"],
                        target_id=session.current_target_id or session.current_target
                    )
                
                # Analyze results
                analysis_text = await self._analyze_results(
                    result=result,
                    tool_name=tool_name,
                    command=command_str,
                    target=session.current_target or "target",
                    model=model
                )
            
            content = f"✅ Auto-executing: `{command_str}`\n\n{display_response}"
            if analysis_text:
                content += f"\n\n### 🧠 Agent Analysis\n{analysis_text}"
            
            return {
                "type": "response",
                "content": content,
                "session_id": session.session_id,
                "executed_command": command_str,
                "result": result,
                "current_phase": session.current_phase
            }
        except Exception as e:
            return {
                "type": "response",
                "content": f"✅ Auto-executed: `{command_str}` (Analysis failed: {e})\n\n{display_response}",
                "session_id": session.session_id,
                "executed_command": command_str,
                "current_phase": session.current_phase
            }

    async def confirm_action(
        self, 
        session_id: str, 
        action_id: str, 
        approved: bool,
        edited_command: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user confirmation for a pending action.
        
        Args:
            session_id: Session ID
            action_id: Action ID to confirm
            approved: Whether user approved the action
            edited_command: Optional edited command if user modified it
            
        Returns:
            Dict with execution result or rejection message
        """
        if session_id not in self.sessions:
            return {
                "type": "error",
                "content": "Session not found",
                "session_id": session_id,
                "current_phase": "Ready"
            }
        
        session = self.sessions[session_id]
        
        if not session.pending_action:
            return {
                "type": "error", 
                "content": "No pending action to confirm",
                "session_id": session_id,
                "current_phase": session.current_phase
            }
        
        if session.pending_action.action_id != action_id:
            return {
                "type": "error",
                "content": "Action ID mismatch",
                "session_id": session_id,
                "current_phase": session.current_phase
            }
        
        pending = session.clear_pending_action()
        
        if not approved:
            return {
                "type": "response",
                "content": f"❌ Action rejected: {pending.tool_name} on {pending.target}",
                "session_id": session_id,
                "current_phase": session.current_phase
            }
        
        command = edited_command if edited_command else pending.command
        
        # Pipe to interactive terminal
        terminal_manager.write_input(f"{command}\n")
        
        executor = get_executor()
        loop = asyncio.get_event_loop()
        
        try:
            params = {"target": pending.target, "domain": pending.target, "url": pending.target}
            
            # 1. Execute tool via unified executor (captures output and parses data)
            result = await loop.run_in_executor(
                None, 
                lambda: executor.execute_tool(
                    tool_name=pending.tool_name,
                    parameters=params,
                    session_id=session_id
                )
            )
            
            analysis_text = ""
            if result.get("success"):
                # 2. Store results structurally in DB
                if result.get("results"):
                    await memory_manager.store_structured(
                        tool_name=pending.tool_name,
                        parsed_data=result["results"],
                        target_id=session.current_target_id or pending.target # Fallback to target string if no ID
                    )
                
                # 3. AI Analysis of the findings
                analysis_text = await self._analyze_results(
                    result=result,
                    tool_name=pending.tool_name,
                    command=command,
                    target=pending.target,
                    model=session.current_model or "mistral"
                )
                
                content = f"✅ Execution successful: `{command}`\n\n"
                if analysis_text:
                    content += f"### 🧠 Agent Analysis\n{analysis_text}\n\n"
                
                if result.get("raw_output"):
                    output = result["raw_output"]
                    if len(output) > 1000:
                        output = output[:1000] + "... (truncated for chat, see terminal for full output)"
                    content += f"<details>\n<summary>Raw Tool Output</summary>\n\n```\n{output}\n```\n</details>"
            else:
                content = f"❌ Execution failed: `{command}`\n\nError: {result.get('error', 'Unknown error')}"
                
            return {
                "type": "response",
                "content": content,
                "session_id": session_id,
                "executed_command": command,
                "result": result,
                "current_phase": session.current_phase
            }
            
        except Exception as e:
            return {
                "type": "error",
                "content": f"Critical error during execution: {str(e)}",
                "session_id": session_id,
                "current_phase": session.current_phase
            }

    def switch_mode(self, session_id: str, mode: str) -> Dict[str, Any]:
        """Switch agent mode for a session."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found", "current_phase": "Ready"}
        
        agent_mode = AgentMode(mode)
        self.sessions[session_id].switch_mode(agent_mode)
        
        return {
            "success": True,
            "mode": mode,
            "session_id": session_id
        }

    async def _analyze_results(
        self, 
        result: Dict[str, Any], 
        tool_name: str, 
        command: str, 
        target: str,
        model: str
    ) -> str:
        """Have the AI analyze tool findings and provide insights."""
        try:
            template = self.jinja_env.get_template("analysis.jinja2")
            prompt = template.render(
                tool_name=tool_name,
                command=command,
                target=target,
                raw_output=result.get("raw_output", ""),
                parsed_data=result.get("results", {})
            )
            
            response = await ollama_client.generate(
                model=model,
                prompt=prompt,
                system="You are a senior penetration tester. Be technical, concise, and professional."
            )
            return response.get("response", "Could not generate analysis.")
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
            return f"Error during result analysis: {str(e)}"


# Global instance
orchestrator = PentestOrchestrator()
