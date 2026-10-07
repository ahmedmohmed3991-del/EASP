# EASP — Enterprise AI Security Platform

## 1. Executive Platform Overview

The **Enterprise AI Security Platform (EASP)** is a Zero-Trust cybersecurity platform designed to protect modern organizations against dual-threat attack vectors targeting artificial intelligence workflows:
1. **Data Loss Prevention (DLP)**: Accidental leakage of sensitive credentials, API keys, intellectual property, PII, and financial identifiers into Generative AI prompts, utilizing reversible AES-256-GCM tokenization with automated TTL expiration.
2. **Social Engineering & Deepfake Voice Defense**: Multi-modal detection of synthetic audio impersonation (RawNet2 acoustic analysis) combined with automated speech transcription (Faster-Whisper) and intent classification (mBERT) to intercept and neutralize coercive vishing attacks.

EASP unifies these vectors into a deterministic **Multi-Modal Risk Engine** and **Policy Enforcement Engine** backed by an append-only **Cryptographic Hash-Chained Audit Ledger** (SHA-256).

---

## 2. Integrated Platform Architecture

```text
               ┌──────────────────────────────────────────────────┐
               │        React + Vite SOC Frontend (Port 3000)     │
               │   Prompt Scanner | Audio AI | SOC Desk | Ledger   │
               └────────────────────────┬─────────────────────────┘
                                        │ HTTP / JSON / JWT
                                        ▼
               ┌──────────────────────────────────────────────────┐
               │         API Gateway & Security Middleware        │
               │  Rate Limiting | Helmet | CORS Allow-List | RBAC │
               └────────────────────────┬─────────────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
        ┌────────────────────────────────┐   ┌───────────────────────────┐
        │      Node.js / Express Core    │   │  Python FastAPI AI Engine │
        │        Backend (Port 5000)     │   │        (Port 8000)        │
        ├────────────────────────────────┤   ├───────────────────────────┤
        │ • User Auth & JWT (bcrypt ≥12) │   │ • DLP Regex + Presidio    │
        │ • AES-256-GCM Token Store (TTL)│   │ • RawNet2 Voice Detector  │
        │ • Deterministic Policy Engine  │   │ • Faster-Whisper ASR      │
        │ • Unified Risk Engine          │   │ • mBERT Social Head       │
        │ • SHA-256 Audit Hash Chaining  │   │ • DSP Acoustic Inspection │
        └───────────────┬────────────────┘   └─────────────▲─────────────┘
                        │                                  │
                        │        Internal Microservice     │
                        └──────────────────────────────────┘
                                        │
                                        ▼
               ┌──────────────────────────────────────────────────┐
               │           MongoDB Database (Port 27017)          │
               │   Single Source of Truth: Users, Roles, Tokens,  │
               │   Policies, Incidents, and Cryptographic Logs    │
               └──────────────────────────────────────────────────┘
```

---

## 3. Technology Stack & Continuity

* **Backend**: Node.js 20+, Express.js, JWT (`jsonwebtoken`), Password Hashing (`bcrypt` $\ge 12$ rounds), AES-256-GCM (`crypto`).
* **Database**: MongoDB 6+ / 7+ with Mongoose ODM (single consistent persistence layer; strict TTL indexes and immutable audit logs).
* **AI Subsystem**: Python 3.11+, FastAPI, PyTorch, Hugging Face Transformers (`mBERT`), Presidio Analyzer & Custom Regex Engine, Faster-Whisper, SciPy/NumPy Signal Processing.
* **Frontend**: React 18, Vite 5, Vanilla CSS Cyber/SOC Glassmorphism Design System (Zero Tailwind/Bootstrap dependencies).
* **Security & Infrastructure**: Helmet, CORS Strict Allow-list, express-rate-limit, Docker & Docker Compose.

---

## 4. Default Seeded Credentials (SOC Demo)

The system automatically initializes default role-based accounts with seeded passwords (`Password123!`):

| Role | Email | Password | Permissions & Scope |
|---|---|---|---|
| **Administrator** | `admin@easp.local` | `Password123!` | Full governance, policy creation, token restoration, incident triage, ledger verification. |
| **Analyst** | `analyst@easp.local` | `Password123!` | Incident triage, analyst note logging, authorized token restoration, audit inspection. |
| **Employee** | `employee@easp.local` | `Password123!` | Prompt scanning, audio submission, self-service inspection. Restricted from tokens and audit logs. |

