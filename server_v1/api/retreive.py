from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import Cookie, Response
from uuid import uuid4
from services.agent.create_agent import run_agent


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
        print(f"DEBUG: New user_id generated: {user_id}")
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=30 * 24 * 60 * 60,  
            httponly=True, 
            samesite="lax" 
        )

    print(f"DEBUG: Processing request for user_id={user_id} session_id={request.session_id}")

    llm_response = run_agent(
        query=request.query,
        session_id=request.session_id,
        user_id=user_id,
    )

    return {
        "status": "success",
        "llm_response": llm_response,
        "user_id": user_id  
    }