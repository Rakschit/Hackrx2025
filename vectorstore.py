from pinecone import Pinecone, ServerlessSpec
import os

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
    if( is_id_there and is_id_there.matches)