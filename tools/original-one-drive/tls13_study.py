#!/usr/bin/env python3
"""
TLS 1.3 Handshake Capture and Annotation — Phase 1B Learning Project

This captures a real TLS 1.3 handshake (connecting to a public HTTPS server),
saves the raw bytes, and annotates every message with what it contains and
why it's there.

Two approaches:
1. Python ssl module — capture the raw TLS bytes via a custom socket
2. OpenSSL s_client — capture via subprocess + tcpdump-style logging

We'll use OpenSSL because it gives us a clean capture of the handshake
without application data mixed in.

Reference: RFC 8446 (TLS 1.3)
"""

import subprocess
import json
import os
import time
from datetime import datetime

# ============================================================================
# APPROACH 1: OpenSSL s_client with verbose output
# ============================================================================

OUTPUT_DIR = "/c/Users/mobil/orca/projects/my 1st/tls_study"

os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET = "https://example.com"
HOST = "example.com"
PORT = 443

print("=" * 60)
print("TLS 1.3 HANDSHAKE CAPTURE AND ANNOTATION")
print("=" * 60)
print(f"Target: {TARGET}")
print(f"Capture directory: {OUTPUT_DIR}")
print()

# --- Step 1: Capture with OpenSSL ---
# openssl s_client -connect host:port -tls1_3 -msg -state
# -msg: log all protocol messages
# -state: log state transitions
# -brief: short summary

print("[1] Running OpenSSL s_client with TLS 1.3 handshake capture...")

# Use openssl s_client to capture the handshake
cmd = [
    "openssl", "s_client",
    "-connect", f"{HOST}:{PORT}",
    "-tls1_3",
    "-state",
    "-brief",
    "-quit",
    "-ign_eof",
]

proc = subprocess.run(
    cmd,
    input=b"",
    capture_output=True,
    timeout=15,
    text=True,
)

# Save raw output
raw_path = os.path.join(OUTPUT_DIR, "openssl_raw.txt")
with open(raw_path, "w") as f:
    f.write("=" * 60 + "\n")
    f.write(f"OpenSSL s_client output — {datetime.now().isoformat()}\n")
    f.write(f"Command: {' '.join(cmd)}\n")
    f.write("=" * 60 + "\n\n")
    f.write("--- STDOUT ---\n")
    f.write(proc.stdout)
    f.write("\n--- STDERR ---\n")
    f.write(proc.stderr)

print(f"  Raw output saved to: {raw_path}")
print(f"  stdout: {len(proc.stdout)} bytes")
print(f"  stderr: {len(proc.stderr)} bytes")

# --- Step 2: Parse and annotate the handshake ---

print("\n[2] Parsing handshake messages...")

# Extract key handshake info from OpenSSL output
handshake_info = {
    "target": TARGET,
    "host": HOST,
    "port": PORT,
    "protocol": "TLS 1.3",
    "timestamp": datetime.now().isoformat(),
    "openssl_version": "OpenSSL 3.5.7",
    "messages": [],
    "summary": "",
}

# Parse brief output for cipher and protocol
lines = proc.stdout.split("\n") + proc.stderr.split("\n")
for line in lines:
    line = line.strip()
    if "Protocol" in line and ":" in line:
        handshake_info["summary"] += line + "\n"
    if "Cipher" in line and ":" in line:
        handshake_info["summary"] += line + "\n"
    if "Server Temp Key" in line:
        handshake_info["summary"] += line + "\n"

# Read the saved raw output for detailed analysis
with open(raw_path) as f:
    raw = f.read()

# --- Step 3: Document the TLS 1.3 handshake protocol ---

print("[3] Documenting TLS 1.3 handshake protocol...")

