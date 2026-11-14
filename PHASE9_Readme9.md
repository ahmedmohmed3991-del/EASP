# Phase 9 - Social Engineering NLP Module (mBERT)

Detects four social-engineering tactics in the text of a phone call:

| Label | Meaning (what the **caller** does) |
|---|---|
| `urgency` | Pushes the other person to act fast or creates fear of a deadline or consequence (act now, account will be closed, "stay on the line", "don't tell anyone"). |
| `authority_impersonation` | Claims or implies an official, organisational or superior identity to gain trust (bank, government, tech company, manager, courier), or insists they are legitimate. |
| `credential_request` | Asks for secrets or identity/access data: password, PIN, one-time code, card details, national ID / SSN, login, remote access to the device. |
| `payment_request` | Asks for money or something equal to money: fees, transfers, gift cards, vouchers, crypto, deposits. |

The labels are **multi-label**: one call can have several tactics, or none.

Model: `bert-base-multilingual-cased` + mean pooling + dropout + one linear layer (4 outputs, sigmoid).
Languages: English and Egyptian Arabic.

> Read section 7 (Known limitations) before relying on the scores. The model was **not** trained or tested on real call recordings.

---

## 1. Quick start (use the trained model)

Put these three files in one folder:

```
phase9_inference.py                  # inference only (no training or data code)
best_mbert_social_engineering.pt     # trained weights (~700 MB)
thresholds.json                      # one threshold per label
```

Install: `pip install torch transformers numpy` (tested with Python 3.11, torch 2.13, transformers 5.15).
The first run downloads the base mBERT weights from Hugging Face (internet needed once; see 4.4 for offline use).

```python
from phase9_inference import build_social_engineering_detector

detector, model, tokenizer = build_social_engineering_detector()   # load ONCE
result = detector.predict("hello this is the security team of your bank, please read me the code we just sent you")

print(result["overall_social_eng_score"])
for label, v in result["predictions"].items():
    print(label, v["score"], v["flagged"])
```

Quick self-test: `python phase9_inference.py` (runs two example sentences).

---

## 2. Input and output contract

**Input:** one string (UTF-8). Arabic, English or mixed. It is the transcript of the call (or a part of it) as produced by the Faster-Whisper STT module (Section 6.4). No speaker tags are needed and none are expected: the model was trained on text with the speaker tags removed.

**Output** (a Python dict; example values are only an illustration of the format):

```python
{
  "text": "<the input>",
  "predictions": {
    "urgency":                 {"score": 0.97, "flagged": True},
    "authority_impersonation": {"score": 0.88, "flagged": True},
    "credential_request":      {"score": 0.95, "flagged": True},
    "payment_request":         {"score": 0.03, "flagged": False}
  },
  "overall_social_eng_score": 0.97      # highest of the four scores
}
```

- `score` = sigmoid probability (0 to 1) of that tactic.
- `flagged` = `score >= threshold` for that label (thresholds come from `thresholds.json`).
- Long transcripts are cut into windows of 120 words (step 60); for each label the **highest** window score is kept. So one dangerous sentence anywhere in the call is enough to flag it.

---

## 3. How it is meant to be used (recommended handling)

- Treat the output as a **warning signal for a human or for a risk engine**, not as proof and not as a reason for automatic blocking.
- `flagged_labels = [l for l, v in result["predictions"].items() if v["flagged"]]` is the simplest alert payload.
- `overall_social_eng_score` is a convenient single number, but it is the maximum of four separate scores, not a calibrated probability of fraud.
- Known weak spots to keep in mind in the UI (see section 7): negated sentences ("no fees", "we will never ask for your PIN") can still raise `payment_request` / `authority_impersonation`; payment requests phrased in unusual words are often missed.

---

## 4. Integration with Phase 10

### 4.1 Where it sits

```
audio -> Faster-Whisper STT (6.4) -> transcript text -> Phase 9 detector -> labels + scores -> Phase 10
```

### 4.2 Minimal service wrapper

```python
# at service start-up (slow: loads ~700 MB of weights)
from phase9_inference import build_social_engineering_detector
detector, _, _ = build_social_engineering_detector()

# per call / per transcript segment
def analyse_transcript(text: str) -> dict:
    out = detector.predict(text)
    return {
        "flagged": [l for l, v in out["predictions"].items() if v["flagged"]],
        "scores": {l: v["score"] for l, v in out["predictions"].items()},
        "overall": out["overall_social_eng_score"],
    }
```

### 4.3 Practical notes

- **Load once.** Do not build the detector for every request.
- **CPU or GPU:** it works on both (it picks CUDA automatically). Latency per call was **not measured**; test it on your hardware before promising real-time behaviour.
- **Streaming calls:** the model was only evaluated on complete texts. If Phase 10 needs live analysis, call `predict` on the transcript collected so far every few seconds. This usage was **not tested**.
- **Thresholds:** keep `thresholds.json` next to the weights. If it is missing, the code falls back to 0.5 for every label.
- **Missing weights:** if `best_mbert_social_engineering.pt` is not found, the builder only prints `[!] No fine-tuned weights found` and continues with an **untrained** head (random scores). Make your service fail loudly in that case, or check that the line `[+] Loaded weights from ...` appears at start-up.
- **Empty or very short text** was not tested; check it in your integration before relying on it.

