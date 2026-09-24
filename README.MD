# EASP Frontend - Enterprise AI Security Platform

Welcome to the frontend repository of our graduation project, the **Enterprise AI Security Platform (EASP)**. This dashboard provides a secure, modern interface for monitoring system security, tracking alerts, and managing security policies.

## Tech Stack
- **Framework:** React (Vite)
- **Routing:** React Router DOM
- **HTTP Client:** Axios
- **Styling:** Custom CSS / Dark Mode UI

## Features

- **Authentication (Phase 1):** JWT-based login/register, backed by the real `.NET` backend (`/api/Auth/login`, `/api/Auth/register`, `/api/Auth/me`).
- **Role-Aware Security Dashboard (Phase 11):**
  - Role-based routing — Employee, Analyst, and Administrator each see a different dashboard view, driven by the roles returned from `/api/Auth/me`.
  - **Employee view:** own detected events, risk score, and policy action only.
  - **Analyst view:** full Detected Incidents table (derived from the audit log) plus the raw Audit Log.
  - **Administrator view:** everything Analyst sees, plus a Measured Performance section and Policy Configuration panel.
  - Incidents are derived from `GET /api/AuditLogs` by filtering security-decision actions (`RISK_EVALUATION`, `AI_TEXT_ANALYSIS`, `AI_VOICE_ANALYSIS`) and parsing their `detailsJson`.
  - Any metric that hasn't actually been measured (e.g. Phase 13 performance results, which the backend doesn't expose yet) renders as **"No measured data available"** instead of a fabricated number.

## Getting Started & Local Installation

To run this project locally on your machine, open your terminal inside the project directory and run the following commands sequentially:

```
cd EASP-Frontend
npm install
npm run dev
```

### Command Breakdown:
1. **`cd EASP-Frontend`**: Changes your current terminal directory to the project's root folder so you can work inside it.
2. **`npm install`**: Installs all required project dependencies (React, Axios, router packages, etc.).
3. **`npm run dev`**: Starts the local Vite development server at `http://localhost:5173`.

### Backend

The frontend expects the EASP backend (`.NET`) running at `http://localhost:5000`. Start it separately (`dotnet run` inside `backend/EASP.Api`) before using the dashboard — CORS is already configured there to allow `http://localhost:5173`.