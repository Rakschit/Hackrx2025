import nltk
from pathlib import Path

nltk.data.path.append(str(Path(__file__).resolve().parent.parent.parent / "nltk_data"))

from nltk.tokenize import sent_tokenize


def ex(text):
    new_text = sent_tokenize(text)
    return new_text

import re
from collections import Counter

def clean_text(text: str, page_count: int) -> str:
    """
    Light cleaning:
    - Normalize encoding
    - Remove page numbers, emails, urls
    - Remove repetitive headers/footers based on frequency
    - Preserve line breaks
    """
    # Normalize encoding
    text = text.encode('utf-8', errors='ignore').decode('utf-8')

    # Remove common patterns
    text = re.sub(r'\bPage[: ]*\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # standalone numbers
    text = re.sub(r'\S+@\S+', '', text)  # emails
    text = re.sub(r'http\S+', '', text)  # urls

    # Split into lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Count frequency of lines
    line_counts = Counter(lines)

    if freq_threshold > 3:
        freq_threshold = 3
    else:
        freq_threshold = page_count
    # Remove lines that appear more often than freq_threshold
    cleaned_lines = [
        line for line in lines if line_counts[line] < freq_threshold
    ]

    # Join lines with newline
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text
