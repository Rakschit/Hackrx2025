from pinecone import Pinecone, ServerlessSpec
import os
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

model = SentenceTransformer("all-MiniLM-L6-v2")

index_name = "hackrxindex"

def get_pinecone_index():

    api_key=os.getenv("PINECONE_API_KEY")
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    has_pinecone_key = bool(api_key)

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name), has_pinecone_key
    

def check_storedEmbeddings(pinecone_index,id_to_check):
    is_id_there = pinecone_index.query(
        vector = [0] * 384,
        top_k = 1,
        filter = {"file_id": id_to_check},
        include_metadata = True
    )
    return is_id_there.to_dict()

def create_embeddings(chunks, index_id, pinecone_index):
    embeddings = model.encode(chunks, convert_to_numpy=True)
    embeddings = normalize(embeddings)
    dimension = embeddings.shape[1]
    
    vectors_to_upsert = []

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
    
    return {"message": "New vector is upserted"}