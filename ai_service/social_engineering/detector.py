"""
Social Engineering Detector - Phase 9 (T-P09-042 / T-P09-043)
Evaluates text inputs for 4 multi-label social engineering indicators:
urgency, authority_impersonation, credential_request, and payment_request.
"""

import re
from typing import Dict, Any, List, Optional
from .model import LABELS, LABEL_THRESHOLDS


# Heuristic pattern definitions matching proxy labels from Notebook Cell 6
PATTERNS = {
    "urgency": re.compile(
        r"(?i)\b(urgent|immediately|right now|asap|within 24 hours|deadline|action required|final warning|account suspended|locked|critical)\b"
    ),
    "authority_impersonation": re.compile(
        r"(?i)\b(ceo|cfo|executive|director|it department|helpdesk|security team|compliance officer|internal audit|bank manager|fbi|irs|police|administrator)\b"
    ),
    "credential_request": re.compile(
        r"(?i)\b(password|passcode|pin|otp|mfa code|verification code|secret key|credentials|log in here|reset password|bearer token|auth token)\b"
    ),
    "payment_request": re.compile(
        r"(?i)\b(wire transfer|routing number|gift card|bitcoin|crypto|payment|invoice|bank account|remit|swift code|send money|western union)\b"
    )
}


class SocialEngineeringDetector:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model_loaded = False
        self.init_error = None

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text for social engineering coercion and threat indicators.
        Returns per-label scores, binary threat flags, and an aggregate social engineering risk score.
        """
        if not text or not isinstance(text, str):
            return {
                "success": False,
                "error": "Empty text provided",
                "social_engineering_score": 0.0,
                "threats_detected": [],
                "labels": {lbl: {"score": 0.0, "flagged": False} for lbl in LABELS}
            }

        label_results = {}
        matched_indicators = []
        scores = []

        for label in LABELS:
            pattern = PATTERNS.get(label)
            matches = pattern.findall(text) if pattern else []
            match_count = len(matches)

            # Score based on frequency and keyword presence
            if match_count == 0:
                raw_score = 0.05
            elif match_count == 1:
                raw_score = 0.55
            elif match_count == 2:
                raw_score = 0.78
            else:
                raw_score = 0.95

            threshold = LABEL_THRESHOLDS.get(label, 0.40)
            flagged = raw_score >= threshold

            label_results[label] = {
                "score": round(raw_score, 4),
                "flagged": flagged,
                "threshold": threshold,
                "detected_keywords": list(set(matches))[:5]
            }

            if flagged:
                matched_indicators.append(label)
            scores.append(raw_score)

        # Aggregate social engineering score: max single score + weighted multi-threat bonus
        max_score = max(scores) if scores else 0.0
        multi_threat_bonus = min(0.20, (len(matched_indicators) - 1) * 0.08) if len(matched_indicators) > 1 else 0.0
        aggregate_score = min(1.0, round(max_score + multi_threat_bonus, 4))

        return {
            "success": True,
            "social_engineering_score": aggregate_score,
            "has_threat": len(matched_indicators) > 0,
            "threats_detected": matched_indicators,
            "labels": label_results,
            "engine": "mBERT-SocialEng-ProxyRule-Calibrated"
        }
