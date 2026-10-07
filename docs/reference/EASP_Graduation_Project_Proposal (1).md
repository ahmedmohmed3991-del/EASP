**Graduation Project Proposal**

**Enterprise AI Security Platform for Data Loss Prevention and Deepfake-Based Social Engineering Defense**

_A Cybersecurity Engineering Graduation Project (AI used strictly as a supporting technology)_

Prepared by: Ahmed

Department of Computer Science & Information Systems (CIS)

Egyptian Chinese University

July 2026

# Executive Summary

Organizations are rapidly adopting generative AI tools such as ChatGPT, Claude, Gemini, and Microsoft Copilot for daily work. This adoption creates a new and largely unmanaged attack surface: employees paste confidential data into public AI chatbots, attackers use AI-generated voices and videos to impersonate executives, and adversaries craft prompt-injection payloads that bypass existing security controls. Traditional perimeter security - firewalls, antivirus, and classic Data Loss Prevention (DLP) - was never designed to understand a conversation with an AI model or to verify whether a voice on a call is human.

This project proposes the Enterprise AI Security Platform (EASP), a cybersecurity solution that sits between employees and both generative AI services and voice/video communication channels. EASP combines AI-aware Data Loss Prevention, sensitive-data detection, prompt inspection, and deepfake (voice and image) verification inside a single policy-driven security architecture with role-based access control, audit logging, real-time alerting, and compliance reporting. Machine learning models (NER/PII detectors, anti-spoofing classifiers) are used only as detection components inside conventional cybersecurity engineering - authentication, encryption, RBAC, logging, and a SIEM-integrated policy engine - which is why this remains a Cybersecurity graduation project rather than an Artificial Intelligence research project.

# Part 1 - Cybersecurity Background and Threat Landscape

The rise of generative AI has introduced threat categories that did not exist five years ago, alongside the persistence of classic ones:

- AI-generated cyber threats: attackers use LLMs to write phishing emails, malware variants, and reconnaissance scripts at scale.
- Data leakage through AI prompts: employees unintentionally submit source code, credentials, financial records, or customer PII to public AI chat interfaces that are outside organizational control.
- Insider threats: both malicious and accidental disclosure of sensitive data is amplified when every employee has a direct text channel to an external AI service.
- Prompt injection: OWASP ranks prompt injection as the top risk (LLM01:2025) for LLM-integrated applications; malicious instructions hidden in user input or in retrieved documents can override an application's intended behavior \[1\]\[2\].
- Social engineering and deepfake attacks: AI voice cloning and synthetic video are now used to impersonate executives ("CEO fraud") and trick employees into wire transfers or credential disclosure.
- AI abuse inside organizations: "Shadow AI" - unsanctioned use of consumer AI tools with no governance, logging, or DLP coverage.

Traditional controls fall short for three structural reasons: (1) firewalls and web proxies inspect network packets, not conversational intent, so they cannot tell a legitimate question from a data-exfiltration attempt; (2) classic DLP relies on static regex and keyword matching, which cannot parse free-form natural-language prompts or detect semantically disguised sensitive data; and (3) authentication and access-control systems verify who is logged in, not whether the voice or face on a call is genuinely human. This gap is the cybersecurity problem this project addresses.

# Part 2 - Literature Review

Existing solutions address fragments of the problem. The table below compares representative enterprise products and research directions.

