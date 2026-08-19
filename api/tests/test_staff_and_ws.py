import pytest
import uuid
from unittest.mock import AsyncMock
from fastapi import WebSocket
from libs.ws_manager import ConnectionManager
from models.user import Staff
from schemas.user import StaffStatus
from sqlalchemy import select


@pytest.mark.asyncio
async def test_staff_termination_wipes_access(client, seed_data: dict, db_session):
    headers_2 = {"Authorization": f"Bearer {seed_data['token_2']}"}
    store_2_id = seed_data["store_2"].store_id
    staff_2_id = seed_data["staff_2"].staff_id

    res = await client.delete(f"/api/v1/{store_2_id}/staff/{staff_2_id}", headers=headers_2)
    assert res.status_code == 200

    db_res = await db_session.execute(select(Staff).where(Staff.staff_id == staff_2_id))
    staff = db_res.scalar_one_or_none()
    assert staff is not None
    assert staff.status == StaffStatus.TERMINATED
    assert staff.access_token is None


@pytest.mark.asyncio
async def test_connection_manager_store_partitioning():
    cm = ConnectionManager()
    store_a = str(uuid.uuid4())
    store_b = str(uuid.uuid4())

    ws_a1 = AsyncMock(spec=WebSocket)
    ws_a2 = AsyncMock(spec=WebSocket)
    ws_b1 = AsyncMock(spec=WebSocket)

    await cm.connect(store_a, "STAFF_A1", ws_a1)
    await cm.connect(store_a, "STAFF_A2", ws_a2)
    await cm.connect(store_b, "STAFF_B1", ws_b1)

    assert len(cm.connections[store_a]) == 2
    assert len(cm.connections[store_b]) == 1

    payload = {"event": "add_product", "data": {"name": "Test"}}
    await cm.broadcast(store_a, payload)

    assert ws_a1.send_json.call_count == 1
    assert ws_a2.send_json.call_count == 1
    ws_b1.send_json.assert_not_called()

    call_args = ws_a1.send_json.call_args[0][0]
    assert "event_id" in call_args
    assert call_args["event"] == "add_product"

    cm.disconnect(ws_a1, store_id=store_a)
    assert len(cm.connections[store_a]) == 1
