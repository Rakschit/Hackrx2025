from fastapi import FastAPI, File, UploadFile
import shutil
import os
from file_utils import extract_text_from_pdf

app = FastAPI()

@app.post("/hackrx/run")
async def upload_file(file: UploadFile = File(...)):
    
    file_type =  os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        return {"Error: Invalid file type \nOnly accepts pdf,docx and eml files"}
    
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    size = os.path.getsize(temp_path)
    
    if file_type == ".pdf":
        file_content = extract_text_from_pdf(temp_path)

    try:
        os.remove(temp_path)
    except Exception as ae:
        print(f"Failed to delete temp file:{ae}")

    return{
        "filename": file.filename,
        "size": size,
        "text": file_content[:21]
    }
