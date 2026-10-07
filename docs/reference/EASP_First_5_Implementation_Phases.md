# EASP — First 5 Implementation Phases

**Enterprise AI Security Platform — Practical Implementation Guide (Phase 0–4)**
Scope lock: Voice-only deepfake detection. No image/video, no PBX production integration, no Threat Intelligence module, no XGBoost/SHAP, no federated learning, no autoencoder anomaly detection. Phase 1 Risk Engine = rule-based weighted fusion only.

---

## 1. Overall Roadmap

```
Phase 0                 Phase 1                Phase 2                  Phase 3                    Phase 4
Repo & Dev Env    →     Auth + JWT + RBAC  →    API Gateway +      →     DLP Engine +           →   AI Dataset Prep +
                                                 Backend Security         Reversible Redaction        AI Service Foundations
                                                 Foundation

(No auth,               (No DLP,                (No AI                  (Regex + Presidio +         (RawNet2 / Faster-Whisper /
no AI,                  no AI models             inference               spaCy + AES-256             mBERT scaffolding,
no DLP yet)              yet)                     yet)                    reversible token map)        dataset documentation only)
```

Data Science work (dataset acquisition, cleaning, label definitions) may start in **parallel from Phase 0**, run by the 4 AI members, so that by Phase 4 the datasets are ready for the AI team to build interfaces around.

Architecture reference for all 5 phases:

```
Frontend (React)
      ↓
Node.js + Express Backend
      ↓
Security / Processing Layer
      ↓
Python AI Services (FastAPI)
      ↓
MongoDB
```

**Stop condition:** After Phase 4, the team validates and does not proceed to Phase 5 (Risk Engine fusion + full pipeline integration) until this document is followed up with a Phase 5+ plan.

---

## 2. Team Responsibility Matrix

| Member  | Track           | Phase 0                                   | Phase 1                              | Phase 2                                    | Phase 3                                  | Phase 4                                       |
|---------|-----------------|--------------------------------------------|----------------------------------------|-----------------------------------------------|---------------------------------------------|--------------------------------------------------|
| Cyber 1 | Cybersecurity   | Repo structure, `.env.example`, README     | User model, password hashing            | API Gateway routing, security headers          | Regex + Presidio detection rules             | Security review of AI service auth/contracts       |
| Cyber 2 | Cybersecurity   | Docker Compose, health endpoints            | JWT generation/validation                | Rate limiting, CORS config                     | AES-256 reversible token mapping (encrypt)   | Security review of dataset access controls          |
| Cyber 3 | Cybersecurity   | Git branching strategy, CI skeleton         | Login endpoint, RBAC middleware         | Input validation middleware                    | TTL/expiration + restore mechanism           | Threat-model review of Phase 5 risk engine inputs   |
| Cyber 4 | Cybersecurity   | Environment variable conventions            | Security tests (invalid/expired/modified JWT) | Centralized error handling, secure config     | Security tests for DLP (unauthorized restore, expired map, malformed input) | Security tests for AI service endpoints (auth, input validation) |
| AI 1    | AI              | Python AI-service skeleton (FastAPI)        | (Supports Cyber on RBAC role definitions for AI-facing endpoints) | Backend→AI service communication contract (schemas) | (Supports spaCy/Presidio rule tuning)     | RawNet2 environment + pretrained checkpoint integration |
| AI 2    | AI              | AI service `/health` endpoint                | —                                        | Request/response contract for AI microservices | —                                            | Faster-Whisper environment + transcription API contract |
| AI 3    | AI              | Dataset workspace setup (folders, `.gitignore` for raw data) | Dataset acquisition starts (ASVspoof, WaveFake) | Dataset cleaning continues                     | Labeling continues (credential/PII test data) | mBERT pretrained encoder + classification-head design |
| AI 4    | AI              | Experiment tracking tool setup (e.g. local MLflow) | Label definition drafting            | Train/validation/test split design             | Data leakage prevention checks               | Dataset documentation (all 7+ required fields per dataset) + domain-gap note |
| CS 1    | CS/Backend      | Node.js + Express skeleton, monorepo wiring | User routes, DB schema (Mongo)          | API Gateway implementation, routing layer      | Backend endpoints for DLP redact/restore     | Backend↔AI service HTTP client + error handling      |
| CS 2    | CS/Backend      | React frontend skeleton, MongoDB container  | Frontend login form (wired to JWT)      | Frontend integration of gateway error responses | Frontend hooks for redaction preview/testing | Backend service registry for AI microservices        |

