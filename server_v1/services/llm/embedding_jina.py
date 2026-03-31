import os
import re
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

# --- Config ---------------------------------------------------------------
_BATCH_SIZE = 50          # chunks per top-level batch
_INTER_BATCH_DELAY_S = 1  # seconds between top-level batches (TPM pacing)
_EMBEDDING_DIM = 1536     # jina-code-embeddings-1.5b actual output dimension (confirmed from logs)
# --------------------------------------------------------------------------


def _sanitize(text: str) -> str:
    """Strip content that Jina's encoder chokes on (null bytes, lone surrogates, etc.)."""
    # Remove null bytes
    text = text.replace("\x00", " ")
    # Re-encode as UTF-8 ignoring lone surrogates
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    # Collapse very long unbroken lines (e.g. minified JS / base64 blobs)
    text = re.sub(r"[^\n]{4000,}", lambda m: m.group()[:4000] + "…", text)
    return text.strip() or "<empty>"


def _single_request(chunks: list[str], task_type: str, max_retries: int = 4) -> requests.Response:
    """One POST to Jina with multi-attempt retry logic for 429 rate limits and 104 TCP resets."""
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}",
    }
    payload = {
        "model": "jina-code-embeddings-1.5b",
        "task": task_type,
        "truncate": True,
        "input": chunks,
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=90)
            
            if resp.status_code == 429:
                logger.warning(f"Rate-limited by Jina API on attempt {attempt+1}/{max_retries}. Sleeping 60s then retrying...")
                time.sleep(60)
                continue
                
            return resp
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network Connection dropped by Jina API ({e}). Retrying attempt {attempt+1}/{max_retries} in 10 seconds...")
            time.sleep(10)
    
    # If all generic retries fail, execute a final one that will raise naturally
    logger.error("Final network retry attempt initiating...")
    return requests.post(url, json=payload, headers=headers, timeout=90)


def _embed_with_bisect(chunks: list[str], task_type: str) -> list[list[float]]:
    """
    Embed a list of chunks robustly.

    Strategy (when a batch returns 400):
      1. Try the full batch once.
      2. On 400, split in half and recurse on each half.
      3. When down to a single chunk, sanitize it and retry once.
      4. If still 400, emit a zero-vector so the ingestion never dies.

    This guarantees we always return exactly len(chunks) vectors.
    """
    if not chunks:
        return []

    # ── Single-chunk base case ──────────────────────────────────────────────
    if len(chunks) == 1:
        resp = _single_request(chunks, task_type)
        if resp.ok:
            return [resp.json()["data"][0]["embedding"]]

        # Try sanitized version
        cleaned = [_sanitize(chunks[0])]
        resp2 = _single_request(cleaned, task_type)
        if resp2.ok:
            logger.warning("Chunk required sanitization before embedding.")
            return [resp2.json()["data"][0]["embedding"]]

        # Give up on this chunk — zero-vector placeholder
        logger.warning(
            f"Skipping unencodable chunk (len={len(chunks[0])}). "
            f"Jina error: {resp2.text[:120]}"
        )
        return [[0.0] * _EMBEDDING_DIM]

    # ── Multi-chunk: try the whole group first ──────────────────────────────
    resp = _single_request(chunks, task_type)
    if resp.ok:
        return [item["embedding"] for item in resp.json()["data"]]

    if resp.status_code != 400:
        # Non-400 failures (5xx etc.) — raise so the outer loop can surface them
        resp.raise_for_status()

    # 400 on a multi-chunk batch → bisect
    logger.warning(
        f"400 on batch of {len(chunks)} chunks. Bisecting to isolate bad chunk(s)..."
    )
    mid = len(chunks) // 2
    left = _embed_with_bisect(chunks[:mid], task_type)
    right = _embed_with_bisect(chunks[mid:], task_type)
    return left + right


def get_embeddings(chunks: list[str]) -> list[list[float]]:
    logger.info(f"Got total chunks of size {len(chunks)} for embedding")

    task_type = "nl2code.query" if len(chunks) == 1 else "nl2code.passage"
    logger.info(
        f"Task type: '{task_type}' | "
        f"Top-level batch size: {_BATCH_SIZE} | "
        f"Total batches: {(len(chunks) + _BATCH_SIZE - 1) // _BATCH_SIZE}"
    )

    embedding_result: list[list[float]] = []
    total_batches = (len(chunks) + _BATCH_SIZE - 1) // _BATCH_SIZE

    for batch_num, i in enumerate(range(0, len(chunks), _BATCH_SIZE)):
        batch = chunks[i : i + _BATCH_SIZE]
        logger.info(
            f"[Batch {batch_num + 1}/{total_batches}] "
            f"chunks {i}–{i + len(batch) - 1} | ~{len(batch) * 150} est. tokens"
        )

        try:
            batch_embeddings = _embed_with_bisect(batch, task_type)
            embedding_result.extend(batch_embeddings)
            logger.info(
                f"[Batch {batch_num + 1}/{total_batches}] "
                f"Done — {len(batch_embeddings)} vectors collected."
            )
        except Exception as e:
            logger.error(f"Unrecoverable error on batch {batch_num + 1}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed batch {batch_num + 1}: {e}",
            )

        # Pace requests to stay under the 2M TPM free-tier cap
        if i + _BATCH_SIZE < len(chunks):
            time.sleep(_INTER_BATCH_DELAY_S)

    return embedding_result