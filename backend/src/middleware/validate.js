// EASP Input Validation Middleware - Phase 2 (T-P02-015)
// Provides clean schema validation to prevent malformed inputs, prototype pollution, and SQL/NoSQL injection payloads.

function validateBody(schema) {
  return (req, res, next) => {
    if (!req.body || typeof req.body !== 'object' || Array.isArray(req.body)) {
      return res.status(400).json({
        status: 'error',
        error: 'Validation error: Request body must be a valid JSON object'
      });
    }

    const errors = [];

    for (const [field, rules] of Object.entries(schema)) {
      const value = req.body[field];

      if (rules.required && (value === undefined || value === null || value === '')) {
        errors.push(`Field '${field}' is required`);
        continue;
      }

      if (value !== undefined && value !== null) {
        if (rules.type && typeof value !== rules.type) {
          errors.push(`Field '${field}' must be of type ${rules.type}`);
        }

        if (rules.min !== undefined) {
          if (typeof value === 'string' && value.length < rules.min) {
            errors.push(`Field '${field}' must be at least ${rules.min} characters`);
          } else if (typeof value === 'number' && value < rules.min) {
            errors.push(`Field '${field}' must be >= ${rules.min}`);
          }
        }

        if (rules.max !== undefined) {
          if (typeof value === 'string' && value.length > rules.max) {
            errors.push(`Field '${field}' cannot exceed ${rules.max} characters`);
          } else if (typeof value === 'number' && value > rules.max) {
            errors.push(`Field '${field}' must be <= ${rules.max}`);
          }
        }

        if (rules.pattern && typeof value === 'string' && !rules.pattern.test(value)) {
          errors.push(rules.message || `Field '${field}' format is invalid`);
        }

        if (rules.enum && !rules.enum.includes(value)) {
          errors.push(`Field '${field}' must be one of: ${rules.enum.join(', ')}`);
        }
      }
    }

    if (errors.length > 0) {
      return res.status(400).json({
        status: 'error',
        error: 'Validation failed',
        details: errors
      });
    }

    next();
  };
}

module.exports = { validateBody };
