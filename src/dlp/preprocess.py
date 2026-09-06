"""
Preprocessing Pipeline for Text DLP & Prompt Injection.
Includes:
- Multilingual text normalization (English & Arabic)
- Cleaning and sanitization
- Stratified Train/Val/Test splitting (70/15/15)
- mBERT tokenization helpers
"""
import re
import unicodedata
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, Any

# Arabic diacritics / harakat regex
ARABIC_DIACRITICS = re.compile(r"[\u064B-\u0652\u0640]")

def normalize_arabic(text: str) -> str:
    """Normalizes Arabic characters (alefs, teh marbuta, remove harakat)."""
    if not isinstance(text, str):
        return ""
    # Remove diacritics / tashkeel
    text = ARABIC_DIACRITICS.sub("", text)
    # Normalize Alef variations (أ, إ, آ -> ا)
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize Teh Marbuta (ة -> ه)
    text = re.sub(r"ة", "ه", text)
    # Normalize Ya (ى -> ي)
    text = re.sub(r"ى", "ي", text)
    return text

def clean_text(text: str) -> str:
    """
    Cleans raw prompt text:
    - Unicode normalization (NFKC)
    - Strips invisible zero-width chars and non-printable control symbols
    - Arabic normalization
    - Whitespace normalization
    """
    if not isinstance(text, str):
        return ""
    
    # Unicode normalize
    text = unicodedata.normalize("NFKC", text)
    
    # Remove zero-width characters and control codes
    text = re.sub(r"[\u200B-\u200D\uFEFF\u0000-\u0008\u000B\u000C\u000E-\u001F]", "", text)
    
    # Normalize Arabic text if present
    if re.search(r"[\u0600-\u06FF]", text):
        text = normalize_arabic(text)
        
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text).strip()
    return text

def create_stratified_splits(
    df: pd.DataFrame,
    text_col: str = "text",
    label_col: str = "label",
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> Dict[str, pd.DataFrame]:
    """
    Splits dataset into 70% Train, 15% Validation, 15% Test with balanced class stratification.
    """
    assert abs((train_size + val_size + test_size) - 1.0) < 1e-5, "Splits must sum to 1.0"
    
    # First split: Train vs (Val + Test)
    temp_size = val_size + test_size
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_size,
        stratify=df[label_col],
        random_state=random_state
    )
    
    # Second split: Val vs Test
    val_ratio_in_temp = val_size / temp_size
    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_ratio_in_temp,
        stratify=temp_df[label_col],
        random_state=random_state
    )
    
    return {
        "train": train_df.reset_index(drop=True),
        "val": val_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True)
    }

class PromptTokenizer:
    """Tokenizer wrapper for bert-base-multilingual-cased (mBERT)."""
    def __init__(self, model_name: str = "bert-base-multilingual-cased", max_length: int = 256):
        from transformers import AutoTokenizer
        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
    def __call__(self, texts, **kwargs):
        return self.tokenizer(
            texts,
            padding=kwargs.get("padding", "max_length"),
            truncation=kwargs.get("truncation", True),
            max_length=self.max_length,
            return_tensors=kwargs.get("return_tensors", "pt")
        )
