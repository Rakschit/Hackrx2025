import os
import shutil
import uuid
import time
import json
import logging
import tempfile
import traceback # Already imported, now we will use it!

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.utils.validators import verify_bearer, validate_document_url, download_file
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import prepare_for_embeddings
from app.utils.embeddings import (create_embeddings, get_pinecone_index, 
                                  get_embeddings_from_namespace, search_relevant_chunks, 
                                  generate_answer_with_gemini)
from app.db import insert_hackrx_logs

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HackRx API",
    description="API for processing documents and answering questions.",
    version="1.0.0"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Helper Functions & Static Endpoints ---
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(static_dir, "favicon.ico"))

def file_id_creation():
    return str(uuid.uuid4())

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Welcome to the HackRx API!"}

# --- Main Application Logic ---
@app.post("/hackrx/run")
async def run_query(request: Request, _: None = Depends(verify_bearer)):
    request_start_time = time.time()
    timings = {}
    temp_path = None

    try:
        # 1. Parse and normalize the request body
        body = await request.json()
        questions = body.get("questions") or body.get("question")
        document_url = body.get("document") or body.get("documents") or ""
    
        if questions and isinstance(questions, str):
            logger.info("Single question string received; converting to list.")
            questions = [questions]

        # 2. Validate the normalized inputs
        if not document_url or not isinstance(questions, list) or not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request must include 'document' (string) and a non-empty 'questions' (list of strings or a single string)."
            )
        
        # ... (The rest of your try block is perfect and remains unchanged) ...
        start_time = time.time()
        validated_url, file_extension = validate_document_url(document_url)
        timings["validate_request"] = round((time.time() - start_time) * 1000)
        logger.info(f"Validated request for document: {validated_url}")

        start_time = time.time()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_path = temp_file.name
        download_file(validated_url, temp_path)
        timings["download_file"] = round((time.time() - start_time) * 1000)
        logger.info(f"File downloaded to temporary path: {temp_path}")

        start_time = time.time()
        if file_extension == "pdf":
            text, page = extract_text_from_pdf(temp_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File extension '.{file_extension}' is valid but text extraction is not implemented."
            )
        timings["extract_text"] = round((time.time() - start_time) * 1000)

        file_id = file_id_creation()
        pinecone_index = get_pinecone_index()
        logger.info(f"Generated File ID: {file_id}")

        start_time = time.time()
        embeddings = get_embeddings_from_namespace(pinecone_index, file_id)
        timings["get_embeddings_from_namespace"] = round((time.time() - start_time) * 1000)

        if not embeddings:
            logger.info(f"No embeddings found for {file_id}. Creating new ones.")
            start_time = time.time()
            chunks = prepare_for_embeddings(text, page)
            timings["prepare_for_embeddings"] = round((time.time() - start_time) * 1000)
        
            start_time = time.time()
            embeddings = create_embeddings(chunks, file_id, pinecone_index)
            timings["create_embeddings"] = round((time.time() - start_time) * 1000)
        else:
            logger.info(f"Found existing embeddings for {file_id}.")

        start_time = time.time()
        top_matches_all = search_relevant_chunks(questions, embeddings)
        timings["search_relevant_chunks"] = round((time.time() - start_time) * 1000)

        answers_list = []
        for i, q in enumerate(questions):
            start_q_time = time.time()
            answer = generate_answer_with_gemini(q, top_matches_all)
            answers_list.append(answer)
            timings[f"generate_answer_llm_{i+1}"] = round(time.time() - start_q_time, 2)

        total_time_ms = int((time.time() - request_start_time) * 1000)
        logger.info(f"Total processing time: {total_time_ms}ms")

        # IMPORTANT: Double-check that your insert_hackrx_logs function expects 'file_link'
        # In a previous version, this was doc_url. Ensure it matches your db.py.
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
        # Re-raise known client-side or validation errors so FastAPI can handle them.
        raise http_exc
    
    except Exception as e:
        # --- THIS IS THE MODIFIED BLOCK ---
        # It catches any other unexpected server-side error and prints the full traceback.
        print("\n" + "="*20 + " UNEXPECTED ERROR CAUGHT " + "="*20)
        traceback.print_exc()
        print("="*66 + "\n")
        
        # This logger line is still excellent practice for production logging.
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

        # Finally, raise a standard 500 error to the client.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred. Check server logs for traceback. Error: {e}"
        )
    finally:
        # Ensure the temporary file is always cleaned up
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Successfully cleaned up temporary file: {temp_path}")
            except OSError as e:
                logger.error(f"Error removing temporary file {temp_path}: {e}")