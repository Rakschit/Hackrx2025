from pinecone import Pinecone, ServerlessSpec
from google import genai
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq

index_name = "hackrxindex"
DATA_PROCESSING_VERSION = "v1"

pc_key=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY")) 

gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_pinecone_index():
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name)

def get_embeddings_from_namespace(pinecone_index, id_to_check, top_k: int = 1000):

    dummy_vector = [0] * 3072  # Adjust based on embedding dimension
    result = pinecone_index.query(
        vector=dummy_vector,
        top_k= top_k,
        namespace=id_to_check,
        include_metadata=True,
        include_values=True
    )
    matches = result.to_dict().get("matches", [])

    return matches

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


def search_relevant_chunks(questions, embeddings: list, top_k: int = 3):
    """
    Given one or more questions and pre-computed embeddings,
    returns the top_k relevant chunks for each question using Gemini embeddings.
    """
    if not embeddings:
        raise ValueError("No embeddings were provided to search_relevant_chunks.")

    # Ensure questions is a list
    if isinstance(questions, str):
        questions = [questions]

    # Precompute chunk vectors once
    chunk_vectors = np.array([np.array(item["embedding"]) for item in embeddings])

    results_all = {}

    for question in questions:
        # Generate embedding for the question using Gemini
        query_response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[question]
        )

        # Extract the embedding vector
        query_embedding = np.array(
            query_response.embeddings[0].values
        ).reshape(1, -1)

        # Compute cosine similarity
        similarity_scores = cosine_similarity(query_embedding, chunk_vectors)[0]

        # Sort indices in descending order of similarity
        ranked_indices = np.argsort(similarity_scores)[::-1][:top_k]

        # Collect top matches with their similarity score
        results = [(similarity_scores[i], embeddings[i]) for i in ranked_indices]

        results_all[question] = results

    return results_all



def generate_answer_with_groq(question: str, embeddings: list, top_k: int = 3):

    # 1. Retrieve top matching chunks for the question
    top_matches_all = search_relevant_chunks(question, embeddings, top_k)

    # search_relevant_chunks returns a dict {question: [(score, {embedding, metadata})]}
    top_matches = top_matches_all[question]

    # 2. Build context string from metadata["text"]
    context = "\n\n".join([
        match_item["metadata"]["text"] for _, match_item in top_matches
    ])

    # 3. Construct prompt
    prompt = f"""Answer clearly and concisely using only the information from the provided document, in one short paragraph.
        If the answer is not found in the document, reply with "I don't know" and briefly explain why it might be missing.

        Context:
        {context}

        Question:
        {question}
    """

    # 4. Call Groq's chat completion
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model="gemma2-9b-it",
    )

    # 5. Return the answer text
    return chat_completion.choices[0].message.content.strip()