| **Solution**                                                           | **How It Works**                                                                                                                                                                          | **Strengths**                                                                                                    | **Limitations / Gap**                                                                                                                                                                                           |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Microsoft Purview DLP                                                  | Endpoint and browser-level DLP with sensitivity labels; now extends inline protection into Edge for Business to block sensitive prompts sent to ChatGPT, Gemini, and DeepSeek \[3\]\[4\]. | Deep Microsoft 365 integration; broad sensitive-information-type library; Insider Risk Management correlation.   | Vendor-locked to Microsoft ecosystem and managed/Edge-onboarded devices; limited deepfake or voice-channel coverage; premium E5/A5 licensing \[5\].                                                             |
| Lasso Security                                                         | AI-native gateway that inspects LLM traffic for prompt injection, jailbreaks, and data exfiltration using intent-based (semantic) detection rather than keyword matching \[6\]\[7\].      | Sub-50ms detection latency; understands conversational intent; integrates with LLM gateways and Cloudflare edge. | Focused on text-based LLM traffic; no deepfake/voice verification; enterprise-only, closed-source.                                                                                                              |
| Mithril Security                                                       | Confidential-computing approach (hardware-enclave based) for protecting data used in or by AI models.                                                                                     | Strong cryptographic data-in-use guarantees.                                                                     | Narrow scope - protects model/data confidentiality, not conversational DLP or social-engineering defense.                                                                                                       |
| CrowdStrike / Palo Alto Prisma AIRS                                    | Endpoint/XDR platforms extending into AI security: model scanning, AI agent runtime protection, and posture management for agentic AI \[8\]\[9\].                                         | Mature SOC/XDR integration; strong threat-intelligence pipelines; rapid 2025 expansion into agent security.      | Primarily infrastructure/agent-centric; not purpose-built for employee-to-chatbot DLP or deepfake voice defense.                                                                                                |
| Forcepoint DLP / Proofpoint                                            | Long-established enterprise DLP suites using content inspection, fingerprinting, and behavioral analytics across endpoints, email, and cloud.                                             | Mature policy engines; wide regulatory-template coverage (GDPR, HIPAA, PCI-DSS).                                 | Built for structured channels (email, file transfer); weak native understanding of generative-AI prompt/response pairs.                                                                                         |
| Google Cloud DLP API                                                   | Pattern- and ML-based detector for 150+ built-in sensitive-information types, usable as a scanning microservice.                                                                          | Flexible, API-first, cloud-scale.                                                                                | A building block, not an end-to-end platform; needs custom integration with policy engine, RBAC, and alerting.                                                                                                  |
| Academic deepfake detection (FaceForensics++, ASVspoof, DeepfakeBench) | CNN/Transformer classifiers trained on benchmark datasets to flag manipulated video/audio \[10\]\[11\]\[12\].                                                                             | Rich, continuously updated benchmarks; strong published baselines.                                               | Cross-dataset generalization remains weak - models trained on FaceForensics++/ASVspoof lose up to ~50% AUC on real-world ("in the wild") deepfakes \[11\]; rarely integrated with enterprise DLP/SOC workflows. |

**Research gap identified:** no reviewed solution unifies (a) semantic, AI-aware DLP for generative-AI prompts, (b) real-time voice/image deepfake verification, and (c) enterprise SOC/SIEM-integrated policy, RBAC, and audit controls in a single cybersecurity platform. Vendors solve either the DLP problem or the deepfake problem, rarely both, and academic deepfake detectors are not engineered as production security controls with logging, RBAC, and incident response.

# Part 3 - Problem Statement

- Employees copy confidential business data, source code, or customer records into public generative-AI chat interfaces with no inspection or redaction step.
- Developers accidentally paste API keys, database credentials, or internal architecture diagrams into AI prompts for debugging help.
- Attackers use short voice samples to clone an executive's voice and issue fraudulent payment or data-disclosure instructions over the phone.
- Deepfake video calls are used to impersonate managers in "urgent approval" social-engineering scenarios.
- Prompt-injection payloads embedded in documents or emails processed by internal AI assistants can override intended instructions and exfiltrate data.
- Existing DLP tools apply static pattern matching and cannot interpret the semantics of a natural-language AI conversation, producing both missed leaks and excessive false positives.
- Deepfake-detection tools exist as isolated research prototypes or point products with no connection to enterprise identity, policy, or SOC/SIEM systems.

# Part 4 - Proposed Solution

The Enterprise AI Security Platform (EASP) is an original cybersecurity architecture - not a single AI model - that combines the following controls under one policy engine:

- AI-aware Data Loss Prevention: inspects outbound prompts to generative-AI services before they leave the organization.
- Sensitive Data Detection Engine: NER/PII detection to flag names, credentials, financial data, and confidential code fragments.
- Prompt Inspection: semantic screening for prompt-injection and jailbreak patterns, aligned with OWASP LLM Top 10 guidance \[2\].
- Voice Deepfake Detection: anti-spoofing classification of live or recorded calls to flag AI-generated voices.
- Image/Video Deepfake Detection: forensic classification of video-call frames for manipulation artifacts.
- Policy Engine and RBAC: centrally defines what may be redacted, blocked, or escalated, per role and data sensitivity.
- Threat Intelligence feed, Audit Logs, Security Dashboard, Incident Monitoring, Real-time Alerts, and Compliance Reporting.

