"""Robust Tool Executor - Unified engine for security tools.

Metaphorically, this is the 'heart' of the pentest engine, combining:
1. Declarative specs (ToolSpec)
2. PTY-based real-time streaming
3. Sync/Async execution models
4. Interactive terminal command building
5. Execution history and session management
"""

import os
import sys
import time
import select
import subprocess
import shutil
import tempfile
import uuid
import importlib
import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Generator, Union

from app.tools.specs import ToolSpec, CommandTemplate, get_all_specs


@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    success: bool
    tool: str
    command: str
    output: str
    error: str = ""
    exit_code: int = 0
    elapsed_time: float = 0.0
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ToolExecutor:
    """Unified engine for executing security tools from specs."""
    
    def __init__(self):
        self.specs: Dict[str, ToolSpec] = {}
        self.aliases: Dict[str, str] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._load_specs()
        self._discover_tools()
        self.working_dir = tempfile.gettempdir()
    
    def _load_specs(self):
        """Load all tool specs from the specs/ modules."""
        for spec in get_all_specs():
            self.specs[spec.name] = spec
            # Register aliases for easier lookup
            if hasattr(spec, 'aliases'):
                for alias in spec.aliases:
                    self.aliases[alias] = spec.name
    
    def _discover_tools(self):
        """Check which tools are actually installed on the system."""
        for spec in self.specs.values():
            spec.find_executable()
            
    def get_tool(self, name: str) -> Optional[ToolSpec]:
        """Get tool spec by name or alias."""
        if name in self.specs:
            return self.specs[name]
        if name in self.aliases:
            return self.specs.get(self.aliases[name])
        return None

    # ─────────────────────────────────────────────────────────────
    # Command Building Logic
    # ─────────────────────────────────────────────────────────────
    
    def build_command_args(
        self,
        tool_name: str,
        command_name: str,
        params: Dict[str, Any]
    ) -> List[str]:
        """Build command arguments array for a tool/command/params combo."""
        spec = self.get_tool(tool_name)
        if not spec:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        if command_name not in spec.commands:
            raise ValueError(f"Unknown command '{command_name}' for tool '{tool_name}'")
            
        template = spec.commands[command_name]
        
        # Build base args starting with executable
        args = []
        if spec.executable_path:
            args.append(spec.executable_path)
        else:
            # Fallback to name if not found but marked as available (system path)
            args.append(spec.name)
            
        # Normalize/Map parameters (support common aliases)
        norm_params = dict(params)
        
        # Mapping logic (target -> domain/url/ip etc)
        if 'target' not in norm_params:
            for fallback in ['domain', 'url', 'host', 'ip', 'address']:
                if fallback in norm_params:
                    norm_params['target'] = norm_params[fallback]
                    break
        
        # domain/url auto-completion
        if 'domain' not in norm_params and 'target' in norm_params:
            norm_params['domain'] = norm_params['target']
            
        if 'url' not in norm_params and 'target' in norm_params:
            val = str(norm_params['target'])
            if not val.startswith(('http://', 'https://')):
                val = f"http://{val}"
            norm_params['url'] = val

        # Substitute template variables
        for arg in template.args:
            if "{" in arg and "}" in arg:
                # Replace all {key} with value
                for key, value in norm_params.items():
                    arg = arg.replace(f"{{{key}}}", str(value))
                
                # Check for remaining required placeholders
                if "{" in arg:
                    raise KeyError(f"Missing required parameter in template: {arg}")
            args.append(arg)
            
        return args

    def get_command_string(self, tool_name: str, command_name: str, params: Dict[str, Any]) -> str:
        """Get the full raw command string (useful for interactive terminal)."""
        args = self.build_command_args(tool_name, command_name, params)
        return " ".join(args)

    # ─────────────────────────────────────────────────────────────
    # Execution Methods
    # ─────────────────────────────────────────────────────────────

    def execute(
        self,
        tool_name: str,
        command_name: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None,
        agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ToolResult:
        """Run a tool synchronously and return result."""
        spec = self.get_tool(tool_name)
        if not spec:
            return ToolResult(False, tool_name, command_name, "", error=f"Unknown tool: {tool_name}")

        # Fallback to internal implementation if no executable
        if spec.implementation and not spec.executable_path:
            return self._run_implementation(spec, params, agent, session_id)

        try:
            args = self.build_command_args(tool_name, command_name, params)
            tmpl = spec.commands[command_name]
            run_timeout = timeout or tmpl.timeout
            
            start_time = time.time()
            res = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=run_timeout,
                stdin=subprocess.DEVNULL
            )
            elapsed = time.time() - start_time
            
            success = res.returncode in tmpl.success_codes
            result = ToolResult(
                success=success,
                tool=tool_name,
                command=command_name,
                output=res.stdout.strip(),
                error=res.stderr.strip() if not success else "",
                exit_code=res.returncode,
                elapsed_time=elapsed
            )
            
            # Auto-parse if success
            if success:
                from app.tools.output_parsers import get_parser
                parser = get_parser(tool_name)
                result.parsed_data = parser(result.output)

            self._record_history(result, params, agent, session_id)
            return result
            
        except Exception as e:
            err_res = ToolResult(False, tool_name, command_name, "", error=str(e))
            self._record_history(err_res, params, agent, session_id)
            return err_res

    def execute_streaming(
        self,
        tool_name: str,
        command_name: str,
        params: Dict[str, Any],
        stream_callback: Optional[Callable[[str], None]] = None,
        timeout: Optional[int] = None,
        agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ToolResult:
        """Run a tool and stream output in real-time via PTY."""
        spec = self.get_tool(tool_name)
        if not spec:
            return ToolResult(False, tool_name, command_name, "", error=f"Unknown tool: {tool_name}")

        if spec.implementation and not spec.executable_path:
            # Sync fallback for implementation-only tools (like web_search)
            res = self._run_implementation(spec, params, agent, session_id)
            if stream_callback and res.output:
                stream_callback(res.output)
            return res

        try:
            args = self.build_command_args(tool_name, command_name, params)
            tmpl = spec.commands[command_name]
            run_timeout = timeout or tmpl.timeout
            
            if stream_callback:
                stream_callback(f"🚀 Running: {' '.join(args)}\n")

            output_lines = []
            start_time = time.time()
            
            # Stream using internal PTY logic
            for line in self._stream_pty(args, timeout=run_timeout):
                output_lines.append(line)
                if stream_callback:
                    stream_callback(line)
            
            elapsed = time.time() - start_time
            output_str = "\n".join(output_lines)
            
            result = ToolResult(
                success=True, # PTY stream assume success if it finishes without exception
                tool=tool_name,
                command=command_name,
                output=output_str,
                elapsed_time=elapsed
            )
            
            # Parse result
            from app.tools.output_parsers import get_parser
            parser = get_parser(tool_name)
            result.parsed_data = parser(output_str)

            if stream_callback:
                stream_callback(f"\n✅ Completed in {elapsed:.2f}s")

            self._record_history(result, params, agent, session_id)
            return result

        except Exception as e:
            if stream_callback:
                stream_callback(f"\n❌ Error: {str(e)}")
            err_res = ToolResult(False, tool_name, command_name, "", error=str(e))
            self._record_history(err_res, params, agent, session_id)
            return err_res

    # ─────────────────────────────────────────────────────────────
    # Backward Compatibility Aliases
    # ─────────────────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Legacy alias for execute. Wraps result in a dict."""
        # Map parameters for specs if needed (handled in execute)
        command_name = kwargs.get("command_name", "default")
        # If tool_name has :command, split it
        if ":" in tool_name and command_name == "default":
            tool_name, command_name = tool_name.split(":", 1)
            
        res = self.execute(tool_name, command_name, parameters, **kwargs)
        return {
            "success": res.success,
            "results": res.parsed_data,
            "raw_output": res.output,
            "error": res.error,
            "execution_id": res.execution_id,
            "timestamp": res.timestamp
        }

    def execute_tool_streaming(self, tool_name: str, parameters: Dict[str, Any], stream_callback=None, **kwargs) -> Dict[str, Any]:
        """Legacy alias for execute_streaming."""
        command_name = kwargs.get("command_name", "default")
        if ":" in tool_name and command_name == "default":
            tool_name, command_name = tool_name.split(":", 1)
            
        res = self.execute_streaming(tool_name, command_name, parameters, stream_callback, **kwargs)
        return {
            "success": res.success,
            "results": res.parsed_data,
            "raw_output": res.output,
            "error": res.error,
            "execution_id": res.execution_id
        }

    # ─────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────

    def _run_implementation(self, spec: ToolSpec, params: Dict[str, Any], agent, session_id) -> ToolResult:
        """Runs a tool via its Python implementation path."""
        try:
            mod_name, func_name = spec.implementation.rsplit('.', 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            
            sig = inspect.signature(func)
            valid_params = {k: v for k, v in params.items() if k in sig.parameters}
            
            start_time = time.time()
            raw_res = func(**valid_params)
            elapsed = time.time() - start_time
            
            output = str(raw_res)
            success = True
            
            if isinstance(raw_res, dict) and "success" in raw_res:
                success = raw_res["success"]
                output = raw_res.get("raw_output", str(raw_res))

            res = ToolResult(success, spec.name, "default", output, elapsed_time=elapsed)
            res.parsed_data = raw_res if isinstance(raw_res, dict) else {"result": raw_res}
            
            self._record_history(res, params, agent, session_id)
            return res
        except Exception as e:
            return ToolResult(False, spec.name, "default", "", error=f"Implementation Error: {e}")

    def _stream_pty(self, command: List[str], timeout: int) -> Generator[str, None, None]:
        """PTY execution logic gauranteed to work on Linux/macOS, fallback on Windows."""
        if sys.platform == "win32":
            # Fallback for Windows
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                yield line.rstrip()
            process.wait()
            return

        import pty
        import errno
        master_fd, slave_fd = pty.openpty()
        
        try:
            process = subprocess.Popen(
                command, 
                stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
                close_fds=True, preexec_fn=os.setsid
            )
            os.close(slave_fd)
            
            start_time = time.time()
            buffer = []
            
            while True:
                if time.time() - start_time > timeout:
                    process.terminate()
                    yield "[TIMEOUT]"
                    break
                
                r, _, _ = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data: break
                        
                        decoded = data.decode('utf-8', errors='replace')
                        for char in decoded:
                            if char in ('\r', '\n'):
                                if buffer:
                                    yield "".join(buffer)
                                    buffer = []
                            else:
                                buffer.append(char)
                    except OSError as e:
                        if e.errno == errno.EIO: break # EOF on PTY
                        raise e
                elif process.poll() is not None:
                    break
        finally:
            try: os.close(master_fd)
            except: pass
            if buffer: yield "".join(buffer)

    def _record_history(self, result: ToolResult, params: Dict[str, Any], agent: str, session_id: str):
        """Append to in-memory history."""
        self.execution_history.append({
            "id": result.execution_id,
            "tool": result.tool,
            "command": result.command,
            "params": params,
            "success": result.success,
            "agent": agent,
            "session_id": session_id,
            "time": result.timestamp,
            "elapsed": result.elapsed_time
        })

    # ─────────────────────────────────────────────────────────────
    # Utility Methods (from CLIExecutor)
    # ─────────────────────────────────────────────────────────────

    def check_installed(self, binary: str) -> bool:
        return shutil.which(binary) is not None

    def parse_table(self, output: str, header_line: int = 0) -> List[Dict[str, str]]:
        lines = [l.strip() for l in output.split("\n") if l.strip()]
        if len(lines) <= header_line: return []
        headers = lines[header_line].split()
        rows = []
        for line in lines[header_line+1:]:
            vals = line.split()
            if len(vals) >= len(headers):
                rows.append({headers[i]: vals[i] for i in range(len(headers))})
        return rows


# Global Singleton
_executor: Optional[ToolExecutor] = None

def get_executor() -> ToolExecutor:
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
