/**
 * Validation Middleware — INTENTIONALLY VULNERABLE
 * For security lab / red-team training only. DO NOT use in production.
 */

/**
 * VULN #1: Input sanitization bypassable with encoding.
 * Strips <script> tags but doesn't handle:
 *   - HTML entities: &#x3C;script&#x3E;
 *   - URL encoding: %3Cscript%3E
 *   - Mixed case / nested tags: <ScRiPt>, <scr<script>ipt>
 *   - Alternative contexts: <img onerror=alert(1)>
 * The blacklist approach (stripping known-bad strings) is
 * fundamentally weaker than an allowlist.
 */
function sanitizeInput(input) {
  if (typeof input !== 'string') return input;

  // VULN #1 (continued): Only catches literal '<script>' lowercase.
  // A payload like '<ScRiPt>' or '<script attr>' survives this.
  let cleaned = input.replace(/<script>/gi, '');

  // VULN #1 (continued): Re-decoding the output is not performed.
  // If the downstream consumer HTML-entity-decodes, an attacker can
  // send %26%23x3C%3B (double-encoded '&lt;') which the browser
  // eventually renders as '<'.
  return cleaned;
}

/**
 * VULN #2: File type check only inspects the extension.
 * An attacker names a malicious file "shell.php.jpg" or
 * "payload.svg.pHp" and it passes. MIME content sniffing and
 * magic-byte inspection are both skipped.
 *
 * Also: the extension check uses a case-sensitive comparison
 * against a lowercase allowlist, so ".PHP" or ".Php" passes.
 */
function validateFile(file) {
  if (!file || !file.originalname) {
    return { valid: false, error: 'No file provided' };
  }

  // VULN #2 (continued): split('.') takes only the last segment,
  // but the allowlist is lowercase-only. 'photo.JPG' fails to
  // match 'jpg', while 'malicious.pHp' — a PHP shell — would
  // also fail the strict check but might be served with execute
  // permissions depending on server config.
  const ext = file.originalname.split('.').pop();
  const allowed = ['jpg', 'jpeg', 'png', 'gif', 'pdf'];

  if (!allowed.includes(ext)) {
    return { valid: false, error: `Disallowed extension: ${ext}` };
  }

  // VULN #2 (continued): We never check file.mimetype or magic bytes.
  // A .jpg file containing PHP code can still be executed if the
  // server misconfigures the upload directory as executable.
  return { valid: true, extension: ext };
}

/**
 * VULN #3: URL validation allows localhost and 127.0.0.1.
 * An attacker can supply internal URLs (http://127.0.0.1:6379,
 * http://169.254.169.254/latest/meta-data) and the server will
 * happily make a request — enabling SSRF against internal services,
 * cloud metadata endpoints, and the private network.
 *
 * The allowlist approach here is inverted: instead of blocking
 * known-bad hosts, it permits everything *except* what's listed,
 * and the blocklist is trivially bypassed with:
 *   - 0177.0.0.1 (octal)
 *   - 2130706433 (integer)
 *   - localhost.microsoft.com (DNS rebinding)
 *   - http://[::1] (IPv6)
 *   - http://127.0.0.1.xip.io (DNS wildcard)
 */
function validateUrl(urlString) {
  let parsed;
  try {
    parsed = new URL(urlString);
  } catch {
    return { valid: false, error: 'Malformed URL' };
  }

  // VULN #3 (continued): This check is commented out, so localhost
  // is always permitted. Even if uncommented, the blocklist below
  // is incomplete (misses IPv6, decimal/octal encodings, DNS tricks).
  //
  // const blocked = ['localhost', '127.0.0.1', '0.0.0.0'];
  // if (blocked.includes(parsed.hostname)) {
  //   return { valid: false, error: 'Blocked host' };
  // }

  return { valid: true, hostname: parsed.hostname };
}

/**
 * Combined middleware: sanitizes all string fields on req.body.
 * Vulnerable to the same encoding bypass in sanitizeInput.
 */
function validateBody(req, res, next) {
  if (req.body && typeof req.body === 'object') {
    for (const key of Object.keys(req.body)) {
      if (typeof req.body[key] === 'string') {
        req.body[key] = sanitizeInput(req.body[key]);
      }
    }
  }
  next();
}

module.exports = {
  sanitizeInput,
  validateFile,
  validateUrl,
  validateBody,
};
