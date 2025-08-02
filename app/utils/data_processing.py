import re
from collections import Counter
import nltk
import unicodedata
from pathlib import Path
nltk.data.path.append(str(Path(__file__).resolve().parent.parent.parent / "nltk_data"))
from nltk.tokenize import sent_tokenize

def clean_text(text: str, page_count: int) -> str:
    # Normalize encoding
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    text = unicodedata.normalize("NFKC",text)

    # changing dash unicode to dash
    text = text.replace("\u2013", "-")

    # Remove common patterns
    text = re.sub(r'\bPage\s*[:\-]?\s*\d+\s*(of|out\s+of)?\s*\d*\b','', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # standalone numbers
    text = re.sub(r'\S+@\S+', '', text)  # emails
    text = re.sub(r'http\S+', '', text)  # urls

    
    

    # Split into lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Count frequency of lines
    line_counts = Counter(lines)

    # Threshold: max 3
    freq_threshold = min(page_count, 3)

    # Remove frequent lines
    cleaned_lines = [
        line for line in lines if line_counts[line] < freq_threshold
    ]

    # Join list back into a string
    text = " ".join(cleaned_lines)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text):
    new_text = sent_tokenize(text)
    return new_text

def create_chunks(sentences, min_words_no_chunk=340, max_chunk_words=500, overlap=50):

    # Count total words
    total_words = sum(len(s.split()) for s in sentences)

    # If document is small, don't chunk
    if total_words <= min_words_no_chunk:
        return [" ".join(sentences)]

    # Determine chunk size
    if 700 <= total_words <= 1000:
        target_chunks = 3
        chunk_size = max(min(total_words // target_chunks, max_chunk_words), 250)
    else:
        chunk_size = max_chunk_words

    chunks = []
    current_chunk = []
    current_len = 0

    for sent in sentences:
        words = sent.split()
        # If adding this sentence exceeds the chunk size
        if current_len + len(words) > chunk_size:
            chunks.append(" ".join(current_chunk))

            # Create overlap
            if overlap > 0:
                overlap_words = " ".join(
                    " ".join(current_chunk).split()[-overlap:]
                )
                current_chunk = [overlap_words]
                current_len = len(overlap_words.split())
            else:
                current_chunk = []
                current_len = 0

        # Add sentence to chunk
        current_chunk.append(sent)
        current_len += len(words)

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def prepare_for_embeddings(text, page):
    cleaned_text = clean_text(text, page)
    sentences = split_into_sentences(" ".join(cleaned_text))
    chunks = create_chunks(sentences)
    return chunks