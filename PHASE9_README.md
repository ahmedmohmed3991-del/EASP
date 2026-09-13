# Phase 9 — Social Engineering NLP Module (mBERT)

## 6.5 Known Limitations — Domain Gap

The mBERT multi-label classifier (Section 6.4) was trained on labels
(urgency, authority_impersonation, credential_request, payment_request)
that are **proxy-derived**, not hand-annotated by security analysts on
real call transcripts. Labels were generated via regex pattern matching
applied to the SMS Spam Collection dataset — a written, English-only,
text-message corpus, not spoken vishing call transcripts.

## Evaluation Results (held-out test set, 1,115 samples)

| Label                     | Precision | Recall | F1-score | Support |
|---------------------------|-----------|--------|----------|---------|
| urgency                   | 0.73      | 0.77   | 0.75     | 88      |
| authority_impersonation   | 0.30      | 0.67   | 0.41     | 9       |
| credential_request        | 1.00      | 0.75   | 0.86     | 8       |
| payment_request           | 0.83      | 0.94   | 0.88     | 128     |
| **Macro F1**              |           |        | **0.73** | 233     |
| **Micro F1**              |           |        | **0.80** | 233     |

## Impact on Model Reliability

- Overall performance is strong (Micro F1 = 0.80), validating the
  architecture and the class-weighted training approach (`pos_weight`,
  capped at 20x) for handling label imbalance.
- `authority_impersonation` remains the weakest label (F1 = 0.41) due to
  severe under-representation in the source data (only 9 of 1,115 test
  samples), which is expected given the regex-based proxy labeling and
  the rarity of explicit authority-impersonation phrasing in SMS spam text.
- Stylistic domain gap: written SMS/spam text differs structurally from
  spoken, transcribed speech (the actual production input, sourced from
  the Faster-Whisper STT module in Section 6.4). Strong performance on
  this proxy dataset does not guarantee equivalent performance on real
  vishing call transcripts.

## Remediation Path

Replace or augment the proxy-labeled dataset with either real
analyst-confirmed vishing call transcripts or the Synthetic Scripted
Call Dialogues described in Section 6.1, with particular focus on
collecting more `authority_impersonation` examples, followed by
re-training/fine-tuning before production deployment.

## Artifacts

- Trained weights: `best_mbert_social_engineering.pt` (saved at epoch 2,
  lowest validation loss)
- Training log: 3 epochs, CPU, final train loss 0.2581, best val loss 0.2711
- Tasks completed: T-P09-042, T-P09-043, T-P09-044, T-P09-045, T-P09-046
