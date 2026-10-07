"""
Unit Tests for EASP AI Components - Phase 3, 4, 8, 9, 10
Tests DLP detection & redaction, RawNet2 fallback, mBERT heuristic scoring, and Risk calculation.
"""

from dlp.engine import DLPEngine
from social_engineering.detector import SocialEngineeringDetector
from voice_deepfake.detector import RawNet2VoiceDetector
import numpy as np


def test_dlp_detection_and_redaction():
    engine = DLPEngine()

    # 1. API Key detection
    text_with_key = "My OpenAI API key is sk-proj-1234567890abcdef1234567890abcdef1234567890abcdef, please keep it safe."
    result = engine.scan_and_redact(text_with_key)
    assert result["has_sensitive_data"] is True, "Expected sensitive data flagged"
    assert result["sensitivity_score"] >= 0.85, "Expected high sensitivity for API key"
    assert "sk-proj-" not in result["redacted_text"], "API key must be redacted from text"
    assert "<REDACTED_OPENAI_API_KEY_" in result["redacted_text"]

    # Test restoration
    token_map = {m["token_id"]: m["original_value"] for m in result["mappings"]}
    restored = engine.restore_text(result["redacted_text"], token_map)
    assert restored == text_with_key, "Restored text must match original"

    # 2. Credit Card detection with Luhn check
    valid_cc_text = "Pay using Visa card 4532015112830366 expires 12/28"
    cc_result = engine.scan_and_redact(valid_cc_text)
    assert cc_result["has_sensitive_data"] is True
    assert "<REDACTED_CREDIT_CARD_" in cc_result["redacted_text"]

    # 3. Benign text without sensitive info
    benign_text = "Good morning team, let us review the quarterly sprint roadmap."
    benign_result = engine.scan_and_redact(benign_text)
    assert benign_result["has_sensitive_data"] is False
    assert benign_result["sensitivity_score"] == 0.0
    assert benign_result["redacted_text"] == benign_text

    print("[PASS] DLP Detection and Reversible Redaction tests")


def test_social_engineering_detection():
    detector = SocialEngineeringDetector()

    # Coercive phishing call
    threat_text = "Urgent: this is the CEO calling. You must send the payment and wire transfer immediately!"
    res = detector.analyze_text(threat_text)
    assert res["has_threat"] is True
    assert res["social_engineering_score"] >= 0.70
    assert "urgency" in res["threats_detected"]
    assert "authority_impersonation" in res["threats_detected"]
    assert "payment_request" in res["threats_detected"]

    # Benign conversation
    benign_text = "Hello, I would like to schedule a product demo for tomorrow at 2 PM."
    benign_res = detector.analyze_text(benign_text)
    assert benign_res["has_threat"] is False
    assert benign_res["social_engineering_score"] < 0.40

    print("[PASS] Social Engineering multi-label tests")


def test_voice_deepfake_detector():
    detector = RawNet2VoiceDetector(weights_path="non_existent_weights.pth")
    detector.cnn_loaded = detector.rawnet_loaded = detector.model_loaded = False
    # Strict rule test: detector must not return silent random dummy values
    dummy_audio = np.sin(np.linspace(0, 500, 16000)).astype(np.float32)
    res = detector.analyze_audio(dummy_audio)
    assert res["success"] is False
    assert "spoof_score" not in res

    print("[PASS] Voice Deepfake detector tests")


if __name__ == "__main__":
    test_dlp_detection_and_redaction()
    test_social_engineering_detection()
    test_voice_deepfake_detector()
    print("\nAll AI component tests passed successfully!")
