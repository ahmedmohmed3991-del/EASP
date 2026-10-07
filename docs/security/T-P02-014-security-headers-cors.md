# Task T-P02-014: Helmet Security Headers & CORS Allow-List Documentation

## Overview
This document describes the implementation, policy rationale, and configuration instructions for **Helmet Security Headers** and the **CORS Allow-List** within the EASP backend (Node.js/Express).

---

## 1. Helmet Security Headers

Helmet secures Express apps by setting various HTTP response headers to defend against common web application vulnerabilities (such as XSS, clickjacking, MIME sniffing, and clickjacking attacks).

### Configured Headers & Rationale

| Header | Configured Value | Security Purpose / Mitigation |
|---|---|---|
| `Content-Security-Policy` (CSP) | Strict baseline (`default-src 'self'`, scripts/styles/images restricted) | Restricts resource loading to prevent Cross-Site Scripting (XSS) and data injection. |
| `Strict-Transport-Security` (HSTS) | `max-age=31536000; includeSubDomains; preload` | Forces browsers to communicate exclusively over HTTPS, mitigating man-in-the-middle (MITM) and SSL-stripping attacks. |
| `X-Content-Type-Options` | `nosniff` | Prevents browsers from MIME-sniffing a response away from the declared `Content-Type`, stopping malicious script execution from uploaded content. |
| `X-Frame-Options` | `SAMEORIGIN` | Mitigates clickjacking attacks by ensuring the backend responses cannot be embedded into unauthorized third-party `<iframe>`s. |
| `Cross-Origin-Opener-Policy` (COOP) | `same-origin` | Isolates the top-level browsing context to prevent cross-origin window manipulation and Spectre-like side-channel attacks. |
| `Cross-Origin-Resource-Policy` (CORP) | `cross-origin` | Allows authorized cross-origin frontends (e.g., React on port 3000/5173) to consume backend API responses while blocking unauthorized embedding. |
| `Referrer-Policy` | `no-referrer` | Protects privacy by omitting the `Referer` header from outgoing requests, ensuring internal tokens or paths are not leaked. |
| `X-DNS-Prefetch-Control` | `off` | Prevents browsers from proactively performing DNS prefetching on links in API payloads. |
| `X-Download-Options` | `noopen` | Specific to Internet Explorer; prevents opening HTML downloads directly in site context. |
| `X-Permitted-Cross-Domain-Policies` | `none` | Blocks Adobe Flash and PDF plugins from loading data across domains. |
| `X-Powered-By` | *Removed / Hidden* | Conceals the technology stack (`Express`) from attackers fingerprinting the server. |

---

## 2. CORS Allow-List Architecture

CORS (Cross-Origin Resource Sharing) is configured via a strict allow-list mechanism instead of an insecure wildcard (`*`) policy.

### Key Characteristics:
1. **Configurable via Environment Variables**: Allowed origins are dynamically loaded from `ALLOWED_ORIGINS` (or legacy `CORS_ALLOWED_ORIGINS`).
2. **Normalized Matching**: Whitespace and trailing slashes are automatically trimmed and normalized so `http://localhost:3000/` and `http://localhost:3000` match seamlessly.
3. **Non-Browser / Machine-to-Machine Support**: Requests without an `Origin` header (e.g., cURL, Docker service-to-service calls, mobile clients, health checks) are permitted without generating CORS errors.
4. **Credential Safety**: Supports credentials (`credentials: true`) exclusively in combination with validated explicit origins, preventing wildcard credential security vulnerabilities.
5. **Deterministic Rejection**: Unauthorized origins are blocked with an HTTP 403 Forbidden status code and structured error JSON response.
6. **Preflight Optimization**: Supports standard HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`) and headers (`Content-Type`, `Authorization`, `X-Requested-With`, `Accept`, `Origin`) with a 24-hour preflight cache (`maxAge: 86400`).

---

## 3. Configuration Guide

### Configuring Allowed Origins

Add or update `ALLOWED_ORIGINS` in your `.env` file with a comma-separated list of origins (scheme + domain/IP + port):

```env
# Example for local development
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Example for production / staging
ALLOWED_ORIGINS=https://app.easp.enterprise.com,https://admin.easp.enterprise.com
```

### Running Validation Tests

To verify that Helmet headers and CORS allow-list rules function correctly:

```bash
cd backend
npm test
```
