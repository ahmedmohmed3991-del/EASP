// EASP Auth Routes - Phase 1
// Endpoints for user registration, login, profile verification, and token refresh.

const express = require('express');
const { register, login, getMe, refreshToken } = require('../controllers/authController');
const { authenticateJWT } = require('../middleware/auth');
const { authLimiter } = require('../middleware/rateLimiter');
const { validateBody } = require('../middleware/validate');

const router = express.Router();

const credentials = {
  email: { required: true, type: 'string', min: 3, max: 254 },
  password: { required: true, type: 'string', min: 1, max: 1024 }
};
router.post('/register', authLimiter, validateBody({
  ...credentials,
  username: { required: true, type: 'string', min: 1, max: 100 },
  password: { required: true, type: 'string', min: 8, max: 1024 }
}), register);
router.post('/login', authLimiter, validateBody(credentials), login);
router.post('/refresh', authLimiter, validateBody({
  refreshToken: { required: true, type: 'string', min: 1, max: 4096 }
}), refreshToken);
router.get('/me', authenticateJWT, getMe);

module.exports = router;
