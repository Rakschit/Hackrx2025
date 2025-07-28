from fastapi import FastAPI
from pydantic import BaseModel
import requests, faiss, pickle
from sentence_transformers import SentenceTransformer
import uvicorn

# Load everything at startup
index = faiss.read_index("vector.index")
with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
def ask(req: QueryRequest):
    # 1. Find relevant text
    q_emb = embed_model.encode([req.query], convert_to_numpy=True)
    _, indices = index.search(q_emb, 5)
    relevant_clauses = [chunks[i] for i in indices[0]]

    # 2. Build prompt
    context = "\n\n".join(relevant_clauses)
    prompt = f"""
    User query:
    {req.query}

    Relevant clauses:
    {context}

    Instructions:
    1. Extract details (age, gender, procedure, location, policy duration).
    2. Decide approval/rejection.
    3. Justify using clauses.
    4. Return valid JSON with: decision, amount, justification, used_clauses.
    """

    # 3. Call local Mistral via Ollama
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )
    return {"result": resp.json()["response"]}

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello! API is running."}

if __name__ == "__main__":
    port = 8000  # You can change this
    print(f"Starting API on http://127.0.0.1:{port}")
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)