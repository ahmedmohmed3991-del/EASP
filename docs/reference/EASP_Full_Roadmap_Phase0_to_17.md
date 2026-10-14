# EASP — Full Implementation Roadmap (Phase 0–17)

**Enterprise AI Security Platform — Technical Project Management & System Architecture Plan**

Authoritative baseline: approved Chapter 1 / Feasibility documents. This roadmap documents planning and architecture for all 18 phases; **only Phase 0 infrastructure is currently being established — no phase beyond Phase 0 is to be implemented yet.**

Scope discipline applies throughout:
- No Future-Work item (image/video deepfake, production PBX/telephony, universal HTTPS interception, Threat Intelligence module, voiceprint verification, federated learning, autoencoder anomaly detection, ML-based source-code leakage detection) is implemented in any baseline phase.
- XGBoost+SHAP, SIEM Syslog/CEF export, the 2–3-app browser extension, and voice confidence calibration are **optional/should-implement** items, called out explicitly where relevant and never assumed as required.
- No accuracy, precision, recall, F1, EER, or latency figure is ever stated as measured unless it actually was measured in that phase. Latency is always described as a **≤3 second target**, never a result.

---

## Roadmap Overview

```
Phase 0  Repo/Docker/React/Express/FastAPI/MongoDB
Phase 1  Authentication + JWT + RBAC
Phase 2  API Gateway + security foundation
Phase 3  DLP (Regex + Presidio + spaCy)
Phase 4  Reversible encrypted token mapping (AES-256)
Phase 5  RawNet2 voice deepfake detection
Phase 6  Faster-Whisper speech-to-text
Phase 7  mBERT social-engineering classifier
Phase 8  Rule-based Risk Engine (Phase 1 fusion logic)
Phase 9  Policy Engine (Allow/Redact/Block/Escalate)
Phase 10 Audit Logging
Phase 11 React Security Dashboard
Phase 12 Controlled voice/audio demonstration integration
Phase 13 End-to-end integration
Phase 14 Security testing
Phase 15 AI evaluation
Phase 16 Performance testing
Phase 17 Final validation
```

**Team tracks used in every phase:** Cyber (4), AI/Data Science (4), CS — Backend/Frontend (2). Data Science responsibilities (acquisition, preprocessing, labeling, splits, evaluation, experiment tracking, domain-gap analysis) are carried entirely by the AI track, not a separate team.

---

## Phase 0 — Repository + Docker + React + Node/Express + FastAPI + MongoDB

**1. Objective:** Stand up a runnable skeleton for all four services with no business logic.

**2. Why this phase exists:** Establishes a shared, reproducible environment for 10 people before any feature work starts.

**3. Cyber tasks:** Define `.env` conventions and secret-handling rules; set up `.gitignore`; write branching/PR conventions; basic CI lint/build skeleton.

**4. AI/Data Science tasks:** Build FastAPI skeleton with `/health`; set up dataset workspace (`/data/raw`, `/data/processed`, `/data/labels`, git-ignored raw data); identify candidate datasets (ASVspoof, WaveFake, SMS Spam Collection, Enron, phishing corpora) without downloading yet.

**5. CS tasks:** Build Express skeleton with `/health`; build React skeleton; write `docker-compose.yml` wiring all four services + MongoDB.

**6. Dependencies:** None — starting point.

**7. Files/modules:** `/backend`, `/frontend`, `/ai-service`, `docker-compose.yml`, `.env.example` per service, `README.md`, `.gitignore`.

**8. APIs/interfaces:** `GET /health` on backend and ai-service only.

**9. Dataset requirements:** None acquired yet; workspace and candidate list only.

**10. Security requirements:** No secrets committed; environment variables used for all config; no auth yet (explicitly out of scope this phase).

**11. Tests:** `docker compose up` succeeds; both `/health` endpoints return 200; frontend loads without console errors.

**12. Acceptance criteria:** One-command boot works for a teammate following only the README.

**13. Definition of Done:** All containers healthy, both health checks green, README validated by a non-author.

**14. Expected deliverables:** Working skeleton repo, Docker Compose file, README, dataset workspace scaffold.

**15. Common mistakes to avoid:** Committing real `.env` values; hardcoding ports instead of using Docker service names; skipping the dataset `.gitignore`.

---

## Phase 1 — Authentication + JWT + RBAC

**1. Objective:** Implement user accounts, password hashing, JWT issuance/validation, and role-based access control.

**2. Why this phase exists:** Every later endpoint (DLP, AI services, dashboard, audit log) needs to know who is calling and what they're allowed to do.

**3. Cyber tasks:** Design `User` schema and password hashing; implement JWT generation/validation middleware; implement RBAC middleware and role definitions; write security tests (invalid credentials, expired JWT, tampered JWT, unauthorized access, privilege escalation).

**4. AI/Data Science tasks:** No implementation this phase; confirm which roles future AI-facing endpoints will require (input only).

**5. CS tasks:** Wire `User` model + auth routes into Express/MongoDB; build the frontend login form and JWT handling.

**6. Dependencies:** Phase 0 complete.

**7. Files/modules:** `User` model, `authController`, `authMiddleware`, `rbacMiddleware`, frontend `LoginForm`.

**8. APIs/interfaces:** `POST /auth/register` (if required), `POST /auth/login`; protected-route middleware contract (role required per route).

**9. Dataset requirements:** None.

**10. Security requirements:** Passwords hashed (bcrypt/argon2), never logged; JWT secret from environment; short-lived access tokens; RBAC enforced server-side, not just hidden in UI.

