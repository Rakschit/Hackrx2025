import os
from fastapi import Header, HTTPException
import requests
from mimetypes import guess_type

from urllib.parse import urlparse, unquote
from app.models import RunRequest

BEARER_API_KEY = os.getenv("BEARER_API_KEY")

def verify_bearer(authorization: str = Header(None)):
    if not BEARER_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: BEARER_API_KEY not set")
    if authorization != f"{BEARER_API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

# ALLOWED FILES TO UPLOAD
allowed_types = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "message/rfc822": "eml",
}

def validate_request(request: RunRequest):
    # VALIDATING QUESTION
    if not request.questions or not all(isinstance(q, str) for q in request.questions):
        raise HTTPException(status_code=400, detail="Questions must be a list of strings")
    
    doc_url = str(request.document)

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

    return file_extension, temp_path


def download_file(doc_url, temp_path):
    try:
        r = requests.get(doc_url, timeout=15)
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {e}")