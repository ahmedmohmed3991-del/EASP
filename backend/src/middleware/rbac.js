// EASP Role-Based Access Control (RBAC) Middleware - Phase 1
// Restricts route access based on verified user roles: Employee, Analyst, Administrator.

function authorizeRoles(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user || !req.user.role) {
      return res.status(401).json({
        status: 'error',
        error: 'Unauthorized: No active user session identified'
      });
    }

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        status: 'error',
        error: `Access forbidden: Role '${req.user.role}' does not have sufficient permissions for this resource`,
        requiredRoles: allowedRoles
      });
    }

    next();
  };
}

module.exports = { authorizeRoles };
