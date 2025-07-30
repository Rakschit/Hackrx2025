from fastapi import FastAPI, File, UploadFile
import shutil
import os
from file_utils import extract_text_from_pdf, chunk_text
from embeddings_utils import normalize_text, get_content_hash
from vectorstore import get_pinecone_index, check_storedEmbeddings, create_embeddings 
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
#import time

load_dotenv()
    
app = FastAPI()
"""
def process_file(file: UploadFile):
    file_type =  os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        return { "error" : "Invalid file type",
            "reason": "Only accepts pdf, docx and eml files"
        }
    
    yield "File type validated.\n"

    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Passing file_utils Function
    if file_type == ".pdf":
        yield "Extracting text from PDF...\n"
        file_content = extract_text_from_pdf(temp_path)
        yield f"Text extraction complete. Extracted {len(file_content)} characters.\n"
        
    yield "Processing complete.\n"

    try:
        os.remove(temp_path)
    except Exception as ae:
        print(f"Failed to delete temp file:{ae}")
"""
@app.post("/hackrx/run")

async def upload_file(file: UploadFile = File(...)):
      
    msg =""
    file_type =  os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        error = {
            "error" : "Invalid file type",
            "reason": "Only accepts pdf, docx and eml files"
        }
        return JSONResponse(content=error)
    
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Passing file_utils Function
    if file_type == ".pdf":
        file_content = extract_text_from_pdf(temp_path)

    
    # Passing embeddings_utils Function
    file_content = normalize_text(file_content)
    file_id = get_content_hash(file_content)
    
    chunks = chunk_text(file_content)
    
    # Passing vectorstore Function
    pinecone_index, pc_api = get_pinecone_index()
    
    is_id_there = check_storedEmbeddings(pinecone_index,file_id)

    matches = is_id_there.get("matches", [])
    is_id_value = matches[0]["id"] if matches else None

    if(is_id_there["matches"]):
        msg = "vector for the file is already there, upserted"
    else:
        msg = "vector not present"
        create_embeddings(chunks, file_id, pinecone_index)
    try:
        os.remove(temp_path)
    except Exception as ae:
        print(f"Failed to delete temp file:{ae}")

    return{
        "filename": file.filename,
        "file id" : file_id,
        "text": file_content[:21],
        "msg": msg,
        "id_value": is_id_value
    }

import httpx

COLAB_URL = "https://ed89cb3e8940.ngrok-free.app/how_are_you"

@app.post("/test")
async def greetings():
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.get(COLAB_URL)  # HTTPS request
        colab_reply = response.text
        
    return {
        "local": "Hello",
        "colab": colab_reply
    }