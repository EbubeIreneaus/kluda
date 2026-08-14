from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from libs.ws_manager import manager as ws_manager
from models.config import LocalSession
from libs.init_db import create_super_staff
from routers.auth import router as auth_router
from routers.staff import router as staff_router
from routers.stock.product import router as product_router
from routers.stock.customer import router as customer_router, router2 as debtor_router
from routers.stock.sales import router as sales_router
from fastapi_pagination import add_pagination


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
    title="Retail POS System API",
    description="High-performance backend API for Retail POS System",
    version="1.0.0",
    lifespan=lifespan,
)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(staff_router)
app.include_router(product_router)
app.include_router(customer_router)
app.include_router(debtor_router)
app.include_router(sales_router)


@app.get("/")
async def root():
    return {"message": "Retail POS API is running"}


@app.websocket("/ws/{staff_id}")
async def websocket_endpoint(staff_id: str, websocket: WebSocket):
    """Per-staff WebSocket connection. Keeps alive until the client disconnects."""
    await ws_manager.connect(staff_id, websocket)
    try:
        while True:
            # Receive pings / any client-sent messages (we just discard them)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


def main():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
