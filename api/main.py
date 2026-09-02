import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from libs.ws_manager import manager as ws_manager
from routers.v1.index import router as v1Router
from fastapi_pagination import add_pagination
from libs.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from libs.payment import payment_manager
from worker.config import get_arq_pool



from libs.logger import setup_logging
from middleware.request_logger import RequestLoggingMiddleware

setup_logging()

app = FastAPI(
    title="Kluda Platform API",
    description="High-performance backend API for Kluda Retail Platform",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(RequestLoggingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.v1.admin.webhook import router as InboundWebhookRouter

app.include_router(v1Router, prefix="/api", tags=['version 1.0.0'])
app.include_router(InboundWebhookRouter, prefix="")


@app.post("/paystack-webhook")
async def paystack_webhook(request: Request):
    signature = request.headers.get("x-paystack-signature")
    body = await request.body()
    if not payment_manager.verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    try:
        event_data = json.loads(body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    pool = await get_arq_pool()
    await pool.enqueue_job("process_paystack_webhook", event_data)
    return {"status": "success"}


@app.get("/ping")
@app.get("/")
async def ping():
    return {"status": "ok", "message": "Kluda API is running"}


@app.websocket("/ws/{store_id}/{staff_id}")
async def websocket_endpoint(store_id: str, staff_id: str, websocket: WebSocket):
    await ws_manager.connect(store_id, staff_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, store_id=store_id)


def main():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
