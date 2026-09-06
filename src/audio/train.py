"""
Optimized Fast Training & Evaluation Pipeline for Voice Deepfake Audio Detection.
Extracts and caches Log-Mel Spectrogram features for all 1,866 real audio files,
trains 2D Spectrogram CNN, and evaluates Accuracy, F1, Equal Error Rate (EER), and ROC-AUC.
"""
import os
import sys
from pathlib import Path

# Silence CUDA warning for sm_120 architecture until PyTorch adds native sm_120 wheels
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import soundfile as sf
import librosa
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, roc_auc_score, accuracy_score, precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.audio.model import AudioDeepfakeCNN, compute_eer

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
CACHE_FILE = DATA_DIR / "audio_deepfake" / "in_the_wild" / "features_cache.npz"

def extract_single_audio_feature(filepath: str, target_sr: int = 16000, duration: float = 4.0, n_mels: int = 64):
    """Fast extraction of Log-Mel spectrogram using soundfile."""
    try:
        data, sr = sf.read(filepath)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        if sr != target_sr:
            data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=target_sr)
        target_len = int(target_sr * duration)
        if len(data) < target_len:
            data = np.pad(data, (0, target_len - len(data)), mode="constant")
        else:
            data = data[:target_len]
        
        mel = librosa.feature.melspectrogram(y=data, sr=target_sr, n_fft=1024, hop_length=512, n_mels=n_mels)
        log_mel = librosa.power_to_db(mel, ref=np.max)
        log_mel_norm = (log_mel - log_mel.min()) / (log_mel.max() - log_mel.min() + 1e-8) * 2.0 - 1.0
        return log_mel_norm.astype(np.float32)
    except Exception as e:
        return np.zeros((n_mels, int(target_sr * duration // 512) + 1), dtype=np.float32)

def get_or_create_audio_features():
    """Extracts features for all 1,866 real audio files and caches to disk."""
    if CACHE_FILE.exists():
        print(f"[CACHE] Loading pre-extracted audio features from: {CACHE_FILE.name}")
        data = np.load(CACHE_FILE)
        return data["X"], data["y"], data["filenames"]
        
    meta_path = DATA_DIR / "audio_deepfake" / "in_the_wild" / "meta.csv"
    df = pd.read_csv(meta_path)
    df["full_path"] = df["filename"].apply(lambda p: str(BASE_DIR / p))
    df = df[df["full_path"].apply(os.path.exists)].reset_index(drop=True)
    
    print(f"[EXTRACT] Extracting Log-Mel Spectrograms for {len(df):,} real audio files...")
    features, labels, valid_paths = [], [], []
    for i, row in df.iterrows():
        spec = extract_single_audio_feature(row["full_path"])
        features.append(spec)
        labels.append(row["label"])
        valid_paths.append(row["filename"])
        if (i + 1) % 200 == 0 or (i + 1) == len(df):
            print(f"  --> Processed {i + 1:,} / {len(df):,} audio files ({(i+1)/len(df)*100:.1f}%)")
            
    X = np.array(features) # Shape: (N, 64, 126)
    y = np.array(labels)   # Shape: (N,)
    
    np.savez_compressed(CACHE_FILE, X=X, y=y, filenames=valid_paths)
    print(f"[CACHE] Saved {len(X)} spectrograms to {CACHE_FILE}")
    return X, y, valid_paths

def train_audio_model(epochs: int = 10, batch_size: int = 32, lr: float = 1e-3):
    """Full neural training pipeline on all real audio recordings."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    X, y, filenames = get_or_create_audio_features()
    # Add channel dimension: (N, 1, 64, 126)
    X = np.expand_dims(X, axis=1)
    
    print(f"\n[DATASET] Total Samples: {len(X)} | Bona Fide: {sum(y==0)} | Deepfake: {sum(y==1)}")
    
    # 70/15/15 Stratified Split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42)
    
    print(f"Train Set: {len(X_train)} | Val Set: {len(X_val)} | Test Set: {len(X_test)}")
    
    # Convert to PyTorch Tensor Loaders
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long))
    test_dataset = TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(y_test, dtype=torch.long))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    model = AudioDeepfakeCNN(in_channels=1, num_classes=2, dropout=0.3)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    
    print("\n--- Training Audio Deepfake 2D CNN ---")
    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss, correct, total = 0.0, 0, 0
        for X_b, y_b in train_loader:
            optimizer.zero_grad()
            outputs = model(X_b)
            loss = criterion(outputs, y_b)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * len(y_b)
            _, preds = torch.max(outputs, 1)
            correct += (preds == y_b).sum().item()
            total += len(y_b)
            
        train_acc = correct / total
        avg_loss = train_loss / total
        
        # Validation
        model.eval()
        v_loss, v_correct, v_total = 0.0, 0, 0
        with torch.no_grad():
            for X_v, y_v in val_loader:
                v_out = model(X_v)
                v_l = criterion(v_out, y_v)
                v_loss += v_l.item() * len(y_v)
                _, v_p = torch.max(v_out, 1)
                v_correct += (v_p == y_v).sum().item()
                v_total += len(y_v)
                
        val_acc = v_correct / v_total
        avg_v_loss = v_loss / v_total
        
        print(f"Epoch [{epoch:02d}/{epochs:02d}] | Train Loss: {avg_loss:.4f} | Train Acc: {train_acc*100:.2f}% | Val Loss: {avg_v_loss:.4f} | Val Acc: {val_acc*100:.2f}%")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODELS_DIR / "audio_deepfake_cnn.pt")
            
    print(f"\n[OK] Model successfully trained and saved: {MODELS_DIR / 'audio_deepfake_cnn.pt'}")
    
    # Final Test Set Evaluation
    model.load_state_dict(torch.load(MODELS_DIR / "audio_deepfake_cnn.pt"))
    model.eval()
    
    all_preds, all_probs = [], []
    with torch.no_grad():
        for X_t, _ in test_loader:
            out = model(X_t)
            probs = torch.softmax(out, dim=1)[:, 1].numpy()
            _, p = torch.max(out, 1)
            all_probs.extend(probs)
            all_preds.extend(p.numpy())
            
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)
    
    acc = accuracy_score(y_test, all_preds)
    p, r, f1, _ = precision_recall_fscore_support(y_test, all_preds, average="binary")
    auc = roc_auc_score(y_test, all_probs)
    
    bonafide_scores = 1.0 - all_probs[y_test == 0]
    spoof_scores = 1.0 - all_probs[y_test == 1]
    eer_val, eer_thresh = compute_eer(bonafide_scores, spoof_scores)
    
    print("\n" + "=" * 60)
    print("=== FINAL TEST RESULTS ON 100% UNSEEN REAL RECORDINGS ===")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Precision: {p*100:.2f}%")
    print(f"Recall:    {r*100:.2f}%")
    print(f"F1-Score:  {f1*100:.2f}%")
    print(f"ROC-AUC:   {auc:.4f}")
    print(f"Equal Error Rate (EER): {eer_val:.2f}%")
    print("=" * 60)
    
    # Save Confusion Matrix and ROC plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    cm = confusion_matrix(y_test, all_preds)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax1,
                xticklabels=["Bona Fide (0)", "Deepfake (1)"], yticklabels=["Bona Fide (0)", "Deepfake (1)"])
    ax1.set_title("Voice Deepfake — Confusion Matrix (Test Set)", fontweight="bold")
    ax1.set_xlabel("Predicted")
    ax1.set_ylabel("True Ground Truth")
    
    fpr, tpr, _ = roc_curve(y_test, all_probs)
    ax2.plot(fpr, tpr, color="#2563eb", lw=2, label=f"2D CNN (AUC = {auc:.4f})")
    ax2.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--")
    ax2.scatter([eer_val/100.0], [1.0 - eer_val/100.0], color="#dc2626", s=70, zorder=5, label=f"EER ({eer_val:.2f}%)")
    ax2.set_title("Voice Deepfake — ROC & EER Analysis", fontweight="bold")
    ax2.set_xlabel("False Positive Rate (FPR)")
    ax2.set_ylabel("True Positive Rate (TPR)")
    ax2.legend(loc="lower right")
    ax2.grid(True, linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    plot_path = FIGURES_DIR / "voice_deepfake_real_test_roc.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"[PLOT] Saved evaluation curve to: {plot_path}")
    
    return {
        "accuracy": float(acc),
        "precision": float(p),
        "recall": float(r),
        "f1": float(f1),
        "auc": float(auc),
        "eer": float(eer_val)
    }

if __name__ == "__main__":
    train_audio_model(epochs=10, batch_size=32)
