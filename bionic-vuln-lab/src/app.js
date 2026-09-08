/**
 * Bionic Vuln Lab - Main Express Server
 * Deliberately vulnerable Node.js/Express app for authorized security training.
 * DO NOT deploy in production. For educational/lab use only.
 */

const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const { WebSocketServer } = require('ws');
const multer = require('multer');
const xml2js = require('xml2js');
const path = require('path');

const app = express();
const PORT = 5017;
const JWT_SECRET = 'hardcoded-secret-key'; // VULN: hardcoded secret

// --- Middleware ---
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- SQLite Database Initialization ---
const db = new sqlite3.Database(':memory:'); // In-memory DB for lab

db.serialize(() => {
  db.run(`CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT,
    role TEXT DEFAULT 'user',
    balance INTEGER DEFAULT 0
  )`);

  // Insert test data
  db.run(`INSERT INTO users (username, password, email, role, balance) VALUES 
    ('admin', 'admin123', 'admin@lab.local', 'admin', 0),
    ('user1', 'password1', 'user1@lab.local', 'user', 1000),
    ('user2', 'password2', 'user2@lab.local', 'user', 500)
  `);
});

// Make db accessible to routes
app.locals.db = db;
app.locals.jwtSecret = JWT_SECRET;

// --- Route Modules ---
// Each route file exports a router with intentional vulnerabilities documented inline.
const bolaRoutes = require('./routes/bola');       // Broken Object Level Authorization
const sqliRoutes = require('./routes/sqli');       // SQL Injection
const jwtRoutes = require('./routes/jwt');         // JWT flaws
const ssrfRoutes = require('./routes/ssrf');       // Server-Side Request Forgery
const uploadRoutes = require('./routes/upload');   // Unrestricted File Upload
const nosqlRoutes = require('./routes/nosql');     // NoSQL Injection
const xxeRoutes = require('./routes/xxe');         // XML External Entity
const wsRoutes = require('./routes/websocket');    // WebSocket hijacking
const raceRoutes = require('./routes/race');       // Race Condition
const adminRoutes = require('./routes/admin');     // Admin panel (privilege escalation)

app.use('/api/bola', bolaRoutes);
app.use('/api/sqli', sqliRoutes);
app.use('/api/jwt', jwtRoutes);
app.use('/api/ssrf', ssrfRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/nosql', nosqlRoutes);
app.use('/api/xxe', xxeRoutes);
app.use('/api/ws', wsRoutes);
app.use('/api/race', raceRoutes);
app.use('/api/admin', adminRoutes);

// --- Health check ---
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', lab: 'bionic-vuln-lab' });
});

// --- Start HTTP server ---
const server = app.listen(PORT, () => {
  console.log(`[Bionic Vuln Lab] Server running on http://localhost:${PORT}`);
  console.log('[Bionic Vuln Lab] WARNING: Deliberately vulnerable - for authorized training only.');
});

// --- WebSocket Server on /api/ws ---
// VULN: No authentication on WebSocket connections
const wss = new WebSocketServer({ server, path: '/api/ws' });

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: 'welcome', msg: 'Connected to vuln lab WebSocket' }));

  ws.on('message', (data) => {
    // VULN: Echoes messages back to all clients without validation (XSS via WS)
    const payload = data.toString();
    wss.clients.forEach((client) => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ type: 'broadcast', data: payload }));
      }
    });
  });
});

// Export for testing
module.exports = { app, server, db };