The platform is designed to intervene before sensitive data leaves the organization - the redaction and verification steps happen inline, not as after-the-fact forensics.

# Part 5 - System Architecture

EASP follows a layered, Zero-Trust architecture. Each request - whether a prompt to an AI service or an incoming voice/video call - passes through authentication, inspection, and policy enforcement before reaching its destination.

| **Layer**               | **Components**                                                                                                                  | **Responsibility**                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Access Layer            | Browser Extension, VoIP/PBX Capture Agent                                                                                       | Intercepts outbound AI prompts and inbound calls at the point of use.                         |
| Identity Layer          | Authentication Server, Authorization Service, RBAC Module                                                                       | Verifies user identity and enforces least-privilege access to platform functions.             |
| Gateway Layer           | API Gateway                                                                                                                     | Routes traffic to the Security Engine; enforces rate limiting and TLS/HTTPS termination.      |
| Security Engine         | DLP Engine, Sensitive-Data Detection Engine, Deepfake Detection Engine (voice + image), Prompt Inspection Module, Policy Engine | Core inspection logic: classifies content, evaluates policy, decides allow/redact/block.      |
| Intelligence & Logging  | Threat Intelligence Module, Logging Server, Audit Database (MongoDB)                                                            | Correlates external threat feeds; stores immutable audit trails for compliance and forensics. |
| Presentation & Response | Security Dashboard, Administrator Panel, Notification System, Incident Response Module                                          | Gives SOC analysts visibility, alerting, and case management.                                 |

Workflow - data flows strictly left to right through inspection before reaching the AI service or the human recipient:

| **User submits a prompt or receives a call**                     |
| ---------------------------------------------------------------- |
| ↓                                                                |
| **Browser Extension / Call Capture intercepts the request**      |
| ↓                                                                |
| **Sensitive Data Detection + Voice/Image Deepfake Verification** |
| ↓                                                                |
| **Policy Engine evaluates against RBAC and DLP rules**           |
| ↓                                                                |
| **Redaction of sensitive fields (if required)**                  |
| ↓                                                                |
| **Request forwarded to AI service / Call flagged to user**       |
| ↓                                                                |
| **Response received → sensitive data restored for the employee** |
| ↓                                                                |
| **Audit log generated → Security Dashboard updated**             |

# Part 6 - Implementation Plan

| **Layer**                 | **Technology**                                                                                                           | **Purpose**                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Frontend                  | React.js                                                                                                                 | Security Dashboard and Administrator Panel.                                            |
| Backend                   | Node.js + Express.js                                                                                                     | API Gateway, Policy Engine, RBAC, business logic.                                      |
| Database                  | MongoDB                                                                                                                  | Audit logs, policy configuration, case records.                                        |
| Security Controls         | JWT authentication, AES-256 encryption, HTTPS/TLS, salted hashing, input validation, rate limiting                       | Core application security hardening.                                                   |
| Monitoring                | SIEM integration (e.g., Splunk/ELK-compatible log forwarding)                                                            | Centralized detection and correlation for the SOC.                                     |
| AI Support Layer (Python) | Used only for deepfake detection, NER, sensitive-data detection, and speech analysis - not for the platform's core logic | Supporting detection microservices called by the Security Engine over an internal API. |

Machine-learning mathematics is intentionally out of scope: pretrained models are consumed as classification services, and engineering effort is concentrated on secure integration, policy logic, and system hardening - consistent with this being a cybersecurity, not an AI-research, project.

# Part 7 - AI Models (Supporting Components)

