from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path
import os, shutil
import nltk
import fitz

# Set nltk_data path once
nltk.data.path.append(str(Path(__file__).resolve().parent.parent / "nltk_data"))

from nltk.tokenize import sent_tokenize

app = FastAPI()

def extract_text_from_pdf(file_path):
    file = fitz.open(file_path)
    text = ""
    for page in file:
        text += page.get_text("text")
    file.close()
    return text

@app.post("/")
def read_root():
    text = "Hello Railway! Tokenization works offline."
    return sent_tokenize(text)

@app.post("/hackrx/run")
async def upload_file(file: UploadFile = File(...)):
    file_type = os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        return JSONResponse(content={
            "error": "Invalid file type",
            "reason": "Only accepts pdf, docx and eml files"
        })

    # Save file to /tmp
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text based on file type
    file_content = ""
    if file_type == ".pdf":
        file_content = extract_text_from_pdf(temp_path)
    else:
        # Placeholder for DOCX/EML extraction
        file_content = f"{file.filename} uploaded, but extraction not implemented."

    new_text = sent_tokenize(file_content)
    return new_text
