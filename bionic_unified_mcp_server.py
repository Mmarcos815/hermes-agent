#!/usr/bin/env python3
"""
Bionic Unified FastMCP Suite Server (bionic_unified_mcp_server.py)
Unifies our entire arsenal of custom protocol engines, security tools, and simulators
into a single, high-leverage FastMCP stdio server for Hermes, Orca ADE, and Claude Code.

Registered Tools:
1. bionic_iso8583_auth_sim: Execute full ISO 8583 + EMV Field 55 + Tokenization auth transaction.
2. bionic_iso20022_transfer: Process ISO 20022 pacs.008 payment & generate pacs.002 status report.
3. bionic_three_ds_evaluate: Simulate 3D Secure 2.2 risk evaluation (Frictionless vs. Challenge).
4. bionic_web3_fuzz_contract: Run invariant & solvency sequence fuzzing on smart contracts.
5. bionic_security_port_scan: Run concurrent TCP socket prober on target host.
6. bionic_security_http_audit: Audit web endpoint security headers (HSTS, CSP, X-Frame).
7. bionic_solidity_audit: Scan Solidity contract source code for reentrancy, oracle, and access bugs.
8. bionic_statement_ocr: Extract and reconcile tabular financial data from document images.
"""

import sys, os, json
from mcp.server.fastmcp import FastMCP

# Add root directory to sys.path
ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from unified_payment_gateway import UnifiedPaymentGateway, ISO8583Message
from iso20022_engine import ISO20022Engine
from three_ds_simulator import ThreeDSServer, DirectoryServer, AccessControlServer
from web3_contract_fuzzer import SmartContractFuzzer
from hexstrike_live_server import live_port_scan, live_http_audit, live_endpoint_probe
from solidity_audit_scanner import SolidityAuditScanner
from financial_table_extractor import FinancialTableExtractor

app = FastMCP("bionic-unified-suite")

# Wire in production MCP primitives (resources + prompts) from learning project 03
try:
    import sys as _sys
    _sys.path.insert(0, r"C:\Users\mobil\orca\projects\my 1st\learning\03_production_mcp")
    from production_mcp_extension import register_production_primitives
    register_production_primitives(app)
    print("[bionic_unified] production MCP primitives wired (resources + prompts)", file=sys.stderr)
except Exception as e:
    print(f"[bionic_unified] could not wire production primitives: {e}", file=sys.stderr)

# ── 1. ISO 8583 & Tokenization Gateway Tool ────────────────────────────────

@app.tool()
def bionic_iso8583_auth_sim(dpan: str = "4800112233445566", amount_cents: int = 15000, stan: str = "123456") -> str:
    """Simulates an ISO 8583 card authorization request with EMV Field 55 cryptogram & Apple Pay detokenization."""
    gateway = UnifiedPaymentGateway()
    req = ISO8583Message(mti="0100")
    req.set_field(2, dpan)
    req.set_field(3, "000000")
    req.set_field(4, f"{amount_cents:012d}")
    req.set_field(7, "0828080000")
    req.set_field(11, stan)
    req.set_field(41, "TERM0001") # Exactly 8 chars for DE 41 fixed ans length
    req.set_field(49, "840") # USD
    
    # EMV Field 55 BER-TLV Cryptogram Payload (LLLVAR in DE 48)
    f55_hex = "9F26084B73A862803893C59F2701809F3602001F9F02060000000150005F2A020840"
    req.set_field(48, f55_hex)

    resp_bytes, audit = gateway.process_authorization(req.pack())
    resp_msg = ISO8583Message.unpack(resp_bytes)

    return json.dumps({
        "status": "APPROVED" if resp_msg.get_field(39) == "00" else "DECLINED",
        "response_code": resp_msg.get_field(39),
        "auth_code": resp_msg.get_field(38),
        "balance_ledger_tag": resp_msg.get_field(54),
        "audit_trace": audit
    }, indent=2)


# ── 2. ISO 20022 pacs.008 / pacs.002 Engine Tool ───────────────────────────