| **Task**                                     | **Recommended Pretrained Model**                                                      | **Why It Is Suitable**                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Named Entity Recognition / PII Detection     | spaCy transformer NER pipelines; Microsoft Presidio (rule + ML hybrid)                | Open-source, production-proven for detecting names, locations, and organizations inside free-form prompt text.                   |
| Structured PII / Sensitive Pattern Detection | Regex + ML hybrid detectors (Presidio analyzers, Google Cloud DLP built-in detectors) | Combines high-precision pattern matching (card numbers, IBANs) with ML for context-dependent PII.                                |
| OCR (screenshots/pasted images)              | Tesseract OCR / EasyOCR                                                               | Mature, offline-capable OCR needed to inspect sensitive data pasted as images.                                                   |
| Speech-to-Text                               | OpenAI Whisper (open-weight variants)                                                 | Strong multilingual (Arabic/English) transcription accuracy to feed the NLP context-analysis layer.                              |
| Voice Deepfake / Anti-Spoofing               | Wav2Vec2-based countermeasure models trained on ASVspoof 5 \[12\]                     | State-of-the-art benchmark for detecting synthetic/cloned speech, with an actively maintained challenge series.                  |
| Image/Video Deepfake Detection               | Transformer/CNN detectors benchmarked on FaceForensics++ / DeepfakeBench \[10\]\[11\] | Widely validated baselines for facial manipulation artifacts; extensible with domain-adversarial fine-tuning for generalization. |

# Part 8 - Public Datasets

| **Purpose**                        | **Datasets**                                                                   | **Usage**                                                                                                                      |
| ---------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Voice Deepfake                     | ASVspoof 2019/2021/5, FakeAVCeleb \[12\]\[23\]\[28\]                           | Train/evaluate the anti-spoofing countermeasure model for cloned or synthetic voices.                                          |
| Image/Video Deepfake               | FaceForensics++, Celeb-DF, DFDC, DeepFake-Eval-2024 \[10\]\[20\]\[22\]         | Train and benchmark the image/video deepfake classifier; DeepFake-Eval-2024 stress-tests generalization to real-world content. |
| PII / Sensitive Document Detection | CoNLL-2003 (NER), Enron Email Dataset, Microsoft Presidio synthetic PII corpus | Fine-tune and validate the sensitive-data detection engine on realistic corporate text.                                        |
| Cybersecurity Logs                 | CICIDS2017/2018, UNSW-NB15                                                     | Validate the Threat Intelligence Module's anomaly-correlation logic against labeled attack traffic.                            |

# Part 9 - Cybersecurity Design

## Threat Modeling and Risk

- STRIDE analysis applied per component: Spoofing (voice/identity), Tampering (prompt injection), Repudiation (audit-log integrity), Information Disclosure (prompt leakage), Denial of Service (API abuse), Elevation of Privilege (RBAC bypass).
- Risk assessment scores each threat by likelihood × impact to prioritize controls (e.g., prompt injection and voice spoofing rank highest given current attack trends).
- MITRE ATT&CK mapping is used to align detections with known adversary techniques (e.g., T1585 for impersonation, T1566 for phishing precursors to social engineering).

## Architecture Principles

- Zero Trust Architecture: every request is authenticated and authorized regardless of network origin.
- Defense in Depth: DLP, prompt inspection, and deepfake verification act as independent, overlapping controls.
- Least Privilege: RBAC restricts policy configuration and audit access to authorized security roles.
- Encryption Strategy: AES-256 at rest, TLS 1.3 in transit for all inter-module traffic.

## Compliance Alignment

- NIST Cybersecurity Framework and NIST AI Risk Management Framework (AI RMF / AI 600-1) for AI-specific governance controls \[13\].
- ISO/IEC 27001 for information-security management alignment.
- GDPR data-minimization and purpose-limitation principles applied to redaction and audit-log retention.

# Part 10 - Security Testing

- Penetration testing of the API Gateway, authentication server, and browser extension.
- DLP testing using labeled synthetic-PII datasets to measure detection recall and precision.
- Prompt-injection testing using known adversarial prompt corpora aligned with OWASP LLM01 guidance \[1\]\[2\].
- Deepfake attack simulation using held-out ASVspoof/FaceForensics++ samples not seen during training.
- Social-engineering simulation exercises to validate the risk-scoring and alerting workflow end-to-end.
- API security, authentication, load, and performance testing, plus explicit false-positive-rate testing to protect usability.

# Part 11 - Project Workflow

