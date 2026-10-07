// EASP Backend - Enterprise AI Security Platform
// Security-hardened Express entry point wiring all 15 project phases.

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

const env = require('./config/env');
const { connectDB } = require('./config/db');
const { corsOptions } = require('./config/cors');
const { helmetOptions } = require('./config/helmet');
const { requestLogger } = require('./middleware/requestLogger');
const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

// Route modules
const healthRoutes = require('./routes/health');
const authRoutes = require('./routes/auth');
const securityRoutes = require('./routes/security');
const incidentsRoutes = require('./routes/incidents');
const auditLogsRoutes = require('./routes/auditLogs');
const policiesRoutes = require('./routes/policies');
const metricsRoutes = require('./routes/metrics');

const app = express();

// 1. Helmet security headers (Content-Security-Policy, HSTS, X-Frame-Options, etc.)
app.use(helmet(helmetOptions));

// 2. Strict CORS allow-list
app.use(cors(corsOptions));

// 3. Request Logging & Security Audit Hook
app.use(requestLogger);

// 4. Request Body Parsers (bounded size to mitigate DoS)
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 5. Application Routes
app.use('/health', healthRoutes);
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/security', securityRoutes);
app.use('/api/v1/incidents', incidentsRoutes);
app.use('/api/v1/audit-logs', auditLogsRoutes);
app.use('/api/v1/policies', policiesRoutes);
app.use('/api/v1/metrics', metricsRoutes);

app.get('/', (req, res) => {
  res.status(200).json({
    service: 'easp-backend',
    status: 'running',
    version: '1.0.0',
    message: 'EASP Enterprise AI Security Platform Backend is active.',
    architecture: 'Two-Branch Defense: Voice Anti-Spoofing & Reversible Generative AI DLP'
  });
});

// 6. Centralized Error Handling
app.use(notFoundHandler);
app.use(errorHandler);

async function start() {
  await connectDB();

  // Auto-seed policies & initial data if policies are empty
  try {
    const Policy = require('./models/Policy');
    const policyCount = await Policy.countDocuments();
    if (policyCount === 0 && env.NODE_ENV !== 'production') {
      console.log('[EASP Backend] Database empty. Running seedAll...');
      const { seedAll } = require('./scripts/seedAll');
      await seedAll();
    }
  } catch (err) {
    console.error('[EASP Backend] Auto-seed check warning:', err.message);
  }

  app.listen(env.PORT, () => {
    console.log(`[EASP Backend] Listening on port ${env.PORT} (${env.NODE_ENV})`);
  });
}

if (require.main === module) {
  start();
}

module.exports = app;
