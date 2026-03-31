from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from core.logging import req_id_var

from services.ingest.pipeline import run_ingest_pipeline

router = APIRouter()

class IngestRequest(BaseModel):
    repo_url: str
    req_id: Optional[str] = None


@router.post("/")
def ingest_repo(request: IngestRequest):
    if request.req_id:
        req_id_var.set(request.req_id)
        
    session_id = run_ingest_pipeline(request.repo_url)
    return {"status" : "success", "session_id" : session_id}