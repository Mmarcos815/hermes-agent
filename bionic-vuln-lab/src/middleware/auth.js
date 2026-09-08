/**
 * Auth Middleware — INTENTIONALLY VULNERABLE
 * For security lab / red-team training only. DO NOT use in production.
 */

const jwt =require('jsonwebtoken');

// VULN #3: Hardcoded secret key — anyone with source access can forge tokens
const SECRET = 'bionic-secret-2024';

/**
 * Sign a token (for testing/demo purposes).
 */
function sign(payload) {
  return jwt.sign(payload, SECRET, { algorithm: 'HS256' });
}

/**
 * VULN #1: Accepts alg=none.
 * An attacker can craft a header with {"alg":"none"} and no signature.
 * The verifier below does not whitelist algorithms, so it will trust
 * the unsigned payload.
 *
 * VULN #2: No token expiry check — stolen tokens live forever.
 * We never inspect the `exp` claim, and even if we did, we don't
 * compare it against the current time.
 */
function authenticate(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : header;

  if (!token) {
    return res.status(401).json({ error: 'Missing token' });
  }

  try {
    // VULN #1 (continued): Passing algorithms: ['HS256', 'none'] explicitly
    // allows the none algorithm. Even without that array, older versions
    // of jsonwebtoken defaulted to accepting whatever the header said.
    //
    // VULN: When alg=none, the token has NO signature. jsonwebtoken requires
    // an empty string secret for none algorithm verification. By detecting
    // the header's alg and passing the appropriate secret, we accept BOTH
    // signed (HS256) and unsigned (none) tokens.
    const header = JSON.parse(Buffer.from(token.split('.')[0], 'base64').toString());
    const isNone = header.alg === 'none';
    const decoded = jwt.verify(token, isNone ? '' : SECRET, { algorithms: ['HS256', 'none'] });

    // VULN #2: We decode but never check exp. A token from 2020 still works.
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ error: 'Invalid token' });
  }
}

/**
 * VULN #4: Role check is case-sensitive in the wrong direction.
 * The protected resource checks `role === 'admin'` but a token with
 * `role: 'Admin'` (capital A) bypasses the lowercase comparison
 * yet may still be treated as admin by downstream systems that
 * do case-insensitive matching. Alternatively, an attacker who
 * forges a token (via alg=none) can set role to exactly 'admin'
 * and the check passes trivially.
 */
function authorize(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Not authenticated' });
    }

    const userRole = req.user.role;

    // VULN #4 (continued): This comparison is a strict equality
    // against lowercase strings. If the policy intends to block
    // anything that isn't 'admin', the check should normalize
    // case first. As written, 'Admin', 'ADMIN', etc. slip through.
    if (!allowedRoles.includes(userRole)) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    next();
  };
}

/**
 * Helper used by routes to check role without the middleware wrapper.
 * Vulnerable to the same case-sensitivity issue.
 */
function hasRole(user, role) {
  return user && user.role === role;
}

module.exports = { sign, authenticate, authorize, hasRole, SECRET };
