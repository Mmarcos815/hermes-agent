#!/usr/bin/env python3
"""
subagent_dispatcher.py — Dispatch parallel subagents for hack missions.

Subagents:
- web_analyzer: Analyze web checkout pages
- apk_analyzer: Analyze APK files (endpoints, permissions, pinning)
- il2cpp_dumper: Dump IL2CPP metadata
- mitm_captor: Capture and analyze traffic
- frida_injector: Inject Frida scripts
- farm_operator: Run farm automation cycles

Usage:
    python subagent_dispatcher.py web_analyzer https://www.tcgplayer.com/login
    python subagent_dispatcher.py apk_analyzer farm_3phones/apks/mintpull.apk
    python subagent_dispatcher.py farm_operator tcgp_pull_cycle
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")
HACK_SERVER = WORKSPACE / "hack_mcp_server"
TOOL_CALLER = WORKSPACE / "tool_caller"


class SubagentDispatcher:
    """Dispatch and manage subagents."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results = {}
    
    def dispatch(self, agent_type: str, target: str, **kwargs) -> Dict:
        """Dispatch a subagent."""
        agents = {
            "web_analyzer": self._web_analyzer,
            "apk_analyzer": self._apk_analyzer,
            "il2cpp_dumper": self._il2cpp_dumper,
            "mitm_captor": self._mitm_captor,
            "frida_injector": self._frida_injector,
            "farm_operator": self._farm_operator,
        }
        
        if agent_type not in agents:
            return {"error": f"Unknown agent: {agent_type}", "available": list(agents.keys())}
        
        return agents[agent_type](target, **kwargs)
    
    def dispatch_parallel(self, tasks: List[Dict]) -> Dict:
        """Dispatch multiple subagents in parallel."""
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for task in tasks:
                agent_type = task.get("agent")
                target = task.get("target")
                kwargs = task.get("kwargs", {})
                future = executor.submit(self.dispatch, agent_type, target, **kwargs)
                futures[future] = f"{agent_type}:{target}"
            
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    results[task_name] = future.result()
                except Exception as e:
                    results[task_name] = {"error": str(e)}
        
        return results
    
    def _web_analyzer(self, url: str, **kwargs) -> Dict:
        """Run web analyzer subagent."""
        script = HACK_SERVER / "web_analyzer.py"
        if not script.exists():
            return {"error": "web_analyzer.py not found"}
        
        result = subprocess.run(
            [sys.executable, str(script), url],
            capture_output=True, text=True, timeout=60
        )
        return {"output": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
    
    def _apk_analyzer(self, apk_path: str, **kwargs) -> Dict:
        """Run APK analyzer subagent."""
        sys.path.insert(0, str(HACK_SERVER))
        from server import scan_apk_endpoints
        
        endpoints = scan_apk_endpoints(apk_path)
        
        # Also decode and analyze
        decoded_dir = WORKSPACE / "temp_decoded"
        decoded_dir.mkdir(exist_ok=True)
        
        return {
            "endpoints": endpoints,
            "decoded_dir": str(decoded_dir),
            "apk_path": apk_path
        }
    
    def _il2cpp_dumper(self, apk_path: str, **kwargs) -> Dict:
        """Run IL2CPP dumper subagent."""
        output_dir = WORKSPACE / "il2cpp_output"
        output_dir.mkdir(exist_ok=True)
        
        result = subprocess.run(
            [sys.executable, str(HACK_SERVER / "server.py"), "dump_il2cpp", apk_path, str(output_dir)],
            capture_output=True, text=True, timeout=120
        )
        return {"output": result.stdout + result.stderr, "output_dir": str(output_dir)}
    
    def _mitm_captor(self, serial: str, duration: int = 30, **kwargs) -> Dict:
        """Run MITM capture subagent."""
        sys.path.insert(0, str(HACK_SERVER))
        from server import start_mitm_capture, stop_mitm_capture
        
        # Start capture
        capture = start_mitm_capture(port=8082, output_file=str(WORKSPACE / "capture.mitm"))
        pid = capture.get("pid")
        
        import time
        time.sleep(duration)
        
        # Stop capture
        stop_mitm_capture(pid)
        
        return {"capture_file": str(WORKSPACE / "capture.mitm"), "duration": duration, "pid": pid}
    
    def _frida_injector(self, serial: str, package: str, **kwargs) -> Dict:
        """Run Frida injector subagent."""
        sys.path.insert(0, str(HACK_SERVER))
        from server import push_frida_gadget, push_frida_script, start_frida_server
        
        results = {}
        results["gadget"] = push_frida_gadget(serial)
        results["script"] = push_frida_script(serial)
        results["server"] = start_frida_server(serial)
        
        return results
    
    def _farm_operator(self, cycle_type: str, **kwargs) -> Dict:
        """Run farm operator subagent."""
        sys.path.insert(0, str(WORKSPACE))
        from farm_ctrl import FarmOrchestrator
        
        farm = FarmOrchestrator()
        
        if cycle_type == "tcgp_pull_cycle":
            farm.run_tcgp_cycle()
        elif cycle_type == "outpost_free_pulls":
            farm.run_outpost_cycle()
        elif cycle_type == "status":
            farm.status()
        
        return {"cycle": cycle_type, "status": "complete"}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python subagent_dispatcher.py <agent_type> <target>")
        print("Agents: web_analyzer, apk_analyzer, il2cpp_dumper, mitm_captor, frida_injector, farm_operator")
        print("Example: python subagent_dispatcher.py web_analyzer https://www.tcgplayer.com/login")
        sys.exit(1)
    
    dispatcher = SubagentDispatcher()
    result = dispatcher.dispatch(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