---

## 3. Phase 0 — Repository & Development Environment

### Phase Objective
Stand up a working, empty-but-runnable skeleton: monorepo, backend, frontend, AI service, database, and Docker Compose — with nothing beyond health checks.

### Why This Phase Exists
Every later phase assumes the team can run the whole stack locally with one command and that Git history starts clean. Skipping this phase causes 10 people to diverge on tooling, folder layout, and environment variables within a week.

### Dependencies
None. This is the starting point.

### Deliverables
- `/backend` — Express app with a single `GET /health` route
- `/frontend` — React app with a placeholder home page
- `/ai-service` — FastAPI app with a single `GET /health` route
- `docker-compose.yml` — backend, frontend, ai-service, MongoDB
- `.env.example` for each service
- `README.md` with setup instructions
- `.gitignore` (node_modules, `__pycache__`, `.env`, datasets/raw)
- Git branching convention documented (e.g. `main`, `dev`, `feature/*`)

### Cybersecurity Tasks (Cyber 1–4)
- Cyber 1: Create repo skeleton folders, write `.env.example` files, draft README setup section.
- Cyber 2: Write `docker-compose.yml` wiring all 4 services + volumes; verify `docker compose up` boots cleanly.
- Cyber 3: Define Git branching strategy and PR template; set up a CI skeleton (lint + build, no tests yet).
- Cyber 4: Document required environment variables per service and where secrets must never be committed.

### AI Tasks (AI 1–4)
- AI 1: Build the FastAPI skeleton with `GET /health` returning `{"status": "ok"}`.
- AI 2: Add the `/health` route's Docker packaging (Dockerfile for `ai-service`).
- AI 3: Create the dataset workspace: `/data/raw`, `/data/processed`, `/data/labels` folders, with `/data/raw` git-ignored.
- AI 4: Set up a lightweight experiment-tracking convention (folder-based run logs or local MLflow), documented in `/ai-service/README.md`.

### CS/Backend Tasks (CS 1–2)
- CS 1: Build the Express skeleton with `GET /health`, wire monorepo scripts (`npm run dev` at root starts backend + frontend).
- CS 2: Build the React skeleton (placeholder landing page) and the MongoDB container config in Compose.

### Data Science Tasks
- AI 3 owns dataset workspace setup and will begin dataset acquisition scouting in parallel from Phase 0 (no downloads committed yet — just identifying sources: ASVspoof, WaveFake, SMS Spam Collection, Enron, phishing corpora).
- AI 4 owns experiment-tracking setup, which will be used starting Phase 4 for baseline evaluation runs.

### Git Structure
- Initial commit: empty skeleton with folder structure only.
- Second commit: Docker Compose + health endpoints working end-to-end.
- Branch convention: `feature/phase0-<short-desc>`, merged into `dev` via PR, `dev` merged into `main` at phase completion.

### Testing
- `docker compose up` boots all 4 containers without errors.
- `curl http://localhost:<backend-port>/health` returns 200.
- `curl http://localhost:<ai-service-port>/health` returns 200.
- Frontend loads in browser without console errors.

### Acceptance Criteria
- All 4 services start via one `docker compose up` command.
- All health endpoints return 200.
- README allows a new team member to get the stack running in under 15 minutes, tested by having someone who did not write it follow the steps.
- No secrets committed to Git (manually verified).

### Common Mistakes
- Committing `.env` files with real values instead of `.env.example`.
- Hardcoding ports/hostnames instead of using environment variables, which breaks Docker networking.
- Skipping the dataset `.gitignore` and later accidentally committing large raw audio files.
- Treating this phase as "optional" and rushing to Phase 1 — inconsistent environments compound quickly across 10 people.

### Documentation
- README: how to run the stack, folder layout, environment variables, branching convention.
- `/ai-service/README.md`: how experiment tracking is organized.

