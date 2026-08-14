from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Singleton WebSocket connection manager.

    Tracks all connected staff clients and broadcasts mutation events to
    every client except the originator of the mutation.
    """

    def __init__(self):
        # List of {"staff_id": str, "websocket": WebSocket}
        self.connections: list[dict] = []

    async def connect(self, staff_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.append({"staff_id": staff_id, "websocket": websocket})
        logger.info(f"WS connected: {staff_id}  (total={len(self.connections)})")

    def disconnect(self, websocket: WebSocket):
        self.connections = [c for c in self.connections if c["websocket"] is not websocket]
        logger.info(f"WS disconnected  (total={len(self.connections)})")

    async def broadcast(self, payload: dict, exclude_staff_id: str | None = None):
        """Send *payload* as JSON to every connected client except *exclude_staff_id*."""
        dead: list[WebSocket] = []
        for conn in self.connections:
            if exclude_staff_id and conn["staff_id"] == exclude_staff_id:
                continue
            try:
                await conn["websocket"].send_json(payload)
            except Exception as exc:
                logger.warning(f"WS send failed for {conn['staff_id']}: {exc}")
                dead.append(conn["websocket"])

        # Prune dead connections discovered during broadcast
        for ws in dead:
            self.disconnect(ws)


# Module-level singleton — import this everywhere
manager = ConnectionManager()
