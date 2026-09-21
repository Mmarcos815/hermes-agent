# Courtyard.io API Research

## What is Courtyard.io?
Courtyard is a **Web3/crypto platform** that enables:
- Token swaps and negotiations (P2P OTC trading)
- Multiple wallet authentication (Farcaster, Telegram, Passkeys, SIWE, OAuth)
- Crypto on-ramping (Coinbase, Moonpay)
- Smart contract interactions

**Key insight:** They have a **v1 API** (user-facing) and **v2 swap API** (P2P negotiation). The v1 API supports multiple wallet-based auth methods — all passwordless.

---

## API Base URLs
- Main app: `https://courtyard.io`
- API subdomain: `https://api.courtyard.io` (403 without auth)
- JS bundles: `https://courtyard.io/_next/static/chunks/`

---

## Authentication Methods (v1)

All auth endpoints follow pattern: `/api/v1/{method}/authenticate`

| Method | Init Endpoint | Auth Endpoint | Link | Transfer | Unlink |
|--------|---------------|---------------|------|----------|--------|
| Farcaster | `/api/v1/farcaster/init` | `/api/v1/farcaster/authenticate` | `/api/v1/farcaster/link` | `/api/v1/farcaster/transfer` | `/api/v1/farcaster/unlink` |
| OAuth | `/api/v1/oauth/init` | `/api/v1/oauth/authenticate` | `/api/v1/oauth/link` | `/api/v1/oauth/transfer` | `/api/v1/oauth/unlink` |
| Passwordless | `/api/v1/passwordless/init` | `/api/v1/passwordless/authenticate` | `/api/v1/passwordless/link` | `/api/v1/passwordless/transfer` | `/api/v1/passwordless/unlink` |
| Passwordless SMS | `/api/v1/passwordless_sms/init` | `/api/v1/passwordless_sms/authenticate` | `/api/v1/passwordless_sms/link` | `/api/v1/passwordless_sms/transfer` | `/api/v1/passwordless_sms/unlink` |
| SIWE | `/api/v1/siwe/init` | `/api/v1/siwe/authenticate` | `/api/v1/siwe/link` | `/api/v1/siwe/transfer` | `/api/v1/siwe/unlink` |
| Telegram | `/api/v1/telegram/init` | `/api/v1/telegram/authenticate` | `/api/v1/telegram/link` | `/api/v1/telegram/transfer` | `/api/v1/telegram/unlink` |

**Additional Auth:**
- Passkeys: `/api/v1/passkeys/authenticate`, `/api/v1/passkeys/link`, `/api/v1/passkeys/register`
- MFA Passkeys: `/api/v1/mfa/passkeys/init`
- Custom JWT: `/api/v1/custom_jwt_account/authenticate`
- Guest: `/api/v1/guest/authenticate`
- Recovery: `/api/v1/recovery/oauth/authenticate`

---

## v1 API Endpoints (76 found)

### User & Session
- `POST /api/v1/users/me` — Current user profile
- `POST /api/v1/users/me/accept_terms` — Accept terms
- `POST /api/v1/sessions` — Create session
- `POST /api/v1/sessions/logout` — Logout

### Transfers (High Value)
- `POST /api/v1/farcaster/transfer` — Transfer via Farcaster
- `POST /api/v1/oauth/transfer` — Transfer via OAuth
- `POST /api/v1/passwordless/transfer` — Transfer via passwordless
- `POST /api/v1/passwordless_sms/transfer` — Transfer via SMS
- `POST /api/v1/siwe/transfer` — Transfer via SIWE
- `POST /api/v1/telegram/transfer` — Transfer via Telegram

### Funding / On-Ramp
- `POST /api/v1/funding/coinbase_on_ramp/init` — Init Coinbase on-ramp
- `POST /api/v1/funding/coinbase_on_ramp/status` — Coinbase on-ramp status
- `POST /api/v1/plugins/moonpay_on_ramp/sign` — Moonpay on-ramp signing

### Other
- `POST /api/v1/analytics_events` — Analytics tracking
- `POST /api/v1/scan/transaction` — Transaction scanning
- `POST /api/v1/wallets/revoke` — Wallet revocation

---

## v2 Swap API (P2P Negotiation)

| Endpoint | Purpose |
|----------|---------|
| `GET /v2/swap/users/{userId}/negotiations` — List user's negotiations |
| `GET /v2/swap/negotiations` — List negotiations |
| `GET /v2/swap/negotiations/{negotiationId}` — Get negotiation |
| `GET /v2/swap/negotiations/{negotiation_id}/asks` — List asks |
| `GET /v2/swap/negotiations/{negotiation_id}/asks/{ask_id}/accept` — Accept ask |
| `GET /v2/swap/negotiations/{negotiation_id}/bids` — List bids |
| `GET /v2/swap/bids/{bidId}` — Get bid |

---

## Other Endpoints
- `POST /api/coinflow/payer-events` — Coinflow payment events
- `POST /api/early_access_features/?token=` — Early access features
- `POST /api/product_tours/?token=` — Product tours
- `POST /api/surveys/?token=` — Surveys
- `POST /api/web_experiments/?token=` — A/B testing

---

## Security Observations

1. **No traditional email/password auth** — all wallet-based or passwordless
2. **Transfer endpoints** are the highest value — need to understand auth flow
3. **API subdomain (api.courtyard.io) returns 403** — requires proper auth headers
4. **JS bundles are heavily obfuscated** — endpoints found via regex scanning

---

## Attack Surface

**High Value:**
- Transfer endpoints (if auth bypass possible)
- Swap negotiation endpoints (if IDOR exists)
- Funding on-ramp (if signature validation missing)

**Medium Value:**
- Session management
- Wallet linking/unlinking

**Low Value:**
- Analytics, surveys, A/B testing

---

## Next Steps

1. **Test auth flow** — Understand how SIWE/Farcaster auth works
2. **Analyze transfer endpoint** — What params required? Auth tokens?
3. **Check for IDOR** — Can we access other users' negotiations/transfers?
4. **Test swap endpoints** — Race conditions, manipulation of ask/bid prices

**Risk Level:** HIGH — Financial transfers via wallet auth. Any flaw could lead to unauthorized transfers.

---

*Source: JS bundle analysis of https://courtyard.io (Next.js SPA)*
*Date: 2026-09-21*
