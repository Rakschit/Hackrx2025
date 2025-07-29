from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss
import numpy as np
import pickle

model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embeddings(chunks):
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    embeddings = normalize(embeddings)
    dimension = embeddings.shape[1]
    
    index = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIDMap(index)
    ids = np.arange(len(embeddings))
    index.add_with_ids(embeddings, ids)

    # faiss.write_index(index, f"indexes/{file_name}vector.index")
    index_path = "/tmp/vector.index"
    chunks_path = "/tmp/chunks.pkl"
    faiss.write_index(index, index_path)
    
    #with open(f"pickle/{file_name}chunks.pkl", "wb") as f:
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)
        
    return index_path, chunks_path