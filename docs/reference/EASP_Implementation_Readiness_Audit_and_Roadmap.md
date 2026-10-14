# EASP — Implementation Readiness Audit & Roadmap

**Status: AUDIT ONLY. No code has been written. Awaiting your approval before Phase 0 begins.**

---

## 0. Source Documents Actually Available

| Document | Present? | Role |
|---|---|---|
| Graduation Project Proposal v1.1 | Yes (`EASP_Graduation_Project_Proposal_v1_1__1_.md`) | Primary source for original project content |
| Feasibility / Chapter 1 Revision report | Yes (`EASP_Chapter1_Revision_Final.docx`) | Secondary — audit, corrections, feasibility decisions |
| **Chapter 1 Final v2.0** (produced in this thread) | Yes (`EASP_Graduation_Project_Chapter1_Final_v2.0.docx`) | **Treated as the current authoritative academic baseline** — it already resolved every conflict between the two documents above under your explicit final decisions (Sections A–R of your prior message) |
| **AI Subsystem Proposal and SRS v2.1 diagrams.md** | **NOT FOUND** | Referenced repeatedly *inside* the feasibility report (quoted as an existing separate document with its own Part B, change log, endpoint definitions) but it has never actually been uploaded to me in any session. Everything I know about it is second-hand, via quotations inside the feasibility report. |
| Existing repository / source code | **NOT FOUND** | No `backend/`, `frontend/`, `ai-services/`, `package.json`, `.git`, or any implementation artifact exists anywhere in the workspace |
| Architecture diagrams (pre-existing) | Not found as separate files | Three diagrams (Use Case, Activity, Architecture) exist only as ones I generated for Chapter 1 Final v2.0 |

**Action required before Phase 12–14 (AI services) can start with full confidence:** please upload the actual `AI Subsystem Proposal and SRS v2.1` file. Until then, I am treating Chapter 1 Final v2.0 — which already absorbed the SRS's key corrections (pretrained-first mBERT framing, Phase 1/2 split, CodeSearchNet removal) — as the working source of truth, and flagging anywhere the SRS might contain implementation-level detail (exact endpoint paths, exact latency budget per stage, exact milestone weeks) that I have not independently verified.

---

## 1. Current Repository Structure

None exists. This is a greenfield implementation. No inherited structure, naming, or partial code constrains Phase 0.

## 2. Existing Implemented Components

None. Nothing has been coded.

## 3. Missing Components

Everything — by design, since nothing exists yet. Full target component list is in Section 7 (Technology Stack) and the Phase table below.

## 4. Documented Baseline Components (per Chapter 1 Final v2.0, §3.2 / §9)

Authentication/RBAC/JWT · API Gateway (rate limiting, TLS) · Phase 1 rule-based Policy/Risk Engine · DLP (Regex + Presidio + spaCy) · Reversible encrypted token-mapping redaction (AES-256) · Audit logging + Security Dashboard · Voice deepfake detection (RawNet2) · Speech-to-text (Faster-Whisper) · Social-engineering detection (mBERT encoder + project-specific classification head) · Controlled Audio/VoIP demonstration environment · Basic security testing.

**Should-implement (conditional, non-blocking):** Risk Engine Phase 2 (XGBoost + SHAP) · SIEM log export · Browser extension (2–3 named AI web apps) · voice-confidence calibration.

**Optional:** Arabic upgrade (mBERT → XLM-R) · rule-based source-code/API-key leakage detection · analyst feedback loop for Phase 2 retraining.

## 5. Future Work Components (excluded from implementation entirely at this stage)

Image/video deepfake detection · production PBX/enterprise telephony integration · universal HTTPS interception · undefined external Threat Intelligence module · advanced ML-based semantic source-code classification · voiceprint enrollment/speaker verification · autoencoder anomaly detection · federated learning/on-device deployment · native Teams/Slack/email integrations · SOAR automation playbooks.

**These must not appear in any Phase below.** If at any point an Antigravity session drifts toward implementing one of these, stop and flag it rather than build it.

## 6. Conflicting Requirements

**No new conflicts.** This message's 13 numbered constraints are consistent with — and in several places restate verbatim — the corrections already locked into Chapter 1 Final v2.0 (reversible-token-mapping phrasing, mBERT-as-encoder-not-classifier, Phase 1 mandatory/Phase 2 conditional, target-vs-measured latency, controlled VoIP only, scoped browser extension, conditional threat intelligence, rule-based source-code detection baseline). I'm treating Chapter 1 Final v2.0 as binding unless you tell me otherwise.

One thing to watch, not a conflict yet: the missing SRS v2.1 file might contain endpoint names or latency-per-stage budgets that differ in detail from what I infer during implementation. When you upload it, I'll re-check Phases 12–17 against it before continuing.

