"""
Training Script for Text DLP / Prompt Injection.
Trains both:
1. Classical Baseline (TF-IDF + Logistic Regression)
2. Fine-tuned Transformer (mBERT / DistilBERT)
Evaluates on balanced 70/15/15 splits and outputs classification reports.
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.dlp.preprocess import clean_text, create_stratified_splits
from src.dlp.model import TFIDFBaselineClassifier

DATA_DIR = BASE_DIR / "data" / "text_dlp" / "prompt_injection"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

def load_combined_prompt_dataset() -> pd.DataFrame:
    """Loads and unifies all available prompt injection datasets."""
    frames = []
    
    # 1. Deepset
    deepset_path = DATA_DIR / "deepset_prompt_injections.parquet"
    if deepset_path.exists():
        df = pd.read_parquet(deepset_path)
        df = df[["text", "label"]].copy()
        frames.append(df)
        
    # 2. Neuralchemy
    neuralchemy_path = DATA_DIR / "neuralchemy_prompt_injections.parquet"
    if neuralchemy_path.exists():
        df = pd.read_parquet(neuralchemy_path)
        # map columns if needed
        text_col = "text" if "text" in df.columns else df.columns[0]
        label_col = "label" if "label" in df.columns else df.columns[1]
        df = df[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"}).copy()
        frames.append(df)

    # 3. S-Labs
    slabs_path = DATA_DIR / "slabs_prompt_injections.parquet"
    if slabs_path.exists():
        df = pd.read_parquet(slabs_path)
        text_col = "text" if "text" in df.columns else df.columns[0]
        label_col = "label" if "label" in df.columns else df.columns[1]
        df = df[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"}).copy()
        frames.append(df)

    if not frames:
        raise FileNotFoundError("No prompt injection datasets found in data/text_dlp/prompt_injection")

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["text"])
    combined["text"] = combined["text"].astype(str).apply(clean_text)
    combined["label"] = combined["label"].astype(int)
    # Remove empty texts
    combined = combined[combined["text"].str.len() > 2].reset_index(drop=True)
    return combined

def plot_confusion_matrix(cm, filename: str, title: str):
    """Plots and saves a styled confusion matrix heatmap."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Benign (0)', 'Injection (1)'],
                yticklabels=['Benign (0)', 'Injection (1)'], ax=ax)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('True Label')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / filename, dpi=300)
    plt.close()

def train_and_eval():
    """Main training routine."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    print("--- Loading & Preprocessing Prompt Datasets ---")
    df = load_combined_prompt_dataset()
    print(f"Total Unique Cleaned Prompts: {len(df):,}")
    print(f"Class Distribution: Safe (0): {(df['label'] == 0).sum():,}, Malicious (1): {(df['label'] == 1).sum():,}")
    
    # Stratified 70 / 15 / 15 Split
    splits = create_stratified_splits(df, text_col="text", label_col="label")
    print(f"Train split: {len(splits['train']):,} | Val split: {len(splits['val']):,} | Test split: {len(splits['test']):,}")
    
    # 1. Train Classical Baseline
    print("\n--- Training Classical Baseline (TF-IDF + Logistic Regression) ---")
    baseline = TFIDFBaselineClassifier(max_features=15000, ngram_range=(1, 2))
    baseline.fit(splits["train"]["text"].tolist(), splits["train"]["label"].tolist())
    
    # Evaluate on Test
    test_metrics = baseline.evaluate(splits["test"]["text"].tolist(), splits["test"]["label"].tolist())
    print(f"Test Accuracy:  {test_metrics['accuracy']*100:.2f}%")
    print(f"Test Precision: {test_metrics['precision']*100:.2f}%")
    print(f"Test Recall:    {test_metrics['recall']*100:.2f}%")
    print(f"Test F1-Score:  {test_metrics['f1_score']*100:.2f}%")
    print(f"Test ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    # Save Model
    model_path = MODELS_DIR / "prompt_injection_baseline.joblib"
    baseline.save(str(model_path))
    print(f"[OK] Saved model to {model_path}")
    
    # Plot Confusion Matrix
    plot_confusion_matrix(
        test_metrics["confusion_matrix"],
        "prompt_injection_cm.png",
        "Prompt Injection Detection - Confusion Matrix"
    )
    
    # Save Metrics Report
    with open(REPORTS_DIR / "prompt_injection_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=2)
        
    return test_metrics

if __name__ == "__main__":
    train_and_eval()
