"""
Phase 9 — mBERT + Classification Head (Social Engineering) — STANDALONE VERSION
Run with: python mbert.py
Requires: torch, transformers, pandas, numpy, scikit-learn, spam.csv (same folder)
"""

import os
import re
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

# ============================================================
# BASE SETUP (normally comes from earlier notebook cells)
# ============================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[+] Using device: {DEVICE}")

LABELS = ["urgency", "authority_impersonation", "credential_request", "payment_request"]

LABEL_THRESHOLDS = {
    "urgency": 0.50,
    "authority_impersonation": 0.35,
    "credential_request": 0.35,
    "payment_request": 0.50,
}


class SocialEngineeringmBERT(nn.Module):
    def __init__(self, model_name: str = "bert-base-multilingual-cased", num_labels: int = 4, dropout: float = 0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.dropout(outputs.pooler_output)
        return self.classifier(pooled)


class SocialEngineeringDetector:
    def __init__(self, model: nn.Module, tokenizer, device=DEVICE):
        self.device = device
        self.tokenizer = tokenizer
        self.model = model.to(self.device)
        self.model.eval()

    def predict(self, text: str, thresholds: dict = None) -> dict:
        thresholds = thresholds or LABEL_THRESHOLDS
        inputs = self.tokenizer(text, truncation=True, max_length=128, padding="max_length", return_tensors="pt")
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()
            probs = np.atleast_1d(probs)

        results = {}
        for idx, label in enumerate(LABELS):
            prob = float(probs[idx])
            results[label] = {"score": round(prob, 4), "flagged": bool(prob >= thresholds[label])}

        return {"text": text, "predictions": results, "overall_social_eng_score": round(float(np.max(probs)), 4)}


def map_to_multilabels(row):
    text = str(row["text"]).lower()
    is_spam = 1 if row["target"] == "spam" else 0
    if not is_spam:
        return [0, 0, 0, 0]

    urgency = 1 if re.search(r"\b(urgent|immediately|now|expire|expires|hurry|today|last chance|warning|alert)\b", text) else 0
    authority = 1 if re.search(r"\b(admin|support|bank|official|team|security|manager|service|headquarters)\b", text) else 0
    credential = 1 if re.search(r"\b(password|pin|code|otp|verify|account|login|details|credentials)\b", text) else 0
    payment = 1 if re.search(r"\b(free|prize|won|win|cash|claim|cost|rate|credit|payment|money|transfer|\$|£)\b", text) else 0

    if urgency == 0 and authority == 0 and credential == 0 and payment == 0:
        urgency = 1
        payment = 1
    return [urgency, authority, credential, payment]


class SocialEngineeringDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        inputs = self.tokenizer(text, max_length=self.max_len, padding="max_length", truncation=True, return_tensors="pt")
        return {
            "input_ids": inputs["input_ids"].flatten(),
            "attention_mask": inputs["attention_mask"].flatten(),
            "labels": torch.tensor(self.labels[item], dtype=torch.float),
        }


def train_social_eng_model(model, data_loader, val_loader=None, epochs=3, lr=2e-5, pos_weight=None, device=DEVICE):
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device) if pos_weight is not None else None)
    model.train()
    best_val_loss = float("inf")
    print(f"[*] Starting Training for {epochs} Epochs on {device}...")
    for epoch in range(epochs):
        total_loss = 0.0
        for batch in data_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(data_loader)
        log_line = f"Epoch [{epoch + 1}/{epochs}] - Train Loss: {avg_loss:.4f}"

        if val_loader is not None:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch in val_loader:
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)
                    labels = batch["labels"].to(device)
                    logits = model(input_ids, attention_mask)
                    val_loss += criterion(logits, labels).item()
            val_loss /= len(val_loader)
            log_line += f" - Val Loss: {val_loss:.4f}"
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), "best_mbert_social_engineering.pt")
                log_line += "  [best model saved]"
            model.train()

        print(log_line)
    print("[+] Model Training Completed.")


