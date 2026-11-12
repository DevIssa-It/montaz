"""Terminal scene: run the demo command for real, keep its output for an animated card."""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_command(command: str, cwd: str, timeout: int = 25) -> dict[str, str]:
    """Run a shell command in the project folder; never raises on non-zero exit."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout + ("\n" + proc.stderr if proc.stderr.strip() else "")).strip()
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        output = f"(command timed out after {timeout}s)"
        returncode = -1
    except OSError as exc:
        output = f"(failed to run: {exc})"
        returncode = -1
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    return {"command": command, "lines": lines[:14], "returncode": returncode}