@app.tool()
def bionic_iso20022_transfer(debtor_iban: str = "GR1601101250000001234567890", creditor_iban: str = "US33FEDN0100000009876543210", amount: float = 2500.0, currency: str = "EUR") -> str:
    """Generates, validates, and settles an ISO 20022 pacs.008 credit transfer, emitting pacs.002 status."""
    engine = ISO20022Engine()
    xml_req = engine.generate_pacs008(debtor_iban, "ETHNGRAA", creditor_iban, "BOFAUS3N", amount, currency)
    parsed = engine.parse_pacs008(xml_req)
    xml_resp, audit = engine.process_and_generate_pacs002(parsed)

    return json.dumps({
        "iso20022_status": audit["transaction_status"],
        "reason_code": audit["reason_code"],
        "reason_description": audit["reason_meaning"],
        "settled_amount": audit["settled_amount"],
        "remaining_balance": audit["remaining_balance"],
        "uetr": audit["uetr"]
    }, indent=2)


# ── 3. 3D Secure 2.2 Protocol Simulator Tool ───────────────────────────────

@app.tool()
def bionic_three_ds_evaluate(pan: str = "4111111111111111", amount_cents: int = 4500, mcc: str = "5411") -> str:
    """Evaluates 3DS 2.2 risk scoring and returns frictionless (Y) or challenge (C) decision with CAVV and ECI."""
    acs = AccessControlServer()
    ds = DirectoryServer(acs)
    three_ds = ThreeDSServer(ds)
    
    ares = three_ds.initiate_authentication(
        merchant_id="MERCH-BIONIC",
        pan=pan,
        amount_cents=amount_cents,
        currency="840",
        mcc=mcc
    )
    return json.dumps(ares, indent=2)


# ── 4. Web3 Smart Contract Invariant Fuzzer Tool ────────────────────────────

@app.tool()
def bionic_web3_fuzz_contract(runs: int = 150) -> str:
    """Executes property-based invariant and solvency sequence fuzzing across DeFi smart contract states."""
    fuzzer = SmartContractFuzzer(seed=999)
    res = fuzzer.fuzz(runs=runs)
    return json.dumps(res, indent=2)


# ── 5. Solidity Smart Contract Bug Bounty Auditor Tool ─────────────────────

@app.tool()
def bionic_solidity_audit(contract_path: str = "contracts/TestnetFlashLoanArbitrage.sol") -> str:
    """Audits Solidity contracts for reentrancy, oracle reliance, and access control vulnerabilities."""
    full_path = os.path.join(ROOT_DIR, contract_path) if not os.path.isabs(contract_path) else contract_path
    scanner = SolidityAuditScanner()
    res = scanner.scan_source(full_path)
    return json.dumps(res, indent=2)


# ── 6. Live Network & HTTP Security Prober Tools ───────────────────────────

@app.tool()
def bionic_security_port_scan(target_host: str = "127.0.0.1", ports: str = "80,443,5000,5055,8080,8888") -> str:
    """Executes high-speed multi-threaded TCP socket scanning and banner grabbing."""
    return live_port_scan(target_host, ports=ports)

@app.tool()
def bionic_security_http_audit(target_url: str = "https://example.com") -> str:
    """Audits HTTP response headers for missing HSTS, CSP, and X-Frame-Options."""
    return live_http_audit(target_url)


# ── 7. Bionic Code Analysis & AST Tool ─────────────────────────────────────

