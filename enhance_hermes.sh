#!/usr/bin/env bash
# ==============================================================================
# Orca ADE / Hermes Agent - Multi-Device Traffic Inspection Master Script
# Target Environment: Orca ADE 8 / Kali Linux
# ==============================================================================

set -e

echo "[*] Initializing Orca ADE 8 framework and device alignment..."

# 1. Reset ADB server and reconnect target devices
echo "[*] Resetting ADB bridge..."
adb kill-server
adb start-server

# Reconnect Phone-01 and Phone-02 (Update ports if necessary from pairing prompts)
echo "[*] Connecting to active Android devices..."
adb connect 192.168.1.157:45313 || true
adb connect 192.168.1.158:35493 || true
adb devices

# 2. Deploy custom Hermes Python skill package for traffic analysis inside Orca ADE 8
SKILLS_DIR="$HOME/.hermes/skills/traffic_analyzer"
mkdir -p "$SKILLS_DIR"

cat << 'EOF' > "$SKILLS_DIR/skill.py"
import json
import os

class TrafficAnalyzerSkill:
    def __init__(self, log_path="/tmp/mitm_flows.json"):
        self.log_path = log_path

    def inspect_latest_flows(self, max_records=10):
        if not os.path.exists(self.log_path):
            return {"error": "Flow log not found. Ensure mitmweb/mitmproxy is active."}
        
        with open(self.log_path, "r") as f:
            lines = f.readlines()
        
        records = [json.loads(line) for line in lines[-max_records:]]
        return {"active_flows_inspected": len(records), "records": records}

if __name__ == "__main__":
    skill = TrafficAnalyzerSkill()
    print(json.dumps(skill.inspect_latest_flows(), indent=2))
EOF

cat << 'EOF' > "$SKILLS_DIR/manifest.json"
{
  "name": "traffic_analyzer",
  "version": "1.0.0",
  "description": "Custom skill to parse active proxy flows and HTTP JSON payloads for Hermes inside Orca ADE 8.",
  "entrypoint": "skill.py"
}
EOF

echo "[+] Custom skill package 'traffic_analyzer' successfully deployed for Orca ADE 8."

# 3. Setup Subagent Orchestration Helper
HELPER_DIR="$HOME/.hermes/helpers"
mkdir -p "$HELPER_DIR"

cat << 'EOF' > "$HELPER_DIR/subagent_spawn.py"
import sys
import subprocess

def spawn_subagent(task_prompt):
    print(f"[*] Spawning isolated Hermes child subagent for task: {task_prompt}")
    cmd = ["hermes", "run", "--subagent", "--prompt", task_prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(spawn_subagent(" ".join(sys.argv[1:])))
    else:
        print("Usage: python3 subagent_spawn.py '<task description>'")
EOF

echo "[+] Subagent helper script installed."
echo "[*] Orca ADE 8 master sequence complete. Ready for execution."