**A. BUILD:** Backend/frontend/AI-service skeletons, Docker Compose, `.env.example` files, README, `.gitignore`, dataset workspace folders.
**B. TEST:** `docker compose up`; curl both health endpoints; open frontend in browser.
**C. VERIFY:** All containers show "healthy"/running state; health endpoints return `200 {"status":"ok"}`; no build errors in logs.
**D. COMMIT:** Tag as `phase0-complete` after all acceptance criteria pass.
**E. DONE:** One-command stack boot, both health checks green, README validated by a teammate who wasn't the author.

---

## 4. Phase 1 — Authentication + JWT + RBAC

### Phase Objective
Implement user registration/login, password hashing, JWT issuance/validation, and a basic role-based access control (RBAC) foundation. No DLP, no AI models yet.

### Why This Phase Exists
Every subsequent phase (DLP endpoints, AI service calls, dashboards) needs to know *who* is calling and *what they're allowed to do*. Authentication and RBAC are the foundation every later security control is layered on top of.

### Dependencies
- Phase 0 complete: backend, MongoDB, and Docker Compose running.

### Deliverables
- `User` Mongoose model (email, hashed password, role, timestamps).
- `POST /auth/register` (if required by scope) and `POST /auth/login`.
- JWT issuance on login; JWT validation middleware.
- Role field with at least two roles defined (e.g. `admin`, `employee`).
- RBAC middleware that restricts a sample protected route by role.
- Security test suite covering the cases below.

### Cybersecurity Tasks (Cyber 1–4)
- Cyber 1: Design the `User` schema; implement password hashing (bcrypt/argon2) on registration.
- Cyber 2: Implement JWT generation on login (short-lived access token; document expiration policy) and JWT validation middleware.
- Cyber 3: Implement the login endpoint and RBAC middleware (role-checking decorator/function used on protected routes); define initial roles.
- Cyber 4: Write and run the security test suite: invalid credentials, expired JWT, modified/tampered JWT, unauthorized endpoint access, privilege escalation attempts (e.g. an `employee` role hitting an `admin`-only route).

### AI Tasks (AI 1–4)
- AI 1: Review and confirm which roles AI-facing endpoints will eventually require (input only — no AI code this phase).
- AI 2, AI 3, AI 4: No backend tasks this phase — continue Phase 0's parallel dataset acquisition work (see Data Science Tasks).

