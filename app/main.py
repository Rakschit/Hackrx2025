from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, HttpUrl
from fastapi.responses import JSONResponse
import os, shutil
from typing import List
import requests
from urllib.parse import urlparse

from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import ex

app = FastAPI()

BEARER_API_KEY = os.getenv("BEARER_API_KEY")

def verify_bearer(authorization: str = Header(...)):
    if not BEARER_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfiguration: BEARER_API_KEY not set")
    if authorization != f"Bearer {BEARER_API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

class RunRequest(BaseModel):
    document: HttpUrl
    questions: List[str]


"""
def save_and_extract(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extension:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only pdf, docx, eml allowed."
        )
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    if ext == ".pdf":
        file_content = extract_text_from_pdf(temp_path)
    return file_content

"""

@app.post("/hackrx/run")
async def run_query(
    request: RunRequest, _: None = Depends(verify_bearer)):

    if not request.questions or not all(isinstance(q, str) for q in request.questions):
        raise HTTPException(status_code=400, detail="Questions must be a list of strings")
    
    doc_url = str(request.document)
    resp = requests.head(doc_url, allow_redirects=True)
    doc_type = resp.headers.get("Content-Type","").lower()

    # CHECKING EXTENSION
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "message/rfc822": "eml"
    }

    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only pdf, docx, eml files allowed")
    
    ext = allowed_types[doc_type]

    parsed = urlparse(doc_url)
    filename = os.path.basename(parsed.path) or "tempfile"
    temp_path = f"/tmp/{filename}"

    try:
        r = requests.get(doc_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {e}")

    with open(temp_path, "wb") as f:
        f.write(r.content)
        
    # Extract text
    if ext == "pdf":
        text = extract_text_from_pdf(temp_path)

    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    return {
        "document": doc_url,
        "questions": request.questions,
        "text_preview": text[:200]
    }





"""
    file_type = os.path.splitext(file.filename)[1].lower()
    

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

    new_text = ex(file_content)r
"""

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text