import pytest
import asyncio
import os
import sqlite3
import platform
from shared.executor import SandboxToolExecutor
from shared.security import ToolPermissions, Capability

@pytest.fixture
def executor(tmp_path):
    db_path = tmp_path / "test_audit.db"
    return SandboxToolExecutor(db_path=str(db_path))

@pytest.mark.asyncio
async def test_execute_allowed_tool(executor):
    permissions = ToolPermissions(allowed_capabilities=[Capability.SHELL_EXEC])
    
    # Use platform-appropriate command
    if platform.system() == "Windows":
        cmd = "cmd /c echo hello"
    else:
        cmd = "echo hello"
    
    args = {"cmd": cmd}
    
    result = await executor.execute("shell_command", args, permissions)
    assert "hello" in result
    
    # Check audit log
    with sqlite3.connect(executor.db_path) as conn:
        logs = conn.execute("SELECT tool_name, success FROM audit_logs").fetchall()
        assert len(logs) == 1
        assert logs[0][0] == "shell_command"
        assert logs[0][1] == 1

@pytest.mark.asyncio
async def test_execute_denied_tool(executor):
    # Only allow FS_READ, but try SHELL_EXEC
    if platform.system() == "Windows":
        cmd = "cmd /c echo hello"
    else:
        cmd = "echo hello"
    
    permissions = ToolPermissions(allowed_capabilities=[Capability.FS_READ])
    args = {"cmd": cmd}
    
    with pytest.raises(PermissionError, match="Zero-Trust Policy Violation"):
        await executor.execute("shell_command", args, permissions)
    
    # Check audit log
    with sqlite3.connect(executor.db_path) as conn:
        logs = conn.execute("SELECT tool_name, success FROM audit_logs").fetchall()
        assert len(logs) == 1
        assert logs[0][1] == 0

@pytest.mark.asyncio
async def test_execute_unknown_tool(executor):
    permissions = ToolPermissions(allowed_capabilities=[Capability.SHELL_EXEC])
    args = {}
    
    with pytest.raises(PermissionError, match="Zero-Trust Policy Violation"):
        await executor.execute("unknown_tool", args, permissions)
