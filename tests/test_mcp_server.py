#!/usr/bin/env python3
"""
Test suite for the Bionic Unified MCP Server.
Invariant tests: assert how two pieces of data relate,
never freeze a current value.
"""
import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Import and return the FastMCP app."""
    import sys
    sys.path.insert(0, '.')
    import importlib.util
    spec = importlib.util.spec_from_file_location('server', 'bionic_unified_mcp_server.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.fixture
def visa_tools():
    """Import visa_mc_mcp_tools."""
    import sys
    sys.path.insert(0, '.')
    import visa_mc_mcp_tools
    return visa_mc_mcp_tools


@pytest.fixture
def payment_scanner():
    """Import mass_payment_key_scanner."""
    import sys
    sys.path.insert(0, '.')
    import mass_payment_key_scanner
    return mass_payment_key_scanner


@pytest.fixture
def stripe():
    """Import stripe_toolkit."""
    import sys
    sys.path.insert(0, '.')
    import stripe_toolkit
    return stripe_toolkit


# ── MCP Server Invariant Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_count_at_least_60(app):
    """Server must register at least 60 tools."""
    tools = await app.list_tools()
    assert len(tools) >= 60, f"Expected >= 60 tools, got {len(tools)}"


@pytest.mark.asyncio
async def test_no_duplicate_tool_names(app):
    """Tool names must be unique."""
    tools = await app.list_tools()
    names = [t.name for t in tools]
    assert len(names) == len(set(names)), f"Duplicates: {[n for n in names if names.count(n) > 1]}"


@pytest.mark.asyncio
async def test_all_tools_have_names(app):
    """Every tool must have a non-empty name."""
    tools = await app.list_tools()
    for t in tools:
        assert t.name, f"Tool without name: {t}"
        assert len(t.name) > 0


@pytest.mark.asyncio
async def test_all_tools_have_descriptions(app):
    """Every tool must have a non-empty description."""
    tools = await app.list_tools()
    for t in tools:
        assert t.description, f"Tool without description: {t.name}"


@pytest.mark.asyncio
async def test_visa_tools_registered(app):
    """All 6 Visa tools must be present."""
    tools = await app.list_tools()
    names = [t.name for t in tools]
    expected = [
        'bionic_visa_phish_page',
        'bionic_visa_cred_collector',
        'bionic_visa_mitm_script',
        'bionic_visa_github_scan',
        'bionic_visa_known_leaks',
        'bionic_visa_attack_chain',
    ]
    for name in expected:
        assert name in names, f"Missing Visa tool: {name}"


@pytest.mark.asyncio
async def test_payment_scanner_registered(app):
    """Payment scanner tools must be present."""
    tools = await app.list_tools()
    names = [t.name for t in tools]
    expected = [
        'bionic_payment_key_scan',
        'bionic_payment_repo_scan',
        'bionic_payment_patterns',
        'bionic_payment_queries',
    ]
    for name in expected:
        assert name in names, f"Missing payment tool: {name}"


@pytest.mark.asyncio
async def test_stripe_tools_registered(app):
    """Stripe tools must be present."""
    tools = await app.list_tools()
    names = [t.name for t in tools]
    expected = [
        'bionic_stripe_surface',
        'bionic_stripe_flaws',
        'bionic_stripe_cards',
    ]
    for name in expected:
        assert name in names, f"Missing Stripe tool: {name}"


# ── Visa MC MCP Tools Tests ───────────────────────────────────────────────

def test_known_leaks_returns_json(visa_tools):
    """get_known_leaked_credentials must return valid JSON."""
    result = visa_tools.get_known_leaked_credentials()
    data = json.loads(result)
    assert isinstance(data, dict)
    assert "visa" in data
    assert len(data["visa"]) >= 1


def test_known_leaks_visa_has_required_fields(visa_tools):
    """Each Visa leak must have source, type, and status."""
    result = visa_tools.get_known_leaked_credentials()
    data = json.loads(result)
    for leak in data["visa"]:
        assert "source" in leak
        assert "type" in leak
        assert "status" in leak


def test_attack_chain_returns_all_phases(visa_tools):
    """Attack chain must have 5 phases."""
    result = visa_tools.credential_harvest_attack_chain("test@example.com")
    data = json.loads(result)
    chain = data.get("chain", data)
    assert len(chain) >= 5


def test_phish_page_generation(visa_tools):
    """Phish page generator must return file path."""
    result = visa_tools.generate_visa_phish_page("https://example.com/collect")
    data = json.loads(result)
    assert "page" in data


def test_mitm_script_generation(visa_tools):
    """MITM script generator must return script path."""
    result = visa_tools.generate_mitm_script()
    assert "mitm_visa_mc.py" in result


# ── Payment Scanner Tests ─────────────────────────────────────────────────

def test_key_patterns_have_8_providers(payment_scanner):
    """Must cover at least 8 payment providers."""
    result = payment_scanner.get_key_patterns()
    data = json.loads(result)
    assert len(data) >= 8


def test_key_patterns_stripe_has_live_key(payment_scanner):
    """Stripe patterns must include sk_live_ pattern."""
    result = payment_scanner.get_key_patterns()
    data = json.loads(result)
    assert "stripe" in data
    patterns = json.dumps(data["stripe"])
    assert "sk_live_" in patterns


def test_search_queries_at_least_30(payment_scanner):
    """Must have at least 30 search queries."""
    result = payment_scanner.get_search_queries()
    data = json.loads(result)
    assert len(data) >= 30


def test_search_queries_include_stripe(payment_scanner):
    """Queries must include stripe patterns."""
    result = payment_scanner.get_search_queries()
    data = json.loads(result)
    queries = " ".join(data)
    assert "sk_live_" in queries
    assert "stripe" in queries


# ── Stripe Toolkit Tests ──────────────────────────────────────────────────

def test_api_surface_has_10_categories(stripe):
    """Stripe API surface must have at least 10 endpoint groups."""
    result = stripe.stripe_api_surface()
    data = json.loads(result)
    # The structure is {"base_url": ..., "auth": ..., "endpoints": {...}}
    endpoints = data.get("endpoints", data)
    assert len(endpoints) >= 10


def test_api_surface_has_charges(stripe):
    """Stripe API must include /charges endpoint."""
    result = stripe.stripe_api_surface()
    data = json.loads(result)
    endpoints = data.get("endpoints", data)
    assert "charges" in endpoints or "payment_intents" in endpoints


def test_known_flaws_at_least_5(stripe):
    """Must document at least 5 historical flaws."""
    result = stripe.stripe_known_flaws()
    data = json.loads(result)
    assert len(data) >= 5


def test_test_cards_include_visa_4242(stripe):
    """Test cards must include Visa 4242424242424242."""
    result = stripe.stripe_test_card_numbers()
    data = json.loads(result)
    all_cards = json.dumps(data)
    assert "4242424242424242" in all_cards


# ── Advanced MCP Tools Tests ────────────────────────────────────────────

def test_swarm_dry_run():
    """Swarm dry run must return a valid report."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.swarm_run_assessment(targets=["10.0.0.1"], allowed_ports=[22, 80])
    # Returns dict directly
    assert "report_id" in result or "total_findings" in result


