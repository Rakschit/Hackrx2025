import os
from fastapi import Header, HTTPException
import requests
from urllib.parse import urlparse
from app.main import RunRequest

BEARER_API_KEY = os.getenv("BEARER_API_KEY")

def verify_bearer(authorization: str = Header(...)):
    if not BEARER_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: BEARER_API_KEY not set")
    if authorization != f"Bearer {BEARER_API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

# ALLOWED FILES TO UPLOAD
allowed_types = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "message/rfc822": "eml",
}

def validate_request(request: RunRequest):
    if not request.questions or not all(isinstance(q, str) for q in request.questions):
        raise HTTPException(status_code=400, detail="Questions must be a list of strings")
    
    doc_url = str(request.document)
    resp = requests.head(doc_url, allow_redirects=True)
    doc_type = resp.headers.get("Content-Type","").lower()

    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only pdf, docx, eml files allowed")
    
    file_extension = allowed_types[doc_type]

    # Prepare temp file path
    parsed = urlparse(doc_url)
    filename = os.path.basename(parsed.path) or f"tempfile.{file_extension}"
    temp_path = f"/tmp/{filename}"
    
    return file_extension, temp_path