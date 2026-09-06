"""
Model architectures and baseline classifiers for Text DLP / Prompt Injection Detection.
Includes:
- Classical Baseline: TF-IDF + Logistic Regression / SGD
- Transformer Classifier: mBERT / DistilBERT Fine-tuning wrapper
- Performance evaluation metrics (Acc, Precision, Recall, F1, ROC-AUC)
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix

class TFIDFBaselineClassifier:
    """Classical baseline for fast inference & benchmark comparison."""
    def __init__(self, max_features: int = 10000, ngram_range: Tuple[int, int] = (1, 2), C: float = 1.0):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True
        )
        self.model = LogisticRegression(C=C, max_iter=1000, random_state=42)
        
    def fit(self, texts: list, labels: list):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        return self
        
    def predict_proba(self, texts: list) -> np.ndarray:
        X = self.vectorizer.transform(texts)
        return self.model.predict_proba(X)[:, 1] # Probability of malicious class
        
    def predict(self, texts: list, threshold: float = 0.5) -> np.ndarray:
        probas = self.predict_proba(texts)
        return (probas >= threshold).astype(int)
        
    def evaluate(self, texts: list, labels: list) -> Dict[str, float]:
        probas = self.predict_proba(texts)
        preds = (probas >= 0.5).astype(int)
        acc = accuracy_score(labels, preds)
        p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
        try:
            auc = roc_auc_score(labels, probas)
        except Exception:
            auc = 0.5
        cm = confusion_matrix(labels, preds).tolist()
        return {
            "accuracy": float(acc),
            "precision": float(p),
            "recall": float(r),
            "f1_score": float(f1),
            "roc_auc": float(auc),
            "confusion_matrix": cm
        }
        
    def save(self, filepath: str):
        joblib.dump({"vectorizer": self.vectorizer, "model": self.model}, filepath)
        
    @classmethod
    def load(cls, filepath: str):
        data = joblib.load(filepath)
        instance = cls()
        instance.vectorizer = data["vectorizer"]
        instance.model = data["model"]
        return instance

def build_transformer_classifier(model_name: str = "bert-base-multilingual-cased", num_labels: int = 2):
    """Initializes AutoModelForSequenceClassification from Hugging Face."""
    from transformers import AutoModelForSequenceClassification
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels
    )
    return model
