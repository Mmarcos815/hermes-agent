# ============================================================================
# BIONIC DAUGHTER v1 — CLOUD / PLATFORM MCP SERVER
# ============================================================================
# MCP server providing cloud platform and infrastructure capabilities.
# Covers: Docker container management, system info, environment monitoring.
# Safety: Docker operations require authorization; system info is read-only.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import subprocess
import json
from mcp.server.fastmcp import FastMCP

app = FastMCP("daughter_cloud")


def _run_cmd(cmd: str, timeout: int = 30) -> str:
    """Run a shell command and return output. Used for Docker/system operations."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return f"ERROR (exit {result.returncode}): {result.stderr.strip()}"
        return result.stdout.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def docker_info() -> str:
    """Get Docker environment information."""
    result = "Docker MCP — Bionic Daughter v1\n"
    result += "======================================\n"
    # Check if docker is available
    check = _run_cmd("docker --version 2>&1", timeout=5)
    if check.startswith("ERROR"):
        result += f"Docker CLI: NOT AVAILABLE ({check})\n"
    else:
        result += f"Docker CLI: {check.split(chr(10))[0]}\n"
    # Check if docker daemon is running
    ps = _run_cmd("docker info 2>&1 | head -3", timeout=10)
    if "error" in ps.lower() or "cannot connect" in ps.lower():
        result += "Docker daemon: NOT RUNNING (daemon not reachable)\n"
    else:
        result += "Docker daemon: RUNNING\n"
    result += "\nDocker tools available:\n"
    result += "  docker_ps — List running containers\n"
    result += "  docker_images — List available images\n"
    result += "  docker_exec — Execute command in a container (requires authorization)\n"
    result += "  docker_logs — Get container logs\n"
    result += "  docker_run — Run a container (requires authorization)\n"
    result += "  docker_stop — Stop a container (requires authorization)\n"
    result += "  docker_rm — Remove a container (requires authorization)\n"
    result += "  docker_info — This info\n"
    return result


@app.tool()
def docker_ps(all_containers: bool = False) -> str:
    """List Docker containers."""
    flag = "--all" if allContainers else ""
    return _run_cmd(f"docker ps {flag} 2>&1", timeout=10)


@app.tool()
def docker_images() -> str:
    """List available Docker images."""
    return _run_cmd("docker images 2>&1", timeout=10)


@app.tool()
def docker_logs(container: str, lines: int = 50) -> str:
    """Get logs from a Docker container."""
    return _run_cmd(f"docker logs --tail {lines} {container} 2>&1", timeout=15)


@app.tool()
def docker_exec(container: str, command: str, authorize: bool = False) -> str:
    """Execute a command inside a Docker container. Requires authorization."""
    if not authorize:
        return "ERROR: Docker exec authorization required. Set authorize=true with Dad's approval."
    return _run_cmd(f"docker exec {container} {command} 2>&1", timeout=30)


@app.tool()
def docker_run(image: str, command: str = "", detach: bool = True, authorize: bool = False) -> str:
    """Run a Docker container. Requires authorization."""
    if not authorize:
        return "ERROR: Docker run authorization required. Set authorize=true with Dad's approval."
    parts = f"docker run"
    if detach:
        parts += " -d"
    if command:
        parts += f" {image} {command}"
    else:
        parts += f" {image}"
    return _run_cmd(parts, timeout=30)


@app.tool()
def docker_stop(container: str, authorize: bool = False) -> str:
    """Stop a Docker container. Requires authorization."""
    if not authorize:
        return "ERROR: Docker stop authorization required. Set authorize=true."
    return _run_cmd(f"docker stop {container} 2>&1", timeout=15)


@app.tool()
def docker_rm(container: str, authorize: bool = False, force: bool = False) -> str:
    """Remove a Docker container. Requires authorization."""
    if not authorize:
        return "ERROR: Docker rm authorization required. Set authorize=true."
    flag = "-f" if force else ""
    return _run_cmd(f"docker rm {flag} {container} 2>&1", timeout=15)


@app.tool()
def system_info() -> str:
    """Get system information (read-only, safe)."""
    result = "System Information — Bionic Daughter v1\n"
    result += "============================================\n"

    # OS
    try:
        result += f"OS: {os.name} — {os.uname().sysname if hasattr(os, 'uname') else 'Unknown'}\n"
    except:
        result += "OS: Unknown\n"

    # Platform
    result += f"Platform: Windows\n"

    # Python
    import sys

    result += f"Python: {sys.version}\n"

    # Environment
    result += f"User: {os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))}\n"
    result += f"Home: {os.environ.get('HOME', os.environ.get('USERPROFILE', 'unknown'))}\n"

    # Working directory
    result += f"Working dir: {os.getcwd()}\n"

    # Project directory check
    project = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent"
    if os.path.isdir(project):
        result += f"Project dir: EXISTS ({project})\n"
        # Count files
        count = sum(1 for _ in os.listdir(project))
        result += f"Project files: {count}\n"
    else:
        result += "Project dir: NOT FOUND\n"

    # GPU check
    try:
        import torch

        result += f"PyTorch: {torch.__version__}\n"
        result += f"CUDA available: {torch.cuda.is_available()}\n"
        if torch.cuda.is_available():
            result += f"GPU: {torch.cuda.get_device_name(0)}\n"
        else:
            result += "GPU: NONE (CPU only)\n"
    except:
        result += "PyTorch: NOT INSTALLED\n"

    return result


@app.tool()
def env_vars(keys: str = "") -> str:
    """Show environment variables. If keys provided, show only those."""
    if keys:
        key_list = [k.strip() for k in keys.split(",")]
        result = ""
        for k in key_list:
            val = os.environ.get(k, "NOT SET")
            # Mask sensitive values
            if any(s in k.lower() for s in ["key", "secret", "token", "password", "api"]):
                if val and len(val) > 4:
                    val = val[:4] + "***"
            result += f"{k}: {val}\n"
        return result
    else:
        # Show all non-sensitive env vars
        result = "Environment Variables:\n"
        for k, v in sorted(os.environ.items()):
            if any(s in k.lower() for s in ["key", "secret", "token", "password", "api"]):
                if v and len(v) > 4:
                    v = v[:4] + "***"
            result += f"  {k}: {v}\n"
        return result


@app.tool()
def disk_usage(path: str = ".") -> str:
    """Show disk usage for a path."""
    try:
        full = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
        if not os.path.exists(full):
            return f"ERROR: Path not found: {path}"
        total_size = 0
        file_count = 0
        dir_count = 0
        for dirpath, dirnames, filenames in os.walk(full):
            dir_count += len(dirnames)
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
                    file_count += 1
        size_mb = total_size / (1024 * 1024)
        return (
            f"Path: {full}\n"
            f"Files: {file_count}\n"
            f"Directories: {dir_count}\n"
            f"Total size: {total_size} bytes ({size_mb:.2f} MB)\n"
        )
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def cloud_info() -> str:
    """Show cloud/platform MCP information."""
    return (
        "Cloud / Platform MCP — Bionic Daughter v1\n"
        "================================================\n"
        "This MCP provides cloud and infrastructure capabilities.\n"
        "\n"
        "Docker (when Docker is available):\n"
        "  docker_info — Docker environment info\n"
        "  docker_ps — List containers\n"
        "  docker_images — List images\n"
        "  docker_logs(container, lines) — Container logs\n"
        "  docker_exec(container, command, authorize) — Exec in container\n"
        "  docker_run(image, command, detach, authorize) — Run container\n"
        "  docker_stop(container, authorize) — Stop container\n"
        "  docker_rm(container, authorize, force) — Remove container\n"
        "\n"
        "System (read-only):\n"
        "  system_info — System information\n"
        "  env_vars(keys) — Environment variables\n"
        "  disk_usage(path) — Disk usage for a path\n"
        "\n"
        "Note: Docker daemon is NOT running on this machine.\n"
        "      Docker tools require Docker to be available.\n"
        "      Sandbox_lab is set up for Dad to start Docker.\n"
    )


if __name__ == "__main__":
    app.run()
