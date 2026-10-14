"""
mBERT Social Engineering Multi-Label Architecture - Phase 9 (T-P09-042)
Ported from EASP_fixed.ipynb (Cell 2).
Uses bert-base-multilingual-cased encoder with a project-specific classification head
for detecting 4 social engineering threat categories.
"""

from typing import List, Dict, Any

LABELS = [
    "urgency",
    "authority_impersonation",
    "credential_request",
    "payment_request"
]

# Calibrated decision thresholds per threat category (Notebook Cell 2)
LABEL_THRESHOLDS = {
    "urgency": 0.40,
    "authority_impersonation": 0.35,
    "credential_request": 0.35,
    "payment_request": 0.40
}

try:
    import torch
    import torch.nn as nn
    from transformers import BertModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = object


if TORCH_AVAILABLE:
    class SocialEngineeringmBERT(nn.Module):
        def __init__(self, num_classes: int = len(LABELS), dropout_prob: float = 0.3):
            super().__init__()
            self.bert = BertModel.from_pretrained("bert-base-multilingual-cased")
            self.dropout = nn.Dropout(dropout_prob)
            self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)

        def forward(self, input_ids, attention_mask=None, token_type_ids=None):
            outputs = self.bert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids
            )
            pooled_output = outputs.pooler_output
            pooled_output = self.dropout(pooled_output)
            logits = self.classifier(pooled_output)
            return logits
else:
    class SocialEngineeringmBERT:
        def __init__(self, *args, **kwargs):
            pass
