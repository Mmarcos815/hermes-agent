import subprocess, json, threading, time, os

PY = "C:/Users/mobil/orca/projects/my 1st/venv/Scripts/python.exe"
PROJ = "C:/Users/mobil/orca/projects/my 1st"

SERVERS = [
    "mcp-servers/ad_attacks_mcp_server.py",
    "mcp-servers/ad_mcp_server.py",
    "mcp-servers/banking_mcp_server.py",
    "mcp-servers/cloud_attacks_mcp_server.py",
    "mcp-servers/cloud_mcp_server.py",
    "mcp-servers/elite_tools_mcp_server.py",
    "mcp-servers/mobile_mcp_server.py",
    "mcp-servers/osint_mcp_server.py",
    "mcp-servers/realworld_mcp_server.py",
    "mcp-servers/recon_mcp_server.py",
    "mcp-servers/redteam_mcp_server.py",
    "mcp-servers/research_mcp_server.py",
    "mcp-servers/starlink_mcp_server.py",
    "mcp-servers/unified_mcp_server.py",
    "mcp-servers/youtube_mcp_server.py",
    "bionic-core/bd_mcp/daughter_mcp_server.py",
    "bionic-core/bd_mcp/daughter_browser_mcp.py",
    "bionic-core/bd_mcp/daughter_cloud_mcp.py",
    "bionic-core/bd_mcp/daughter_communication_mcp.py",
    "bionic-core/bd_mcp/daughter_composio_mcp.py",
    "bionic-core/bd_mcp/daughter_database_mcp.py",
    "bionic-core/bd_mcp/daughter_filesystem_mcp.py",
    "bionic-core/bd_mcp/daughter_github_mcp_tools.py",
    "bionic-core/bd_mcp/daughter_hexstrike.py",
    "bionic-core/bd_mcp/daughter_productivity_mcp.py",
    "bionic-core/bd_mcp/daughter_web_search_mcp.py",
    "bionic-core/bd_mcp/daughter_youtube_mcp.py",
    "bionic-core/bd_mcp/formbot_mcp.py",
    "bionic-core/bd_mcp/payment_scanner_mcp.py",
    "redteam/nmap_mcp_server/server.py",
    "redteam/MCP_Red_Team_Agent/server.py",
    "redteam/autopentest-ai/server/server.py",
    "redteam/mcploit/server.py",
    "redteam/kali_mcp/server.py",
    "redteam/pentestMCP/server.py",
    "redteam/pentester-mcp/server.py",
    "redteam/exploitdb-mcp-server/server.py",
]

def read_lines(pipe, buf, stop):
    try:
        for line in iter(pipe.readline, ''):
            if line.strip():
                buf.append(line.strip())
            if stop.is_set():
                break
    except Exception:
        pass

def test_one(rel):
    path = os.path.join(PROJ, rel)
    proc = subprocess.Popen([PY, path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, cwd=PROJ)
    out, err = [], []
    stop = threading.Event()
    t1 = threading.Thread(target=read_lines, args=(proc.stdout, out, stop), daemon=True)
    t2 = threading.Thread(target=read_lines, args=(proc.stderr, err, stop), daemon=True)
    t1.start(); t2.start()
    try:
        proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 't', 'version': '1'}}}) + chr(10))
        proc.stdin.flush()
        time.sleep(3)
        proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': 2, 'method': 'notifications/initialized'}) + chr(10))
        proc.stdin.flush()
        time.sleep(1)
        proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': 3, 'method': 'tools/list', 'params': {}}) + chr(10))
        proc.stdin.flush()
        time.sleep(4)
    except Exception as e:
        stop.set()
        try: proc.kill()
        except Exception: pass
        return (rel, 'IOERR', 0, str(e)[:100])
    stop.set()
    try:
        proc.terminate(); proc.wait(timeout=3)
    except Exception:
        try: proc.kill()
        except Exception: pass
    time.sleep(0.5)
    tools = []
    crashed = any(('Traceback' in l) for l in err)
    for line in out:
        try: r = json.loads(line)
        except Exception: continue
        res = r.get('result', {})
        if isinstance(res, dict) and 'tools' in res:
            tools = [t.get('name', '?') for t in res['tools']]
    if tools and not crashed:
        return (rel, 'PASS', len(tools), ','.join(tools[:4]))
    if crashed:
        return (rel, 'CRASH', 0, (err[0] if err else '?')[:100])
    return (rel, 'NOTOOLS', 0, (err[0] if err else 'no output')[:100])

if __name__ == '__main__':
    total_tools = 0; npass = 0
    results = []
    for s in SERVERS:
        r = test_one(s)
        results.append(r)
        short = s.split('/')[-1]
        print(f'{r[1]:7} | {short:38} | n={r[2]:3} | {r[3][:80]}', flush=True)
        if r[1] == 'PASS': npass += 1; total_tools += r[2]
    print(f'{chr(10)}RESULT: {npass}/{len(SERVERS)} PASS, {total_tools} tools')