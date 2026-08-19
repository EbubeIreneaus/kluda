from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from libs.ws_manager import manager as ws_manager
from models.config import LocalSession
from libs.init_db import create_super_staff
from routers.v1.index import router as v1Router
from fastapi_pagination import add_pagination
from libs.limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.exceptions import HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with LocalSession() as session:
        try:
            await create_super_staff(session)
            await session.commit()
        except Exception as e:
            await session.rollback()
    yield


app = FastAPI(
    title="Kluda Platform API",
    description="High-performance backend API for Kluda Retail Platform",
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    raise HTTPException(status_code=429, detail="Too Many Requests")

app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1Router, prefix="/api", tags=['version 1.0.0'])


@app.get("/")
async def root():
    return {"message": "Kluda API is running"}


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
