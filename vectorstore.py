from pinecone import Pinecone, ServerlessSpec
import numpy as np
import os

index_name = "hackrxindex"

def get_pinecone_index():

    api_key=os.getenv("PINECONE_API_KEY")
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    has_pinecone_key = bool(api_key)
    """
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    """
    # return pc.Index(index_name), has_pinecone_key
    return has_pinecone_key


def check_storedEmbeddings(pinecone_index,id_to_check):
    dummy_vector = np.zeros(384).tolist()
    is_id_there = pinecone_index.query(
        vector = dummy_vector,
        top_k = 1,
        include_metadata = True,
        filter = {"file_id": id_to_check}
    )
    return is_id_there