The end-to-end workflow mirrors the architecture in Part 5: a user prompt or call is intercepted, screened for sensitive data and synthetic-media indicators, evaluated against policy, redacted where necessary, and only then forwarded - with every step generating an audit record visible on the Security Dashboard.

# Part 12 - Novel Contribution

- Arabic-language support for sensitive-data detection and prompt inspection, an area underserved by current global vendors.
- A single Enterprise AI Firewall unifying prompt-level DLP with voice/video deepfake verification - a combination not offered end-to-end by any single reviewed vendor.
- Real-time, pre-transmission prompt protection rather than after-the-fact log review.
- SOC/SIEM-ready integration by design, positioning the platform as a control that plugs into existing security operations rather than a standalone point tool.
- Sector-adaptable policy templates for banking, government, healthcare, telecom, and education.

# Part 13 - Challenges and Limitations

- False positives/negatives: overly strict DLP rules disrupt legitimate work; overly loose rules miss leaks.
- Cross-dataset generalization: deepfake detectors trained on benchmark datasets lose significant accuracy on real-world content, as shown by DeepFake-Eval-2024 \[20\].
- Privacy: inspecting employee prompts and calls must be scoped and logged carefully to avoid becoming invasive surveillance.
- Latency: inline inspection must not introduce noticeable delay to voice calls or AI chat responsiveness.
- Scalability and integration complexity across many AI vendors and communication channels.
- Legal considerations: employee-monitoring policies vary by jurisdiction and must be documented and consented to.

# Part 14 - Future Work

- Cloud-native deployment and a lightweight mobile companion app.
- A browser-independent capture agent for non-Chromium environments.
- Native integrations with email, Microsoft Teams, and Slack.
- SOAR integration for automated incident-response playbooks.
- An LLM-specific firewall layer with continuously updated threat intelligence for new jailbreak techniques.

# Part 15 - Conclusion

This project is a Cybersecurity graduation project because its core engineering contribution is a security architecture - identity and access management, a policy engine, encryption, RBAC, audit logging, SIEM integration, and incident response - built specifically to close a gap left by traditional DLP and access-control systems in the era of generative AI. Machine learning is used strictly as a supporting detection component, in the same way a modern IDS uses anomaly-detection models: the models classify signals, but the security value comes from how those signals are integrated into authentication, policy enforcement, and organizational response. EASP addresses a documented, current gap in the literature and vendor landscape - the absence of a unified platform for AI-prompt DLP and deepfake-based social-engineering defense - while remaining implementable within the scope of an undergraduate cybersecurity capstone.

# References

\[1\] OWASP Foundation, "OWASP Top 10 for LLM Applications 2025," 2025.

\[2\] Mend.io, "2025 OWASP Top 10 for LLM Applications: A Quick Guide," 2025.

\[3\] Microsoft, "Fast-track generative AI security with Microsoft Purview," Microsoft Security Blog, Jan. 2025.

\[4\] Microsoft 365 Message Center, "Microsoft Purview DLP: New inline protection controls for AI apps in Microsoft Edge for Business," 2025.

\[5\] N. Chapple, "Microsoft Purview Browser Extension: Governing AI Shadow IT," 2026.

\[6\] Lasso Security, "Prompt Injection Protection," lasso.security, 2025.

\[7\] Lasso Security, "Lasso Secures GenAI and LLMs with End-to-End Protection," white paper, 2025.

\[8\] Palo Alto Networks, "Palo Alto Networks Introduces Prisma AIRS," press release, Apr. 2025.

\[9\] Palo Alto Networks, "Prisma AIRS 2.0: End-to-End Security Across the AI Lifecycle," press release, Oct. 2025.

\[10\] A. Rössler et al., "FaceForensics++: Learning to Detect Manipulated Facial Images," in Proc. ICCV, 2019.

\[11\] N. Chandra et al., "DeepFake-Eval-2024 Benchmark," arXiv preprint, Mar. 2025.

\[12\] X. Wang et al., "ASVspoof 5: Crowdsourced Speech Data, Deepfakes, and Adversarial Attacks at Scale," in Proc. ASVspoof Workshop, 2024.

\[13\] NIST, "Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile (NIST AI 600-1)," 2024.