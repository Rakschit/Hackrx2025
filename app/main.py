import os
import shutil
import uuid
import time
import json
import logging
import tempfile
# import hashlib

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.utils.validators import verify_bearer, validate_document_url, download_file
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import (create_embeddings, get_pinecone_index, 
                                  get_embeddings_from_namespace, search_relevant_chunks, 
                                  generate_answer_with_groq, generate_answer_with_gemini)
from app.db import insert_hackrx_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HackRx API",
    description="API for processing documents and answering questions.",
    version="1.0.0"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve favicon explicitly
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(static_dir, "favicon.ico"))

def file_id_creation():
    return str(uuid.uuid4())

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the HackRx API!"}

@app.get("/hackrx/run")
async def run_query_get():
    return {"message": "GET request received - no auth required"}

@app.post("/hackrx/run")
async def run_query(request: Request, _: None = Depends(verify_bearer)):
    request_start_time = time.time()
    timings = {}
    temp_path = None

    try:
        # 1. Parse Request Body
        body = await request.json()
        questions = body.get("questions", [])
        document_url = body.get("document", "")

        if not document_url or not isinstance(questions, list) or not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request must include 'document' (string) and a non-empty 'questions' (list of strings)."
            )
        """
    if request.method == "POST":
        body = await request.json()
        questions = body.get("questions", [])
        document = body.get("document", "")
    else:
        questions_param = request.query_params.get("questions", "")
        questions = questions_param.split(",") if questions_param else []
        document = request.query_params.get("document", "")
        """
        start_time = time.time()
        validated_url, file_extension = validate_document_url(document_url)
        timings["validate_request"] = round((time.time() - start_time) * 1000)
        logger.info(f"Validated request for document: {validated_url}")

        """
    if not document:
        return {"error": "document parameter is required"}

    # Prepare a dict for validate_request
    dummy_req = {"questions": questions, "document": document}
    doc_url, file_extension, temp_path = validate_request(dummy_req)

    timings["validate_request"] = time.time() - start
        """

        start_time = time.time()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_path = temp_file.name
        
        download_file(validated_url, temp_path)
        timings["download_file"] = round((time.time() - start_time) * 1000)
        logger.info(f"File downloaded to temporary path: {temp_path}")

        # Extract text
        if file_extension == "pdf":
            text, page = extract_text_from_pdf(temp_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File extension '.{file_extension}' is valid but text extraction is not implemented."
            )
        timings["extract_text"] = round((time.time() - start_time) * 1000)

        """
    start = time.time()
    file_id = file_id_creation(text.lower())
    timings["file_id_creation"] = time.time() - start

    start = time.time()
    pinecone_index = get_pinecone_index()
    timings["get_pinecone_index"] = time.time() - start
        """
        file_id = file_id_creation()
        pinecone_index = get_pinecone_index()
        logger.info(f"Generated File ID: {file_id}")

        start_time = time.time()
        embeddings = get_embeddings_from_namespace(pinecone_index, file_id)
        timings["get_embeddings_from_namespace"] = time.time() - start_time

        """
    # Fetch embeddings

    start = time.time()
    embeddings = get_embeddings_from_namespace(pinecone_index, file_id)
    timings["get_embeddings_from_namespace"] = time.time() - start
        """


        # If no embeddings, prepare and create
        if not embeddings:
            logger.info(f"No embeddings found for {file_id}. Creating new ones.")
            start_time = time.time()
            chunks = prepare_for_embeddings(text, page)
            timings["prepare_for_embeddings"] = time.time() - start_time
        
            start_time = time.time()
            embeddings = create_embeddings(chunks, file_id, pinecone_index)
            timings["create_embeddings"] = time.time() - start_time

        else:
            logger.info(f"Found existing embeddings for {file_id}.")

        start_time = time.time()
        top_matches_all = search_relevant_chunks(questions, embeddings)
        timings["search_relevant_chunks"] = time.time() - start_time

        """
    for q in questions:
        start_q = time.time()
        
        answers_list.append(generate_answer_with_gemini(q, top_matches_all))
        timings[f"generate_answer_with_llm_{q}"] = time.time() - start_q
        """
        """
    answers_list = []
    for i, q in enumerate(questions, start=1):
        start_q = time.time()
        # use groq when testing
        # answers_list.append(generate_answer_with_groq(q, top_matches_all))
        # use gemini when uploading
        answers_list.append(generate_answer_with_gemini(q, top_matches_all[questions[i]]))
        timings[f"generate_answer_with_llm_{i}"] = round(time.time() - start_q, 2)
        """
        answers_list = []
        for i, q in enumerate(questions):
            start_q_time = time.time()
            answer = generate_answer_with_gemini(q, top_matches_all)
            answers_list.append(answer)
            timings[f"generate_answer_llm_{i+1}"] = round(time.time() - start_q_time, 2)

        total_time_ms = int((time.time() - request_start_time) * 1000)
        logger.info(f"Total processing time: {total_time_ms}ms")


        insert_hackrx_logs(
            file_id=file_id,
            file_link=validated_url,
            questions_json=json.dumps(questions),
            answers_json=json.dumps(answers_list),
            total_time_ms=total_time_ms,
            timings_json=json.dumps(timings)
        )
        return {"answers": answers_list}
    
    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {e}"
        )
    finally:
        # 10. Ensure Temporary File is Always Removed
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Successfully cleaned up temporary file: {temp_path}")
            except OSError as e:
                logger.error(f"Error removing temporary file {temp_path}: {e}")



@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text