// EASP Authentication Middleware - Phase 1
// Validates JWT bearer tokens, enforces expiration, attaches verified user identity to req.user.

const jwt = require('jsonwebtoken');
const env = require('../config/env');
const User = require('../models/User');

async function authenticateJWT(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      status: 'error',
      error: 'Authentication required: missing or malformed Bearer token'
    });
  }

  const token = authHeader.split(' ')[1].trim();

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET, { algorithms: ['HS256'] });
    if (!decoded.userId || !/^[a-f\d]{24}$/i.test(decoded.userId)) {
      return res.status(401).json({ status: 'error', error: 'Invalid user identity' });
    }
    const user = await User.findById(decoded.userId);
    if (!user || !user.isActive) {
      return res.status(401).json({ status: 'error', error: 'User account is unavailable' });
    }
    req.user = {
      id: user._id.toString(),
      username: user.username,
      email: user.email,
      role: user.role
    };
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({
        status: 'error',
        error: 'Authentication failed: token has expired'
      });
    }
    return res.status(401).json({
      status: 'error',
      error: 'Authentication failed: invalid or tampered token'
    });
  }
}

module.exports = { authenticateJWT };