---

## 5. Quickstart & Local Setup

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/ahmedmohmed3991-del/EASP.git easp
cd easp
cp .env.example .env
```

Ensure `.env` contains:
```env
PORT=5000
NODE_ENV=development
MONGO_URI=mongodb://127.0.0.1:27017/easp
AI_SERVICE_URL=http://127.0.0.1:8000
JWT_SECRET=easp_dev_super_secret_jwt_key_2026_at_least_32_chars
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 2: Seed Database

```bash
cd backend
npm install
node src/scripts/seedUsers.js
node src/scripts/seedPolicies.js
```

### Step 3: Launch AI Microservice

```bash
cd ../ai_service
python -m venv venv
.\venv\Scripts\activate      # Windows (or source venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python app.py
```
*Microservice active at `http://127.0.0.1:8000` with interactive OpenAPI docs at `/docs`.*

### Step 4: Launch Backend Server

```bash
cd ../backend
npm start
```
*Backend active at `http://127.0.0.1:5000`.*

### Step 5: Launch Frontend Application

```bash
cd ../frontend
npm install
npm run dev
```
*Access the SOC console at `http://localhost:5173` or build for production with `npm run build`.*

---

## 6. Comprehensive Test & Verification Suites

Execute the automated test suites to verify system integrity:

```bash
# 1. Backend Security Headers & CORS Allow-List (10/10 PASS)
cd backend && node tests/security.test.js

# 2. Comprehensive Security, RBAC, DLP & Hash-Chain Suite (13/13 PASS)
node tests/full_security.test.js

# 3. End-to-End Graduation Scenarios Suite (5/5 PASS)
node tests/e2e.test.js

# 4. Python AI Subsystem Unit Tests
cd ../ai_service
python tests/test_ai_components.py

# 5. Wall-Clock Latency Benchmark Harness (Passes <= 3.0s requirement)
python tests/test_latency.py
```

---

## 7. Validated Graduation Scenarios

1. **Scenario 1 — Benign Prompt**: Normal user query evaluated through DLP and NLP $\rightarrow$ Low Risk $\rightarrow$ `ALLOW` $\rightarrow$ Cryptographic audit record generated.
2. **Scenario 2 — DLP Credential Leak**: Sensitive API key (e.g. OpenAI secret `sk-proj-...` or Credit Card) detected $\rightarrow$ Reversible AES-256 tokenization replaces secret $\rightarrow$ `REDACT` action enforced $\rightarrow$ Only Analyst/Admin can restore original secret via fail-closed endpoint.
3. **Scenario 3 — Voice Deepfake Attack**: Synthetic voice sample submitted $\rightarrow$ RawNet2 detects acoustic anomalies (high spoof probability) $\rightarrow$ Risk elevated $\rightarrow$ `ESCALATE` action with analyst notification.
4. **Scenario 4 — Social Engineering Coercion**: High-urgency executive impersonation text $\rightarrow$ mBERT detects coercive pressure $\rightarrow$ Threat score $> 0.80$ $\rightarrow$ `BLOCK` action enforced $\rightarrow$ High severity SOC incident logged.
5. **Scenario 5 — Multi-Modal Combined Threat**: Simultaneous synthetic voice + social engineering coercion + credential harvesting $\rightarrow$ Unified Multi-Modal Risk Engine triggers critical threat elevation $\rightarrow$ `BLOCK` $\rightarrow$ Immediate Critical Incident dispatched with SHA-256 audit record.

---

## 8. Architectural Integrity & Compliance Notes

* **Single Persistence Layer**: MongoDB/Mongoose is the sole database technology across all subsystems. No duplicate or competing SQL databases are present.
* **No Fabricated Benchmarks**: Model benchmarks and telemetry display only empirically verified results; where weights are offline in dev environments, the interface explicitly reports `"No measured live metrics fabricated per Task Book T-P11-057"`.
* **Phase 2 XGBoost + SHAP Status**: Evaluated and formally classified as **Conditional / Not Implemented** due to the rejection of circular synthetic datasets per Task Book T-P13-063. Phase 1 Deterministic Rule-Based Engine serves as the verified production baseline.
* **Future Work Protection**: Video/image deepfakes, PBX telephony bridges, universal HTTPS proxying, and autoencoder anomaly detection remain documented as Future Work out of scope for graduation baseline.
