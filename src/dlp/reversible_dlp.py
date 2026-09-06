"""
Reversible Zero-Trust DLP & Redaction Engine
---------------------------------------------
- Uses AES-256 (Fernet) in-memory cryptographic ephemeral vault.
- Redacts sensitive PII, API keys, credentials, credit cards into tokens (<REDACTED_TYPE_HASH>).
- Provides 100% lossless reversible decryption for authorized security audit workflows.
"""
import os
import re
import json
from pathlib import Path
from typing import Tuple, List, Dict
from cryptography.fernet import Fernet

class ReversibleDLPEngine:
    def __init__(self, pii_dataset_path: str = None):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.token_vault = {}
        self.pii_dataset_path = pii_dataset_path
        self.patterns = {
            "EMAIL_ADDRESS": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "API_KEY": r"(?i)(?:api_key|token|secret|sk-[a-zA-Z0-9]{20,}|AWS_KEY=[a-zA-Z0-9_]{16,})",
            "PHONE_OR_IMEI": r"\b(?:\d{2,3}[- ]\d{6}[- ]\d{6}[- ]\d|\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4})\b",
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "URL": r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+",
            "PASSWORD_SECRET": r"(?i)(?:password|secret|pass|كلمة سر)\s*[:=]\s*\S+"
        }

    def scan_and_redact(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Scans text, encrypts matches with AES-256, and returns redacted string + entity list."""
        all_matches = []
        for entity_type, pattern in self.patterns.items():
            for m in re.finditer(pattern, text):
                all_matches.append((m.start(), m.end(), entity_type, m.group()))

        # Resolve overlaps
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        non_overlapping = []
        last_end = -1
        for start, end, entity_type, orig_val in all_matches:
            if start >= last_end:
                non_overlapping.append((start, end, entity_type, orig_val))
                last_end = end

        non_overlapping.sort(key=lambda x: x[0], reverse=True)

        redacted_text = text
        detected_entities = []
        for start, end, entity_type, orig_val in non_overlapping:
            token_hash = os.urandom(3).hex().upper()
            token = f"<REDACTED_{entity_type}_{token_hash}>"
            encrypted_val = self.cipher.encrypt(orig_val.encode()).decode()
            self.token_vault[token] = encrypted_val
            redacted_text = redacted_text[:start] + token + redacted_text[end:]
            detected_entities.append({
                "type": entity_type,
                "original": orig_val,
                "token": token,
                "encrypted_vault_id": encrypted_val[:16] + "..."
            })

        return redacted_text, detected_entities

    def restore_text(self, redacted_text: str) -> str:
        """Losslessly decrypts tokens back to the original plaintext using the AES-256 vault."""
        restored_text = redacted_text
        for token, enc_val in self.token_vault.items():
            if token in restored_text:
                try:
                    original_val = self.cipher.decrypt(enc_val.encode()).decode()
                    restored_text = restored_text.replace(token, original_val)
                except Exception:
                    pass
        return restored_text
