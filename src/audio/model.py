"""
Model architectures and evaluation for Voice Deepfake Detection.
Includes:
- 2D Spectrogram CNN Classifier
- Equal Error Rate (EER) and minDCF computation
- PyTorch Dataset & Evaluator
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sklearn.metrics import roc_curve, accuracy_score, precision_recall_fscore_support, roc_auc_score
from typing import Dict, Any, Tuple

def compute_eer(bonafide_scores: np.ndarray, spoof_scores: np.ndarray) -> Tuple[float, float]:
    """
    Computes Equal Error Rate (EER) and optimal threshold for anti-spoofing evaluation.
    EER is the point where False Acceptance Rate (FAR) == False Rejection Rate (FRR).
    """
    labels = np.concatenate([np.ones_like(bonafide_scores), np.zeros_like(spoof_scores)])
    scores = np.concatenate([bonafide_scores, spoof_scores])
    
    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1 - tpr
    
    # Find the threshold where FPR and FNR are closest
    idx = np.nanargmin(np.abs(fpr - fnr))
    eer = (fpr[idx] + fnr[idx]) / 2.0
    threshold = thresholds[idx]
    
    return float(eer * 100.0), float(threshold) # Returns EER as percentage

class AudioDeepfakeCNN(nn.Module):
    """
    2D CNN architecture tailored for Log-Mel Spectrogram deepfake voice classification.
    Processes (Batch, 1, Mel_Bins, Time_Steps) -> Binary logits (Bona fide vs Deepfake).
    """
    def __init__(self, in_channels: int = 1, num_classes: int = 2, dropout: float = 0.3):
        super().__init__()
        
        # Block 1
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        
        # Block 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        
        # Block 3
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        
        # Block 4
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Classification Head
        self.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (B, 1, H, W)
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = F.relu(self.bn4(self.conv4(x)))
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        logits = self.fc(x)
        return logits
