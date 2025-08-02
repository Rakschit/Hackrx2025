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
# text-embedding-004, gemini-embedding-001
def create_embeddings(chunks, index_id):
    gemini_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key)

    all_embeddings = []
    API_BATCH_SIZE = 0
    for i in range(0, len(chunks), API_BATCH_SIZE):
        # Get the current batch of chunks
        request_batch = chunks[i:i+API_BATCH_SIZE]

        try:
            # Make the API call for the current batch
            response = client.embed_content(
                model="models/embedding-001",  # Using the 'models/' prefix is good practice
                content=request_batch,
                task_type="RETRIEVAL_DOCUMENT"
            )

            # Process the response for the current batch
            for j, emb in enumerate(response['embedding']):
                # Calculate the original index of the chunk
                original_chunk_index = i + j
                
                metadata = {
                    "text": chunks[original_chunk_index],
                    "file_id": index_id,
                    "chunk_id": f"{index_id}-{original_chunk_index}",
                    "version": DATA_PROCESSING_VERSION
                }
                
                all_embeddings.append((
                    f"{index_id}-{original_chunk_index}",  
                    emb,         
                    metadata            
                ))

        except Exception as e:
            print(f"An error occurred during batch {i//API_BATCH_SIZE + 1}: {e}")
            # You might want to decide here if you want to continue or stop
            # For now, we'll just print and continue
            continue

    return all_embeddings



    
    # Process the chunks in batches of 100
    
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