## 7. Technology Stack (validated against documentation, not arbitrarily chosen)

| Layer | Technology | Why |
|---|---|---|
| Backend | Node.js + Express.js | Specified in both source documents; team likely has JS experience; large middleware ecosystem for RBAC/rate-limiting |
| Database | MongoDB + Mongoose | Specified in both source documents; flexible schema suits heterogeneous audit/incident records |
| Auth | JWT + bcrypt | Standard, specified; short-TTL tokens fit the fail-safe requirement |
| Frontend | React.js | Specified in both source documents |
| AI services | Python (FastAPI recommended, see §9) | Whisper/RawNet2/mBERT/Presidio/spaCy are Python-native; forcing them into Node via bindings adds risk for no benefit |
| AI models | Faster-Whisper, RawNet2, mBERT + custom head, Presidio, spaCy | Per Chapter 1 §6 |
| Risk Engine | Phase 1 rule-based (mandatory) → Phase 2 XGBoost+SHAP (conditional) | Per Chapter 1 §6.4.5–6.4.6 |
| Containerization | Docker + docker-compose | Not explicitly mandated by either document, but strongly recommended to isolate Python AI services from the Node backend and to make the demo reproducible — **flagged as an open decision, not assumed**, see §21 |

## 8. Architecture Assessment

