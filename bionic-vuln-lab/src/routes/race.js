const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const db = require('../db');

/**
 * Race Condition Vulnerability (TOCTOU)
 *
 * POST /api/buy
 *
 * VULNERABILITY: Balance deduction has a check-then-act race condition.
 * The server reads the user's balance, checks if sufficient, then deducts.
 * Between the read and the write, concurrent requests can pass the check.
 *
 * EXPLOINT: Send 50 simultaneous POST /api/buy requests with $10 each
 * when balance is $100. All 50 pass the balance check before any
 * deduction commits — user spends $500 with only $100 in account.
 *
 * IMPACT: Negative balances, double-spending, financial fraud.
 *
 * FIX: Use database transactions with proper locking (SELECT ... FOR UPDATE),
 * or use atomic UPDATE with WHERE balance >= amount and check rows affected.
 */
router.post('/buy', authenticate, (req, res) => {
  const { productId, price } = req.body;
  const userId = req.user.id;

  // VULN: Step 1 — Read current balance (no lock held)
  const user = db.findUserById(userId);

  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  // VULN: Step 2 — Check balance (TOCTOU window opens here)
  if (user.balance < price) {
    return res.status(400).json({ error: 'Insufficient funds' });
  }

  // VULN: Step 3 — Deduct balance (TOCTOU window — another request
  // could have passed the check between Step 1 and here)
  const newBalance = user.balance - price;

  // VULN: Non-atomic update — no transaction, no row locking
  user.balance = newBalance;

  return res.json({
    message: 'Purchase successful',
    productId,
    price,
    newBalance,
    warning: 'Race condition — balance check and deduction are not atomic'
  });
});

module.exports = router;
