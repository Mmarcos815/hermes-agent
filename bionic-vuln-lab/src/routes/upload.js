const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const { authenticate } = require('../middleware/auth');

/**
 * Unrestricted File Upload Vulnerability
 *
 * POST /api/upload
 *
 * VULNERABILITY: Only the file extension is checked. The server stores
 * uploaded files with their original name in a publicly accessible directory.
 * An attacker uploads "shell.jpg.php" — passes the extension check (.php
 * after .jpg confuses naive checks, or .phtml, .php5 variants).
 *
 * The upload directory is within the web root, so the server executes the file.
 *
 * EXPLOIT: Upload a PHP web shell disguised as an image, then access
 * /uploads/shell.php?cmd=whoami for RCE.
 *
 * IMPACT: Remote code execution, full server compromise.
 *
 * FIX: Use MIME type + magic bytes validation, randomize filenames, store
 * outside web root, disable script execution in upload dir.
 */
const storage = multer.diskStorage({
  // VULN: Keeps original filename — attacker controls the name
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, '../../public/uploads'));
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname); // VULN: originalname preserved
  }
});

const upload = multer({
  storage,
  // VULN: Only checks if filename CONTAINS an image extension anywhere
  // "shell.jpg.php" passes because .jpg is found in the name
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.gif'];
    const name = file.originalname.toLowerCase();

    // VULN: Trivial bypass — "shell.jpg.php" contains ".jpg"
    // VULN: Case sensitivity: ".JPG" or ".Php" variants
    const passes = allowed.some(ext => name.includes(ext));
    if (passes) {
      return cb(null, true);
    }
    cb(new Error('Invalid file type'));
  }
});

router.post('/upload', authenticate, upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  return res.json({
    message: 'File uploaded successfully',
    filename: req.file.originalname,
    path: `/uploads/${req.file.originalname}`,
    warning: 'Upload vulnerable — only extension checked, file stored in web root'
  });
});

module.exports = router;