**11. Tests:** The 5 security test cases listed in Cyber tasks, automated.

**12. Acceptance criteria:** All security tests pass consistently; no plaintext passwords anywhere.

**13. Definition of Done:** Login issues a valid JWT; protected routes correctly enforce roles; all attack-style tests fail safely.

**14. Expected deliverables:** Working auth system, RBAC middleware, security test suite, role documentation.

**15. Common mistakes to avoid:** Enforcing RBAC only on the frontend; user-enumeration via inconsistent error messages; long-lived tokens with no expiration.

---

## Phase 2 — API Gateway + Security Foundation

**1. Objective:** Harden the request path: routing, rate limiting, input validation, CORS, security headers, centralized error handling, and the backend↔AI service contract (schema only).

**2. Why this phase exists:** Every feature built afterward — DLP, AI calls, dashboard — must inherit a hardened, observable request path rather than reimplementing security per-route.

**3. Cyber tasks:** Implement rate limiting, input validation middleware, CORS policy, security headers, centralized error handler (no leaked stack traces).

**4. AI/Data Science tasks:** Co-author the backend↔AI service JSON contract (fields, types, latency **target** note) with CS; continue dataset cleaning/split-design work in parallel.

**5. CS tasks:** Implement API Gateway routing layer; build a stubbed HTTP client for backend→AI service calls per the agreed contract; update frontend error handling to match the new centralized format.

**6. Dependencies:** Phase 1 complete (authenticated, role-aware requests).

**7. Files/modules:** `rateLimiter`, `inputValidation` schemas, `corsConfig`, `securityHeaders`, `errorHandler`, `ai-service-contract.md`, `aiServiceClient` (stub).

**8. APIs/interfaces:** Documented request/response schema for backend→AI calls (no live call yet).

**9. Dataset requirements:** Continued cleaning of Phase-0-identified datasets; finalized train/val/test split methodology (documented, not yet executed).

**10. Security requirements:** Every route rate-limited and validated; CORS restricted to known origins; error responses never leak internals.

**11. Tests:** Rate-limit 429 on threshold breach; malformed input rejected with 400; disallowed-origin CORS rejection; security headers present on all responses; forced internal error returns generic message only.

**12. Acceptance criteria:** All middleware active on every route (verified, not assumed); contract reviewed and signed off by both AI and CS leads.

**13. Definition of Done:** Gateway uniformly hardens all routes; AI service contract finalized before Phase 5–7 work begins.

**14. Expected deliverables:** Hardened gateway, documented contract, updated frontend error handling.

**15. Common mistakes to avoid:** Leaving `CORS: *` "temporarily"; validating only on the frontend; skipping rate limiting on auth routes (brute-force gap); locking the AI contract without AI-track sign-off.

---

## Phase 3 — DLP (Regex + Presidio + spaCy)

**1. Objective:** Build the sensitive-data detection pipeline combining regex patterns with Presidio and spaCy-based PII/NER detection.

**2. Why this phase exists:** This is the detection half of EASP's core DLP control — it must exist before reversible redaction (Phase 4) has anything to redact.

**3. Cyber tasks:** Implement regex detector module for credential/API-key-shaped patterns; integrate Presidio + spaCy for PII detection (names, emails, phone numbers); build a unified detection interface merging both result sets; define detection security tests.

**4. AI/Data Science tasks:** Tune spaCy/Presidio recognizers with domain-relevant patterns from labeled test data; continue dataset labeling for DLP-relevant text (Enron, SMS Spam Collection, synthetic PII samples) per Phase-1-defined label conventions.

**5. CS tasks:** Build `POST /dlp/detect` endpoint (detection only, no redaction/restore yet), gated by RBAC and inheriting Phase 2 middleware; minimal frontend test page for detection output.

**6. Dependencies:** Phase 2 complete (endpoint inherits validation, rate limiting, error handling).

**7. Files/modules:** `regexDetector`, `presidioSpacyDetector`, `unifiedDetectionService`, `dlpController`, frontend `DetectionTestPage`.

**8. APIs/interfaces:** `POST /dlp/detect` — input: text; output: list of flagged spans + type + detector source.

**9. Dataset requirements:** Labeled PII/credential/phishing-style text samples for detector tuning and false-positive review; label definitions must trace back to Phase-1 conventions.

**10. Security requirements:** Detected sensitive values must never be logged in plaintext during detection; detection endpoint fully covered by Phase 2 middleware.

**11. Tests:** Known PII samples correctly flagged; known credential-shaped strings correctly flagged; benign-text sample set checked for over-flagging (document rate observed, do not fabricate a target precision).

**12. Acceptance criteria:** All detection tests pass; no plaintext sensitive value appears in any log during testing.

**13. Definition of Done:** `/dlp/detect` reliably flags PII/credentials across the test dataset with results reviewed by both Cyber and AI tracks.

**14. Expected deliverables:** Unified detection service, detection endpoint, false-positive review notes, updated dataset documentation.

**15. Common mistakes to avoid:** Logging original sensitive values during debugging; treating Presidio/spaCy defaults as sufficient without project-specific tuning; fabricating a false-positive rate instead of reporting the observed one.

---

## Phase 4 — Reversible Encrypted Token Mapping (AES-256)

**1. Objective:** Replace detected sensitive spans with reversible tokens using AES-256 encrypted mapping, with TTL/expiration and an authorized restore mechanism.

**2. Why this phase exists:** Detection alone (Phase 3) doesn't protect data in transit to an AI service — this phase makes redaction actionable and reversible only for authorized, time-bound restoration.

