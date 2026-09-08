#!/usr/bin/env python3
"""Dry-run probe for bionic tools. No side effects. Just instantiates + uses non-mutating methods."""
import json
results = {}

# 1. bionic_code_engine
try:
    from bionic_code_engine import BionicCodeEngine
    e = BionicCodeEngine()
    sample = 'def add(a, b):\n    return a + b\n'
    out = e.analyze_source(sample)
    key_info = type(out).__name__ if not isinstance(out, dict) else list(out.keys())[:5]
    results['bionic_code_engine'] = ('OK', key_info)
except Exception as e:
    results['bionic_code_engine'] = ('FAIL', str(e)[:80])

# 2. bionic_self_dev
try:
    from bionic_self_dev import BionicSelfDevEngine
    e = BionicSelfDevEngine()
    caps = e.list_capabilities() if hasattr(e, 'list_capabilities') else dir(e)
    results['bionic_self_dev'] = ('OK', f'{len(caps)} attrs')
except Exception as e:
    results['bionic_self_dev'] = ('FAIL', str(e)[:80])

# 3. bionic_bounty_sweeper
try:
    from bionic_bounty_sweeper import AutonomousBountySweeper
    s = AutonomousBountySweeper()
    findings = s.scan_contract_source('pragma solidity ^0.8.0; contract Test { uint x; }')
    info = f'{len(findings)} findings'
except Exception as e:
    results['bionic_bounty_sweeper'] = ('FAIL', str(e)[:80])

# 4. bionic_foundry_invariant_fuzzer
try:
    from bionic_foundry_invariant_fuzzer import InvariantVaultFuzzer
    f = InvariantVaultFuzzer()
    import random
    for _ in range(100):
        f.swap_usdc_for_bionic(random.uniform(100, 10000))
    results['bionic_foundry_invariant_fuzzer'] = ('OK', f'broken={f.invariant_broken} violations={len(f.violation_log)}')
except Exception as e:
    results['bionic_foundry_invariant_fuzzer'] = ('FAIL', str(e)[:80])

# 5. unified_payment_gateway
try:
    from unified_payment_gateway import UnifiedPaymentGateway, ISO8583Message
    g = UnifiedPaymentGateway()
    msg = ISO8583Message(mti='0100', pan='4111111111111111', amount='000000001000', stan='000001')
    method_name = 'build_iso8583' if hasattr(g, 'build_iso8583') else 'encode'
    iso = getattr(g, method_name)(msg)
    info = f'{len(iso)} bytes' if hasattr(iso, '__len__') else type(iso).__name__
    results['unified_payment_gateway'] = ('OK', info)
except Exception as e:
    results['unified_payment_gateway'] = ('FAIL', str(e)[:80])

# 6. solidity_audit_scanner
try:
    from solidity_audit_scanner import SolidityAuditScanner
    s = SolidityAuditScanner()
    sample = 'function withdraw() public { msg.sender.call{value: balance}(""); balance = 0; }'
    findings = s.scan_source(sample)
    info = f'{len(findings)} findings' if hasattr(findings, '__len__') else type(findings).__name__
    results['solidity_audit_scanner'] = ('OK', info)
except Exception as e:
    results['solidity_audit_scanner'] = ('FAIL', str(e)[:80])

# 7. three_ds_simulator
try:
    from three_ds_simulator import ThreeDSServer, DirectoryServer, AccessControlServer
    acs = AccessControlServer()
    ds = DirectoryServer(acs=acs)
    methods = [m for m in dir(ds) if not m.startswith('_')][:8]
    results['three_ds_simulator'] = ('OK', f'{len(methods)} DS methods')
except Exception as e:
    results['three_ds_simulator'] = ('FAIL', str(e)[:80])

# 8. iso8583_engine
try:
    from iso8583_engine import ISO8583Message, PaymentSwitchSimulator
    sim = PaymentSwitchSimulator()
    methods = [m for m in dir(sim) if not m.startswith('_')][:8]
    results['iso8583_engine'] = ('OK', f'{len(methods)} switch methods')
except Exception as e:
    results['iso8583_engine'] = ('FAIL', str(e)[:80])

