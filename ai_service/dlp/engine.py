"""
EASP Reversible DLP & Redaction Engine - Phase 3 / Phase 4
Identifies sensitive data spans, performs token substitution, and calculates
the DLP sensitivity score for the downstream Risk Engine.
"""

import secrets
from typing import Dict, Any, List
from .recognizers import scan_patterns


class DLPEngine:
    def __init__(self):
        pass

    def scan_and_redact(self, text: str) -> Dict[str, Any]:
        """
        Scans text for sensitive information, generates reversible token mappings,
        and constructs the redacted text representation.
        """
        if not text or not isinstance(text, str):
            return {
                "original_text": text or "",
                "redacted_text": text or "",
                "entities": [],
                "mappings": [],
                "sensitivity_score": 0.0,
                "has_sensitive_data": False
            }

        raw_matches = scan_patterns(text)

        # Resolve overlapping spans (longest match wins)
        resolved_matches = []
        for match in raw_matches:
            overlap = False
            for existing in resolved_matches:
                if not (match["end"] <= existing["start"] or match["start"] >= existing["end"]):
                    overlap = True
                    break
            if not overlap:
                resolved_matches.append(match)

        resolved_matches.sort(key=lambda m: m["start"])

        # Construct redacted string and token mappings
        redacted_parts = []
        mappings = []
        last_idx = 0

        severity_scores = {
            "CRITICAL": 0.95,
            "HIGH": 0.80,
            "MEDIUM": 0.50,
            "LOW": 0.25
        }

        max_severity_score = 0.0

        for match in resolved_matches:
            # Append preceding unredacted text
            redacted_parts.append(text[last_idx:match["start"]])

            # Generate unique token
            token_hash = secrets.token_hex(16)
            token_id = f"<REDACTED_{match['entity_type']}_{token_hash}>"

            redacted_parts.append(token_id)
            mappings.append({
                "token_id": token_id,
                "entity_type": match["entity_type"],
                "category": match["category"],
                "original_value": match["text"],
                "start": match["start"],
                "end": match["end"]
            })

            severity_val = severity_scores.get(match["severity"], 0.3)
            if severity_val > max_severity_score:
                max_severity_score = severity_val

            last_idx = match["end"]

        redacted_parts.append(text[last_idx:])
        redacted_text = "".join(redacted_parts)

        # Calculate sensitivity score: bounded in [0.0, 1.0]
        # Base on highest severity found, modulated by number of entities
        count_boost = min(0.15, len(mappings) * 0.03) if mappings else 0.0
        dlp_sensitivity_score = min(1.0, round(max_severity_score + count_boost, 4)) if mappings else 0.0

        return {
            "original_text": text,
            "redacted_text": redacted_text,
            "entities": resolved_matches,
            "mappings": mappings,
            "sensitivity_score": dlp_sensitivity_score,
            "has_sensitive_data": len(mappings) > 0
        }

    def restore_text(self, redacted_text: str, token_map: Dict[str, str]) -> str:
        """
        Restores tokens in redacted text back to their original sensitive values.
        token_map: dictionary of { token_id: original_value }
        """
        if not redacted_text or not token_map:
            return redacted_text

        result = redacted_text
        for token_id, original_val in token_map.items():
            result = result.replace(token_id, original_val)
        return result
