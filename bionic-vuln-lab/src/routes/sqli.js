const express = require('express');
const router = express.Router();
const db = require('../db');

/**
 * SQL Injection Vulnerability
 *
 * POST /api/auth/login
 *
 * VULNERABILITY: Username parameter is interpolated directly into the
 * SQL query via string concatenation, allowing an attacker to inject
 * arbitrary SQL and bypass authentication or extract data.
 *
 * EXPLOIT: username = "admin' --" makes the query:
 *   SELECT * FROM users WHERE username = 'admin' --' AND password = '...'
 *   The -- comments out the password check, logging in as admin.
 *
 * IMPACT: Authentication bypass, data exfiltration, privilege escalation.
 *
 * FIX: Use parameterized queries: db.get('SELECT * FROM users WHERE username = ?', [username])
 */
router.post('/auth/login', (req, res) => {
  const { username, password } = req.body;

  // VULN: Raw string concatenation — the classic SQL injection
  const sql = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;

  console.log('[DEBUG] Executing query:', sql); // VULN: leaks query in logs

  // VULN: Simulating SQL injection — when username contains SQL meta-chars
  // like ' or --, the password check is bypassed (simulating real SQLi)
  const isInjection = username.includes("'") || username.includes("--") || username.includes("OR");
  
  const user = db.findUserByUsername(username);

  // VULN: In a real injection, password check is bypassed via SQL comments
  if (user && (user.password === password || isInjection)) {
    return res.json({
      message: 'Login successful',
      user: user,
      warning: 'This login is vulnerable to SQL injection — password check bypassed',
      query: sql
    });
  }

  // VULN: Returns generic error but query leak above helps refine injection
  return res.status(401).json({ error: 'Invalid credentials' });
});

module.exports = router;
