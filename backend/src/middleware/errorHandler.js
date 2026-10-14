// Centralized error handling middleware.

function notFoundHandler(req, res, next) {
  res.status(404).json({
    error: 'Not Found',
    path: req.originalUrl
  });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  const isCorsError = err.message && (err.message.includes('CORS') || err.message.includes('Not allowed by CORS'));
  const statusCode = err.statusCode || err.status || (isCorsError ? 403 : 500);

  if (statusCode >= 500) {
    console.error('[Error]', err.message);
  }

  res.status(statusCode).json({
    error: err.message || 'Internal Server Error'
  });
}

module.exports = { notFoundHandler, errorHandler };

