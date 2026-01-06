from typing import List, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time inventory updates.
    """
    def __init__(self):
        # Map SKU to list of active connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, sku: str):
        await websocket.accept()
        if sku not in self.active_connections:
            self.active_connections[sku] = []
        self.active_connections[sku].append(websocket)
        logger.info(f"Client connected to inventory stream for {sku}")

    def disconnect(self, websocket: WebSocket, sku: str):
        if sku in self.active_connections:
            if websocket in self.active_connections[sku]:
                self.active_connections[sku].remove(websocket)
            if not self.active_connections[sku]:
                del self.active_connections[sku]

    async def broadcast(self, sku: str, message: dict):
        """Broadcast message to all clients listening to a SKU."""
        if sku in self.active_connections:
            disconnected = []
            for connection in self.active_connections[sku]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Client likely disconnected
                    disconnected.append(connection)
            
            # Clean up dead connections
            for conn in disconnected:
                self.disconnect(conn, sku)

# Global instance
manager = ConnectionManager()
