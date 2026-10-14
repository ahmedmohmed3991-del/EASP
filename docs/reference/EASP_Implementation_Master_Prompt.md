You are a Senior Full-Stack Engineer, Cybersecurity Architect, and AI/ML Engineer.

Your task is to IMPLEMENT the graduation project below exactly as specified. This is a CYBERSECURITY graduation project — the AI models are supporting microservices only, never the source of security decisions. Follow the architecture, tech stack, and model choices exactly; do not substitute your own architecture unless something below is genuinely infeasible, in which case flag it explicitly before deviating.

======================================================================
PROJECT
======================================================================

Title: "Enterprise AI Security Platform (EASP) for Data Loss Prevention (DLP) and Deepfake-Based Social Engineering Defense"

One-line description: EASP sits between employees and both generative-AI services (ChatGPT, Claude, Gemini, Copilot) and voice/video communication channels. It inspects outbound prompts for sensitive data and prompt-injection attempts, verifies whether a voice or face on a call is synthetic, and enforces all of this through a policy engine with RBAC, audit logging, and SIEM-ready alerting — before sensitive data ever leaves the organization.

======================================================================
PART A — CYBERSECURITY ARCHITECTURE (already finalized, implement as-is)
======================================================================

A1. Layered architecture (6 layers):

1. Access Layer — Browser Extension (intercepts outbound AI prompts) + VoIP/PBX Capture Agent (intercepts inbound calls).
2. Identity Layer — Authentication Server, Authorization Service, RBAC Module.
3. Gateway Layer — API Gateway (TLS termination, rate limiting, routing to the Security Engine).
4. Security Engine — DLP Engine, Sensitive-Data Detection Engine, Deepfake Detection Engine (voice + image), Prompt Inspection Module, Policy Engine.
5. Intelligence & Logging — Threat Intelligence Module, Logging Server, Audit Database (MongoDB).
6. Presentation & Response — Security Dashboard, Administrator Panel, Notification System, Incident Response Module.

A2. End-to-end workflow (implement this exact sequence):

1. User submits a prompt or receives a call.
2. Browser Extension / Call Capture intercepts the request.
3. Sensitive Data Detection + Voice/Image Deepfake Verification run in parallel.
4. Policy Engine evaluates the result against RBAC and DLP rules.
5. Redaction of sensitive fields (if required).
6. Request forwarded to the AI service, or call flagged to the user.
7. Response received → sensitive data restored for the employee.
8. Audit log generated → Security Dashboard updated.

A3. Tech stack:

- Frontend: React.js (Security Dashboard, Administrator Panel).
- Backend: Node.js + Express.js (API Gateway, Policy Engine, RBAC, business logic).
- Database: MongoDB (audit logs, policy configuration, case records).
- Security controls: JWT authentication, AES-256 encryption at rest, TLS 1.3 in transit, salted password hashing, strict input validation, API rate limiting, RBAC on every endpoint, immutable audit logging.
- Monitoring: forward logs to a SIEM-compatible sink (Splunk/ELK-style log shipping).
- Python is used ONLY for the AI microservices in Part B — never for core platform logic.

A4. Cybersecurity design principles to apply throughout implementation:

- Zero Trust: authenticate and authorize every request regardless of network origin.
- Defense in Depth: DLP, prompt inspection, and deepfake verification are independent, overlapping controls — none should be a single point of failure.
- Least Privilege: RBAC restricts policy configuration and audit access to authorized security roles only.
- STRIDE threat modeling per component (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) — document mitigations per component as you build them.
- Compliance alignment: NIST Cybersecurity Framework, NIST AI RMF (AI 600-1), ISO/IEC 27001, GDPR data-minimization for redaction and log retention.

A5. Security testing to implement/automate:

- Penetration testing hooks for the API Gateway, authentication server, and browser extension.
- DLP testing using labeled synthetic-PII data (recall/precision).
- Prompt-injection testing using known adversarial prompt corpora (OWASP LLM01-aligned).
- Deepfake attack simulation using held-out samples never seen during training.
- API security, auth, load, and performance testing.
- Explicit False Positive Rate testing — usability is a hard requirement, not an afterthought.

======================================================================
PART B — AI MICROSERVICES (already selected, implement as bounded services)
======================================================================

General rule: every AI module is a REST microservice called only by the Node.js Security Engine. Each returns a normalized payload: {label, score, spans[]}. The AI layer NEVER makes the allow/block decision — it only supplies evidence to the Policy Engine.

B1. Module-by-module spec:

1. PII / Sensitive Data Detection
   - Model: Microsoft Presidio + spaCy NER (en_core_web_trf for higher accuracy if GPU available, en_core_web_sm for CPU-only).
   - Input: prompt text. Output: list of entities + confidence scores.
   - Target latency: < 100 ms.
   - Training: use directly; tune recognizer rules/context words for meaningful F1 gains (no model training required).

2. Named Entity Recognition (NER)
   - Model: spaCy transformer pipeline, same service as PII detection (shared dependency).
   - Dataset for validation: CoNLL-2003.

3. Prompt Classification (topic/risk bucketing)
   - Model: DistilBERT (fine-tuned) or SetFit for few-shot setups.
   - Input: prompt text. Output: topic/risk category.
   - Target latency: < 100 ms.
   - Training: fine-tune on a small internally labeled policy taxonomy (a few hundred to low thousands of examples).

