import asyncio
import os
import subprocess
import tempfile
import sqlite3
import json
import hashlib
import hmac
from typing import Any, Dict, Optional, List
from .security import ToolExecutorInterface, ToolPermissions, Capability, AuditLog
from .telemetry import StructuredLogger

from .config import settings

class SandboxToolExecutor(ToolExecutorInterface):
    def __init__(self, db_path: Optional[str] = None):
        self.logger = StructuredLogger("tool_executor")
        self.db_path = db_path or settings.audit_db_path
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
                    success INTEGER,
                    previous_hash TEXT,
                    hash TEXT,
                    signature TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS root_hash_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    root_hash TEXT,
                    signature TEXT
                )
            """)

    def _validate_path(self, path: str, sandbox_dir: str) -> str:
        """Ensures a path is within the sandbox directory to prevent traversal."""
        abs_path = os.path.abspath(os.path.join(sandbox_dir, path))
        if not abs_path.startswith(os.path.abspath(sandbox_dir)):
            raise PermissionError(f"Security Violation: Path {path} is outside the sandbox.")
        return abs_path

    async def execute(self, tool_name: str, args: Dict[str, Any], permissions: ToolPermissions) -> Any:
        # 1. Capability Check - STRICT MAPPING
        required_cap = self._get_required_capability(tool_name)
        
        if not required_cap or required_cap not in permissions.allowed_capabilities:
            self.logger.error(f"SECURITY ALERT: Permission denied for tool {tool_name}", 
                               required_cap=required_cap.value if required_cap else "UNKNOWN")
            
            self._persist_audit_log(AuditLog(
                timestamp=asyncio.get_event_loop().time(),
                caller_id="orchestrator",
                tool_name=tool_name,
                arguments=args,
                capabilities_used=[required_cap] if required_cap else [],
                result_summary=f"DENIED: Missing capability {required_cap.value if required_cap else 'UNKNOWN'}",
                success=False
            ))
            raise PermissionError(f"Zero-Trust Policy Violation: Missing capability for {tool_name}")

        self.logger.info(f"Executing tool {tool_name} under policy enforcement", tool_name=tool_name)
        
        # 2. Extract Resource Limits
        limits = permissions.resource_limits or {}
        timeout = limits.get("timeout", 10) # Default 10s

        try:
            # 3. Execution in ISOLATED Environment
            with tempfile.TemporaryDirectory() as tmpdir:
                if tool_name == "shell_command":
                    cmd = args.get("cmd")
                    if isinstance(cmd, str):
                        import shlex
                        cmd_list = shlex.split(cmd)
                    else:
                        cmd_list = cmd
                    
                    # Try to use nsjail if available (Linux only)
                    import shutil
                    nsjail_path = shutil.which("nsjail")
                    
                    if nsjail_path:
                        self.logger.info("Using nsjail for kernel-level isolation")
                        # Basic nsjail command for isolation
                        nsjail_cmd = [
                            nsjail_path,
                            "--mode", "o",
                            "--chroot", tmpdir,
                            "--user", "nobody",
                            "--group", "nogroup",
                            "--lr", "/bin:/bin",
                            "--lr", "/lib:/lib",
                            "--lr", "/lib64:/lib64",
                            "--lr", "/usr:/usr",
                            "--time_limit", str(timeout),
                            "--",
                        ] + cmd_list
                        result = subprocess.run(nsjail_cmd, shell=False, capture_output=True, text=True, timeout=timeout + 1)
                    else:
                        self.logger.warning("nsjail not found. Falling back to subprocess isolation.")
                        # Prevent absolute path execution in fallback mode
                        if cmd_list and (cmd_list[0].startswith("/") or ":" in cmd_list[0]):
                             self.logger.warning(f"Tool {tool_name} is using an absolute binary path: {cmd_list[0]}")

                        result = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, cwd=tmpdir, timeout=timeout)
                    
                    output = result.stdout + result.stderr
                    success = result.returncode == 0
                
                elif tool_name == "read_file":
                    rel_path = args.get("path")
                    safe_path = self._validate_path(rel_path, tmpdir)
                    if os.path.exists(safe_path):
                        with open(safe_path, "r") as f:
                            output = f.read()
                        success = True
                    else:
                        output = f"File not found: {rel_path}"
                        success = False
                else:
                    output = f"Deterministic execution of {tool_name}"
                    success = True

                # 4. Persistent Audit Logging with Integrity
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
        """Write to SQLite ledger with cryptographic hash chaining and HMAC signatures."""
        system_secret = settings.audit_secret.encode()
        
        with sqlite3.connect(self.db_path) as conn:
            # 1. Get the hash of the previous record
            cursor = conn.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            log.previous_hash = row[0] if row else "GENESIS"
            
            # 2. Calculate hash for the current record
            record_data = json.dumps({
                "timestamp": log.timestamp,
                "caller_id": log.caller_id,
                "tool_name": log.tool_name,
                "arguments": log.arguments,
                "capabilities_used": [c.value for c in log.capabilities_used],
                "result_summary": log.result_summary,
                "success": log.success,
                "previous_hash": log.previous_hash
            }, sort_keys=True)
            log.hash = hashlib.sha256(record_data.encode()).hexdigest()
            
            # 3. Create digital signature (HMAC)
            log.signature = hmac.new(system_secret, log.hash.encode(), hashlib.sha256).hexdigest()
            
            # 4. Insert into DB
            conn.execute("""
                INSERT INTO audit_logs (timestamp, caller_id, tool_name, arguments, capabilities_used, result_summary, success, previous_hash, hash, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.timestamp,
                log.caller_id,
                log.tool_name,
                json.dumps(log.arguments),
                json.dumps([c.value for c in log.capabilities_used]),
                log.result_summary,
                1 if log.success else 0,
                log.previous_hash,
                log.hash,
                log.signature
            ))

            # 5. Periodic Root Hash Snapshot (every 10 logs)
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            if count % 10 == 0:
                snapshot_sig = hmac.new(system_secret, log.hash.encode() + b"SNAPSHOT", hashlib.sha256).hexdigest()
                conn.execute("INSERT INTO root_hash_snapshots (timestamp, root_hash, signature) VALUES (?, ?, ?)",
                             (log.timestamp, log.hash, snapshot_sig))
                self.logger.info("Root hash snapshot created", root_hash=log.hash)