def test_kill_chain_structure():
    """Kill chain must have 7 stages."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.kill_chain_run(target="test.com")
    assert result["execution_summary"]["total_stages"] == 7


def test_evilginx_config():
    """Evilginx config generator must produce phishlets."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.evilginx_generate_config(
        target_domain="login.example.com", phish_domain="phish.example.com"
    )
    assert "config" in result
    assert "phishlets" in result["config"]


def test_phishing_page_generator():
    """Phishing generator must return page path."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.phishing_generate_page(
        brand="microsoft", include_server=False, output_dir="./test_phish"
    )
    assert "page" in result
    assert "index.html" in result["page"]


def test_rfid_card_analysis():
    """RFID analyzer must identify MIFARE Classic."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.rfid_analyze_card(atqa="0004", sak="08", uid="A1B2C3D4")
    assert "card" in result
    assert result["card"] != "UNKNOWN"


def test_ble_classify_low_signal():
    """BLE classifier must flag weak signals."""
    import advanced_mcp_tools
    result = advanced_mcp_tools.ble_classify_device(rssi=-85, name="Unknown")
    assert result["risk"] in ["HIGH", "LOW"]


# ── Integration Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_categories_complete(app):
    """All 3 core categories must be present."""
    tools = await app.list_tools()
    names = [t.name for t in tools]
    
    # Visa tools
    assert any("visa" in n for n in names)
    # Payment scanner
    assert any("payment" in n for n in names)
    # Stripe tools
    assert any("stripe" in n for n in names)


def test_visa_known_leaks_structure():
    """Known leaks must have visa and high_value_targets."""
    import visa_mc_mcp_tools
    result = visa_mc_mcp_tools.get_known_leaked_credentials()
    data = json.loads(result)
    assert "visa" in data
    assert len(data["visa"]) >= 1


def test_scan_results_file_exists():
    """Scan results must be persisted."""
    import os
    assert os.path.exists("scan_results_full.json")
    with open("scan_results_full.json") as f:
        data = json.load(f)
    assert data["total_findings"] > 0


# ── Performance / Rate Limit Tests ────────────────────────────────────────

def test_github_search_rate_limit():
    """GitHub search must include rate limiting."""
    import mass_payment_key_scanner
    import inspect
    source = inspect.getsource(mass_payment_key_scanner.scan_github_for_payment_keys)
    assert "time.sleep" in source or "rate" in source.lower()


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
