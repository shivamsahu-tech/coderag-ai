from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import Cookie, Response
from uuid import uuid4
from services.retreive.pipeline import run_retreival_pipeline


router = APIRouter()

class RetreivalRequest(BaseModel):
    session_id: str
    query: str


@router.post("")
async def retreive_answer(
    request: RetreivalRequest,
    response: Response,
    user_id: str = Cookie(None) 
):  
    print("Received retreive request:", request)
    
    if user_id is None:
        user_id = str(uuid4())
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=30 * 24 * 60 * 60,  
            httponly=True, 
            samesite="lax" 
        )

    llm_response = run_retreival_pipeline(
        session_id=request.session_id,
        query=request.query,
        user_id=user_id
    )

    return {
        "status": "success",
        "llm_response": llm_response,
        "user_id": user_id  
    }