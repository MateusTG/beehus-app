from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Broadcasts a JSON message to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # If sending fails, we might want to remove the dead connection
                # typically handled in disconnect, but safe to ignore here for simplicity
                pass
