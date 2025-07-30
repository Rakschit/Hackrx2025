from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import hashlib # add to requirements


model = SentenceTransformer("all-MiniLM-L6-v2")

def normalize_text(text):
    text = " ".join(text.split())
    return text

def get_content_hash(normalized):
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def create_embeddings(chunks, index_id):
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
        
    return {"message": "New vector is upserted"}