The layered architecture you proposed (Frontend → API Gateway → Auth/RBAC → Core Backend → Security Services → AI Services → DB) matches Figure 3 in Chapter 1 Final v2.0 and is validated as correct. One refinement: Prompt Inspection and Social-Engineering Detection should be implemented as **one backing service** (both map to the mBERT + head endpoint per the original proposal's own integration addendum), not two separate services, to avoid the naming duplication already flagged and corrected in Chapter 1 §3.1.

## 9. AI Service Architecture — Recommendation: Separate Python Microservices (Option B)

| Criterion | Embedded in Node backend (A) | Separate Python services (B) | Winner |
|---|---|---|---|
| Model library availability | Poor — Whisper/RawNet2/mBERT are Python-native; Node bindings are immature or nonexistent | Native | **B** |
| Performance | Would require child-process spawning anyway, negating any benefit | Direct in-process inference | **B** |
| Maintainability | Mixes two language ecosystems in one codebase | Clean separation; AI team can iterate without touching backend | **B** |
| Development complexity (team of students, mixed skill) | Higher — backend devs would need to debug Python via bindings | Lower — each team owns its language | **B** |
| GPU access | Awkward from Node | Native (CUDA/CPU fallback handled in Python) | **B** |
| API communication | N/A | Internal REST (or gRPC, but REST is simpler for a student team) over localhost/Docker network | **B** |
| Security | Slightly larger attack surface (extra internal network hop) | Mitigated by keeping AI services on an internal-only Docker network, not exposed externally | **B**, with mitigation |
| Debugging | Single process | Independent logs per service, easier to isolate faults | **B** |

**Decision:** three independent Python services — `whisper-service`, `voice-deepfake-service` (RawNet2), `social-engineering-service` (mBERT+head) — each exposing a small internal REST API, called by the Node backend's Security Engine layer. Presidio/spaCy can run either as a fourth Python service or as a library inside a shared `dlp-service` — recommended as one combined `dlp-service` (Presidio + spaCy + regex) since none of the three need model-specific isolation the way the deep-learning models do.

## 10. Database Architecture (MongoDB, proposed collections)

| Collection | Purpose | Key fields | TTL? |
|---|---|---|---|
| `users` | Accounts | email, passwordHash, role | No |
| `roles` | RBAC definitions | name, permissions[] | No |
| `policies` | Admin-configured DLP/risk rules | ruleType, threshold, action | No |
| `tokenMappings` | Reversible redaction map (Section 6.4.4 lifecycle) | tokenId, encryptedValue, createdAt | **Yes — TTL index, mandatory** |
| `incidents` | Risk-scored events for analyst review | riskLevel, sourceType, scores{}, status | No |
| `auditLogs` | Append-only decision log | actorId, action, timestamp, decision | No (append-only, no deletion path in app logic) |
| `evaluationResults` | Data-science measured metrics (EER, F1, WER, etc.) | component, metric, value, datasetVersion, measuredAt | No |

`tokenMappings` TTL is not optional — it is the mechanism that satisfies the "automatic deletion" requirement in Chapter 1 §6.4.4 and this message's constraint #5.

## 11. API Architecture

REST, versioned under `/api/v1/`, JWT bearer auth on every route except `/api/v1/auth/login`. Full per-endpoint contracts are defined during each relevant phase (Phase 4 for the gateway shape; Phases 5–9 for DLP/redaction/risk/policy/audit; Phases 12–14 for the three AI services) rather than all up front, since contract details depend on what each phase actually builds — defining them prematurely risks inventing specifics not grounded in the documentation.

## 12. Frontend Architecture

React, role-aware routing (Employee vs. Analyst vs. Administrator views), a Security Dashboard that explicitly distinguishes **Detected Event / Risk Level / Policy Action / Model Result / Measured Performance** per your instruction, and a hard rule enforced at the component level: any metric without a real measured value renders literally as `"No measured data available"` — never a placeholder number.

## 13–18. Track-Level Responsibilities

| Track | Owns | Depends on |
|---|---|---|
| **Cybersecurity** | Auth, RBAC, JWT, rate limiting, input validation, CORS, security headers, DLP integration into policy, audit logging integrity, threat-model-driven security tests | Backend foundation (Phase 1–2) |
| **AI** | Faster-Whisper, RawNet2, mBERT+head services; per-model API contracts; inference error handling | Data Science (labels/datasets), Backend (integration contract) |
| **Data Science** | Dataset acquisition/licensing, preprocessing, label definition, train/val/test splits, leakage prevention, evaluation metrics, experiment logging | Nothing blocking — can start dataset work in parallel with Phase 0–2 |
| **Backend/CS** | Express app, Mongo models, API gateway, Risk/Policy engines, audit logging plumbing | Phase 0–2 foundation |
| **Frontend/UI** | React app, auth UI, dashboard, role-aware views | Backend auth API (Phase 3) must exist first for real integration, but UI scaffolding can start on Phase 10 in parallel with Phase 4–9 using mocked responses |
| **QA/Integration** | Test plans per phase, security test scenarios (unauthorized access, privilege escalation, invalid JWT, rate-limit behavior, leakage, prompt injection, unauthorized restoration, malformed requests, token abuse), end-to-end workflow validation | Every phase feeds QA; QA does not block earlier phases but blocks phase sign-off |

## 19. Dependencies (cross-phase)

- AI services (12–14) depend on Data Science label/dataset work being at least partially done — **can start in parallel with Phase 0–9**, should not wait until Phase 12.
- Risk Fusion (16) depends on all three AI services (12–14) plus DLP (5) being independently functional first — explicit non-negotiable gate per your "do not integrate until each model works independently" instruction.
- Phase 2 (XGBoost+SHAP, Phase 22) depends on Phase 19 (AI/Data Science Evaluation) producing enough labeled incident data to make a go/no-go call — this is the same open decision already flagged in Chapter 1 §13.
- Browser Extension (21) is explicitly gated on your approval, independent of technical readiness.

## 20. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Missing SRS v2.1 file means some implementation-level specifics are unverified | Medium | Flagged in §0; re-check Phases 12–17 once uploaded |
| mBERT social-engineering classifier trained mostly on text corpora (SMS/Enron/phishing), evaluated on synthetic call transcripts — domain gap | Medium–High | Already documented as a stated limitation in Chapter 1 §6.5; do not let implementation silently overstate accuracy |
| No GPU confirmed available | Medium | RawNet2/Whisper/mBERT should all have a CPU-fallback path validated in Phase 12–14 acceptance criteria, even if slower than the latency target |
| Two-semester timeline vs. 24 phases | Medium | Should-implement/optional phases (21, 22) are explicitly the first to drop if time runs short — this is already built into the phase numbering |
| Team-generated synthetic labeled data (social-engineering, Phase 2 incidents) may end up too small for meaningful evaluation | Medium | Data Science track must report actual corpus size at the end of labeling, not before — no size is assumed in advance |

## 21. Open Decisions

1. **Upload the AI Subsystem Proposal & SRS v2.1 file** — currently missing.
2. Docker/docker-compose vs. plain local processes for running the Python AI services — recommended Docker, not yet confirmed by you.
3. Monorepo (proposed structure below) vs. separate repos per service — recommended monorepo for a student team, not yet confirmed.
4. GPU availability for AI services — unknown, affects Phase 12–14 acceptance criteria (CPU fallback needed either way).
5. All open items already listed in Chapter 1 §13 (dataset versions/sizes, browser-extension final app list, Phase 2 go/no-go, WER measurement scope, Arabic upgrade attempt, supervisor sign-off on STRIDE/testing tool list, numeric risk-level thresholds) remain open and now also block specific phases below (marked per-phase).

## 22. Recommended Implementation Order

Your proposed 24-phase structure is sound and matches the dependency graph in §19. One adjustment: **Data Science dataset work (part of Phase 19's scope) should start informally alongside Phase 0–2**, not wait until Phase 19, since AI services in Phase 12–14 need labeled data ready by the time they're built. I've reflected this as a "can start early" note on the relevant phases below rather than renumbering the whole sequence.

---

# Phase-by-Phase Roadmap

Each phase follows: **Implement → Run → Test → Fix → Verify → Document → Commit → Next Phase.** No phase begins until the previous one's acceptance criteria are met and you've reviewed the Git checkpoint.

---

### PHASE 0 — Repository & Environment Setup
- **Objective:** Establish the monorepo skeleton, tooling, and environment baseline — no business logic yet.
- **Responsible team:** Backend/CS (lead), all teams (setup buy-in)
- **Dependencies:** None
- **Inputs:** This roadmap; your confirmation of monorepo vs. multi-repo (Open Decision #3)
- **Outputs:** Empty-but-runnable repo skeleton; `.gitignore`; `README.md`; linting/formatting config
- **Files to create:** `EASP/` root with `backend/`, `frontend/`, `ai-services/`, `data/`, `docs/`, `tests/`, `docker/`, `README.md`, `.gitignore`
- **APIs:** None yet
- **Database changes:** None
- **AI components:** None yet — placeholder folders only
- **Security components:** `.env.example` with no real secrets, secret-scanning note in README
- **UI components:** None yet
- **Data Science tasks:** Create `data/raw/`, `data/processed/`, `data/evaluation/` with a `.gitkeep` and a `DATASETS.md` stub for Open Decision tracking
- **Tests:** Smoke test — `npm run lint` / `python -m py_compile` succeed on empty scaffolding
- **Acceptance criteria:** Repo clones clean; folder structure matches §Architecture; no secrets committed
- **Estimated complexity:** Low
- **Blockers:** Your confirmation on Open Decisions #2 and #3
- **Git checkpoint:** `phase-00-repo-setup`

---

### PHASE 1 — System Foundation
- **Objective:** Minimal Express app and minimal React app that boot and talk to each other with a health-check endpoint.
- **Responsible team:** Backend/CS, Frontend/UI
- **Dependencies:** Phase 0
- **Files to create:** `backend/src/app.js`, `backend/src/config/`, `frontend/src/App.jsx`, `backend/package.json`, `frontend/package.json`
- **APIs:** `GET /api/v1/health` → `{status:"ok"}`
- **Database changes:** None
- **AI components:** None
- **Security components:** Basic Helmet security headers, CORS config (restricted origin)
- **UI components:** Blank React shell hitting `/health`
- **Data Science tasks:** None (parallel dataset work continues informally)
- **Tests:** Integration test hitting `/health`; frontend renders without console errors
- **Acceptance criteria:** `npm start` on backend and frontend both run locally; health check returns 200 end to end
- **Estimated complexity:** Low
- **Blockers:** None
- **Git checkpoint:** `phase-01-foundation`

---

### PHASE 2 — Database & Core Backend
- **Objective:** MongoDB connection, base Mongoose schemas (`users`, `roles`, `auditLogs` stub), core service-layer folder structure.
- **Responsible team:** Backend/CS
- **Dependencies:** Phase 1
- **Files to create:** `backend/src/config/db.js`, `backend/src/models/User.js`, `backend/src/models/Role.js`, `backend/src/models/AuditLog.js`
- **Database changes:** Creates `users`, `roles`, `auditLogs` collections
- **APIs:** None public yet
- **Security components:** Mongoose schema-level validation; no plaintext password fields
- **Tests:** Unit tests for schema validation (reject malformed user doc)
- **Acceptance criteria:** App connects to MongoDB on boot; schema validation tests pass
- **Estimated complexity:** Low–Medium
- **Blockers:** MongoDB instance availability (local or Atlas — Open Decision, confirm with you)
- **Git checkpoint:** `phase-02-database`

---

### PHASE 3 — Authentication + Authorization + RBAC
- **Objective:** JWT login/registration, bcrypt password hashing, role-based middleware.
- **Responsible team:** Cybersecurity (lead), Backend/CS
- **Dependencies:** Phase 2
- **Files to create:** `backend/src/controllers/authController.js`, `backend/src/middleware/auth.js`, `backend/src/middleware/rbac.js`, `backend/src/routes/authRoutes.js`
- **APIs:** `POST /api/v1/auth/register`, `POST /api/v1/auth/login` → JWT; `GET /api/v1/auth/me` (protected)
- **Database changes:** Seed default roles (Employee, Analyst, Administrator)
- **Security components:** bcrypt salt rounds ≥ 12; short JWT TTL + refresh strategy defined; rate limiting on login route (ties into Phase 4 but minimally stubbed here)
- **Testing:** Valid login, invalid password, expired token, missing token, wrong-role access attempt — each as an explicit test case with expected output
- **Acceptance criteria:** All five test cases above pass; no plaintext password ever logged or stored
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-03-auth-rbac`

---

### PHASE 4 — API Gateway + Security Middleware
- **Objective:** Central request pipeline — rate limiting, input validation, security headers, request logging hook.
- **Responsible team:** Cybersecurity, Backend/CS
- **Dependencies:** Phase 3
- **Files to create:** `backend/src/middleware/rateLimit.js`, `backend/src/middleware/validate.js`, `backend/src/middleware/securityHeaders.js`
- **Security components:** express-rate-limit config, Joi/Zod schema validation on all mutating routes, Helmet finalized, CORS allow-list finalized
- **Testing:** Rate-limit trigger test (Nth request rejected), malformed-payload rejection test, missing-header/CORS rejection test
- **Acceptance criteria:** All requests without valid input fail closed with a clear 4xx, not a 5xx crash
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-04-gateway-middleware`

---

### PHASE 5 — DLP Engine
- **Objective:** Regex + Presidio + spaCy pipeline detecting sensitive-data categories actually defined in Chapter 1 §6.1/§6.4.4 (PII, credentials, structured secrets) — no invented categories.
- **Responsible team:** Cybersecurity (integration), AI/Data Science (Presidio/spaCy pipeline)
- **Dependencies:** Phase 4 (as a callable backend service); can be built in parallel as a standalone Python service starting at Phase 0
- **Files to create:** `ai-services/dlp-service/` (FastAPI app, Presidio config, spaCy pipeline, regex rule set), `backend/src/services/dlpClient.js`
- **APIs:** Internal — `POST /internal/dlp/scan {text}` → `{entities:[...], sensitivityScore}`
- **Database changes:** None yet (redaction map comes in Phase 6)
- **AI components:** Presidio default recognizers + spaCy NER + custom regex for credentials/API keys
- **Data Science tasks:** Acquire Presidio synthetic PII test corpus / ai4privacy sample for evaluation (not training)
- **Testing:** Labeled PII/credential test set → recall/precision/false-positive rate actually measured, not assumed
- **Acceptance criteria:** Detector correctly flags a defined test set of PII/credential examples above an agreed-with-you recall threshold; measured numbers logged to `evaluationResults`, not fabricated
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-05-dlp-engine`

---

### PHASE 6 — Reversible Encrypted Token Mapping
- **Objective:** Implement the full lifecycle from Chapter 1 §6.4.4 / this message's constraint #5.
- **Responsible team:** Cybersecurity (lead), Backend/CS
- **Dependencies:** Phase 5
- **Files to create:** `backend/src/services/redactionService.js`, `backend/src/models/TokenMapping.js`
- **Database changes:** `tokenMappings` collection with **mandatory TTL index**
- **Security components:** AES-256 encryption of the mapping value; access control restricting who can call restoration; TTL/retention config; automatic deletion via TTL index; failure-handling (what happens if restoration is requested after expiry — must fail safely, not silently return the token); concurrent-request isolation test
- **Testing:** Round-trip integrity (redact → restore matches original), TTL expiry test (restoration after expiry fails safely), concurrency test (two simultaneous redactions don't collide), unauthorized-restoration attempt test
- **Acceptance criteria:** All four tests above pass; no original sensitive value is ever persisted outside the encrypted, TTL-bound mapping
- **Estimated complexity:** Medium–High
- **Blockers:** None
- **Git checkpoint:** `phase-06-token-mapping`

---

### PHASE 7 — Rule-Based Risk Engine (Phase 1)
- **Objective:** Deterministic weighted-rule fusion per Chapter 1 §6.4.5. Must function with zero ML dependency.
- **Responsible team:** Cybersecurity, Backend/CS
- **Dependencies:** Phase 5 (DLP score available); voice/NLP scores can be stubbed with mock values until Phase 12–14 exist
- **Files to create:** `backend/src/services/riskEngine.js`, `backend/src/config/riskRules.js`
- **Database changes:** `incidents` collection
- **APIs:** Internal `computeRisk({dlpScore, voiceScore, nlpScore}) → {riskLevel}`
- **Testing:** Combined-incident scenario tests (documented in Chapter 1 §7.5) — e.g., high DLP + high voice-spoof → High risk; all-low → Low risk
- **Acceptance criteria:** Risk Engine produces correct, explainable levels for every documented test scenario using rules alone; numeric thresholds are the ones confirmed with your supervisor per Open Decision (Chapter 1 §13) — until confirmed, thresholds are marked NEEDS CONFIRMATION in code comments, not silently invented
- **Estimated complexity:** Medium
- **Blockers:** Numeric risk thresholds — Open Decision, flagged
- **Git checkpoint:** `phase-07-risk-engine`

---

### PHASE 8 — Policy Engine
- **Objective:** Allow/Redact/Block/Escalate decisioning tied to risk level and role.
- **Responsible team:** Cybersecurity, Backend/CS
- **Dependencies:** Phase 7
- **Files to create:** `backend/src/services/policyEngine.js`, `backend/src/models/Policy.js`
- **Database changes:** `policies` collection (admin-configurable)
- **APIs:** Internal — consumes `riskLevel`, produces `policyAction`
- **Testing:** Each policy action path (allow, redact, block, escalate) tested against a matching risk-level input
- **Acceptance criteria:** Every risk level maps to exactly one deterministic, testable policy action
- **Estimated complexity:** Low–Medium
- **Blockers:** None
- **Git checkpoint:** `phase-08-policy-engine`

---

### PHASE 9 — Audit Logging
- **Objective:** Append-only, tamper-resistant logging of every policy decision.
- **Responsible team:** Cybersecurity, Backend/CS
- **Dependencies:** Phase 8
- **Files to create:** `backend/src/services/auditService.js`
- **Database changes:** Finalize `auditLogs` schema with no update/delete route exposed anywhere in the app layer
- **Testing:** Tamper-attempt test (no API path exists to modify/delete a log entry); audit-event generation test on every policy decision
- **Acceptance criteria:** 100% of Phase 8 decisions produce exactly one audit entry; no mutation endpoint exists
- **Estimated complexity:** Low–Medium
- **Blockers:** None
- **Git checkpoint:** `phase-09-audit-logging`

---

### PHASE 10 — Frontend Foundation + Authentication UI
- **Objective:** Login/registration UI wired to Phase 3's real auth API; role-aware routing shell.
- **Responsible team:** Frontend/UI
- **Dependencies:** Phase 3 (can scaffold earlier with mocks, but must integrate against the real API before sign-off)
- **Files to create:** `frontend/src/pages/Login.jsx`, `frontend/src/pages/Register.jsx`, `frontend/src/services/authApi.js`, `frontend/src/context/AuthContext.jsx`
- **Testing:** Login success/failure UI states; protected-route redirect for unauthenticated users
- **Acceptance criteria:** A real user can register, log in, and reach a role-appropriate landing page against the live backend
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-10-frontend-auth`

---

### PHASE 11 — Security Dashboard
- **Objective:** Build the dashboard shell with the mandated Detected Event / Risk Level / Policy Action / Model Result / Measured Performance distinction, backed by Phase 7–9 data (still with stubbed AI scores at this point).
- **Responsible team:** Frontend/UI, Cybersecurity (data shape review)
- **Dependencies:** Phase 9, Phase 10
- **Files to create:** `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/IncidentCard.jsx`, `frontend/src/components/MetricDisplay.jsx`
- **UI components:** `MetricDisplay` component renders `"No measured data available"` whenever a metric is null/undefined — enforced at the component level, not left to page-author discipline
- **Testing:** Dashboard renders real incidents from Phase 7–9 data; missing-metric case renders the fallback string, not a blank or zero
- **Acceptance criteria:** No fabricated number can appear on screen even if a developer forgets to pass real data — the component itself refuses to render a fake default
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-11-dashboard`

---

### PHASE 12 — Faster-Whisper Service
*(Data Science: dataset/label work for this and Phases 13–14 should already be underway from Phase 0 onward.)*
- **Objective:** Standalone, independently testable speech-to-text microservice.
- **Responsible team:** AI (lead), Data Science (test audio)
- **Dependencies:** None blocking — independent of Phases 1–11
- **Files to create:** `ai-services/whisper-service/main.py`, `Dockerfile`, `requirements.txt`
- **APIs:** `POST /internal/transcribe {audio}` → `{transcript}`
- **AI components:** Faster-Whisper (CTranslate2), CPU-fallback path validated
- **Data Science tasks:** Prepare a small labeled test-audio sample for spot-check evaluation; decide (with you) whether a formal WER measurement is in scope (Open Decision, Chapter 1 §13)
- **Testing:** Transcription spot-check against known test clips; error handling for corrupt/empty audio input
- **Acceptance criteria:** Service runs standalone, returns correct transcript for known test clips, fails gracefully on bad input
- **Estimated complexity:** Medium
- **Blockers:** None
- **Git checkpoint:** `phase-12-whisper-service`

---

### PHASE 13 — RawNet2 Voice Deepfake Service
- **Objective:** Standalone voice-authenticity classifier, audio-only, per constraint #1.
- **Responsible team:** AI (lead), Data Science (ASVspoof data prep)
- **Dependencies:** None blocking — independent of Phases 1–12
- **Files to create:** `ai-services/voice-deepfake-service/main.py`, `Dockerfile`, `requirements.txt`
- **APIs:** `POST /internal/voice-authenticity {audio}` → `{label, confidence}`
- **AI components:** Pretrained RawNet2 checkpoint; optional fine-tuning only if baseline eval on held-out ASVspoof data shows a need and time permits
- **Data Science tasks:** ASVspoof 2019/2021 subset preparation with proper train/dev/eval split; **no dataset size claimed until actually confirmed** (Open Decision, Chapter 1 §13)
- **Testing:** Held-out genuine-vs-spoofed test → EER actually measured and logged to `evaluationResults`
- **Acceptance criteria:** Service runs standalone; measured EER exists (whatever the number is) rather than an assumed figure
- **Estimated complexity:** Medium–High
- **Blockers:** ASVspoof subset finalization (Open Decision)
- **Git checkpoint:** `phase-13-rawnet2-service`

---

### PHASE 14 — mBERT Social-Engineering Classification Pipeline
- **Objective:** Encoder + project-specific classification head, per Chapter 1 §6.4.3 and this message's constraint #3.
- **Responsible team:** AI (lead), Data Science (labeling)
- **Dependencies:** None blocking to start; needs the labeled corpus (SMS/Enron/phishing + synthetic calls) from Data Science before the head can be trained
- **Files to create:** `ai-services/social-engineering-service/main.py`, `model/classification_head.py`, `Dockerfile`, `requirements.txt`
- **APIs:** `POST /internal/social-engineering {transcript}` → `{labels: [...], scores: {...}}`
- **AI components:** Pretrained mBERT encoder (frozen-baseline first) + trained dense/softmax classification head on categories: Urgency, Authority Impersonation, Credential Request, Payment Request, Suspicious
- **Data Science tasks:** Finalize labeled corpus size/class balance (Open Decision, Chapter 1 §13); stratified held-out split with no train/test overlap
- **Testing:** Held-out labeled set → per-label precision/recall/F1 actually measured
- **Acceptance criteria:** Service runs standalone; measured per-label metrics exist and are logged; domain-gap limitation (text-corpus training vs. spoken-call evaluation) explicitly noted in the service's own README, not hidden
- **Estimated complexity:** High
- **Blockers:** Labeled corpus size finalization (Open Decision)
- **Git checkpoint:** `phase-14-mbert-social-engineering`

---

### PHASE 15 — AI Pipeline Integration
- **Objective:** Connect the three independently-working AI services (12–14) to the Node backend's Security Engine layer — first time they're wired together.
- **Responsible team:** Backend/CS, AI
- **Dependencies:** Phases 12, 13, 14 must each individually pass their own acceptance criteria first — **hard gate, not a soft preference**
- **Files to create:** `backend/src/services/aiGatewayClient.js` (internal HTTP client for the three services)
- **APIs:** Backend-internal calls to each service's existing contract — no new AI-facing API surface introduced here
- **Testing:** End-to-end call: audio in → transcript + voice label + NLP labels out, correctly routed
- **Acceptance criteria:** All three services reachable from the backend with correct error handling on timeout/service-down (fail-safe → manual review, not fail-open, per Chapter 1 §7.4)
- **Estimated complexity:** Medium
- **Blockers:** Phases 12–14 completion
- **Git checkpoint:** `phase-15-ai-integration`

---

### PHASE 16 — Unified Risk Fusion
- **Objective:** Replace Phase 7's stubbed voice/NLP scores with real Phase 15 outputs.
- **Responsible team:** Backend/CS, Cybersecurity
- **Dependencies:** Phase 15
- **Files to modify:** `backend/src/services/riskEngine.js` (remove stubs, wire real inputs)
- **Testing:** Re-run Phase 7's combined-incident scenarios, now with real model outputs instead of mocks
- **Acceptance criteria:** Same scenarios pass with live data as passed with mocked data in Phase 7
- **Estimated complexity:** Medium
- **Blockers:** Phase 15
- **Git checkpoint:** `phase-16-risk-fusion`

---

### PHASE 17 — End-to-End Security Workflow
- **Objective:** Full pipeline live: prompt/voice in → DLP/AI analysis → risk fusion → policy decision → audit log → dashboard update.
- **Responsible team:** All teams (integration milestone)
- **Dependencies:** Phases 6, 8, 9, 16
- **Testing:** The four demo scenarios from Chapter 1 §5.3 (benign call, spoofed-voice call, social-engineering call, DLP leak attempt) plus one combined-incident scenario, run end to end for real
- **Acceptance criteria:** All five scenarios produce correct, traceable outcomes visible on the dashboard with real (not mocked) data throughout
- **Estimated complexity:** High (integration risk concentrated here)
- **Blockers:** All prior phases
- **Git checkpoint:** `phase-17-e2e-workflow`

---

### PHASE 18 — Cybersecurity Testing
- **Objective:** Formal security test pass across the whole system.
- **Responsible team:** Cybersecurity, QA
- **Dependencies:** Phase 17
- **Testing:** Unauthorized access, privilege escalation, invalid/expired JWT, brute-force/rate-limit behavior, sensitive-data leakage, prompt-injection test cases (OWASP-LLM01-aligned), unauthorized restoration attempt, malformed API requests, session/token abuse — each with documented input, expected output, and actual (executed) result
- **Acceptance criteria:** Every test case above has a real pass/fail result recorded — none marked "assumed passing"
- **Estimated complexity:** Medium–High
- **Blockers:** Phase 17
- **Git checkpoint:** `phase-18-security-testing`

---

### PHASE 19 — AI/Data Science Evaluation
- **Objective:** Consolidated, formal measurement pass across all AI components — supersedes ad hoc spot-checks from Phases 12–14 with final numbers used in the defense.
- **Responsible team:** Data Science, AI
- **Dependencies:** Phase 15 minimum; ideally Phase 17
- **Testing:** Final EER (RawNet2), per-label precision/recall/F1 (mBERT+head), DLP recall/precision/FPR, optional WER (Whisper) — all logged to `evaluationResults` with dataset version and timestamp
- **Acceptance criteria:** Every baseline AI component has one final, dated, reproducible measured result — no number appears in the eventual defense that isn't traceable to this phase's output
- **Estimated complexity:** Medium
- **Blockers:** Underlying dataset/label finalization (Open Decisions)
- **Git checkpoint:** `phase-19-ai-evaluation`

---

### PHASE 20 — Performance & Latency Testing
- **Objective:** Measure actual end-to-end latency against the ≤3-second target.
- **Responsible team:** Backend/CS, QA
- **Dependencies:** Phase 17
- **Testing:** Wall-clock timing from request capture to policy decision, per pipeline stage and end-to-end, under demonstration load
- **Acceptance criteria:** A real measured latency number exists and is recorded, whether or not it meets the ≤3s target — if it doesn't meet target, that is reported honestly, not hidden
- **Estimated complexity:** Low–Medium
- **Blockers:** Phase 17
- **Git checkpoint:** `phase-20-performance-testing`

---

### PHASE 21 — Browser Extension (ONLY IF APPROVED)
- **Objective:** Prompt capture limited to explicitly supported AI web applications (final list: Open Decision, Chapter 1 §13).
- **Responsible team:** Frontend/UI, Cybersecurity
- **Dependencies:** Phase 6 (redaction), your explicit go-ahead
- **Blockers:** Your approval + final supported-app list — **do not start without both**
- **Git checkpoint:** `phase-21-browser-extension` (only created if this phase runs)

---

### PHASE 22 — XGBoost + SHAP (ONLY IF DATA IS SUFFICIENT)
- **Objective:** Phase 2 conditional risk-fusion enhancement, per Chapter 1 §6.4.6.
- **Responsible team:** Data Science, AI
- **Dependencies:** Phase 19 must show sufficient labeled incident data exists — **go/no-go decision made from real data, not assumed in advance**
- **Blockers:** Phase 19 outcome + your go/no-go confirmation
- **Git checkpoint:** `phase-22-xgboost-shap` (only created if this phase runs)

---

### PHASE 23 — Final Integration
- **Objective:** Merge whichever of Phases 21–22 actually ran back into the main end-to-end workflow; regression-test Phase 17's five scenarios once more.
- **Responsible team:** All teams
- **Dependencies:** Phases 17–20, plus 21/22 if they ran
- **Acceptance criteria:** Full system, in its final approved scope, passes the same five scenarios from Phase 17 with no regression
- **Estimated complexity:** Medium
- **Git checkpoint:** `phase-23-final-integration`

---

### PHASE 24 — Final Demonstration & Documentation
- **Objective:** Defense-ready state — demo script rehearsed, all documentation (architecture, API, database, AI, cybersecurity, testing) synchronized with what was actually built.
- **Responsible team:** All teams
- **Dependencies:** Phase 23
- **Outputs:** Updated `docs/` reflecting real implementation (not the aspirational Chapter 1 baseline where the two diverge); final measured-metrics summary; rehearsed demo script
- **Acceptance criteria:** Every claim in the documentation is traceable to either (a) working code or (b) an explicitly labeled Future Work item — no gap between what's written and what's built
- **Git checkpoint:** `phase-24-final-demo`

---

## What Happens Next

This is the complete audit and roadmap. **I have not written any implementation code.** Please review and confirm:

1. The Open Decisions in §21 (especially #1 — uploading the SRS v2.1 file — and #2/#3, Docker and monorepo)
2. Whether the phase order and team assignments above match your expectations
3. Which phase to start with (Phase 0 is the natural starting point)

Once you approve, we proceed one phase at a time through Antigravity, following Implement → Run → Test → Fix → Verify → Document → Commit before moving on.