### 4.4 Offline deployment

The base model is downloaded from Hugging Face on first use. For a machine without internet: run once on a connected machine, then copy the Hugging Face cache folder (`~/.cache/huggingface`) to the target machine, or set `HF_HOME` to a folder that contains it.

---

## 5. How it works

### 5.1 Data (EASP-SE-Corpus)

| Source | What | How it is labelled |
|---|---|---|
| Synthetic calls (`generate_dataset_v2.py`) | 4,000 scripted calls, English + Egyptian Arabic, half scam / half benign, 6 scam types (bank, IT support, manager, delivery, telecom prize, government), 1,912 benign calls are "hard negatives" (they contain words like bank, PIN, transfer but ask for nothing). Splits: train 2,880 / val 360 / test 360 / gold 400. | **By construction**: every scripted line carries the tactics it expresses, saved per turn as `tags`. Scam calls skip stages at random, so tactics appear in different combinations. Benign calls have no tags. |
| External dialogues (BothBosu `multi-agent-scam-conversation`, files `train_data.csv`, `test_data.csv`) | English scam / non-scam dialogues generated by an LLM (1,280 train, 320 test dialogues). | **Keyword rules** applied to the caller's turns only (benign dialogues = all zero). These are proxy labels. Check the dataset's license on its Hugging Face page before redistributing it. |
| Your own sentences (optional `my_lines.csv`) | Hand-written lines, `split=train` goes to training, `split=test` stays hidden for an independent test. | Written by hand. |

Training windows: long dialogues are cut into windows of about 80 to 160 words (labels computed per window). The synthetic training calls are also added once more with **only the caller's lines** (so the model also sees that format).

Final training set: 10,969 windows. Validation: 980. Test: synthetic 360, external 1,510.

### 5.2 Training setup

AdamW (lr 3e-5, weight decay 0.01), linear warm-up (10%) then decay, binary cross-entropy with `pos_weight` (capped at 20), gradient clipping 1.0, dropout 0.3, max length 256 tokens, batch 16 (GPU), up to 6 epochs, early stopping (patience 2) on validation macro-F1. One threshold per label is chosen on the validation set only. The last run used a GPU (Colab T4) and reached its best validation macro-F1 (0.9816) at epoch 6.

### 5.3 Why the evaluation has several parts

A simple word-count model (TF-IDF + logistic regression) is trained on the same data as a **baseline**: if mBERT cannot beat it, mBERT adds nothing. Because the synthetic data comes from templates, a high score on it says very little. So the report also includes: an external test set, a speech-to-text-noise version of every test set, a small hand-written **challenge set** (40 calls whose tactics are said without the usual keywords, plus benign calls full of trigger words), and a human-reviewed gold set.

---

## 6. Results

Macro F1 over the 4 labels (95% bootstrap interval in brackets). Last training run:

| Test | mBERT | TF-IDF baseline | Comment |
|---|---|---|---|
| Synthetic test (360 windows) | 0.999 | 0.986 | Templates: not informative. |
| External test, windows (1,510) | 0.965 (0.956-0.973) | 0.855 | Labels of this set are keyword rules: this is agreement with the rules, not proven accuracy. |
| External test, calls (320) | 0.986 (0.978-0.994) | | A call has a tactic if any window has it. |
| External, windows, STT-style noise | 0.890 (0.874-0.905) | | No punctuation, lower case, 5% words dropped. |
| External, calls, STT-style noise | 0.961 (0.943-0.974) | | |
| Challenge set (40 calls) | 0.632 (0.478-0.733) | 0.465 | Small set, wide interval. Keyword rules alone: 0.39. |
| Human-reviewed gold (104 synthetic calls) | **[fill in: run `--gold_only` on the final weights]** | | The previous training round scored 0.995. |

**Run-to-run variation.** The same configuration trained twice gave challenge-set scores of 0.743 and 0.632 (an earlier configuration: 0.658). Differences of about 0.1 on the challenge set are within noise; do not read them as improvements.

---

## 7. Known limitations (replaces the old Section 6.5)

