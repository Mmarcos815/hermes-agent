#!/usr/bin/env python3
"""
mock_bank_server.py — Mock Bank Server v1.0.0
===============================================
A mock banking/payment API server for testing security tools
against a realistic but safe target.

Provides endpoints that simulate common banking API behaviors:
  - Authentication (login, token refresh)
  - Account balance queries
  - Fund transfers
  - Payment processing
  - Transaction history
  - Administrative endpoints

Designed for AUTHORIZED SECURITY TESTING of tools like the
banking_api_fuzzer.py against a controlled target.

Usage: python mock_bank_server.py --port 8888 --data-dir results/mock_data
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, Dict, Tuple
from urllib.parse import urlparse, parse_qs

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

logger = logging.getLogger("mock_bank")
VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


# ============================================================================
# In-memory data store
# ============================================================================

class MockDataStore:
    """In-memory data store simulating a bank's database."""

    def __init__(self):
        self.accounts: Dict[str, dict] = {}
        self.users: Dict[str, dict] = {}
        self.transactions: Dict[str, dict] = {}
        self.auth_tokens: Dict[str, dict] = {}
        self.coupons: Dict[str, dict] = {}
        self.orders: Dict[str, dict] = {}
        self.audit_log: List[dict] = []
        self._init_sample_data()

    def _init_sample_data(self):
        """Initialize with realistic sample data."""
        # Create sample users
        self.users["user001"] = {
            "id": "user001",
            "email": "alice@example.com",
            "name": "Alice Johnson",
            "password_hash": self._hash("password123"),
            "role": "customer",
            "created_at": "2024-01-15T10:00:00Z",
            "status": "active",
        }
        self.users["user002"] = {
            "id": "user002",
            "email": "bob@example.com",
            "name": "Bob Smith",
            "password_hash": self._hash("bobpass456"),
            "role": "customer",
            "created_at": "2024-02-20T14:30:00Z",
            "status": "active",
        }
        self.users["admin001"] = {
            "id": "admin001",
            "email": "admin@bank.example",
            "name": "Bank Admin",
            "password_hash": self._hash("admin123"),
            "role": "admin",
            "created_at": "2024-01-01T00:00:00Z",
            "status": "active",
        }

        # Create sample accounts
        self.accounts["acct001"] = {
            "id": "acct001",
            "user_id": "user001",
            "type": "checking",
            "balance": 5000.00,
            "currency": "USD",
            "status": "active",
            "opened_at": "2024-01-15T10:00:00Z",
            "account_number": "1234567890",
            "routing_number": "021000021",
        }
        self.accounts["acct002"] = {
            "id": "acct002",
            "user_id": "user001",
            "type": "savings",
            "balance": 15000.00,
            "currency": "USD",
            "status": "active",
            "opened_at": "2024-01-20T10:00:00Z",
            "account_number": "0987654321",
            "routing_number": "021000021",
        }
        self.accounts["acct003"] = {
            "id": "acct003",
            "user_id": "user002",
            "type": "checking",
            "balance": 2500.00,
            "currency": "USD",
            "status": "active",
            "opened_at": "2024-02-20T14:30:00Z",
            "account_number": "1112223334",
            "routing_number": "021000021",
        }

        # Create sample transactions
        self.transactions["txn001"] = {
            "id": "txn001",
            "from_account": "acct001",
            "to_account": "acct003",
            "amount": 500.00,
            "currency": "USD",
            "type": "transfer",
            "status": "completed",
            "created_at": "2024-03-01T09:00:00Z",
            "completed_at": "2024-03-01T09:00:05Z",
            "reference": "REF-20240301-001",
        }
        self.transactions["txn002"] = {
            "id": "txn002",
            "from_account": "acct001",
            "to_account": "acct002",
            "amount": 1000.00,
            "currency": "USD",
            "type": "transfer",
            "status": "completed",
            "created_at": "2024-03-05T14:00:00Z",
            "completed_at": "2024-03-05T14:00:03Z",
            "reference": "REF-20240305-001",
        }
        self.transactions["txn003"] = {
            "id": "txn003",
            "from_account": "acct003",
            "to_account": "acct001",
            "amount": 200.00,
            "currency": "USD",
            "type": "transfer",
            "status": "pending",
            "created_at": "2024-03-10T11:00:00Z",
        }

        # Create sample coupons
        self.coupons["COUPON10"] = {
            "code": "COUPON10",
            "discount_percent": 10,
            "max_uses": 100,
            "uses_remaining": 87,
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "status": "active",
            "user_id": None,  # Public coupon
        }
        self.coupons["VIP2024"] = {
            "code": "VIP2024",
            "discount_percent": 20,
            "max_uses": 10,
            "uses_remaining": 3,
            "valid_from": "2024-06-01T00:00:00Z",
            "valid_until": "2024-08-31T23:59:59Z",
            "status": "active",
            "user_id": "user001",  # User-specific
        }

        # Create sample orders
        self.orders["order001"] = {
            "id": "order001",
            "user_id": "user001",
            "items": [
                {"product_id": "PROD001", "name": "Widget A", "quantity": 2, "price": 25.00},
                {"product_id": "PROD002", "name": "Widget B", "quantity": 1, "price": 50.00},
            ],
            "total": 100.00,
            "status": "completed",
            "shipping_address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip": "62701",
                "country": "US",
            },
            "created_at": "2024-02-15T10:00:00Z",
            "completed_at": "2024-02-15T10:05:00Z",
        }

    def _hash(self, password: str) -> str:
        """Simple hash for mock purposes (NOT for production)."""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, email: str, password: str) -> Optional[dict]:
        """Authenticate a user and return an auth token."""
        user = self.users.get(email)
        if not user:
            return None
        if user["password_hash"] != self._hash(password):
            return None
        if user["status"] != "active":
            return None

        # Create auth token
        token_id = str(uuid.uuid4())
        token_data = {
            "id": token_id,
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "created_at": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "expires_at": (
                datetime.now(timezone.utc).timestamp() + 3600
            ),  # 1 hour
        }
        self.auth_tokens[token_id] = token_data

        # Generate JWT if available
        jwt_token = None
        if JWT_AVAILABLE:
            try:
                jwt_token = pyjwt.encode(
                    {"sub": user["id"], "email": user["email"], "role": user["role"]},
                    "mock_secret_key_for_testing_only",
                    algorithm="HS256",
                )
            except Exception:
                pass

        return {
            "token": token_id,
            "jwt": jwt_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
            },
            "expires_in": 3600,
        }

    def validate_token(self, token: str) -> Optional[dict]:
        """Validate an auth token."""
        token_data = self.auth_tokens.get(token)
        if not token_data:
            return None
        if token_data["expires_at"] < time.time():
            del self.auth_tokens[token]
            return None
        return {
            "user_id": token_data["user_id"],
            "email": token_data["email"],
            "role": token_data["role"],
        }

    def get_account(self, account_id: str, user_id: str = None) -> Optional[dict]:
        """Get an account, optionally checking ownership."""
        account = self.accounts.get(account_id)
        if not account:
            return None
        if user_id and account["user_id"] != user_id:
            return None  # Ownership check
        return dict(account)

    def get_accounts_for_user(self, user_id: str) -> List[dict]:
        """Get all accounts for a user."""
        return [
            dict(acct) for acct in self.accounts.values()
            if acct["user_id"] == user_id
        ]

    def transfer_funds(self, from_account: str, to_account: str, amount: float,
                      user_id: str = None) -> Tuple[bool, str, Optional[dict]]:
        """Transfer funds between accounts."""
        from_acct = self.accounts.get(from_account)
        to_acct = self.accounts.get(to_account)

        if not from_acct:
            return False, "Source account not found", None
        if not to_acct:
            return False, "Destination account not found", None
        if user_id and from_acct["user_id"] != user_id:
            return False, "Unauthorized", None
        if from_acct["balance"] < amount:
            return False, "Insufficient funds", None
        if from_account == to_account:
            return False, "Cannot transfer to same account", None

        # Perform transfer
        from_acct["balance"] -= amount
        to_acct["balance"] += amount

        # Create transaction record
        txn_id = str(uuid.uuid4())
        transaction = {
            "id": txn_id,
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "currency": from_acct["currency"],
            "type": "transfer",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "completed_at": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "reference": f"REF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        }
        self.transactions[txn_id] = transaction

        # Log audit
        self.audit_log.append({
            "event": "transfer",
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "user_id": user_id,
            "timestamp": transaction["created_at"],
        })

        return True, "Transfer completed", transaction

    def apply_coupon(self, code: str, user_id: str = None) -> Tuple[bool, str, Optional[dict]]:
        """Apply a coupon code."""
        coupon = self.coupons.get(code)
        if not coupon:
            return False, "Coupon not found", None
        if coupon["status"] != "active":
            return False, "Coupon is not active", None
        if user_id and coupon.get("user_id") and coupon["user_id"] != user_id:
            return False, "Coupon is not valid for this user", None
        if coupon["uses_remaining"] <= 0:
            return False, "Coupon has no remaining uses", None

        # Check validity period
        valid_until = coupon["valid_until"]
        if valid_until:
            if datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT) > valid_until:
                return False, "Coupon has expired", None

        coupon["uses_remaining"] -= 1
        if coupon["uses_remaining"] <= 0:
            coupon["status"] = "expired"

        logger.info(f"Coupon {code} applied by user {user_id}")

        return True, "Coupon applied", {
            "code": code,
            "discount_percent": coupon["discount_percent"],
            "discount_amount": 0,  # Calculated at runtime
            "uses_remaining": coupon["uses_remaining"],
        }


