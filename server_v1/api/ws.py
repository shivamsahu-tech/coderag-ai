from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.websocket import manager

router = APIRouter()

@router.websocket("/logs/{req_id}")
async def websocket_logs(websocket: WebSocket, req_id: str):
    await manager.connect(websocket, req_id)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, req_id)