def evaluate_model(model, test_loader, thresholds: dict = None, device=DEVICE):
    thresholds = thresholds or LABEL_THRESHOLDS
    threshold_vec = np.array([thresholds[l] for l in LABELS])

    model.eval()
    all_probs, all_targets = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].numpy()
            logits = model(input_ids, attention_mask)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_probs.extend(probs)
            all_targets.extend(labels)

    all_probs = np.array(all_probs)
    all_targets = np.array(all_targets)
    all_preds = (all_probs >= threshold_vec).astype(int)

    print("\n" + "=" * 50)
    print("      NLP SOCIAL ENGINEERING EVALUATION REPORT      ")
    print("=" * 50)
    print(classification_report(all_targets, all_preds, target_names=LABELS, zero_division=0))
    print(f"Macro F1-Score: {f1_score(all_targets, all_preds, average='macro', zero_division=0):.4f}")
    print(f"Micro F1-Score: {f1_score(all_targets, all_preds, average='micro', zero_division=0):.4f}")
    print("=" * 50)
    return all_probs, all_targets


# ============================================================
# PHASE 9 — mBERT + CLASSIFICATION HEAD (SOCIAL ENGINEERING)
# ============================================================

# --- T-P09-042 ---
def build_social_engineering_detector(model_name="bert-base-multilingual-cased", device=DEVICE):
    tok = AutoTokenizer.from_pretrained(model_name)
    model = SocialEngineeringmBERT(model_name=model_name, num_labels=len(LABELS))
    weights_path = "best_mbert_social_engineering.pt"
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device))
        print(f"[+] Loaded fine-tuned weights from '{weights_path}'.")
    else:
        print(f"[!] No fine-tuned weights found — using base (untrained) mBERT head.")
    return SocialEngineeringDetector(model=model, tokenizer=tok, device=device), model, tok


# --- T-P09-043 ---
def load_sms_spam_dataset(csv_path="spam.csv", tokenizer=None, batch_size=None):
    df = pd.read_csv(csv_path, encoding="latin-1")
    df = df.rename(columns={"v1": "target", "v2": "text"})[["text", "target"]]
    df["labels"] = df.apply(map_to_multilabels, axis=1)

    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["target"])
    train_ds = SocialEngineeringDataset(train_df["text"].values, train_df["labels"].values, tokenizer)
    test_ds = SocialEngineeringDataset(test_df["text"].values, test_df["labels"].values, tokenizer)

    bs = batch_size or (16 if torch.cuda.is_available() else 8)
    train_dl = DataLoader(train_ds, batch_size=bs, shuffle=True)
    test_dl = DataLoader(test_ds, batch_size=bs, shuffle=False)

    train_labels_arr = np.array(train_df["labels"].tolist())
    pos_counts = train_labels_arr.sum(axis=0)
    neg_counts = train_labels_arr.shape[0] - pos_counts
    pw = torch.tensor(np.clip(neg_counts / np.clip(pos_counts, 1, None), 1.0, 20.0), dtype=torch.float32)
    return train_dl, test_dl, pw


# --- T-P09-044 ---
def run_social_engineering_training(model, train_loader, test_loader, pos_weight, force_retrain=False, epochs=3):
    weights_path = "best_mbert_social_engineering.pt"
    if os.path.exists(weights_path) and not force_retrain:
        print(f"[+] T-P09-044 skipped: weights already exist at '{weights_path}'.")
        model.load_state_dict(torch.load(weights_path, map_location=DEVICE))
        return
    train_social_eng_model(model, train_loader, val_loader=test_loader, epochs=epochs, pos_weight=pos_weight)
    print("[+] T-P09-044 done.")


# --- T-P09-046 ---
PHASE9_DOMAIN_GAP_NOTE = """
[DOMAIN GAP NOTE — T-P09-046]
Labels are proxy-derived via regex from SMS Spam Collection text, not
hand-annotated call transcripts. See SRS Section 6.5 for full write-up.
"""

if __name__ == "__main__":
    se_detector, se_model, se_tokenizer = build_social_engineering_detector()
    print("[+] T-P09-042 done.")

    se_train_loader, se_test_loader, se_pos_weight = load_sms_spam_dataset(tokenizer=se_tokenizer)
    print(f"[+] T-P09-043 done: {len(se_train_loader.dataset)} train / {len(se_test_loader.dataset)} test.")

    run_social_engineering_training(se_model, se_train_loader, se_test_loader, se_pos_weight, force_retrain=False)

    evaluate_model(se_model, se_test_loader, thresholds=LABEL_THRESHOLDS)
    print("[+] T-P09-045 done.")

    print(PHASE9_DOMAIN_GAP_NOTE)

    print("=" * 60)
    print("✓ PHASE 9 COMPLETED")
    print("=" * 60)