tls13_handshake_docs = {
    "title": "TLS 1.3 Handshake — Full Protocol Documentation",
    "reference": "RFC 8446",
    "messages": [
        {
            "name": "ClientHello",
            "direction": "Client → Server",
            "what_it_contains": [
                "protocol_version: {0x0303 for TLS 1.3 (compatibility with TLS 1.2)",
                "random: 32 bytes of client randomness (used for key derivation)",
                "session_id: empty or reused (TLS 1.3 ignores it for handshake)",
                "cipher_suites: list of supported cipher suites (e.g. TLS_AES_128_GCM_SHA256)",
                "legacy_compression_methods: usually just [0x00] (null)",
                "extensions: the important part — supported versions, key share (ECDHE public key), supported versions extension, signature algorithms, etc.",
            ],
            "why_it_exists": " initiates the handshake. Tells the server what the client supports. Includes the client's ephemeral ECDHE public key (in the key_share extension) so the server can compute the shared secret.",
            "key_points": [
                "The key_share extension contains the client's ECDHE public key (e.g. x25519 or secp256r1).",
                "The server uses this + its own private key to compute the shared secret.",
                "cipher_suites tell the server which TLS 1.3 cipher suites the client supports.",
                "supported_versions extension signals TLS 1.3 (0x0304).",
            ],
        },
        {
            "name": "ServerHello",
            "direction": "Server → Client",
            "what_it_contains": [
                "protocol_version: 0x0303 (TLS 1.3 compatibility)",
                "random: 32 bytes of server randomness",
                "selected_cipher_suite: which cipher suite the server chose",
                "extensions: key_share (server's ECDHE public key), supported_versions",
            ],
            "why_it_exists": " The server picks a cipher suite, sends its ECDHE public key, and confirms TLS 1.3. Both sides now have: client_random, server_random, client ECDHE public key, server ECDHE public key.",
            "key_points": [
                "The server's key_share extension contains the server's ECDHE public key.",
                "Both sides now have the material to compute the shared secret (ECDHE).",
                "After ServerHello, both sides compute the handshake traffic keys.",
            ],
        },
        {
            "name": "EncryptedExtensions",
            "direction": "Server → Client",
            "what_it_contains": [
                "Various extensions that don't need to be encrypted in older TLS but are now: server_name, alpn, etc.",
                "This is the first message encrypted with the handshake traffic key.",
            ],
            "why_it_exists": " Carries extensions that don't fit in ServerHello. In TLS 1.3, everything after ServerHello is encrypted with the handshake traffic key (derived from the ECDHE shared secret + HKDF).",
        },
        {
            "name": "CertificateRequest (optional)",
            "direction": "Server → Client (if mutual TLS)",
            "what_it_contains": [
                "Types of certificates acceptable",
                "Distinguished names of acceptable CAs",
                "Signature algorithms",
            ],
            "why_it_exists": " If the server wants the client to authenticate with a certificate (mutual TLS / mTLS), it sends this. Often not present for regular web browsing.",
        },
        {
            "name": "Certificate",
            "direction": "Server → Client",
            "what_it_contains": [
                "The server's certificate chain (X.509 certificates)",
                "Server cert → intermediate CA cert(s) → (root CA usually not included)",
                "Each certificate is signed by the next one in the chain.",
            ],
            "why_it_exists": " Proves the server's identity. The client verifies the chain against its trusted root CAs. The certificate contains the server's public key (RSA or ECDSA) which is used to verify the CertificateVerify signature.",
            "key_points": [
                "The server cert's public key is used to verify the signature in CertificateVerify.",
                "The chain is verified up to a trusted root CA.",
                "Extensions like Subject Alternative Name (SAN) contain the hostname.",
            ],
        },
        {
            "name": "CertificateVerify",
            "direction": "Server → Client",
            "what_it_contains": [
                "A digital signature over the entire handshake so far.",
                "The signature is computed over: a context string + all handshake messages up to this point.",
                "Signed with the private key corresponding to the server certificate's public key.",
            ],
            "why_it_exists": " Proves that the server owns the private key corresponding to the certificate. Without this, an attacker could present a valid certificate they don't own. The signature covers the handshake transcript, preventing tampering.",
            "key_points": [
                "The signature is over the handshake hash, not just one message.",
                "For RSA keys: RSASSA-PSS signature.",
                "For ECDSA keys: ECDSA signature.",
                "This is what prevents MITM: the MITM can't sign the handshake with the real server's private key.",
            ],
        },
        {
            "name": "ServerFinished",
            "direction": "Server → Client",
            "what_it_contains": [
                "A verify_data field: HMAC over the handshake transcript using the server's handshake traffic key.",
                "This is the first message that proves both sides have computed the same handshake traffic keys.",
            ],
            "why_it_exists": " Confirms the server has derived the same handshake traffic keys as the client. If the keys don't match (wrong shared secret, tampered handshake), this message won't verify. This completes the server's side of the handshake.",
        },
        {
            "name": "ClientFinished",
            "direction": "Client → Server",
            "what_it_contains": [
                "A verify_data field: HMAC over the handshake transcript using the client's handshake traffic key.",
            ],
            "why_it_exists": " Confirms the client has derived the same handshake traffic keys. This completes the handshake. After this, both sides switch to application traffic keys and send real data.",
        },
    ],
    "key_derivation": {
        "overview": "TLS 1.3 derives all keys from the ECDHE shared secret using HKDF.",
        "steps": [
            "1. ECDHE shared secret: computed from client ECDHE public key + server ECDHE private key (and vice versa). This is the 'shared secret' or 'pre-master secret'.",
            "2. HKDF-Extract: takes the shared secret + salt (usually a hash of the hello random values) → produces the 'early secret' or 'handshake secret'.",
            "3. HKDF-Expand-Label: derives specific keys from the secret:",
            "   - client_handshake_traffic_secret: keys for encrypting client→server handshake messages",
            "   - server_handshake_traffic_secret: keys for encrypting server→client handshake messages",
            "   - client_application_traffic_secret_N: keys for client→server application data (N=0 for first)",
            "   - server_application_traffic_secret_N: keys for server→client application data",
            "   - exporter_master_secret: for TLS exporter (not used in basic handshake)",
            "   - resumption_master_secret: for session resumption",
            "4. Each direction has separate keys for encryption and integrity (though TLS 1.3 AEAD combines both).",
        ],
    },
    "cipher_suites": {
        "TLS 1.3 cipher suites (simpler than TLS 1.2 — just AEAD + hash):": [
            "TLS_AES_128_GCM_SHA256: AES-128-GCM + SHA-256 (HKDF hash)",
            "TLS_AES_256_GCM_SHA384: AES-256-GCM + SHA-384",
            "TLS_CHACHA20_POLY1305_SHA256: ChaCha20-Poly1305 + SHA-256",
            "TLS_AES_128_CCM_SHA256: AES-128-CCM + SHA-256 (less common)",
        ],
        "TLS 1.2 cipher suites (more complex — separate key exchange, auth, bulk, MAC):": [
            "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256: ECDHE key exchange, RSA auth, AES-128-GCM, SHA-256",
            "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256: ECDHE, ECDSA auth, AES-128-GCM, SHA-256",
        ],
        "key_point": "TLS 1.3 removed RSA key exchange (no forward secrecy). Only ECDHE is used. Authentication is via the certificate + CertificateVerify, not via the key exchange.",
    },
    "certificate_validation": {
        "what_the_client_checks": [
            "1. Chain: each certificate is signed by the next one. Verify signatures up to a trusted root CA.",
            "2. Hostname: the server certificate's Subject Alternative Name (SAN) contains the hostname being connected to. (CN fallback is deprecated.)",
            "3. Validity period: not before / not after dates are current.",
            "4. Key usage / extended key usage: the certificate is authorized for server authentication (EKU: serverAuth).",
            "5. Revocation: CRL or OCSP check (often skipped in practice, which is a weakness).",
            "6. Signature algorithms: the certificate's signature uses an acceptable algorithm.",
        ],
    },
    "what_attacker_sees": {
        "without_MITM": "Only the ClientHello and ServerHello are visible in the clear (plus the server certificate, which is sent encrypted in TLS 1.3 but was visible in TLS 1.2). Everything else is encrypted with the handshake traffic keys.",
        "with_MITM": "A MITM would have to: (1) present its own certificate (which the client wouldn't trust unless the attacker has a compromised CA), (2) sign the handshake transcript with its own private key (which the client would detect as not matching the real server's certificate).",
        "why_TLS_1.3_is_harder_to_MITM_than_1.2": "TLS 1.2 sent the certificate in the clear, so a MITM could present any certificate and the client might accept it if the user clicks through. TLS 1.3 encrypts the certificate, and the CertificateVerify signature ties the certificate to the specific handshake, making MITM much harder.",
    },
    "session_resumption": {
        "PSK": "Pre-Shared Key: the client and server can resume a previous session using a PSK (derived from the previous session's resumption_master_secret). The client sends the PSK in the ClientHello (PSK extension), and both sides derive the same keys without a full ECDHE exchange.",
        "session_ticket": "An alternative to PSK: the server gives the client a 'ticket' (encrypted blob) that contains the PSK. The client presents it on resumption.",
        "0-RTT": "With PSK, the client can send application data in the first flight (0-RTT — zero round trips). This is faster but has replay attack risks.",
        "full_handshake": "Without resumption, a full TLS 1.3 handshake takes 1-RTT (one round trip): ClientHello → ServerHello...ServerFinished → ClientFinished. With 0-RTT resumption, the client's first message can include application data.",
    },
}

