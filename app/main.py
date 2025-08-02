from fastapi import FastAPI, Depends
import os, shutil
import hashlib
from pinecone import Pinecone

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import create_embeddings, get_pinecone_index
from app.models import RunRequest

app = FastAPI()

pc_key=os.getenv("PINECONE_API_KEY")
    
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

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
    # pinecone_index = get_pinecone_index()
    # embeddings = create_embeddings(chunks, file_id)
    # pinecone_index.upsert(emb=embeddings)

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
        "chunks:": chunks
    }

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text