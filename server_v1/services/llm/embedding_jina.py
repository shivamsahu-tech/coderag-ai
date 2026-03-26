import os
import requests
import time
from dotenv import load_dotenv
from fastapi import HTTPException
from core.logging import get_logger

logger = get_logger(__name__)
load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
if not JINA_API_KEY:
    raise ValueError("Jina API key not found. Please set the JINA_API_KEY environment variable.")

def get_embeddings(chunks: list[str]) -> list[list[float]]:
    logger.info(f"Got total chunks of size {len(chunks)} for embedding")

    # 1. Dynamically set the task type
    # If there is only 1 item, it's a search query. Otherwise, it's code being stored.
    if len(chunks) == 1:
        task_type = "nl2code.query"
        logger.info("Single chunk detected: Setting Jina task to 'nl2code.query'")
    else:
        task_type = "nl2code.passage"
        logger.info("Multiple chunks detected: Setting Jina task to 'nl2code.passage'")

    embedding_result = []
    
    # Updated bundle size. 500 chunks * ~150 tokens = ~75,000 tokens per request.
    bundle_size = 500 
    
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }

    for i in range(0, len(chunks), bundle_size):
        bundle_chunks = chunks[i:i+bundle_size]
        
        # Calculate roughly how many tokens this batch contains
        estimated_tokens = len(bundle_chunks) * 150
        logger.info(f"Sending batch {i} to {i + len(bundle_chunks)} (Est. ~{estimated_tokens} tokens)")

        # 2. Inject the dynamic task_type into the payload
        payload = {
            "model": "jina-code-embeddings-1.5b", 
            "task": task_type, 
            "truncate": False,
            "input": bundle_chunks
        }

        try:
            # We use a slight timeout definition to prevent hanging on massive batches
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            # If we hit a rate limit (429), handle it gracefully
            if response.status_code == 429:
                logger.warning("Hit Jina AI rate limit. Sleeping for 60 seconds...")
                time.sleep(60)
                # Retry the exact same request once
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
            response.raise_for_status() 
            
            response_data = response.json()
            
            batch_embeddings = [item["embedding"] for item in response_data["data"]]
            embedding_result.extend(batch_embeddings)
            
            logger.info("Batch embedding successful.")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error during embedding: {e} | Response: {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed the chunks due to API error: {response.text}"
            )
        except Exception as e:
            logger.error(f"An error occurred during embedding: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed the chunks | Error : {e}"
            )
    
    return embedding_result