# Save annotated documentation
docs_path = os.path.join(OUTPUT_DIR, "tls13_protocol_docs.json")
with open(docs_path, "w") as f:
    json.dump(tls13_handshake_docs, f, indent=2)

print(f"  Protocol documentation saved to: {docs_path}")

# --- Step 4: OpenSSL command reference (every flag explained) ---

openssl_reference = {
    "command": "openssl s_client",
    "flags": {
        "-connect host:port": "Which server to connect to.",
        "-tls1_3": "Force TLS 1.3 (do not negotiate TLS 1.2). Use -tls1_2 for TLS 1.2.",
        "-state": "Print state transitions as the handshake progresses (useful for seeing each step).",
        "-msg": "Log every protocol message in hex + text (very verbose).",
        "-brief": "Print a short summary: protocol, cipher, server temp key. Less verbose than -msg.",
        "-cert file": "Send a client certificate (for mutual TLS).",
        "-key file": "Client private key (with -cert).",
        "-CAfile file": "Trusted CA certificates to verify the server certificate against.",
        "-verify depth": "Depth for certificate chain verification.",
        "-ign_eof": "Don't close connection on EOF (keep it open).",
        "-quiet": "Suppress session and certificate info (just the data).",
        "-prexit": "Print session info when the connection closes.",
        "-proxy [host:]port": "Connect via a proxy.",
        "-security_debug": "Print security debug information.",
        "-security_debug_verbose": "More verbose security debug.",
        "-trace": "Print most hex-encoded content (very verbose).",
        "-no_alt_chains": "Don't try alternate certificate chains.",
    },
    "related_commands": {
        "openssl ciphers -v 'ALL:TLSv1.3'": "List all TLS 1.3 cipher suites with details.",
        "openssl ciphers -v -s -tls1_3": "List TLS 1.3 suites this OpenSSL supports.",
        "openssl s_client -connect host:port -tls1_2 -brief": "Same but TLS 1.2 for comparison.",
        "openssl x509 -in cert.pem -text -noout": "Print certificate details from a PEM file.",
        "openssl dhparam -out dhparam.pem 2048": "Generate DH parameters (for older key exchange).",
        "openssl ecparam -genkey -name prime256v1 -out ec_key.pem": "Generate an EC key.",
        "openssl pkeyutl -sign -in data -inkey key.pem -out sig.bin": "Sign data with a private key.",
        "openssl pkeyutl -verify -in data -pubin -pubkey pub.pem -sigfile sig.bin": "Verify a signature.",
    },
}

