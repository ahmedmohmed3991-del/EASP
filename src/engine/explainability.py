"""
EASP Explainable AI (XAI) Engine - SHAP & XGBoost Risk Model
------------------------------------------------------------
- Uses XGBoost + SHAP TreeExplainer to explain multi-modal risk scoring.
- Calculates exact feature contribution impacts (Deepfake, Prompt Injection, Urgency, Authority, PII).
"""
import numpy as np
import xgboost as xgb
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

class SHAPRiskExplainer:
    def __init__(self):
        self.feature_names = [
            "Prompt Injection Threat",
            "Voice Deepfake Prob",
            "Social Engineering Urgency",
            "Authority Impersonation",
            "Sensitive PII Entities"
        ]
        self.model = self._train_surrogate_model()
        self.explainer = shap.TreeExplainer(self.model)

    def _train_surrogate_model(self) -> xgb.XGBClassifier:
        np.random.seed(42)
        n_samples = 800
        X = np.random.uniform(0.0, 1.0, size=(n_samples, len(self.feature_names)))
        X[:, 4] = np.random.choice([0, 1, 2, 3, 4], size=n_samples)

        y = []
        for row in X:
            pi, df, urg, auth, pii = row
            score = (pi * 0.35) + (df * 0.35) + (max(urg, auth) * 0.20) + (min(pii * 0.25, 1.0) * 0.10)
            if score >= 0.65:
                y.append(2)  # BLOCK
            elif score >= 0.35:
                y.append(1)  # FLAG
            else:
                y.append(0)  # ALLOW

        clf = xgb.XGBClassifier(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.08,
            objective="multi:softprob",
            num_class=3,
            random_state=42
        )
        clf.fit(X, y)
        return clf

    def explain(self, pi: float, df: float, urg: float, auth: float, pii: int) -> Tuple[Dict[str, float], plt.Figure]:
        """Calculates SHAP values and returns contribution dict + matplotlib bar chart."""
        vec = np.array([[pi, df, urg, auth, float(pii)]])
        shap_values = self.explainer.shap_values(vec)
        
        # Handle SHAP multi-class format: array shape (1, n_features, n_classes) or list of arrays
        if isinstance(shap_values, list):
            # Pick highest severity class (BLOCK / class 2)
            shap_impacts = shap_values[2][0]
        elif len(shap_values.shape) == 3:
            shap_impacts = shap_values[0, :, 2]
        else:
            shap_impacts = shap_values[0]

        impact_dict = {
            self.feature_names[i]: round(float(shap_impacts[i]), 4)
            for i in range(len(self.feature_names))
        }

        # Plot SHAP Contribution Bar Chart
        fig, ax = plt.subplots(figsize=(6.5, 3.0))
        y_pos = np.arange(len(self.feature_names))
        vals = [impact_dict[k] for k in self.feature_names]
        colors = ['#ef4444' if v > 0 else '#10b981' for v in vals]
        
        ax.barh(y_pos, vals, color=colors, align='center', height=0.55)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(self.feature_names, fontsize=9, fontweight='500')
        ax.axvline(0, color='gray', linestyle='--', alpha=0.7)
        ax.set_xlabel("SHAP Impact on Policy BLOCK Probability", fontsize=9)
        ax.set_title("XAI Feature Attribution Breakdown (SHAP Engine)", fontsize=10, fontweight='bold')
        plt.tight_layout()

        return impact_dict, fig
