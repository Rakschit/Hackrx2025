from fastapi import FastAPI, File, UploadFile
import shutil
import os

app = FastAPI()

@app.post("/hackrx/run")
async def upload_file(file: UploadFile = File(...)):
    
    file_type =  os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        return {"Error: Invalid file type"}
    
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    size = os.path.getsize(temp_path)
    
    return{
        "filename": file.filename
    }
