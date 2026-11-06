import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from api import ROUTERS
from core.config import ENABLE_SCHEDULER, FRONTEND_URL
from core.database import init_db
from exceptions.base import AppException
from tasks.scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_db()
    task = asyncio.create_task(scheduler_loop()) if ENABLE_SCHEDULER else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="CareerBridge API",
    description="Hệ thống tìm việc thông minh tích hợp AI và BI",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.message, "code": exc.code}
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    # Hai request đồng thời cùng vượt qua bước kiểm tra trùng -> ràng buộc UNIQUE của CSDL chặn lại
    logging.getLogger(__name__).info("Integrity error: %s", exc.orig)
    return JSONResponse(
        status_code=409, content={"detail": "Dữ liệu đã tồn tại hoặc bị xung đột", "code": "CONFLICT"}
    )


for router in ROUTERS:
    app.include_router(router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
