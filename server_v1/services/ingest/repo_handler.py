import uuid, git, os, shutil
from core.logging import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

def clone_repo(github_url: str):
    session_id = str(uuid.uuid4())
    local_path = os.path.join("data", "repos", session_id)
    try:
        logger.info("Cloning the repository from GitHub...")
        git.Repo.clone_from(github_url, local_path)
        logger.info("Repository cloned successfully! 🚀")
        return session_id, local_path
    except Exception as e:
        logger.error(f"Failed to clone repo : {github_url} | Error : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone repository: {str(e)}"
        )

def cleanup_repo(repo_path: str):
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logger.info("Temporary files cleaned up.")
        else:
            logger.warning(f"Repo path not found during cleanup: {repo_path}")
    
    except Exception as e:
        logger.error(f"Failed to cleanup repo: {repo_path} | Error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup repository: {str(e)}"
        )