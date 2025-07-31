import nltk
from pathlib import Path

nltk.data.path.append(str(Path(__file__).resolve().parent.parent.parent / "nltk_data"))

from nltk.tokenize import sent_tokenize

def ex(text):
    new_text = sent_tokenize(text)
    return new_text