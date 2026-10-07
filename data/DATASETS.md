# EASP Dataset Tracking & Licensing Verification Sheet (T-P00-002 / T-P00-003)

**Platform**: Enterprise AI Security Platform (EASP)  
**Track**: AI / Data Science (AI 4 Lead)  
**Standard**: 8-Field Documentation Specification (Name, Source, Purpose, Data Type, Labels, Intended Component, Split Usage, Limitations & Licensing)

---

## 1. ASVspoof 2019 / 2021 (Logical Access)
* **Full Name**: Automatic Speaker Verification Spoofing and Countermeasures Challenge (ASVspoof 2019 LA / 2021 LA)
* **Source & URL**: Datashare Edinburgh / Speech@FIT (`https://www.asvspoof.org/`)
* **Purpose**: Primary training and benchmark corpus for voice anti-spoofing and logical access deepfake detection.
* **Data Type**: Audio files (.flac / .wav), 16 kHz, single-channel mono PCM.
* **Labels**: Binary (`bonafide` vs. `spoof`), with algorithm tags (A01–A19: TTS, voice conversion, neural vocoders).
* **Intended Component**: RawNet2 Voice Deepfake Detector (`ai_service/voice_deepfake/rawnet2.py`).
* **Split Usage**: Standard protocol partitions: Train (2,580 bonafide, 22,800 spoof), Dev (2,548 bonafide, 22,296 spoof), Eval (real unseen attacks).
* **Limitations & License**: Academic research license. Prohibits commercial redistribution. Audio contains specific acoustic characteristics of challenge recording setup; cross-dataset generalization gap exists for telephony/VoIP.

---

## 2. WaveFake Dataset
* **Full Name**: WaveFake: A Data Set to Facilitate Audio Deepfake Detection
* **Source & URL**: Frank & Schönherr (2021), Zenodo (`https://zenodo.org/record/5642694`)
* **Purpose**: Secondary benchmark to evaluate RawNet2 against modern neural vocoders (MelGAN, Parallel WaveGAN, Multi-band MelGAN, WaveGlow).
* **Data Type**: 16 kHz 16-bit PCM WAV audio.
* **Labels**: Synthetic spoof vs original bonafide (from LJSpeech and JSUT).
* **Intended Component**: Voice Deepfake Cross-Architecture Evaluation (`tests/ai_evaluation/voice_eval.py`).
* **Split Usage**: Evaluation set only (10% sample subset reserved for out-of-distribution evaluation).
* **Limitations & License**: Creative Commons Attribution 4.0 International (CC BY 4.0). English and Japanese only.

---

## 3. SMS Spam Collection
* **Full Name**: SMS Spam Collection v.1
* **Source & URL**: UCI Machine Learning Repository / Tiago A. Almeida (`https://archive.ics.uci.edu/dataset/228/sms+spam+collection`)
* **Purpose**: Baseline text corpus for social engineering and phishing pattern analysis.
* **Data Type**: Plain text messages (5,574 English SMS messages).
* **Labels**: Heuristically mapped multi-labels: `urgency`, `authority_impersonation`, `credential_request`, `payment_request`.
* **Intended Component**: mBERT Social Engineering Classifier (`ai_service/social_engineering/`).
* **Split Usage**: 70% Train, 15% Validation, 15% Test.
* **Limitations & License**: Public domain / Open academic use. **CRITICAL DOMAIN GAP**: SMS messages are concise and written, differing syntactically from transcribed spoken phone conversations (Chapter 1 §6.5).

---

## 4. Enron Email Dataset
* **Full Name**: Enron Email Corpus
* **Source & URL**: CMU / FERC Public Records (`https://www.cs.cmu.edu/~enron/`)
* **Purpose**: Natural enterprise email corpus used to calibrate false-positive rates (FPR) on benign enterprise communication.
* **Data Type**: MIME/plain text email bodies.
* **Labels**: Benign enterprise text vs synthetic injected spear-phishing samples.
* **Intended Component**: False Positive Rate (FPR) stress testing for both DLP and mBERT.
* **Split Usage**: Test and validation calibration only.
* **Limitations & License**: Public record. Outdated conversational style (early 2000s), lacks modern cloud SaaS terminology.

---

## 5. ai4privacy / pii-masking-200k
* **Full Name**: AI4Privacy Multilingual PII Masking Dataset (200k)
* **Source & URL**: HuggingFace (`ai4privacy/pii-masking-200k`)
* **Purpose**: Evaluation and validation of sensitive PII detection (Names, Addresses, Phone Numbers, Tax IDs, IBANs).
* **Data Type**: Multilingual synthetic sentences with token-level character-span annotations.
* **Labels**: Presidio-compatible entity classes (`PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `IBAN_CODE`, `LOCATION`, `IP_ADDRESS`).
* **Intended Component**: DLP Microservice benchmark (`ai_service/dlp/`).
* **Split Usage**: Evaluation sample only (never mixed into training splits).
* **Limitations & License**: Apache 2.0. Synthetic sentences; requires custom regex recognizers for platform-specific tokens (API keys, JWTs).

---

## 6. CoNLL-2003 Language Independent Named Entity Recognition
* **Full Name**: CoNLL-2003 NER Dataset (English)
* **Source & URL**: Tjong Kim Sang & De Meulder (2003)
* **Purpose**: Validation of spaCy NER entity tagging for enterprise names and organizations.
* **Data Type**: Reuters news stories tokenized with IOB tags.
* **Labels**: `PER`, `ORG`, `LOC`, `MISC`.
* **Intended Component**: spaCy NER verification pipeline.
* **Split Usage**: Validation/Test.
* **Limitations & License**: Open for academic evaluation. News domain bias.
