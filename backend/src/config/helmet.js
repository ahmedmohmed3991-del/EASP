const env = require('./env');

/**
 * Helmet Security Headers Configuration
 * Tailored for enterprise REST API security in EASP.
 * Provides defense-in-depth protection against XSS, clickjacking, MIME sniffing,
 * cross-origin resource leakage, and information disclosure.
 */
const helmetOptions = {
  // Content Security Policy (CSP): Restrict sources of executable scripts, objects, frames
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      baseUri: ["'self'"],
      fontSrc: ["'self'", 'https:', 'data:'],
      formAction: ["'self'"],
      frameAncestors: ["'self'"],
      imgSrc: ["'self'", 'data:', 'blob:'],
      objectSrc: ["'none'"],
      scriptSrc: ["'self'"],
      scriptSrcAttr: ["'none'"],
      styleSrc: ["'self'", 'https:', "'unsafe-inline'"],
      upgradeInsecureRequests: env.NODE_ENV === 'production' ? [] : null
    }
  },
  // Cross-Origin-Opener-Policy: Isolates browsing context to same-origin
  crossOriginOpenerPolicy: { policy: 'same-origin' },
  // Cross-Origin-Resource-Policy: Allows cross-origin API resource sharing with authorized frontends
  crossOriginResourcePolicy: { policy: 'cross-origin' },
  // Cross-Origin-Embedder-Policy: Disabled for API compatibility unless explicitly required
  crossOriginEmbedderPolicy: false,
  // DNS Prefetch Control: Prevent browser DNS prefetching
  dnsPrefetchControl: { allow: false },
  // Frameguard: Prevent clickjacking (X-Frame-Options: SAMEORIGIN)
  frameguard: { action: 'sameorigin' },
  // Hide X-Powered-By header to obscure the backend runtime
  hidePoweredBy: true,
  // Strict-Transport-Security (HSTS): Enforce HTTPS in production environments
  hsts: {
    maxAge: 31536000, // 1 year in seconds
    includeSubDomains: true,
    preload: true
  },
  // IE No Open: Prevent IE from executing downloads in the site's context
  ieNoOpen: true,
  // MIME Sniffing: Prevent browsers from MIME-sniffing response bodies away from declared Content-Type
  noSniff: true,
  // Origin-Agent-Cluster: Request origin-keyed agent cluster
  originAgentCluster: true,
  // Permitted Cross Domain Policies: Restrict Adobe Flash / PDF cross-domain access
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
  // Referrer-Policy: Prevent referrer leakage
  referrerPolicy: { policy: 'no-referrer' },
  // XSS Filter: Disable legacy buggy XSS auditor (standard practice for modern browsers)
  xssFilter: false
};

module.exports = { helmetOptions };
