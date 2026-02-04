"""Tool implementations with subprocess streaming.

Bridge to the consolidated ToolExecutor.
"""

from app.tools.executor import get_executor

def get_cli_executor():
    """Returns the unified ToolExecutor."""
    return get_executor()

def run_cli_command(cmd, **kwargs):
    """Bridge to execute_tool."""
    # Note: old cli_executor.run takes cmd as first arg. 
    # execute_tool expects tool_name as first arg.
    # This might need careful mapping if used widely.
    # For now, we assume cmd[0] is the tool name if it's a list.
    tool_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
    return get_executor().execute_tool(tool_name=tool_name, parameters=kwargs.get("params", {}), **kwargs)

def check_tool_installed(binary: str) -> bool:
    """Checks if a tool is installed."""
    return get_executor().check_installed(binary)

def get_tool_path(binary: str) -> str:
    """Gets the path of the tool."""
    import shutil
    return shutil.which(binary)

__all__ = [
    "get_cli_executor", 
    "run_cli_command",
    "check_tool_installed",
    "get_tool_path"
]
