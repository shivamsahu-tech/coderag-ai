# This file was edited to switch from a local embedding service to using Google Gemini for embeddings.
# The previous implementation using a local service is commented out below for reference.
import google.generativeai as genai 
from dotenv import load_dotenv
import os, requests
from core.logging import get_logger
from fastapi import HTTPException
import time

logger = get_logger(__name__)

load_dotenv()

if not os.getenv("LLM_API_KEY"):
    raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
genai.configure(api_key=os.getenv("LLM_API_KEY"))

vector_dim = int(os.getenv("VECTOR_DIMENSION") or 384)

def get_embeddings(chunks: list[str]) -> list[list[float]]:
    logger.info(f"got chunks of size {len(chunks)} for embedding")
    # if len(chunks) == 1:
    #     task_type="CODE_RETRIEVAL_QUERY"
    # else:
    #     task_type="RETRIEVAL_DOCUMENT"

    embedding_result = []
    bundle_size = 100

    for i in range(0, len(chunks), bundle_size):
        bundle_chunks = chunks[i:i+bundle_size]

        try:
            response = genai.embed_content(
                model="gemini-embedding-001",
                content=bundle_chunks,
                task_type="RETRIEVAL_DOCUMENT" ,
                output_dimensionality=vector_dim 
            )
            logger.info(f"embedding successfull for {i} : {i+bundle_size}")
            if i+bundle_size < len(chunks):
                logger.info("sleeping for 61")
                time.sleep(61)
                logger.info("waked up!!")
            embedding_result.extend(response['embedding'])
        
        except Exception as e:
            logger.error(f"An error occurred during embedding: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed the chunks | Error : {e}"
            )
    
    return embedding_result



# default dimension is 384
def get_embeddings_local(chunks):
    response = requests.post(
        "http://localhost:8001/embed",
        json={"chunks": chunks},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.json()["embeddings"]


# Example usage:# c
# chunks = ["This is a sample text.", "Another piece of text."]
# embeddings = get_embeddings(chunks)
# print(embeddings)