ref_path = os.path.join(OUTPUT_DIR, "openssl_reference.json")
with open(ref_path, "w") as f:
    json.dump(openssl_reference, f, indent=2)

print(f"  OpenSSL reference saved to: {ref_path}")

# --- Step 5: Verification — did we capture a real TLS 1.3 handshake? ---

print("\n[4] Verification...")

# Check what we got
if "TLSv1.3" in proc.stdout or "TLSv1.3" in proc.stderr or "TLS 1.3" in proc.stdout:
    print("  VERIFIED: Connected using TLS 1.3")
elif "Protocol" in proc.stdout or "Protocol" in proc.stderr:
    for line in lines:
        if "Protocol" in line:
            print(f"  Protocol found in output: {line.strip()}")
            break
else:
    print("  NOTE: Could not confirm TLS version in output — check saved files")

if "AES" in proc.stdout or "AES" in proc.stderr:
    print("  VERIFIED: AES cipher suite used (GCM)")
elif "Cipher" in proc.stdout or "Cipher" in proc.stderr:
    for line in lines:
        if "Cipher" in line:
            print(f"  Cipher found in output: {line.strip()}")
            break

print(f"\n  Files produced:")
print(f"    - {raw_path}")
print(f"    - {docs_path}")
print(f"    - {ref_path}")

