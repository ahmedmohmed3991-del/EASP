// EASP Backend - Enterprise AI Security Platform
// Security-hardened Express entry point with Helmet security headers and CORS allow-list.

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

const env = require('./config/env');
const { connectDB } = require('./config/db');
const { corsOptions } = require('./config/cors');
const { helmetOptions } = require('./config/helmet');
const healthRoutes = require('./routes/health');
const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

const app = express();

// 1. Apply Helmet security headers before all routes and middleware
app.use(helmet(helmetOptions));

// 2. Apply CORS policy with environment-configured allow-list
app.use(cors(corsOptions));

// 3. Body parser middleware
app.use(express.json());

// 4. Application routes
app.use('/health', healthRoutes);

app.get('/', (req, res) => {
  res.status(200).json({
    service: 'easp-backend',
    status: 'running',
    message: 'EASP Backend is running with Helmet security headers and CORS allow-list active.'
  });
});

// 5. Centralized error handling
app.use(notFoundHandler);
app.use(errorHandler);

async function start() {
  await connectDB();

  app.listen(env.PORT, () => {
    console.log(`[EASP Backend] Listening on port ${env.PORT} (${env.NODE_ENV})`);
  });
}

if (require.main === module) {
  start();
}

module.exports = app;
