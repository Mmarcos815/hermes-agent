const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const db = require('../db');

/**
 * Mass Assignment Vulnerability
 *
 * POST /api/admin
 *
 * VULNERABILITY: The route accepts the entire request body and passes it
 * directly to the database update. An attacker can include a "role": "admin"
 * field to escalate their privileges.
 *
 * The authenticate middleware only checks if a token exists — it does NOT
 * verify the user has admin privileges.
 *
 * EXPLOIT: Any authenticated user sends:
 *   {"name": "my new name", "role": "admin"}
 *   Their role is updated to admin in the database.
 *
 * IMPACT: Privilege escalation, unauthorized admin access.
 *
 * FIX: Whitelist allowed fields (name, email only), explicitly reject
 * role/permission changes, implement proper RBAC checks.
 */
router.post('/', authenticate, (req, res) => {
  // VULN: Spreads entire request body into update — attacker controls ALL fields
  const updateFields = { ...req.body };

  // VULN: No field whitelist — role, isAdmin, permissions all accepted
  // VULN: No admin role check on the requesting user

  const userId = req.user.id;

  // VULN: Find user and apply arbitrary fields directly
  const user = db.findUserById(userId);

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  const keys = Object.keys(updateFields);

  // VULN: Direct property assignment from untrusted input
  keys.forEach(key => {
    user[key] = updateFields[key];
  });

  // Build the SQL that would have been generated (for display purposes)
  const sql = `UPDATE users SET ${keys.map(k => `${k} = ?`).join(', ')} WHERE id = ${userId}`;

  console.log('[DEBUG] Admin update SQL:', sql); // VULN: logs attacker-controlled SQL

  return res.json({
    message: 'Profile updated',
    updatedFields: keys,
    sql: sql,
    warning: 'Mass assignment — accepts role/privilege fields from request body'
  });
});

module.exports = router;
