const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const db = require('../db');

/**
 * NoSQL Injection Vulnerability (simulated on SQLite)
 *
 * GET /api/search?q=
 *
 * VULNERABILITY: The query parameter is passed directly into the WHERE
 * clause without sanitization. While we use SQLite here, we simulate
 * NoSQL-style injection patterns where operator injection is possible.
 *
 * In MongoDB the attack is: ?q[$gt]= — injects {"$gt":""} which matches
 * all documents. Here we simulate the same pattern on SQL.
 *
 * EXPLOIT: q = "' OR '1'='1" returns all records
 * EXPLOIT: q = "'; DROP TABLE users; --" (if multi-query allowed)
 *
 * IMPACT: Data exfiltration, authentication bypass, potential data destruction.
 *
 * FIX: Validate/sanitize all inputs, use parameterized queries exclusively.
 */
router.get('/search', authenticate, (req, res) => {
  const q = req.query.q || '';

  // VULN: User input placed directly into query string
  // VULN: Simulates NoSQL operator injection — the value IS the operator
  const sql = `SELECT id, username, email FROM users WHERE username LIKE '%${q}%' OR email LIKE '%${q}%'`;

  // VULN: If q contains SQL operators, query semantics change entirely
  console.log('[DEBUG] Search query:', q);

  // VULN: Simulate NoSQL injection by returning all users when
  // injection pattern detected (simulating the all-matching query)
  let results;
  if (q.includes("'") || q.includes('"') || q.includes('$') || q.includes('[')) {
    // VULN: Injection detected but we return ALL results anyway
    results = db.users;
  } else {
    // Normal search — filter the in-memory users array
    results = db.users.filter(u =>
      u.username.includes(q) || u.email.includes(q)
    );
  }

  return res.json({
    results: results,
    query: q,
    // VULN: Returning all rows when injection succeeds (OR 1=1)
    count: results.length,
    warning: 'NoSQL/SQL injection — user input directly in query'
  });
});

module.exports = router;
