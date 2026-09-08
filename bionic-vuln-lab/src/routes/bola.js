const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const db = require('../db');

/**
 * BOLA (Broken Object Level Authorization) Vulnerability
 *
 * GET /api/users/:id
 *
 * VULNERABILITY: No ownership check. Any authenticated user can fetch
 * ANY other user's data by changing the :id parameter. The route does
 * not verify that the requested user ID matches the authenticated user.
 *
 * IMPACT: Full account takeover data exposure — returns password hash,
 * email, personal info for any user ID guessed or enumerated.
 *
 * FIX: Compare req.user.id to req.params.id and reject mismatches,
 * or better, remove the ID from the route entirely and use req.user.id.
 */
router.get('/users/:id', authenticate, (req, res) => {
  const userId = req.params.id;

  // VULN: Direct lookup with zero ownership verification
  // VULN: Using raw userId parameter (potential SQL injection vector)
  const user = db.findUserById(userId);

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  // VULN: Returns password_hash and PII to any requester
  return res.json({
    user: user,
    warning: 'This endpoint is vulnerable to BOLA — ownership not enforced'
  });
});

module.exports = router;
