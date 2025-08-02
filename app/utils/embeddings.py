from pinecone import Pinecone, ServerlessSpec
from google import genai
import os

index_name = "hackrxindex"
DATA_PROCESSING_VERSION = "v1"

pc_key=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY")) 

def get_pinecone_index():

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name)

"""
def check_storedEmbeddings(pinecone_index,id_to_check):
    is_id_there = pinecone_index.query(
        vector = [0] * 384,             # replace with gemini option
        top_k = 1,
        filter = {"file_id": id_to_check},
        include_metadata = True
    )
    return is_id_there.to_dict()
"""

def store_embeddings(chunks, index_id, pinecone_index):
    gemini_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key)

    response = client.models.embed_content(
        
        model="gemini-embedding-001",  # Gemini embedding model
        contents = chunks              # pass the whole list
    )

    embeddings = []
    for i, emb in enumerate(response.embeddings):
        metadata = {
            "text": chunks[i],
            "file_id": index_id,
            "version": DATA_PROCESSING_VERSION
        }
        
        embeddings.append((
            f"{index_id}-{i}",  
            emb.values,         
            metadata            
        ))
    index = pc.Index(pinecone_index)
    index.upsert(vector = embeddings)

def create_embeddings(chunks,index_id, pinecone_index):
    store_embeddings(chunks, index_id, pinecone_index)
    return 


