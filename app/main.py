from fastapi import FastAPI, Depends
from pydantic import BaseModel, HttpUrl
import os, shutil
from typing import List

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import ex

app = FastAPI()

class RunRequest(BaseModel):
    document: HttpUrl
    questions: List[str]

@app.post("/hackrx/run")
async def run_query(request: RunRequest, _: None = Depends(verify_bearer)):
    file_extension, temp_path = validate_request(request)
    
    # Extract text
    if file_extension == "pdf":
        text = extract_text_from_pdf(temp_path)

    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    return {
        "extension": file_extension,
        "questions": request.questions,
        "text_preview": text[:200]
    }

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text