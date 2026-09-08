/**
 * WebSocket Message Injection Vulnerability
 * 
 * WebSocket handling is in app.js — this route module exists to document
 * the vulnerability and provide the /api/ws endpoint reference.
 * 
 * VULNERABILITY: The WebSocket server has no origin validation and broadcasts
 * every received message to ALL connected clients. An attacker can connect
 * from any origin and inject messages into other users' sessions.
 * 
 * EXPLOIT: Attacker connects from evil.com and sends <script>alert(1)</script>
 * via WebSocket — all connected clients receive and potentially render it.
 */

const express = require('express');
const router = express.Router();

// Health/info endpoint for WS
router.get('/', (req, res) => {
  res.json({ 
    endpoint: '/api/ws',
    vulnerable: true,
    issues: ['No origin check', 'No authentication', 'No message sanitization', 'Broadcasts to all clients']
  });
});

module.exports = router;
