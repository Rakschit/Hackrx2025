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

def create_chunks(sentences, max_chunk_words=500, overlap_sentences=2):
    """
    Creates semantically meaningful chunks from a list of sentences.

    Args:
        sentences (list[str]): A list of sentences from the document.
        max_chunk_words (int): The target maximum number of words for a chunk.
        overlap_sentences (int): How many sentences to include as overlap between chunks.

    Returns:
        list[str]: A list of text chunks.
    """
    if not sentences:
        return []

    # Pre-calculate the word count for each sentence
    sentence_word_counts = [len(s.split()) for s in sentences]
    total_words = sum(sentence_word_counts)

    # If the document is small, return it as a single chunk
    if total_words <= max_chunk_words:
        return [" ".join(sentences)]

    chunks = []
    current_chunk_sentences = []
    current_chunk_words = 0
    
    for i, sentence in enumerate(sentences):
        sentence_len = sentence_word_counts[i]

        # If adding the next sentence would exceed the max size, finalize the current chunk
        if current_chunk_words + sentence_len > max_chunk_words and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))

            # Start the next chunk with an overlap
            # A deque is efficient for this, but a simple slice works well too
            overlap_start_index = max(0, len(current_chunk_sentences) - overlap_sentences)
            current_chunk_sentences = current_chunk_sentences[overlap_start_index:]
            
            # Recalculate the word count for the new, overlapped chunk
            current_chunk_words = sum(len(s.split()) for s in current_chunk_sentences)

        # If a single sentence is larger than the max chunk size, handle it
        if sentence_len > max_chunk_words:
            # If there's a pending chunk, save it first
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_chunk_words = 0
            
            # Add the huge sentence as its own chunk
            chunks.append(sentence)
            continue # Move to the next sentence

        # Add the current sentence to the chunk
        current_chunk_sentences.append(sentence)
        current_chunk_words += sentence_len

    # Add the final chunk if any sentences are left
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks

def prepare_for_embeddings(text, page):
    cleaned_text = clean_text(text, page)
    sentences = split_into_sentences(" ".join(cleaned_text))
    chunks = create_chunks(sentences)
    return chunks