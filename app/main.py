from fastapi import FastAPI, Depends
import os, shutil
import hashlib
from pinecone import Pinecone
import uuid
import time
import json

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import create_embeddings, get_pinecone_index, get_embeddings_from_namespace, search_relevant_chunks, generate_answer_with_groq, generate_answer_with_gemini
from app.models import RunRequest
from app.db import insert_hackrx_logs

app = FastAPI()

def file_id_creation(text):
    random_id = str(uuid.uuid4())
    return random_id

@app.post("/hackrx/run")
# async def run_query(request: RunRequest, _: None = Depends(verify_bearer)):
async def run_query(request: RunRequest):
    request_start = time.time()
    timings = {}

    start = time.time()
    doc_url, file_extension, temp_path = validate_request(request)
    timings["validate_request"] = time.time() - start

    # Extract text
    start = time.time()
    if file_extension == "pdf":
        text, page = extract_text_from_pdf(temp_path)
    timings["extract_text"] = time.time() - start

    start = time.time()
    file_id = file_id_creation(text.lower())
    timings["file_id_creation"] = time.time() - start

    start = time.time()
    pinecone_index = get_pinecone_index()
    timings["get_pinecone_index"] = time.time() - start

    # Fetch embeddings

    start = time.time()
    embeddings = get_embeddings_from_namespace(pinecone_index, file_id)
    timings["get_embeddings_from_namespace"] = time.time() - start

    # If no embeddings, prepare and create
    if not embeddings:
        start = time.time()
        chunks = prepare_for_embeddings(text, page)
        timings["prepare_for_embeddings"] = time.time() - start
        
        start = time.time()
        embeddings = create_embeddings(chunks, file_id, pinecone_index)
        timings["create_embeddings"] = time.time() - start

    questions = request.questions
    
    start = time.time()
    top_matches_all = search_relevant_chunks(questions, embeddings)
    timings["search_relevant_chunks"] = time.time() - start

    answers_list = []
    """
    for q in questions:
        start_q = time.time()
        
        answers_list.append(generate_answer_with_gemini(q, top_matches_all))
        timings[f"generate_answer_with_llm_{q}"] = time.time() - start_q
    """
    for i, q in enumerate(questions, start=1):
        start_q = time.time()
        # use groq when testing
        # answers_list.append(generate_answer_with_groq(q, top_matches_all))
        # use gemini when uploading
        answers_list.append(generate_answer_with_gemini(q, top_matches_all))
        timings[f"generate_answer_with_llm_{i}"] = round(time.time() - start_q, 2)


    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    # ---- DATABASE INSERTION ----
    total_time = time.time() - request_start
    total_time_ms = int(total_time * 1000)

    questions_json = json.dumps(questions)
    answers_json = json.dumps(answers_list)
    timings_json = json.dumps(timings)

    insert_hackrx_logs(file_id, doc_url, questions_json, answers_json, total_time_ms, timings_json)

    return {
       "answers": answers_list,
        "timings": timings,
        "total_time_ms": total_time_ms
    }

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text