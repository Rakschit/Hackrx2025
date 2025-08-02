from fastapi import FastAPI, Depends
import os, shutil
import hashlib

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import create_embeddings, get_pinecone_index
from app.models import RunRequest

app = FastAPI()

def file_id_creation(text):
    text = " ".join(text.split())
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

@app.post("/hackrx/run")
async def run_query(request: RunRequest, _: None = Depends(verify_bearer)):
    
    file_extension, temp_path = validate_request(request)

    # Extract text
    if file_extension == "pdf":
        text,page = extract_text_from_pdf(temp_path)

    file_id = file_id_creation(text.lower())

    # if file_id is # inside the pinecone db then prepare chunks
    # has_embeddings(file_id)

    chunks = prepare_for_embeddings(text, page)   
    pinecone_index = get_pinecone_index()
    msg = create_embeddings(chunks, file_id, pinecone_index)

    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    return {
        "extension": file_extension,
        "questions": request.questions,
        "page": page,
        "chunks length": len(chunks),
        "message": msg
    }

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text