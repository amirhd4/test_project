from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from order_service.app.api.v1.orders import router as orders_router
from order_service.app.config import settings
from order_service.app.database import init_db
from order_service.app.kafka_producer import kafka_service

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Order Service...")
    await init_db()
    await kafka_service.start()
    yield
    logger.info("Shutting down Order Service...")
    await kafka_service.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

app.include_router(orders_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}
