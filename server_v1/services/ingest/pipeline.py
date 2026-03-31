from core.logging import get_logger
from services.ingest.repo_handler import clone_repo, cleanup_repo
from services.ingest.file_traversal import extract_all_nodes
from services.ingest.storage import store_nodes_in_neo4j
import uuid

logger = get_logger(__name__)

def run_ingest_pipeline(repo_url: str):
    logger.info("Initializing ingestion pipeline...")
    session_id, repo_path = clone_repo(repo_url)
    
from fastapi import HTTPException

# ... existing code ...

def run_ingest_pipeline(repo_url: str):
    logger.info("Initializing ingestion pipeline...")
    session_id, repo_path = clone_repo(repo_url)
    
    logger.info("Commencing deep code extraction & file traversal...")
    all_nodes = extract_all_nodes(repo_path)
    
    if len(all_nodes) > 2000:
        logger.error(f"Repository is too large (found {len(all_nodes)} nodes). To save server memory and API credits, setting strict limit of 2000 nodes.")
        cleanup_repo(repo_path)
        raise HTTPException(
            status_code=400, 
            detail=f"Repository is too large! Found {len(all_nodes)} code chunks, but the strict limit for this free server is 2000 to prevent crashing and save free tier API credits."
        )
    
    logger.info("Cleaning up temporary repository files...")
    cleanup_repo(repo_path)
    
    if not all_nodes:
        logger.info("No readable code documents found in the repository.")
        return session_id

    logger.info(f"Successfully extracted {len(all_nodes)} structural code elements. Starting storage process...")
    store_nodes_in_neo4j(all_nodes, session_id)
    
    logger.info("Pipeline execution successfully concluded. Repository is now ready for analysis! 🎉")
    return session_id



