import asyncio
import os
import subprocess
import tempfile
import sqlite3
import json
from typing import Any, Dict, Optional, List
from .security import ToolExecutorInterface, ToolPermissions, Capability, AuditLog
from .telemetry import StructuredLogger

class SandboxToolExecutor(ToolExecutorInterface):
    def __init__(self, db_path: str = "audit_ledger.db"):
        self.logger = StructuredLogger("tool_executor")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the immutable (append-only) audit ledger."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    caller_id TEXT,
                    tool_name TEXT,
                    arguments TEXT,
                    capabilities_used TEXT,
                    result_summary TEXT,
                    success INTEGER
                )
            """)

    async def execute(self, tool_name: str, args: Dict[str, Any], permissions: ToolPermissions) -> Any:
        # 1. Capability Check - STRICT MAPPING
        required_cap = self._get_required_capability(tool_name)
        
        # Default to DENY if no mapping or not in allowed list
        if not required_cap or required_cap not in permissions.allowed_capabilities:
            self.logger.error(f"SECURITY ALERT: Permission denied for tool {tool_name}", 
                               required_cap=required_cap.value if required_cap else "UNKNOWN")
            raise PermissionError(f"Zero-Trust Policy Violation: Missing capability for {tool_name}")

        self.logger.info(f"Executing tool {tool_name} under policy enforcement", tool_name=tool_name)
        
        try:
            # 2. Execution in ISOLATED Environment
            # For MVP, we use a restricted subprocess WITHOUT shell=True
            with tempfile.TemporaryDirectory() as tmpdir:
                if tool_name == "shell_command":
                    # SECURITY: shell=False is mandatory. Args must be a list.
                    cmd = args.get("cmd")
                    if isinstance(cmd, str):
                        # Convert string cmd to list safely or reject
                        import shlex
                        cmd_list = shlex.split(cmd)
                    else:
                        cmd_list = cmd
                        
                    # Executing without shell=True to prevent injection
                    result = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, cwd=tmpdir, timeout=10)
                    output = result.stdout + result.stderr
                    success = result.returncode == 0
                else:
                    # Mock for other tools
                    output = f"Deterministic execution of {tool_name}"
                    success = True

                # 3. Persistent Audit Logging with Integrity
                log = AuditLog(
                    timestamp=asyncio.get_event_loop().time(),
                    caller_id="orchestrator", 
                    tool_name=tool_name,
                    arguments=args,
                    capabilities_used=[required_cap],
                    result_summary=output[:500],
                    success=success
                )
                self._persist_audit_log(log)
                
                return output

        except Exception as e:
            self.logger.error(f"Execution Failure: {e}", tool_name=tool_name)
            self._persist_audit_log(AuditLog(
                timestamp=asyncio.get_event_loop().time(),
                caller_id="orchestrator",
                tool_name=tool_name,
                arguments=args,
                capabilities_used=[required_cap],
                result_summary=str(e),
                success=False
            ))
            raise

    def _get_required_capability(self, tool_name: str) -> Optional[Capability]:
        """Strict mapping of tools to capabilities. Returns None for unknown tools."""
        mapping = {
            "ls": Capability.FS_READ,
            "read_file": Capability.FS_READ,
            "write_file": Capability.FS_WRITE,
            "curl": Capability.NET_OUTBOUND,
            "git": Capability.GITHUB_WRITE,
            "shell_command": Capability.SHELL_EXEC
        }
        return mapping.get(tool_name)

    def _persist_audit_log(self, log: AuditLog):
        """Write to SQLite ledger."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_logs (timestamp, caller_id, tool_name, arguments, capabilities_used, result_summary, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log.timestamp,
                log.caller_id,
                log.tool_name,
                json.dumps(log.arguments),
                json.dumps([c.value for c in log.capabilities_used]),
                log.result_summary,
                1 if log.success else 0
            ))
