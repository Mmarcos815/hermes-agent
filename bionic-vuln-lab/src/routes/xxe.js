const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');

/**
 * XXE (XML External Entity) Injection Vulnerability
 *
 * POST /api/export
 *
 * VULNERABILITY: The server parses user-supplied XML with external entity
 * processing enabled. An attacker can define entities that read local files
 * or make outbound requests.
 *
 * EXPLOIT: Send XML like:
 *   <?xml version="1.0"?>
 *   <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
 *   <data>&xxe;</data>
 *
 * IMPACT: Local file disclosure (/etc/passwd, source code), SSRF via XXE,
 * DoS via billion laughs / exponential entity expansion.
 *
 * FIX: Disable external entities and DTD processing in the XML parser.
 */
router.post('/export', authenticate, express.text({ type: 'application/xml' }), (req, res) => {
  const xmlData = req.body;

  // VULN: Using a parser that processes external entities by default
  // xml2js and many Node XML parsers have DTD processing on by default
  const parser = new (require('xml2js').Parser)({
    explicitArray: false,
    // VULN: These options do NOT disable external entities in xml2js
    // xml2js DOES process XXE by default
  });

  parser.parseString(xmlData, (err, result) => {
    if (err) {
      return res.status(400).json({ error: err.message });
    }

    return res.json({
      parsed: result,
      // VULN: If XXE injected file contents, they appear here
      warning: 'XXE vulnerability — external entities processed without restriction'
    });
  });
});

module.exports = router;