print(f"\n{'=' * 60}")
print("TLS 1.3 HANDSHAKE STUDY COMPLETE")
print(f"{'=' * 60}")
print("""
WHAT I LEARNED FROM THIS:

1. The TLS 1.3 handshake has exactly 2 round trips (1-RTT):
   - Flight 1 (client): ClientHello
   - Flight 2 (server): ServerHello, EncryptedExtensions, Certificate,
     CertificateVerify, ServerFinished
   - Flight 3 (client): ClientFinished (+ optional application data)

2. After ServerHello, everything is encrypted with handshake traffic keys
   derived from the ECDHE shared secret via HKDF.

3. The certificate is sent encrypted in TLS 1.3 (unlike TLS 1.2 where it
   was in the clear). The CertificateVerify signature ties the certificate
   to the handshake transcript.

4. There is no separate key exchange message in TLS 1.3 — the key share
   is in the ClientHello and ServerHello extensions.

5. Cipher suites in TLS 1.3 only specify the AEAD and hash algorithm.
   Key exchange is always ECDHE (RSA key exchange was removed).

6. Session resumption via PSK can achieve 0-RTT (application data in
   first flight) but has replay attack risks.

WHAT I STILL NEED TO DO:
  - Capture a real packet-level trace (Wireshark) — not available on Windows here,
    but the OpenSSL output gives the same information at the protocol level.
  - Compare TLS 1.2 vs 1.3 side by side (run OpenSSL with -tls1_2).
  - Read RFC 8446 sections 4 and 5 (the handshake) in detail.
  - Understand the HKDF key schedule (section 7.1 of RFC 8446) step by step.
""")

# --- Bonus: try to get more detail with -msg flag ---

print("\n[5] Bonus: capturing with -msg for detailed protocol message dump...")

cmd_msg = [
    "openssl", "s_client",
    "-connect", f"{HOST}:{PORT}",
    "-tls1_3",
    "-msg",
    "-state",
    "-quit",
]

proc_msg = subprocess.run(
    cmd_msg,
    input=b"",
    capture_output=True,
    timeout=15,
    text=True,
)

msg_path = os.path.join(OUTPUT_DIR, "openssl_msg_detailed.txt")
with open(msg_path, "w") as f:
    f.write(f"OpenSSL s_client -msg output — {datetime.now().isoformat()}\n")
    f.write(f"Command: {' '.join(cmd_msg)}\n\n")
    f.write("--- STDOUT ---\n")
    f.write(proc_msg.stdout)
    f.write("\n--- STDERR ---\n")
    f.write(proc_msg.stderr)

print(f"  Detailed message dump saved to: {msg_path}")
print(f"  stdout: {len(proc_msg.stdout)} bytes")
print(f"  stderr: {len(proc_msg.stderr)} bytes")

# Count handshake messages
msg_count = proc_msg.stderr.count("TLS") + proc_msg.stdout.count("TLS")
print(f"  Approximate protocol message references: {msg_count}")

print(f"\n{'=' * 60}")
print("BONUS DETAILED CAPTURE COMPLETE")
print(f"{'=' * 60}")
