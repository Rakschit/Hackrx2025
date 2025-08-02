from pinecone import Pinecone, ServerlessSpec
from google import genai
import os

index_name = "hackrxindex"
DATA_PROCESSING_VERSION = "v1" 

def get_pinecone_index():

    pc_key=os.getenv("PINECONE_API_KEY")
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    # DEBUGGING
    has_pinecone_key = bool(pc_key)

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name), has_pinecone_key

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

def create_embeddings(chunks, index_id, pinecone_index):
    gemini_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key)

    response = client.models.embed_content(
        # text-embedding-004, gemini-embedding-001
        model="text-embedding-004",  # Gemini embedding model
        contents=chunks              # pass the whole list
    )

    embeddings = []
    for i, emb in enumerate(response.embeddings):
        metadata = {
            "text": chunks[i],
            "file_id": index_id,
            "chunk_id": f"{index_id}-{i}",
            "version": DATA_PROCESSING_VERSION
        }
        
        embeddings.append((
            f"{index_id}-{i}",  
            emb.values,         
            metadata            
        ))


    embeddings = []
    for i, emb in enumerate(response.embeddings):
        embeddings.append({
            "chunk_id": f"{index_id}-{i}",
            "embedding": emb.values,
            "text": chunks[i],
            "file_id": index_id
        })
    pinecone_index.upsert(emb=embeddings)

    return "embeddings upserted"

"""
    for i, vector in enumerate(embeddings):
        vectors_to_upsert.append(
            {
                "id": f"{index_id}-{i}",
                "values": vector.tolist(),
                "metadata":{
                "text": chunks[i],
                "file_id": index_id
            }
        }
    )
    pinecone_index.upsert(vectors=vectors_to_upsert)
"""

    


"""
def has_embeddings(file_id):
    return
"""