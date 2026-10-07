# Social Engineering Classifier Domain-Gap Documentation (Task T-P09-046)

**Module**: `ai_service/social_engineering/`  
**Model Architecture**: mBERT (`bert-base-multilingual-cased`) with 4-class multi-label head  
**Author**: AI 3 Lead / EASP AI Track  
**Source Baseline**: EASP Chapter 1 Final v2.0 §6.5 & EASP Task Book v1.0 Table 25

---

## 1. Description of Domain Gap
The training and initial tuning labels for the social engineering detection branch are proxy-derived from text-based messaging corpora (such as the SMS Spam Collection, Enron Email, and synthesized phishing dialogues). 

**The Key Domain Gap**:
1. **Written Text vs. Spoken Dialogue**: SMS and email messages are concise, written asynchronously, and often exhibit explicit textual spam markers (e.g., links, shortcodes, imperative call-to-actions). Real spoken social engineering attacks (vishing, telephone pretexting) involve conversational disfluencies, pauses, social niceties, ambient acoustic noise, and gradual rapport-building before introducing coercive demands.
2. **Transcription Error Propagation**: Speech-to-Text models (Faster-Whisper) may introduce acoustic transcription errors, misrecognize technical jargon, or drop subtle phonemes, creating an out-of-distribution input for standard text classifiers.
3. **Multi-Label Proxy Heuristics**: Labels (`urgency`, `authority_impersonation`, `credential_request`, `payment_request`) are assigned via keyword/regex mapping over raw spam corpora rather than hand-annotated human psychological deception tags.

---

## 2. Mitigation Strategy & Defense Narrative
* **Calibrated Thresholds**: As established in notebook Cell 2 and implemented in `model.py`, lower decision thresholds (0.35) are applied to rarer categories (`authority_impersonation`, `credential_request`) to prioritize Recall over Precision, minimizing false negatives on coercive attacks.
* **Academic Honesty**: As required by project guidelines, evaluation metrics (Precision, Recall, F1) reflect this proxy training regime and must **never be overstated** as human-evaluated conversational speech ground truth.
* **Future Work Classification**: Fine-tuning on genuine, hand-annotated enterprise voice call transcripts remains formally classified as Future Work.
