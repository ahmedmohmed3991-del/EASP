"""
Unified Risk Scoring & Policy Engine for EASP.
Combines multi-modal threat telemetry:
- AI-Prompt DLP & Prompt Injection Probabilities
- PII Leakage Detection & Severity Ratings
- Voice Deepfake Detection Probabilities
- Social Engineering / Phishing Indicators
Outputs an actionable composite Risk Score (0-100) and Policy Action (Allow, Flag, Block).
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json

@dataclass
class ThreatTelemetry:
    """Input payload containing individual layer confidence scores."""
    prompt_injection_prob: float = 0.0 # [0.0, 1.0]
    deepfake_prob: float = 0.0         # [0.0, 1.0]
    social_eng_prob: float = 0.0       # [0.0, 1.0]
    pii_entities_count: int = 0        # Count of sensitive PII entities
    pii_severity_score: float = 0.0    # [0.0, 1.0] derived from entity types (e.g. API keys vs first names)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PolicyDecision:
    """Output decision object containing composite score, decision, and explanation."""
    composite_risk_score: float        # [0.0, 100.0]
    action: str                        # 'ALLOW', 'FLAG', 'BLOCK'
    reasons: List[str]                 # Specific triggers explaining the risk
    breakdown: Dict[str, float]        # Normalized component risk scores
    telemetry: ThreatTelemetry

class EASPRiskPolicyEngine:
    """
    Enterprise Policy Engine that executes dynamic multi-factor risk weighting,
    compound threat multiplier logic, and threshold enforcement.
    """
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        allow_threshold: float = 35.0,
        block_threshold: float = 70.0
    ):
        # Default layer weights (normalized to sum to 1.0)
        self.weights = weights or {
            "prompt_injection": 0.35,
            "deepfake": 0.35,
            "social_engineering": 0.15,
            "pii_leakage": 0.15
        }
        self.allow_threshold = allow_threshold
        self.block_threshold = block_threshold

    def evaluate(self, telemetry: ThreatTelemetry) -> PolicyDecision:
        """Evaluates input telemetry and produces a policy decision."""
        reasons = []
        breakdown = {}

        # 1. Component Contributions (0-100 scale)
        pi_score = telemetry.prompt_injection_prob * 100.0
        df_score = telemetry.deepfake_prob * 100.0
        se_score = telemetry.social_eng_prob * 100.0
        pii_score = max(telemetry.pii_severity_score * 100.0, min(telemetry.pii_entities_count * 20.0, 100.0))

        breakdown["prompt_injection"] = round(pi_score, 2)
        breakdown["voice_deepfake"] = round(df_score, 2)
        breakdown["social_engineering"] = round(se_score, 2)
        breakdown["pii_leakage"] = round(pii_score, 2)

        # 2. Weighted Base Score
        base_score = (
            pi_score * self.weights["prompt_injection"] +
            df_score * self.weights["deepfake"] +
            se_score * self.weights["social_engineering"] +
            pii_score * self.weights["pii_leakage"]
        )

        # 3. Compound Threat Multiplier (e.g. deepfake combined with injection/social engineering)
        multiplier = 1.0
        if telemetry.deepfake_prob > 0.65 and telemetry.social_eng_prob > 0.60:
            multiplier += 0.25
            reasons.append("Coordinated Multi-Modal Threat: Voice Deepfake combined with Social Engineering.")
            
        if telemetry.prompt_injection_prob > 0.70 and telemetry.pii_entities_count > 0:
            multiplier += 0.20
            reasons.append("Critical Exfiltration Threat: Prompt Injection attempting PII/Secret extraction.")

        final_score = min(100.0, base_score * multiplier)

        # 4. Reason Tagging
        if pi_score >= 70.0:
            reasons.append(f"High-confidence Prompt Injection detected ({pi_score:.1f}%).")
        if df_score >= 70.0:
            reasons.append(f"Synthetic / Cloned Voice Deepfake detected ({df_score:.1f}%).")
        if se_score >= 70.0:
            reasons.append(f"Social Engineering / Phishing pattern identified ({se_score:.1f}%).")
        if telemetry.pii_entities_count > 0:
            reasons.append(f"Sensitive Data Exposure: {telemetry.pii_entities_count} PII entity/secret(s) identified.")

        # 5. Policy Decision Thresholds
        if final_score >= self.block_threshold:
            action = "BLOCK"
            if not reasons:
                reasons.append(f"Composite risk score ({final_score:.1f}) exceeds BLOCK threshold ({self.block_threshold}).")
        elif final_score >= self.allow_threshold:
            action = "FLAG"
            if not reasons:
                reasons.append(f"Composite risk score ({final_score:.1f}) requires SOC analyst review or step-up authentication.")
        else:
            action = "ALLOW"
            if not reasons:
                reasons.append("Interaction verified safe against enterprise security baseline.")

        return PolicyDecision(
            composite_risk_score=round(final_score, 2),
            action=action,
            reasons=reasons,
            breakdown=breakdown,
            telemetry=telemetry
        )

if __name__ == "__main__":
    engine = EASPRiskPolicyEngine()
    
    # Test Scenario: High Prompt Injection + PII
    sample = ThreatTelemetry(
        prompt_injection_prob=0.92,
        deepfake_prob=0.10,
        social_eng_prob=0.30,
        pii_entities_count=2,
        pii_severity_score=0.85
    )
    decision = engine.evaluate(sample)
    print("--- Test Policy Decision ---")
    print(f"Action: {decision.action}")
    print(f"Composite Score: {decision.composite_risk_score}/100")
    print(f"Reasons: {decision.reasons}")
    print(f"Breakdown: {decision.breakdown}")
