import asyncio
import os
import subprocess
import tempfile
from typing import Any, Dict
from .security import ToolExecutorInterface, ToolPermissions, Capability, AuditLog
from .telemetry import StructuredLogger

class SandboxToolExecutor(ToolExecutorInterface):
    def __init__(self):
        self.logger = StructuredLogger("tool_executor")

    async def execute(self, tool_name: str, args: Dict[str, Any], permissions: ToolPermissions) -> Any:
        # 1. Capability Check
        required_cap = self._get_required_capability(tool_name)
        if required_cap not in permissions.allowed_capabilities:
            self.logger.error(f"Permission denied for tool {tool_name}", required_cap=required_cap)
            raise PermissionError(f"Missing capability: {required_cap}")

        # 2. Execution in Sandbox
        self.logger.info(f"Executing tool {tool_name} in sandbox", tool_name=tool_name)
        
        try:
            # In a real system, this would spin up a gVisor/Firecracker VM or Docker container
            # Here we'll use a temporary directory and a restricted subprocess as a proxy
            with tempfile.TemporaryDirectory() as tmpdir:
                # Mock execution logic
                if tool_name == "shell_command":
                    cmd = args.get("cmd")
                    # DANGEROUS: Just for demonstration. In reality, we'd use a real sandbox.
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=tmpdir, timeout=10)
                    output = result.stdout + result.stderr
                    success = result.returncode == 0
                else:
                    output = f"Executed {tool_name} with {args}"
                    success = True

                # 3. Audit Logging
                log = AuditLog(
                    timestamp=asyncio.get_event_loop().time(),
                    caller_id="orchestrator", # Should be passed in
                    tool_name=tool_name,
                    arguments=args,
                    capabilities_used=[required_cap],
                    result_summary=output[:100],
                    success=success
                )
                self._write_audit_log(log)
                
                return output

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}", tool_name=tool_name)
            raise

    def _get_required_capability(self, tool_name: str) -> Capability:
        # Mapping tool names to capabilities
        mapping = {
            "shell_command": Capability.SHELL_EXEC,
            "read_file": Capability.FS_READ,
            "write_file": Capability.FS_WRITE,
            "fetch_url": Capability.NET_OUTBOUND
        }
        return mapping.get(tool_name, Capability.FS_READ) # Default to safest

    def _write_audit_log(self, log: AuditLog):
        # In production, write to an immutable ledger/database
        with open("audit_log.jsonl", "a") as f:
            f.write(log.model_dump_json() + "\n")
