from fastapi import FastAPI, File, UploadFile
import shutil
import os
from file_utils import extract_text_from_pdf, chunk_text
from embeddings_utils import normalize_text, get_content_hash, create_embeddings 
from vectorstore import get_pinecone_index, check_storedEmbeddings
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

@app.post("/hackrx/run")
async def upload_file(file: UploadFile = File(...)):
    
    file_type =  os.path.splitext(file.filename)[1].lower()
    allowed = [".pdf", ".docx", ".eml"]

    if file_type not in allowed:
        return { "error" : "Invalid file type",
            "reason": "Only accepts pdf, docx and eml files"}
    
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

    index_path, chunks_path = create_embeddings(chunks)

    # Passing vectorstore Function
    pinecone_index = get_pinecone_index()
    is_id_there = check_storedEmbeddings(pinecone_index,file_id)
    if(is_id_there["matches"]):
        return {"message":"vector for the file is already there","upserted":"no"}
    
    else:
        create_embeddings(chunks, file_id)


    try:
        os.remove(temp_path)
    except Exception as ae:
        print(f"Failed to delete temp file:{ae}")

    return{
        "filename": file.filename,
        "file id" : file_id,
        "text": file_content[:21],
        "index": index_path,
        "chunks": chunks_path
    }


@app.post("/hackrx/hello")
async def run():
    return {"message": "hello"}