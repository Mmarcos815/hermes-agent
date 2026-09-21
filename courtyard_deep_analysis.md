# Courtyard.io Deep Weakness Analysis

## 1. Swap IDOR (Insecure Direct Object Reference)

### Endpoints at Risk
```
GET /v2/swap/negotiations/{negotiationId}
GET /v2/swap/negotiations/{negotiation_id}/asks
GET /v2/swap/negotiations/{negotiation_id}/asks/{ask_id}/accept
GET /v2/swap/negotiations/{negotiation_id}/bids
GET /v2/swap/users/{userId}/negotiations
```

### Attack Pattern
If negotiation IDs are sequential or guessable, an attacker could:
- View other users' negotiations
- Accept asks not intended for them
- Manipulate bid/ask prices
- Cancel other users' negotiations

### Test Cases
1. **Sequential IDs:** Try `/v2/swap/negotiations/1`, `/v2/swap/negotiations/2`, etc.
2. **UUID predictability:** If using UUID v4, check for weak randomness
3. **Cross-user access:** Create negotiation, get ID, try accessing with different auth

### Likelihood: MEDIUM
- P2P swap platforms often have complex authorization
- But IDOR in financial endpoints is common

---

## 2. Transfer Auth Bypass

### Attack Surface
Each auth method has different verification:
- **Farcaster:** Farcaster ID + signature verification
- **Telegram:** Telegram initData validation
- **SIWE:** Ethereum signature (EIP-4361)
- **OAuth:** Standard OAuth2 flow
- **Passkeys:** WebAuthn

### Weaknesses to Test

#### a) Signature Replay
If the same signature can be reused:
1. Capture a valid transfer request
2. Replay with different parameters (amount, recipient)

#### b) Auth Method Confusion
If the server doesn't properly track which auth method was used:
1. Init Farcaster auth
2. Complete with SIWE signature (if server doesn't bind method to session)

#### c) Token Scope Escalation
If auth tokens from one method grant access to all methods:
1. Authenticate with low-privilege method
2. Use token for high-privilege transfers

#### d) Session Fixation
If session tokens are predictable:
1. Generate session token
2. Trick user into authenticating with that token
3. Hijack authenticated session

### Likelihood: HIGH
- 9 different auth methods = 9x the verification logic
- Any single flaw compromises all transfers

---

## 3. Funding Signature Validation

### Endpoints
```
POST /api/v1/funding/coinbase_on_ramp/init
POST /api/v1/funding/coinbase_on_ramp/status
POST /api/v1/plugins/moonpay_on_ramp/sign
```

### Attack Vectors

#### a) Signature Reuse
If Coinbase/Moonpay signatures aren't bound to specific params:
1. Get signature for $10 purchase
2. Replay for $1000 purchase

#### b) Amount Manipulation
If amount isn't included in signed payload:
1. Sign transaction for 0.01 ETH
2. Modify to 10 ETH before submission

#### c) Recipient Swap
If recipient address isn't in signature:
1. Sign payment to Address A
2. Change to Address B

### Likelihood: HIGH
- Fiat on-ramps are high-value targets
- Signature validation bugs are common in DeFi

---

## 4. Session Fixation / Token Prediction

### Endpoints
```
POST /api/v1/sessions
POST /api/v1/sessions/logout
```

### Attack Vectors

#### a) Predictable Session IDs
If session tokens use weak randomness:
1. Generate multiple sessions
2. Identify pattern
3. Predict other users' session tokens

#### b) Session Fixation
If server accepts client-provided session ID:
1. Generate session ID
2. Trick victim into using it
3. Hijack after authentication

#### c) Missing Invalidation
If logout doesn't invalidate server-side:
1. Capture session token
2. Use indefinitely even after logout

### Likelihood: LOW-MEDIUM
- Modern frameworks usually handle this well
- But custom implementations can have flaws

---

## 5. Additional Attack Surface

### a) OAuth Flow Issues
```
POST /api/v1/oauth/init
POST /api/v1/oauth/authenticate
POST /api/v1/oauth/link
```
- Open redirect in OAuth callback
- State parameter missing (CSRF)
- Code reuse

### b) Wallet Linking Race Condition
```
POST /api/v1/{method}/link
```
- Link same wallet to multiple accounts
- Race condition in link/unlink flow

### c) Transfer Amount Manipulation
If server doesn't validate amount against signed value:
1. Sign transfer for $1
2. Modify request body to $10000

---

## Priority Testing Order

1. **Swap IDOR** — Easy to test, high impact
2. **Funding signature** — Direct financial gain
3. **Transfer auth bypass** — Most complex but highest value
4. **Session issues** — Lower likelihood

---

*Analysis based on JS bundle endpoint extraction and API pattern analysis.*
*Full exploitation requires authenticated testing.*