# 9. iso20022_engine
try:
    from iso20022_engine import ISO20022Engine
    e = ISO20022Engine()
    methods = [m for m in dir(e) if not m.startswith('_')][:8]
    results['iso20022_engine'] = ('OK', f'{len(methods)} methods')
except Exception as e:
    results['iso20022_engine'] = ('FAIL', str(e)[:80])

# 10. financial_table_extractor
try:
    from financial_table_extractor import FinancialTableExtractor
    e = FinancialTableExtractor()
    methods = [m for m in dir(e) if not m.startswith('_')][:8]
    results['financial_table_extractor'] = ('OK', f'{len(methods)} methods')
except Exception as e:
    results['financial_table_extractor'] = ('FAIL', str(e)[:80])

# 11. web3_contract_fuzzer
try:
    from web3_contract_fuzzer import SmartContractFuzzer
    e = SmartContractFuzzer(seed=42)
    methods = [m for m in dir(e) if not m.startswith('_')][:8]
    results['web3_contract_fuzzer'] = ('OK', f'{len(methods)} methods')
except Exception as e:
    results['web3_contract_fuzzer'] = ('FAIL', str(e)[:80])

# 12. api_defense_lab (Round 3 addition)
try:
    import api_defense_lab
    classes = [n for n,v in vars(api_defense_lab).items() if isinstance(v, type) and not n.startswith('_')]
    results['api_defense_lab'] = ('OK', f'{len(classes)} classes: {classes[:3]}')
except Exception as e:
    results['api_defense_lab'] = ('FAIL', str(e)[:80])

# 13. web3_defi_lab (Round 3 addition)
try:
    import web3_defi_lab
    classes = [n for n,v in vars(web3_defi_lab).items() if isinstance(v, type) and not n.startswith('_')]
    results['web3_defi_lab'] = ('OK', f'{len(classes)} classes: {classes[:3]}')
except Exception as e:
    results['web3_defi_lab'] = ('FAIL', str(e)[:80])

# 14. llm_adversarial_suite (Round 3 addition)
try:
    from llm_adversarial_suite import GuardrailAuditor
    e = GuardrailAuditor()
    methods = [m for m in dir(e) if not m.startswith('_')][:5]
    results['llm_adversarial_suite'] = ('OK', f'{len(methods)} methods: {methods}')
except Exception as e:
    results['llm_adversarial_suite'] = ('FAIL', str(e)[:80])

# 15. statement_extractor_cli (Round 3 addition)
try:
    from statement_extractor_cli import FinancialTableExtractor, StatementExtractionCLI
    e = FinancialTableExtractor()
    methods = [m for m in dir(e) if not m.startswith('_')][:5]
    results['statement_extractor_cli'] = ('OK', f'{len(methods)} methods')
except Exception as e:
    results['statement_extractor_cli'] = ('FAIL', str(e)[:80])

# 16. orca_swarm_orchestrator (Round 3 addition)
try:
    import orca_swarm_orchestrator
    classes = [n for n,v in vars(orca_swarm_orchestrator).items() if isinstance(v, type) and not n.startswith('_')]
    results['orca_swarm_orchestrator'] = ('OK', f'{len(classes)} classes: {classes[:3]}')
except Exception as e:
    results['orca_swarm_orchestrator'] = ('FAIL', str(e)[:80])

# 17. bionic_audit_pipeline orchestrator (Round 3 addition)
try:
    from bionic_audit_pipeline import BionicAuditPipeline
    p = BionicAuditPipeline()
    methods = [m for m in dir(p) if not m.startswith('_')][:5]
    results['bionic_audit_pipeline'] = ('OK', f'{len(methods)} methods')
except Exception as e:
    results['bionic_audit_pipeline'] = ('FAIL', str(e)[:80])

# 18. bionic_command_center (Round 3 addition)
try:
    from bionic_command_center import MODULES
    results['bionic_command_center'] = ('OK', f'{len(MODULES)} modules in menu')
except Exception as e:
    results['bionic_command_center'] = ('FAIL', str(e)[:80])

print(json.dumps(results, indent=2))

passed = sum(1 for v in results.values() if v[0] == 'OK')
total = len(results)
print(f'\n{passed}/{total} tools passed dry-run')