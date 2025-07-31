from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from app.utils.text_extraction import extract_text_from_pdf
from app.utils.data_processing import ex
import os, shutil

app = FastAPI()

@app.post("/")
def read_root():
    text = "Hello Railway!"
    return text

@app.post("/hackrx/run")
async def upload_file(file: UploadFile = File(...)):
    file_type = os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

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

    new_text = ex(file_content)

    return new_text
