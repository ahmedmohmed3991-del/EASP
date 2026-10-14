// EASP Auth Routes - Phase 1
// Endpoints for user registration, login, profile verification, and token refresh.

const express = require('express');
const { register, login, getMe, refreshToken } = require('../controllers/authController');
const { authenticateJWT } = require('../middleware/auth');
const { authLimiter } = require('../middleware/rateLimiter');

const router = express.Router();

router.post('/register', authLimiter, register);
router.post('/login', authLimiter, login);
router.post('/refresh', authLimiter, refreshToken);
router.get('/me', authenticateJWT, getMe);

module.exports = router;
