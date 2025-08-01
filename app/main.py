from fastapi import FastAPI, Depends
import os, shutil

from app.utils.validators import verify_bearer, validate_request
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import clean_text
from app.models import RunRequest

app = FastAPI()

@app.post("/hackrx/run")
async def run_query(request: RunRequest, _: None = Depends(verify_bearer)):
    
    file_extension, temp_path = validate_request(request)

    # Extract text
    if file_extension == "pdf":
        text,page = extract_text_from_pdf(temp_path)

    text = clean_text(text,page)    

    # Removing temporary file after processing
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass

    return {
        "extension": file_extension,
        "questions": request.questions,
        "page": page,
    }

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text