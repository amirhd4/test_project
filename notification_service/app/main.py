from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, Query
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notification_service.app.config import settings
from notification_service.app.database import get_db, init_db
from notification_service.app.kafka_consumer import kafka_consumer_service
from notification_service.app.models import Notification

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Notification Service...")
    await init_db()
    await kafka_consumer_service.start()
    yield
    logger.info("Shutting down Notification Service...")
    await kafka_consumer_service.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/api/v1/notifications", tags=["Notifications"])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List sent notification records."""
    query = select(Notification).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        {
            "id": n.id,
            "order_id": n.order_id,
            "customer_id": n.customer_id,
            "channel": n.channel,
            "recipient": n.recipient,
            "message": n.message,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]
