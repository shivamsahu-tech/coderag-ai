import asyncio
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.loop = None

    async def connect(self, ws: WebSocket, req_id: str):
        await ws.accept()
        if req_id not in self.active_connections:
            self.active_connections[req_id] = []
        self.active_connections[req_id].append(ws)

    def disconnect(self, ws: WebSocket, req_id: str):
        if req_id in self.active_connections:
            self.active_connections[req_id].remove(ws)
            if not self.active_connections[req_id]:
                del self.active_connections[req_id]

    async def send_log(self, message: str, req_id: str):
        if req_id in self.active_connections:
            # We must iterate over a copy or handle disconnected websockets gracefully.
            for connection in self.active_connections[req_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

manager = ConnectionManager()
