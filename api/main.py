from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from libs.ws_manager import manager as ws_manager
from routers.v1.index import router as v1Router
from fastapi_pagination import add_pagination
from libs.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware



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
app.include_router(InboundWebhookRouter, prefix="/api/admin")
app.include_router(InboundWebhookRouter, prefix="/api")
app.include_router(InboundWebhookRouter, prefix="")


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
