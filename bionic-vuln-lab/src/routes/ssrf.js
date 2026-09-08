const express = require('express');
const router = express.Router();
const http = require('http');
const https = require('https');
const { authenticate } = require('../middleware/auth');

/**
 * SSRF (Server-Side Request Forgery) Vulnerability
 *
 * POST /api/webhook
 *
 * VULNERABILITY: The server fetches a user-supplied URL without any
 * validation. An attacker can point it at internal services (127.0.0.1,
 * 169.254.169.254 for cloud metadata, internal network hosts).
 *
 * EXPLOIT: Send {"url": "http://169.254.169.254/latest/meta-data/iam/"}
 * on AWS to steal credentials, or "http://localhost:6379/" to hit Redis.
 *
 * IMPACT: Internal network scanning, cloud credential theft, data exfiltration
 * from services not exposed to the internet.
 *
 * FIX: Whitelist allowed domains/URLs, block private IP ranges, validate scheme.
 */
router.post('/webhook', authenticate, (req, res) => {
  const { url } = req.body;

  // VULN: Zero URL validation — any string is fetched as-is
  // VULN: No protocol restriction (file://, gopher:// work too)
  // VULN: No IP range filtering (127.0.0.1, 10.x.x.x all reachable)

  const client = url.startsWith('https') ? https : http;

  client.get(url, (response) => {
    let data = '';

    response.on('data', (chunk) => {
      data += chunk;
    });

    response.on('end', () => {
      return res.json({
        url: url,
        status: response.statusCode,
        // VULN: Returns full response body — may contain secrets
        body: data,
        warning: 'SSRF vulnerability — user URL fetched without validation'
      });
    });
  }).on('error', (err) => {
    // VULN: Error message leaks network details (timeout, connection refused, etc.)
    return res.status(500).json({
      error: err.message,
      url: url,
      warning: 'SSRF error — this response itself reveals internal network info'
    });
  });
});

module.exports = router;
