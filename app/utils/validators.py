import os
from fastapi import Header, HTTPException
import requests
from mimetypes import guess_type

from urllib.parse import urlparse, unquote
from app.models import RunRequest

BEARER_API_KEY = os.getenv("BEARER_API_KEY")

def verify_bearer(authorization: str = Header(None)): #CHANGE THE BEARER KEY AS SAME AS THE PROBLEM STATEMENT
    if not BEARER_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: BEARER_API_KEY not set")
    
    valid_keys = [f"Bearer {BEARER_API_KEY}", BEARER_API_KEY]
    if authorization not in valid_keys:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
# ALLOWED FILES TO UPLOAD
allowed_types = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "message/rfc822": "eml",
}

def validate_request(request):
    # VALIDATING QUESTION
    questions = request.questions if hasattr(request, "questions") else request.get("questions")
    document = request.document if hasattr(request, "document") else request.get("document")

    if not questions or not all(isinstance(q, str) for q in questions):
        raise HTTPException(status_code=400, detail="Questions must be a list of strings")

    doc_url = str(document)

    resp = requests.head(doc_url, stream=True, allow_redirects=True)
    doc_type = resp.headers.get("Content-Type", "").lower().split(";")[0].strip()
    resp.close()

    # If content-type is missing from the header
    # can use python-magic for checking the file type
    if not doc_type:
        parsed = urlparse(doc_url)
        ext = os.path.splitext(parsed.path)[1].lower()
        mime, _ = guess_type(parsed.path)
        doc_type = mime or ""

    # Validate
    
    if doc_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Only pdf, docx, eml files allowed. Got: '{doc_type}'"
        )    
    
    file_extension = allowed_types[doc_type]

    # Prepare temp file path
    parsed = urlparse(doc_url)
    filename = os.path.basename(parsed.path)
    filename = unquote(filename) if filename else f"tempfile.{file_extension}"
    temp_path = f"/tmp/{filename}"
    
    download_file(doc_url, temp_path) # DOWNLOAD FILE AFTER VALIDATING

    return doc_url, file_extension, temp_path


def download_file(doc_url, temp_path):
    try:
        r = requests.get(doc_url, timeout=15)
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {e}")