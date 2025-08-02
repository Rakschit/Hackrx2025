from fastapi import FastAPI, Depends
import os, shutil
import hashlib
from pinecone import Pinecone
import uuid

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import create_embeddings, get_pinecone_index, get_embeddings_from_namespace, search_relevant_chunks, generate_answer_with_groq
from app.models import RunRequest

app = FastAPI()

def file_id_creation(text):
    random_id = str(uuid.uuid4())
    return random_id

@app.post("/hackrx/run")
async def run_query(request: RunRequest, _: None = Depends(verify_bearer)):
    
    file_extension, temp_path = validate_request(request)
    # Extract text
    if file_extension == "pdf":
        text,page = extract_text_from_pdf(temp_path)

    file_id = file_id_creation(text.lower())

    pinecone_index = get_pinecone_index()
    # has_embeddings = get_embeddings_from_namespace(pinecone_index, file_id)

    embeddings = get_embeddings_from_namespace(pinecone_index, file_id)

    #if not embeddings: 
    chunks = prepare_for_embeddings(text, page)
    embeddings = create_embeddings(chunks, file_id, pinecone_index)

    questions = request.questions

    top_matches_all = search_relevant_chunks(questions, embeddings)
    answers_list = [
        generate_answer_with_groq(q, embeddings, top_k=3)
        for q in questions
    ]

    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    return embeddings, answers_list

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text