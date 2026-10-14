// EASP Authentication Middleware - Phase 1
// Validates JWT bearer tokens, enforces expiration, attaches verified user identity to req.user.

const jwt = require('jsonwebtoken');
const env = require('../config/env');

function authenticateJWT(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      status: 'error',
      error: 'Authentication required: missing or malformed Bearer token'
    });
  }

  const token = authHeader.split(' ')[1].trim();

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET);
    req.user = {
      id: decoded.userId,
      username: decoded.username,
      email: decoded.email,
      role: decoded.role
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
