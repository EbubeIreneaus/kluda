from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import uuid
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[dict]] = {}

    async def connect(self, store_id: str | uuid.UUID, staff_id: str, websocket: WebSocket):
        await websocket.accept()
        key = str(store_id)
        if key not in self.connections:
            self.connections[key] = []
        self.connections[key].append({"staff_id": staff_id, "websocket": websocket})
        logger.info(f"WS connected: store={key} staff={staff_id} (store_total={len(self.connections[key])})")

    def disconnect(self, websocket: WebSocket, store_id: str | uuid.UUID | None = None):
        if store_id is not None:
            key = str(store_id)
            if key in self.connections:
                self.connections[key] = [c for c in self.connections[key] if c["websocket"] is not websocket]
                if not self.connections[key]:
                    del self.connections[key]
        else:
            empty_keys = []
            for key, conns in self.connections.items():
                self.connections[key] = [c for c in conns if c["websocket"] is not websocket]
                if not self.connections[key]:
                    empty_keys.append(key)
            for k in empty_keys:
                del self.connections[k]
        logger.info("WS disconnected")

    async def broadcast(
        self,
        store_id: str | uuid.UUID,
        payload: dict,
        origin_client_id: str | None = None
    ):
        key = str(store_id)
        if key not in self.connections:
            return

        if "event_id" not in payload:
            payload["event_id"] = str(uuid.uuid4())
        if origin_client_id and "origin_client_id" not in payload:
            payload["origin_client_id"] = str(origin_client_id)

        encoded_payload = jsonable_encoder(payload)
        dead: list[WebSocket] = []
        for conn in self.connections[key]:
            try:
                await conn["websocket"].send_json(encoded_payload)
            except Exception as exc:
                logger.warning(f"WS send failed for store={key} staff={conn['staff_id']}: {exc}")
                dead.append(conn["websocket"])

        for ws in dead:
            self.disconnect(ws, store_id=key)


manager = ConnectionManager()
