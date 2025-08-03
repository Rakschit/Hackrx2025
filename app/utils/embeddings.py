from pinecone import Pinecone, ServerlessSpec
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
# from google import genai
import google.generativeai as genai

index_name = "hackrxindex"
DATA_PROCESSING_VERSION = "v1"

pc_key=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY")) 

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_pinecone_index():
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(index_name)

def get_embeddings_from_namespace(pinecone_index, id_to_check, top_k: int = 1000):
    dummy_vector = [0] * 768  # Adjust dimension
    result = pinecone_index.query(
        vector=dummy_vector,
        top_k=top_k,
        namespace=id_to_check,
        include_metadata=True,
        include_values=True
    )
    matches = result.to_dict().get("matches", [])

    # Convert to desired structure
    embeddings = [
        {"embedding": m["values"], "metadata": m["metadata"]}
        for m in matches
    ]

    return embeddings

def store_embeddings(chunks: list, index_id: str, pinecone_index):
    response = genai.embed_content(
        model="models/gemini-embedding-001",
        content=chunks,  
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768
    )

    embeddings_list = response['embedding']

    vectors_to_upsert = []
    embeddings = []

    for i, emb_vector in enumerate(embeddings_list):
        metadata = {
            "text": chunks[i],
            "version": DATA_PROCESSING_VERSION
        }

        vectors_to_upsert.append((
            f"{index_id}-{i}",
            emb_vector, 
            metadata
        ))

        # For the return value
        embeddings.append({
            "embedding": emb_vector, 
            "metadata": metadata
        })

    pinecone_index.upsert(
        vectors=vectors_to_upsert,
        namespace=index_id
    )
    return embeddings

def create_embeddings(chunks,index_id, pinecone_index):
    embeddings = store_embeddings(chunks, index_id, pinecone_index)
    return embeddings

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
        query_response = genai.embed_content(
            model="models/gemini-embedding-001", # models/gemini-embedding-001
            content=[question],
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768
        )
        # Extract the embedding vector
        query_embedding = np.array(
            query_response['embedding']
        ).reshape(1, -1)

        # Compute cosine similarity
        similarity_scores = cosine_similarity(query_embedding, chunk_vectors)[0]

        # Sort indices in descending order of similarity
        ranked_indices = np.argsort(similarity_scores)[::-1][:top_k]

        # Collect top matches with their similarity score
        results = [(similarity_scores[i], embeddings[i]) for i in ranked_indices]

        results_all[question] = results

    return results_all

def generate_answer_with_groq(question: str, top_matches_all: dict, top_k: int = 3):

    # search_relevant_chunks returns a dict {question: [(score, {embedding, metadata})]}
    top_matches = top_matches_all[question][:top_k]

    # 2. Build context string from metadata["text"]
    context = "\n\n".join([
        match_item["metadata"]["text"] for _, match_item in top_matches
    ])

    # 3. Construct prompt
    prompt = f"""Answer clearly and concisely using only the information from the provided document, in one short paragraph.
    If there are minor typos or formatting errors in the document, correct them when forming the answer.
    If the answer is not found in the document, reply with "I don't know" and briefly explain why it might be missing.
    Do not use external knowledge and keep the response strictly based on the given text.


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

import json
import google.generativeai as genai

generative_model = genai.GenerativeModel("gemini-2.5-flash-lite")

def generate_answers_with_gemini(questions, top_matches_all, top_k=3):
    if isinstance(questions, str):
        questions = [questions]

    qa_blocks = []
    for question in questions:
        if question not in top_matches_all or not top_matches_all[question]:
            qa_blocks.append(f"Question: {question}\nContext: (no context available)\n")
            continue

        top_matches = top_matches_all[question][:top_k]

        context_parts = []
        for match_item in top_matches:
            if isinstance(match_item, tuple):
                context_parts.append(match_item[1]["metadata"]["text"])
            else:
                context_parts.append(match_item["metadata"]["text"])

        context = "\n\n".join(context_parts)
        qa_blocks.append(f"Question: {question}\nContext:\n{context}\n")

    combined_prompt = f"""
    Answer each question based only on its context.
    If context is missing, answer "I don't have any context to answer this question."
    Return only the answers, each answer separated by a blank line. 
    Do not include extra text or numbering.

    Questions and contexts:

    {chr(10).join(qa_blocks)}
    """

    response = generative_model.generate_content(combined_prompt)
    
    return response
