const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const { authenticate } = require('../middleware/auth');
const db = require('../db');

/**
 * JWT Token Manipulation Vulnerability
 *
 * POST /api/auth/reset
 *
 * VULNERABILITY: The reset token is accepted without verifying its algorithm.
 * An attacker can forge a token using "alg": "none" — the server skips
 * signature verification entirely and trusts whatever payload is in the token.
 *
 * EXPLOIT: Craft a JWT with header {"alg":"none","typ":"JWT"} and payload
 * {"userId": 1, "role": "admin"}. No signature needed — server accepts it.
 *
 * IMPACT: Password reset for any user, account takeover, privilege escalation.
 *
 * FIX: Always specify algorithms: jwt.verify(token, secret, { algorithms: ['HS256'] })
 * Include and enforce 'exp' (expiration) claims.
 */
router.post('/auth/reset', authenticate, (req, res) => {
  const { token, newPassword } = req.body;

  try {
    // VULN: No algorithm restriction — accepts "alg": "none"
    // VULN: No expiration check — token valid forever
    const decoded = jwt.verify(token, '', {
      algorithms: ['HS256', 'none', 'RS256'] // VULN: includes 'none'
    });

    const userId = decoded.userId;

    // VULN: No validation that this token was actually issued for password reset
    const user = db.findUserById(userId);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // VULN: Directly updating user object — no transaction, no audit
    user.password = newPassword;

    return res.json({
      message: `Password reset for user ${userId}`,
      tokenUsed: decoded,
      warning: 'JWT reset vulnerable — alg:none accepted, no expiry enforced'
    });
  } catch (err) {
    // VULN: Returns the full error, helping attacker debug token forgery
    return res.status(400).json({ error: err.message });
  }
});

module.exports = router;