4. Prompt Injection Detection
   - Model: ProtectAI deberta-v3-base-prompt-injection-v2 (use deberta-v3-small variant if latency-constrained).
   - Input: prompt text (truncate to 512 tokens). Output: binary label + score.
   - Target latency: < 150 ms.
   - Training: fine-tune the existing checkpoint on 1k-5k labeled EASP-specific prompts (benign + injected); reuse public injection datasets (Harelix Prompt-Injection-Mixed-Techniques-2024, ChatGPT-Jailbreak-Prompts, InjecAgent) as a base. Estimated training time: 2-6 hours on a single mid-range GPU (8-12GB VRAM).
   - Known limitation to design around: current DeBERTa-based guardrails (including this one) remain vulnerable to adversarially rephrased attacks — do not treat this module as infallible; log all borderline scores for human review.

5. Voice Deepfake Detection
   - Model: RawNet3 or ECAPA-TDNN (ensemble optional for higher robustness).
   - Input: 2-4 second audio chunks, resampled to 16kHz, VAD-segmented. Output: real/spoof score.
   - Target latency: < 300 ms per chunk.
   - Training: fine-tune on ASVspoof (2019/2021/5) plus an optional small in-house calibration set. Estimated training time: 1-2 days on a single GPU (12GB+ VRAM).
   - Known limitation to design around: cross-dataset and in-the-wild accuracy drops significantly versus in-domain benchmark accuracy (Deepfake-Eval-2024 found ~48% AUC drop for audio) — report and monitor both in-domain and out-of-domain performance, don't just quote the benchmark number.

6. Image/Video Deepfake Detection
   - Model: EfficientNet-B4 (frame-level), optional GRU temporal head if video-level context is needed.
   - Input: face-detected/cropped video frame or image. Output: real/fake score per frame.
   - Target latency: < 250 ms per frame; use frame sub-sampling (every Nth frame) to control cost.
   - Training: fine-tune on FaceForensics++/DFDC. Estimated training time: 1-2 days on a single GPU (12GB+ VRAM).
   - Known limitation to design around: ~45-50% AUC drop on real-world (in-the-wild) deepfakes versus academic benchmarks (Deepfake-Eval-2024) — same reporting requirement as the voice module.

7. OCR (screenshots / scanned documents)
   - Model: EasyOCR (best mixed Arabic/English support).
   - Input: screenshot or scanned image. Output: extracted text, fed into the PII/prompt-injection pipeline.
   - Target latency: < 500 ms per page.
   - Training: use directly, no training required.

8. Speech-to-Text
   - Model: Whisper — use "small" for CPU-only deployments, "large-v3" if a GPU is available (most robust to noise/reverberation).
   - Input: audio stream. Output: transcript text, fed into PII/prompt-injection pipeline.
   - Target latency: near real-time for streaming, a few seconds for batch.
   - Training: use directly, no training required.

9. Security-Policy Text Classification
   - Model: DistilBERT (fine-tuned on the internal DLP policy taxonomy).
   - Same rationale/latency target as prompt classification (module 3); can share infrastructure.

B2. Datasets to use for training/evaluation:

- Voice deepfake: ASVspoof 2019/2021/5, WaveFake, FakeAVCeleb.
- Image/video deepfake: FaceForensics++, DFDC, Deepfake-Eval-2024 (in-the-wild evaluation only).
- NER/PII: CoNLL-2003, Presidio synthetic PII generator output.
- Prompt injection: Harelix Prompt-Injection-Mixed-Techniques-2024, ChatGPT-Jailbreak-Prompts, InjecAgent.
- Cybersecurity text/logs: CICIDS2017/2018, UNSW-NB15.

B3. Performance optimization to implement:

- INT8/FP16 quantization for DeBERTa and CNN-based deepfake models.
- Batch inference for asynchronous paths (e.g., periodic audit re-scans); keep synchronous DLP path single-request for latency.
- Caching of repeated/near-duplicate prompt classifications.
- Shared GPU inference runtime across modules instead of one GPU process per module.
- Frame sub-sampling for video deepfake detection.

B4. Evaluation requirements:

- Classification modules (PII, injection, prompt classification): Precision, Recall, F1, Confusion Matrix.
- Detection modules (voice/image deepfake): ROC-AUC, FPR, FNR — reported separately for in-domain and out-of-domain (in-the-wild) test sets. This split is mandatory, not optional.
- Transcription/OCR modules: Word Error Rate (WER) / Character Error Rate (CER).

======================================================================
PART C — INTEGRATION RULES (apply across both parts)
======================================================================

- AI microservices are called exclusively by the Node.js/Express Security Engine — never directly by the React frontend or browser extension.
- Every inference result is written to MongoDB with the originating request ID, so the Audit Database can reconstruct which AI signal triggered which policy decision.
- The Security Dashboard visualizes AI output (e.g., deepfake confidence over a call's duration) but can never bypass the Policy Engine directly.
- The Logging System records model name, model version, and inference latency per call — required for both SIEM feeds and future model-drift detection.
- The AI layer supplies evidence only; the Policy Engine (Part A) makes every allow/redact/block decision.

======================================================================
DELIVERABLES EXPECTED FROM THIS IMPLEMENTATION PASS
======================================================================

1. Repository structure separating: /backend (Node.js/Express), /frontend (React), /ai-services (Python microservices, one per module in Part B), /extension (browser extension).
2. Working API contracts between the Security Engine and each AI microservice (request/response schemas as specified in B1).
3. RBAC-protected endpoints and JWT authentication wired end-to-end.
4. MongoDB schemas for: policies, audit logs, incidents, users/roles.
5. A minimal working Security Dashboard showing recent events, deepfake/DLP scores, and audit trail.
6. Basic automated tests covering the security-testing checklist in A5 (at least unit/integration-level, not full pentest).

If any requirement above conflicts with actual implementation constraints (e.g., GPU unavailability, licensing issues with a dataset), stop and flag the conflict with a recommended alternative before proceeding — do not silently substitute a different model or architecture.
