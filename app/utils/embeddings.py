from pinecone import Pinecone, ServerlessSpec
from google import genai
import os

index_name = "hackrxindex"
DATA_PROCESSING_VERSION = "v1"

pc_key=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY")) 

gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key)

def get_pinecone_index():
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name)

def check_storedEmbeddings(pinecone_index, id_to_check):
    # Create a dummy vector of the correct dimension (e.g., 768 for gemini)
    dummy_vector = [0] * 3072  # for gemini-embedding-001

    result = pinecone_index.query(
        vector=dummy_vector,
        top_k=1,
        namespace=id_to_check,   # search only in this namespace
        include_metadata=True
    )
    return result.to_dict()

def store_embeddings(chunks, index_id, pinecone_index):
    

    # Generate all embeddings in one request (contents = list of strings)
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents = chunks  # pass the entire list
    )

    embeddings = []
    for i, emb in enumerate(response.embeddings):
        metadata = {
            "text": chunks[i],
            "version": DATA_PROCESSING_VERSION
        }

        embeddings.append((
            f"{index_id}-{i}",     # unique ID
            emb.values,     # embedding vector from list
            metadata
        ))

    # Upload all embeddings to Pinecone
    pinecone_index.upsert(
        vectors=embeddings,
        namespace = f"index_id",
    )

def create_embeddings(chunks,index_id, pinecone_index):
    store_embeddings(chunks, index_id, pinecone_index)
    return 


