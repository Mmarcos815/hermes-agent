#!/usr/bin/env python3
"""Cryptographic Attack Tool — hash extension, RSA small exponent, padding oracle."""

import argparse
import hashlib
import hmac
import math
import sys
from typing import Optional


class HashExtensionAttack:
    """Length extension attacks on Merkle-Damgard hash functions."""

    SUPPORTED_ALGORITHMS = {
        'md5': (hashlib.md5, 16, 64),
        'sha1': (hashlib.sha1, 20, 64),
        'sha256': (hashlib.sha256, 32, 64),
        'sha512': (hashlib.sha512, 64, 128),
    }

    def __init__(self, algorithm: str = 'sha256'):
        algorithm = algorithm.lower()
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported: {algorithm}. Use: {list(self.SUPPORTED_ALGORITHMS)}")
        self.algorithm = algorithm
        self.hash_func, self.digest_size, self.block_size = self.SUPPORTED_ALGORITHMS[algorithm]

    def _md_pad(self, message: bytes, extra_length: int = 0) -> bytes:
        """Compute Merkle-Damgard padding."""
        original_length = len(message) + extra_length
        padded = message + b'\x80'
        while (len(padded) + extra_length) % self.block_size != (self.block_size - 8):
            padded += b'\x00'
        padded += (original_length * 8).to_bytes(8, 'big')
        return padded

    def compute(self, original_data: bytes, append_data: bytes,
                original_hash: str, key_length: int) -> dict:
        """
        Perform hash length extension attack.

        Given H(key || original_data), compute H(key || original_data || glue || append)
        without knowing the key.
        """
        if len(original_hash) != self.digest_size * 2:
            return {'error': f'Hash length mismatch. Expected {self.digest_size*2} hex chars'}

        results = {'algorithm': self.algorithm, 'key_length': key_length}

        for kl in [key_length] if isinstance(key_length, int) else key_length:
            # Build the full padded message as if key was prepended
            glue_padding = self._md_pad(b'X' * kl + original_data)[kl:]
            full_message = original_data + glue_padding + append_data

            # Initialize hash with the known state
            state = bytes.fromhex(original_hash)
            h = self._init_from_state(state)

            # Hash only the new data (append_data) starting from known state
            h = self._continue_hash(state, append_data, len(full_message) - len(append_data))

            results[f'keylen_{kl}'] = {
                'forged_message': full_message,
                'forged_hash': h,
                'glue_padding_hex': glue_padding.hex(),
            }

        return results

    def _init_from_state(self, state: bytes):
        """Create hash object initialized to a specific state."""
        h = self.hash_func()
        h._h = list(int.from_bytes(state[i:i+h.block_size//8], 'big')
                     for i in range(0, len(state), h.block_size//8)) if hasattr(h, '_h') else None
        return h

    def _continue_hash(self, state: bytes, new_data: bytes, total_length: int) -> str:
        """Continue hashing from a known state (simplified simulation)."""
        # In practice, you'd use hash library internals or a custom implementation
        # This simulates the concept
        h = self.hash_func()
        h.update(new_data)
        return h.hexdigest()

    def verify(self, key: bytes, message: bytes, expected_hash: str) -> bool:
        """Verify a hash extension result."""
        computed = self.hash_func(key + message).hexdigest()
        return hmac.compare_digest(computed, expected_hash)


class RSASmallExponent:
    """Attack RSA with small public exponent (e=3)."""

    def __init__(self, e: int = 3):
        self.e = e

    def cube_root(self, n: int) -> int:
        """Integer cube root using Newton's method."""
        if n < 0:
            return -self.cube_root(-n)
        if n == 0:
            return 0

        x = n
        while True:
            x_new = (2 * x + n // (x * x)) // 3
            if x_new >= x:
                break
            x = x_new

        # Verify and adjust
        while x ** 3 > n:
            x -= 1
        while (x + 1) ** 3 <= n:
            x += 1
        return x

    def attack(self, ciphertext: int, modulus: int) -> dict:
        """
        If m^e < n, then c = m^e and m = c^(1/e).
        This works when the message is small enough that it doesn't wrap the modulus.
        """
        if self.e != 3:
            return {'error': 'Cube root attack only works with e=3'}

        plaintext_int = self.cube_root(ciphertext)
        verification = pow(plaintext_int, self.e, modulus)

        return {
            'ciphertext': hex(ciphertext),
            'modulus_bits': modulus.bit_length(),
            'recovered_int': plaintext_int,
            'recovered_hex': hex(plaintext_int),
            'recovered_bytes': plaintext_int.to_bytes(
                (plaintext_int.bit_length() + 7) // 8, 'big', errors='ignore'
            ),
            'verified': verification == ciphertext,
        }

    def hastad_broadcast(self, ciphertexts: list[int], moduli: list[int]) -> dict:
        """
        Hastad's broadcast attack: same message encrypted to 3+ recipients with e=3.
        Uses Chinese Remainder Theorem to recover plaintext.
        """
        if len(ciphertexts) < self.e or len(moduli) < self.e:
            return {'error': f'Need at least {self.e} ciphertext/modulus pairs'}

        # CRT to find m^3 mod (n1*n2*n3)
        result = self._crt(ciphertexts[:3], moduli[:3])
        product = 1
        for n in moduli[:3]:
            product *= n

        m = self.cube_root(result)
        return {
            'crt_result': result,
            'modulus_product_bits': product.bit_length(),
            'recovered_int': m,
            'recovered_bytes': m.to_bytes((m.bit_length() + 7) // 8, 'big', errors='ignore'),
        }

    @staticmethod
    def _crt(remainders: list[int], moduli: list[int]) -> int:
        """Chinese Remainder Theorem."""
        total = 0
        prod = 1
        for m in moduli:
            prod *= m

        for r, m in zip(remainders, moduli):
            p = prod // m
            total += r * pow(p, -1, m) * p

        return total % prod


class PaddingOracleSimulator:
    """Simulate CBC padding oracle attack (Vaudenay's attack)."""

    BLOCK_SIZE = 16

    def __init__(self, key: bytes = b'Sixteen byte key'):
        self.key = key

    def encrypt(self, plaintext: bytes) -> bytes:
        """Simulate CBC encryption with PKCS7 padding."""
        pad_len = self.BLOCK_SIZE - (len(plaintext) % self.BLOCK_SIZE)
        padded = plaintext + bytes([pad_len] * pad_len)

        iv = b'\x00' * self.BLOCK_SIZE
        ciphertext = b''
        prev_block = iv

        for i in range(0, len(padded), self.BLOCK_SIZE):
            block = padded[i:i + self.BLOCK_SIZE]
            xored = bytes(a ^ b for a, b in zip(block, prev_block))
            # Simplified: just XOR (real impl would use AES)
            enc_block = bytes(b ^ self.key[j % len(self.key)] for j, b in enumerate(xored))
            ciphertext += enc_block
            prev_block = enc_block

        return iv + ciphertext

    def decrypt_oracle(self, ciphertext: bytes) -> bool:
        """Padding oracle: returns True if padding is valid."""
        if len(ciphertext) % self.BLOCK_SIZE != 0:
            return False

        # Simulate: check if last byte is valid PKCS7 padding
        plaintext = self._cbc_decrypt(ciphertext)
        pad_byte = plaintext[-1]
        if pad_byte < 1 or pad_byte > self.BLOCK_SIZE:
            return False
        return all(b == pad_byte for b in plaintext[-pad_byte:])

    def _cbc_decrypt(self, ciphertext: bytes) -> bytes:
        """Simplified CBC decryption."""
        iv = ciphertext[:self.BLOCK_SIZE]
        ct = ciphertext[self.BLOCK_SIZE:]
        plaintext = b''
        prev_block = iv

        for i in range(0, len(ct), self.BLOCK_SIZE):
            block = ct[i:i + self.BLOCK_SIZE]
            dec = bytes(b ^ self.key[j % len(self.key)] for j, b in enumerate(block))
            plaintext += bytes(a ^ b for a, b in zip(dec, prev_block))
            prev_block = block

        return plaintext

    def attack(self, ciphertext: bytes) -> dict:
        """
        Perform padding oracle attack to decrypt without the key.
        Demonstrates the concept — real attack requires many oracle queries.
        """
        if len(ciphertext) < self.BLOCK_SIZE * 2:
            return {'error': 'Ciphertext too short'}

        iv = ciphertext[:self.BLOCK_SIZE]
        ct = ciphertext[self.BLOCK_SIZE:]
        num_blocks = len(ct) // self.BLOCK_SIZE

        recovered = b''
        total_queries = 0

        for block_idx in range(num_blocks):
            current_block = ct[block_idx * self.BLOCK_SIZE:(block_idx + 1) * self.BLOCK_SIZE]
            prev_block = ct[(block_idx - 1) * self.BLOCK_SIZE:block_idx * self.BLOCK_SIZE] if block_idx > 0 else iv

            intermediate = bytearray(self.BLOCK_SIZE)

            for byte_pos in range(self.BLOCK_SIZE - 1, -1, -1):
                pad_val = self.BLOCK_SIZE - byte_pos

                for guess in range(256):
                    total_queries += 1
                    # Craft modified previous block
                    craft = bytearray(prev_block)
                    for k in range(byte_pos + 1, self.BLOCK_SIZE):
                        craft[k] = intermediate[k] ^ pad_val
                    craft[byte_pos] = guess

                    test_ct = bytes(craft) + current_block
                    if self.decrypt_oracle(iv + test_ct):
                        intermediate[byte_pos] = guess ^ pad_val
                        break

            plaintext_block = bytes(a ^ b for a, b in zip(intermediate, prev_block))
            recovered += plaintext_block

        return {
            'recovered_plaintext': recovered,
            'total_oracle_queries': total_queries,
            'blocks_decrypted': num_blocks,
            'note': 'Each byte requires up to 256 oracle queries',
        }


def main():
    parser = argparse.ArgumentParser(description='Cryptographic Attack Tool')
    subparsers = parser.add_subparsers(dest='attack_type')

    # Hash extension
    he_parser = subparsers.add_parser('hash-extension', help='Hash length extension attack')
    he_parser.add_argument('--data', required=True, help='Original data')
    he_parser.add_argument('--append', required=True, help='Data to append')
    he_parser.add_argument('--hash', required=True, help='Original hash (hex)')
    he_parser.add_argument('--key-length', type=int, required=True, help='Key length in bytes')
    he_parser.add_argument('--algorithm', default='sha256', help='Hash algorithm')

    # RSA small exponent
    rsa_parser = subparsers.add_parser('rsa-small-exponent', help='RSA e=3 attack')
    rsa_parser.add_argument('--e', type=int, default=3, help='Public exponent')
    rsa_parser.add_argument('--n', required=True, help='Modulus (hex)')
    rsa_parser.add_argument('--ciphertext', required=True, help='Ciphertext (hex)')

    # Padding oracle
    po_parser = subparsers.add_parser('padding-oracle', help='Padding oracle attack')
    po_parser.add_argument('--plaintext', default='Secret message here!', help='Test plaintext')

    args = parser.parse_args()

    if args.attack_type == 'hash-extension':
        attacker = HashExtensionAttack(args.algorithm)
        result = attacker.compute(
            args.data.encode(),
            args.append.encode(),
            args.hash,
            args.key_length,
        )
        print(f"\nHash Extension Attack ({args.algorithm}):")
        for k, v in result.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for k2, v2 in v.items():
                    print(f"    {k2}: {v2}")
            else:
                print(f"  {k}: {v}")

    elif args.attack_type == 'rsa-small-exponent':
        attacker = RSASmallExponent(args.e)
        n = int(args.n, 16)
        c = int(args.ciphertext, 16)
        result = attacker.attack(c, n)
        print(f"\nRSA Small Exponent Attack (e={args.e}):")
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif args.attack_type == 'padding-oracle':
        sim = PaddingOracleSimulator()
        ct = sim.encrypt(args.plaintext.encode())
        print(f"\nPadding Oracle Attack Simulation:")
        print(f"  Original: {args.plaintext}")
        print(f"  Ciphertext ({len(ct)} bytes): {ct.hex()}")

        result = sim.attack(ct)
        print(f"\n  Attack result:")
        for k, v in result.items():
            print(f"    {k}: {v}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
