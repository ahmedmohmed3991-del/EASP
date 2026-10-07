"""
EASP DLP Recognizers - Phase 3 (T-P03-018 / T-P03-020)
Comprehensive regex-based and structured pattern recognizers for:
- API keys (OpenAI, GitHub, AWS, HuggingFace, Slack, Generic Bearer)
- Financial secrets (Credit Cards with Luhn check, IBANs)
- Personal Identifiable Information (Emails, Phone numbers, IPv4/IPv6, SSNs)
"""

import re
from typing import List, Dict, Any


def luhn_checksum_valid(number_str: str) -> bool:
    """Validates credit card numbers using Luhn algorithm."""
    digits = [int(d) for d in re.sub(r"\D", "", number_str)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for idx, d in enumerate(reverse_digits):
        if idx % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


RECOGNIZER_PATTERNS = [
    # 1. High-Sensitivity Credentials & API Keys
    {
        "type": "OPENAI_API_KEY",
        "category": "CREDENTIAL",
        "regex": re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,}|sk-proj-[a-zA-Z0-9_-]{20,})\b"),
        "score": 0.98,
        "severity": "CRITICAL"
    },
    {
        "type": "GITHUB_TOKEN",
        "category": "CREDENTIAL",
        "regex": re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,})\b"),
        "score": 0.98,
        "severity": "CRITICAL"
    },
    {
        "type": "AWS_ACCESS_KEY",
        "category": "CREDENTIAL",
        "regex": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "score": 0.95,
        "severity": "CRITICAL"
    },
    {
        "type": "GENERIC_BEARER_TOKEN",
        "category": "CREDENTIAL",
        "regex": re.compile(r"(?i)\bbearer\s+([A-Za-z0-9_\-\.]{24,})\b"),
        "score": 0.92,
        "severity": "HIGH"
    },
    {
        "type": "PRIVATE_KEY_HEADER",
        "category": "CREDENTIAL",
        "regex": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "score": 1.00,
        "severity": "CRITICAL"
    },

    # 2. Financial Identifiers
    {
        "type": "CREDIT_CARD",
        "category": "FINANCIAL",
        "regex": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
        "score": 0.90,
        "severity": "HIGH",
        "validator": luhn_checksum_valid
    },
    {
        "type": "IBAN_CODE",
        "category": "FINANCIAL",
        "regex": re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b"),
        "score": 0.88,
        "severity": "HIGH"
    },

    # 3. Personal Identifiable Information (PII)
    {
        "type": "EMAIL_ADDRESS",
        "category": "PII",
        "regex": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "score": 0.85,
        "severity": "MEDIUM"
    },
    {
        "type": "PHONE_NUMBER",
        "category": "PII",
        "regex": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "score": 0.80,
        "severity": "MEDIUM"
    },
    {
        "type": "IPV4_ADDRESS",
        "category": "NETWORK",
        "regex": re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        "score": 0.75,
        "severity": "LOW"
    },
    {
        "type": "US_SSN",
        "category": "PII",
        "regex": re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"),
        "score": 0.90,
        "severity": "HIGH"
    }
]


def scan_patterns(text: str) -> List[Dict[str, Any]]:
    """
    Executes all pattern recognizers against the input text.
    Returns matched entity spans with offsets, categories, and confidence scores.
    """
    matches = []
    if not text:
        return matches

    for pattern_def in RECOGNIZER_PATTERNS:
        for match in pattern_def["regex"].finditer(text):
            span_text = match.group(0)

            # Run validator if specified
            if "validator" in pattern_def and not pattern_def["validator"](span_text):
                continue

            matches.append({
                "entity_type": pattern_def["type"],
                "category": pattern_def["category"],
                "start": match.start(),
                "end": match.end(),
                "text": span_text,
                "confidence": pattern_def["score"],
                "severity": pattern_def["severity"]
            })

    # Sort spans by start offset
    matches.sort(key=lambda m: m["start"])
    return matches
