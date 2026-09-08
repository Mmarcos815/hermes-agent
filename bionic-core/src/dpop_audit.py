# DPoP (Demonstration of Proof-of-Possession) — RFC 9449
# https://www.rfc-editor.org/rfc/rfc9449.html

import hashlib
import base64
import json
import time
import hmac
import uuid
import os


class DPoPKeyPair:
    """Manages DPoP key pair per RFC 9449."""
    
    def __init__(self, private_key_pem=None):
        self.private_key = private_key_pem or self._generate_ec_key()
        self.public_key = self._derive_public_key(self.private_key)
        self.fingerprint = self._compute_fingerprint()
        self.issued_at = int(time.time())
        self.expires_at = self.issued_at + 86400  # 24 hours
    
    def _generate_ec_key(self):
        """Generate a new EC P-256 private key."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        private_key = ec.generate_private_key(ec.SECP256R1())
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    
    def _derive_public_key(self, private_key_pem):
        """Derive the public key in JWK format."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        pub_key = private_key.public_key()
        return pub_key.public_bytes(
            encoding=serialization.Encoding.JWK,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode('utf-8')
    
    def _compute_fingerprint(self):
        """Compute thumbprint of the public key."""
        return hashlib.sha256(
            self.public_key.encode('utf-8')
        ).hexdigest()[:16]
    
    def generate_dpop_proof(self, http_method, request_uri, access_token):
        """
        Generate a DPoP proof for an HTTP request.
        
        Per RFC 9449: dpop = base64url(
          SHA-256(
            JWK thumbprint || "." || 
            CNonce || "." || 
            timestamp || "." ||
            http-method || ":" || request-target
          )
        )
        """
        # Create the JWK thumbprint
        jwk = json.loads(self.public_key)
        jwk_thumbprint = base64.urlsafe_b64encode(
            hashlib.sha256(
                json.dumps(jwk, separators=(',', ':')).encode()
            ).digest()
        ).rstrip(b'=').decode('utf-8')
        
        # Generate a client nonce
        c_nonce = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode('utf-8')
        
        # Timestamp
        t = int(time.time())
        
        # Create the proof input string
        proof_input = f"{jwk_thumbprint}.{c_nonce}.{t}.{http_method.upper()}:{request_uri}"
        
        # Compute SHA-256 and base64url encode
        proof = base64.urlsafe_b64encode(
            hashlib.sha256(proof_input.encode('utf-8')).digest()
        ).rstrip(b'=').decode('utf-8')
        
        return proof
    
    def to_dict(self):
        """Serialize the key pair to a dictionary (for storage)."""
        return {
            "fingerprint": self.fingerprint,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "public_key": self.public_key,
        }


class AuditLogger:
    """Structured audit logger for Hermes Agent operations."""
    
    def __init__(self, log_dir=None):
        self.log_dir = log_dir or os.path.expanduser("~/.hermes/logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_id = f"session_{int(time.time())}"
        self.entries = []
    
    def log(self, level, category, message, details=None, severity="info"):
        """
        Log an audit entry.
        
        Returns the entry ID.
        """
        entry_id = f"{self.session_id}_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        entry = {
            "id": entry_id,
            "timestamp": int(time.time()),
            "session_id": self.session_id,
            "level": level,
            "category": category,
            "message": message,
            "severity": severity,
            "details": details or {},
        }
        
        self.entries.append(entry)
        self._write_entry(entry)
        
        return entry_id
    
    def _write_entry(self, entry):
        """Write a single audit entry to the log file."""
        log_file = os.path.join(self.log_dir, f"audit_{self.session_id}.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')
    
    def get_entries(self, since=None):
        """Get audit entries, optionally filtered by timestamp."""
        entries = self.entries
        if since:
            entries = [e for e in entries if e["timestamp"] > since]
        return entries
    
    def get_summary(self):
        """Get audit summary statistics."""
        if not self.entries:
            return {"total": 0, "by_level": {}, "by_category": {}}
        
        by_level = {}
        by_category = {}
        for entry in self.entries:
            level = entry["level"]
            category = entry["category"]
            
            by_level[level] = by_level.get(level, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            "total": len(self.entries),
            "by_level": by_level,
            "by_category": by_category,
        }


# Convenience function for quick audit logging
def audit(level, category, message, **kwargs):
    """Quick audit logging function."""
    logger = AuditLogger()
    return logger.log(level, category, message, kwargs)


# Security helper functions
def validate_jwt_token(token):
    """Validate a JWT token and return payload (simplified)."""
    try:
        # JWT structure validation
        parts = token.split('.')
        if len(parts) != 3:
            return {"valid": False, "error": "Invalid JWT structure"}
        
        # In production, validate signature with public key
        # For now, just decode the payload
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return {"valid": True, "payload": payload}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_token_revocation(token_id, revocation_list):
    """Check if a token has been revoked."""
    return token_id in revocation_list


def generate_audit_hash(entry):
    """Generate a tamper-evident hash for an audit entry."""
    # Sort keys for deterministic output
    sorted_entry = json.dumps(entry, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(sorted_entry.encode('utf-8')).hexdigest()[:16]