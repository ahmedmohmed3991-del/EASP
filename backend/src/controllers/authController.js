// EASP Auth Controller - Phase 1
// Handles user registration, login, JWT issuance, and session verification.

const jwt = require('jsonwebtoken');
const User = require('../models/User');
const env = require('../config/env');

function generateTokens(user) {
  const payload = {
    userId: user._id.toString(),
    username: user.username,
    email: user.email,
    role: user.role
  };

  const accessToken = jwt.sign(payload, env.JWT_SECRET, {
    expiresIn: env.JWT_EXPIRES_IN
  });

  const refreshToken = jwt.sign(payload, env.JWT_REFRESH_SECRET, {
    expiresIn: env.JWT_REFRESH_EXPIRES_IN
  });

  return { accessToken, refreshToken };
}

// POST /api/v1/auth/register
async function register(req, res) {
  try {
    const { username, email, password, role } = req.body;

    if (!username || !email || !password) {
      return res.status(400).json({
        status: 'error',
        error: 'Validation failed: username, email, and password are required'
      });
    }

    if (password.length < 8) {
      return res.status(400).json({
        status: 'error',
        error: 'Validation failed: password must be at least 8 characters long'
      });
    }

    // Check existing user
    const existingUser = await User.findOne({
      $or: [{ email: email.toLowerCase() }, { username }]
    });

    if (existingUser) {
      return res.status(409).json({
        status: 'error',
        error: 'A user with this email or username already exists'
      });
    }

    const passwordHash = await User.hashPassword(password);
    // Public registration must never grant privileged roles.
    const assignedRole = 'Employee';

    const user = new User({
      username,
      email: email.toLowerCase(),
      passwordHash,
      role: assignedRole
    });

    const { accessToken, refreshToken } = generateTokens(user);
    user.refreshToken = refreshToken;
    user.lastLoginAt = new Date();
    await user.save();

    res.status(201).json({
      status: 'success',
      message: 'User registered successfully',
      user: user.toJSON(),
      token: accessToken,
      refreshToken
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to register user: ' + err.message
    });
  }
}

// POST /api/v1/auth/login
async function login(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        status: 'error',
        error: 'Email and password are required'
      });
    }

    // Find user with passwordHash explicitly selected
    const user = await User.findOne({ email: email.toLowerCase() }).select('+passwordHash +refreshToken');

    if (!user || !user.isActive) {
      // Use uniform message to avoid user-enumeration
      return res.status(401).json({
        status: 'error',
        error: 'Invalid email or password'
      });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({
        status: 'error',
        error: 'Invalid email or password'
      });
    }

    const { accessToken, refreshToken } = generateTokens(user);
    user.refreshToken = refreshToken;
    user.lastLoginAt = new Date();
    await user.save();

    res.status(200).json({
      status: 'success',
      message: 'Authentication successful',
      user: user.toJSON(),
      token: accessToken,
      refreshToken
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Authentication failed: ' + err.message
    });
  }
}

// GET /api/v1/auth/me
async function getMe(req, res) {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.status(404).json({
        status: 'error',
        error: 'User not found'
      });
    }

    res.status(200).json({
      status: 'success',
      user: user.toJSON()
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to retrieve profile: ' + err.message
    });
  }
}

// POST /api/v1/auth/refresh
async function refreshToken(req, res) {
  try {
    const { refreshToken: token } = req.body;

    if (!token) {
      return res.status(400).json({
        status: 'error',
        error: 'Refresh token is required'
      });
    }

    let decoded;
    try {
      decoded = jwt.verify(token, env.JWT_REFRESH_SECRET);
    } catch {
      return res.status(401).json({
        status: 'error',
        error: 'Invalid or expired refresh token'
      });
    }

    const user = await User.findById(decoded.userId).select('+refreshToken');
    if (!user || !user.isActive || user.refreshToken !== token) {
      return res.status(401).json({
        status: 'error',
        error: 'Revoked or invalid session'
      });
    }

    const newTokens = generateTokens(user);
    user.refreshToken = newTokens.refreshToken;
    await user.save();

    res.status(200).json({
      status: 'success',
      token: newTokens.accessToken,
      refreshToken: newTokens.refreshToken
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to refresh token: ' + err.message
    });
  }
}

module.exports = { register, login, getMe, refreshToken };