### CS/Backend Tasks (CS 1–2)
- CS 1: Wire the `User` model and auth routes into the Express app; connect to MongoDB.
- CS 2: Build the frontend login form and wire it to `POST /auth/login`, storing the JWT (in memory or httpOnly cookie per the team's chosen approach) and attaching it to subsequent requests.

### Data Science Tasks
- AI 3 continues sourcing ASVspoof and WaveFake (audio deepfake datasets) — download and initial folder placement in `/data/raw`, not yet processed.
- AI 4 continues drafting label definitions (what counts as "spoof" vs "bona fide" for voice; what counts as "phishing" vs "benign" for text) so labeling can start cleanly in Phase 4.

### Git Structure
- Commits scoped per task: `feat(auth): user model + password hashing`, `feat(auth): jwt issuance and validation`, `feat(auth): rbac middleware`, `test(auth): security test suite`.
- Merge to `dev` only after the full security test suite passes.

### Testing
- Register/login with valid credentials succeeds and returns a valid JWT.
- Login with invalid credentials fails with 401, no user enumeration in the error message.
- Accessing a protected route with no token returns 401.
- Accessing a protected route with an expired token returns 401.
- Accessing a protected route with a tampered token (changed payload/signature) returns 401.
- A lower-privileged role attempting an admin-only route returns 403.

### Acceptance Criteria
- All security tests above pass consistently.
- Passwords are never stored or logged in plaintext (manually verified in DB and logs).
- JWT secret is read from environment variables, never hardcoded.

### Common Mistakes
- Storing JWTs in `localStorage` without understanding the XSS trade-off (document the team's chosen approach and why).
- Returning different error messages for "user not found" vs "wrong password" (enables user enumeration).
- Forgetting to check role on the *backend* route and only hiding UI elements on the frontend — RBAC must be enforced server-side.
- Using long-lived JWTs with no expiration.

### Documentation
- Document the roles defined and what each is allowed to access.
- Document JWT expiration policy and refresh strategy (or explicitly note refresh is deferred to a later phase).

**A. BUILD:** User model, register/login routes, JWT issuance/validation, RBAC middleware, frontend login form.
**B. TEST:** Run the 6 security test cases listed above (automated, e.g. Jest/Supertest).
**C. VERIFY:** All 6 test cases pass; manual check that passwords are hashed in MongoDB, not plaintext.
**D. COMMIT:** Tag as `phase1-complete` once all tests pass on `dev`.
**E. DONE:** Login issues a valid JWT, protected routes correctly enforce role checks, and all 5 attack-style test cases (expired/tampered/unauthorized/escalation/invalid-creds) fail safely.

---

## 5. Phase 2 — API Gateway + Backend Security Foundation

### Phase Objective
Build the gateway layer in front of the backend: routing, rate limiting, input validation, CORS, security headers, centralized error handling, and the communication contract to the (not-yet-implemented) AI services. No actual AI inference yet.

### Why This Phase Exists
Before any AI model or DLP logic runs, the request path must already be hardened: throttled, validated, and observable. This phase also defines the exact shape of the request/response contract the AI microservices will implement in Phase 4, so both sides can build against a shared interface instead of guessing.

### Dependencies
- Phase 1 complete: authenticated requests carry a valid JWT and role.

### Deliverables
- Gateway routing layer (can be the Express app itself, organized as a gateway module).
- Rate limiting middleware (e.g. per-IP and per-user limits).
- Input validation middleware (schema-based, e.g. Joi/Zod) applied to all routes.
- CORS configuration restricted to known origins.
- Security headers middleware (e.g. Helmet-equivalent: CSP, X-Content-Type-Options, X-Frame-Options).
- Centralized error handler that never leaks stack traces to clients.
- A documented request/response JSON contract for backend → AI service calls (schema only, no live call yet).
- Secure configuration loading (all secrets via env vars, validated at startup).

### Cybersecurity Tasks (Cyber 1–4)
- Cyber 1: Implement the API Gateway routing foundation and security headers middleware.
- Cyber 2: Implement rate limiting (per-IP and per-authenticated-user) and CORS configuration.
- Cyber 3: Implement input validation middleware (schema-based) applied consistently across existing routes.
- Cyber 4: Implement centralized error handling; write tests confirming no stack traces or internal details leak in error responses.

### AI Tasks (AI 1–4)
- AI 1: Co-author the backend→AI service request/response contract with CS 1 (field names, types, expected latency budget note — target ≤3s, not a measured result).
- AI 2, AI 3, AI 4: Continue Phase 4 preparation work — dataset cleaning and split design (see Data Science Tasks).

### CS/Backend Tasks (CS 1–2)
- CS 1: Implement the API Gateway routing layer and the backend→AI service communication foundation (an HTTP client wrapper, unused/stubbed until Phase 4, following the contract co-authored with AI 1).
- CS 2: Update the frontend to handle the new centralized error response format gracefully (toast/alert on validation errors, rate-limit errors, etc.).

### Data Science Tasks
- AI 3 continues dataset cleaning on ASVspoof/WaveFake samples acquired in Phase 1 (removing corrupted files, normalizing audio format/sample rate) — no model training yet.
- AI 4 finalizes the train/validation/test split design (e.g. 70/15/15) and documents the rule that splits must be fixed **before** any preprocessing that could leak information across splits (e.g. normalization statistics computed only on the train set).

### Git Structure
- Commits scoped per middleware: `feat(gateway): rate limiting`, `feat(gateway): input validation`, `feat(gateway): security headers`, `feat(gateway): centralized error handling`, `docs(contract): backend-ai-service schema`.

### Testing
- Rate limiting: exceeding the configured threshold returns 429.
- Input validation: malformed request bodies are rejected with a clear 400, not a 500.
- CORS: requests from a non-allowlisted origin are blocked.
- Security headers: present in all responses (verified via curl `-I` or a header-checking test).
- Error handling: forcing an internal error (e.g. a thrown exception in a test route) returns a generic message, not a stack trace.

### Acceptance Criteria
- All middleware above is active on every route, not just new ones.
- No response, under any error condition, leaks internal file paths, stack traces, or library versions.
- The backend→AI service contract is written down and reviewed by at least one AI-track member and one CS-track member.

### Common Mistakes
- Applying rate limiting only to some routes and forgetting auth routes (a common brute-force gap).
- Over-permissive CORS (`*`) left in "temporarily" and forgotten.
- Validating input on the frontend only, skipping backend validation.
- Designing the AI service contract without agreeing on it with the AI team first, causing rework in Phase 4.

### Documentation
- Document the rate-limit thresholds and rationale.
- Document the backend↔AI service contract (this becomes the reference for Phase 4 implementation).
- Document the security headers applied and why.

**A. BUILD:** Rate limiting, input validation, CORS, security headers, centralized error handler, backend↔AI-service contract doc, stubbed HTTP client.
**B. TEST:** Automated tests for rate-limit 429, validation 400s, CORS rejection, header presence, generic error responses.
**C. VERIFY:** All tests pass; manual curl check of headers and error format; contract doc reviewed by both tracks.
**D. COMMIT:** Tag as `phase2-complete`.
**E. DONE:** Gateway hardens every route uniformly, and the AI service contract is signed off by both AI and CS leads before Phase 4 begins.

---

## 6. Phase 3 — DLP Engine + Reversible Redaction

### Phase Objective
Build the sensitive-data detection pipeline (regex + Presidio + spaCy) and a reversible encrypted token mapping mechanism using AES-256, with TTL/expiration and a restore mechanism.

### Why This Phase Exists
This is the core DLP control of EASP: detect PII/credentials in text and replace them with reversible tokens so downstream processing (e.g. an AI prompt) never sees raw sensitive data, while still allowing an authorized restore for legitimate workflows.

### Dependencies
- Phase 2 complete: input validation and gateway hardening in place, so DLP endpoints inherit the same protections.

### Deliverables
- Regex-based detector module for common patterns (credentials, API keys, etc.).
- Presidio + spaCy integration for PII detection (names, emails, phone numbers, etc.).
- A unified detection interface combining regex + Presidio/spaCy results.
- Reversible encrypted token mapping using AES-256 (explicitly *not* called "tokenization" in any doc or code comment).
- TTL/expiration logic on the token map.
- Restore endpoint that reverses a token back to original value, gated by authorization.
- Secure deletion of expired mappings.

### Cybersecurity Tasks (Cyber 1–4)
- Cyber 1: Implement the regex detector module and integrate Presidio + spaCy for PII/credential detection.
- Cyber 2: Implement the reversible encrypted token mapping using AES-256 — encryption of detected values into a mapping store.
- Cyber 3: Implement TTL/expiration logic and the restore mechanism (decrypt-and-return, gated by role/authorization from Phase 1 RBAC).
- Cyber 4: Write and run the DLP security test suite (below); implement secure deletion of expired mappings.

### AI Tasks (AI 1–4)
- AI 1: Support tuning of spaCy/Presidio recognizers with domain-specific patterns relevant to the project's scope (e.g. common corporate-credential formats used in test data).
- AI 2, AI 3, AI 4: Continue Phase 4 preparation — labeling work (see Data Science Tasks).

### CS/Backend Tasks (CS 1–2)
- CS 1: Build backend endpoints for redact (`POST /dlp/redact`) and restore (`POST /dlp/restore`), wired to the DLP engine and gated by RBAC.
- CS 2: Build a minimal frontend page to submit sample text, view the redacted output, and (if authorized) trigger a restore — useful for team testing/demo.

### Data Science Tasks
- AI 3 continues labeling: for the DLP-relevant test datasets (synthetic PII/credential samples, SMS Spam Collection, Enron for phishing-style text), assign labels consistent with AI 4's Phase 1 label definitions.
- AI 4 documents data leakage prevention checks specific to this phase's test data (e.g. ensuring synthetic PII test samples used to validate the DLP engine don't overlap with any later model-training splits).

### Git Structure
- Commits: `feat(dlp): regex detector`, `feat(dlp): presidio-spacy integration`, `feat(dlp): aes256-reversible-token-mapping`, `feat(dlp): ttl-and-restore`, `test(dlp): security suite`.

### Testing
- PII detection: known PII samples (email, phone, name) are correctly flagged.
- Credential detection: known credential-shaped strings (API-key-like patterns) are correctly flagged.
- Redaction: flagged spans are replaced with tokens, original text is never returned unredacted from `/dlp/redact`.
- Restoration: an authorized restore call correctly returns the original value.
- Unauthorized restoration: a restore call from a role without permission is rejected (403).
- Expired token map: a restore call after TTL expiration fails safely (fail-closed, not fail-open).
- Malformed input: non-text or oversized input is rejected with a clear error, not a crash.
- False positives: a small benign-text sample set is checked to confirm it does not over-flag common non-sensitive content (document the rate, do not fabricate a precision number).

### Acceptance Criteria
- All 8 test cases above pass.
- No plaintext sensitive value is ever persisted outside the AES-256-encrypted mapping store.
- Restore is fail-closed by default (any ambiguity or error results in denial, not disclosure).
- Documentation consistently uses "reversible encrypted token mapping using AES-256" — never "AES-256 tokenization."

### Common Mistakes
- Logging the original sensitive value anywhere (application logs, error messages, debug output) before or during redaction.
- Implementing restore without an authorization check, treating "possession of the token" as sufficient.
- Letting expired mappings linger in the database instead of actively deleting them.
- Conflating "tokenization" (a distinct, non-reversible-by-design industry term in some contexts) with this project's reversible encrypted mapping — keep the wording precise in all docs.

### Documentation
- Document the detection pipeline (regex → Presidio/spaCy → unified result).
- Document the AES-256 reversible token mapping design, TTL policy, and restore authorization rules.
- Document the false-positive review process without fabricating a specific rate.

**A. BUILD:** Regex detector, Presidio/spaCy integration, AES-256 reversible token mapping, TTL/expiration, restore endpoint, secure deletion.
**B. TEST:** Run the 8 DLP test cases (automated where possible; manual review for false-positive spot-check).
**C. VERIFY:** All 8 pass; manual check that no sensitive value appears in logs; restore is fail-closed on expiry/unauthorized attempts.
**D. COMMIT:** Tag as `phase3-complete`.
**E. DONE:** Redaction and restore work end-to-end through the RBAC-gated endpoints, with TTL enforcement and no plaintext leakage anywhere in logs or storage.

---

## 7. Phase 4 — AI Dataset Preparation + AI Service Foundations

### Phase Objective
Prepare AI service scaffolding (RawNet2, Faster-Whisper, mBERT) as pretrained-first baselines with defined input/output contracts, and formally document all datasets. No training, no fusion, no Phase 5 risk engine work yet.

### Why This Phase Exists
Before any model is trained or fused into a risk score, the team needs working inference interfaces around pretrained baselines and a rigorous, honestly-documented dataset foundation — this prevents the common failure mode of building a risk engine on top of undocumented or leaky data.

### Dependencies
- Phase 2's backend↔AI service contract (defines the interface these services must expose).
- Phase 0's AI service skeleton (FastAPI app to extend).

### Deliverables
- RawNet2 environment + pretrained checkpoint integration + inference interface (input: audio file/stream; output: spoof-probability score) matching the Phase 2 contract.
- Faster-Whisper environment + inference interface (input: audio; output: transcript text) matching the Phase 2 contract.
- mBERT pretrained encoder loaded, with a designed (not yet trained, or trained only as a smoke test) classification head for social-engineering detection, and explicit label definitions.
- Dataset documentation for every dataset in use (ASVspoof, WaveFake, SMS Spam Collection, Enron, relevant phishing corpora, synthetic scripted call dialogues, PII datasets), each including: name, source, purpose, data type, labels, intended component, train/validation/test usage, limitations, license/usage constraints.
- A written note on the known domain gap between text-based phishing/social-engineering datasets and real spoken social-engineering conversations.

### Cybersecurity Tasks (Cyber 1–4)
- Cyber 1: Review AI service endpoint authentication (ensure AI microservices are not publicly reachable without the backend's service-to-service credential).
- Cyber 2: Review dataset access controls — raw datasets containing any real (non-synthetic) data must not be world-readable in the repo or shared storage.
- Cyber 3: Threat-model the future risk-engine inputs (what happens if a downstream AI service returns malformed or adversarial output) — documentation only this phase, no fusion logic built.
- Cyber 4: Write and run security tests for the new AI service endpoints (auth required, input validation on audio/text payloads, oversized-file rejection).

### AI Tasks (AI 1–4)
- AI 1: Set up the RawNet2 environment, integrate a pretrained checkpoint, and build the inference interface with the input/output contract matching Phase 2's spec.
- AI 2: Set up the Faster-Whisper environment and build the transcription API contract (input/output interface) matching Phase 2's spec.
- AI 3: Load the mBERT pretrained encoder and design the classification-head architecture (layer sizes, output classes) for social-engineering detection; define labels precisely (e.g. what qualifies as "social-engineering indicator" vs. benign).
- AI 4: Write the full dataset documentation for every dataset listed in the deliverables, and the domain-gap note.

### CS/Backend Tasks (CS 1–2)
- CS 1: Implement the backend HTTP client calls to the new AI service endpoints (RawNet2, Faster-Whisper) per the Phase 2 contract — this phase only wires the calls, does not yet fuse results into a risk score.
- CS 2: Build a minimal internal test page/route to submit a sample audio file and view the RawNet2 score + Whisper transcript side by side, for team QA during this phase.

### Data Science Tasks
- AI 1 & AI 3 own dataset acquisition finalization for their respective components (voice datasets for AI 1's RawNet2 work; text/social-engineering datasets for AI 3's mBERT work).
- AI 3 & AI 4 own preprocessing and labeling completion, applying the label definitions from Phase 1.
- AI 4 owns the train/validation/test split execution (using the design finalized in Phase 2), and the evaluation plan (which metrics will be reported later, without fabricating numbers now).
- AI 4 owns data leakage prevention verification: confirming no sample appears in more than one split, and that any preprocessing statistics were computed only on the training portion.

### Git Structure
- Commits: `feat(ai): rawnet2-inference-interface`, `feat(ai): whisper-transcription-interface`, `feat(ai): mbert-classification-head-design`, `docs(data): dataset-documentation`, `docs(data): domain-gap-note`, `feat(backend): ai-service-client-wiring`.
- Dataset documentation lives in `/ai-service/docs/datasets/` as one file per dataset.

### Testing
- RawNet2 interface: submitting a known-format audio sample returns a score in the expected range/shape, without error.
- Faster-Whisper interface: submitting a known-format audio sample returns a non-empty transcript string.
- mBERT: encoder loads successfully and the classification head produces output of the expected shape on a smoke-test input (not evaluated for accuracy yet — that belongs to a later phase).
- AI service endpoints reject oversized files and non-audio/non-text payloads with a clear error.
- Dataset documentation completeness: every required field present for every dataset (checked against the 8-field checklist above).

### Acceptance Criteria
- All three AI service interfaces (RawNet2, Faster-Whisper, mBERT) are callable end-to-end from the backend and return correctly shaped output.
- No performance, accuracy, or latency numbers are recorded anywhere as if measured — the ≤3s figure remains explicitly labeled as a target only.
- Every dataset has a complete documentation file with all required fields, including honest limitations and license constraints.
- Train/validation/test splits are finalized and a data-leakage check has been performed and documented.
- The domain-gap note exists and is reviewed by at least one AI-track member who did not write it.

### Common Mistakes
- Reporting a specific accuracy/latency number "to fill in the section" — this must never be fabricated; write "not yet measured" instead.
- Treating mBERT as if it already understands social engineering out of the box — it needs the project-specific classification head and labeled training data, which only begins here, not finishes here.
- Computing preprocessing statistics (e.g. normalization) across the full dataset before splitting, leaking test-set information into training.
- Skipping the domain-gap documentation because it's "just a caveat" — it directly protects the project's credibility during defense by pre-empting an examiner's question.
- Starting Phase 5 fusion logic early because "it's almost the same work" — it isn't; fusion depends on all four Phase 4 interfaces being stable first.

### Documentation
- One file per dataset with all 8 required fields (name, source, purpose, data type, labels, intended component, train/val/test usage, limitations/license).
- The domain-gap note (text-based social-engineering data vs. real spoken conversations).
- Input/output contract documentation for each of the three AI service interfaces.
- A short note confirming Phase 2 vs Phase 4 conventions are consistent (schema fields didn't drift during implementation).

**A. BUILD:** RawNet2/Whisper/mBERT scaffolding and interfaces, backend wiring to AI services, dataset documentation set, domain-gap note.
**B. TEST:** Smoke tests on all 3 AI interfaces; endpoint security tests; dataset documentation completeness check; leakage check.
**C. VERIFY:** All smoke tests pass with correctly shaped (not necessarily accurate) output; every dataset doc has all 8 fields; leakage check log reviewed.
**D. COMMIT:** Tag as `phase4-complete`.
**E. DONE:** All three AI interfaces are callable end-to-end with correctly shaped output, all datasets are fully documented with no fabricated numbers, and splits are finalized and leakage-checked.

---

## 8. Cross-Team Dependencies

| Dependency | From → To | What's Needed |
|---|---|---|
| Contract before code | Cyber/CS (Phase 2) → AI (Phase 4) | The backend↔AI service request/response schema must be agreed before AI 1/AI 2 build their inference interfaces, or interfaces will need rework. |
| RBAC before DLP restore | Cyber (Phase 1) → Cyber (Phase 3) | The restore endpoint's authorization check depends on roles defined in Phase 1. |
| Gateway hardening before DLP endpoints | Cyber (Phase 2) → Cyber (Phase 3) | DLP redact/restore endpoints inherit rate limiting, input validation, and error handling from Phase 2 rather than reimplementing them. |
| Label definitions before labeling | AI 4 (Phase 1 draft) → AI 3 (Phase 3–4 labeling) | Labeling work in Phase 3/4 needs the label definitions drafted during Phase 1 to stay consistent across datasets. |
| Split design before split execution | AI 4 (Phase 2 design) → AI 4 (Phase 4 execution) | Train/val/test split methodology must be fixed before AI 1/AI 3 finalize dataset preprocessing, to avoid leakage. |
| AI service auth | Cyber (Phase 1 RBAC + Phase 2 gateway) → AI (Phase 4 endpoints) | AI service endpoints in Phase 4 reuse the auth model instead of inventing a separate one. |
| CS as the integration layer | CS 1 (Phase 2 stub, Phase 4 real client) | CS 1 is the single point wiring backend to AI services both phases — any contract change must go through CS 1. |

---

## 9. Definition of Done — Checklist Per Phase

**Phase 0**
- [ ] `docker compose up` starts all services with one command
- [ ] Backend and AI-service `/health` endpoints return 200
- [ ] README validated by a non-author teammate
- [ ] No secrets committed

**Phase 1**
- [ ] Register/login work with hashed passwords
- [ ] JWT issuance/validation implemented
- [ ] RBAC enforced server-side on at least one protected route
- [ ] All 6 auth security tests pass

**Phase 2**
- [ ] Rate limiting, input validation, CORS, security headers active on every route
- [ ] Centralized error handler leaks nothing internal
- [ ] Backend↔AI service contract written and reviewed by both tracks

**Phase 3**
- [ ] Regex + Presidio/spaCy detection working
- [ ] AES-256 reversible token mapping implemented (never called "tokenization")
- [ ] TTL/expiration and restore mechanism working, fail-closed
- [ ] All 8 DLP security tests pass

**Phase 4**
- [ ] RawNet2, Faster-Whisper, mBERT interfaces callable end-to-end with correctly shaped output
- [ ] All datasets documented with all 8 required fields, no fabricated numbers
- [ ] Train/val/test splits finalized and leakage-checked
- [ ] Domain-gap note written and peer-reviewed

---

## 10. Git Checkpoints

| Checkpoint | Tag | Condition to Tag |
|---|---|---|
| End of Phase 0 | `phase0-complete` | All Phase 0 acceptance criteria pass |
| End of Phase 1 | `phase1-complete` | All 6 auth security tests pass |
| End of Phase 2 | `phase2-complete` | All gateway tests pass + AI contract signed off |
| End of Phase 3 | `phase3-complete` | All 8 DLP security tests pass |
| End of Phase 4 | `phase4-complete` | All 3 AI interfaces smoke-tested + dataset docs complete + leakage checked |

Each tag should be created on `main` after `dev` has been merged in and the phase's acceptance criteria are verifiably met — not on a Friday deadline basis.

---

**Phase 0–4 complete. Stop here and validate the repository before proceeding to Phase 5.**
