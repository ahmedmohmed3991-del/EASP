"""
EASP Phase 2 ML Risk Engine (XGBoost + SHAP Explainability)
Task T-P13-063 & Proposal Compliance
Predicts risk fusion action (ALLOW, ESCALATE, BLOCK) and provides
local mathematical SHAP feature attributions per decision.
"""

import os
import time
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from typing import Dict, Any, Optional

FEATURE_NAMES = [
    "deepfake_score",
    "urgency_score",
    "authority_score",
    "credential_score",
    "payment_score",
    "dlp_entity_count"
]

CLASSES = ["ALLOW", "ESCALATE", "BLOCK"]


class XGBoostRiskEngine:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.model_path = os.path.join(model_dir, "xgboost_risk_engine.json")
        self.feature_names = FEATURE_NAMES
        self.classes = CLASSES
        self.model = None
        self.explainer = None
        self.metrics = {"status": "UNVERIFIED"}
        if not os.path.isfile(self.model_path):
            raise RuntimeError("Risk model checkpoint is missing")
        self.model = xgb.XGBClassifier()
        self.model.load_model(self.model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def predict_and_explain(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs XGBoost inference and SHAP local attribution on an incident feature vector.
        """
        start = time.perf_counter()

        vec = [
            float(incident.get("deepfake_score", 0.0)),
            float(incident.get("urgency_score", 0.0)),
            float(incident.get("authority_score", 0.0)),
            float(incident.get("credential_score", 0.0)),
            float(incident.get("payment_score", 0.0)),
            float(incident.get("dlp_entity_count", 0.0))
        ]

        df_in = pd.DataFrame([vec], columns=self.feature_names)
        pred_idx = int(self.model.predict(df_in)[0])
        probs = self.model.predict_proba(df_in)[0]

        # Calculate SHAP local attribution for the chosen class
        shap_explanation = self.explainer(df_in)
        raw_shaps = shap_explanation.values[0][:, pred_idx]

        attributions = {
            feat: round(float(val), 4)
            for feat, val in zip(self.feature_names, raw_shaps)
        }

        # Find primary driver
        primary_driver = max(attributions.items(), key=lambda item: abs(item[1]))[0]

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            "success": True,
            "decision": self.classes[pred_idx],
            "action": self.classes[pred_idx],
            "confidence": round(float(probs[pred_idx]), 4),
            "class_probabilities": {
                self.classes[i]: round(float(probs[i]), 4)
                for i in range(len(self.classes))
            },
            "shap_attributions": attributions,
            "primary_driver": primary_driver,
            "latency_ms": latency_ms,
            "engine": "Phase 2 XGBoost + SHAP TreeExplainer"
        }