1. **No real call data.** Everything is synthetic, LLM-generated or hand-written text. Egyptian Arabic exists only as scripted synthetic text. Real speech (hesitations, STT errors, overlapping speakers) may behave differently. The noise test above is only an approximation.
2. **Proxy labels on the external data.** Its labels come from keyword rules, and the model was also trained on part of them. Its high scores mean "agrees with the rules". Human-reviewed external windows are still needed for an honest number.
3. **Synthetic labels are exact by design, but narrow.** The wording comes from templates and a limited set of extra phrasings, so the model is strongest on familiar phrasing and weaker on unusual wording (most clearly `payment_request`: e.g. "move the funds", "settle it with a voucher").
4. **Negation.** "No fees due", "we will never ask for your PIN", "من غير أي رسوم" can still trigger `payment_request` or `authority_impersonation`.
5. **Challenge set is small and not fully independent.** 40 calls, written by an AI assistant, and some of the extra phrasings in the generator are similar in style. Use your own hand-written test sentences (`my_lines.csv`, `split=test`) for an independent check.
6. **One person reviewed the gold set**, and the automatic suggestion was probably visible while reviewing. Agreement between two independent reviewers (Cohen's kappa) has not been measured yet.
7. **Thresholds** are tuned on a validation set where the model is almost perfect, so they are not very precise. They can move between training runs.
8. **Scores are not calibrated probabilities** and the module must not be used for automatic blocking.

Remediation path: collect real, analyst-confirmed Egyptian-Arabic and English call transcripts, label them by two reviewers, add them to training and keep part of them hidden as the main test; add more negation and paraphrase examples; repeat training with several seeds and report mean and standard deviation.

---

## 8. Reproduce, retrain, evaluate

Files: `phase9_all_in_one.py` (data build + training + evaluation), `generate_dataset_v2.py` (synthetic data), `train_data.csv` / `test_data.csv` (external dialogues), optional `my_lines.csv`.

```
pip install torch transformers pandas numpy scikit-learn
python phase9_all_in_one.py --regenerate        # make the synthetic calls, build the corpus, train, evaluate  (use a GPU)
```

Training on a CPU is refused unless you add `--allow_cpu` (it takes many hours). A Colab notebook that does everything with a free T4 GPU (`phase9_colab_v3.ipynb`) is provided.

| Command | What it does |
|---|---|
| `--quick` | Tiny run to check that the pipeline works. |
| `--eval_only` | Load saved weights, tune thresholds, run all evaluations (slow on CPU). |
| `--tune_only` | Load saved weights, re-tune thresholds on the validation set, write `thresholds.json`. |
| `--gold_only --gold FILE.csv` | Fast: evaluate on a hand-reviewed file (columns `reviewed_*`). |
| `--challenge_only` | Fast: evaluate on the 40 challenge calls and list the mistakes. |
| `--sources synthetic` | Ablation: train on synthetic data only (does the external data help?). |
| `--make_review_sheet N` | Write N external windows to a sheet for hand labelling. |
| `--kappa FILE.csv` | Agreement (Cohen's kappa) between two reviewers (`reviewed_*` and `reviewed2_*`). |
| `--no_caller_aug`, `--seed`, `--max_len`, `--epochs`, `--lr`, `--thr` | Training / evaluation options. |

Hand review: open `review_tool.html` in a browser, choose a CSV (for example `gold_review_4labels.csv`), judge what the **caller** does in each text, and download the reviewed CSV.

---

## 9. Files

| File | Purpose | Give to Phase 10? |
|---|---|---|
| `phase9_inference.py` | Load the model and predict. | Yes |
| `best_mbert_social_engineering.pt` | Trained weights. | Yes |
| `thresholds.json` | Per-label thresholds. | Yes |
| `phase9_all_in_one.py` | Data build, training, evaluation, review tools. | No (reproduction) |
| `generate_dataset_v2.py` | Synthetic data generator with per-line tactic tags. | No (reproduction) |
| `review_tool.html` | Browser tool for hand labelling. | No |
| `gold_review_4labels_reviewed.csv` | Human-reviewed gold calls. | No (evidence) |
| `training_log.txt`, `corpus_report.txt`, `challenge_set.csv` | Run log, data statistics, challenge calls. | No (evidence) |

---

## 10. Roadmap tasks

| Task | What was done |
|---|---|
| T-P09-042 | `SocialEngineeringmBERT` + `SocialEngineeringDetector`, builder `build_social_engineering_detector()`. |
| T-P09-043 | Corpus build (synthetic + external + optional own sentences), windows, splits. |
| T-P09-044 | Training with validation-based epoch selection and early stopping. |
| T-P09-045 | Evaluation: per-label precision/recall/F1, bootstrap intervals, baseline, STT-noise, challenge set, gold. |
| T-P09-046 | Known limitations (section 7). |

Note: the first version of this phase trained on the SMS Spam Collection with keyword proxy labels (macro-F1 0.73 on its own test set). That dataset and those numbers are replaced by the corpus and results above and are not comparable.

---

## 11. Next steps (if time allows)

1. Hand-review 50 to 100 external windows (and a second reviewer for kappa).
2. Write 30 to 40 own test sentences (`my_lines.csv`, `split=test`) for an independent check.
3. Run the ablation (`--sources synthetic`) to show whether the external data helps.
4. Train with 3 seeds and report mean and standard deviation.
5. Add negation and payment-paraphrase examples, retrain, compare on the independent test sentences.
