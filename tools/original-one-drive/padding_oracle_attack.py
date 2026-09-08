#!/usr/bin/env python3
"""
Padding Oracle Attack Demonstration — Phase 1C Learning Project

This demonstrates the classic CBC padding oracle attack (Vaudenay, 2002).
We build a vulnerable "server" that decrypts CBC ciphertexts and leaks
whether the PKCS#7 padding is valid, then use that oracle to decrypt
a ciphertext WITHOUT knowing the key.

Purpose: Understand exactly how padding oracles work, what information
each query leaks, and how the attack reconstructs plaintext byte by byte.

Reference: Vaudenay, "Security Flaws Induced by CBC Padding — Applications
to SSL, IPSEC, WTLS..." (2002)
"""

import os
import json
from typing import List, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# ============================================================================
# SETUP: AES-CBC with PKCS#7 padding
# ============================================================================

AES_KEY = os.urandom(16)   # 128-bit key (unknown to the attacker)
AES_IV = os.urandom(16)    # Initialization vector

OUTPUT_DIR = "/c/Users/mobil/orca/projects/my 1st/crypto_study"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    """Pad data to a multiple of block_size using PKCS#7."""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    """Remove PKCS#7 padding. Raises ValueError if padding is invalid."""
    if len(data) % block_size != 0:
        raise ValueError("Data not a multiple of block size")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise ValueError(f"Invalid padding byte: {pad_len}")
    for i in range(pad_len):
        if data[-(i+1)] != pad_len:
            raise ValueError(f"Inconsistent padding at position {i}")
    return data[:-pad_len]