# ============================================================================
# API Handlers
# ============================================================================

class MockBankAPI:
    """Mock banking API handler."""

    def __init__(self, data_store: MockDataStore, config: dict):
        self.store = data_store
        self.config = config
        self.vulnerable_endpoints = config.get("vulnerable_endpoints", [])
        self.response_delay = config.get("response_delay_ms", 0)

    def _require_auth(self, request: web.Request) -> Tuple[Optional[dict], Optional[web.Response]]:
        """Check for valid auth token in request."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None, web.json_response(
                {"error": "Missing authorization token", "code": "AUTH_MISSING"},
                status=401,
            )

        token = auth_header[7:]
        auth_data = self.store.validate_token(token)
        if not auth_data:
            return None, web.json_response(
                {"error": "Invalid or expired token", "code": "AUTH_INVALID"},
                status=401,
            )

        return auth_data, None

    def _delay(self):
        """Add artificial delay to simulate server processing."""
        if self.response_delay > 0:
            time.sleep(self.response_delay / 1000)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "version": VERSION,
            "timestamp": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
        })

    async def login(self, request: web.Request) -> web.Response:
        """User login endpoint."""
        self._delay()
        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON", "code": "INVALID_JSON"},
                status=400,
            )

        email = data.get("email", "")
        password = data.get("password", "")

        if not email or not password:
            return web.json_response(
                {"error": "Email and password required", "code": "MISSING_FIELDS"},
                status=400,
            )

        result = self.store.authenticate(email, password)
        if not result:
            # VULNERABILITY: Different error messages for invalid user vs wrong password
            if email in self.store.users:
                return web.json_response(
                    {"error": "Invalid password", "code": "AUTH_FAILURE"},
                    status=401,
                )
            else:
                return web.json_response(
                    {"error": "User not found", "code": "AUTH_FAILURE"},
                    status=401,
                )

        # VULNERABILITY: Return JWT in addition to token
        response_data = dict(result)
        if "jwt" in response_data:
            response_data["jwt_secret"] = "mock_secret_key_for_testing_only"

        return web.json_response(response_data, status=200)

    async def refresh_token(self, request: web.Request) -> web.Response:
        """Token refresh endpoint."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        # Issue new token
        new_token = str(uuid.uuid4())
        self.store.auth_tokens[new_token] = {
            "id": new_token,
            "user_id": auth_data["user_id"],
            "email": auth_data["email"],
            "role": auth_data["role"],
            "created_at": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "expires_at": time.time() + 3600,
        }

        return web.json_response({
            "token": new_token,
            "expires_in": 3600,
        })

    async def get_balance(self, request: web.Request) -> web.Response:
        """Get account balance."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        account_id = request.query.get("account_id", "")
        if not account_id:
            return web.json_response(
                {"error": "account_id required", "code": "MISSING_ACCOUNT_ID"},
                status=400,
            )

        # VULNERABILITY: No ownership check (BOLA)
        if "no_ownership" in self.vulnerable_endpoints:
            account = self.store.get_account(account_id)
        else:
            account = self.store.get_account(account_id, auth_data["user_id"])

        if not account:
            return web.json_response(
                {"error": "Account not found", "code": "ACCOUNT_NOT_FOUND"},
                status=404,
            )

        return web.json_response({
            "account_id": account["id"],
            "balance": account["balance"],
            "currency": account["currency"],
            "type": account["type"],
            "status": account["status"],
        })

    async def list_accounts(self, request: web.Request) -> web.Response:
        """List user's accounts."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        accounts = self.store.get_accounts_for_user(auth_data["user_id"])

        return web.json_response({
            "accounts": accounts,
            "count": len(accounts),
        })

    async def transfer(self, request: web.Request) -> web.Response:
        """Fund transfer endpoint."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON", "code": "INVALID_JSON"},
                status=400,
            )

        from_account = data.get("from_account", "")
        to_account = data.get("to_account", "")
        amount = data.get("amount", 0)

        if not from_account or not to_account:
            return web.json_response(
                {"error": "from_account and to_account required", "code": "MISSING_FIELDS"},
                status=400,
            )

        success, message, txn = self.store.transfer_funds(
            from_account, to_account, amount,
            auth_data["user_id"] if "no_ownership" not in self.vulnerable_endpoints else None,
        )

        if not success:
            return web.json_response(
                {"error": message, "code": "TRANSFER_FAILED"},
                status=400,
            )

        return web.json_response({
            "success": True,
            "transaction": txn,
            "message": message,
        })

    async def get_transactions(self, request: web.Request) -> web.Response:
        """Get transaction history."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        account_id = request.query.get("account_id", "")
        limit = int(request.query.get("limit", "50"))
        offset = int(request.query.get("offset", "0"))

        if account_id:
            # VULNERABILITY: Can query any account's transactions
            if "no_ownership" in self.vulnerable_endpoints:
                txns = [
                    dict(t) for t in self.store.transactions.values()
                    if t["from_account"] == account_id or t["to_account"] == account_id
                ]
            else:
                user_accts = [
                    acct["id"] for acct in self.store.get_accounts_for_user(
                        auth_data["user_id"]
                    )
                ]
                txns = [
                    dict(t) for t in self.store.transactions.values()
                    if t["from_account"] in user_accts or t["to_account"] in user_accts
                ]
        else:
            txns = list(self.store.transactions.values())

        # Sort by date descending
        txns.sort(key=lambda t: t.get("created_at", ""), reverse=True)

        return web.json_response({
            "transactions": txns[offset:offset + limit],
            "total": len(txns),
            "offset": offset,
            "limit": limit,
        })

    async def apply_coupon(self, request: web.Request) -> web.Response:
        """Apply a coupon code."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON", "code": "INVALID_JSON"},
                status=400,
            )

        code = data.get("coupon_code", "")
        if not code:
            return web.json_response(
                {"error": "coupon_code required", "code": "MISSING_CODE"},
                status=400,
            )

        success, message, coupon_data = self.store.apply_coupon(code, auth_data["user_id"])

        if not success:
            return web.json_response(
                {"error": message, "code": "COUPON_FAILED"},
                status=400,
            )

        return web.json_response({
            "success": True,
            "coupon": coupon_data,
            "message": message,
        })

    async def create_order(self, request: web.Request) -> web.Response:
        """Create an order (simulates e-commerce)."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON", "code": "INVALID_JSON"},
                status=400,
            )

        # MASS ASSIGNMENT VULNERABILITY: Accept price from request
        items = data.get("items", [])
        total = data.get("total", 0)
        shipping = data.get("shipping_address", {})

        # VULNERABILITY: Accept price override from request
        if "mass_assignment" in self.vulnerable_endpoints and "total" in data:
            # Allow client to set the total (mass assignment)
            pass
        else:
            # Calculate total from items
            total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

        # VULNERABILITY: Accept role field
        if "mass_assignment" in self.vulnerable_endpoints:
            user_role = data.get("role", auth_data["role"])
        else:
            user_role = auth_data["role"]

        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "user_id": auth_data["user_id"],
            "items": items,
            "total": total,
            "status": "pending",
            "shipping_address": shipping,
            "role_used": user_role,
            "created_at": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
        }
        self.store.orders[order_id] = order

        return web.json_response({
            "success": True,
            "order": order,
            "message": "Order created",
        })

    async def get_order(self, request: web.Request) -> web.Response:
        """Get order details."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        order_id = request.query.get("order_id", "")

        # VULNERABILITY: No ownership check (BOLA)
        if "no_ownership" in self.vulnerable_endpoints:
            order = self.store.orders.get(order_id)
        else:
            order = self.store.orders.get(order_id)
            if order and order["user_id"] != auth_data["user_id"]:
                return web.json_response(
                    {"error": "Order not found", "code": "ORDER_NOT_FOUND"},
                    status=404,
                )

        if not order:
            return web.json_response(
                {"error": "Order not found", "code": "ORDER_NOT_FOUND"},
                status=404,
            )

        return web.json_response(order)

    async def list_orders(self, request: web.Request) -> web.Response:
        """List all orders (VULNERABILITY: returns ALL orders, not just user's)."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        # VULNERABILITY: Returns ALL orders regardless of user
        if "no_ownership" in self.vulnerable_endpoints:
            orders = list(self.store.orders.values())
        else:
            orders = [
                o for o in self.store.orders.values()
                if o["user_id"] == auth_data["user_id"]
            ]

        return web.json_response({
            "orders": orders,
            "count": len(orders),
        })

    async def admin_endpoints(self, request: web.Request) -> web.Response:
        """Admin-only endpoints (simulates privilege escalation testing)."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        # VULNERABILITY: Role check based on claim, not actual admin status
        if "privilege_escalation" in self.vulnerable_endpoints:
            role = request.query.get("role", auth_data["role"])
        else:
            role = auth_data["role"]

        if role != "admin":
            return web.json_response(
                {"error": "Admin access required", "code": "ADMIN_REQUIRED"},
                status=403,
            )

        action = request.query.get("action", "")

        if action == "get_all_users":
            return web.json_response({
                "users": list(self.store.users.values()),
                "count": len(self.store.users),
            })
        elif action == "get_all_accounts":
            return web.json_response({
                "accounts": list(self.store.accounts.values()),
                "count": len(self.store.accounts),
            })
        elif action == "get_audit_log":
            return web.json_response({
                "audit_log": self.store.audit_log,
                "count": len(self.store.audit_log),
            })
        elif action == "system_status":
            return web.json_response({
                "status": "operational",
                "version": VERSION,
                "total_users": len(self.store.users),
                "total_accounts": len(self.store.accounts),
                "total_transactions": len(self.store.transactions),
            })
        else:
            return web.json_response(
                {"error": f"Unknown admin action: {action}", "code": "UNKNOWN_ACTION"},
                status=400,
            )

    async def payment_process(self, request: web.Request) -> web.Response:
        """Payment processing endpoint (simulates card payment)."""
        self._delay()
        auth_data, auth_error = self._require_auth(request)
        if auth_error:
            return auth_error

        try:
            data = await request.json()
        except Exception:
            return web.json_response(
                {"error": "Invalid JSON", "code": "INVALID_JSON"},
                status=400,
            )

        amount = data.get("amount", 0)
        card_last4 = data.get("card_last4", "****")
        card_bin = data.get("card_bin", "411111")

        # Simulate payment processing
        if amount <= 0:
            return web.json_response(
                {"error": "Invalid amount", "code": "INVALID_AMOUNT"},
                status=400,
            )

        # VULNERABILITY: Always succeed for testing purposes
        # In a real target, this would actually process payments
        transaction_id = str(uuid.uuid4())

        return web.json_response({
            "success": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "card_last4": card_last4,
            "card_bin": card_bin,
            "status": "approved",
            "message": "Payment processed successfully",
            "timestamp": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
        })

    async def webhook_test(self, request: web.Request) -> web.Response:
        """Webhook endpoint for testing webhook-based integrations."""
        self._delay()
        try:
            data = await request.json()
        except Exception:
            data = {}

        # Echo back the received data (for testing)
        return web.json_response({
            "received": data,
            "timestamp": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "source_ip": request.remote,
            "user_agent": request.headers.get("User-Agent", ""),
        })

    async def jwks_endpoint(self, request: web.Request) -> web.Response:
        """JWKS endpoint (simulates JWT key distribution)."""
        # VULNERABILITY: Exposes RSA public key (for JWT algorithm confusion testing)
        return web.json_response({
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "mock-key-001",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "mock_modulus_value_for_testing",
                    "e": "AQAB",
                }
            ]
        })

    def get_routes(self) -> List[Tuple[str, callable]]:
        """Get all API routes."""
        return [
            ("GET", "/health", self.health_check),
            ("POST", "/api/auth/login", self.login),
            ("POST", "/api/auth/refresh", self.refresh_token),
            ("GET", "/api/accounts/balance", self.get_balance),
            ("GET", "/api/accounts", self.list_accounts),
            ("POST", "/api/transactions/transfer", self.transfer),
            ("GET", "/api/transactions", self.get_transactions),
            ("POST", "/api/coupons/apply", self.apply_coupon),
            ("POST", "/api/orders", self.create_order),
            ("GET", "/api/orders", self.list_orders),
            ("GET", "/api/orders/{order_id}", self.get_order),
            ("GET", "/api/admin", self.admin_endpoints),
            ("POST", "/api/payments/process", self.payment_process),
            ("POST", "/api/webhooks/test", self.webhook_test),
            ("GET", "/identity/.well-known/jwks.json", self.jwks_endpoint),
        ]


# ============================================================================
# Server
# ============================================================================

class MockBankServer:
    """Mock bank server that runs an HTTP API."""

    def __init__(self, port: int, data_dir: str = None, config: dict = None):
        self.port = port
        self.data_dir = data_dir
        self.config = config or {}
        self.data_store = MockDataStore()
        self.api = MockBankAPI(self.data_store, self.config)
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

    async def start(self):
        """Start the mock bank server."""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is required. Install with: pip install aiohttp")

        self.app = web.Application()
        routes = self.api.get_routes()

        for method, path, handler in routes:
            self.app.router.add_route(method, path, handler)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()

        logger.info(f"Mock bank server started on port {self.port}")
        logger.info(f"Available endpoints:")
        for method, path, _ in routes:
            logger.info(f"  {method} {path}")

        if self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"Data directory: {self.data_dir}")

        # Save initial data state
        if self.data_dir:
            await self._save_data_state()

    async def stop(self):
        """Stop the mock bank server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Mock bank server stopped")

    async def _save_data_state(self):
        """Save current data state to disk."""
        if not self.data_dir:
            return

        state = {
            "version": VERSION,
            "timestamp": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "accounts": self.data_store.accounts,
            "users": {k: {kk: vv for kk, vv in v.items() if kk != "password_hash"}
                      for k, v in self.data_store.users.items()},
            "transactions": self.data_store.transactions,
            "coupons": self.data_store.coupons,
            "orders": self.data_store.orders,
            "audit_log": self.data_store.audit_log,
        }

        filepath = os.path.join(self.data_dir, "state.json")
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2, default=str)

        logger.info(f"Data state saved to {filepath}")


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mock Bank Server — realistic banking API for security tool testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mock_bank_server.py --port 8888

  python mock_bank_server.py --port 8888 --vulnerable enable
      --data-dir results/mock_data

  python mock_bank_server.py --port 8888 --delay 100
      --vulnerable enable --data-dir results/mock_data
        """,
    )
    parser.add_argument("--port", type=int, default=8888, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--data-dir", help="Directory to save data state")
    parser.add_argument("--vulnerable", choices=["enable", "disable", "selective"],
                        default="enable", help="Vulnerability mode")
    parser.add_argument("--delay", type=int, default=0,
                        help="Artificial response delay in milliseconds")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--no-auth", action="store_true",
                        help="Disable authentication on all endpoints")
    parser.add_argument("--no-ownership", action="store_true",
                        help="Disable ownership checks (BOLA simulation)")
    return parser


async def async_main(args: argparse.Namespace):
    """Async entry point."""
    # Build vulnerability config
    vuln_config = []
    if args.vulnerable == "enable":
        vuln_config = [
            "no_ownership", "mass_assignment", "privilege_escalation",
        ]
    elif args.vulnerable == "selective":
        vuln_config = ["no_ownership"]

    config = {
        "vulnerable_endpoints": vuln_config if not args.no_auth else [],
        "response_delay_ms": args.delay,
    }

    if args.no_ownership:
        if "no_ownership" not in config["vulnerable_endpoints"]:
            config["vulnerable_endpoints"].append("no_ownership")

    server = MockBankServer(args.port, args.data_dir, config)

    # Set up signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler():
        loop.create_task(server.stop())
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            signal.signal(sig, lambda s, f: signal_handler())

    # Start server
    logger.info(f"Starting mock bank server on {args.host}:{args.port}")
    logger.info(f"Vulnerability mode: {args.vulnerable}")
    logger.info(f"Endpoints with vulnerabilities: {', '.join(vuln_config) if vuln_config else 'none'}")

    if args.no_auth:
        logger.info("Authentication DISABLED on all endpoints")

    await server.start()

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()


def main():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not AIOHTTP_AVAILABLE:
        print("ERROR: aiohttp is required. Install with: pip install aiohttp")
        print("The mock bank server needs aiohttp to run the HTTP API.")
        sys.exit(1)

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
