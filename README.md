# EASP — Enterprise AI Security Platform

## 1. Project Overview

EASP is a Zero-Trust-inspired enterprise cybersecurity platform being built
incrementally as a graduation project. The full system will eventually
include authentication/JWT, RBAC, an API gateway, DLP, reversible encrypted
token mapping (AES-256), voice deepfake detection (RawNet2), speech-to-text
(Faster-Whisper), social engineering detection (mBERT), a rule-based risk
engine, a policy engine, audit logging, and a security dashboard.

This repository is being built phase by phase. **This README currently
documents Phase 0 only.**

## 2. Phase 0 Objective

Build and validate the development foundation: a working, containerized
skeleton connecting the React frontend, Node.js/Express backend, Python
FastAPI AI microservice, and MongoDB — with health checks proving each
layer can reach the next. **Phase 0 contains no AI model inference, no
authentication, and no security modules.** It exists purely to prove the
architecture runs end-to-end before any real functionality is added.

## 3. Architecture

```
React Frontend  (port 3000)
      ↓  HTTP
Node.js + Express Backend  (port 5000)
      ↓  HTTP
Python FastAPI AI Service  (port 8000)
      ↓
MongoDB  (port 27017)
```

- The frontend polls the backend's `/health` and `/health/ai` endpoints and
  renders live CONNECTED / DISCONNECTED status for all four layers.
- The backend's `/health` reports its own status plus MongoDB connection
  state.
- The backend's `/health/ai` performs a live call to the AI service's
  `/health` endpoint and reports reachability.
- The AI service's `/health` reports service status and confirms
  `models_loaded: false` — no models are loaded in Phase 0.

## 4. Prerequisites

- Docker Engine (20.10+) and Docker Compose v2 (`docker compose`, not the
  legacy `docker-compose`)
- Git
- (Optional, for running services outside Docker) Node.js 20+, Python 3.11+

## 5. Installation

```bash
git clone <your-repo-url> easp
cd easp
```

## 6. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and set real development values for:

| Variable | Description |
|---|---|
| `MONGO_USERNAME` | MongoDB root username (dev only) |
| `MONGO_PASSWORD` | MongoDB root password (dev only) |
| `MONGO_URI` | Full Mongo connection string used by the backend |
| `PORT` | Backend port (default `5000`) |
| `AI_SERVICE_URL` | URL the backend uses to reach the AI service |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins for CORS |

`.env` is git-ignored. Never commit real secrets, even development ones.
See [Security Headers & CORS Documentation](docs/security/T-P02-014-security-headers-cors.md) for security headers and CORS allow-list architecture.

## 7. Docker Commands

```bash
# Validate the compose file
docker compose config

# Build all images
docker compose build

# Start all services in the background
docker compose up -d

# List running containers
docker compose ps

# Tail logs
docker compose logs --tail=100
```

## 8. Starting the System

```bash
docker compose up -d
```

Then open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:5000/health
- Backend → AI health: http://localhost:5000/health/ai
- AI service health: http://localhost:8000/health

## 9. Stopping the System

```bash
docker compose down
```

To also remove the persisted MongoDB volume (⚠️ deletes data):

```bash
docker compose down -v
```

## 10. Health Checks

| Endpoint | Purpose |
|---|---|
| `GET http://localhost:5000/health` | Backend status + MongoDB connection state |
| `GET http://localhost:5000/health/ai` | Backend → AI service reachability |
| `GET http://localhost:8000/health` | AI service status, confirms no models loaded |

## 11. Troubleshooting

- **Backend shows MongoDB `disconnected`**: confirm `MONGO_URI` in `.env`
  matches the credentials in `MONGO_USERNAME` / `MONGO_PASSWORD`, and that
  the `mongodb` container is healthy (`docker compose ps`).
- **`/health/ai` reports `reachable: false`**: confirm the `ai_service`
  container is running and that `AI_SERVICE_URL` points to
  `http://ai_service:8000` (the Docker service name, not `localhost`, when
  running inside Compose).
- **Frontend shows everything DISCONNECTED**: confirm `VITE_BACKEND_URL`
  points to a URL reachable from your browser (typically
  `http://localhost:5000`), and that CORS is not being blocked (the backend
  enables CORS for all origins in Phase 0).
- **Port already in use**: another process is using 3000, 5000, 8000, or
  27017. Stop it or change the port mapping in `docker-compose.yml`.

## 12. Known Limitations (Phase 0)

- No authentication, JWT, or RBAC — all endpoints are open.
- No DLP, risk engine, policy engine, or audit logging.
- No AI models are loaded or installed (RawNet2, Faster-Whisper, mBERT,
  XGBoost, SHAP are all out of scope for this phase).
- MongoDB is not yet configured for append-only audit behavior — that is
  introduced in the Audit Logging phase.
- CPU-only. No NVIDIA/CUDA requirement exists yet; GPU support arrives
  when RawNet2/Faster-Whisper are implemented.
- Target end-to-end latency: ≤3 seconds, subject to experimental
  validation. This is a target, not a measured result.

## 13. Next Phase

**PHASE 1 — Authentication + JWT + RBAC**
(Not implemented in this repository yet.)