def encrypt_cbc(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt with AES-CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded = pkcs7_pad(plaintext)
    return encryptor.update(padded) + encryptor.finalize()

def decrypt_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt with AES-CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    return pkcs7_unpad(padded)

# ============================================================================
# THE VULNERABLE SERVER: a padding oracle
# ============================================================================

class PaddingOracle:
    """
    A server that decrypts CBC ciphertexts and tells the attacker whether
    the PKCS#7 padding is valid. This is the classic padding oracle.

    In a real system, this oracle might be:
    - A web server that returns different error messages for bad padding
      vs. bad authentication
    - A TLS implementation that closes the connection differently
    - Any system that leaks padding validity through timing or responses
    """

    def __init__(self, key: bytes, iv: bytes):
        self.key = key
        self.iv = iv

    def decrypt_and_check_padding(self, ciphertext: bytes) -> bool:
        """
        Decrypt the ciphertext and return True if padding is valid,
        False if padding is invalid.
        
        THIS IS THE ORACLE — it leaks one bit of information per query:
        "does the decrypted plaintext have valid PKCS#7 padding?"
        """
        try:
            plaintext = decrypt_cbc(ciphertext, self.key, self.iv)
            return True  # Valid padding
        except ValueError:
            return False  # Invalid padding

# ============================================================================
# THE ATTACK: decrypt a ciphertext using only the padding oracle
# ============================================================================

class PaddingOracleAttacker:
    """
    Given only a padding oracle (a function that says "valid padding: yes/no"
    for any ciphertext), decrypt the plaintext WITHOUT knowing the key.

    The attack works because:
    1. In CBC, decryption of block i is: P_i = D(C_i) XOR C_{i-1}
    2. If we modify C_{i-1} (the previous block), we can control what
       plaintext byte we get after decryption.
    3. By trying all 256 possible values for a byte of C_{i-1}, we can
       find the one that produces valid padding — and that tells us the
       corresponding plaintext byte.
    4. We work backward from the last byte to the first, reconstructing
       the entire plaintext.
    """

    def __init__(self, oracle: PaddingOracle):
        self.oracle = oracle

    def attack(self, ciphertext: bytes) -> bytes:
        """
        Decrypt ciphertext using only the padding oracle.
        
        Strategy (Vaudenay attack):
        - Work one block at a time, from last block to first.
        - For each block, work one byte at a time, from last byte to first.
        - For byte position j (from the end), try all 256 values of the
          modified previous-block byte until we get valid padding.
        - The valid padding tells us what the decrypted byte should be.
        - XOR with the known intermediate value to get the plaintext byte.
        """
        block_size = 16
        blocks = [ciphertext[i:i+block_size] for i in range(0, len(ciphertext), block_size)]
        
        # We can only attack blocks that have a preceding block.
        # The IV acts as the "previous block" for the first block.
        # The attack modifies the previous ciphertext block to control
        # what the oracle sees as plaintext.
        
        plaintext_blocks = []
        
        # Start with the IV as the "previous block" for block 0
        prev_block = self.oracle.iv
        
        for block_idx in range(len(blocks)):
            current_block = blocks[block_idx]
            intermediate = self._decrypt_block(current_block, prev_block)
            # Plaintext = intermediate XOR previous_block
            plaintext_block = bytes([intermediate[i] ^ prev_block[i] for i in range(block_size)])
            plaintext_blocks.append(plaintext_block)
            prev_block = current_block  # This block becomes previous for next
        
        # Concatenate and remove padding
        full_plaintext = b"".join(plaintext_blocks)
        try:
            return pkcs7_unpad(full_plaintext, block_size)
        except ValueError:
            # If unpadding fails, return the raw plaintext (might be truncated)
            return full_plaintext

    def _decrypt_block(self, block: bytes, prev_block: bytes) -> List[int]:
        """
        Recover the intermediate value (D(block)) for one block using
        the padding oracle.
        
        Textbook Vaudenay attack — clean, no complex verification.
        
        For each byte position from last to first:
        1. Set already-solved bytes in modified_prev so they produce
           the target padding value (target_pad = block_size - byte_pos).
        2. Brute-force modified_prev[byte_pos] through all 256 values.
           The first value that makes the oracle return True gives us
           intermediate[byte_pos] = target_pad XOR candidate.
        3. Move to the next byte.
        
        Why this works without explicit verification:
        - For byte 15 (last byte), multiple candidates can produce valid
          padding (for any padding value 1..16 where the unmodified bytes
          happen to match). We pick the first one found.
        - For byte 14, we set target_pad=2 and modified_prev[15] such that
          plaintext[15] = 2. Now ONLY the candidate that makes plaintext[14] = 2
          will validate — because plaintext[15] is forced to 2, and the oracle
          checks BOTH bytes for padding=2.
        - If our byte-15 candidate was wrong, NO value for byte 14 will work
          (because plaintext[15] would be wrong). The attack would fail at byte 14.
          So correctness at byte 14 implicitly verifies byte 15.
        - This cascading consistency check continues for all bytes.
        """
        block_size = 16
        intermediate = [0] * block_size
        modified_prev = list(prev_block)
        DEBUG = os.environ.get("PADDING_DEBUG", "0") == "1"
        
        for byte_pos in range(block_size - 1, -1, -1):
            target_pad = block_size - byte_pos
            
            if DEBUG:
                print(f"  Byte {byte_pos}: target_pad={target_pad}, prev_block={bytes(modified_prev).hex()}")
            
            # Set already-determined bytes (to the right) to produce target_pad
            # plaintext[i] = intermediate[i] XOR modified_prev[i]
            # We want plaintext[i] = target_pad
            # So: modified_prev[i] = intermediate[i] XOR target_pad
            for i in range(byte_pos + 1, block_size):
                modified_prev[i] = intermediate[i] ^ target_pad
            
            if DEBUG:
                print(f"    After setting tail: modified_prev={bytes(modified_prev).hex()}")
                print(f"    Brute-forcing byte {byte_pos}...")
            
            # Brute-force: find the modified_prev[byte_pos] value that
            # makes the oracle return True (valid padding)
            candidate = None
            candidate_idx = None
            for idx, guess in enumerate(range(256)):
                modified_prev[byte_pos] = guess
                ct = bytes(modified_prev) + block
                if self.oracle.decrypt_and_check_padding(ct):
                    candidate = guess
                    candidate_idx = idx
                    if DEBUG:
                        print(f"    Found candidate={guess} at idx={idx} (oracle=True)")
                    break
                if DEBUG and idx < 10:
                    # Show first few attempts
                    pt_byte = intermediate[byte_pos] ^ guess if intermediate[byte_pos] else '?'
                    print(f"    Try {guess}: modified_prev[byte_pos]={guess}, ct={ct.hex()}")
            
            if candidate is None:
                raise ValueError(f"Could not find valid padding for byte {byte_pos}")
            
            if DEBUG:
                print(f"    candidate={candidate}, target_pad={target_pad}")
                print(f"    intermediate[{byte_pos}] = {target_pad} XOR {candidate} = {target_pad ^ candidate}")
            
            # Compute intermediate byte: intermediate = target_pad XOR candidate
            # Because: plaintext[byte_pos] = intermediate[byte_pos] XOR candidate = target_pad
            # Therefore: intermediate[byte_pos] = target_pad XOR candidate
            intermediate[byte_pos] = target_pad ^ candidate
            
            # Keep modified_prev[byte_pos] = candidate for the next iteration
            # (it will be overwritten when we set the tail for the new target_pad)
            modified_prev[byte_pos] = candidate
        
        if DEBUG:
            print(f"  Block intermediate: {intermediate}")
            print(f"  Block plaintext: {bytes([intermediate[i] ^ prev_block[i] for i in range(block_size)]).hex()}")
        
        return intermediate


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate():
    print("=" * 60)
    print("PADDING ORACLE ATTACK DEMONSTRATION")
    print("=" * 60)
    print("""
This demonstrates the Vaudenay CBC padding oracle attack.

Scenario:
  - A server encrypts a secret message with AES-CBC + PKCS#7 padding.
  - The server has a bug: it tells anyone whether a submitted ciphertext
    has valid padding (without revealing the plaintext or key).
  - An attacker can use this "oracle" to decrypt the ciphertext WITHOUT
    knowing the key.

How it works:
  1. CBC decryption: P_i = AES_D(C_i) XOR C_{i-1}
  2. If we modify C_{i-1}, we control P_i (because AES_D(C_i) is fixed).
  3. PKCS#7 padding requires the last N bytes to all equal N.
  4. By trying all 256 values of C_{i-1}[j], we can find the one that
     makes P_i[j] = (block_size - j) — the padding value for that position.
  5. That tells us AES_D(C_i)[j], and from there we get the plaintext.
""")

    # --- Step 1: Create a secret and encrypt it ---
    print("[1] Encrypting a secret message...")
    
    secret = b"SuperSecretAttackPayload123"  # 27 bytes
    print(f"    Secret: '{secret.decode()}' ({len(secret)} bytes)")
    
    ciphertext = encrypt_cbc(secret, AES_KEY, AES_IV)
    print(f"    Ciphertext: {ciphertext.hex()}")
    print(f"    Length: {len(ciphertext)} bytes ({len(ciphertext) // 16} blocks)")
    print(f"    Key: {AES_KEY.hex()} (KNOWN TO US, NOT TO ATTACKER)")
    print(f"    IV: {AES_IV.hex()}")
    
    # Save the challenge
    challenge = {
        "ciphertext": ciphertext.hex(),
        "iv": AES_IV.hex(),
        "secret_length": len(secret),
        "challenge": "Decrypt this without the key, using only the padding oracle",
    }
    with open(os.path.join(OUTPUT_DIR, "challenge.json"), "w") as f:
        json.dump(challenge, f, indent=2)
    print(f"    Challenge saved.")

    # --- Step 2: The attacker only has the oracle ---
    print("\n[2] The attacker's capabilities:")
    print("    - Can submit ANY ciphertext to the oracle")
    print("    - Oracle returns: True (valid padding) or False (invalid padding)")
    print("    - Does NOT know the key")
    print("    - Does NOT know the plaintext")
    print("    - Does NOT know anything except the ciphertext and IV")
    
    oracle = PaddingOracle(AES_KEY, AES_IV)
    attacker = PaddingOracleAttacker(oracle)
    
    # --- Step 3: Run the attack ---
    print("\n[3] Running the padding oracle attack...")
    
    # Count queries
    query_count = [0]
    original_decrypt = oracle.decrypt_and_check_padding
    def counting_oracle(ct):
        query_count[0] += 1
        return original_decrypt(ct)
    attacker.oracle.decrypt_and_check_padding = counting_oracle
    
    recovered = attacker.attack(ciphertext)
    print(f"    Attack completed!")
    print(f"    Queries made: {query_count[0]}")
    print(f"    Expected queries: ~{16 * 16 * len(ciphertext) // 16} (256 per byte)")
    
    # --- Step 4: Verify ---
    print("\n[4] Verification:")
    print(f"    Original:  '{secret.decode()}'")
    print(f"    Recovered: '{recovered.decode()}'")
    
    if secret == recovered:
        print("\n    SUCCESS! Attacker decrypted the ciphertext without the key.")
    else:
        print(f"\n    PARTIAL: recovered {recovered[:len(secret)]}")
        # Try to see what we got
        print(f"    Raw recovered ({len(recovered)} bytes): {recovered.hex()}")
    
    # --- Step 5: Save results ---
    results = {
        "secret": secret.decode(),
        "recovered": recovered.decode() if isinstance(recovered, bytes) else recovered,
        "match": secret == recovered,
        "queries": query_count[0],
        "ciphertext": ciphertext.hex(),
        "key": AES_KEY.hex(),
        "iv": AES_IV.hex(),
        "explanation": {
            "attack_name": "Vaudenay CBC Padding Oracle Attack (2002)",
            "how_it_works": "Modify the previous ciphertext block byte by byte. For each modification, the oracle tells us whether the decrypted plaintext has valid padding. By building up the padding byte by byte, we can determine the intermediate value (AES_D(block)) for each block, and from there compute the plaintext.",
            "queries_per_byte": 256,
            "total_queries_theoretical": 256 * 16 * (len(ciphertext) // 16),
            "actual_queries": query_count[0],
            "why_it_works": "CBC decryption XORS the decrypted block with the previous ciphertext block. By controlling the previous block, we control the plaintext. The padding oracle tells us when we've set a plaintext byte to a specific value (the padding value).",
        }
    }
    
    with open(os.path.join(OUTPUT_DIR, "attack_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[5] Results saved to: {os.path.join(OUTPUT_DIR, 'attack_results.json')}")
    
    # --- Step 6: Visual explanation ---
    print("\n" + "=" * 60)
    print("VISUAL EXPLANATION")
    print("=" * 60)
    print("""
CBC Decryption (what happens inside the block cipher):

    Ciphertext Block i:    [C_i]
              |            |
              v            v
         AES_Decrypt    (block cipher decryption)
              |            |
              v            v
         Intermediate:  [I_i = AES_D(C_i)]
              |            |
              +------------+------------+
              |            |            |
              v            v            v
         XOR with    XOR with      XOR with
         C_{i-1}[0]  C_{i-1}[1]    C_{i-1}[15]
              |            |            |
              v            v            v
         Plaintext:   [P_i[0]     P_i[1]    ...  P_i[15]]
              |            |            |
              +------------+------------+

The attacker modifies C_{i-1} (the previous ciphertext block).
This changes P_i = I_i XOR C_{i-1}.

When the attacker sets C_{i-1}[15] such that P_i[15] = 0x01,
the padding is valid (PKCS#7 says last byte = 1 means 1 byte of padding).
That tells the attacker that I_i[15] = C_{i-1}[15] XOR 0x01.

Then the attacker sets C_{i-1}[14] and C_{i-1}[15] such that
P_i[14:16] = [0x02, 0x02], and brute-forces C_{i-1}[14].
When the oracle says valid, the attacker knows I_i[14].

Continue for all 16 bytes, then move to the next block.

This is why padding oracles are dangerous: ONE BIT of information
(valid/invalid padding) per query, combined with the CBC structure,
is enough to recover the entire plaintext.
""")

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("""
REAL-WORLD IMPACT:
  - This exact attack has been used against real TLS implementations,
    web servers, and encrypted data storage.
  - The "Lucky Thirteen" attack (2013) was a timing-based padding oracle
    against TLS CBC mode.
  - Many web applications have been compromised because they returned
    different error messages for "bad padding" vs. "bad MAC" — giving
    the attacker the oracle for free.

HOW TO PREVENT:
  1. Use authenticated encryption (AES-GCM, ChaCha20-Poly1305) instead
     of CBC + separate MAC. AEAD verifies integrity BEFORE decryption.
  2. In TLS 1.3, CBC was removed entirely — only AEAD cipher suites.
  3. If you must use CBC, verify the MAC BEFORE checking padding, and
     use constant-time comparison for both. Never leak which check failed.
  4. Don't return different error messages for padding vs. authentication
     failures. Generic "decryption failed" is safe.
""")


if __name__ == "__main__":
    demonstrate()