@app.tool()
def bionic_code_analyze(file_path: str = "unified_payment_gateway.py") -> str:
    """Performs deep AST complexity analysis and function mapping on Python source files."""
    full_path = os.path.join(ROOT_DIR, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.exists(full_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    with open(full_path, "r", encoding="utf-8") as f:
        code_str = f.read()
    from bionic_code_engine import BionicCodeEngine
    engine = BionicCodeEngine()
    analysis = engine.analyze_source(code_str)
    return json.dumps(analysis, indent=2)

@app.tool()
def bionic_generate_tests(file_path: str = "iso8583_engine.py") -> str:
    """Automatically scaffolds pytest unit tests based on AST function signatures."""
    full_path = os.path.join(ROOT_DIR, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.exists(full_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    with open(full_path, "r", encoding="utf-8") as f:
        code_str = f.read()
    from bionic_code_engine import BionicCodeEngine
    engine = BionicCodeEngine()
    tests = engine.generate_unit_tests(code_str, module_name=os.path.basename(file_path).replace(".py", ""))
    return json.dumps({"module": file_path, "scaffolded_tests": tests}, indent=2)


# ── 8. Bionic Private Cloud VPS & Memory Topology Tool ──────────────────────

@app.tool()
def bionic_vps_plan_memory(physical_ram_gb: int = 128, numa_nodes: int = 2) -> str:
    """Calculates optimal bare-metal RAM layout, HugePages 2MB allocations, and ZRAM effective capacity."""
    from bionic_cloud_vps_engine import HighRamCapacityPlanner
    planner = HighRamCapacityPlanner(physical_ram_gb=physical_ram_gb, numa_nodes=numa_nodes)
    layout = planner.calculate_memory_layout()
    return json.dumps(layout, indent=2)

@app.tool()
def bionic_vps_provision_instance(name: str = "bionic-agent-vps-01", vcpus: int = 16, ram_gb: int = 64, disk_gb: int = 200) -> str:
    """Provisions an isolated High-RAM microVM instance with automated cloud-init and QEMU KVM launch scripts."""
    from bionic_cloud_vps_engine import PrivateCloudVPSManager
    manager = PrivateCloudVPSManager()
    res = manager.provision_vps(name=name, vcpus=vcpus, ram_gb=ram_gb, disk_gb=disk_gb)
    return json.dumps(res, indent=2)


# ── 9. API Exploit Lab Tools ─────────────────────────────────────────────────

from advanced_mcp_tools import (
    apiexploit_list_vulns,
    evilginx_generate_config,
    c2_generate_artifacts,
    phishing_generate_page,
    evasion_encode_payload,
    evasion_generate_ua,
    evasion_domain_front,
    evasion_simulate_injection,
    kill_chain_run,
    c2_server_start,
    c2_server_stop,
    c2_list_implants,
    c2_dispatch_command,
    c2_get_results,
    fuzz_coverage_guided,
    fuzz_web,
    fuzz_api,
    rfid_analyze_card,
    rfid_em4100_pattern,
    rfid_mifare_clone_script,
    badusb_generate_payload,
    wifi_deauth_detect,
    ble_parse_advertisement,
    ble_classify_device,
    uart_jtag_reference,
    se_generate_vishing_script,
    se_generate_pretext,
    se_osint_profile,
    se_generate_phishing_email,
    se_campaign_create,
    se_campaign_record_event,
    supplychain_dependency_confusion_scan,
    supplychain_typosquat_detect,
    supplychain_cicd_scan,
    supplychain_container_scan,
    supplychain_integrity_verify,
    swarm_run_assessment,
)

@app.tool()
def bionic_apiexploit_list_vulns() -> str:
    """List all vulnerabilities in the API Exploit Lab server."""
    return json.dumps(apiexploit_list_vulns(), indent=2)

@app.tool()
def bionic_evilginx_config(target_domain: str, phish_domain: str, redirect_url: str = "/", 
                            cookies: list = None, proxy_hosts: list = None) -> str:
    """Generate Evilginx3 phishlet YAML config (config file only, no runtime)."""
    return json.dumps(evilginx_generate_config(target_domain, phish_domain, redirect_url, cookies, proxy_hosts), indent=2, default=str)

@app.tool()
def bionic_c2_deploy_artifacts(framework: str = "sliver", output_dir: str = "./c2_lab") -> str:
    """Generate Docker Compose artifacts for Sliver or Mythic C2 lab."""
    return json.dumps(c2_generate_artifacts(framework, output_dir), indent=2)

@app.tool()
def bionic_phishing_page(brand: str = "generic", include_server: bool = False, output_dir: str = "./phish_lab") -> str:
    """Generate static HTML phishing page for security awareness training."""
    return json.dumps(phishing_generate_page(brand, include_server, output_dir), indent=2)

@app.tool()
def bionic_evasion_encode(payload: str, method: str = "base64") -> str:
    """Encode a payload using base64, hex, XOR, or AES-256-CBC."""
    return json.dumps(evasion_encode_payload(payload, method), indent=2)

@app.tool()
def bionic_evasion_ua(browser: str = "chrome", strategy: str = "random") -> str:
    """Generate a random or browser-specific User-Agent string."""
    return json.dumps(evasion_generate_ua(browser, strategy), indent=2)

@app.tool()
def bionic_evasion_domain_front(front_domain: str, target_host: str, path: str = "/") -> str:
    """Generate a domain-fronting request structure."""
    return json.dumps(evasion_domain_front(front_domain, target_host, path), indent=2)

@app.tool()
def bionic_evasion_injection_demo(technique: str, target: str = "notepad.exe") -> str:
    """Demonstrate process injection technique (simulation only)."""
    return json.dumps(evasion_simulate_injection(technique, target), indent=2)

@app.tool()
def bionic_kill_chain(target: str = "https://api.example.com", objective: str = "full_compromise") -> str:
    """Execute the 7-stage kill chain orchestrator (BOLA→JWT→MassAssign→SQLi→SSRF→Cloud→Persist)."""
    return json.dumps(kill_chain_run(target, objective), indent=2)

@app.tool()
def bionic_c2_server_start(host: str = "0.0.0.0", port: int = 8080) -> str:
    """Start the C2 server with dashboard and implant comms endpoint."""
    return json.dumps(c2_server_start(host, port), indent=2)

@app.tool()
def bionic_c2_server_stop() -> str:
    """Stop the running C2 server."""
    return json.dumps(c2_server_stop(), indent=2)

@app.tool()
def bionic_c2_list_implants() -> str:
    """List all registered implants on the C2 server."""
    return json.dumps(c2_list_implants(), indent=2)

@app.tool()
def bionic_c2_dispatch(implant_id: str, plugin: str = "exec", params: dict = None) -> str:
    """Dispatch a command to an implant via the C2 server."""
    return json.dumps(c2_dispatch_command(implant_id, plugin, params), indent=2)

@app.tool()
def bionic_c2_results(implant_id: str, limit: int = 50) -> str:
    """Get results from an implant."""
    return json.dumps(c2_get_results(implant_id, limit), indent=2)

@app.tool()
def bionic_fuzz_web(url: str, params: dict = None, headers: dict = None, method: str = "GET") -> str:
    """Fuzz web parameters and headers with known attack payloads."""
    return json.dumps(fuzz_web(url, params, headers, method), indent=2)

@app.tool()
def bionic_fuzz_api(base_url: str, api_type: str = "rest", endpoints: list = None) -> str:
    """Fuzz REST or GraphQL API endpoints."""
    return json.dumps(fuzz_api(base_url, api_type, endpoints), indent=2)

@app.tool()
def bionic_fuzz_coverage(target_code: str = "lambda data: None", seeds: list = None, max_iter: int = 500) -> str:
    """Run AFL-style coverage-guided fuzzing on a target function."""
    return json.dumps(fuzz_coverage_guided(target_code, seeds, max_iter), indent=2)

@app.tool()
def bionic_rfid_analyze(atqa: str, sak: str, uid: str) -> str:
    """Identify RFID card type from ATQA/SAK/UID."""
    return json.dumps(rfid_analyze_card(atqa, sak, uid), indent=2)

@app.tool()
def bionic_rfid_em4100(uid: str) -> str:
    """Generate EM4100 125kHz emulation pattern."""
    return json.dumps(rfid_em4100_pattern(uid), indent=2)

@app.tool()
def bionic_rfid_mifare_clone(uid: str) -> str:
    """Generate Proxmark3 MIFARE Classic clone script."""
    return rfid_mifare_clone_script(uid)

@app.tool()
def bionic_badusb_payload(payload_type: str = "ducky_reverse_shell", lhost: str = "192.168.1.100", 
                           lport: int = 4444) -> str:
    """Generate DigiSpark or Rubber Ducky payload."""
    return badusb_generate_payload(payload_type, lhost, lport)

@app.tool()
def bionic_wifi_deauth(frames: list = None) -> str:
    """Detect WiFi deauthentication attacks from frame data."""
    return json.dumps(wifi_deauth_detect(frames), indent=2)

@app.tool()
def bionic_ble_parse(hex_data: str) -> str:
    """Parse BLE advertisement packet."""
    return json.dumps(ble_parse_advertisement(hex_data), indent=2)

@app.tool()
def bionic_ble_classify(rssi: int, name: str = None) -> str:
    """Classify BLE device and assess risk."""
    return json.dumps(ble_classify_device(rssi, name), indent=2)

@app.tool()
def bionic_uart_jtag(ref_type: str = "pinouts", target: str = None) -> str:
    """Get UART/JTAG pinout reference or OpenOCD config."""
    return json.dumps(uart_jtag_reference(ref_type, target), indent=2)

@app.tool()
def bionic_se_vishing(template: str = "it_support", target_name: str = "John Smith") -> str:
    """Generate a vishing call script from a template."""
    return se_generate_vishing_script(template, target_name)

@app.tool()
def bionic_se_pretext(scenario: str = "auditor") -> str:
    """Generate a pretexting scenario script."""
    return se_generate_pretext(scenario)

@app.tool()
def bionic_se_osint(email: str) -> str:
    """Generate an OSINT profile skeleton from an email address."""
    return json.dumps(se_osint_profile(email), indent=2)

@app.tool()
def bionic_se_phishing(template: str = "password_reset", target_name: str = "John Smith",
                        target_email: str = "john@example.com") -> str:
    """Generate a phishing email from a template."""
    return json.dumps(se_generate_phishing_email(template, target_name, target_email), indent=2)

@app.tool()
def bionic_se_campaign_create(name: str, total_targets: int = 100) -> str:
    """Create a new SE campaign for tracking."""
    return json.dumps(se_campaign_create(name, total_targets), indent=2)

@app.tool()
def bionic_se_campaign_event(campaign_id: str, event: str, count: int = 1) -> str:
    """Record an event in an SE campaign."""
    return json.dumps(se_campaign_record_event(campaign_id, event, count), indent=2)

@app.tool()
def bionic_supplychain_depconfusion(package_name: str, registry_url: str = "https://registry.npmjs.org") -> str:
    """Scan for dependency confusion vulnerability."""
    return json.dumps(supplychain_dependency_confusion_scan(package_name, registry_url), indent=2)

@app.tool()
def bionic_supplychain_typosquat(package_name: str, registry: str = "pypi") -> str:
    """Detect typosquat candidates for a package name."""
    return json.dumps(supplychain_typosquat_detect(package_name, registry), indent=2)

@app.tool()
def bionic_supplychain_cicd(manifest_path: str = ".github/workflows/ci.yml") -> str:
    """Scan CI/CD pipeline manifest for attack patterns."""
    return json.dumps(supplychain_cicd_scan(manifest_path), indent=2)

@app.tool()
def bionic_supplychain_container(image_ref: str = "alpine:latest") -> str:
    """Scan container image reference for security issues."""
    return json.dumps(supplychain_container_scan(image_ref), indent=2)

@app.tool()
def bionic_supplychain_integrity(package_name: str, version: str, local_path: str, expected_hash: str = None) -> str:
    """Verify package integrity via SHA-256 hash."""
    return json.dumps(supplychain_integrity_verify(package_name, version, local_path, expected_hash), indent=2)

@app.tool()
def bionic_swarm_assess(targets: list = None, allowed_ports: list = None) -> str:
    """Run multi-agent security assessment swarm."""
    return json.dumps(swarm_run_assessment(targets, allowed_ports), indent=2)


# ── 10. Visa/Mastercard Credential Harvesting ───────────────────────────────
# FOR AUTHORIZED SECURITY TESTING ONLY

from visa_mc_mcp_tools import (
    generate_visa_phish_page,
    generate_cred_collector,
    generate_mitm_script,
    scan_github_for_credentials,
    get_known_leaked_credentials,
    credential_harvest_attack_chain,
)

@app.tool()
def bionic_visa_phish_page(attacker_url: str = "https://localhost:8080/collect", output_path: str = "visa_login.html") -> str:
    """Generate a fake Visa Developer Portal login page for authorized phishing tests."""
    return generate_visa_phish_page(attacker_url, output_path)

@app.tool()
def bionic_visa_cred_collector(port: int = 8080, output_file: str = "captured_credentials.jsonl") -> str:
    """Generate a credential collector HTTP server for phishing tests."""
    return generate_cred_collector(port, output_file)

@app.tool()
def bionic_visa_mitm_script() -> str:
    """Generate a mitmproxy script that intercepts Visa/Mastercard API credentials."""
    return generate_mitm_script()

@app.tool()
def bionic_visa_github_scan() -> str:
    """Scan GitHub for leaked Visa/Mastercard API credentials."""
    return scan_github_for_credentials()

@app.tool()
def bionic_visa_known_leaks() -> str:
    """Return database of known leaked Visa/Mastercard credentials from public sources."""
    return get_known_leaked_credentials()

@app.tool()
def bionic_visa_attack_chain(target_email: str, attacker_domain: str = "attacker.com") -> str:
    """Build a complete credential harvesting attack chain for a Visa/Mastercard target."""
    return credential_harvest_attack_chain(target_email, attacker_domain)


# ── 11. Mass Payment Key Scanner ────────────────────────────────────────────

from mass_payment_key_scanner import (
    scan_github_for_payment_keys,
    scan_repo_for_keys,
    test_stripe_key,
    test_paypal_token,
    get_key_patterns,
    get_search_queries,
)

@app.tool()
def bionic_payment_key_scan(max_results: int = 10, queries: list = None) -> str:
    """Mass scan GitHub for leaked payment API keys (Stripe, Visa, MC, PayPal, Amex)."""
    return scan_github_for_payment_keys(max_results, queries)

@app.tool()
def bionic_payment_repo_scan(repo: str) -> str:
    """Deep scan a specific repo for payment API keys."""
    return scan_repo_for_keys(repo)

@app.tool()
def bionic_stripe_key_test(api_key: str) -> str:
    """Test a Stripe API key and return balance info if valid."""
    return test_stripe_key(api_key)

@app.tool()
def bionic_paypal_token_test(client_id: str, secret: str) -> str:
    """Test PayPal API credentials and return token info if valid."""
    return test_paypal_token(client_id, secret)

@app.tool()
def bionic_payment_patterns() -> str:
    """Return all payment key patterns used for scanning."""
    return get_key_patterns()

@app.tool()
def bionic_payment_queries() -> str:
    """Return all GitHub search queries for payment keys."""
    return get_search_queries()


# ── 12. Stripe Logic Flaw Testing ─────────────────────────────────────────

from stripe_toolkit import (
    stripe_test_coupon,
    stripe_test_amount,
    stripe_test_currency,
    stripe_test_webhook,
    stripe_test_connect,
    stripe_test_checkout,
    stripe_test_idor,
    payment_recon_paypal,
    payment_recon_amex,
    payment_recon_square,
    payment_recon_braintree,
    payment_recon_adyen,
    payment_recon_all,
)

@app.tool()
def bionic_stripe_coupon_test(api_key: str, coupon_id: str, iterations: int = 5) -> str:
    """Test Stripe coupon for unlimited redemption."""
    return stripe_test_coupon(api_key, coupon_id, iterations)

@app.tool()
def bionic_stripe_amount_test(api_key: str, amount_cents: int = 100) -> str:
    """Test Stripe for amount manipulation (0 or negative)."""
    return stripe_test_amount(api_key, amount_cents)

@app.tool()
def bionic_stripe_currency_test(api_key: str) -> str:
    """Test Stripe for currency manipulation."""
    return stripe_test_currency(api_key)

@app.tool()
def bionic_stripe_webhook_test(api_key: str, webhook_secret: str, payload: dict = None) -> str:
    """Test Stripe webhook for signature bypass."""
    return stripe_test_webhook(api_key, webhook_secret, payload)

@app.tool()
def bionic_stripe_connect_test(api_key: str, account_id: str) -> str:
    """Test Stripe Connect for payout manipulation."""
    return stripe_test_connect(api_key, account_id)

@app.tool()
def bionic_stripe_checkout_test(api_key: str, price_id: str) -> str:
    """Test Stripe Checkout for session manipulation."""
    return stripe_test_checkout(api_key, price_id)

@app.tool()
def bionic_stripe_idor_test(api_key: str, object_id: str, object_type: str = "customers") -> str:
    """Test Stripe for IDOR vulnerabilities."""
    return stripe_test_idor(api_key, object_id, object_type)

@app.tool()
def bionic_payment_recon(provider: str = "all") -> str:
    """Return payment API attack surface for a provider (paypal, amex, square, braintree, adyen, all)."""
    if provider == "paypal":
        return payment_recon_paypal()
    elif provider == "amex":
        return payment_recon_amex()
    elif provider == "square":
        return payment_recon_square()
    elif provider == "braintree":
        return payment_recon_braintree()
    elif provider == "adyen":
        return payment_recon_adyen()
    else:
        return payment_recon_all()


# ── 13. Skimmer & Keylogger Defense ───────────────────────────────────────

from skimmer_detection_toolkit import (
    scan_webpage_for_skimmers,
    scan_apk_for_keylogger,
    scan_windows_file_for_keylogger,
    scan_windows_persistence,
    audit_pos_terminal,
    get_skimmer_signatures,
    get_defense_recommendations,
)

@app.tool()
def bionic_skimmer_scan_web(html: str, url: str = "unknown") -> str:
    """Scan a webpage for JavaScript skimmer indicators."""
    return scan_webpage_for_skimmers(html, url)

@app.tool()
def bionic_skimmer_scan_apk(manifest_path: str) -> str:
    """Scan Android APK manifest for keylogger/skimmer indicators."""
    return scan_apk_for_keylogger(manifest_path)

@app.tool()
def bionic_keylogger_scan_windows(file_path: str) -> str:
    """Scan a Windows PE file for keylogger indicators."""
    return scan_windows_file_for_keylogger(file_path)

@app.tool()
def bionic_keylogger_scan_persistence() -> str:
    """Scan Windows registry for keylogger persistence mechanisms."""
    return scan_windows_persistence()

@app.tool()
def bionic_pos_audit(config: dict) -> str:
    """Audit POS terminal configuration for security issues."""
    return audit_pos_terminal(config)

@app.tool()
def bionic_skimmer_signatures() -> str:
    """Return known skimmer signatures and IOCs (Magecart, Android skimmers)."""
    return get_skimmer_signatures()

@app.tool()
def bionic_skimmer_defenses() -> str:
    """Return comprehensive defense recommendations for all platforms."""
    return get_defense_recommendations()


# ── 14. Farm 3 Phones Integration ─────────────────────────────────────────

from farm_integration import (
    adb_devices,
    farm_phone_status,
    price_manip_test,
    hunt_endpoints,
    analyze_apk,
    generate_ssl_bypass,
    generate_frida_script,
)

@app.tool()
def bionic_farm_status() -> str:
    """Get status of all phones in the farm."""
    return json.dumps(farm_phone_status(), indent=2)

@app.tool()
def bionic_adb_devices() -> str:
    """List connected Android devices."""
    return json.dumps(adb_devices(), indent=2)

@app.tool()
def bionic_price_manip_test(url: str, params: dict, cookie: str = None) -> str:
    """Test checkout for price manipulation flaws."""
    return json.dumps(price_manip_test(url, params, cookie), indent=2)

@app.tool()
def bionic_hunt_endpoints(target: str, wordlist: list = None) -> str:
    """Hunt for API endpoints on a target domain."""
    return json.dumps(hunt_endpoints(target, wordlist), indent=2)

@app.tool()
def bionic_analyze_apk(apk_path: str) -> str:
    """Analyze an APK for endpoints, permissions, and security issues."""
    return json.dumps(analyze_apk(apk_path), indent=2)

@app.tool()
def bionic_generate_ssl_bypass(package: str) -> str:
    """Generate SSL bypass configuration for a package."""
    return json.dumps(generate_ssl_bypass(package), indent=2)

@app.tool()
def bionic_generate_frida_script(target_class: str, method: str = "onCreate") -> str:
    """Generate a Frida hook for a target class/method."""
    return json.dumps(generate_frida_script(target_class, method), indent=2)


if __name__ == "__main__":
    app.run()
