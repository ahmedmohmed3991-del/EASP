// MongoDB connection handling using mongoose.
// Phase 0: plain connection only. No audit/append-only behavior here.

const mongoose = require('mongoose');
const env = require('./env');

let isConnecting = false;

async function connectDB() {
  if (mongoose.connection.readyState === 1) {
    return mongoose.connection;
  }

  if (isConnecting) {
    return mongoose.connection;
  }

  isConnecting = true;

  try {
    await mongoose.connect(env.MONGO_URI, {
      serverSelectionTimeoutMS: 5000
    });
    console.log(`[MongoDB] Connected: ${env.MONGO_URI}`);
  } catch (err) {
    console.error(`[MongoDB] Connection failed: ${err.message}`);
  } finally {
    isConnecting = false;
  }

  return mongoose.connection;
}

// Returns a simple string describing the current connection state.
// 0 = disconnected, 1 = connected, 2 = connecting, 3 = disconnecting
function getConnectionState() {
  const states = {
    0: 'disconnected',
    1: 'connected',
    2: 'connecting',
    3: 'disconnecting'
  };
  return states[mongoose.connection.readyState] || 'unknown';
}

module.exports = { connectDB, getConnectionState, mongoose };
