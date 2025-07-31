from fastapi import FastAPI
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize

app = FastAPI()

@app.post("/")
def read_root():
    nltk.data.path.append(str(Path(__file__).resolve().parent.parent / "nltk_data"))
    text = "Hello Railway! Tokenization works offline."
    sent_tokenize(text)
    