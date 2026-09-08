/**
 * Bionic Vuln Lab - Main Express Server
 * Deliberately vulnerable Node.js/Express app for authorized security training.
 * DO NOT deploy in production. For educational/lab use only.
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 5017;
const JWT_SECRET = 'hardcoded-secret-key'; // VULN: hardcoded secret

// --- Middleware ---
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- Mock Database (pure JS, no native deps) ---
const db = require('./src/db');

// Make db accessible to routes
app.locals.db = db;
app.locals.jwtSecret = JWT_SECRET;

// --- Route Modules ---
const bolaRoutes = require('./src/routes/bola');
const sqliRoutes = require('./src/routes/sqli');
const jwtRoutes = require('./src/routes/jwt');
const ssrfRoutes = require('./src/routes/ssrf');
const uploadRoutes = require('./src/routes/upload');
const nosqlRoutes = require('./src/routes/nosql');
const xxeRoutes = require('./src/routes/xxe');
const raceRoutes = require('./src/routes/race');
const adminRoutes = require('./src/routes/admin');
const wsRoutes = require('./src/routes/websocket');

app.use('/api/bola', bolaRoutes);
app.use('/api/sqli', sqliRoutes);
app.use('/api/jwt', jwtRoutes);
app.use('/api/ssrf', ssrfRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/nosql', nosqlRoutes);
app.use('/api/xxe', xxeRoutes);
app.use('/api/race', raceRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/ws', wsRoutes);

// --- WebSocket Server (separate from HTTP) ---
const { WebSocketServer } = require('ws');
const server = app.listen(PORT, () => {
  console.log(`[Bionic Vuln Lab] Server running on http://localhost:${PORT}`);
  console.log('[Bionic Vuln Lab] WARNING: Deliberately vulnerable - for authorized training only.');
});

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

// --- Health check ---
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', lab: 'bionic-vuln-lab' });
});

// Export for testing
module.exports = { app, server, db };