**3. Cyber tasks:** Implement AES-256 encryption of detected values into a mapping store; implement TTL/expiration logic; implement the restore mechanism gated by RBAC from Phase 1; implement secure deletion of expired mappings; write the DLP security test suite (below).

**4. AI/Data Science tasks:** Support data-leakage prevention verification for any test data used to validate redaction/restore (ensure test PII samples don't overlap with later model-training splits).

**5. CS tasks:** Build `POST /dlp/redact` (detect + tokenize) and `POST /dlp/restore` endpoints; minimal frontend flow to redact sample text and, if authorized, restore it.

**6. Dependencies:** Phase 1 (RBAC for restore authorization), Phase 3 (detection engine to feed redaction).

**7. Files/modules:** `aes256TokenMappingService`, `ttlExpirationJob`, `restoreController`, `secureDeletionJob`, frontend `RedactRestoreDemo`.

**8. APIs/interfaces:** `POST /dlp/redact` (input: text → output: redacted text + token map ID); `POST /dlp/restore` (input: token map ID + auth → output: original text or 403/expired error).

**9. Dataset requirements:** Synthetic PII/credential samples for restore/expiry/false-positive testing (kept separate from any model-training data).

**10. Security requirements:** All mappings AES-256 encrypted at rest; restore is fail-closed (any error or ambiguity denies restoration, never discloses); expired mappings actively and securely deleted, not merely ignored. Documentation must always use "reversible encrypted token mapping using AES-256" — never "tokenization."

**11. Tests:** Redaction never returns unredacted text; authorized restore returns correct original value; unauthorized restore returns 403; expired-mapping restore fails safely; malformed input rejected without crash.

**12. Acceptance criteria:** All test cases above pass; no plaintext sensitive value persists outside the encrypted mapping store.

**13. Definition of Done:** Redact/restore work end-to-end through RBAC-gated endpoints with TTL enforcement and fail-closed behavior verified.

**14. Expected deliverables:** Working redact/restore endpoints, TTL and deletion jobs, DLP security test suite, updated documentation with the correct AES-256 terminology.

**15. Common mistakes to avoid:** Implementing restore as "if you have the token you get the value" without an authorization check; letting expired mappings linger; calling the mechanism "tokenization" anywhere in docs or code comments.

---

## Phase 5 — RawNet2 Voice Deepfake Detection

**1. Objective:** Integrate a pretrained RawNet2 model as the voice deepfake / anti-spoofing detection component, with a defined inference interface.

**2. Why this phase exists:** This is the voice-authenticity detection core of EASP's social-engineering defense — later fused into the Risk Engine (Phase 8), never treated as a standalone product feature.

**3. Cyber tasks:** Review the RawNet2 service endpoint for authentication (service-to-service credential, not public); validate input handling (file type/size limits) to prevent malformed-audio attacks.

**4. AI/Data Science tasks:** Set up the RawNet2 environment and integrate a pretrained checkpoint (pretrained-first baseline; no training from scratch); build the inference interface per the Phase 2 contract; acquire and clean ASVspoof/WaveFake data; document dataset per the 8-field standard (name, source, purpose, data type, labels, intended component, split usage, limitations, license); finalize the train/val/test split for this component and check for leakage.

**5. CS tasks:** Wire the backend HTTP client to the RawNet2 endpoint per the Phase 2 contract (no fusion into a risk score yet); build a minimal internal QA page to submit a sample audio file and view the returned score.

**6. Dependencies:** Phase 2 contract, Phase 0 AI service skeleton.

**7. Files/modules:** `rawnet2InferenceService`, `rawnet2Router` (FastAPI), backend `rawnet2Client`, `/ai-service/docs/datasets/asvspoof.md`, `/ai-service/docs/datasets/wavefake.md`.

**8. APIs/interfaces:** Input: audio file/stream (defined format/sample rate); output: spoof-probability score matching the Phase 2 schema.

**9. Dataset requirements:** ASVspoof, WaveFake — documented per the 8-field standard; splits fixed before any preprocessing statistics are computed.

**10. Security requirements:** Endpoint requires the service-to-service auth from Phase 2/1; oversized or non-audio payloads rejected with a clear error, not a crash.

**11. Tests:** Smoke test — known-format audio sample returns a correctly shaped score without error; oversized/malformed file rejected safely.

**12. Acceptance criteria:** Interface callable end-to-end from the backend; correctly shaped output confirmed; no accuracy/EER figure recorded unless a real evaluation was run (that belongs to Phase 15).

**13. Definition of Done:** RawNet2 interface stable, dataset fully documented, split finalized and leakage-checked.

**14. Expected deliverables:** Working RawNet2 inference service, dataset documentation, split/leakage report.

**15. Common mistakes to avoid:** Reporting an EER/accuracy number this early "to fill in a slide"; training RawNet2 from scratch instead of using the pretrained-first approach; skipping the leakage check because "it's just a smoke test."

---

## Phase 6 — Faster-Whisper Speech-to-Text

**1. Objective:** Integrate Faster-Whisper for transcription, exposing an inference interface matching the Phase 2 contract.

**2. Why this phase exists:** Transcripts produced here feed the mBERT social-engineering classifier (Phase 7) — this phase is purely the speech-to-text layer, not the semantic analysis.

**3. Cyber tasks:** Review endpoint authentication and input validation (audio format/size limits) consistent with Phase 5's pattern.

**4. AI/Data Science tasks:** Set up the Faster-Whisper environment (pretrained model, no fine-tuning required for baseline); build the transcription API contract/interface; document any audio preprocessing steps applied before transcription.

**5. CS tasks:** Wire backend client to the Faster-Whisper endpoint; extend the Phase 5 QA page to also show the transcript alongside the RawNet2 score.

**6. Dependencies:** Phase 2 contract; can run in parallel with Phase 5 since both are independent AI-service integrations.

**7. Files/modules:** `whisperInferenceService`, `whisperRouter`, backend `whisperClient`.

**8. APIs/interfaces:** Input: audio file/stream; output: transcript text matching the Phase 2 schema.

**9. Dataset requirements:** None required for a pretrained-baseline integration; any evaluation audio samples used for smoke testing should be documented informally (source, format).

**10. Security requirements:** Same auth and input-validation posture as Phase 5.

**11. Tests:** Smoke test — known-format audio sample returns a non-empty transcript; malformed/oversized input rejected safely.

**12. Acceptance criteria:** Interface callable end-to-end with correctly shaped, non-empty transcript output.

**13. Definition of Done:** Whisper interface stable and integrated into the shared QA page alongside RawNet2.

**14. Expected deliverables:** Working transcription service, contract documentation.

**15. Common mistakes to avoid:** Assuming transcription accuracy without ever checking a sample manually; skipping input validation because "it's just Whisper."

---

## Phase 7 — mBERT Social-Engineering Classifier

**1. Objective:** Load the pretrained mBERT encoder and build a project-specific classification head for detecting social-engineering indicators in transcribed/text content.

**2. Why this phase exists:** mBERT is explicitly not a ready-made social-engineering classifier — this phase is where the project-specific adaptation (the actual graduation-project contribution on the AI side) happens.

**3. Cyber tasks:** Review the endpoint's auth/input-validation posture consistent with Phases 5–6; threat-model what happens if this classifier receives adversarial or malformed transcript input (feeds into Phase 8/9 fail-safe design).

**4. AI/Data Science tasks:** Load the pretrained mBERT encoder; design the classification-head architecture (layer sizes, output classes) and precise label definitions (what qualifies as a "social-engineering indicator" vs. benign); acquire/clean/label text datasets (SMS Spam Collection, Enron, phishing corpora, synthetic scripted call dialogues); finalize and leakage-check the train/val/test split for this component; write the classifier's inference interface.

**5. CS tasks:** Wire backend client to the mBERT endpoint per the Phase 2 contract.

**6. Dependencies:** Phase 6 (transcripts as one input source), Phase 2 contract.

**7. Files/modules:** `mbertClassificationHead`, `mbertInferenceService`, `mbertRouter`, backend `mbertClient`, dataset docs for each text dataset, `domain-gap-note.md`.

**8. APIs/interfaces:** Input: text (transcript or raw); output: social-engineering-indicator classification matching Phase 2 schema.

**9. Dataset requirements:** SMS Spam Collection, Enron, phishing corpora, synthetic scripted call dialogues — each documented per the 8-field standard; explicit written domain-gap note acknowledging that text-based phishing/social-engineering datasets are not identical to real spoken social-engineering conversations.

**10. Security requirements:** Same endpoint auth/input-validation posture as Phases 5–6; classifier failure modes documented for Phase 9's fail-safe policy design.

**11. Tests:** Smoke test — classifier loads and produces correctly shaped output on a test input (not evaluated for accuracy yet, that's Phase 15); malformed input rejected safely.

**12. Acceptance criteria:** Classifier interface callable end-to-end; label definitions and domain-gap note reviewed by at least one AI-track member who didn't write them.

**13. Definition of Done:** mBERT classification head designed, interface stable, datasets documented, domain-gap note complete.

**14. Expected deliverables:** Working mBERT classification service, dataset documentation set, domain-gap note.

**15. Common mistakes to avoid:** Treating mBERT as already understanding social engineering without the project-specific head and labeled data; skipping the domain-gap note (this is a common defense-panel question); computing preprocessing stats before splitting (leakage).

---

## Phase 8 — Rule-Based Risk Engine (Phase 1 Fusion Logic)

**1. Objective:** Combine outputs from RawNet2, mBERT, and DLP detection into a single rule-based (weighted, not ML-based) risk score.

**2. Why this phase exists:** This is where the three independent AI/DLP signals become one actionable risk assessment — the fusion layer the Policy Engine (Phase 9) will act on. XGBoost+SHAP (Phase 2 risk engine) is explicitly out of scope here and only revisited later if sufficient labeled incident data exists.

**3. Cyber tasks:** Define the weighting rules jointly with AI (e.g., what combination of a high RawNet2 spoof score + a positive mBERT social-engineering flag constitutes "high risk"); threat-model edge cases (missing/partial signals, one service down); write fail-safe rules (default to a safe, restrictive outcome when signals are missing or a service errors).

**4. AI/Data Science tasks:** Define the fusion formula and thresholds based on documented, defensible rationale (not fabricated); document how each signal (RawNet2 score, mBERT classification, DLP detection count/type) maps to a rule-based weight; note explicitly that this is Phase 1 (rule-based) and XGBoost+SHAP is deferred and conditional.

**5. CS tasks:** Implement the Risk Engine service consuming outputs from the three upstream services (Phases 3/5/7) and producing a single risk score/level; wire it into the backend.

**6. Dependencies:** Phases 3, 4, 5, 7 complete (all upstream signals must exist and be callable).

**7. Files/modules:** `ruleBasedRiskEngine`, `riskEngineConfig` (weights/thresholds), `riskEngineController`.

**8. APIs/interfaces:** Input: DLP detection result + RawNet2 score + mBERT classification; output: risk level (e.g. Low/Medium/High) + contributing-factor breakdown.

**9. Dataset requirements:** None new; may reference labeled data from Phases 5/7 to sanity-check rule thresholds, without claiming a formal validation study.

**10. Security requirements:** Fail-safe: if any upstream signal is unavailable or malformed, the engine defaults to a conservative (higher-risk) outcome rather than silently ignoring the missing signal.

**11. Tests:** Known signal combinations produce the expected risk level; missing/partial signal input triggers the documented fail-safe behavior; malformed upstream output is rejected/handled without crashing the engine.

**12. Acceptance criteria:** Risk levels are reproducible and traceable to the documented rule set — no hidden or undocumented weighting.

**13. Definition of Done:** Risk Engine consumes all three upstream signals correctly, fail-safe behavior verified, weighting rules documented.

**14. Expected deliverables:** Working rule-based Risk Engine, documented weighting rationale, fail-safe test results.

**15. Common mistakes to avoid:** Building or half-building XGBoost+SHAP "just in case" during this phase; hardcoding weights without documenting the rationale; failing open (returning "low risk") when an upstream signal errors.

---

## Phase 9 — Policy Engine (Allow / Redact / Block / Escalate)

**1. Objective:** Translate the Risk Engine's output into an enforced action: Allow, Redact, Block, or Escalate.

**2. Why this phase exists:** A risk score alone doesn't protect anything — the Policy Engine is the enforcement point that actually changes what happens to a request based on role, risk level, and DLP findings.

**3. Cyber tasks:** Define policy rules per role (from Phase 1 RBAC) and risk level; implement enforcement logic; ensure Escalate actions integrate with Audit Logging (Phase 10) and, if in scope, an alerting path; write security tests for each action path.

**4. AI/Data Science tasks:** Support tuning of risk-level thresholds that trigger each policy action, based on Phase 8's documented rule set.

**5. CS tasks:** Implement the Policy Engine service and its integration points with the DLP redact/restore endpoints (Phase 4), the Risk Engine (Phase 8), and the eventual dashboard (Phase 11).

**6. Dependencies:** Phase 8 (risk score input), Phase 4 (redact action), Phase 1 (role-aware policy).

**7. Files/modules:** `policyEngineService`, `policyRulesConfig`, `policyEngineController`.

**8. APIs/interfaces:** Input: risk level + role + DLP findings; output: enforced action (Allow/Redact/Block/Escalate) + reason code.

**9. Dataset requirements:** None.

**10. Security requirements:** Policy decisions must be deterministic and traceable to a specific rule; Escalate path must never silently fail (must always produce an audit entry).

**11. Tests:** Each of the four actions triggers correctly for its designed risk/role combination; an Escalate action always produces a corresponding audit log entry (tested jointly with Phase 10 once available, or stubbed if built in parallel).

**12. Acceptance criteria:** All four action paths tested and traceable to documented rules.

**13. Definition of Done:** Policy Engine reliably converts risk scores into the correct enforced action across all tested role/risk combinations.

**14. Expected deliverables:** Working Policy Engine, documented policy rule set, test results for all four action paths.

**15. Common mistakes to avoid:** Hardcoding policy decisions in the Risk Engine itself instead of keeping this a separate, auditable layer; letting an Escalate action complete without generating a log entry.

---

## Phase 10 — Audit Logging

**1. Objective:** Implement immutable audit logging for authentication events, DLP actions, Risk Engine outputs, and Policy Engine decisions.

**2. Why this phase exists:** A security platform without audit logs cannot be trusted or defended in an academic or real-world review — this is required for compliance-style reasoning and for the dashboard (Phase 11) to have data to display.

**3. Cyber tasks:** Define what must be logged (auth events, DLP redact/restore, risk scores, policy decisions) without ever logging raw sensitive values; implement log integrity measures (e.g., append-only writes, no update/delete API); write tests confirming sensitive values never appear in logs.

**4. AI/Data Science tasks:** Confirm which AI-service outputs (RawNet2 score, mBERT classification) should appear in the audit trail alongside DLP/risk data.

**5. CS tasks:** Implement the audit log storage (MongoDB collection) and a write-only logging service used by auth, DLP, Risk Engine, and Policy Engine modules.

**6. Dependencies:** Phases 1, 4, 8, 9 (this phase logs their outputs).

**7. Files/modules:** `auditLogService`, `AuditLog` model (append-only), integration hooks in `authController`, `dlpController`, `riskEngineController`, `policyEngineController`.

**8. APIs/interfaces:** Internal logging interface (not directly user-facing this phase); `GET /audit/logs` (RBAC-gated, read-only) for later dashboard use.

**9. Dataset requirements:** None.

**10. Security requirements:** Logs are append-only (no update/delete route exposed); logs never contain plaintext sensitive values (only references/token IDs where relevant); read access to logs is RBAC-gated.

**11. Tests:** Every auth/DLP/risk/policy event produces a corresponding log entry; log entries never contain raw sensitive values; unauthorized roles cannot read logs.

**12. Acceptance criteria:** 100% of the defined event types produce a log entry in testing; no sensitive-value leakage in any log entry.

**13. Definition of Done:** All four upstream modules reliably log to the append-only store, verified by test coverage.

**14. Expected deliverables:** Working audit logging service, `AuditLog` schema, read-only log endpoint, log-content security test results.

**15. Common mistakes to avoid:** Logging DLP-restored plaintext values "for debugging"; exposing an update/delete endpoint on the log collection; forgetting to log Escalate actions from Phase 9.

---

## Phase 11 — React Security Dashboard

**1. Objective:** Build the SOC-style dashboard: audit log viewer, risk-level overview, DLP activity, and (if relevant) policy decisions — role-gated per Phase 1 RBAC.

**2. Why this phase exists:** This is the human interface that makes the platform demonstrable and usable by a SOC-analyst-style role, and it's the primary artifact for the project defense demo.

**3. Cyber tasks:** Define which roles can view which dashboard sections; review the dashboard's API calls for proper RBAC enforcement (not just UI-level hiding).

**4. AI/Data Science tasks:** Define how AI-service outputs (RawNet2 score, mBERT classification) should be summarized/visualized without overstating certainty (e.g., showing a score, not an unqualified "fake"/"real" label unless the underlying decision logic supports that framing).

**5. CS tasks:** Build the React dashboard: audit log table/view, risk-level summary, DLP activity view; wire to `GET /audit/logs` and related read endpoints; implement role-gated navigation.

**6. Dependencies:** Phase 10 (log data to display), Phase 1 (roles), Phase 8/9 (risk/policy data).

**7. Files/modules:** `Dashboard` React app section, `AuditLogView`, `RiskOverview`, `DlpActivityView`, `AdminPanel` (role-gated).

**8. APIs/interfaces:** Consumes `GET /audit/logs`, and read endpoints for risk/policy summaries (built as needed off Phase 8/9 data).

**9. Dataset requirements:** None.

**10. Security requirements:** All dashboard data fetches go through RBAC-gated endpoints; no client-side-only access control.

**11. Tests:** Role-appropriate dashboard sections render correctly per role; unauthorized roles cannot fetch restricted data even via direct API calls (not just hidden UI).

**12. Acceptance criteria:** Dashboard accurately reflects backend data with correct role-based visibility, verified by both UI testing and direct API testing.

**13. Definition of Done:** Dashboard is functional, role-gated correctly at both UI and API level, and usable for a live demo.

**14. Expected deliverables:** Working React dashboard, role-gated views, API-level RBAC verification results.

**15. Common mistakes to avoid:** Hiding UI elements by role without enforcing the same restriction server-side; presenting AI scores as certainties instead of probabilistic outputs.

---

## Phase 12 — Controlled Voice/Audio Demonstration Integration

**1. Objective:** Build a controlled, offline/sandboxed demonstration flow where a pre-recorded or live-in-lab audio sample flows through RawNet2 → Faster-Whisper → mBERT → Risk Engine → Policy Engine → Dashboard, for defense purposes.

**2. Why this phase exists:** The project's baseline explicitly excludes production PBX/telephony integration and universal HTTPS interception — this phase provides a realistic, demonstrable substitute scoped to what an undergraduate team can actually build and defend.

**3. Cyber tasks:** Ensure the demonstration environment is sandboxed (no real telephony, no production network exposure); review the demo's data-handling (are sample recordings stored securely, deleted after use, consented to by participants if real voices are used).

**4. AI/Data Science tasks:** Prepare a small, clearly-labeled set of demonstration audio samples (synthetic or consented recordings only); document their provenance and limitations distinctly from the training/evaluation datasets used in Phases 5–7.

**5. CS tasks:** Build the end-to-end demo flow UI/trigger (e.g., an "upload/select sample and run through pipeline" flow in the dashboard) wired to the already-built services.

**6. Dependencies:** Phases 5, 6, 7, 8, 9, 10, 11 all functioning individually.

**7. Files/modules:** `demoPipelineController`, `DemoRunner` frontend component, `/ai-service/docs/datasets/demo-samples.md`.

**8. APIs/interfaces:** `POST /demo/run` — input: selected sample; output: full pipeline trace (transcript, RawNet2 score, mBERT classification, risk level, policy action) for display.

**9. Dataset requirements:** Small demonstration sample set, clearly separated from training/evaluation data, with documented consent/provenance.

**10. Security requirements:** Demo environment isolated from any production-like network path; demo audio deleted or securely stored per policy after each session; explicitly labeled as "controlled demonstration," never described as a production telephony integration.

**11. Tests:** A known-benign sample produces an Allow/Low-risk result end-to-end; a known-suspicious sample (e.g., a spoofed sample from the ASVspoof test split, used only for demo not training) produces an Escalate/High-risk result end-to-end.

**12. Acceptance criteria:** The full pipeline runs end-to-end reliably for at least the two demo cases above, with all steps visible on the dashboard.

**13. Definition of Done:** Demonstration flow works reliably and repeatably for the project defense, using only sandboxed, documented sample data.

**14. Expected deliverables:** Working demo pipeline trigger and view, documented demo sample set, isolation/consent documentation.

**15. Common mistakes to avoid:** Describing this as "PBX integration" or implying production telephony capability; reusing training-split samples as demo samples without noting the overlap; leaving demo audio stored insecurely after sessions.

---

## Phase 13 — End-to-End Integration

**1. Objective:** Integrate all previously independent modules (auth, gateway, DLP, redaction, RawNet2, Whisper, mBERT, Risk Engine, Policy Engine, audit logging, dashboard) into one coherent running system, beyond the scoped Phase 12 demo path.

**2. Why this phase exists:** Phases 1–12 build components in relative isolation; this phase confirms they function together as a single platform under realistic (not just demo-scripted) conditions.

**3. Cyber tasks:** Verify RBAC and gateway hardening apply consistently across every integrated route; re-run the Phase 1/2/3/4 security test suites against the fully integrated system to catch regressions.

**4. AI/Data Science tasks:** Verify that RawNet2/Whisper/mBERT outputs flow correctly and consistently into the Risk Engine under integrated conditions (not just isolated smoke tests).

**5. CS tasks:** Resolve integration issues across backend, AI services, and frontend; ensure consistent error handling and data contracts across the full request path.

**6. Dependencies:** All of Phases 0–12.

**7. Files/modules:** Integration test suite, updated API documentation reflecting the final, integrated contract set.

**8. APIs/interfaces:** No new interfaces — this phase validates existing ones working together.

**9. Dataset requirements:** None new.

**10. Security requirements:** All previously-established security controls (RBAC, rate limiting, validation, AES-256 redaction, fail-safe Risk Engine, audit logging) must hold under integrated conditions.

**11. Tests:** Full regression run of all prior phases' test suites against the integrated system; at least one multi-module scenario test (e.g., a request that triggers DLP redaction, a risk score, a policy action, and an audit log entry in one flow).

**12. Acceptance criteria:** No regressions found, or all found regressions fixed and re-tested; the multi-module scenario test passes.

**13. Definition of Done:** The full platform runs as one integrated system with all previously verified security and functional behavior intact.

**14. Expected deliverables:** Integration test report, updated/consolidated API documentation.

**15. Common mistakes to avoid:** Treating "the demo works" (Phase 12) as equivalent to "everything is integrated"; skipping regression testing of earlier phases' security suites.

---

## Phase 14 — Security Testing

**1. Objective:** Conduct a dedicated, systematic security testing pass across the fully integrated platform.

**2. Why this phase exists:** This is a Cybersecurity graduation project — a dedicated security testing phase, beyond the per-phase unit tests already run, is required to credibly claim the platform was assessed as a whole.

**3. Cyber tasks:** Design and execute a security test plan covering: authentication/RBAC bypass attempts, rate-limit bypass attempts, input validation edge cases, DLP restore abuse attempts, policy-engine bypass attempts, and audit-log tampering attempts; document findings and remediations.

**4. AI/Data Science tasks:** Support testing of adversarial/malformed inputs specifically against RawNet2, Whisper, and mBERT endpoints (e.g., corrupted audio, extremely short/long input, non-target-language text) to confirm safe failure rather than crashes or undefined behavior.

**5. CS tasks:** Fix any integration-level vulnerabilities identified; ensure test results are reproducible via an automated test suite where possible.

**6. Dependencies:** Phase 13 complete (integrated system to test).

**7. Files/modules:** `security-test-plan.md`, automated security test suite additions, `security-findings-report.md`.

**8. APIs/interfaces:** None new — testing existing interfaces.

**9. Dataset requirements:** Adversarial/edge-case input samples for AI service robustness testing (documented, not claimed as a formal adversarial-ML evaluation unless it genuinely is one).

**10. Security requirements:** All findings must be remediated or explicitly documented as accepted risk with rationale (appropriate for an undergraduate project scope).

**11. Tests:** The full security test plan executed against the integrated system; regression tests re-run after each fix.

**12. Acceptance criteria:** No critical/high findings remain unaddressed; medium/low findings documented with rationale if deferred.

**13. Definition of Done:** Security test plan fully executed, findings documented, critical/high issues resolved and re-verified.

**14. Expected deliverables:** Security test plan, findings report, remediation evidence.

**15. Common mistakes to avoid:** Treating earlier per-phase tests as a substitute for this dedicated pass; leaving any critical finding "for later" without explicit sign-off from the team/advisor.

---

## Phase 15 — AI Evaluation

**1. Objective:** Formally evaluate RawNet2, Faster-Whisper (qualitatively), and mBERT on their held-out test splits, and report real, measured results.

**2. Why this phase exists:** This is the only phase where accuracy/precision/recall/F1/EER-type figures may legitimately be reported — because it's where they are actually measured, using the splits finalized and leakage-checked back in Phases 5 and 7.

**3. Cyber tasks:** Review the evaluation process for any signs the test split was compromised (e.g., accidental training-data reuse) — an independent check on data integrity.

**4. AI/Data Science tasks:** Run RawNet2 evaluation on its held-out ASVspoof/WaveFake test split and report the actual metric(s) obtained (e.g., EER, if computed); run mBERT evaluation on its held-out text test split and report actual metrics (e.g., accuracy, F1, precision, recall) as measured; perform qualitative review of Faster-Whisper transcription quality on a sample set (word-error-rate only if actually computed); document all results with methodology, exact test-set composition, and known limitations.

**5. CS tasks:** Support any tooling needed to batch-run evaluation samples through the deployed inference services.

**6. Dependencies:** Phases 5 and 7 (finalized, leakage-checked splits); Phase 13 (stable integrated services to evaluate against, or standalone service evaluation if preferred).

**7. Files/modules:** `evaluation-report-rawnet2.md`, `evaluation-report-mbert.md`, `evaluation-report-whisper.md` (qualitative), evaluation scripts.

**8. APIs/interfaces:** None new.

**9. Dataset requirements:** The held-out test splits defined in Phases 5 and 7, used here for the first and only time as test data.

**10. Security requirements:** N/A for this phase beyond ensuring test data wasn't previously exposed to the models (leakage check).

**11. Tests:** Evaluation scripts run cleanly and reproducibly against the held-out splits; results cross-checked by a second AI-track member.

**12. Acceptance criteria:** Reported metrics are reproducible from the documented methodology and test set; no metric is reported without having actually been computed.

**13. Definition of Done:** Evaluation reports complete for RawNet2 and mBERT with real measured metrics, and a qualitative Whisper review, all peer-reviewed.

**14. Expected deliverables:** Three evaluation reports with methodology, results, and limitations sections.

**15. Common mistakes to avoid:** Reporting a metric from an earlier phase's smoke test as if it were a formal evaluation result; evaluating on data that overlapped with training; presenting a single run's result without noting variance if multiple runs were feasible.

---

## Phase 16 — Performance Testing

**1. Objective:** Measure actual system latency and throughput against the documented ≤3 second **target**, and report real, measured numbers.

**2. Why this phase exists:** This is the only phase where a latency figure may be reported as a result — everywhere else, ≤3 seconds is a target, not a claim.

**3. Cyber tasks:** Verify performance testing doesn't bypass security controls (e.g., testing shouldn't disable rate limiting in a way that misrepresents real-world behavior); review resource-exhaustion risk under load (a security-relevant performance concern).

**4. AI/Data Science tasks:** Measure and report actual inference latency for RawNet2, Whisper, and mBERT individually under realistic load; note any component that misses the ≤3s target and why.

**5. CS tasks:** Set up and run load/latency testing tooling against the integrated end-to-end pipeline (e.g., request → DLP → AI services → Risk Engine → Policy Engine); report actual end-to-end latency figures.

**6. Dependencies:** Phase 13 (integrated system to test).

**7. Files/modules:** `performance-test-plan.md`, `performance-test-report.md`, load-testing scripts.

**8. APIs/interfaces:** None new.

**9. Dataset requirements:** Representative sample inputs for load generation (documented, not claimed as production traffic).

**10. Security requirements:** Load testing conducted only in the sandboxed/dev environment, never against a live-if-any production system.

**11. Tests:** End-to-end latency measured across a representative sample set; per-component latency measured for RawNet2, Whisper, mBERT.

**12. Acceptance criteria:** Actual measured latency is reported honestly whether or not it meets the ≤3s target; if it doesn't meet target, that is stated plainly along with likely causes.

**13. Definition of Done:** Performance test report complete with real measured numbers and an honest comparison against the ≤3s target.

**14. Expected deliverables:** Performance test plan and report with measured latency/throughput figures.

**15. Common mistakes to avoid:** Reporting the ≤3s figure as if it were the measured result rather than clearly separating target vs. actual; testing under unrealistically light load and generalizing the result.

---

## Phase 17 — Final Validation

**1. Objective:** Confirm the full platform meets all baseline feature requirements, all acceptance criteria from Phases 0–16 are satisfied, and the system is ready for defense/demonstration.

**2. Why this phase exists:** This is the final gate before presenting EASP as complete — it confirms nothing was skipped or left in a partially-working state.

**3. Cyber tasks:** Re-verify all security acceptance criteria from Phases 1–4, 8–10, 14 in one consolidated pass; sign off on the security posture of the final system.

**4. AI/Data Science tasks:** Re-verify all AI/dataset documentation (Phases 5–7, 15) is complete, accurate, and consistent with the final integrated behavior; sign off on the AI components.

**5. CS tasks:** Re-verify all backend/frontend acceptance criteria from Phases 0, 2, 9, 11, 13; sign off on system integration.

**6. Dependencies:** All of Phases 0–16.

**7. Files/modules:** `final-validation-checklist.md` consolidating every phase's Definition of Done.

**8. APIs/interfaces:** None new — final confirmation of all existing ones.

**9. Dataset requirements:** Confirm all dataset documentation is complete and consistent; no undocumented dataset in use anywhere in the final system.

**10. Security requirements:** Confirm no Future-Work item has been silently implemented; confirm no fabricated metric appears anywhere in final documentation.

**11. Tests:** Full regression suite (all phases) run one final time against the final system state.

**12. Acceptance criteria:** Every phase's Definition of Done is checked off and verifiably true in the final system, not just historically true at the time that phase was built.

**13. Definition of Done:** Consolidated checklist fully signed off by all three tracks (Cyber, AI, CS).

**14. Expected deliverables:** Final validation checklist and sign-off record, ready to support the graduation project defense.

**15. Common mistakes to avoid:** Assuming a phase is still "done" without re-checking it after later integration work; discovering at defense time that a Future-Work item accidentally crept into the implementation or that an unmeasured number was written down as fact somewhere in the documentation.

---

## Global Reminders (apply to every phase above)

- Every phase's tasks are scoped strictly to the **Baseline Features** list. Optional items (XGBoost+SHAP, SIEM export, browser extension, voice confidence calibration) are only pursued if explicitly requested and resourced separately — they are not folded into any baseline phase's Definition of Done.
- No Future-Work item is implemented in any phase above. If a phase's design tempts the team toward one (e.g., wanting "real" telephony in Phase 12, or wanting a Threat Intelligence feed in Phase 8), that impulse should be logged as a Future Work note, not built.
- No accuracy/precision/recall/F1/EER/latency figure appears anywhere before Phases 15–16, where it is actually measured — and even then, only the specific number actually computed is reported.
- Latency is described as "≤3 seconds (target)" everywhere except Phase 16's actual measured results.

**Current status confirmed: only Phase 0 is authorized for implementation right now. Phases 1–17 above are planning/architecture only until explicitly requested.**
