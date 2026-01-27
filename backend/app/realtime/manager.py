from fastapi import WebSocket
from typing import Dict, Set
import json
from datetime import datetime, timezone


class ConnectionManager:
    """Manages WebSocket connections per board (room)."""

    def __init__(self):
        # board_id -> set of WebSocket connections
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, board_id: int):
        """Accept connection and add to room."""
        await websocket.accept()
        if board_id not in self.rooms:
            self.rooms[board_id] = set()
        self.rooms[board_id].add(websocket)

    def disconnect(self, websocket: WebSocket, board_id: int):
        """Remove connection from room."""
        if board_id in self.rooms:
            self.rooms[board_id].discard(websocket)
            if not self.rooms[board_id]:
                del self.rooms[board_id]

    async def broadcast_to_board(self, board_id: int, event_type: str, item_data: dict = None, exclude: WebSocket = None):
        """Broadcast event to all connections in a board room."""
        if board_id not in self.rooms:
            return

        message = {
            "type": event_type,
            "board_id": board_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "item": item_data
        }

        dead_connections = []

        for connection in self.rooms[board_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.rooms[board_id].discard(conn)


# Global connection manager instance
manager = ConnectionManager()
