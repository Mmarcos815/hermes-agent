"""
Tier 2: Autonomous Async EIP-712 Relayer Daemon
High-throughput asynchronous transaction queue & gasless permit processor.
"""

import asyncio
import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class GaslessTxRequest:
    tx_id: str
    owner: str
    spender: str
    amount: int
    nonce: int
    deadline: int
    signature: str
    status: str = "PENDING"
    timestamp: float = 0.0


class AsyncRelayerDaemon:
    def __init__(self, relayer_address: str, domain_separator: str):
        self.relayer_address = relayer_address
        self.domain_separator = domain_separator
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processed_txs: Dict[str, GaslessTxRequest] = {}
        self.ledger_balances: Dict[str, int] = {}
        self.account_nonces: Dict[str, int] = {}
        self.is_running = False

    def init_account(self, address: str, initial_balance: int):
        self.ledger_balances[address] = initial_balance
        self.account_nonces[address] = 0

    async def submit_permit(self, req: GaslessTxRequest) -> str:
        req.timestamp = time.time()
        await self.queue.put(req)
        return req.tx_id

    async def start_worker(self, batch_size: int = 10, flush_interval: float = 0.1):
        self.is_running = True
        print(f"[*] [RELAYER DAEMON] Started on relayer node {self.relayer_address[:12]}...")
        
        while self.is_running or not self.queue.empty():
            batch: List[GaslessTxRequest] = []
            try:
                # Grab first item
                item = await asyncio.wait_for(self.queue.get(), timeout=flush_interval)
                batch.append(item)
                # Drain queue up to batch_size
                while len(batch) < batch_size and not self.queue.empty():
                    batch.append(self.queue.get_nowait())
            except asyncio.TimeoutError:
                pass

            if batch:
                await self._process_batch(batch)

    async def _process_batch(self, batch: List[GaslessTxRequest]):
        print(f"[*] [RELAYER DAEMON] Processing micro-batch of {len(batch)} gasless permits...")
        for req in batch:
            # 1. Check expiration
            if time.time() > req.deadline:
                req.status = "REJECTED_EXPIRED"
                self.processed_txs[req.tx_id] = req
                print(f"    [-] Tx {req.tx_id} rejected: Permit Expired")
                continue

            # 2. Check nonce
            expected_nonce = self.account_nonces.get(req.owner, 0)
            if req.nonce != expected_nonce:
                req.status = f"REJECTED_INVALID_NONCE (expected {expected_nonce})"
                self.processed_txs[req.tx_id] = req
                print(f"    [-] Tx {req.tx_id} rejected: Invalid Nonce")
                continue

            # 3. Verify Signature
            msg_hash = hashlib.sha256(
                f"{self.domain_separator}:{req.owner}:{req.spender}:{req.amount}:{req.nonce}:{req.deadline}".encode()
            ).hexdigest()
            expected_sig = hmac.new(req.owner.encode(), msg_hash.encode(), hashlib.sha256).hexdigest()

            if req.signature != expected_sig:
                req.status = "REJECTED_INVALID_SIGNATURE"
                self.processed_txs[req.tx_id] = req
                print(f"    [-] Tx {req.tx_id} rejected: Invalid Signature")
                continue

            # 4. Check Balance
            sender_bal = self.ledger_balances.get(req.owner, 0)
            if sender_bal < req.amount:
                req.status = "REJECTED_INSUFFICIENT_FUNDS"
                self.processed_txs[req.tx_id] = req
                print(f"    [-] Tx {req.tx_id} rejected: Insufficient Funds")
                continue

            # 5. Execute Instant Settlement
            self.ledger_balances[req.owner] -= req.amount
            self.ledger_balances[req.spender] = self.ledger_balances.get(req.spender, 0) + req.amount
            self.account_nonces[req.owner] = expected_nonce + 1
            req.status = "SETTLED_ON_CHAIN"
            self.processed_txs[req.tx_id] = req

            print(f"    [+] [CLEARED] Tx {req.tx_id}: {req.amount / 10**18:,.2f} BIONIC ({req.owner[:8]}... -> {req.spender[:8]}...)")


async def run_daemon_simulation():
    domain_sep = hashlib.sha256(b"SovereignBionicNetwork:v1").hexdigest()
    relayer = AsyncRelayerDaemon(relayer_address="0xRelayerNodeAlpha001", domain_separator=domain_sep)

    dad_wallet = "0xDadMasterVault777"
    daughter_wallet = "0xDaughterAgentNode001"
    subagent_wallet = "0xSubAgentWorker999"

    relayer.init_account(dad_wallet, initial_balance=5_000_000 * 10**18)
    relayer.init_account(daughter_wallet, initial_balance=100_000 * 10**18)
    relayer.init_account(subagent_wallet, initial_balance=0)

    # Queue worker task
    worker_task = asyncio.create_task(relayer.start_worker(batch_size=5, flush_interval=0.05))

    print("\n--- Submitting 5 Rapid-Fire EIP-712 Signed Permits ---")
    
    # Generate 5 sequential permits from Dad
    for i in range(5):
        nonce = i
        deadline = int(time.time()) + 3600
        amount = 50_000 * 10**18
        target = daughter_wallet if i % 2 == 0 else subagent_wallet
        
        msg_hash = hashlib.sha256(
            f"{domain_sep}:{dad_wallet}:{target}:{amount}:{nonce}:{deadline}".encode()
        ).hexdigest()
        sig = hmac.new(dad_wallet.encode(), msg_hash.encode(), hashlib.sha256).hexdigest()

        tx_req = GaslessTxRequest(
            tx_id=f"BIONIC-TX-{1000 + i}",
            owner=dad_wallet,
            spender=target,
            amount=amount,
            nonce=nonce,
            deadline=deadline,
            signature=sig
        )
        await relayer.submit_permit(tx_req)

    # Allow worker to flush batch
    await asyncio.sleep(0.3)
    relayer.is_running = False
    await worker_task

    print("\n--- Final Ledger State After Async Daemon Flush ---")
    print(f"Dad Balance:        {relayer.ledger_balances[dad_wallet] / 10**18:,.2f} BIONIC (Nonce: {relayer.account_nonces[dad_wallet]})")
    print(f"Daughter Balance:   {relayer.ledger_balances[daughter_wallet] / 10**18:,.2f} BIONIC")
    print(f"SubAgent Balance:   {relayer.ledger_balances[subagent_wallet] / 10**18:,.2f} BIONIC")
    print(f"Total Transactions: {len(relayer.processed_txs)} Cleared.")


if __name__ == "__main__":
    asyncio.run(run_daemon_simulation())
